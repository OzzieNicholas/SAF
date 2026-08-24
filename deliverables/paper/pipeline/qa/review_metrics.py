#!/usr/bin/env python3
"""Stage-3 review metrics: reproduce H3 and emit model-level summaries.

This utility deliberately mirrors ``tools/train_convonet.py``.  It does not
change the frozen split or label semantics; it only retains per-model scores
that the original headline runner did not serialize.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
_SRC = os.path.join(_ROOT, "src")
_TOOLS = os.path.join(_ROOT, "tools")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
try:
    from data_paths import resolve_data_paths
except ImportError:
    from tools.data_paths import resolve_data_paths


def summarize_score_distribution(values):
    """Return JSON-safe descriptive statistics for a per-model score vector."""
    import numpy as np

    scores = np.asarray(values, dtype=float).reshape(-1)
    if scores.size == 0:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "median": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "zero_fraction": None,
        }
    if not np.isfinite(scores).all():
        raise ValueError("score distributions must contain finite values")

    q1, median, q3 = np.percentile(scores, [25, 50, 75])
    return {
        "count": int(scores.size),
        "mean": float(scores.mean()),
        "std": float(scores.std()),
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "zero_fraction": float(np.mean(scores == 0.0)),
    }


def both_class(models):
    import numpy as np

    return [
        m for m in models
        if np.asarray(m.labels).size
        and np.asarray(m.labels).any()
        and (~np.asarray(m.labels)).any()
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description="Reproduce H3 with per-model metrics")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360_full")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural_v1")))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--max-models", type=int, default=None)
    ap.add_argument(
        "--out",
        default=None,
        help="result path; defaults to artifacts/runs/paper_review_metrics/latest.json",
    )
    args = ap.parse_args()

    import numpy as np
    import torch
    from artifacts import write_result
    from support_accessibility import eval as E
    from support_accessibility.data import split_by_model
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    device = "cuda" if torch.cuda.is_available() else "cpu"
    fusion, _ = load_dataset(args.fusion)
    procedural, _ = load_dataset(args.procedural)
    fusion = both_class(fusion)
    if args.max_models:
        fusion = fusion[: args.max_models]

    def prep(model):
        occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape).to(device)
        coords = to_grid_coords(model.points, model.occ.shape).to(device)
        labels = torch.as_tensor(np.asarray(model.labels, np.float32)).to(device)
        return occ, coords, labels

    rows = []
    for seed in range(args.seeds):
        train, _val, test = split_by_model(fusion, frac_train=0.6, frac_val=0.2, seed=seed)
        test = [m for m in test if m.points.shape[0] > 0]
        torch.manual_seed(seed)
        net = ConvONetLite().to(device)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
        loss = torch.nn.BCEWithLogitsLoss()
        data = [prep(m) for m in train + procedural]
        for _ in range(args.epochs):
            net.train()
            for i in torch.randperm(len(data)):
                occ, coords, labels = data[i]
                opt.zero_grad()
                loss(net(occ, coords), labels).backward()
                opt.step()

        net.eval()
        per_model = []
        with torch.no_grad():
            for model in test:
                occ, coords, _ = prep(model)
                pred = (torch.sigmoid(net(occ, coords)) >= 0.5).cpu().numpy()
                gold = np.asarray(model.labels, bool)
                per_model.append({
                    "name": model.name,
                    "n_points": int(gold.size),
                    "f1": float(E.f1_inaccessible(pred, gold)),
                    "iou": float(E.iou_inaccessible(pred, gold)),
                })
        f1 = np.asarray([x["f1"] for x in per_model], float)
        iou = np.asarray([x["iou"] for x in per_model], float)
        f1_distribution = summarize_score_distribution(f1)
        iou_distribution = summarize_score_distribution(iou)
        rows.append({
            "seed": seed,
            "n_test_models": len(per_model),
            "model_macro_f1": float(f1.mean()) if f1.size else 0.0,
            "model_macro_iou": float(iou.mean()) if iou.size else 0.0,
            "model_median_f1": float(np.median(f1)) if f1.size else 0.0,
            "model_q1_f1": float(np.percentile(f1, 25)) if f1.size else 0.0,
            "model_q3_f1": float(np.percentile(f1, 75)) if f1.size else 0.0,
            "model_f1_distribution": f1_distribution,
            "model_iou_distribution": iou_distribution,
            "per_model": per_model,
        })
        print(json.dumps({k: v for k, v in rows[-1].items() if k != "per_model"}, ensure_ascii=False), flush=True)

    macro = np.asarray([r["model_macro_f1"] for r in rows], float)
    macro_iou = np.asarray([r["model_macro_iou"] for r in rows], float)
    median_f1 = np.asarray(
        [r["model_f1_distribution"]["median"] for r in rows
         if r["model_f1_distribution"]["median"] is not None],
        float,
    )
    iqr_f1 = np.asarray(
        [r["model_f1_distribution"]["iqr"] for r in rows
         if r["model_f1_distribution"]["iqr"] is not None],
        float,
    )
    median_iou = np.asarray(
        [r["model_iou_distribution"]["median"] for r in rows
         if r["model_iou_distribution"]["median"] is not None],
        float,
    )
    iqr_iou = np.asarray(
        [r["model_iou_distribution"]["iqr"] for r in rows
         if r["model_iou_distribution"]["iqr"] is not None],
        float,
    )
    rep = {
        "kind": "paper_review_metrics",
        "device": device,
        "seeds": args.seeds,
        "epochs": args.epochs,
        "fusion_models": len(fusion),
        "procedural_models": len(procedural),
        "split": "repeated model-level 0.6/0.2/0.2 holdout (same as train_convonet.py)",
        "model_macro_f1_mean": float(macro.mean()) if macro.size else 0.0,
        "model_macro_f1_std": float(macro.std()) if macro.size else 0.0,
        "model_macro_iou_mean": float(macro_iou.mean()) if macro_iou.size else 0.0,
        "model_macro_iou_std": float(macro_iou.std()) if macro_iou.size else 0.0,
        "repeat_model_median_f1_mean": float(median_f1.mean()) if median_f1.size else None,
        "repeat_model_median_f1_std": float(median_f1.std()) if median_f1.size else None,
        "repeat_model_f1_iqr_mean": float(iqr_f1.mean()) if iqr_f1.size else None,
        "repeat_model_f1_iqr_std": float(iqr_f1.std()) if iqr_f1.size else None,
        "repeat_model_median_iou_mean": float(median_iou.mean()) if median_iou.size else None,
        "repeat_model_median_iou_std": float(median_iou.std()) if median_iou.size else None,
        "repeat_model_iou_iqr_mean": float(iqr_iou.mean()) if iqr_iou.size else None,
        "repeat_model_iou_iqr_std": float(iqr_iou.std()) if iqr_iou.size else None,
        "runs": rows,
    }
    rep = write_result(
        "paper_review_metrics",
        rep,
        output=args.out,
        inputs=(args.fusion, args.procedural),
    )
    print("REVIEW_METRICS " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
