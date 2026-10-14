#!/usr/bin/env python3
"""重复随机留出：切分随机性下的未见零件表现。

在全部 Fusion 两类零件上做 5 次随机的零件级 0.6/0.2/0.2 留出（切分种子 0..4），训练集为训练切分加程序化零件，
训练流程与固定留出模型相同。每次报告零件等权 F1 / IoU（每个测试零件一个分数再平均）、零件 F1 的中位数与
四分位距（反映难零件的长尾），以及点池 F1。五次留出的测试集可以重叠，不是 K 折交叉验证。

用法：
  python experiments/cross_model_prediction.py --seeds 5 --epochs 80
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def main():
    ap = argparse.ArgumentParser(description="重复随机留出：零件等权与点池指标")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/cross_model_prediction/result.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import mean_std, predict_proba, train_convonet      # 同目录脚本
    from support_accessibility import eval as E
    from support_accessibility.data import both_class, split_by_model
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.runtime.run_records import write_result

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fusion = both_class(load_dataset(a.fusion)[0])
    procedural = load_dataset(a.procedural)[0]

    runs = []
    for seed in range(a.seeds):
        train, _val, test = split_by_model(fusion, frac_train=0.6, frac_val=0.2, seed=seed)
        net = train_convonet(train + procedural, a.epochs, seed, dev, log=False)
        preds = [predict_proba(net, m, dev) >= 0.5 for m in test]
        golds = [np.asarray(m.labels, bool) for m in test]
        f1 = np.array([E.f1_inaccessible(p, g) for p, g in zip(preds, golds)])
        iou = np.array([E.iou_inaccessible(p, g) for p, g in zip(preds, golds)])
        q1, median, q3 = np.percentile(f1, [25, 50, 75])
        runs.append({"seed": seed, "n_test_models": len(test),
                     "part_f1_mean": float(f1.mean()), "part_iou_mean": float(iou.mean()),
                     "part_f1_median": float(median), "part_f1_iqr": float(q3 - q1),
                     "part_f1_zero_fraction": float(np.mean(f1 == 0.0)),
                     "pooled_f1": float(E.f1_inaccessible(np.concatenate(preds), np.concatenate(golds)))})
        print(json.dumps(runs[-1], ensure_ascii=False), flush=True)

    summary = {k: mean_std([r[k] for r in runs]) for k in runs[0] if k not in ("seed", "n_test_models")}
    rep = write_result("cross_model_prediction", {
        "device": dev, "epochs": a.epochs, "fusion_models": len(fusion), "procedural_models": len(procedural),
        "split": "repeated part-level 0.6/0.2/0.2 holdout over all Fusion both-class parts (split seeds 0..N-1)",
        **{f"{k}_mean": v[0] for k, v in summary.items()}, **{f"{k}_std": v[1] for k, v in summary.items()},
        "runs": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in runs],
    }, a.out, (a.fusion, a.procedural))
    print("CROSS_MODEL_PREDICTION " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
