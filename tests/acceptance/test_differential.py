"""差分对拍（D-003/D-025）：体素腐蚀口径 vs 暴力参考。

快实现（EDT 最近体素采样）与慢参考（连续采样点到实体体素中心的距离）使用同一方向集和
ray-march 步长，但仍是两种离散近似。D-025 因而冻结批量审核口径：在 r±epsilon 的操作性
邻域检查后，robust 不一致率不得超过 1%，而不是要求任意单个随机 occupancy 必须零不一致。
固定反例 seed=882 被强制纳入批量样本，避免用随机性隐藏已知近似差异。需 numpy + oracle。
"""

from unittest import SkipTest

from . import pending, result

_EPS = 0.75          # 边界邻域（体素）
_NDIR = 32           # 控时
_N_CASES = 1000      # 批量性质需要稳定分母；运行约 1--2 s
_MAX_ROBUST_RATE = 0.01  # D-025


def _check_one(o, p, r):
    """(ok, exact)：exact=严格一致；ok=一致或可容忍的边界。"""
    if o.label(p, r).value == o.reference_label(p, r).value:
        return True, True
    boundary = all(o.label(p, r + d).value == o.reference_label(p, r + d).value
                   for d in (-_EPS, _EPS))
    return boundary, False


def _gen_cases(n, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    for _ in range(n):
        N = int(rng.integers(14, 19))
        occ = rng.random((N, N, N)) < float(rng.uniform(0.2, 0.4))
        free = np.argwhere(~occ)
        if not len(free):
            continue
        p = tuple(free[rng.integers(len(free))].astype(float))
        yield occ, p, float(rng.uniform(1.0, 3.5))


def _run(cases):
    """返回 (robust_mismatch, boundary_tolerated, total)。"""
    from support_accessibility.oracle import SupportAccessibilityOracle
    robust = boundary = total = 0
    for occ, p, r in cases:
        o = SupportAccessibilityOracle(occ, {"n_directions": _NDIR})
        ok, exact = _check_one(o, p, r)
        total += 1
        if not ok:
            robust += 1
        elif not exact:
            boundary += 1
    return robust, boundary, total


def _audit_cases():
    """包含已知反例，再接固定批量样本；修复反例后仍使用同一审核集。"""
    from itertools import chain
    return chain(_gen_cases(1, seed=882), _gen_cases(_N_CASES - 1, seed=12345))


def _passes_d025(robust, total):
    return total == _N_CASES and robust / max(total, 1) <= _MAX_ROBUST_RATE


def checks():
    try:
        import numpy  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return [pending("voxel_vs_bruteforce", f"依赖未就绪：{e}", "D-003")]
    try:
        robust, boundary, total = _run(_audit_cases())
        return [result(
            "voxel_vs_bruteforce",
            _passes_d025(robust, total),
            f"{total} 件：robust 不一致={robust} ({robust / max(total, 1):.2%})，"
            f"操作性边界={boundary}；阈值≤{_MAX_ROBUST_RATE:.0%}",
            "D-003,D-025",
        )]
    except Exception as e:
        return [result("voxel_vs_bruteforce", False, f"评估异常：{e}", "D-003")]


def test_voxel_matches_bruteforce():
    """固定批量差分符合 D-025；已知 seed=882 不被隐去。"""
    try:
        import numpy  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    robust, boundary, total = _run(_audit_cases())
    assert _passes_d025(robust, total), (
        f"robust 差分率 {robust}/{total}={robust / max(total, 1):.2%} 超过 D-025 的 "
        f"{_MAX_ROBUST_RATE:.0%}；操作性边界={boundary}"
    )
