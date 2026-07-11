"""程序化已知答案件生成器 —— walking skeleton 的头几个测试件。

从 charter/decisions.md 的 D-001/D-002 与旗舰案例来：**构造即知正确标签**
（造了个盲腔，其底部就必须判不可达）。它们既是验收层的头几个输入，也是 oracle 的直觉锚。

几何实现需 numpy/trimesh（工具链 spike 装依赖后再填）；故当前为接口桩，
模块级只用 stdlib，函数体 NotImplementedError，验收层据此保持 PENDING（红）。
"""

from dataclasses import dataclass, field


@dataclass
class KnownAnswerCase:
    """一个构造即知答案的程序化件。"""
    name: str
    expected: str                 # "inaccessible" / "accessible"
    params: dict = field(default_factory=dict)
    # mesh、支撑接触点、构建方向由实现填充


def blind_cavity(depth, opening_width):
    """深 depth、开口 opening_width 的盲孔盒。底部已知 = 不可达（D-001）。"""
    raise NotImplementedError("需 numpy/trimesh；工具链 spike 后实现。")


def open_downface():
    """开阔外表面下朝悬臂。已知 = 可达（D-002：下半球逼近、只计本体遮挡）。"""
    raise NotImplementedError("需 numpy/trimesh。")


def deep_narrow_slot(width, depth):
    """深窄槽。随 width/depth 与工具半径耦合，用于半径单调性趋势（D-003）。"""
    raise NotImplementedError("需 numpy/trimesh。")


def flagship_pair(support_area_target, cavity_depth_a, cavity_depth_b):
    """旗舰配对：支撑面积近似相等、腔深不同的两件，保 E1/H1（可达性≠支撑面积）存在性。"""
    raise NotImplementedError("需 numpy/trimesh。")
