"""图件中按名称指定的固定案例，是这类案例的唯一清单。

结果画廊与方向评价示例按固定规则选件（规则写在各自脚本中），不在此登记。
"""

# 方法总览（图 2）：固定留出集中的多级台阶零件，风险面大部分从仰视方向可见。
METHOD_OVERVIEW = "145643_0b6cfcf1_0000"


def assert_holdout(checkpoint, name, figure):
    """定性结果必须来自留出零件，否则失败。"""
    if name not in set(checkpoint.get("test_names", ())):
        raise RuntimeError(f"{figure}: {name} is not in the declared held-out set")
