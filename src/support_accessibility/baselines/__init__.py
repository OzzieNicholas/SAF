"""几何启发式对照基线（基线对照；对照位，非主线，见 D-015）。

论文用它们证明"神经方法不是简单规则/纯可见性即可替代"（工具尺寸效应 / 基线对照）：
- `ray_visibility`：**无工具半径**的纯射线可见性 = oracle 在 r=0。工具尺寸效应对照——工具尺寸不可忽略：
  某点纯射线可见（r=0 可达），但工具有非零半径时可能进不去（r>0 不可达）。
- `majority`：多数类（可达性问题里通常=全可达）——平凡下界。
- `local_solid_rule`：局部几何规则（查询点 patch 内实体占比超阈→判不可达）——"简单局部启发式"对照。

不可达=风险正类（与 eval / labels 一致）。numpy/oracle 在函数内 import（系统 py 仍可 import baselines）。
"""

from support_accessibility.runtime.frozen_params import FROZEN


def ray_visibility(occ, points, n_directions=FROZEN.n_directions):
    """无工具半径射线可见性基线 = oracle@r=0。返回 bool[K]，True=不可达（无方向射线可逃逸）。"""
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle
    o = SupportAccessibilityOracle(occ, {"n_directions": n_directions})
    pts = np.asarray(points, dtype=float).reshape(-1, 3)
    return np.array([o.label(p, 0.0).value == "inaccessible" for p in pts], dtype=bool)


def coarse_finite_tool_proxy(occ, points, radius, n_directions=16):
    """有限半径、低方向数的占据代理；用于近似标签 oracle，而非替代其真值口径。

    参考标签使用冻结的 128 个全局候选方向并可在有原网格时做边界带连续细化。
    本函数只在占据栅格上枚举更少的下半球方向，因此保留有限工具语义而有意丢失
    方向分辨率和网格细化。返回值与其它基线一致：``True`` 表示不可达。
    """
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle

    n_directions = int(n_directions)
    if n_directions < 4:
        raise ValueError("n_directions must be at least 4")
    oracle = SupportAccessibilityOracle(np.asarray(occ, dtype=bool), {"n_directions": n_directions})
    pts = np.asarray(points, dtype=float).reshape(-1, 3)
    return np.asarray(
        [oracle.label(point, float(radius)).value == "inaccessible" for point in pts],
        dtype=bool,
    )


def baseline_method_roles():
    """返回论文报告中各预测器的固定角色，防止把近似代理误写成标签 oracle。"""
    return {
        "majority": "trivial_class_reference",
        "local_rule": "local_geometric_heuristic",
        "ray_visibility": "zero_radius_semantic_ablation",
        "coarse_finite_tool": "coarse_geometric_proxy",
        "tiny_local": "local_learned_reference",
        "convonet": "shape_conditioned_surrogate",
    }


def majority_label(train_models):
    """训练集多数类（True=不可达占多数？可达性问题通常返回 False=可达）。"""
    import numpy as np
    lab = np.concatenate([np.asarray(m.labels, dtype=bool) for m in train_models if m.points.shape[0] > 0])
    return bool(lab.mean() > 0.5)


def predict_majority(n_points, maj_label):
    """对 n 个点全预测多数类。"""
    import numpy as np
    return np.full(int(n_points), bool(maj_label), dtype=bool)


def local_solid_rule(occ, points, patch_half=5, threshold=0.5):
    """局部几何规则基线：查询点周围 (2h+1)^3 patch 实体占比 > threshold → 判不可达。"""
    import numpy as np
    occ = np.asarray(occ, dtype=bool)
    nx, ny, nz = occ.shape
    fracs = []
    for p in np.asarray(points, dtype=float).reshape(-1, 3):
        x, y, z = (int(round(v)) for v in p)
        sub = occ[max(0, x - patch_half):min(nx, x + patch_half + 1),
                  max(0, y - patch_half):min(ny, y + patch_half + 1),
                  max(0, z - patch_half):min(nz, z + patch_half + 1)]
        fracs.append(float(sub.mean()) if sub.size else 0.0)
    return np.asarray(fracs) > threshold
