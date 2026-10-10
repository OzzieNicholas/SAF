"""网格前端验收：真实网格 → igl solidify → occupancy → oracle，复现已知答案。

守护 mesh 前端口径（D-009）。在 saf（igl/trimesh/scipy）内真跑；
依赖缺失 → PENDING/skip。双重锚定：① solidify 占据与解析盒 IoU≈1；② 两条已知答案在真实网格上复现。
"""

from unittest import SkipTest

from . import pending, result
from tests.fixtures import known_answer_meshes as K

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
    V, F = K.box_vf((6.0, 6.0, 4.0))
    occ, lo, pitch = M.mesh_to_occupancy(V, F, resolution=_RES)
    ax = [lo[i] + (np.arange(occ.shape[i]) + 0.5) * pitch for i in range(3)]
    gx, gy, gz = np.meshgrid(*ax, indexing="ij")
    ana = (np.abs(gx) <= 3.0) & (np.abs(gy) <= 3.0) & (np.abs(gz) <= 2.0)
    return float((occ & ana).sum() / (occ | ana).sum())


def _nudge_cases_ok():
    """nudge_to_free 三态 + 栅格外（D-028）。lo=0/pitch=1 → 体素索引=floor(world)。"""
    import numpy as np
    from support_accessibility.data import mesh as M
    lo = (0., 0, 0); pitch = 1.0
    free = np.zeros((5, 5, 5), bool); free[:, :, 3] = True            # 天花板在 z=3，c 下方自由
    s_free = M.nudge_to_free(free, (2.5, 2.5, 2.5), (0, 0, -1), 1.0, lo, pitch)[0] == "free"
    below = np.zeros((5, 5, 5), bool); below[:, :, 1] = True          # 实体在下 → +n 落实体、−n 自由 = 翻面
    s_flip = M.nudge_to_free(below, (2.5, 2.5, 2.5), (0, 0, -1), 1.0, lo, pitch) == ("flipped", None)
    both = np.zeros((5, 5, 5), bool); both[:, :, 1] = True; both[:, :, 3] = True   # 上下皆实体 = 窄隙
    s_conf = M.nudge_to_free(both, (2.5, 2.5, 2.5), (0, 0, -1), 1.0, lo, pitch)[0] == "confined"
    s_oob = M.nudge_to_free(np.zeros((5, 5, 5), bool), (2.5, 2.5, 0.5), (0, 0, -1), 2.0, lo, pitch)[0] == "free"  # 出界=自由
    return bool(s_free and s_flip and s_conf and s_oob)


def _occ_ceil_shape_ok():
    """立方体 mesh at res R → occ.shape 各轴 = R（ceil 修正防最大轴过冲 R+1；D-028 extend D-009）。"""
    from support_accessibility.data import mesh as M
    V, F = K.box_vf((4.0, 4.0, 4.0))
    occ, _lo, _pitch = M.mesh_to_occupancy(V, F, resolution=_RES)
    return occ.shape == (_RES, _RES, _RES)


def checks():
    try:
        import numpy, igl, trimesh  # noqa: F401
        from support_accessibility.data import mesh as M
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", d) for n, d in
                (("mesh_solidify_box", "D-009"),
                 ("mesh_box_downface", "D-002"),
                 ("mesh_two_box_gap", "D-001"),
                 ("mesh_nudge_to_free", "D-028"),
                 ("mesh_occ_ceil_shape", "D-028"))]
    out = []
    try:
        iou = _solidify_box_iou()
        out.append(result("mesh_solidify_box", iou >= 0.97, f"box solidify IoU={iou:.3f}", "D-009"))
    except Exception as e:
        out.append(result("mesh_solidify_box", False, f"异常：{e}", "D-009"))
    for case_fn, name, dec in ((K.box_downface_case, "mesh_box_downface", "D-002"),
                               (K.two_box_gap_case, "mesh_two_box_gap", "D-001")):
        try:
            case = case_fn()
            got = _label_case(case)
            out.append(result(name, got == case.expected, f"期望={case.expected} 实得={got}", dec))
        except Exception as e:
            out.append(result(name, False, f"异常：{e}", dec))
    try:
        out.append(result("mesh_nudge_to_free", _nudge_cases_ok(),
                          "缠绕安全外移三态 free/flipped/confined + 栅格外=自由（D-028 extend D-010）", "D-028"))
        out.append(result("mesh_occ_ceil_shape", _occ_ceil_shape_ok(),
                          f"立方体 occ.shape=({_RES},{_RES},{_RES})（ceil 无过冲，D-028 extend D-009）", "D-028"))
    except Exception as e:
        out.append(result("mesh_nudge_to_free", False, f"异常：{e}", "D-028"))
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
        got = _label_case(K.box_downface_case())
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == "accessible", f"盒下朝面应可达，实得 {got}"


def test_gap_inaccessible():
    """两盒窄间隙 → 不可达（D-001 confinement）。"""
    try:
        from support_accessibility.data import mesh as M
        got = _label_case(K.two_box_gap_case())
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == "inaccessible", f"窄间隙应不可达，实得 {got}"


def test_nudge_to_free_three_state():
    """缠绕安全外移三态：free/flipped(弃)/confined(留) + 栅格外=自由（D-028 extend D-010）。"""
    try:
        import numpy  # noqa: F401
    except ImportError as e:
        raise SkipTest(str(e))
    assert _nudge_cases_ok()


def test_occ_ceil_shape_no_overshoot():
    """立方体 mesh → occ.shape 无 ceil 过冲（各轴=res，D-028 extend D-009）。"""
    try:
        import igl  # noqa: F401
    except ImportError as e:
        raise SkipTest(str(e))
    assert _occ_ceil_shape_ok()
