"""几何 oracle：支撑接触区工具可接近性的几何代理判定器（语义 C，体素腐蚀口径）。

冻结的判定语义与口径（见 governance/decisions.md，改动须 supersede）：
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
（沿途漂移撞壁）也会判不可达；方向数↑**经验上**更可达——严格保证仅对**嵌套**方向集 S1⊆S2 成立
（direction_monotonic，见 test_properties / D-003；非嵌套 Fibonacci 方向数单调不作严格不变量）。偏保守是
几何代理的已知行为；边界情形靠更密采样 / 边界胶囊细化缓解。
"""

from enum import Enum

import numpy as np
from scipy import ndimage

from .capsule import capsule_hits_mesh, precompute_mesh


class Label(str, Enum):
    ACCESSIBLE = "accessible"
    INACCESSIBLE = "inaccessible"
    UNCERTAIN = "uncertain"       # 预留（D-021 保留待用：未来 labels.emit_uncertain_band 敏感性扫单列不确定带）；当前判定口径不产出（D-020：细化给真值而非隔离）


IMPLEMENTED = True


def decide_label(clearances, r, eps, refine=None):
    """判定（D-003 边界带精确细化）。clearances = 每逼近方向沿射线的最小净空（体素）。

    - **无网格（refine=None）**：二分——任一 clearance > r 即 ACCESSIBLE，否则 INACCESSIBLE。
      与细化前口径逐比特一致（程序化管线用合成占据、无网格，故不受影响、不退绿）。
    - **有网格（refine 给定）**：三态细化——任一 clearance > r+ε → 明确无碰撞逃逸 → ACCESSIBLE；
      否则对 AMBIGUOUS 方向（clearance > r-ε）逐个交精确胶囊 refine(i)（True=无碰撞）定夺，
      任一为真 → ACCESSIBLE；皆碰 → INACCESSIBLE。（细化给真值而非隔离，故不出 UNCERTAIN。）
    """
    if refine is None:
        return Label.ACCESSIBLE if any(c > r for c in clearances) else Label.INACCESSIBLE
    if any(c > r + eps for c in clearances):
        return Label.ACCESSIBLE
    for i, c in enumerate(clearances):
        if c > r - eps and refine(i):
            return Label.ACCESSIBLE
    return Label.INACCESSIBLE


def decide_direction_labels(clearances, r, eps, refine=None):
    """方向级可达性场（D-024，extend D-004）：每逼近方向是否可达，**不 OR 归约**。返回 bool list。

    同 decide_label 的逐方向判据，只是保留每方向结果而非取 any：
    - **无网格（refine=None）**：dir i 可达 ⟺ clearance_i > r（逐方向二分）。
    - **有网格**：clearance_i > r+ε → 明确可达；含糊（> r-ε）→ 交精确胶囊 refine(i)；否则不可达。
    **不变量**：any(本函数) == (decide_label(同参) == ACCESSIBLE)——二分口径是本场的 any-归约（见 D-024）。
    """
    out = []
    for i, c in enumerate(clearances):
        if refine is None:
            out.append(c > r)
        elif c > r + eps:
            out.append(True)
        elif c > r - eps:
            out.append(bool(refine(i)))
        else:
            out.append(False)
    return out


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

    def __init__(self, occupancy, params=None, mesh=None):
        self.occ = np.ascontiguousarray(occupancy, dtype=bool)
        self.params = dict(params or {})
        # D-003：距离场一次算好，工具半径对全体点/方向摊销。free_dist[c]=中心 c 到最近实体的距离。
        self.free_dist = ndimage.distance_transform_edt(~self.occ)
        if "directions" in self.params:                 # 显式方向集（D-005 方向灵活；方向单调保证性测试 / E5 用）
            d = np.asarray(self.params["directions"], dtype=float).reshape(-1, 3)
            self.dirs = d / np.linalg.norm(d, axis=1, keepdims=True)
        else:
            self.dirs = lower_hemisphere_dirs(int(self.params.get("n_directions", 128)))
        self.step = float(self.params.get("march_step", 0.5))
        self.eps = float(self.params.get("epsilon_voxels", 1.5))
        self.mesh = mesh                 # (V,F,lo,pitch) 世界坐标网格+体素变换；None=无细化（体素二分）
        # D-020 细化的网格常量（tris/质心/外接半径/包围球）每模型算一次，供所有点×方向的 refine 复用
        self._mesh_precomp = precompute_mesh(mesh[0], mesh[1]) if mesh is not None else None
        self._shape = np.asarray(self.occ.shape)

    # —— 主口径（D-003 体素腐蚀 + 方向 ray-march + 边界带精确胶囊细化）——
    def label(self, point, radius):
        """支撑接触点可达性标签。有网格 → 边界带精确细化；无网格 → 体素二分（口径见 decide_label）。"""
        p = np.asarray(point, dtype=float)
        r = float(radius)
        clearances = [self._min_clearance_along(p, v, r) for v in self.dirs]
        refine = self._make_refine(p, r) if self.mesh is not None else None
        return decide_label(clearances, r, self.eps, refine)

    def direction_labels(self, point, radius):
        """方向级可达性场（D-024）：对 self.dirs 每个逼近方向判可达，返回 bool ndarray (len(dirs),)。
        OR 归约 == label（二分口径 D-004 是本场 any-归约）。方向序与 self.dirs 一致。"""
        p = np.asarray(point, dtype=float)
        r = float(radius)
        clearances = [self._min_clearance_along(p, v, r) for v in self.dirs]
        refine = self._make_refine(p, r) if self.mesh is not None else None
        return np.asarray(decide_direction_labels(clearances, r, self.eps, refine), dtype=bool)

    def _min_clearance_along(self, p, v, r):
        """球心从 p+r·v 沿 v 到出界，射线上到最近实体的最小净空（体素）；出界=逃逸(+inf)。
        早退：净空 < r-ε 即明确碰撞，返回该值（省走完整条射线，不影响 >r / >r±ε 分类）。"""
        lo_bound = r - self.eps
        t, m = r, np.inf
        while True:
            c = p + t * v
            idx = np.floor(c + 0.5).astype(int)                 # 最近体素
            if np.any(idx < 0) or np.any(idx >= self._shape):
                return m                                        # 出界=逃逸；m 为途中最小净空
            fd = float(self.free_dist[idx[0], idx[1], idx[2]])
            if fd < m:
                m = fd
            if fd < lo_bound:
                return fd                                       # 明确碰撞，提前退出
            t += self.step

    def _make_refine(self, p, r):
        """构造 refine(i)：方向 i 的精确胶囊-网格测试是否无碰撞（True=可逃逸）。体素→世界坐标。"""
        V, F, lo, pitch = self.mesh
        p_world = np.asarray(lo, float) + (p + 0.5) * float(pitch)     # world_to_voxel 的逆
        r_world = r * float(pitch)

        pc = self._mesh_precomp                                        # 每模型预算常量，复用不重算
        def refine(i):
            v = self.dirs[i]
            origin = p_world + r_world * v
            return not capsule_hits_mesh(origin, v, r_world, V, F, precomp=pc)     # 精确无碰撞
        return refine

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
