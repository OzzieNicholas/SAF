"""支撑接触区提取验收：网格+d → 下朝悬垂面 S(P,d)（docs §9、D-010）。

基于 box（外向缠绕明确）。四锚点：提取正确、方向依赖(§9.2)、阈值(θc=45)、端到端(接触区→可达)。
依赖缺失 → PENDING（checks）/ SkipTest（test_）。
"""

from unittest import SkipTest

from . import pending, result

_NDIR = 64


def _box(extents=(6.0, 6.0, 4.0)):
    from support_accessibility.data import mesh as M
    return M.box_vf(extents)


def _extract(d, overhang_deg=45.0):
    from support_accessibility.data import overhang as O
    V, F = _box()
    return V, F, O.support_contact_faces(V, F, d, overhang_deg)


def _has_bottom(sc, z=-2.0, tol=0.1):
    import numpy as np
    return bool(len(sc.centroids)) and bool((np.abs(sc.centroids[:, 2] - z) < tol).any())


def _end_to_end_all_accessible():
    import numpy as np
    from support_accessibility.data import mesh as M, overhang as O
    from support_accessibility.oracle import SupportAccessibilityOracle
    V, F = _box()
    sc = O.support_contact_faces(V, F, [0, 0, 1.0])
    occ, lo, pitch = M.mesh_to_occupancy(V, F, resolution=48)
    o = SupportAccessibilityOracle(occ, {"n_directions": _NDIR})
    r = 1.0 / pitch
    labs = []
    for c, n in zip(sc.centroids, sc.normals):
        q = c + n * (2.0 * pitch)                    # 质心沿外法向外移到自由侧，作查询点
        labs.append(o.label(M.world_to_voxel(q, lo, pitch), r).value)
    return len(labs) > 0 and all(x == "accessible" for x in labs)


def checks():
    try:
        import numpy as np
        from support_accessibility.data import overhang, mesh  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", "D-010") for n in
                ("sc_extraction", "sc_direction_dependence", "sc_threshold", "sc_end_to_end_accessible")]
    out = []
    try:
        _, _, sc = _extract([0, 0, 1.0])
        ok = (len(sc.centroids) == 2 and np.allclose(sc.centroids[:, 2], -2.0, atol=0.1)
              and bool(np.all((sc.normals @ np.array([0, 0, 1.0])) < -0.99)))
        out.append(result("sc_extraction", ok, f"d=+z 悬垂面={len(sc.centroids)}（期望底面2）", "D-010"))
    except Exception as e:
        out.append(result("sc_extraction", False, f"异常：{e}", "D-010"))
    try:
        _, _, scx = _extract([1.0, 0, 0])
        ok = (len(scx.centroids) == 2 and np.allclose(scx.centroids[:, 0], -3.0, atol=0.1)
              and not _has_bottom(scx))
        out.append(result("sc_direction_dependence", ok, "d=+x 取 -x 面(x≈-3)，非底面", "D-010"))
    except Exception as e:
        out.append(result("sc_direction_dependence", False, f"异常：{e}", "D-010"))
    try:
        def bo(g):
            return _has_bottom(_extract([np.sin(np.radians(g)), 0, np.cos(np.radians(g))])[2])
        out.append(result("sc_threshold", bo(30) and not bo(60), "tilt30=悬垂 & tilt60=非（θc=45）", "D-010"))
    except Exception as e:
        out.append(result("sc_threshold", False, f"异常：{e}", "D-010"))
    try:
        out.append(result("sc_end_to_end_accessible", _end_to_end_all_accessible(),
                           "box d=+z 支撑接触点全 accessible", "D-010"))
    except Exception as e:
        out.append(result("sc_end_to_end_accessible", False, f"异常：{e}", "D-010"))
    return out


def test_box_overhang_extraction():
    """box d=+z → 悬垂=底面2面（z≈-2、n≈-z）；顶/侧不含。"""
    try:
        import numpy as np
        _, _, sc = _extract([0, 0, 1.0])
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert len(sc.centroids) == 2, f"底面应2面，得 {len(sc.centroids)}"
    assert np.allclose(sc.centroids[:, 2], -2.0, atol=0.1), "悬垂应在底面 z=-2"
    assert bool(np.all((sc.normals @ np.array([0, 0, 1.0])) < -0.99)), "底面法向应 ≈ -z"


def test_direction_dependence():
    """box d=+x → 取 -x 面，不含底面（S 随 d 变，§9.2）。"""
    try:
        import numpy as np
        _, _, scx = _extract([1.0, 0, 0])
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert len(scx.centroids) == 2 and np.allclose(scx.centroids[:, 0], -3.0, atol=0.1), "d=+x 应取 -x 面"
    assert not _has_bottom(scx), "d=+x 不应含底面"


def test_overhang_threshold():
    """θc=45：底面在 d 倾 30° 时悬垂、倾 60° 时非。"""
    try:
        import numpy as np
        b30 = _has_bottom(_extract([np.sin(np.radians(30)), 0, np.cos(np.radians(30))])[2])
        b60 = _has_bottom(_extract([np.sin(np.radians(60)), 0, np.cos(np.radians(60))])[2])
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert b30, "tilt30° 底面应悬垂"
    assert not b60, "tilt60° 底面应非悬垂（θc=45）"


def test_support_contact_accessible_on_box():
    """端到端：box d=+z 支撑接触点 → solidify → oracle → 全可达。"""
    try:
        ok = _end_to_end_all_accessible()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert ok, "box d=+z 支撑接触点应全可达"
