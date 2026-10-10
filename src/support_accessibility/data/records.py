"""统一的带标签样本记录与按模型切分。

模块级只用 stdlib；numpy 在函数内 import，保证系统 py（无 numpy）仍能导入。
"""

from dataclasses import dataclass


# —— 标签样本：形状条件样本，oracle 自动打标（无人工标注）——
@dataclass
class LabeledModel:
    """一个程序化件的形状条件训练样本。occ=形状条件；points=下朝支撑接触点；labels=oracle 标签。"""
    name: str
    occ: object            # np.ndarray[bool]，True=实体（形状条件输入）
    points: object         # np.ndarray (K,3) float，体素坐标（下朝支撑接触点，查询点）
    labels: object         # np.ndarray (K,) bool，True=不可达（风险正类，D-004 二分类）
    radius: float          # 工具球半径（体素）


def split_by_model(models, frac_train=0.7, frac_val=None, seed=0):
    """按模型切分（split.by=model；禁按点随机切分，见 configs/oracle_params.yaml）。

    frac_val=None → 返回 (train, test)（2-way；在内存快评/薄纵切用）；
    frac_val 给值 → 返回 (train, val, test)（物化数据集用，落地 D-016 切分 {train,val,test}）。
    注：val 为**预留 held-out**——超参先验固定、当前工具（cross_model_prediction/eval_*/regression_check）均未在 val 上调参（见各 tool 的 `_fva` 丢弃）。
    """
    import numpy as np
    idx = np.arange(len(models))
    np.random.default_rng(seed).shuffle(idx)
    n = len(models)
    n_tr = int(round(n * frac_train))
    if frac_val is None:
        return [models[i] for i in idx[:n_tr]], [models[i] for i in idx[n_tr:]]
    n_va = int(round(n * frac_val))
    return ([models[i] for i in idx[:n_tr]],
            [models[i] for i in idx[n_tr:n_tr + n_va]],
            [models[i] for i in idx[n_tr + n_va:]])
