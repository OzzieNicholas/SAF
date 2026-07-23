"""精确胶囊-网格边界细化几何原语（D-003：边界带用精确胶囊-网格求交细化）。

体素腐蚀口径判不定的边界点，用精确几何（无离散误差）定夺：胶囊（半径 r 沿逼近方向的扫掠球）
是否与零件本体网格求交 ⟺ 半无穷射线到三角网格的最小距离 ≤ r。纯 numpy（无 gemm），本地可跑。

自底向上、测试先行：point-triangle 最近点（Ericson）→ segment-triangle 距离 → capsule_hits_mesh。
numpy 模块级 import（本模块属 oracle 包，与 oracle/__init__ 同为数值依赖）。
"""
import numpy as np


def _closest_pt_point_triangle(p, a, b, c):
    """三角形 abc 上距 p 最近的点（Ericson, Real-Time Collision Detection §5.1.5）。"""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = float(ab @ ap), float(ac @ ap)
    if d1 <= 0 and d2 <= 0:
        return a                                    # 顶点 a 区域
    bp = p - b
    d3, d4 = float(ab @ bp), float(ac @ bp)
    if d3 >= 0 and d4 <= d3:
        return b                                    # 顶点 b 区域
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        return a + v * ab                           # 边 ab 区域
    cp = p - c
    d5, d6 = float(ab @ cp), float(ac @ cp)
    if d6 >= 0 and d5 <= d6:
        return c                                    # 顶点 c 区域
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        return a + w * ac                           # 边 ac 区域
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + w * (c - b)                       # 边 bc 区域
    denom = 1.0 / (va + vb + vc)                     # 面内部
    return a + ab * (vb * denom) + ac * (vc * denom)


def point_triangle_sq_dist(p, tri):
    """点 p 到三角形 tri[(3,3)] 的最小平方距离。"""
    p = np.asarray(p, float)
    q = _closest_pt_point_triangle(p, tri[0], tri[1], tri[2])
    d = p - q
    return float(d @ d)


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def segment_segment_sq_dist(p1, q1, p2, q2, eps=1e-12):
    """两线段 [p1,q1]、[p2,q2] 的最小平方距离（Ericson §5.1.9 ClosestPtSegmentSegment）。"""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = float(d1 @ d1), float(d2 @ d2), float(d2 @ r)
    if a <= eps and e <= eps:
        d = p1 - p2
        return float(d @ d)
    if a <= eps:
        s, t = 0.0, _clamp01(f / e)
    else:
        c = float(d1 @ r)
        if e <= eps:
            t, s = 0.0, _clamp01(-c / a)
        else:
            b = float(d1 @ d2)
            denom = a * e - b * b
            s = _clamp01((b * f - c * e) / denom) if denom > eps else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, _clamp01(-c / a)
            elif t > 1.0:
                t, s = 1.0, _clamp01((b - c) / a)
    c1, c2 = p1 + d1 * s, p2 + d2 * t
    d = c1 - c2
    return float(d @ d)


def _segment_intersects_triangle(A, B, tri, eps=1e-12):
    """线段 [A,B] 是否穿过三角形内部（Möller–Trumbore，段参数 ∈[0,1]）。"""
    a, b, c = tri
    e1, e2, d = b - a, c - a, B - A
    p = np.cross(d, e2)
    det = float(e1 @ p)
    if abs(det) < eps:
        return False                                # 平行/共面
    inv = 1.0 / det
    tvec = A - a
    u = float(tvec @ p) * inv
    if u < 0.0 or u > 1.0:
        return False
    q = np.cross(tvec, e1)
    v = float(d @ q) * inv
    if v < 0.0 or u + v > 1.0:
        return False
    w = float(e2 @ q) * inv                          # 沿段参数
    return 0.0 <= w <= 1.0


def segment_triangle_sq_dist(A, B, tri):
    """线段 [A,B] 到三角形 tri 的最小平方距离 = 穿越则 0，否则 min(端点对面, 段对三边)。"""
    A = np.asarray(A, float); B = np.asarray(B, float)
    tri = np.asarray(tri, float)
    if _segment_intersects_triangle(A, B, tri):
        return 0.0
    best = min(point_triangle_sq_dist(A, tri), point_triangle_sq_dist(B, tri))
    for i in range(3):
        best = min(best, segment_segment_sq_dist(A, B, tri[i], tri[(i + 1) % 3]))
    return best


def capsule_hits_mesh(origin, direction, r, V, F, margin=1.0):
    """胶囊（半径 r、原点 origin、单位方向 direction 的半无穷扫掠球）是否触及三角网格 (V,F)。

    ⟺ 半无穷射线 {origin + t·direction, t≥0} 到网格最小距离 ≤ r。用越过最远顶点的长段近似半无穷
    射线（故段覆盖网格可能落入 r 的全部射线参数）；网格在原点后方且 >r 则不触（方向敏感）。返回 bool。
    """
    origin = np.asarray(origin, float)
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    V = np.asarray(V, float)
    F = np.asarray(F, np.int64)
    far = float(np.max(np.linalg.norm(V - origin, axis=1))) + float(r) + float(margin)
    B = origin + d * far
    r2 = float(r) * float(r)
    for f in F:
        if segment_triangle_sq_dist(origin, B, V[f]) <= r2:
            return True
    return False
