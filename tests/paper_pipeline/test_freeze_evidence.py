"""证据冻结：每个被论文引用的实验结果以相对路径、哈希和运行号写入清单。"""

import hashlib
import json

import pytest


def _write_result(root, name, **overrides):
    path = root / "artifacts" / "runs" / name / "result.json"
    path.parent.mkdir(parents=True)
    value = {"artifact_schema_version": 1, "kind": name, "run_id": "baseline-run",
             "command": f"experiments/{name}.py --max-models 400"}
    value.update(overrides)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_canonical_entry_records_a_relative_path_hash_and_run_metadata(tmp_path):
    from paper.pipeline.audits.freeze_evidence import canonical_entry

    path = _write_result(tmp_path, "baseline_comparison")

    assert canonical_entry(tmp_path, "baseline_comparison") == {
        "path": "artifacts/runs/baseline_comparison/result.json",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "run_id": "baseline-run",
        "command": "experiments/baseline_comparison.py --max-models 400",
    }


def test_canonical_entry_rejects_a_result_with_another_kind(tmp_path):
    from paper.pipeline.audits.freeze_evidence import canonical_entry

    _write_result(tmp_path, "baseline_comparison", kind="other")

    with pytest.raises(RuntimeError, match="kind"):
        canonical_entry(tmp_path, "baseline_comparison")


def test_canonical_entry_rejects_missing_results(tmp_path):
    from paper.pipeline.audits.freeze_evidence import canonical_entry

    with pytest.raises(RuntimeError, match="missing"):
        canonical_entry(tmp_path, "baseline_comparison")


def test_every_canonical_experiment_has_a_script():
    from paper.pipeline.audits.freeze_evidence import CANONICAL_EXPERIMENTS
    from support_accessibility.runtime.data_paths import REPO_ROOT

    for name in CANONICAL_EXPERIMENTS:
        assert (REPO_ROOT / "experiments" / f"{name}.py").is_file(), name
