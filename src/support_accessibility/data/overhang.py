"""支撑接触区提取：网格(V,F) + 构建方向 d → 下朝悬垂面（支撑接触区代理 S(P,d)）。

判据（D-010）：外法向 n 与 d 夹角超阈值 ⟺ 局部倾角<自支撑临界角
⟺ `n·d̂ < -cos(overhang_deg)`。θ_c=overhang_angle_deg=45（configs/oracle_params.yaml）。S 随 d 变。
接触点取悬垂面质心。外法向用 numpy cross；真实网格的翻面由 data/mesh.py 的缠绕安全外移丢弃（D-028）。numpy 在函数内 import（防御式，系统 py 仍可 `import overhang`）。
"""

from support_accessibility.runtime.frozen_params import FROZEN

from dataclasses import dataclass


# 6 个轴向候选构建方向：把方向 d 转到 +z 的正交旋转（行列式 +1，保持网格缠绕方向）。
# 零件按此旋转后，仍以 +z 为构建方向提取接触区，即可评价候选方向 d。
AXIS_BUILD_ROTATIONS = {
    "+z": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "-z": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
    "+x": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    "-x": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
    "+y": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "-y": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
}


@dataclass
class SupportContact:
    """支撑接触区代理 S(P,d)：下朝悬垂面（质心=接触点）。"""
    indices: object      # (k,) 悬垂面在 F 中的行号
    centroids: object    # (k,3) 面质心（世界坐标）
    normals: object      # (k,3) 外法向（单位）
    d: object            # (3,) 单位构建方向
    overhang_deg: float


def face_normals_centroids(V, F):
    """每面外法向（单位化）+ 质心。返回 (normals[m,3], centroids[m,3])。"""
    import numpy as np
    V = np.asarray(V, float)
    F = np.asarray(F, np.int64)
    tri = V[F]                                        # (m,3,3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln > 0, ln, 1.0)
    return n, tri.mean(axis=1)


def support_contact_faces(V, F, d, overhang_deg=FROZEN.overhang_deg):
    """下朝悬垂面 = 支撑接触区代理 S(P,d)。判据 n·d̂ < -cos(overhang_deg)。"""
    import numpy as np
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    n, c = face_normals_centroids(V, F)
    # Avoid dispatching a tiny BLAS matvec after VTK/PyVista has loaded its
    # OpenMP runtime on Windows.  Elementwise reduction is mathematically
    # identical and keeps figure generation in the same process reliable.
    mask = np.sum(n * d[None, :], axis=1) < -np.cos(np.radians(overhang_deg))
    idx = np.nonzero(mask)[0]
    return SupportContact(idx, c[mask], n[mask], d, float(overhang_deg))
