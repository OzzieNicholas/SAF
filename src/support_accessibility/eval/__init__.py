"""指标 emitter。计时/计数真实（stdlib）；评价指标已实现（已知答案锚定 test_eval）。

- 效率/预算：query_count、stage_ms —— 喂 tests/gate.py 的 oracle 预算门（D0 实测→外推）。
- 评价：不可达类 F1、不可达区域 IoU、不可达面积比例误差、**方向排序 Top-k 命中/precision@k**（E5/D-024，模型级为主）。
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


def data_digest(*roots):
    """输入数据集身份摘要（sha256 前 16 hex）：拼接各 root 的 dataset.json + manifest.csv 字节。
    回归门用它判机器产物是否对应当前数据——不匹配 → 陈旧产物 → PENDING（防陈旧产物撑绿，D-026）。"""
    import hashlib
    import os
    h = hashlib.sha256()
    for root in roots:
        for fn in ("dataset.json", "manifest.csv"):
            p = os.path.join(root, fn)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    h.update(f.read())
    return h.hexdigest()[:16]


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
    """不可达**点占比**误差 = |pred 不可达点占比 − gold 不可达点占比|。

    注：这是点占比误差；仅当点集**按面积均匀采样**时才≈面积比例误差，而当前 ingest（逐三角质心 / 分层体素）
    不满足该假设（真面积口径见 conf/params.yaml sampling 注 + eval_h1 说明）。数值本身有效（同点集 pred vs gold），
    只是"面积"解读不成立。形状校验对齐 f1/iou（`_check_same`）。"""
    import numpy as np
    p, g = _pos_mask(pred_region), _pos_mask(gold_region)
    _check_same(p, g)
    if p.size == 0:
        return 0.0
    return abs(float(np.mean(p)) - float(np.mean(g)))


# ---- 方向排序指标（E5 / D-024；problem.md「方向排序相关 Top-k」）----
def _rank_inputs(scores, viable):
    import numpy as np
    S = np.asarray(scores, float)
    V = np.asarray(viable, bool)
    if S.shape != V.shape:
        raise ValueError(f"scores/viable 形状不一致：{S.shape} vs {V.shape}")
    if S.ndim != 2:
        raise ValueError(f"需 (N,D) 二维，实得 {S.shape}")
    return S, V


def topk_direction_hit_rate(scores, viable, k=1):
    """方向排序 Top-k 命中率：每点按 scores 降序取前 k 个方向，其中≥1 个 oracle-viable 即命中；
    在**有≥1 可达方向**的点上取均值（全挡点无排序意义、单列比例）。scores/viable=(N,D)。无可排序点→1.0。

    问的是「模型能否在最有把握的 k 个方向里给出一个真能到达的逼近方向」（DfAM 实用：推荐进刀方向）。
    """
    import numpy as np
    S, V = _rank_inputs(scores, viable)
    ranked = V.any(axis=1)
    if not ranked.any():
        return 1.0
    k = max(1, min(int(k), S.shape[1]))
    topk = np.argsort(-S, axis=1)[:, :k]
    hit = np.take_along_axis(V, topk, axis=1).any(axis=1)
    return float(hit[ranked].mean())


def topk_direction_precision(scores, viable, k=3):
    """方向排序 precision@k：每点 top-k 方向中 oracle-viable 的比例，在有≥1 可达方向的点上取均值。"""
    import numpy as np
    S, V = _rank_inputs(scores, viable)
    ranked = V.any(axis=1)
    if not ranked.any():
        return 1.0
    k = max(1, min(int(k), S.shape[1]))
    topk = np.argsort(-S, axis=1)[:, :k]
    prec = np.take_along_axis(V, topk, axis=1).mean(axis=1)
    return float(prec[ranked].mean())


def spearman(x, y):
    """Spearman 秩相关 ρ（纯 numpy：秩化后 Pearson，避开 scipy.stats 的 OMP 冲突）。
    并列用平均秩。样本 <2 或某侧零方差 → 0.0（无相关/退化）。用于 H1（支撑面积⊥可达）+ 方向排序相关。"""
    import numpy as np
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.size != y.size:
        raise ValueError(f"x/y 长度不一：{x.size} vs {y.size}")
    if x.size < 2:
        return 0.0

    def _rank(a):
        order = np.argsort(a, kind="mergesort")
        r = np.empty(a.size, float); r[order] = np.arange(a.size, dtype=float)
        # 并列取平均秩
        _, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
        sums = np.zeros(cnt.size); np.add.at(sums, inv, r)
        return (sums / cnt)[inv]
    rx, ry = _rank(x), _rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def summary(pred, gold):
    """一个预测器 vs gold 的指标包（不可达=正类）：{f1, iou, acc, area_err}。用于 E4 基线对照。"""
    import numpy as np
    p, g = _pos_mask(pred), _pos_mask(gold)
    return {"f1": f1_inaccessible(p, g), "iou": iou_inaccessible(p, g),
            "acc": float((p == g).mean()) if p.size else 1.0,
            "area_err": inaccessible_area_error(p, g)}
