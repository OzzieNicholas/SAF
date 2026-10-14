#!/usr/bin/env python3
"""跨来源评测（D-022）：固定留出模型在 Thingi10K 两类零件上的不可达 F1。

模型就是 experiments/holdout_model.py 的多种子权重（只在 Fusion 与程序化零件上训练），与 Fusion 固定留出集上的
结果直接可比。Thingi10K 网格来自打印社区，缠绕与流形质量更差，只用于测试。同时给出两种几何代理
（零半径射线、16 方向粗判定）在同一子集上的 F1。

用法：
  python experiments/cross_domain_robustness.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def main():
    ap = argparse.ArgumentParser(description="跨来源评测：固定留出模型在 Thingi10K 两类零件上的表现（D-022）")
    paths = resolve_data_paths()
    ap.add_argument("--thingi", default=str(paths.processed_root("thingi10k")))
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/cross_domain_robustness/result.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import load_holdout_models, mean_std, predict_proba      # 同目录脚本
    from support_accessibility import baselines as B, eval as E
    from support_accessibility.data import both_class
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.runtime.run_records import write_result

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    parts = both_class(load_dataset(a.thingi)[0])
    gold = np.concatenate([np.asarray(m.labels, bool) for m in parts])
    nets = load_holdout_models(dev)
    print(f"device={dev} thingi both-class parts={len(parts)} points={gold.size}", flush=True)

    f1s, ious = [], []
    for seed, net, _ck in nets:
        pred = np.concatenate([predict_proba(net, m, dev) >= 0.5 for m in parts])
        f1s.append(E.f1_inaccessible(pred, gold)); ious.append(E.iou_inaccessible(pred, gold))
        print(f"seed {seed}: F1 {f1s[-1]:.4f}", flush=True)
    ray = np.concatenate([B.ray_visibility(m.occ, m.points) for m in parts])
    coarse = np.concatenate([B.voxel_judgment(m.occ, m.points, m.radius, 16) for m in parts])
    f1_m, f1_s = mean_std(f1s)
    rep = write_result("cross_domain_robustness", {
        "model_run": "holdout_model", "training_seeds": [s for s, _n, _c in nets],
        "thingi_bothclass": len(parts), "thingi_pts": int(gold.size),
        "thingi_gold_inacc_frac": round(float(gold.mean()), 4),
        "crossdomain_f1_mean": f1_m, "crossdomain_f1_std": f1_s,
        "crossdomain_f1_by_seed": [round(float(v), 4) for v in f1s],
        "crossdomain_iou_mean": mean_std(ious)[0],
        "crossdomain_rayvis_f1": round(float(E.f1_inaccessible(ray, gold)), 4),
        "crossdomain_coarse16_f1": round(float(E.f1_inaccessible(coarse, gold)), 4),
    }, a.out, (a.thingi,))
    print("CROSS_DOMAIN_ROBUSTNESS " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
