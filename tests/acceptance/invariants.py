"""不变量：对已知输入必须恒成立的结构性质。失败即响。

oracle/数据管线未接时返回 PENDING（不 raise），使验收层"会跑、可全红"。
（语义已知答案见 known_answers；单调/等变见 properties；对拍见 differential。）
"""

from unittest import SkipTest

from . import pending

try:
    from support_accessibility import oracle
except ImportError:
    oracle = None


def _ready():
    return oracle is not None and getattr(oracle, "IMPLEMENTED", False)


def mesh_sanity():
    """网格 sanity：0 长边 / 非流形 / 自交 / 法向一致性（接数据管线后真检）。"""
    return pending("mesh_sanity", "数据管线未接。")


def checks():
    return [mesh_sanity()]


# —— pytest 入口（依赖就绪前 skip）——
def test_mesh_sanity():
    if not _ready():
        raise SkipTest("数据管线/oracle 未就绪")
    raise NotImplementedError("接数据管线后实现")
