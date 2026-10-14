#!/usr/bin/env python3
"""误差分析：固定留出模型在留出零件上的误判出现在哪里。

读取 experiments/holdout_model.py 的多种子权重（与基线对照、消融为同一组模型）。每个接触点的几何难度
用「可达方向数」刻画：两级判定器在 64 个下半球方向上逐方向判定（与点级标签同一细化口径），
0 个即不可达，1–5 个为余量临界，≥6 个为开阔。报告整体误判率、误报与漏报拆分，以及按可达方向数分箱的
误判率（训练种子间均值 ± 标准差）。

用法：
  python experiments/failure_analysis.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()

BINS = {"0": (0, 0), "1-2": (1, 2), "3-5": (3, 5), "6+": (6, None)}


def main():
    ap = argparse.ArgumentParser(description="误差分析（按可达方向数分箱）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root), help="Fusion 原始网格目录（生成细化方向标签）")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/failure_analysis/result.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, load_holdout_models, mean_std, predict_proba, refined_direction_labels
    from support_accessibility import eval as E
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.runtime.run_records import write_result

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    _train, _val, test = holdout_split(load_dataset(a.fusion)[0])
    nets = load_holdout_models(dev)
    viable = refined_direction_labels(test, a.fusion, a.root, a.workers)
    n_viable = np.concatenate([viable[m.name].sum(axis=1) for m in test])
    gold = np.concatenate([np.asarray(m.labels, bool) for m in test])
    bins = {k: (n_viable >= lo) & (n_viable <= (hi if hi is not None else n_viable.max())) for k, (lo, hi) in BINS.items()}
    print(f"device={dev} test={len(test)} points={gold.size} seeds={[s for s, _n, _c in nets]}", flush=True)

    runs = []
    for seed, net, _ck in nets:
        pred = np.concatenate([predict_proba(net, m, dev) >= 0.5 for m in test])
        err = pred != gold
        runs.append({"f1": float(E.f1_inaccessible(pred, gold)), "error": float(err.mean()),
                     "false_alarm": float((pred & ~gold).mean()), "missed": float((~pred & gold).mean()),
                     **{f"bin_{k}": float(err[v].mean()) for k, v in bins.items()}})
        print(f"seed {seed}: " + " ".join(f"{k}={v:.3f}" for k, v in runs[-1].items()), flush=True)

    def stat(key):
        return mean_std([r[key] for r in runs])

    rep = write_result("failure_analysis", {
        "training_seeds": [s for s, _n, _c in nets], "test_models": len(test), "test_points": int(gold.size),
        "direction_semantics": "two-stage refined direction labels (same semantics as point labels)",
        "f1_inaccessible": stat("f1")[0], "f1_inaccessible_std": stat("f1")[1],
        "error_rate": stat("error")[0], "error_rate_std": stat("error")[1],
        "false_alarm_rate": stat("false_alarm")[0], "false_alarm_rate_std": stat("false_alarm")[1],
        "missed_rate": stat("missed")[0], "missed_rate_std": stat("missed")[1],
        "error_rate_by_nviable": {k: stat(f"bin_{k}")[0] for k in BINS},
        "error_rate_by_nviable_std": {k: stat(f"bin_{k}")[1] for k in BINS},
        "nviable_share": {k: round(float(v.mean()), 4) for k, v in bins.items()},
    }, a.out, (a.fusion, a.root))
    print("FAILURE_ANALYSIS " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
