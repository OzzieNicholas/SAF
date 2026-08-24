#!/usr/bin/env python3
"""Run the publication-scale synthetic differential audit for D-003/D-025.

The fast EDT/ray-march oracle and the brute-force reference are independent
discrete approximations.  D-025 accepts a batch robust-mismatch rate no greater
than one percent after the operational radius-neighbourhood check.  This tool
uses one deterministic occupancy per integer seed, records every non-exact
seed, and emits a retained run artifact for the manuscript integrity report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[4]
for path in (ROOT / "src", ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _case(seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    size = int(rng.integers(14, 19))
    occupancy = rng.random((size, size, size)) < float(rng.uniform(0.2, 0.4))
    free = np.argwhere(~occupancy)
    if not len(free):
        raise RuntimeError(f"seed {seed} generated no free voxel")
    point = tuple(free[rng.integers(len(free))].astype(float))
    radius = float(rng.uniform(1.0, 3.5))
    return occupancy, point, radius


def _labels(oracle, point, radius: float) -> tuple[str, str]:
    return oracle.label(point, radius).value, oracle.reference_label(point, radius).value


def _classify(oracle, point, radius: float, epsilon: float) -> tuple[str, dict[str, object]]:
    base = _labels(oracle, point, radius)
    offsets = {
        f"{delta:+g}": _labels(oracle, point, radius + delta)
        for delta in (-epsilon, epsilon)
    }
    if base[0] == base[1]:
        verdict = "exact"
    elif all(pair[0] == pair[1] for pair in offsets.values()):
        verdict = "operational_boundary"
    else:
        verdict = "robust_mismatch"
    detail = {
        "point": [float(value) for value in point],
        "radius": radius,
        "fast": base[0],
        "reference": base[1],
        "offset_labels": {
            key: {"fast": pair[0], "reference": pair[1]}
            for key, pair in offsets.items()
        },
    }
    return verdict, detail


def run_audit(
    cases: int,
    seed_start: int,
    n_directions: int,
    epsilon: float,
    threshold: float,
) -> dict[str, object]:
    from support_accessibility.oracle import SupportAccessibilityOracle

    counts = {"exact": 0, "operational_boundary": 0, "robust_mismatch": 0}
    boundary_seeds: list[int] = []
    robust_rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for seed in range(seed_start, seed_start + cases):
        occupancy, point, radius = _case(seed)
        oracle = SupportAccessibilityOracle(
            occupancy,
            {"n_directions": n_directions, "epsilon_voxels": 1.5},
        )
        verdict, detail = _classify(oracle, point, radius, epsilon)
        counts[verdict] += 1
        if verdict == "operational_boundary":
            boundary_seeds.append(seed)
        elif verdict == "robust_mismatch":
            robust_rows.append({"seed": seed, **detail})

    robust_rate = counts["robust_mismatch"] / max(cases, 1)
    boundary_rate = counts["operational_boundary"] / max(cases, 1)
    strict_rate = counts["exact"] / max(cases, 1)
    return {
        "audit_version": "D-025-synthetic-v1",
        "cases": cases,
        "seed_range": [seed_start, seed_start + cases - 1],
        "n_directions": n_directions,
        "radius_neighbourhood_epsilon_voxels": epsilon,
        "robust_mismatch_threshold": threshold,
        "counts": counts,
        "strict_agreement_rate": round(strict_rate, 6),
        "operational_boundary_rate": round(boundary_rate, 6),
        "robust_mismatch_rate": round(robust_rate, 6),
        "passes_d025": robust_rate <= threshold,
        "robust_mismatches": robust_rows,
        "operational_boundary_seeds": boundary_seeds,
        "known_seed_882_included": seed_start <= 882 < seed_start + cases,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "criterion": "robust_mismatch_rate <= 0.01 (D-025)",
        "interpretation": (
            "The r±epsilon comparison is an operational discrepancy classifier, not a proof "
            "of radius monotonicity; D-008 records that point-touch semantic C is not radius "
            "monotone on unrestricted geometry."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="D-025 publication-scale synthetic differential audit")
    parser.add_argument("--cases", type=int, default=10_000)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--n-directions", type=int, default=32)
    parser.add_argument("--epsilon", type=float, default=0.75)
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument(
        "--out",
        default="artifacts/runs/paper_integrity/differential_latest.json",
    )
    args = parser.parse_args()
    if args.cases <= 0:
        parser.error("--cases must be positive")
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be in [0, 1]")

    from artifacts import write_result

    payload = run_audit(
        cases=args.cases,
        seed_start=args.seed_start,
        n_directions=args.n_directions,
        epsilon=args.epsilon,
        threshold=args.threshold,
    )
    result = write_result(
        "paper_integrity_differential",
        payload,
        output=args.out,
        inputs=(
            "src/support_accessibility/oracle/__init__.py",
            "tests/acceptance/test_differential.py",
            "governance/decisions.md",
            "configs/params.yaml",
        ),
    )
    print("PAPER_DIFFERENTIAL " + json.dumps(result, ensure_ascii=False))
    return 0 if result["passes_d025"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
