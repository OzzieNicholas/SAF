"""网格前端验收：真实网格 → igl solidify → occupancy → oracle，复现已知答案。

守护 mesh 前端口径（D-007 选 igl / D-009 本片口径）。在 saf（igl/trimesh/scipy）内真跑；
依赖缺失 → PENDING/skip。双重锚定：① solidify 占据与解析盒 IoU≈1；② 两条已知答案在真实网格上复现。
"""

from unittest import SkipTest

from . import pending, result

_RES = 48
_NDIR = 64


def _label_case(case):
    """MeshCase → solidify → oracle.label → 实得标签字符串。"""
    from support_accessibility.data import mesh as M
    from support_accessibility.oracle import SupportAccessibilityOracle
    occ, lo, pitch = M.mesh_to_occupancy(case.V, case.F, resolution=_RES)
    p = M.world_to_voxel(case.point_world, lo, pitch)
    r = case.radius_world / pitch
    return SupportAccessibilityOracle(occ, {"n_directions": _NDIR}).label(p, r).value


def _solidify_box_iou():
    """box solidify 占据 vs 解析盒 IoU。"""
    import numpy as np
    from support_accessibility.data import mesh as M
    V, F = M.box_vf((6.0, 6.0, 4.0))
    occ, lo, pitch = M.mesh_to_occupancy(V, F, resolution=_RES)
    ax = [lo[i] + (np.arange(occ.shape[i]) + 0.5) * pitch for i in range(3)]
    gx, gy, gz = np.meshgrid(*ax, indexing="ij")
    ana = (np.abs(gx) <= 3.0) & (np.abs(gy) <= 3.0) & (np.abs(gz) <= 2.0)
    return float((occ & ana).sum() / (occ | ana).sum())


def checks():
    try:
        import numpy, igl, trimesh  # noqa: F401
        from support_accessibility.data import mesh as M
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", d) for n, d in
                (("mesh_solidify_box", "D-007/D-009"),
                 ("mesh_box_downface", "D-002"),
                 ("mesh_two_box_gap", "D-001"))]
    out = []
    try:
        iou = _solidify_box_iou()
        out.append(result("mesh_solidify_box", iou >= 0.97, f"box solidify IoU={iou:.3f}", "D-007/D-009"))
    except Exception as e:
        out.append(result("mesh_solidify_box", False, f"异常：{e}", "D-007/D-009"))
    for case_fn, name, dec in ((M.box_downface_case, "mesh_box_downface", "D-002"),
                               (M.two_box_gap_case, "mesh_two_box_gap", "D-001")):
        try:
            case = case_fn()
            got = _label_case(case)
            out.append(result(name, got == case.expected, f"期望={case.expected} 实得={got}", dec))
        except Exception as e:
            out.append(result(name, False, f"异常：{e}", dec))
    return out


def test_solidify_box():
    """igl solidify 的占据与解析盒一致（IoU≈1）。"""
    try:
        iou = _solidify_box_iou()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert iou >= 0.97, f"solidify IoU={iou:.3f} 偏低"


def test_box_downface_accessible():
    """真实盒下朝面 → 可达（D-002）。"""
    try:
        from support_accessibility.data import mesh as M
        got = _label_case(M.box_downface_case())
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == "accessible", f"盒下朝面应可达，实得 {got}"


def test_gap_inaccessible():
    """两盒窄间隙 → 不可达（D-001 confinement）。"""
    try:
        from support_accessibility.data import mesh as M
        got = _label_case(M.two_box_gap_case())
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == "inaccessible", f"窄间隙应不可达，实得 {got}"
