"""tiny 形状条件预测器（Phase-1 薄纵切，纯 numpy CPU）。

目标：端到端证明"形状条件特征 → 支撑接触点可达性"在**未见模型**上成立（H3 跨模型），
derisk 论文头号命题。**这不是最终模型**——真实 ConvONet / PyTorch 版属 Phase-3（用户本地 GPU，
见 CLAUDE.md 神经栈）；此云端 env torch 装不下（pytorch 源被代理挡）、且薄纵切要的是可验证的可行性信号。

形状条件特征 = 查询点周围的**局部占据 patch**（原始几何，非 oracle 代理，故非循环）+ 归一点坐标；
小 2 层 MLP + BCE + Adam（numpy 手写反传）学决策边界。numpy 在函数内 import（系统 py 仍可 import models）。
"""

from dataclasses import dataclass

PATCH_HALF = 5                      # patch 边长 = 2*PATCH_HALF+1（覆盖腔壁：本批腔宽 ≤7）


@dataclass
class TinyModel:
    """训练后的权重 + 特征超参（predict 复用同一 patch 口径）。"""
    W1: object
    b1: object
    W2: object
    b2: object
    patch_half: int


def _sigmoid(z):
    """数值稳定 sigmoid（z 极负时走 exp(z)/(1+exp(z))，避免 exp(-z) 溢出）。"""
    import numpy as np
    out = np.empty_like(z, dtype=np.float64)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def _patch_at(occ, p, w):
    """点 p 周围 (2w+1)^3 占据 patch；越界补 0（外部=开放自由空间）。返回展平 (D0,) float32。"""
    import numpy as np
    occ = np.asarray(occ, dtype=np.float32)
    nx, ny, nz = occ.shape
    x, y, z = (int(round(v)) for v in p)
    out = np.zeros((2 * w + 1, 2 * w + 1, 2 * w + 1), dtype=np.float32)
    xs, xe = max(0, x - w), min(nx, x + w + 1)
    ys, ye = max(0, y - w), min(ny, y + w + 1)
    zs, ze = max(0, z - w), min(nz, z + w + 1)
    if xs < xe and ys < ye and zs < ze:
        out[xs - (x - w):xe - (x - w), ys - (y - w):ye - (y - w), zs - (z - w):ze - (z - w)] = \
            occ[xs:xe, ys:ye, zs:ze]
    return out.ravel()


def features(occ, points, patch_half=PATCH_HALF):
    """(occ, K点) → (K, D) 形状条件特征：局部 patch（居中到 ±0.5）+ 归一坐标 (x,y,z)/shape。"""
    import numpy as np
    occ = np.asarray(occ)
    shape = np.asarray(occ.shape, dtype=np.float32)
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    patches = np.stack([_patch_at(occ, p, patch_half) for p in pts]) - 0.5
    coords = pts / shape
    return np.concatenate([patches, coords], axis=1).astype(np.float32)


def _stack(models, patch_half):
    import numpy as np
    Xs = [features(m.occ, m.points, patch_half) for m in models if m.points.shape[0] > 0]
    ys = [np.asarray(m.labels, dtype=np.float32).reshape(-1, 1) for m in models if m.points.shape[0] > 0]
    return np.concatenate(Xs), np.concatenate(ys)


def train(train_models, hidden=24, epochs=300, lr=0.01, weight_decay=1e-4, patch_half=PATCH_HALF, seed=0):
    """在训练模型上拟合 tiny MLP（全批 Adam + BCE + L2）。返回 TinyModel。"""
    import numpy as np
    X, y = _stack(train_models, patch_half)
    n, d = X.shape
    rng = np.random.default_rng(seed)
    W1 = (rng.standard_normal((d, hidden)) * (2.0 / d) ** 0.5).astype(np.float32)
    b1 = np.zeros((1, hidden), np.float32)
    W2 = (rng.standard_normal((hidden, 1)) * (2.0 / hidden) ** 0.5).astype(np.float32)
    b2 = np.zeros((1, 1), np.float32)
    params = [W1, b1, W2, b2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    for t in range(1, epochs + 1):
        z1 = X @ W1 + b1
        a1 = np.maximum(z1, 0.0)
        logit = a1 @ W2 + b2
        pr = _sigmoid(logit)
        dlogit = (pr - y) / n
        grads = [X.T @ (dlogit @ W2.T * (z1 > 0)) + weight_decay * W1,
                 (dlogit @ W2.T * (z1 > 0)).sum(0, keepdims=True),
                 a1.T @ dlogit + weight_decay * W2,
                 dlogit.sum(0, keepdims=True)]
        for i, g in enumerate(grads):
            m[i] = beta1 * m[i] + (1 - beta1) * g
            v[i] = beta2 * v[i] + (1 - beta2) * (g * g)
            mhat = m[i] / (1 - beta1 ** t)
            vhat = v[i] / (1 - beta2 ** t)
            params[i] -= lr * mhat / (np.sqrt(vhat) + eps)
    return TinyModel(params[0], params[1], params[2], params[3], patch_half)


def predict_proba(model, occ, points):
    """(TinyModel, occ, K点) → (K,) 不可达概率。"""
    import numpy as np
    X = features(occ, points, model.patch_half)
    a1 = np.maximum(X @ model.W1 + model.b1, 0.0)
    logit = a1 @ model.W2 + model.b2
    return _sigmoid(logit).ravel()


def predict(model, occ, points, threshold=0.5):
    """(K,) bool 预测（True=不可达，风险正类）。"""
    return predict_proba(model, occ, points) >= threshold
