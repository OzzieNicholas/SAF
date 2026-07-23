"""精确胶囊-网格边界细化的几何原语（D-003）——TDD 建 src/.../oracle/capsule.py。

已知答案件：手算真值锚定 segment-triangle 最小距离的每个分支 + capsule_hits_mesh。
纯 numpy（无 gemm）；缺 numpy → skip。gate 集成（checks()）在原语稳后补。
"""
from unittest import SkipTest

from . import pending, result


def _np():
    try:
        import numpy  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"numpy 未就绪：{e}")


def checks():
    """gate 集成：几何原语 + 三态判定代表性断言（D-003 边界带精确胶囊细化落地 / D-020）。"""
    try:
        import numpy as np
        from support_accessibility.oracle.capsule import segment_triangle_sq_dist, capsule_hits_mesh
        from support_accessibility.oracle import decide_label, Label
    except ImportError as e:
        return [pending("capsule_refinement", f"依赖未就绪：{e}", "D-003")]
    try:
        tri = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
        ok_cross = segment_triangle_sq_dist(np.array([0.25, 0.25, -1.]), np.array([0.25, 0.25, 1.]), tri) < 1e-12
        ok_above = abs(segment_triangle_sq_dist(np.array([0.2, 0.2, 1.]), np.array([0.3, 0.2, 1.]), tri) - 1.0) < 1e-9
        V = np.array([[0., 0, 0], [2, 0, 0], [0, 2, 0]]); F = np.array([[0, 1, 2]])
        O = np.array([0.5, 0.5, 2.]); D = np.array([1., 0, 0])
        ok_cap = (capsule_hits_mesh(O, D, 1.5, V, F) is False) and (capsule_hits_mesh(O, D, 2.5, V, F) is True)
        ok_dec = (decide_label([5., 2, 1], 3., 1., refine=None) == Label.ACCESSIBLE
                  and decide_label([2.9, 1, 0.5], 3., 0.5, refine=None) == Label.INACCESSIBLE
                  and decide_label([3.2, 3.1, 0.5], 3., 0.5, refine=lambda i: i == 1) == Label.ACCESSIBLE)
        return [
            result("capsule_segment_triangle", bool(ok_cross and ok_above), "穿越=0 & 平行内部上方=垂距", "D-003"),
            result("capsule_hits_mesh", bool(ok_cap), "半径阈值 2：miss@1.5 / hit@2.5", "D-003"),
            result("decide_label_three_tier", bool(ok_dec), "无网格二分 + 有网格含糊交精确 refine（D-020）", "D-003"),
        ]
    except Exception as e:
        return [result("capsule_refinement", False, f"异常：{e}", "D-003")]


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


# —— 三态判定逻辑（clearance vs r±ε → CLEAR/BLOCKED/AMBIGUOUS，AMBIGUOUS 交精确 refine）——
def test_decide_clear_direction_accessible():
    """某方向净空 > r+ε → 直接 accessible，不触发 refine。"""
    _np()
    from support_accessibility.oracle import decide_label, Label
    calls = []
    got = decide_label([5.0, 2.0, 1.0], r=3.0, eps=1.0, refine=lambda i: calls.append(i) or True)
    assert got == Label.ACCESSIBLE and calls == [], f"实得 {got}, refine 调用 {calls}"


def test_decide_no_mesh_binary():
    """无网格（refine=None）→ 二分（与细化前口径一致，程序化管线不变）：任一净空 > r 即可达。"""
    _np()
    from support_accessibility.oracle import decide_label, Label
    assert decide_label([3.2, 1.0, 0.5], r=3.0, eps=0.5, refine=None) == Label.ACCESSIBLE    # 3.2>3
    assert decide_label([2.9, 1.0, 0.5], r=3.0, eps=0.5, refine=None) == Label.INACCESSIBLE  # 皆≤3


def test_decide_all_blocked_inaccessible():
    """全方向净空 < r-ε → INACCESSIBLE。"""
    _np()
    from support_accessibility.oracle import decide_label, Label
    got = decide_label([1.0, 0.5, 0.2], r=3.0, eps=0.5, refine=None)
    assert got == Label.INACCESSIBLE, f"实得 {got}"


def test_decide_ambiguous_refine_clear_accessible():
    """含糊方向经精确 refine 判无碰撞 → ACCESSIBLE。"""
    _np()
    from support_accessibility.oracle import decide_label, Label
    calls = []
    def refine(i):
        calls.append(i)
        return i == 1                                   # 方向1精确无碰撞
    got = decide_label([3.2, 3.1, 0.5], r=3.0, eps=0.5, refine=refine)   # idx0,1 含糊；idx2 blocked
    assert got == Label.ACCESSIBLE and 1 in calls, f"实得 {got}, calls {calls}"


def test_decide_ambiguous_refine_blocked_inaccessible():
    """所有含糊方向经精确 refine 皆碰撞 → INACCESSIBLE。"""
    _np()
    from support_accessibility.oracle import decide_label, Label
    got = decide_label([3.2, 3.1, 0.5], r=3.0, eps=0.5, refine=lambda i: False)
    assert got == Label.INACCESSIBLE, f"实得 {got}"
