"""指标验收：不可达类 F1 / 区域 IoU / 面积比例误差 —— 已知输入→已知输出（评分 emitter 有牙）。

守护 problem.md 指标口径（不可达=风险正类）。纯 numpy；缺依赖 → PENDING（gate）/ SkipTest（pytest）。
"""

from unittest import SkipTest

from . import pending, result


def _cases():
    """(名, 通过?, 详情) —— 手算真值锚定三指标。"""
    import numpy as np
    from support_accessibility import eval as E
    T, F = True, False
    g = np.array([T, T, F, F, T])          # gold 正类(不可达) at 0,1,4
    p_mix = np.array([T, T, T, F, F])      # pred 正类 at 0,1,2 → tp{0,1}=2 fp{2}=1 fn{4}=1
    p_neg = np.array([F, F, F, F, F])
    # 方向排序（E5 / D-024）：scores(N,D) 可达性打分（高=更可达），viable(N,D) oracle 可达方向
    scr = np.array([[3., 1, 2], [1, 3, 2]]); via = np.array([[T, F, F], [F, T, F]])   # 每点 top-1 即 viable
    scr1 = np.array([[3., 1, 2]]); via1 = np.array([[F, F, T]])                       # top-1 非 viable、top-2 含
    scrB = np.array([[1., 2, 3], [3, 2, 1]]); viaB = np.array([[F, F, F], [T, F, F]])  # point0 全挡→排除
    return [
        ("f1_perfect", abs(E.f1_inaccessible(g, g) - 1.0) < 1e-9, "完美预测 F1=1"),
        ("f1_all_negative", E.f1_inaccessible(p_neg, g) == 0.0, "全判可达 → 漏报正类 F1=0"),
        ("f1_known_mix", abs(E.f1_inaccessible(p_mix, g) - 4.0 / 6) < 1e-9, "tp2/fp1/fn1 → F1=2/3"),
        ("f1_empty_both", E.f1_inaccessible(p_neg, p_neg) == 1.0, "两侧无正类 → F1=1"),
        ("iou_identical", E.iou_inaccessible(g, g) == 1.0, "同 mask IoU=1"),
        ("iou_disjoint", E.iou_inaccessible(np.array([T, F, F]), np.array([F, T, F])) == 0.0, "不交 IoU=0"),
        ("iou_known", abs(E.iou_inaccessible(p_mix, g) - 0.5) < 1e-9, "交2/并4 → IoU=0.5"),
        ("area_err_known", abs(E.inaccessible_area_error(p_neg, g) - 0.6) < 1e-9, "|0−0.6|=0.6"),
        ("area_err_zero", E.inaccessible_area_error(g, g) == 0.0, "同→0"),
        ("topk_hit_top1", E.topk_direction_hit_rate(scr, via, 1) == 1.0, "每点 top-1 即 viable → 命中率 1"),
        ("topk_hit_miss", E.topk_direction_hit_rate(scr1, via1, 1) == 0.0, "top-1 非 viable → 0"),
        ("topk_hit_k2", E.topk_direction_hit_rate(scr1, via1, 2) == 1.0, "top-2 含 viable → 1"),
        ("topk_prec_k2", abs(E.topk_direction_precision(scr1, via1, 2) - 0.5) < 1e-9, "top-2 中 1/2 viable"),
        ("topk_excl_blocked", E.topk_direction_hit_rate(scrB, viaB, 1) == 1.0, "全挡点排除、余点 top-1 命中"),
        ("spearman_monotone", abs(E.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9, "完全单调升 ρ=1"),
        ("spearman_inverse", abs(E.spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-9, "完全反序 ρ=-1"),
        ("spearman_ties", abs(E.spearman([1, 1, 2, 2], [1, 2, 1, 2]) - 0.0) < 1e-9, "并列取平均秩、正交 ρ=0"),
        ("spearman_degenerate", E.spearman([1, 1, 1], [1, 2, 3]) == 0.0, "一侧零方差 → ρ=0"),
    ]


def checks():
    try:
        import numpy  # noqa: F401
        from support_accessibility import eval  # noqa: F401
    except ImportError as e:
        return [pending("eval_metrics", f"依赖未就绪：{e}")]
    try:
        return [result(nm, ok, det) for nm, ok, det in _cases()]
    except Exception as e:
        return [result("eval_metrics", False, f"异常：{e}")]


def test_eval_metrics():
    try:
        import numpy  # noqa: F401
        from support_accessibility import eval  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    for nm, ok, det in _cases():
        assert ok, f"{nm}: {det}"
