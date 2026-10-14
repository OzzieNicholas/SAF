#!/usr/bin/env python3
"""全分布筛查评测：固定留出模型在全部未参与训练的 Fusion 零件上（含全可达的单类件）的表现。

主实验只在两类件上评测，回答「零件确有风险时能否认出风险点」；本实验回答设计筛查真正面对的问题：
在真实零件分布里，模型会对多少本无风险的零件报警，能否把有风险的零件排在前面。
评测集 = Fusion 全部物化件 − 固定留出模型的训练与验证零件。对照为零半径射线可见性（128 方向）
与粗有限工具代理（16 全局方向，无细化），二者在同一点集上逐点计算。

指标：
  零件级  真值 = 零件含至少一个不可达点；网络以零件内最大概率排序得 ROC/AUROC，
          三种方法在各自工作点（任一点判不可达即报警）给出检出率与全可达件误报率；
  点级    全评测集点池 F1；全可达件上被误判为不可达的点占比；
  占比    两类件上预测与真实不可达点占比的 Spearman ρ。

用法：
  python experiments/screening_evaluation.py --workers 16
"""
import argparse
import os

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()

COARSE_DIRECTIONS = 16


def _geometric_flags(task):
    """工作进程：载入一件，返回 (name, 射线可见性预测, 粗代理预测)。传路径而非数组，避免 Windows spawn 序列化大数组。"""
    name, npz_path, radius = task
    import numpy as np
    from support_accessibility.data.dataset import load_model
    from support_accessibility import baselines as B
    m = load_model(npz_path, name, radius)
    ray = B.ray_visibility(m.occ, m.points, FROZEN.n_directions)
    coarse = B.voxel_judgment(m.occ, m.points, m.radius, COARSE_DIRECTIONS)
    return name, np.asarray(ray, bool), np.asarray(coarse, bool)


