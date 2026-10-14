#!/usr/bin/env python3
"""把论文引用的实验结果冻结进证据清单 ``paper/evidence/manifest.json``。

清单记录每个实验结果的路径、SHA-256、运行号和命令；论文只引用清单里的结果。
重跑任何实验后都要重新运行本脚本，再重新生成图件和数值核对。

用法：
  python -m paper.pipeline.audits.freeze_evidence
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from paper.pipeline.evidence import MANIFEST_KIND, SCHEMA_VERSION
from paper.pipeline.paths import EVIDENCE_MANIFEST
from support_accessibility.runtime.data_paths import REPO_ROOT

ROOT = REPO_ROOT

# 论文引用的实验：实验名即 artifacts/runs/<实验名>/result.json 的目录名和结果里的 kind。
CANONICAL_EXPERIMENTS = (
    "contact_area_vs_accessibility",
    "tool_radius_effect",
    "label_audit",
    "oracle_differential_audit",
    "mesh_quality_audit",
    "cross_model_prediction",
    "baseline_comparison",
    "shape_context_ablation",
    "cross_domain_robustness",
    "direction_field_prediction",
    "failure_analysis",
    "holdout_model",
    "cost_accuracy_frontier",
    "screening_evaluation",
    "orientation_evaluation",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def result_path(name: str) -> str:
    return f"artifacts/runs/{name}/result.json"


def canonical_entry(root: Path, name: str) -> dict[str, str]:
    """校验一份实验结果并返回它在清单里的不可变引用。"""
    relative_path = result_path(name)
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Evidence path escapes repository root: {path}") from exc
    if not path.is_file():
        raise RuntimeError(f"Canonical evidence is missing: {relative_path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read canonical evidence {relative_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Canonical evidence must be an object: {relative_path}")
    if value.get("artifact_schema_version") != SCHEMA_VERSION:
        raise RuntimeError(f"Canonical evidence has unsupported schema: {relative_path}")
    if value.get("kind") != name:
        raise RuntimeError(
            f"Canonical evidence kind mismatch for {relative_path}: expected {name!r}, got {value.get('kind')!r}"
        )
    run_id = value.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise RuntimeError(f"Canonical evidence has no run_id: {relative_path}")
    command = value.get("command", "")
    if not isinstance(command, str):
        raise RuntimeError(f"Canonical evidence command is invalid: {relative_path}")
    return {"path": relative_path, "sha256": _sha256(path), "run_id": run_id, "command": command}


def build_payload(root: Path) -> dict[str, object]:
    return {
        "scope": (
            "potential support-contact proxy; part-body occlusion only; finite spherical tool; "
            "discrete straight approaches; fixed r=0.05, +z, 45 degrees, and 128/64 directions"
        ),
        "canonical_runs": {name: canonical_entry(root, name) for name in CANONICAL_EXPERIMENTS},
        "statistical_rules": {
            "positive_class": "inaccessible",
            "split_unit": "model-level",
            "fixed_holdout": "first 400 both-class Fusion parts, split seed 0, 0.6/0.2/0.2; five training seeds; "
                             "baseline, ablation, failure, frontier, screening and orientation runs share these weights",
            "repeat_holdout": "five repeated 0.6/0.2/0.2 random model holdouts; test sets may overlap",
            "geometry_hierarchy": (
                "full 128-global/64-lower-direction refined oracle supplies labels; "
                "the 16-global/8-lower-direction finite-tool result is a coarse proxy; "
                "the neural model is a shape-conditioned surrogate"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(EVIDENCE_MANIFEST), help="清单路径；默认 paper/evidence/manifest.json")
    args = parser.parse_args()

    payload = build_payload(ROOT)
    target = Path(args.out)
    if not target.is_absolute():
        target = ROOT / target
    record = {"artifact_schema_version": SCHEMA_VERSION, "kind": MANIFEST_KIND}
    record.update(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"FROZEN {len(CANONICAL_EXPERIMENTS)} experiments -> {target.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
