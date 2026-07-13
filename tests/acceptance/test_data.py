"""程序化标签数据集验收：生成 → oracle 自动打标 → 按模型切分，且非退化（两类俱在）。

守护 Phase-1 数据管线：形状条件样本 (occ, 下朝接触点, 标签)，标签由 oracle 自动生成（无人工标注）；
split.by=model（禁按点切分，见 conf/params.yaml）。saf 内真跑；缺依赖 → PENDING/skip。
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
    """按模型切分，train/test 模型互斥（H3 跨模型前提）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    from support_accessibility import data as D
    tr, te = D.split_by_model(D.make_dataset(**_ARGS), frac_train=0.7, seed=0)
    assert {m.name for m in tr}.isdisjoint({m.name for m in te}) and len(te) > 0
