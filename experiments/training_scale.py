#!/usr/bin/env python3
"""训练规模：把 Fusion 训练零件从固定协议的 240 件扩大到全部可用两类件，跨来源表现是否随之改善。

扩大后的训练集 = 全部 Fusion 两类件中除固定留出协议的验证与测试零件外的所有零件，加程序化零件；
训练流程、轮数与训练种子和 experiments/holdout_model.py 相同。在同一固定留出测试集（80 件）与 Thingi10K
两类件上评测，并按原始网格是否水密分组（逐件拓扑取自 mesh_quality_audit），与固定协议模型直接对照。
Thingi10K 只用于测试。

用法：
  python experiments/training_scale.py --seeds 5
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.run_records import RUN_ROOT

setup_console()


def main():
    ap = argparse.ArgumentParser(description="训练规模对固定留出集与跨来源表现的影响")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--thingi", default=str(paths.processed_root("thingi10k")))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/training_scale/result.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, mean_std, predict_proba, train_convonet      # 同目录脚本
    from support_accessibility import eval as E
    from support_accessibility.data import both_class
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.runtime.run_records import write_result

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fusion = load_dataset(a.fusion)[0]
    procedural = load_dataset(a.procedural)[0]
    _train, val, test = holdout_split(fusion)
    held = {m.name for m in val + test}
    train = [m for m in both_class(fusion) if m.name not in held]
    thingi = both_class(load_dataset(a.thingi)[0])
    with open(RUN_ROOT / "mesh_quality_audit" / "details.json", encoding="utf-8") as fh:
        watertight = {d["name"]: d["quality"]["is_watertight"] for d in json.load(fh)["sources"]
                      if d["source"] == "thingi10k" and d["status"] == "audited"}
    groups = {"thingi": thingi,
              "thingi_watertight": [m for m in thingi if watertight[m.name]],
              "thingi_not_watertight": [m for m in thingi if not watertight[m.name]],
              "fusion_holdout": test}
    print(f"device={dev} train={len(train)} (+proc {len(procedural)}) holdout={len(test)} thingi={len(thingi)}", flush=True)

    scores = {g: [] for g in groups}
    for seed in range(a.seeds):
        net = train_convonet(train + procedural, a.epochs, seed, dev, log=False)
        for g, parts in groups.items():
            pred = np.concatenate([predict_proba(net, m, dev) >= 0.5 for m in parts])
            gold = np.concatenate([np.asarray(m.labels, bool) for m in parts])
            scores[g].append(E.f1_inaccessible(pred, gold))
        print(f"seed {seed}: " + " ".join(f"{g}={v[-1]:.4f}" for g, v in scores.items()), flush=True)

    rep = write_result("training_scale", {
        "device": dev, "training_seeds": list(range(a.seeds)), "epochs": a.epochs,
        "train_rule": "all Fusion both-class parts except the fixed-holdout val/test parts, plus procedural parts",
        "n_train_models": len(train), "n_procedural": len(procedural),
        "n_parts": {g: len(p) for g, p in groups.items()},
        "f1": {g: dict(zip(("mean", "std"), mean_std(v))) for g, v in scores.items()},
        "f1_by_seed": {g: [round(float(x), 4) for x in v] for g, v in scores.items()},
    }, a.out, (a.fusion, a.procedural, a.thingi, RUN_ROOT / "mesh_quality_audit" / "details.json"))
    print("TRAINING_SCALE " + json.dumps({k: v for k, v in rep.items() if k != "f1_by_seed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
