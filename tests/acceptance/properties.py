"""变形/性质测试：不需要知道绝对答案，只钉"关系"——最适合理解不完整的研究期。

守护决策：
  D-005  联合旋转等变：mesh 与构建方向 d 一起转 → 标签同步旋转（只转 mesh 不转 d 不成立）
  D-005  尺度不变：mesh 与工具半径 r 同比缩放 → 标签不变
  D-003  半径单调：r↑ → 不可达集只增不减
  D-003  方向单调：采样方向数↑ → 可达集只增不减

真实策略用 Hypothesis 生成随机小 mesh / 旋转 / 缩放 / 半径（生成器即语料，无需手攒件）。
需 hypothesis + oracle；当前 PENDING（红）。
"""

from unittest import SkipTest

from . import pending

try:
    from support_accessibility import oracle  # noqa: F401
except ImportError:
    oracle = None


def _ready():
    return oracle is not None and getattr(oracle, "IMPLEMENTED", False)


def checks():
    return [
        pending("rotation_equivariance", "hypothesis+oracle 未就绪。", "D-005"),
        pending("scale_invariance", "hypothesis+oracle 未就绪。", "D-005"),
        pending("radius_monotonic", "hypothesis+oracle 未就绪。", "D-003"),
        pending("direction_monotonic", "hypothesis+oracle 未就绪。", "D-003"),
    ]


def test_rotation_equivariance():
    if not _ready():
        raise SkipTest("oracle 未实现（D-005）")
    raise NotImplementedError("Hypothesis:联合旋转(mesh,d)→标签同步旋转")


def test_scale_invariance():
    if not _ready():
        raise SkipTest("oracle 未实现（D-005）")
    raise NotImplementedError("Hypothesis:同比缩放(mesh,r)→标签不变")


def test_radius_monotonic():
    if not _ready():
        raise SkipTest("oracle 未实现（D-003）")
    raise NotImplementedError("Hypothesis:r↑→不可达集只增不减")


def test_direction_monotonic():
    if not _ready():
        raise SkipTest("oracle 未实现（D-003）")
    raise NotImplementedError("Hypothesis:方向数↑→可达集只增不减")
