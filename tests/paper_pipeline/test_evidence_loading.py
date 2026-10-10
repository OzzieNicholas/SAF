"""证据加载：路径、哈希、实验名、运行号任何一项漂移都必须失败。"""

import hashlib
import json
from pathlib import Path

import pytest


def _write_evidence_tree(root: Path) -> tuple[Path, Path]:
    artifact_path = root / "artifacts" / "runs" / "baseline_comparison" / "result.json"
    artifact_path.parent.mkdir(parents=True)
    artifact = {"artifact_schema_version": 1, "kind": "baseline_comparison", "run_id": "baseline-run", "methods": {}}
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    manifest_path = root / "paper" / "evidence" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest = {
        "artifact_schema_version": 1,
        "kind": "paper_evidence",
        "run_id": "paper-run",
        "canonical_runs": {
            "baseline_comparison": {
                "path": "artifacts/runs/baseline_comparison/result.json",
                "sha256": digest,
                "run_id": "baseline-run",
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, artifact_path


def _api():
    from paper.pipeline.evidence import load_canonical_artifact, load_manifest

    return load_manifest, load_canonical_artifact


def test_matching_canonical_artifact_loads(tmp_path):
    manifest_path, _ = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _api()

    manifest = load_manifest(manifest_path, tmp_path)
    artifact = load_canonical_artifact(manifest, "baseline_comparison", tmp_path)

    assert artifact["run_id"] == "baseline-run"


def test_run_id_mismatch_fails_closed(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _api()
    manifest = load_manifest(manifest_path, tmp_path)
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["run_id"] = "different-run"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    manifest["canonical_runs"]["baseline_comparison"]["sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    with pytest.raises(RuntimeError, match="run_id"):
        load_canonical_artifact(manifest, "baseline_comparison", tmp_path)


def test_hash_mismatch_fails_closed(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _api()
    manifest = load_manifest(manifest_path, tmp_path)
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(RuntimeError, match="SHA-256"):
        load_canonical_artifact(manifest, "baseline_comparison", tmp_path)


def test_artifact_kind_must_equal_the_manifest_key(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _api()
    manifest = load_manifest(manifest_path, tmp_path)
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["kind"] = "other"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    manifest["canonical_runs"]["baseline_comparison"]["sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    with pytest.raises(RuntimeError, match="kind"):
        load_canonical_artifact(manifest, "baseline_comparison", tmp_path)


def test_artifact_path_cannot_escape_repository(tmp_path):
    manifest_path, _ = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _api()
    manifest = load_manifest(manifest_path, tmp_path)
    manifest["canonical_runs"]["baseline_comparison"]["path"] = "../outside.json"

    with pytest.raises(RuntimeError, match="escapes"):
        load_canonical_artifact(manifest, "baseline_comparison", tmp_path)
