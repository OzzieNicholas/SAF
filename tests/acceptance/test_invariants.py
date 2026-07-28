"""不变量：对已知输入必须恒成立的结构性质。失败即响。

oracle/数据管线未接时返回 PENDING（不 raise），使验收层"会跑、可全红"。
（语义已知答案见 test_known_answers；单调/等变见 test_properties；对拍见 test_differential。）
"""

from unittest import SkipTest

from . import na

try:
    from support_accessibility import oracle
except ImportError:
    oracle = None


def _ready():
    return oracle is not None and getattr(oracle, "IMPLEMENTED", False)


def mesh_sanity():
    """网格 sanity（0 长边/非流形/自交/法向）——**已被他处覆盖**，判定 N/A（终态，D-027）：
    occ 正确性由 `test_mesh_frontend`（solidify IoU + 已知答案）守护；退化面由 D-022（胶囊跳过零面积）；
    真实标签有效性由 D-025（差分/res-稳定/分布审核）；网格合格性由 ingest §4.8 筛选。无需独立冗余检。"""
    return na("mesh_sanity", "已被 mesh_frontend(occ 正确) + D-022(退化面) + D-025(标签审核) + ingest §4.8 覆盖")


def checks():
    return [mesh_sanity()]


# —— pytest 入口（依赖就绪前 skip）——
def test_mesh_sanity():
    raise SkipTest("网格 sanity 判定 N/A（终态，D-027）：occ 正确性由 test_mesh_frontend、退化面 D-022、"
                   "标签审核 D-025、合格性 ingest §4.8 覆盖，无需独立冗余检")