def auroc(scores, truth):
    """秩和法 AUROC（并列取平均秩）；单类时返回 None。"""
    import numpy as np
    s = np.asarray(scores, float); y = np.asarray(truth, bool)
    n_pos, n_neg = int(y.sum()), int((~y).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(s.size); ranks[order] = np.arange(1, s.size + 1)
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.zeros(cnt.size); np.add.at(sums, inv, ranks)
    ranks = (sums / cnt)[inv]
    return float((ranks[y].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def roc_curve(scores, truth):
    """返回 (fpr, tpr) 数组，阈值取全部唯一分数（降序）。"""
    import numpy as np
    s = np.asarray(scores, float); y = np.asarray(truth, bool)
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    distinct = np.r_[np.flatnonzero(np.diff(s)), y.size - 1]
    tp = np.cumsum(y)[distinct]; fp = np.cumsum(~y)[distinct]
    return np.r_[0.0, fp / max(int((~y).sum()), 1)], np.r_[0.0, tp / max(int(y.sum()), 1)]


def main():
    ap = argparse.ArgumentParser(description="全分布筛查评测（含单类件）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None, help="只评前 N 件（试跑用）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/screening_evaluation/result.json（试跑请指定其他路径）")
    a = ap.parse_args()

    import json
    from concurrent.futures import ProcessPoolExecutor
    import numpy as np
    import torch
    from holdout_model import load_holdout_models, predict_proba      # 同目录脚本
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    nets = load_holdout_models(dev)
    ckpt = nets[0][2]
    used = set(ckpt["train_names"]) | set(ckpt["val_names"])
    fixed_test = set(ckpt["test_names"])
    models, rows = load_dataset(a.fusion)
    pairs = [(m, r) for m, r in zip(models, rows) if m.name not in used and m.points.shape[0] > 0]
    if a.limit:
        pairs = pairs[:a.limit]
    print(f"eval parts={len(pairs)} (excluded train+val={len(used)}) device={dev} seeds={len(nets)}", flush=True)

    probs = [{m.name: predict_proba(net, m, dev) for m, _ in pairs} for _s, net, _c in nets]
    print("network done", flush=True)

    ray, coarse = {}, {}
    tasks = [(m.name, os.path.join(a.fusion, r["npz_path"]), float(m.radius)) for m, r in pairs]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, (name, rv, cp) in enumerate(ex.map(_geometric_flags, tasks, chunksize=8)):
            ray[name], coarse[name] = rv, cp
            if (i + 1) % 500 == 0:
                print(f"geometric baselines {i + 1}/{len(tasks)}", flush=True)

    names = [m.name for m, _ in pairs]
    gold = {m.name: np.asarray(m.labels, bool) for m, _ in pairs}
    has_risk = np.array([gold[n].any() for n in names])
    both = np.array([gold[n].any() and (~gold[n]).any() for n in names])
    geometric = {"ray_r0_128": ray, "coarse_16": coarse}

    def summarize(pred):
        flag = np.array([pred[n].any() for n in names])
        P = np.concatenate([pred[n] for n in names]); G = np.concatenate([gold[n] for n in names])
        safe_pts = np.concatenate([pred[n] for n in names if not gold[n].any()]) if (~has_risk).any() else np.zeros(0, bool)
        frac_p = np.array([pred[n].mean() for n in names]); frac_g = np.array([gold[n].mean() for n in names])
        return {
            "part_detection_rate": round(float(flag[has_risk].mean()), 4),
            "part_false_alarm_rate": round(float(flag[~has_risk].mean()), 4) if (~has_risk).any() else None,
            "pooled_f1": round(float(E.f1_inaccessible(P, G)), 4),
            "pooled_f1_both_class_parts": round(float(E.f1_inaccessible(
                np.concatenate([pred[n] for n, b in zip(names, both) if b]),
                np.concatenate([gold[n] for n, b in zip(names, both) if b]))), 4),
            "point_false_positive_rate_on_safe_parts": round(float(safe_pts.mean()), 5) if safe_pts.size else None,
            "inacc_fraction_spearman_both_class": round(float(E.spearman(frac_p[both], frac_g[both])), 4),
        }

    per_seed = [summarize({n: prob[n] >= 0.5 for n in names}) for prob in probs]
    network = {}
    for key in per_seed[0]:
        vals = np.array([s[key] for s in per_seed], float)
        network[key] = round(float(vals.mean()), 4)
        network[key + "_std"] = round(float(vals.std()), 4)
    scores = [np.array([prob[n].max() for n in names]) for prob in probs]
    aucs = np.array([auroc(s, has_risk) for s in scores])
    rocs = []
    for s in scores:
        fpr, tpr = roc_curve(s, has_risk)
        keep = np.unique(np.r_[np.linspace(0, fpr.size - 1, 400).astype(int), fpr.size - 1])
        rocs.append({"fpr": [round(float(v), 5) for v in fpr[keep]], "tpr": [round(float(v), 5) for v in tpr[keep]]})
    in_fixed = np.array([n in fixed_test for n in names])
    rep = write_result("screening_evaluation", {
        "model_run": "holdout_model", "training_seeds": [s for s, _n, _c in nets],
        "n_eval_parts": len(names), "n_excluded_train_val": len(used),
        "n_parts_with_risk": int(has_risk.sum()), "n_safe_parts": int((~has_risk).sum()),
        "n_both_class_parts": int(both.sum()), "n_fixed_holdout_parts_included": int(in_fixed.sum()),
        "n_eval_points": int(sum(gold[n].size for n in names)),
        "coarse_directions": COARSE_DIRECTIONS, "reference_directions": FROZEN.n_directions,
        "network_part_auroc_max_prob": round(float(aucs.mean()), 4),
        "network_part_auroc_max_prob_std": round(float(aucs.std()), 4),
        "methods": {"network": network, **{k: summarize(v) for k, v in geometric.items()}},
        "network_by_seed": per_seed,
        "network_roc_by_seed": rocs,
        "part_scores": {"names": names, "max_prob_seed_mean": [round(float(v), 5) for v in np.mean(scores, axis=0)],
                        "has_risk": has_risk.astype(int).tolist(),
                        "ray_flag": [int(ray[n].any()) for n in names],
                        "coarse_flag": [int(coarse[n].any()) for n in names]},
    }, a.out, (a.fusion,))
    print("SCREENING " + json.dumps({k: v for k, v in rep.items() if k not in ("part_scores", "network_roc_by_seed")},
                                    ensure_ascii=False))


if __name__ == "__main__":
    main()
