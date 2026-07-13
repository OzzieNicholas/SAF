"""指标 emitter。计时/计数是真实的（stdlib）；评价指标是待实现桩。

- 效率/预算：query_count、stage_ms —— 喂 tests/gate.py 的 oracle 预算门（D0 实测→外推）。
- 评价：不可达类 F1、不可达区域 IoU、不可达面积比例误差、方向排序相关（模型级为主）。
"""

import time
from contextlib import contextmanager

_counters = {"oracle_queries": 0}
_timings_ms = {}


def incr(name, n=1):
    _counters[name] = _counters.get(name, 0) + n


def counters():
    return dict(_counters)


@contextmanager
def stage(name):
    """计一个阶段的墙钟毫秒：with stage("oracle_label_one_dir"): ..."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        _timings_ms[name] = _timings_ms.get(name, 0.0) + (time.perf_counter() - t0) * 1000.0


def timings_ms():
    return dict(_timings_ms)


def extrapolate_oracle_cost(per_dir_ms, n_models, points_per_model, n_directions, n_radii):
    """把 D0 实测的"单点单方向 ms"外推到 MVP 规模，返回预计总小时数。预算门用。"""
    total_ms = per_dir_ms * n_models * points_per_model * n_directions * n_radii
    return total_ms / 1000.0 / 3600.0


# ---- 评价指标（不可达=风险正类；problem.md 指标口径）----
def _pos_mask(labels):
    """把标签数组归一为"不可达=正类"的 bool mask。接受 bool/int/float/str/Label。

    bool→原样；int→非0为正；float→≥0.5为正；字符串/Label→'inaccess…'为正。
    """
    import numpy as np
    a = np.asarray(labels)
    if a.dtype == bool:
        return a
    if a.dtype.kind in "iu":
        return a != 0
    if a.dtype.kind == "f":
        return a >= 0.5
    flat = [str(getattr(x, "value", x)).lower().startswith("inaccess") for x in a.ravel()]
    return np.asarray(flat, dtype=bool).reshape(a.shape)


def _check_same(p, g):
    if p.shape != g.shape:
        raise ValueError(f"pred/gold 形状不一致：{p.shape} vs {g.shape}")


def f1_inaccessible(pred, gold):
    """不可达类（风险正类）F1。pred/gold 同长标签数组（不可达=正）。两侧皆无正类 → 1.0。"""
    import numpy as np
    p, g = _pos_mask(pred), _pos_mask(gold)
    _check_same(p, g)
    tp = int(np.sum(p & g)); fp = int(np.sum(p & ~g)); fn = int(np.sum(~p & g))
    denom = 2 * tp + fp + fn
    return 1.0 if denom == 0 else 2.0 * tp / denom


def iou_inaccessible(pred_region, gold_region):
    """不可达区域 IoU（正类交并比）。并集为空（两侧皆无不可达）→ 1.0。"""
    import numpy as np
    p, g = _pos_mask(pred_region), _pos_mask(gold_region)
    _check_same(p, g)
    inter = int(np.sum(p & g)); union = int(np.sum(p | g))
    return 1.0 if union == 0 else inter / union


def inaccessible_area_error(pred_region, gold_region):
    """不可达面积比例误差 = |pred 不可达占比 − gold 不可达占比|（点按面积均匀采样时占比≈面积比）。"""
    import numpy as np
    p, g = _pos_mask(pred_region), _pos_mask(gold_region)
    if p.size != g.size:
        raise ValueError(f"pred/gold 元素数不一致：{p.size} vs {g.size}")
    if p.size == 0:
        return 0.0
    return abs(float(np.mean(p)) - float(np.mean(g)))


def summary(pred, gold):
    """一个预测器 vs gold 的指标包（不可达=正类）：{f1, iou, acc, area_err}。用于 E4 基线对照。"""
    import numpy as np
    p, g = _pos_mask(pred), _pos_mask(gold)
    return {"f1": f1_inaccessible(p, g), "iou": iou_inaccessible(p, g),
            "acc": float((p == g).mean()) if p.size else 1.0,
            "area_err": inaccessible_area_error(p, g)}
