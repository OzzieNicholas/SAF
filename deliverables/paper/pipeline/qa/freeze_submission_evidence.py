#!/usr/bin/env python3
"""Freeze current machine-readable evidence inputs for the anonymous manuscript."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


RUN_SPECS = (
    ("baselines", "artifacts/runs/baselines/latest.json", "baselines"),
    ("ablation", "artifacts/runs/ablation/latest.json", "ablation"),
    ("failure_audit", "artifacts/runs/failure_audit/failure.json", "failure_audit"),
    ("regression", "artifacts/runs/regression/latest.json", "regression"),
    ("paper_review_metrics", "artifacts/runs/paper_review_metrics/latest.json", "paper_review_metrics"),
    ("mesh_quality", "artifacts/runs/mesh_quality/latest.json", "mesh_quality"),
    ("e5", "artifacts/runs/e5/latest.json", "e5"),
    ("paper_direction_audit", "artifacts/runs/paper_direction_audit/latest.json", "paper_direction_audit"),
)

HISTORICAL_SOURCES = {
    "true_area": {
        "path": "artifacts/runs/true_area/latest.json",
        "status": "legacy_non_envelope",
        "scope": "full-corpus triangle-area correlation; retained for descriptive H1 context only",
    },
    "cross_domain_h5": {
        "path": "artifacts/runs/paper_rewrite/h5_eval_20260814.json",
        "status": "captured_historical_output",
        "scope": "three-seed fixed-subset cross-domain evaluation; not rerun in this evidence refresh",
    },
}


def _inside_root(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"Evidence path escapes repository root: {resolved_path}") from exc
    return resolved_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_entry(root: Path, relative_path: str, expected_kind: str) -> dict[str, str]:
    """Validate one retained result and return its immutable manifest reference."""
    path = _inside_root(root, root / relative_path)
    if not path.is_file():
        raise RuntimeError(f"Canonical evidence is missing: {relative_path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read canonical evidence {relative_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Canonical evidence must be an object: {relative_path}")
    if value.get("artifact_schema_version") != 1:
        raise RuntimeError(f"Canonical evidence has unsupported schema: {relative_path}")
    if value.get("kind") != expected_kind:
        raise RuntimeError(
            f"Canonical evidence kind mismatch for {relative_path}: "
            f"expected {expected_kind!r}, got {value.get('kind')!r}"
        )
    run_id = value.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise RuntimeError(f"Canonical evidence has no run_id: {relative_path}")
    command = value.get("command", "")
    if not isinstance(command, str):
        raise RuntimeError(f"Canonical evidence command is invalid: {relative_path}")
    return {
        "path": Path(relative_path).as_posix(),
        "sha256": _sha256(path),
        "run_id": run_id,
        "command": command,
    }


def build_payload(root: Path, manuscript_version: str) -> dict[str, object]:
    """Build the paper-rewrite payload from exactly the declared current runs."""
    canonical_runs = {
        name: canonical_entry(root, relative_path, expected_kind)
        for name, relative_path, expected_kind in RUN_SPECS
    }
    historical_sources = {}
    for name, source in HISTORICAL_SOURCES.items():
        relative_path = source["path"]
        path = _inside_root(root, root / relative_path)
        if not path.is_file():
            raise RuntimeError(f"Historical evidence is missing: {relative_path}")
        historical_sources[name] = {
            **source,
            "sha256": _sha256(path),
        }
    return {
        "manuscript_version": manuscript_version,
        "scope": (
            "potential support-contact proxy; part-body occlusion only; finite spherical tool; "
            "discrete straight approaches; fixed r=0.05, +z, 45 degrees, and 128/64 directions"
        ),
        "source_revision": "working tree; file-level evidence hashes are frozen below",
        "canonical_runs": canonical_runs,
        "historical_sources": historical_sources,
        "statistical_rules": {
            "positive_class": "inaccessible",
            "split_unit": "model-level",
            "repeat_holdout": "five repeated 0.6/0.2/0.2 random model holdouts; test sets may overlap",
            "geometry_hierarchy": (
                "full 128-global/64-lower-direction refined oracle supplies labels; "
                "the 16-global/8-lower-direction finite-tool result is a coarse proxy; "
                "the neural model is a shape-conditioned surrogate"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="deliverables/paper/evidence/manifest.json",
        help="canonical manifest path relative to the repository root",
    )
    parser.add_argument("--version", default="2026-08-15-submission-evidence-v2")
    args = parser.parse_args()

    from artifacts import run_metadata

    payload = build_payload(ROOT, args.version)
    inputs = tuple(relative_path for _name, relative_path, _kind in RUN_SPECS) + tuple(
        source["path"] for source in HISTORICAL_SOURCES.values()
    )
    target = Path(args.out)
    if not target.is_absolute():
        target = ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    record = run_metadata("paper_rewrite", inputs=inputs)
    record.update(payload)
    record["output"] = target.relative_to(ROOT).as_posix()
    target.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("PAPER_EVIDENCE " + json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
