#!/usr/bin/env python3
"""Audit denominators and non-neural baselines for the E5 direction task.

The script mirrors ``tools/eval_e5.py`` exactly for its first ``max_models``
manifest records (including single-class records) and its 0.7/0.3 model split,
but does not train a network. It recomputes the signed D-020 refined direction
labels, then reports eligible-point counts, viable-direction prevalence, a
random-ranking expectation, and a train-set global direction-prior ranking.
These quantities are explanatory additions to E5; they do not replace the
retained E5 headline artifact.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def _topk_stats(order, viable, k):
    import numpy as np

    chosen = order[:k]
    hit = np.asarray(viable[:, chosen].any(axis=1), bool)
    precision = np.asarray(viable[:, chosen].mean(axis=1), float)
    return float(hit.mean()), float(precision.mean())


def _compute_refined_model(task):
    """Load one manifest record and recompute its D-020 direction labels.

    Workers receive paths rather than model arrays so Windows spawn does not
    pickle the full 3-D occupancy and mesh payload for every task.
    """
    name, npz_path, radius, data_root, mesh_path, n_directions, resolution = task
    import numpy as np
    from support_accessibility.data.dataset import load_model
    from support_accessibility.data.fusion360 import load_obj, normalize
    from support_accessibility.data import mesh as MESH
    from support_accessibility.oracle import SupportAccessibilityOracle

    model = load_model(os.path.join(data_root, npz_path), name, radius)
    V, F = load_obj(mesh_path)
    Vn, _ = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=resolution)
    if occ.shape != model.occ.shape or not np.array_equal(occ, np.asarray(model.occ, bool)):
        raise RuntimeError(f"Occupancy mismatch for {name}; refusing mixed semantics")
    oracle = SupportAccessibilityOracle(
        model.occ,
        {"n_directions": n_directions},
        mesh=(Vn, F, lo, pitch),
    )
    viable = np.stack(
        [oracle.direction_labels(point, model.radius) for point in model.points]
    ).astype(bool)
    return name, viable


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/processed/fusion360_full")
    parser.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    parser.add_argument("--max-models", type=int, default=500)
    parser.add_argument("--n-directions", type=int, default=128)
    parser.add_argument("--resolution", type=int, default=48)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    import json
    import math
    import numpy as np
    from artifacts import write_result
    from support_accessibility.data import split_by_model
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data.fusion360 import iter_final_designs

    models, manifest = load_dataset(args.data)
    # eval_e5 applies --max-models before any class filtering; preserve that
    # cohort so the denominator audit is comparable to the published E5 run.
    models = models[: args.max_models]
    mesh_paths = dict(iter_final_designs(args.root))
    tasks = []
    for model, row in zip(models, manifest):
        path = mesh_paths.get(model.name)
        if path is None:
            raise FileNotFoundError(f"Missing Fusion mesh for {model.name}")
        tasks.append((
            model.name,
            row["npz_path"],
            float(model.radius),
            args.data,
            path,
            args.n_directions,
            args.resolution,
        ))

    viable_by_name = {}
    if args.workers <= 1:
        for index, task in enumerate(tasks, start=1):
            name, viable = _compute_refined_model(task)
            viable_by_name[name] = viable
            if index % 25 == 0 or index == len(tasks):
                print(f"refined labels {index}/{len(tasks)}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(_compute_refined_model, task) for task in tasks]
            for index, future in enumerate(as_completed(futures), start=1):
                name, viable = future.result()
                viable_by_name[name] = viable
                if index % 25 == 0 or index == len(tasks):
                    print(f"refined labels {index}/{len(tasks)}", flush=True)
    items = [(model.name, viable_by_name[model.name]) for model in models]

    train, test = split_by_model(items, frac_train=0.7, seed=0)
    train_viable = np.concatenate([row for _name, row in train], axis=0)
    test_viable = np.concatenate([row for _name, row in test], axis=0)
    D = int(test_viable.shape[1])
    n_viable = test_viable.sum(axis=1).astype(int)
    eligible = n_viable > 0
    eligible_viable = test_viable[eligible]

    global_order = np.argsort(-train_viable.mean(axis=0), kind="stable")
    prior = {}
    for k in (1, 3):
        hit, precision = _topk_stats(global_order, eligible_viable, k)
        prior[f"top{k}_hit"] = hit
        prior[f"top{k}_precision"] = precision

    denominator = math.comb(D, 3)
    random_top3 = []
    for count in n_viable[eligible]:
        blocked = D - int(count)
        no_hit = math.comb(blocked, 3) / denominator if blocked >= 3 else 0.0
        random_top3.append(1.0 - no_hit)

    bins = {
        "0": int((n_viable == 0).sum()),
        "1-2": int(((n_viable >= 1) & (n_viable <= 2)).sum()),
        "3-5": int(((n_viable >= 3) & (n_viable <= 5)).sum()),
        "6+": int((n_viable >= 6).sum()),
    }
    total = int(n_viable.size)
    rep = {
        "kind": "paper_direction_audit",
        "data": args.data,
        "root": args.root,
        "max_models": int(args.max_models),
        "workers": int(args.workers),
        "models_materialized": len(models),
        "both_class_models": int(sum(
            bool(np.asarray(model.labels).size)
            and bool(np.asarray(model.labels).any())
            and bool((~np.asarray(model.labels)).any())
            for model in models
        )),
        "cohort_names_sha256": hashlib.sha256(
            "\n".join(model.name for model in models).encode("utf-8")
        ).hexdigest(),
        "all_points": int(sum(np.asarray(model.points).shape[0] for model in models)),
        "train_models": len(train),
        "test_models": len(test),
        "n_directions": D,
        "target_mode": "refined(D-020)",
        "occupancy_fallback": 0,
        "test_points": total,
        "eligible_points": int(eligible.sum()),
        "eligible_fraction": float(eligible.mean()),
        "direction_viable_fraction_all_points": float(test_viable.mean()),
        "direction_viable_fraction_eligible_points": float(eligible_viable.mean()),
        "viable_count_mean_all_points": float(n_viable.mean()),
        "viable_count_median_all_points": float(np.median(n_viable)),
        "viable_count_distribution": bins,
        "viable_count_distribution_fraction": {
            key: value / total for key, value in bins.items()
        },
        "random_baseline": {
            "top1_hit": float(eligible_viable.mean()),
            "top3_hit": float(np.mean(random_top3)),
            "top3_precision": float(eligible_viable.mean()),
        },
        "global_direction_prior_baseline": prior,
        "global_direction_viable_frequency": train_viable.mean(axis=0).tolist(),
        "split": "first max_models manifest records; 0.7/0.3 model split; seed 0 (mirrors eval_e5)",
        "note": "Counts and baselines are denominator audits for E5 Top-k metrics; they are not new neural performance claims.",
    }
    enriched = write_result(
        "paper_direction_audit",
        rep,
        inputs=(
            os.path.join(args.data, "manifest.csv"),
            os.path.join(args.data, "dataset.json"),
            __file__,
        ),
    )
    print("DIRECTION_AUDIT " + json.dumps(enriched, ensure_ascii=False))


if __name__ == "__main__":
    main()
