"""方向级可达性场（方向级场 / D-024）——oracle 把点级二分扩为每逼近方向可达性向量。

冻结口径（D-024，extend D-004）：dir i 可达 ⟺ 工具球沿 dir i 能到 p（同 D-001..D-003 判据，只是不 OR 归约）。
**核心不变量**：any(direction_labels) == (label == ACCESSIBLE) —— 二分口径 D-004 是本场的 any-归约，未变。
无网格 → 逐方向二分（c_i>r）；有网格 → 逐方向三态（clear / 含糊交精确细化 / blocked）。纯 numpy/scipy。
"""
from unittest import SkipTest

from . import pending, result


def _np():
    try:
        import numpy  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"numpy 未就绪：{e}")


def checks():
    """gate 集成：方向级场的判定逻辑 + OR-归约不变量 + 盲腔/开阔已知答案。"""
    try:
        import numpy as np
        from support_accessibility.oracle import (SupportAccessibilityOracle, decide_direction_labels,
                                                  decide_label, Label)
        from support_accessibility.data import blind_cavity_case, open_downface_case
    except ImportError as e:
        return [pending("direction_field", f"依赖未就绪：{e}", "D-024")]
    try:
        # 逐方向判定逻辑（无网格二分 + 有网格三态）
        dl_nomesh = decide_direction_labels([5., 2, 1], 3., 1., refine=None)
        ok_nomesh = list(map(bool, dl_nomesh)) == [True, False, False]
        dl_amb = decide_direction_labels([3.2, 3.1, 0.5], 3., 0.5, refine=lambda i: i == 1)
        ok_amb = list(map(bool, dl_amb)) == [False, True, False]
        # OR-归约不变量 + 已知答案（盲腔全不可达 / 开阔有可达方向）
        bc = blind_cavity_case(); od = open_downface_case()
        inv_ok = True
        for cse in (bc, od):
            o = SupportAccessibilityOracle(cse.occ, {"n_directions": 64})
            df = o.direction_labels(cse.point, cse.radius)
            inv_ok &= (bool(df.any()) == (o.label(cse.point, cse.radius) == Label.ACCESSIBLE))
        bc_o = SupportAccessibilityOracle(bc.occ, {"n_directions": 64})
        od_o = SupportAccessibilityOracle(od.occ, {"n_directions": 64})
        known_ok = (not bc_o.direction_labels(bc.point, bc.radius).any()      # 盲腔顶：无方向可达
                    and od_o.direction_labels(od.point, od.radius).any())     # 开阔面：有方向可达
        return [
            result("direction_decide_logic", bool(ok_nomesh and ok_amb), "逐方向二分 + 三态含糊细化", "D-024"),
            result("direction_field_or_reduces_to_binary", bool(inv_ok), "any(方向场)==二分 label（D-004 是 any-归约）", "D-024"),
            result("direction_field_known_answers", bool(known_ok), "盲腔顶无方向可达 / 开阔面有方向可达", "D-024"),
        ]
    except Exception as e:
        return [result("direction_field", False, f"异常：{e}", "D-024")]


def test_decide_direction_labels_nomesh_binary():
    """无网格（refine=None）→ 逐方向二分 c_i>r。"""
    _np()
    from support_accessibility.oracle import decide_direction_labels
    dl = decide_direction_labels([5.0, 2.0, 1.0], r=3.0, eps=1.0, refine=None)
    assert list(map(bool, dl)) == [True, False, False], list(map(bool, dl))


def test_decide_direction_labels_ambiguous_refine():
    """有网格：含糊方向（r-ε<c≤r+ε）逐个交精确 refine 定夺；明确 clear（c>r+ε）直接可达。"""
    _np()
    from support_accessibility.oracle import decide_direction_labels
    dl = decide_direction_labels([3.2, 3.1, 0.5], r=3.0, eps=0.5, refine=lambda i: i == 1)
    assert list(map(bool, dl)) == [False, True, False], list(map(bool, dl))
    dl2 = decide_direction_labels([5.0, 3.1, 0.5], r=3.0, eps=0.5, refine=lambda i: False)
    assert list(map(bool, dl2)) == [True, False, False], list(map(bool, dl2))   # 5>3.5 clear，含糊 refine False


def test_direction_field_or_reduces_to_binary():
    """核心不变量：any(direction_labels) == (label==ACCESSIBLE)。二分口径 D-004 是本场的 any-归约。"""
    _np()
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle, Label
    from support_accessibility.data import blind_cavity_case, open_downface_case, slab_with_blind_hole, down_facing_points
    for cse in (blind_cavity_case(), open_downface_case()):
        o = SupportAccessibilityOracle(cse.occ, {"n_directions": 64})
        assert bool(o.direction_labels(cse.point, cse.radius).any()) == (o.label(cse.point, cse.radius) == Label.ACCESSIBLE)
    # 多点批量：混合腔（宽腔可达点 + 窄腔不可达点）逐点 OR-归约一致
    occ = slab_with_blind_hole(28, opening=3, depth=10)
    o = SupportAccessibilityOracle(occ, {"n_directions": 64})
    for p in down_facing_points(occ):
        assert bool(o.direction_labels(p, 3.0).any()) == (o.label(p, 3.0) == Label.ACCESSIBLE)


def test_convonet_out_dim_direction_head():
    """ConvONet-lite 方向级输出头（方向级场）：out_dim=D → 每点 D 个 logit [N,D]；out_dim=1 → [N]（向后兼容跨模型预测/跨域鲁棒性）。

    验收层设计上无 torch（gate 零安装、torch 模型经 tools/ 验证）；本 torch 断言仅在能干净加载 torch 的
    进程跑（隔离/CI）。满载进程里 torch fbgemm.dll 偶发 WinError 127（Windows DLL 顺序脆性）→ 归为不可用而 skip；
    out_dim 契约另由 experiments/direction_field_prediction.py 实跑（out_dim=64 出 [N,64]）覆盖。
    """
    try:
        import torch
    except (ImportError, OSError) as e:                 # OSError=torch 原生 DLL 满载进程加载失败（见 docstring）
        raise SkipTest(str(e))
    import numpy as np
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    occ = torch.zeros(1, 1, 8, 8, 8); occ[0, 0, 3:6, 3:6, 3:6] = 1.0
    gc = to_grid_coords(np.array([[2., 2, 2], [4, 4, 4], [5, 5, 5]]), (8, 8, 8))
    assert tuple(ConvONetLite(out_dim=1)(occ, gc).shape) == (3,)         # 向后兼容
    assert tuple(ConvONetLite(out_dim=5)(occ, gc).shape) == (3, 5)       # 方向级 [N,D]


def test_direction_field_known_answers():
    """盲腔顶：无逼近方向可达（全 False）；开阔下朝面：有可达方向（非全 False）。"""
    _np()
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.data import blind_cavity_case, open_downface_case
    bc, od = blind_cavity_case(), open_downface_case()
    assert not SupportAccessibilityOracle(bc.occ, {"n_directions": 64}).direction_labels(bc.point, bc.radius).any()
    assert SupportAccessibilityOracle(od.occ, {"n_directions": 64}).direction_labels(od.point, od.radius).any()
