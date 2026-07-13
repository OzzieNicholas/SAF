"""变形/性质测试：不需要知道绝对答案，只钉"关系"。

守护决策与现状（详见 charter/decisions.md、charter/README.md 映射）：
  D-005 尺度不变（整数上采样 k×，label 不变）—— **已证伪（D-011）**：分辨率依赖、非严格
        不变量；粗网格误判欠分辨薄特征（细网格纠正为不可达）；真实网格上复核
  D-005 旋转等变 —— 体素旋转有重采样伪影，属连续几何性质，移交 mesh 前端批次
  D-003 半径单调（r↑→不可达↑）—— **已证伪（D-008）**：point-touch 语义C 下不成立，不作不变量
  D-003 方向单调（方向数↑→可达↑）—— 经验稳但非嵌套 Fibonacci 不保证；需 oracle 显式方向集才能给保证性测试（后续）

四条变形性质当前均非严格不变量（证伪或待证），故 checks() 全记 pending、pytest 全 skip；
真实网格接入后复核（证伪方法留在对应 decisions 条目，不作残留代码）。
"""

from unittest import SkipTest

from . import pending


def checks():
    return [
        pending("scale_invariance", "整数上采样证伪（D-011）：分辨率依赖、非严格不变量；真实网格上复核", "D-011"),
        pending("radius_monotonic", "已证伪（D-008），不作不变量；真实网格上复核", "D-003"),
        pending("direction_monotonic", "经验稳，需 oracle 显式方向集给保证性测试（后续）", "D-003"),
        pending("rotation_equivariance", "体素旋转有重采样伪影；连续版移交 mesh 前端", "D-005"),
    ]


def test_scale_invariance():
    raise SkipTest("尺度不变经整数上采样证伪（D-011）：分辨率依赖、非严格不变量；粗网格误判欠分辨薄特征；真实网格上复核")


def test_radius_monotonic():
    raise SkipTest("半径单调已证伪（D-008）：point-touch 语义C 下不成立，不作不变量；真实网格上复核")


def test_direction_monotonic():
    raise SkipTest("方向单调经验稳但非嵌套 Fibonacci 不保证；需 oracle 显式方向集给保证性测试（后续批次）")


def test_rotation_equivariance():
    raise SkipTest("体素旋转有重采样伪影，属连续几何性质；连续版移交 mesh 前端批次")
