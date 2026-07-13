"""基线对照验收（H2 + E4）：证明工具尺寸不可忽略、神经胜纯可见性/多数类基线。

守护论文立论（docs §8 / E4 / H2）：几何启发式居对照位（D-015）。留出（未见）模型上——
  H2：存在"射线可见(r=0 可达) 但工具够不到(r>0 不可达)"的点 ⇒ 工具尺寸不可忽略。
  E4：神经预测显著胜"无工具半径射线可见性"与"多数类"基线。
诚实记录：局部规则基线在当前**易件**上与神经相当（局部可分）——待更硬/非局部件区分（Phase-2 后续）。
saf 内真跑；缺依赖 → PENDING/skip。
"""

from unittest import SkipTest

from . import pending, result

_ARGS = dict(n_models=24, N=28, max_points=24, radius=3.0, n_directions=32, seed=0)
_EPOCHS = 200
_H2_MIN = 0.05        # H2 材料下限（实测 ≈0.16）
_MARGIN = 0.15        # 神经胜射线可见性的稳健余量（实测 1.0 vs 0.64）


def _deps():
    import numpy, scipy  # noqa: F401
    from support_accessibility import data, models, eval, baselines  # noqa: F401


def _run():
    import numpy as np
    from support_accessibility import data as D, models as M, eval as E, baselines as B
    ms = D.make_dataset(**_ARGS)
    tr, te = D.split_by_model(ms, frac_train=0.7, seed=_ARGS["seed"])
    mdl = M.train(tr, epochs=_EPOCHS, seed=_ARGS["seed"])
    te = [m for m in te if m.points.shape[0] > 0]
    gold = np.concatenate([np.asarray(m.labels, bool) for m in te])
    neural = np.concatenate([M.predict(mdl, m.occ, m.points) for m in te])
    rayvis = np.concatenate([B.ray_visibility(m.occ, m.points, _ARGS["n_directions"]) for m in te])
    localr = np.concatenate([B.local_solid_rule(m.occ, m.points) for m in te])
    maj = B.predict_majority(gold.size, B.majority_label(tr))
    ray_visible_blocked = float((~rayvis & gold).mean())       # r=0 可达 但 gold 不可达
    return dict(gold=gold, h2=ray_visible_blocked,
                neural=E.summary(neural, gold)["f1"], rayvis=E.summary(rayvis, gold)["f1"],
                localr=E.summary(localr, gold)["f1"], majority=E.summary(maj, gold)["f1"],
                pos=int(gold.sum()), tot=int(gold.size))


def checks():
    try:
        _deps()
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}") for n in
                ("h2_tool_radius_matters", "e4_neural_beats_ray_visibility", "e4_neural_beats_majority")]
    try:
        r = _run()
        return [
            result("h2_tool_radius_matters", r["h2"] >= _H2_MIN,
                   f"射线可见但工具够不到 {r['h2']*100:.0f}%（≥{_H2_MIN*100:.0f}%）→ 工具尺寸不可忽略"),
            result("e4_neural_beats_ray_visibility", r["neural"] >= r["rayvis"] + _MARGIN,
                   f"神经 F1={r['neural']:.3f} vs 射线可见性 {r['rayvis']:.3f}（余量≥{_MARGIN}；局部规则 {r['localr']:.3f} 当前易件持平）"),
            result("e4_neural_beats_majority", r["neural"] >= r["majority"] + 0.3,
                   f"神经 F1={r['neural']:.3f} vs 多数类 {r['majority']:.3f}（正类 {r['pos']}/{r['tot']}）"),
        ]
    except Exception as e:
        return [result("h2_tool_radius_matters", False, f"异常：{e}")]


def test_tool_radius_matters_h2():
    """存在射线可见但工具够不到的点（H2：工具尺寸不可忽略）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    r = _run()
    assert r["h2"] >= _H2_MIN, f"H2 材料不足：射线可见但工具够不到仅 {r['h2']*100:.1f}%"


def test_neural_beats_visibility_and_majority_e4():
    """神经预测胜纯射线可见性与多数类基线（E4）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    r = _run()
    assert r["neural"] >= r["rayvis"] + _MARGIN, f"神经 {r['neural']:.3f} 未显著胜射线可见性 {r['rayvis']:.3f}"
    assert r["neural"] >= r["majority"] + 0.3, f"神经 {r['neural']:.3f} 未胜多数类 {r['majority']:.3f}"
