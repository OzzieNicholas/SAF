"""Tests for freezing current evidence inputs into the paper manifest."""

import hashlib
import json

import pytest


def test_canonical_entry_records_a_relative_path_hash_and_run_metadata(tmp_path):
    from deliverables.paper.pipeline.qa.freeze_submission_evidence import canonical_entry

    artifact_path = tmp_path / "artifacts" / "runs" / "baselines" / "latest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact = {
        "artifact_schema_version": 1,
        "kind": "baselines",
        "run_id": "baseline-run",
        "command": "tools/eval_baselines.py --max-models 400",
    }
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    entry = canonical_entry(tmp_path, "artifacts/runs/baselines/latest.json", "baselines")

    assert entry == {
        "path": "artifacts/runs/baselines/latest.json",
        "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "run_id": "baseline-run",
        "command": "tools/eval_baselines.py --max-models 400",
    }


def test_canonical_entry_rejects_a_wrong_evidence_kind(tmp_path):
    from deliverables.paper.pipeline.qa.freeze_submission_evidence import canonical_entry

    artifact_path = tmp_path / "artifacts" / "runs" / "baselines" / "latest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(
        json.dumps({"artifact_schema_version": 1, "kind": "other", "run_id": "wrong"}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="kind"):
        canonical_entry(tmp_path, "artifacts/runs/baselines/latest.json", "baselines")


def test_legacy_non_envelope_evidence_is_declared_separately():
    from deliverables.paper.pipeline.qa.freeze_submission_evidence import HISTORICAL_SOURCES, RUN_SPECS

    assert "true_area" not in {name for name, _path, _kind in RUN_SPECS}
    assert HISTORICAL_SOURCES["true_area"]["path"] == "artifacts/runs/true_area/latest.json"
    assert HISTORICAL_SOURCES["true_area"]["status"] == "legacy_non_envelope"
