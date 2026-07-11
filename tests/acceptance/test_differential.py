"""差分对拍（D-003）：体素腐蚀口径 vs 暴力胶囊参考，非边界点必须一致。

这是**信任 oracle 的命门**——快实现（体素腐蚀）用慢但显然对的参考（暴力胶囊）门住。
需两套实现就绪（oracle.label 与 oracle.reference_label）+ numpy；当前 PENDING（红）。
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
    return [pending("voxel_vs_bruteforce", "两套实现未就绪。", "D-003")]


def test_voxel_matches_bruteforce():
    """随机小程序化件上，label 与 reference_label 在非边界点一致（D-003）。"""
    raise SkipTest("differential 未接（后续批次：Hypothesis 随机件对拍 label vs reference_label，容差 ε）")
