"""差分对拍（D-003）：体素腐蚀口径 vs 暴力胶囊参考——信任 oracle 的命门。

快实现（体素腐蚀 label）用慢但显然对的参考（暴力 reference_label）门住。两者用同一方向集与步长，
方法不同（EDT 体素采样 vs 连续到实体体素的最小距离），故仅在 r 阈值附近可能差 ~1 体素（边界带）。
规则：label≠reference 时，若 r±ε 邻域两者仍一致 → 判边界、容忍；robust 不一致 = 真 bug = FAIL。
探针实测 148/150 一致、2/2 皆边界（见 D-003 / 计划）。需 numpy + oracle。
"""

from unittest import SkipTest

from . import pending, result

_EPS = 0.75          # 边界邻域（体素）
_NDIR = 32           # 控时


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


def checks():
    try:
        import numpy  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return [pending("voxel_vs_bruteforce", f"依赖未就绪：{e}", "D-003")]
    try:
        robust, boundary, total = _run(_gen_cases(10, seed=12345))
        return [result("voxel_vs_bruteforce", robust == 0,
                       f"{total} 件：robust 不一致={robust}，容忍边界={boundary}", "D-003")]
    except Exception as e:
        return [result("voxel_vs_bruteforce", False, f"评估异常：{e}", "D-003")]


try:
    from hypothesis import given, settings, strategies as st
    _HAS_HYP = True
except ImportError:
    _HAS_HYP = False


if _HAS_HYP:
    @settings(max_examples=50, deadline=None)
    @given(seed=st.integers(min_value=0, max_value=2 ** 31 - 1))
    def test_voxel_matches_bruteforce(seed):
        """随机件：label 与 reference 一致，或仅差在 ε 边界带（D-003）。"""
        try:
            import numpy  # noqa: F401
            from support_accessibility import oracle  # noqa: F401
        except ImportError as e:
            raise SkipTest(f"依赖未就绪：{e}")
        robust, _, _ = _run(_gen_cases(1, seed=seed))
        assert robust == 0, f"robust 差分不一致（非边界）：seed={seed}"
else:
    def test_voxel_matches_bruteforce():
        raise SkipTest("hypothesis 未安装（env sfa 内应有）")
