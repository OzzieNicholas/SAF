"""程序化已知答案件生成器 —— walking skeleton 的头几个测试件（构造即知答案）。

本批用**解析占据栅格**（numpy）直接构造，绕开 mesh 布尔/manifold 依赖；mesh→occupancy 的真实前端
（igl 判内外、trimesh 读取）属后续批次。点/半径以体素为单位，与 oracle 口径一致。
构造即知答案：造了个窄盲腔，其天花板下的点就必然不可达（D-001）；开阔下朝面必然可达（D-002）。

模块级只用 stdlib；numpy 在函数内 import，保证系统 py（无 numpy）仍能 `import data`（gate 兜底 PENDING）。
"""

from dataclasses import dataclass


@dataclass
class VoxelCase:
    """占据栅格上的一个构造即知答案件。"""
    name: str
    decision: str
    occ: object          # np.ndarray[bool]，True=实体
    point: tuple         # (x,y,z) 体素坐标（支撑接触点，下朝面）
    radius: float        # 工具球半径（体素）
    expected: str        # "accessible" | "inaccessible"


def blind_cavity_case(N=40, opening=3, depth=16, radius=3.0):
    """底面开口的盲孔：实心厚板 z∈[z0,z1)，从底面 z0 向上挖 opening×opening 方孔到 z0+depth（不透顶）。
    查询点 = 孔顶（下朝天花板）下方的自由体素。opening 窄于 ~2r → 球进不去 → 不可达（D-001）。
    板上下留自由空间（基板不建模，遮挡下界）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0, z1 = 8, N - 8
    occ[:, :, z0:z1] = True                              # 实心厚板（x,y 全）
    c, h = N // 2, opening // 2
    occ[c - h:c + h + 1, c - h:c + h + 1, z0:z0 + depth] = False   # 从底面挖方孔到 z0+depth（盲）
    ceiling = z0 + depth                                 # 天花板（实体）在 z=ceiling
    point = (float(c), float(c), float(ceiling - 1))     # 天花板下的自由体素（下朝面）
    return VoxelCase("blind_cavity", "D-001", occ, point, float(radius), "inaccessible")


def open_downface_case(N=40, radius=3.0):
    """开阔下朝面：厚板 z∈[z0,z1)，底面 z0 下方全自由。查询点=板底中心下方的自由体素 → 可达（D-002）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0, z1 = 20, N - 6
    occ[:, :, z0:z1] = True
    c = N // 2
    point = (float(c), float(c), float(z0 - 1))          # 板底下的自由体素（下朝面）
    return VoxelCase("open_downface", "D-002", occ, point, float(radius), "accessible")


# —— 后续批次 ——
def deep_narrow_slot(width, depth):
    """深窄槽；随 width/depth 与工具半径耦合，用于半径单调趋势（D-003）。"""
    raise NotImplementedError("后续批次（变形性质）。")


def flagship_pair(support_area_target, cavity_depth_a, cavity_depth_b):
    """旗舰配对：支撑面积近似相等、腔深不同的两件，保 E1/H1 存在性。"""
    raise NotImplementedError("后续批次。")
