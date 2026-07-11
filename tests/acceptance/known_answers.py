"""已知答案件：语义 C 在旗舰几何上的正确性（构造即知答案）。

守护决策：
  D-001  盲腔底部 = 不可达（语义C 的旗舰正确性）
  D-002  开阔外表面下朝面 = 可达（下半球逼近、基板不建模、只计本体遮挡）

oracle 实现 + 依赖（numpy/trimesh）就绪前保持 PENDING（红）。
"""

from unittest import SkipTest

from . import pending

try:
    from support_accessibility import oracle, data  # noqa: F401
except ImportError:
    oracle = data = None


def _ready():
    return oracle is not None and getattr(oracle, "IMPLEMENTED", False)


def checks():
    return [
        pending("blind_cavity_inaccessible", "oracle/数据未就绪。", "D-001"),
        pending("open_downface_accessible", "oracle/数据未就绪。", "D-002"),
    ]


def test_blind_cavity_inaccessible():
    """盲腔底部必判不可达（D-001）。"""
    if not _ready():
        raise SkipTest("oracle 未实现（D-001）")
    raise NotImplementedError("接 data.blind_cavity + oracle.label 后实现")


def test_open_downface_accessible():
    """开阔下朝面必判可达（D-002）。"""
    if not _ready():
        raise SkipTest("oracle 未实现（D-002）")
    raise NotImplementedError("接 data.open_downface + oracle.label 后实现")
