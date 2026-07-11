"""几何 oracle：支撑接触区工具可接近性的几何代理判定器（语义 C，体素腐蚀口径）。

冻结的判定语义与口径（见 charter/decisions.md，改动须 supersede）：
  D-001 语义 C：点 p 可达 ⟺ 存在方向 v，半径 r 的工具球沿直线从无穷远逼近 p 而不碰撞。
  D-002 基板不建模；工具从下半球逼近（v_z<0，构建方向固定 +z）；只计零件本体遮挡（=遮挡下界）。
  D-003 口径 = 体素/距离场腐蚀（工具半径对全体点一次摊销）+ 方向栅格 ray-march。
  D-005 球模型、方向灵活。

本实现工作在**占据栅格**（occupancy, True=实体）上：
  occupancy → 距离场 free_dist = distance_transform_edt(~occ)（每自由体素到最近实体的距离）
  → 每方向从球心 p+r·v 沿 v 到出界做 ray-march，全程 free_dist>r 则该方向无碰撞。
mesh→occupancy 前端（igl generalized winding number 判内外、pitch/longest_edge_1 归一）属后续批次
（真实网格接入）；本批用程序化解析占据（构造即知答案）验证核心口径，点/半径以体素为单位。

注：有限方向采样使本口径**偏保守**——深窄腔即便存在连续竖直插入，若采样方向都不够竖直
（沿途漂移撞壁）也会判不可达；方向数↑→更可达（direction_monotonic 性质，D-003）。这是几何代理
的已知性质，给出偏保守的可达性；边界情形靠更密采样 / 边界胶囊细化缓解（后续批次）。
"""

from enum import Enum

import numpy as np
from scipy import ndimage


class Label(str, Enum):
    ACCESSIBLE = "accessible"
    INACCESSIBLE = "inaccessible"
    UNCERTAIN = "uncertain"       # 边界带（精确胶囊细化，后续批次）


IMPLEMENTED = True


def lower_hemisphere_dirs(n):
    """Fibonacci 球面取 v_z<0（D-002：工具从下方逼近下朝面）。返回 (m,3) 单位向量。"""
    i = np.arange(n) + 0.5
    phi = np.arccos(1.0 - 2.0 * i / n)              # 极角 [0,π]
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i          # 黄金角
    dirs = np.stack([np.sin(phi) * np.cos(theta),
                     np.sin(phi) * np.sin(theta),
                     np.cos(phi)], axis=1)
    return dirs[dirs[:, 2] < 0.0]                   # 下半球


class SupportAccessibilityOracle:
    """在占据栅格上对支撑接触点判定可达性代理标签（体素单位）。

    occupancy : np.ndarray[bool] 三维，True=实体。
    point/radius 以体素为单位；n_directions/march_step 见 params。
    """

    def __init__(self, occupancy, params=None):
        self.occ = np.ascontiguousarray(occupancy, dtype=bool)
        self.params = dict(params or {})
        # D-003：距离场一次算好，工具半径对全体点/方向摊销。free_dist[c]=中心 c 到最近实体的距离。
        self.free_dist = ndimage.distance_transform_edt(~self.occ)
        self.dirs = lower_hemisphere_dirs(int(self.params.get("n_directions", 128)))
        self.step = float(self.params.get("march_step", 0.5))
        self._shape = np.asarray(self.occ.shape)

    # —— 主口径（D-003 体素腐蚀 + 方向 ray-march）——
    def label(self, point, radius):
        p = np.asarray(point, dtype=float)
        r = float(radius)
        for v in self.dirs:
            if self._clear_along(p, v, r):
                return Label.ACCESSIBLE            # 存在一个无碰撞插入方向
        return Label.INACCESSIBLE

    def _clear_along(self, p, v, r):
        """球心从 p+r·v 沿 v 到出界，全程 free_dist>r？（体素 ray-march）"""
        t = r
        while True:
            c = p + t * v
            idx = np.floor(c + 0.5).astype(int)                 # 最近体素
            if np.any(idx < 0) or np.any(idx >= self._shape):
                return True                                     # 到达"无穷远"(出界)仍无碰撞
            if self.free_dist[idx[0], idx[1], idx[2]] <= r:
                return False                                    # 球心离实体 ≤ r → 碰撞
            t += self.step

    # —— 对拍参考（暴力：直接测球∩实体体素；供 differential 门交叉验证）——
    def reference_label(self, point, radius):
        if not hasattr(self, "_solid_pts"):
            self._solid_pts = np.argwhere(self.occ).astype(float)   # (M,3) 实体体素坐标
        p = np.asarray(point, dtype=float)
        r = float(radius)
        for v in self.dirs:
            if self._ref_clear_along(p, v, r):
                return Label.ACCESSIBLE
        return Label.INACCESSIBLE

    def _ref_clear_along(self, p, v, r):
        r2 = r * r
        t = r
        while True:
            c = p + t * v
            idx = np.floor(c + 0.5)
            if np.any(idx < 0) or np.any(idx >= self._shape):
                return True
            if self._solid_pts.size and ((self._solid_pts - c) ** 2).sum(1).min() <= r2:
                return False                                    # 任一实体体素中心落在球内 → 碰撞
            t += self.step
