"""形状条件预测验收（Phase-1 薄纵切端到端）：在**未见模型**上预测支撑接触点可达性。

守护论文头号命题 H3（跨模型预测成立）的可行性：程序化件 → oracle 打标 → 训 tiny 模型 →
在**按模型切分的留出件**上评分，须显著胜过多数类基线。saf 内真跑；缺依赖 → PENDING/skip。

注：tiny numpy 模型只为 derisk 管线（云端无 torch）；真实 ConvONet/PyTorch 属 Phase-3。
留出 F1 实测稳定 ≈1.0（见提交说明），故 0.6 是带大余量的鲁棒下限，抗跨平台数值差。
"""

from unittest import SkipTest

from . import pending, result

_ARGS = dict(n_models=24, N=28, max_points=24, radius=3.0, n_directions=32, seed=0)
_EPOCHS = 200
_F1_BAR = 0.6


def _deps():
    import numpy, scipy  # noqa: F401
    from support_accessibility import data, models, eval  # noqa: F401


def _train_eval():
    import numpy as np
    from support_accessibility import data as D, models as M, eval as E
    ms = D.make_dataset(**_ARGS)
    tr, te = D.split_by_model(ms, frac_train=0.7, seed=_ARGS["seed"])
    mdl = M.train(tr, epochs=_EPOCHS, seed=_ARGS["seed"])
    pte = np.concatenate([M.predict(mdl, m.occ, m.points) for m in te if m.points.shape[0] > 0])
    gte = np.concatenate([np.asarray(m.labels, bool) for m in te if m.points.shape[0] > 0])
    base = np.zeros_like(gte)                       # 多数类基线：全判可达
    return dict(f1=E.f1_inaccessible(pte, gte), iou=E.iou_inaccessible(pte, gte),
                acc=float((pte == gte).mean()), base_f1=E.f1_inaccessible(base, gte),
                base_acc=float((base == gte).mean()), pos=int(gte.sum()), tot=int(gte.size),
                ntr=len(tr), nte=len(te))


def checks():
    try:
        _deps()
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}") for n in ("model_cross_model_f1", "model_beats_baseline")]
    try:
        r = _train_eval()
        out = [result("model_cross_model_f1", r["f1"] >= _F1_BAR,
                      f"留出({r['nte']}件未见) 不可达 F1={r['f1']:.3f} IoU={r['iou']:.3f} acc={r['acc']:.3f}（≥{_F1_BAR}）")]
        beats = r["f1"] > r["base_f1"] and r["acc"] > r["base_acc"]
        out.append(result("model_beats_baseline", beats,
                          f"F1 {r['f1']:.3f}>基线{r['base_f1']:.3f}、acc {r['acc']:.3f}>{r['base_acc']:.3f}（正类 {r['pos']}/{r['tot']}）"))
        return out
    except Exception as e:
        return [result("model_cross_model_f1", False, f"异常：{e}")]


def test_model_generalizes_cross_model():
    """未见模型上不可达 F1 达标且胜过多数类基线（H3 可行性）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    r = _train_eval()
    assert r["f1"] >= _F1_BAR, f"留出 F1={r['f1']:.3f} < {_F1_BAR}"
    assert r["f1"] > r["base_f1"] and r["acc"] > r["base_acc"], \
        f"未胜基线：F1 {r['f1']:.3f} vs {r['base_f1']:.3f}，acc {r['acc']:.3f} vs {r['base_acc']:.3f}"
