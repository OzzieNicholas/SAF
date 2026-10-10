"""Unit tests for retained-evidence and disposable-cache boundaries."""

import tempfile
from pathlib import Path

import pytest


from support_accessibility.runtime import run_records as artifacts

ROOT = artifacts.ROOT


def test_write_result_adds_reproducibility_envelope(monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        tmp_path = Path(raw)
        monkeypatch.setattr(artifacts, "ROOT", tmp_path)
        output = tmp_path / "runs" / "sample" / "result.json"
        payload = artifacts.write_result("sample", {"value": 3}, output,
                                         (tmp_path / "input.txt",))
        assert payload["artifact_schema_version"] == 1
        assert payload["kind"] == "sample"
        assert payload["run_id"]
        assert payload["input_digest"]
        assert [path.name for path in output.parent.iterdir()] == ["result.json"]
        assert output.read_text(encoding="utf-8").endswith("\n")


def test_cache_scope_and_prune_kind_cannot_escape_cache_root():
    with pytest.raises(ValueError):
        artifacts.cache_root("../../outside")


def test_prune_only_targets_old_cache(monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        tmp_path = Path(raw)
        artifact_root = tmp_path / "artifacts"
        cache_root = artifact_root / "cache"
        evidence_root = artifact_root / "runs"
        old_cache = cache_root / "figures" / "old.bin"
        fresh_cache = cache_root / "figures" / "fresh.bin"
        retained = evidence_root / "figures" / "report.json"
        for path in (old_cache, fresh_cache, retained):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("data", encoding="utf-8")
        old_time = old_cache.stat().st_mtime - 8 * 86400
        import os
        os.utime(old_cache, (old_time, old_time))

        monkeypatch.setattr(artifacts, "CACHE_ROOT", cache_root)
        assert artifacts.stale_cache_files(7) == [old_cache]
        assert retained.is_file()
        old_cache.unlink()
        assert not old_cache.exists()
        assert fresh_cache.is_file()
        assert retained.is_file()


def test_run_envelope_redacts_absolute_data_paths(monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        tmp_path = Path(raw)
        monkeypatch.setattr(artifacts, "ROOT", tmp_path)
        monkeypatch.setattr(artifacts, "RUN_ROOT", tmp_path / "artifacts" / "runs")
        result = artifacts.write_result(
            "sample",
            {"data": r"E:\\Work\\Data\\SAF\\processed\\procedural"},
            tmp_path / "artifacts" / "runs" / "sample" / "result.json",
        )
        assert "E:" not in str(result)
        assert result["data"].startswith("external://") or result["data"].startswith("dataset://")
