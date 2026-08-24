#!/usr/bin/env python3
"""Validate the manuscript integrity sidecar and its local evidence links."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
TRACE_KEYS = {
    "artifact_id",
    "source_data",
    "transformation",
    "caption_claim",
    "supported_manuscript_claims",
    "limitations",
}
EXPERIMENT_KEYS = {
    "experiment_id",
    "title",
    "repro_lock",
    "planned_vs_executed",
    "negative_results",
    "known_limitations",
}
ALIGNMENT_KEYS = {
    "finding_id",
    "scoped_manifest_id",
    "claim_id",
    "claim_text",
    "experiment_id",
    "result_pointer",
    "manuscript_locator",
    "alignment_verdict",
    "rationale",
    "judge_model",
    "judge_run_at",
    "rule_version",
}
EXPECTED_ARTIFACTS = {
    *(f"fig{index:02d}" for index in range(1, 11)),
    *(f"table{index:02d}" for index in range(1, 7)),
}
BOUNDARY = (
    "This check verifies disclosure and claim-to-provenance fidelity. It does not judge "
    "whether the experiment was correctly designed, run, statistically adequate, or "
    "reproducible by ARS."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_source(source: dict[str, object], errors: list[str], root: Path = ROOT) -> None:
    raw = source.get("path")
    if not isinstance(raw, str) or not raw:
        errors.append("source_data entry has no path")
        return
    if bool(source.get("external")) or source.get("available") is False or raw.startswith("${SAF_"):
        return
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        errors.append(f"source path is missing: {raw}")
        return
    expected = source.get("sha256")
    if expected is not None:
        if not path.is_file():
            errors.append(f"hashed source is not a file: {raw}")
        elif _sha256(path).lower() != str(expected).lower():
            errors.append(f"source SHA-256 drift: {raw}")


def validate(
    sidecar: dict[str, object], *, root: Path = ROOT, paper_dir: Path | None = None
) -> dict[str, object]:
    """Validate a sidecar against an explicit repository/package root.

    ``root`` and ``paper_dir`` are injectable so the paper gate can validate a
    staged or temporary package without silently resolving links against the
    caller's checkout.
    """
    errors: list[str] = []
    warnings: list[str] = []

    traces = sidecar.get("figure_table_trace")
    if not isinstance(traces, list):
        errors.append("figure_table_trace must be an array")
        traces = []
    artifact_ids: list[str] = []
    for index, trace in enumerate(traces):
        if not isinstance(trace, dict):
            errors.append(f"trace {index} is not an object")
            continue
        missing = TRACE_KEYS - trace.keys()
        if missing:
            errors.append(f"trace {index} missing keys: {sorted(missing)}")
            continue
        artifact_id = str(trace["artifact_id"])
        artifact_ids.append(artifact_id)
        sources = trace["source_data"]
        if not isinstance(sources, list) or not sources:
            errors.append(f"{artifact_id}: source_data must be non-empty")
        else:
            for source in sources:
                if isinstance(source, dict):
                    _check_source(source, errors, root)
                else:
                    errors.append(f"{artifact_id}: source_data entry is not an object")
        transformation = trace["transformation"]
        if not isinstance(transformation, dict):
            errors.append(f"{artifact_id}: transformation is not an object")
        elif "script" in transformation:
            _check_source(
                {"path": transformation["script"], "sha256": transformation.get("sha256")},
                errors,
                root,
            )
            if not transformation.get("command"):
                errors.append(f"{artifact_id}: scripted transformation has no command")
        elif transformation.get("kind") == "manual_derivation":
            if not transformation.get("pointer") or not transformation.get("verification"):
                errors.append(f"{artifact_id}: manual derivation is not precise")
        else:
            errors.append(f"{artifact_id}: transformation is neither scripted nor manual")
        if not str(trace["caption_claim"]).strip():
            errors.append(f"{artifact_id}: empty caption claim")
        if not isinstance(trace["supported_manuscript_claims"], list):
            errors.append(f"{artifact_id}: supported_manuscript_claims must be an array")
        if not isinstance(trace["limitations"], list):
            errors.append(f"{artifact_id}: limitations must be an array")

    if set(artifact_ids) != EXPECTED_ARTIFACTS:
        errors.append(
            "figure/table trace coverage mismatch: "
            f"missing={sorted(EXPECTED_ARTIFACTS - set(artifact_ids))}, "
            f"extra={sorted(set(artifact_ids) - EXPECTED_ARTIFACTS)}"
        )
    if len(artifact_ids) != len(set(artifact_ids)):
        errors.append("duplicate artifact_id in figure_table_trace")
    for index in range(1, 11):
        stem = f"fig{index:02d}_"
        figures = paper_dir or (root / "deliverables" / "paper")
        figures = figures / "figures"
        if len(list(figures.glob(stem + "*.png"))) != 1 or len(list(figures.glob(stem + "*.pdf"))) != 1:
            errors.append(f"fig{index:02d}: expected exactly one PNG/PDF pair")

    declaration = sidecar.get("experiment_intake_declaration")
    if not isinstance(declaration, dict) or declaration.get("status") != "experiments_declared":
        errors.append("experiment_intake_declaration must declare experiments")
    experiments = sidecar.get("experiment_provenance")
    if not isinstance(experiments, list) or not experiments:
        errors.append("experiment_provenance must be non-empty")
        experiments = []
    experiment_ids: list[str] = []
    for index, experiment in enumerate(experiments):
        if not isinstance(experiment, dict):
            errors.append(f"experiment {index} is not an object")
            continue
        missing = EXPERIMENT_KEYS - experiment.keys()
        if missing:
            errors.append(f"experiment {index} missing keys: {sorted(missing)}")
            continue
        experiment_id = str(experiment["experiment_id"])
        experiment_ids.append(experiment_id)
        for item in experiment["repro_lock"].get("artifacts", []):
            _check_source(item, errors, root)
        for item in experiment["planned_vs_executed"]:
            if item.get("executed") is False and not item.get("skip_reason"):
                errors.append(f"{experiment_id}: skipped plan item has no reason")
        if not isinstance(experiment["negative_results"], list):
            errors.append(f"{experiment_id}: negative_results must be an array")
        if not isinstance(experiment["known_limitations"], list):
            errors.append(f"{experiment_id}: known_limitations must be an array")
    if len(experiment_ids) != len(set(experiment_ids)):
        errors.append("duplicate experiment_id")

    claims = sidecar.get("claim_manifest")
    if not isinstance(claims, list) or not claims:
        errors.append("claim_manifest must be non-empty")
        claims = []
    claim_by_id = {claim.get("claim_id"): claim for claim in claims if isinstance(claim, dict)}
    for claim_id, claim in claim_by_id.items():
        for experiment_id in claim.get("planned_experiment_ids", []):
            if experiment_id not in experiment_ids:
                errors.append(f"{claim_id}: dangling experiment pointer {experiment_id}")

    alignments = sidecar.get("experiment_alignment_results")
    if not isinstance(alignments, list):
        errors.append("experiment_alignment_results must be an array")
        alignments = []
    aligned_claims: set[str] = set()
    for index, alignment in enumerate(alignments):
        if not isinstance(alignment, dict):
            errors.append(f"alignment {index} is not an object")
            continue
        missing = ALIGNMENT_KEYS - alignment.keys()
        if missing:
            errors.append(f"alignment {index} missing keys: {sorted(missing)}")
            continue
        claim_id = str(alignment["claim_id"])
        aligned_claims.add(claim_id)
        if claim_id not in claim_by_id:
            errors.append(f"alignment {index}: unknown claim {claim_id}")
        if alignment["experiment_id"] not in experiment_ids:
            errors.append(f"alignment {index}: unknown experiment {alignment['experiment_id']}")
        if alignment["alignment_verdict"] != "ALIGNED":
            errors.append(
                f"alignment {index}: non-clean verdict {alignment['alignment_verdict']}"
            )
        if alignment["rule_version"] != "EA-v1":
            errors.append(f"alignment {index}: unexpected rule version")
    if aligned_claims != set(claim_by_id):
        errors.append(
            f"claim alignment coverage mismatch: {sorted(set(claim_by_id) - aligned_claims)}"
        )
    if sidecar.get("c4_boundary_statement") != BOUNDARY:
        errors.append("C4 boundary statement is missing or paraphrased")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "traces": len(traces),
            "experiments": len(experiments),
            "claims": len(claims),
            "alignments": len(alignments),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SAF manuscript integrity sidecar")
    parser.add_argument(
        "--sidecar", default="deliverables/paper/evidence/integrity_sidecar.json"
    )
    parser.add_argument("--out", default="artifacts/runs/paper_integrity/qa_latest.json")
    args = parser.parse_args()
    path = Path(args.sidecar)
    if not path.is_absolute():
        path = ROOT / path
    sidecar = json.loads(path.read_text(encoding="utf-8"))
    report = validate(sidecar, root=ROOT)
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
