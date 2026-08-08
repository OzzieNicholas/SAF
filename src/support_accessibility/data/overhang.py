"""支撑接触区提取：网格(V,F) + 构建方向 d → 下朝悬垂面（支撑接触区代理 S(P,d)）。

判据（docs §9.1、decisions D-010）：外法向 n 与 d 夹角超阈值 ⟺ 局部倾角<自支撑临界角
⟺ `n·d̂ < -cos(overhang_deg)`。θ_c=overhang_angle_deg=45（configs/params.yaml）。S 随 d 变（§9.2）。
MVP 用悬垂面质心作支撑接触点。外法向用 numpy cross（假设外向一致缠绕——trimesh 图元成立；
真实网格缠绕修复属后续）。numpy 在函数内 import（防御式，系统 py 仍可 `import overhang`）。
"""

from dataclasses import dataclass


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


def support_contact_faces(V, F, d, overhang_deg=45.0):
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
