"""网格前端：真实三维网格 → 占据栅格（igl generalized winding number 判内外）。

口径见 governance/decisions.md D-007（选 igl）/ D-009（本片：阈值 0.5；无 CSG，多实体用 numpy V/F 堆叠；
**禁用 trimesh.util.concatenate / apply_translation——本 env 原生崩溃**）。产出 occupancy 喂 oracle（体素单位）。
mesh 创建/加载用 trimesh；合并与平移用 numpy。

numpy/igl/trimesh 在函数内 import，保证系统 py（无这些）仍能 `import mesh`（gate 兜底 PENDING）。
"""

from dataclasses import dataclass


@dataclass
class MeshCase:
    """真实网格上的构造即知答案件。"""
    name: str
    decision: str
    V: object            # (n,3) float 顶点
    F: object            # (m,3) int 面
    point_world: tuple   # 查询点（世界坐标）
    radius_world: float  # 工具半径（世界坐标）
    expected: str        # "accessible" | "inaccessible"


def box_vf(extents, center=(0.0, 0.0, 0.0)):
    """从 trimesh 取盒的 (V,F)；平移用 numpy 加法（不用 apply_translation）。"""
    import numpy as np
    import trimesh
    m = trimesh.creation.box(extents=extents)
    V = np.asarray(m.vertices, float) + np.asarray(center, float)
    F = np.asarray(m.faces, np.int32)
    return V, F


def stack_vf(parts):
    """手动合并多实体 (V,F)：np.vstack 顶点 + 面索引偏移（替代 trimesh.concatenate）。"""
    import numpy as np
    Vs, Fs, off = [], [], 0
    for V, F in parts:
        V = np.asarray(V, float)
        Vs.append(V)
        Fs.append(np.asarray(F, np.int32) + off)
        off += len(V)
    return np.vstack(Vs), np.vstack(Fs).astype(np.int32)


def mesh_to_occupancy(V, F, resolution=48, pad=0.2):
    """网格 → 占据栅格。over 填充 bbox 建栅格中心点，igl.fast_winding_number>0.5 判内。

    返回 (occ[bool 三维], lo[3] 世界坐标原点, pitch 体素边长)。
    """
    import numpy as np
    import igl
    V = np.asarray(V, float)
    F = np.asarray(F, np.int32)
    lo = V.min(0); hi = V.max(0); ext = hi - lo
    lo = lo - ext * pad; hi = hi + ext * pad
    pitch = float((hi - lo).max()) / resolution
    # -1e-9：消最大轴 ceil 浮点过冲（res→res+1 跨平台，破字节可复现）；max(1,·)：零厚度轴不塌成空栅格
    ns = [max(1, int(np.ceil((hi[i] - lo[i]) / pitch - 1e-9))) for i in range(3)]
    ax = [lo[i] + (np.arange(ns[i]) + 0.5) * pitch for i in range(3)]
    gx, gy, gz = np.meshgrid(*ax, indexing="ij")
    pts = np.ascontiguousarray(np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1))
    occ = igl.fast_winding_number(V, F, pts).reshape(ns[0], ns[1], ns[2]) > 0.5
    return occ, lo, pitch


def world_to_voxel(p, lo, pitch):
    """世界坐标 → 体素索引坐标（喂 oracle.label）。"""
    import numpy as np
    return tuple((np.asarray(p, float) - np.asarray(lo, float)) / pitch - 0.5)


def nudge_to_free(occ, c, n, nudge_world, lo, pitch):
    """接触点沿外法向 +n 外移 nudge_world 得体素查询点，按落点分**三态**（缠绕/窄隙安全，D-028 extend D-010）：

      - "free"    ：+n 落自由/栅格外 → 返回该点。**常态，与旧 +n 口径逐点一致**。
      - "confined"：+n 落实体 且 −n 也落实体 → 深窄槽/两体窄隙里的**真下朝面**（稀有不可达正类几何）→ 返回 +n 点
                    （同旧口径、oracle 判不可达）——**不删最硬的正类样本**。
      - "flipped" ：+n 落实体 但 −n 落自由 → 法向翻转（该面真外法向朝上、并非下朝面，被悬垂判据误纳 S(P,d)）→ 返回 None（**丢弃**）。

    返回 (status, q|None)。占据用 igl 缠绕数（对缠绕稳健），法向用 np.cross（缠绕敏感），本三态桥接二者：
    只丢弃"翻面"这一类伪下朝面（旧口径会把它当可达点误纳），confined/free 与旧口径一致。判据语义 D-001..D-005 未动。
    """
    import numpy as np
    occ = np.asarray(occ, bool)
    c = np.asarray(c, float)
    n = np.asarray(n, float)

    def _solid(q):
        idx = tuple(int(np.floor(v + 0.5)) for v in q)          # 最近体素（同 oracle floor(c+.5) 约定；显式界判避 numpy 负索引回绕）
        if all(0 <= idx[i] < occ.shape[i] for i in range(3)):
            return bool(occ[idx])
        return False                                            # 栅格外 = 自由（pad 区）

    q = world_to_voxel(c + n * nudge_world, lo, pitch)
    if not _solid(q):
        return "free", q
    q2 = world_to_voxel(c - n * nudge_world, lo, pitch)
    return ("flipped", None) if not _solid(q2) else ("confined", q)


# —— 两个真实网格已知答案件（构造即知）——
def box_downface_case():
    """单盒 6×6×4（z∈[-2,2]）。查询点在底面下方 → 下朝面开阔 → accessible（D-002）。"""
    V, F = box_vf((6.0, 6.0, 4.0))
    return MeshCase("mesh_box_downface", "D-002", V, F, (0.0, 0.0, -2.5), 1.0, "accessible")


def two_box_gap_case(gap=1.2):
    """两盒 8×8×4 叠放、窄间隙 gap（numpy 堆叠）。间隙点在上盒底面下、工具直径>gap → inaccessible（D-001 confinement）。"""
    V1, F1 = box_vf((8.0, 8.0, 4.0))                                  # z ∈ [-2, 2]
    V2, F2 = box_vf((8.0, 8.0, 4.0), center=(0.0, 0.0, 4.0 + gap))    # z ∈ [2+gap, 6+gap]
    V, F = stack_vf([(V1, F1), (V2, F2)])
    # 间隙 z∈[2, 2+gap]；查询点在上盒下朝面(z=2+gap)略下；半径取 gap（直径 2·gap>gap，进不去）
    return MeshCase("mesh_two_box_gap", "D-001", V, F, (0.0, 0.0, 2.0 + gap - 0.3), float(gap), "inaccessible")
