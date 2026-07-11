"""变形/性质测试：不需要知道绝对答案，只钉"关系"。

守护决策与现状（详见 charter/decisions.md、charter/README.md 映射）：
  D-005 尺度不变（整数上采样 k×，label 不变）—— 已接绿
  D-005 旋转等变 —— 体素旋转有重采样伪影，属连续几何性质，移交 mesh 前端批次
  D-003 半径单调（r↑→不可达↑）—— **已证伪（D-008）**：point-touch 语义C 下不成立，不作不变量
  D-003 方向单调（方向数↑→可达↑）—— 经验稳但非嵌套 Fibonacci 不保证；需 oracle 显式方向集才能给保证性测试（后续）

需 hypothesis + numpy + oracle。
"""

from unittest import SkipTest

from . import pending, result

_EPS = 0.5
_NDIR = 32


def _scale_check_one(seed):
    """整数上采样 k=2：label(occ,p,r) == label(k·occ, k·p, k·r)？返回 (ok, exact)。"""
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle as Ora
    rng = np.random.default_rng(seed)
    N = int(rng.integers(10, 15))
    occ = rng.random((N, N, N)) < float(rng.uniform(0.2, 0.4))
    free = np.argwhere(~occ)
    if not len(free):
        return True, True
    p = free[rng.integers(len(free))].astype(float)
    r = float(rng.uniform(1.0, 3.0))
    k = 2
    o1 = Ora(occ, {"n_directions": _NDIR})
    occ2 = np.repeat(np.repeat(np.repeat(occ, k, 0), k, 1), k, 2)
    o2 = Ora(occ2, {"n_directions": _NDIR})
    p2 = tuple(p * k + (k - 1) / 2.0)
    l1 = lambda rr: o1.label(tuple(p), rr).value
    l2 = lambda rr: o2.label(p2, rr).value
    if l1(r) == l2(r * k):
        return True, True
    boundary = (l1(r - _EPS) == l2((r - _EPS) * k)) and (l1(r + _EPS) == l2((r + _EPS) * k))
    return boundary, False


def _run_scale(n, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    robust = boundary = total = 0
    for _ in range(n):
        ok, exact = _scale_check_one(int(rng.integers(0, 2 ** 31 - 1)))
        total += 1
        if not ok:
            robust += 1
        elif not exact:
            boundary += 1
    return robust, boundary, total


def checks():
    out = []
    try:
        import numpy  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
        robust, boundary, total = _run_scale(8, seed=999)
        out.append(result("scale_invariance", robust == 0,
                           f"{total} 件：robust 违反={robust}，容忍边界={boundary}", "D-005"))
    except ImportError as e:
        out.append(pending("scale_invariance", f"依赖未就绪：{e}", "D-005"))
    except Exception as e:
        out.append(result("scale_invariance", False, f"评估异常：{e}", "D-005"))
    out.append(pending("radius_monotonic", "已证伪（D-008），不作不变量；真实网格上复核", "D-003"))
    out.append(pending("direction_monotonic", "经验稳，需 oracle 显式方向集给保证性测试（后续）", "D-003"))
    out.append(pending("rotation_equivariance", "体素旋转有重采样伪影；连续版移交 mesh 前端", "D-005"))
    return out


try:
    from hypothesis import given, settings, strategies as st
    _HAS_HYP = True
except ImportError:
    _HAS_HYP = False


if _HAS_HYP:
    @settings(max_examples=40, deadline=None)
    @given(seed=st.integers(min_value=0, max_value=2 ** 31 - 1))
    def test_scale_invariance(seed):
        """整数上采样 k=2：label 不变，或仅差在 ε 边界带（D-005）。"""
        try:
            import numpy  # noqa: F401
            from support_accessibility import oracle  # noqa: F401
        except ImportError as e:
            raise SkipTest(f"依赖未就绪：{e}")
        ok, _ = _scale_check_one(seed)
        assert ok, f"scale 不变量被 robust 违反：seed={seed}"
else:
    def test_scale_invariance():
        raise SkipTest("hypothesis 未安装（env sfa 内应有）")


def test_radius_monotonic():
    raise SkipTest("半径单调已证伪（D-008）：point-touch 语义C 下不成立，不作不变量；真实网格上复核")


def test_direction_monotonic():
    raise SkipTest("方向单调经验稳但非嵌套 Fibonacci 不保证；需 oracle 显式方向集给保证性测试（后续批次）")


def test_rotation_equivariance():
    raise SkipTest("体素旋转有重采样伪影，属连续几何性质；连续版移交 mesh 前端批次")
