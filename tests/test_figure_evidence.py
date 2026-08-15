import hashlib
import json
from pathlib import Path

import pytest


def _write_evidence_tree(root: Path) -> tuple[Path, Path]:
    artifact_path = root / "artifacts" / "runs" / "baselines" / "latest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact = {
        "artifact_schema_version": 1,
        "kind": "baselines",
        "run_id": "baseline-run",
        "methods": {},
    }
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    manifest_path = root / "artifacts" / "runs" / "paper_rewrite" / "latest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest = {
        "artifact_schema_version": 1,
        "kind": "paper_rewrite",
        "run_id": "paper-run",
        "canonical_runs": {
            "baselines": {
                "path": "artifacts/runs/baselines/latest.json",
                "sha256": digest,
                "run_id": "baseline-run",
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, artifact_path


def _load_api():
    from tools.figures.paper_evidence import load_canonical_artifact, load_manifest

    return load_manifest, load_canonical_artifact


def test_matching_canonical_artifact_loads(tmp_path):
    manifest_path, _ = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _load_api()

    manifest = load_manifest(manifest_path, tmp_path)
    artifact = load_canonical_artifact(manifest, "baselines", "baselines", tmp_path)

    assert artifact["run_id"] == "baseline-run"


def test_run_id_mismatch_fails_closed(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _load_api()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["run_id"] = "different-run"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["canonical_runs"]["baselines"]["sha256"] = hashlib.sha256(
        artifact_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded_manifest = load_manifest(manifest_path, tmp_path)
    with pytest.raises(RuntimeError, match="run_id"):
        load_canonical_artifact(loaded_manifest, "baselines", "baselines", tmp_path)


def test_hash_mismatch_fails_closed(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _load_api()
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    manifest = load_manifest(manifest_path, tmp_path)
    with pytest.raises(RuntimeError, match="SHA-256"):
        load_canonical_artifact(manifest, "baselines", "baselines", tmp_path)


def test_artifact_kind_and_schema_are_validated(tmp_path):
    manifest_path, artifact_path = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _load_api()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["artifact_schema_version"] = 2
    artifact["kind"] = "other"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["canonical_runs"]["baselines"]["sha256"] = hashlib.sha256(
        artifact_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded_manifest = load_manifest(manifest_path, tmp_path)
    with pytest.raises(RuntimeError, match="schema"):
        load_canonical_artifact(loaded_manifest, "baselines", "baselines", tmp_path)


def test_artifact_path_cannot_escape_repository(tmp_path):
    manifest_path, _ = _write_evidence_tree(tmp_path)
    load_manifest, load_canonical_artifact = _load_api()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["canonical_runs"]["baselines"]["path"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded_manifest = load_manifest(manifest_path, tmp_path)
    with pytest.raises(RuntimeError, match="escapes"):
        load_canonical_artifact(loaded_manifest, "baselines", "baselines", tmp_path)


def test_active_figure_scripts_do_not_embed_retired_result_literals():
    root = Path(__file__).resolve().parents[1]
    retired = {
        "tools/figures/fig08_baselines_ablation.py": (
            "0.925",
            "0.916",
            "0.926",
            "0.803",
            "0.859",
            "0.338",
            "0.527",
        ),
        "tools/figures/fig10_failure.py": (
            "np.asarray((2.9, 15.7, 10.7, 3.9))",
            "np.asarray((1.4, 3.3))",
            "axhline(4.7",
            "4.7% ± 0.3%",
        ),
    }

    for relative_path, tokens in retired.items():
        source = (root / relative_path).read_text(encoding="utf-8")
        for token in tokens:
            assert token not in source, f"retired token {token!r} remains in {relative_path}"


def test_baseline_figure_requires_and_displays_the_geometry_proxy_hierarchy():
    from tools.figures.fig08_baselines_ablation import baseline_method_entries

    roles = {
        "majority": "trivial_class_reference",
        "local_rule": "local_geometric_heuristic",
        "ray_visibility": "zero_radius_semantic_ablation",
        "coarse_finite_tool": "coarse_geometric_proxy",
        "tiny_local": "local_learned_reference",
        "convonet": "shape_conditioned_surrogate",
    }
    entries = baseline_method_entries({"method_roles": roles})

    assert [key for key, _label, _role in entries] == list(roles)
    assert entries[3] == ("coarse_finite_tool", "粗有限工具 proxy", "coarse_geometric_proxy")
    assert entries[-1] == ("convonet", "形状条件 surrogate", "shape_conditioned_surrogate")

    roles["coarse_finite_tool"] = "reference_oracle"
    with pytest.raises(RuntimeError, match="role"):
        baseline_method_entries({"method_roles": roles})


def test_low_opacity_context_suppresses_full_feature_edges():
    from tools.figures._data import _context_feature_edges_enabled

    assert _context_feature_edges_enabled(0.10) is False
    assert _context_feature_edges_enabled(0.49) is False
    assert _context_feature_edges_enabled(0.50) is True
    assert _context_feature_edges_enabled(1.00) is True

    with pytest.raises(ValueError, match="between 0 and 1"):
        _context_feature_edges_enabled(-0.01)
    with pytest.raises(ValueError, match="between 0 and 1"):
        _context_feature_edges_enabled(1.01)
