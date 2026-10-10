"""程序化标签数据集验收：生成 → oracle 自动打标 → 按模型切分，且非退化（两类俱在）。

守护程序化数据管线：形状条件样本 (occ, 下朝接触点, 标签)，标签由 oracle 自动生成（无人工标注）；
split.by=model（禁按点切分，见 configs/oracle_params.yaml）。saf 内真跑；缺依赖 → PENDING/skip。
"""

from unittest import SkipTest

from . import pending, result

_ARGS = dict(n_models=12, N=28, max_points=24, radius=3.0, n_directions=32, seed=0)


def _deps():
    import numpy, scipy  # noqa: F401
    from support_accessibility import data, oracle  # noqa: F401


def checks():
    try:
        _deps()
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}") for n in
                ("dataset_shapes", "dataset_both_classes", "dataset_labels_match_oracle", "dataset_split_by_model")]
    import numpy as np
    from support_accessibility import data as D, oracle as O
    out = []
    try:
        ms = D.make_dataset(**_ARGS)
        shapes_ok = (len(ms) == _ARGS["n_models"] and
                     all(m.occ.ndim == 3 and m.points.ndim == 2 and m.points.shape[1] == 3
                         and m.points.shape[0] == m.labels.shape[0] for m in ms))
        out.append(result("dataset_shapes", shapes_ok, f"{len(ms)} 件：(occ,points,labels) 自洽"))

        alllab = np.concatenate([m.labels for m in ms])
        both = bool(alllab.any() and (~alllab).any())
        out.append(result("dataset_both_classes", both,
                           f"不可达 {int(alllab.sum())}/{alllab.size}（两类俱在→非退化学习问题）"))

        m0 = next((m for m in ms if m.labels.any()), ms[0])   # 取含不可达的件，复算覆盖风险正类
        o = O.SupportAccessibilityOracle(m0.occ, {"n_directions": _ARGS["n_directions"]})
        recomputed = np.array([o.label(p, m0.radius).value == "inaccessible" for p in m0.points])
        out.append(result("dataset_labels_match_oracle", bool(np.array_equal(recomputed, m0.labels)),
                           f"{m0.name}: 标签逐点复算=oracle（含 {int(m0.labels.sum())} 不可达）"))

        tr, te = D.split_by_model(ms, frac_train=0.7, seed=_ARGS["seed"])
        ntr, nte = {m.name for m in tr}, {m.name for m in te}
        split_ok = ntr.isdisjoint(nte) and len(tr) + len(te) == len(ms) and len(te) > 0
        out.append(result("dataset_split_by_model", split_ok, f"train{len(tr)}/test{len(te)}：模型级无泄漏"))

        fa, fb = D.flagship_pair(support_area_target=64, cavity_depth_a=4, cavity_depth_b=16)   # 面积与可达性的解耦存在性
        na, nb = fa.points.shape[0], fb.points.shape[0]
        acc_a, acc_b = 1.0 - fa.labels.mean(), 1.0 - fb.labels.mean()
        fp_ok = abs(na - nb) <= max(2, 0.15 * max(na, nb)) and acc_a >= 0.8 and acc_b <= 0.2
        out.append(result("flagship_pair_area_perp_access", bool(fp_ok),
                          f"面积与可达性的解耦：面积 {na}≈{nb} 相等，可达率 a={acc_a:.2f} vs b={acc_b:.2f}（面积⊥可达）"))
    except Exception as e:
        out.append(result("dataset_shapes", False, f"异常：{e}"))
    return out


def test_dataset_non_degenerate():
    """数据集两类俱在、形状自洽（否则不是可学习问题）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    import numpy as np
    from support_accessibility import data as D
    ms = D.make_dataset(**_ARGS)
    assert len(ms) == _ARGS["n_models"]
    alllab = np.concatenate([m.labels for m in ms])
    assert alllab.any() and (~alllab).any(), "数据集退化：只有一类"
    for m in ms:
        assert m.points.shape[0] == m.labels.shape[0] and m.points.shape[1] == 3


def test_split_by_model_no_leakage():
    """按模型切分，train/test 模型互斥（跨模型预测跨模型前提）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    from support_accessibility import data as D
    tr, te = D.split_by_model(D.make_dataset(**_ARGS), frac_train=0.7, seed=0)
    assert {m.name for m in tr}.isdisjoint({m.name for m in te}) and len(te) > 0


def test_flagship_pair_equal_area_opposite_access():
    """面积与可达性的解耦存在性旗舰对：支撑面积（下朝接触点数）近似相等，但可达性相反——证"面积⊥可达"。
    补支撑面积与可达性弱相关统计（|ρ|≤0.27）的存在性证据：a=开阔悬空 ledge（可达）vs b=深窄槽腔顶（不可达），同面积。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    from support_accessibility.data import flagship_pair
    a, b = flagship_pair(support_area_target=64, cavity_depth_a=4, cavity_depth_b=16)
    na, nb = a.points.shape[0], b.points.shape[0]
    assert na > 0 and nb > 0, f"接触点空：{na},{nb}"
    assert abs(na - nb) <= max(2, 0.15 * max(na, nb)), f"支撑面积不近似相等：{na} vs {nb}"
    acc_a, acc_b = 1.0 - a.labels.mean(), 1.0 - b.labels.mean()
    assert acc_a >= 0.8, f"a（开阔 ledge）应多可达，实得可达率 {acc_a:.2f}"
    assert acc_b <= 0.2, f"b（深窄腔）应多不可达，实得可达率 {acc_b:.2f}"
