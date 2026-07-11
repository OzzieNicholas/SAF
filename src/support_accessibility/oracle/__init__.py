"""几何 oracle：支撑接触区工具可接近性的几何代理判定器。

判定语义与口径是**冻结的问题定义**（见 charter/decisions.md，改动须 supersede）：
  - D-001 语义 C：点 p 可达 ⟺ 存在方向，工具沿直线从无穷远逼近 p 而不碰撞。
  - D-002 基板不建模；工具从下半球逼近；只计零件本体遮挡（=遮挡下界）。
  - D-003 口径 = 体素/距离场腐蚀（半径摊销）+ 边界带精确胶囊细化。
  - D-005 球模型、方向灵活。

当前是接口骨架：几何计算尚未实现（依赖 numpy/scipy/trimesh，且是第一个 TDD 目标）。
tests/gate.py 依赖 IMPLEMENTED 标志把相关验收标为 PENDING，从而验收层"会跑、可全红"。
"""

from enum import Enum


class Label(str, Enum):
    ACCESSIBLE = "accessible"
    INACCESSIBLE = "inaccessible"
    UNCERTAIN = "uncertain"       # 边界带：栅格分辨率决定不了、或多次检查不一致


# 几何核心是否就绪。实现后置 True，验收层的几何性质随之从 PENDING 转入真实评估。
IMPLEMENTED = False


class SupportAccessibilityOracle:
    """在给定实体几何、构建方向、工具半径下，对支撑接触点判定可达性代理标签。

    实现顺序（建门先于建码，第一个 TDD 目标）：
      1) solidify(mesh)         稳健判内外（generalized winding number），得体素占据/距离场
      2) erode(dist, r)         阈值 r 得"腐蚀自由场"（工具半径对全体点一次摊销，D-003）
      3) label(p, dirs, r)      从 p+r·v 沿 v 到无穷远做栅格 ray-march；下半球方向集（D-002）
      4) refine_boundary(...)   对 UNCERTAIN 薄层用精确胶囊-网格求交细化
      5) reference_label        小案例暴力胶囊求交，供 oracle 自对拍（differential）
    """

    def __init__(self, params):
        self.params = params  # 见 conf/params.yaml: oracle.* / tool.* / geometry.*

    def label(self, point, directions, radius):
        """返回 Label。point:(x,y,z)；directions:下半球方向集；radius:相对归一尺度。"""
        raise NotImplementedError(
            "oracle.label 未实现（D-003 体素腐蚀口径）——这是第一个 TDD 目标。"
        )

    def reference_label(self, point, directions, radius):
        """小案例暴力参考实现（胶囊-网格求交），仅用于对拍，不作主口径。"""
        raise NotImplementedError("oracle.reference_label 未实现（对拍参考）。")
