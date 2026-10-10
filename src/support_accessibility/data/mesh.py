"""网格前端：真实三维网格 → 占据栅格（igl generalized winding number 判内外）。

口径见 governance/决策台账.md D-009（本片：阈值 0.5；无 CSG，多实体用 numpy V/F 堆叠；
**禁用 trimesh.util.concatenate / apply_translation——本 env 原生崩溃**）。产出 occupancy 喂 oracle（体素单位）。
mesh 创建/加载用 trimesh；合并与平移用 numpy。

numpy/igl/trimesh 在函数内 import，保证系统 py（无这些）仍能 `import mesh`（gate 兜底 PENDING）。
"""

from support_accessibility.runtime.frozen_params import FROZEN


def mesh_to_occupancy(V, F, resolution=FROZEN.resolution, pad=0.2):
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

      - "free"    ：+n 落自由/栅格外 → 返回该点。常态。
      - "confined"：+n 落实体 且 −n 也落实体 → 深窄槽/两体窄隙里的**真下朝面**（稀有不可达正类几何）→ 返回 +n 点
                    （oracle 判不可达）——**不删最硬的正类样本**。
      - "flipped" ：+n 落实体 但 −n 落自由 → 法向翻转（该面真外法向朝上、并非下朝面，被悬垂判据误纳 S(P,d)）→ 返回 None（**丢弃**）。

    返回 (status, q|None)。占据用 igl 缠绕数（对缠绕稳健），法向用 np.cross（缠绕敏感），本三态桥接二者：
    只丢弃"翻面"这一类伪下朝面；confined 与 free 均保留（依据见 D-028）。判据语义 D-001..D-005 未动。
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
