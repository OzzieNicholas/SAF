"""精确胶囊-网格边界细化的几何原语（D-003）——TDD 建 src/.../oracle/capsule.py。

已知答案件：手算真值锚定 segment-triangle 最小距离的每个分支 + capsule_hits_mesh。
纯 numpy（无 gemm）；缺 numpy → skip。gate 集成（checks()）在原语稳后补。
"""
from unittest import SkipTest


def _np():
    try:
        import numpy  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"numpy 未就绪：{e}")


def test_segment_above_triangle_interior():
    """段平行于三角面、悬于其内部上方 → 距离=垂直高度（既非端点、也非边最近）。"""
    _np()
    import numpy as np
    from support_accessibility.oracle.capsule import segment_triangle_sq_dist
    tri = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
    A = np.array([0.2, 0.2, 1.0]); B = np.array([0.3, 0.2, 1.0])   # 平行、投影落在三角内
    d2 = segment_triangle_sq_dist(A, B, tri)
    assert abs(d2 - 1.0) < 1e-9, f"期望 1.0，实得 {d2}"


def test_segment_parallel_outside_edge():
    """段平行于三角一条边、悬于边外侧 → 最近是"中段对边"，两端点更远（逼出 seg-seg）。"""
    _np()
    import numpy as np
    from support_accessibility.oracle.capsule import segment_triangle_sq_dist
    tri = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
    A = np.array([-1., -1, 0]); B = np.array([2., -1, 0])          # 平行 ab 边、y=-1 外侧
    d2 = segment_triangle_sq_dist(A, B, tri)
    assert abs(d2 - 1.0) < 1e-9, f"期望 1.0（中段对 ab 边），实得 {d2}"


def test_segment_crosses_triangle():
    """段穿过三角面内部 → 距离 0（逼出穿越测试）。"""
    _np()
    import numpy as np
    from support_accessibility.oracle.capsule import segment_triangle_sq_dist
    tri = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
    A = np.array([0.25, 0.25, -1.]); B = np.array([0.25, 0.25, 1.])   # 竖直穿过内部点(0.25,0.25,0)
    d2 = segment_triangle_sq_dist(A, B, tri)
    assert d2 < 1e-12, f"穿越应距离 0，实得 {d2}"


def test_capsule_hits_mesh_radius_threshold():
    """胶囊（半径 r 沿方向的扫掠球）触网 ⟺ 半无穷射线到网格最小距离 ≤ r。"""
    _np()
    import numpy as np
    from support_accessibility.oracle.capsule import capsule_hits_mesh
    V = np.array([[0., 0, 0], [2, 0, 0], [0, 2, 0]])
    F = np.array([[0, 1, 2]])
    O = np.array([0.5, 0.5, 2.]); D = np.array([1., 0, 0])       # 平行三角面、垂距=2、沿 +x
    assert capsule_hits_mesh(O, D, 1.5, V, F) is False           # 2 > 1.5 → 未触
    assert capsule_hits_mesh(O, D, 2.5, V, F) is True            # 2 ≤ 2.5 → 触


def test_capsule_forward_only():
    """半无穷射线只朝前：三角面在原点前方沿 -dir 一侧、且距原点 > r → 不触（方向敏感）。"""
    _np()
    import numpy as np
    from support_accessibility.oracle.capsule import capsule_hits_mesh
    V = np.array([[-1., -1, 0], [1, -1, 0], [0, -3, 0]])          # 三角面在 y<0（原点后方）
    F = np.array([[0, 1, 2]])
    O = np.array([0., 0, 0.]); D = np.array([0., 1, 0])          # 原点，朝 +y（远离三角面）
    assert capsule_hits_mesh(O, D, 0.5, V, F) is False           # 三角面在后方且 >r → 不触
