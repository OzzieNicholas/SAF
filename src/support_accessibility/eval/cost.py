"""运行成本：计时、计数、预算外推与数据集摘要。

- 效率/预算：query_count、stage_ms —— 喂 tests/gate.py 的 oracle 预算门（D0 实测→外推）。
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
    """输入数据集身份摘要（sha256 前 16 hex）：**只哈希各 root 的 manifest.csv**（每件 n_points/n_inaccessible→标签变必现）。
    刻意**排除 dataset.json**——它含 label_audit 会改写的 label_audit/human_signoff，避免"跑审核使回归产物假陈旧"（D-026 P5）。
    回归门据此判机器产物是否对应当前数据——不匹配 → 陈旧 → PENDING（防陈旧产物撑绿）。"""
    import hashlib
    import os
    h = hashlib.sha256()
    for root in roots:
        p = os.path.join(root, "manifest.csv")
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:16]
