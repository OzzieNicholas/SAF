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


# ---- 评价指标（待实现；不可达=风险正类）----
def f1_inaccessible(pred, gold):
    raise NotImplementedError("f1_inaccessible 待实现（阶段5指标固化前）。")


def iou_inaccessible(pred_region, gold_region):
    raise NotImplementedError("iou_inaccessible 待实现。")


def inaccessible_area_error(pred_region, gold_region):
    raise NotImplementedError("inaccessible_area_error 待实现。")
