"""几何启发式对照基线（E4；对照位，非主线，见 D-015）。

论文用它们证明"神经方法不是简单规则/纯可见性即可替代"（H2 / E4）：
- `ray_visibility`：**无工具半径**的纯射线可见性 = oracle 在 r=0。H2 对照——工具尺寸不可忽略：
  某点纯射线可见（r=0 可达），但工具有非零半径时可能进不去（r>0 不可达）。
- `majority`：多数类（可达性问题里通常=全可达）——平凡下界。
- `local_solid_rule`：局部几何规则（查询点 patch 内实体占比超阈→判不可达）——"简单局部启发式"对照。

不可达=风险正类（与 eval / labels 一致）。numpy/oracle 在函数内 import（系统 py 仍可 import baselines）。
"""


def ray_visibility(occ, points, n_directions=32):
    """无工具半径射线可见性基线 = oracle@r=0。返回 bool[K]，True=不可达（无方向射线可逃逸）。"""
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle
    o = SupportAccessibilityOracle(occ, {"n_directions": n_directions})
    pts = np.asarray(points, dtype=float).reshape(-1, 3)
    return np.array([o.label(p, 0.0).value == "inaccessible" for p in pts], dtype=bool)


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
