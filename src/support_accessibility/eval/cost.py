"""运行成本与数据身份：标签构建的预算外推（预算门用）与输入数据集摘要（回归门用）。"""


def extrapolate_oracle_cost(per_dir_ms, n_models, points_per_model, n_directions, n_radii):
    """把实测的「单点单方向毫秒」外推到全量标签构建，返回预计总小时数。"""
    total_ms = per_dir_ms * n_models * points_per_model * n_directions * n_radii
    return total_ms / 1000.0 / 3600.0


def data_digest(*roots):
    """输入数据集身份摘要（sha256 前 16 位十六进制），只哈希各数据根的 manifest.csv。

    manifest 每行含 n_points / n_inaccessible，标签一变摘要必变；不哈希 dataset.json，因为标签审核会改写其中的
    签收字段，避免「跑一次审核就让回归产物显得过期」（D-026）。
    """
    import hashlib
    import os
    h = hashlib.sha256()
    for root in roots:
        p = os.path.join(root, "manifest.csv")
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:16]
