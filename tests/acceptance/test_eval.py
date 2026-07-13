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
