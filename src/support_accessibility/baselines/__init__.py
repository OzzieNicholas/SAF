"""对照基线：说明形状条件网络不能被简单规则或更粗的几何判定替代（D-015）。

- ``voxel_judgment``：只用占据栅格、不做边界带细化的体素判定，可调工具半径与方向数。
  零半径射线可见性（``ray_visibility``，半径 0）与 16 方向粗判定都是它的特例；
  精度—耗时实验用它扫描方向数。
- ``majority_label`` / ``predict_majority``：多数类，平凡下界。
- ``local_solid_rule``：查询点邻域实体占比超过阈值即判不可达，简单局部启发式。

不可达为风险正类（True），与标签一致。numpy 与 oracle 在函数内导入。
"""

from support_accessibility.runtime.frozen_params import FROZEN


def voxel_judgment(occ, points, radius, n_directions):
    """不经细化的体素判定：半径 radius（体素）、n_directions 个全局方向中的下半球方向。返回 bool[K]，True 为不可达。"""
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle
    if int(n_directions) < 4:
        raise ValueError("n_directions must be at least 4")
    oracle = SupportAccessibilityOracle(np.asarray(occ, bool), {"n_directions": int(n_directions)})
    pts = np.asarray(points, float).reshape(-1, 3)
    return np.asarray([oracle.label(p, float(radius)).value == "inaccessible" for p in pts], bool)


def ray_visibility(occ, points, n_directions=FROZEN.n_directions):
    """零半径射线可见性：没有任何方向的射线能逃逸即判不可达（体素判定在 r=0 的特例）。"""
    return voxel_judgment(occ, points, 0.0, n_directions)


def baseline_method_roles():
    """论文中各预测器的固定角色，防止把近似代理误写成标签判定器。"""
    return {
        "majority": "trivial_class_reference",
        "local_rule": "local_geometric_heuristic",
        "ray_visibility": "zero_radius_semantic_ablation",
        "coarse_finite_tool": "coarse_geometric_proxy",
        "tiny_local": "local_learned_reference",
        "convonet": "shape_conditioned_surrogate",
    }


def majority_label(train_models):
    """训练集多数类（True 为不可达占多数）。"""
    import numpy as np
    lab = np.concatenate([np.asarray(m.labels, dtype=bool) for m in train_models if m.points.shape[0] > 0])
    return bool(lab.mean() > 0.5)


def predict_majority(n_points, maj_label):
    """对 n 个点全预测多数类。"""
    import numpy as np
    return np.full(int(n_points), bool(maj_label), dtype=bool)


def local_solid_rule(occ, points, patch_half=5, threshold=0.5):
    """局部几何规则：查询点周围 (2h+1)^3 邻域实体占比 > threshold → 判不可达。"""
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
