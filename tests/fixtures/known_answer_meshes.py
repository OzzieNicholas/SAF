"""构造即知答案的合成网格：盒子与双盒窄间隙。

供网格前端、支撑接触区与 Fusion 测试使用，不属于产品代码。
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
