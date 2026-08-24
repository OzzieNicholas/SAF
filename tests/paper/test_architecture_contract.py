import json
from pathlib import Path

import pytest


def test_external_data_paths_are_project_scoped_and_logical_manifest_is_portable(monkeypatch):
    from tools.data_paths import logical_data_ref, resolve_data_paths

    monkeypatch.setenv("SAF_DATA_ROOT", r"E:\Work\Data")
    monkeypatch.setenv("SAF_TEMPORARY_ROOT", r"E:\Work\Data\Temporary")
    paths = resolve_data_paths(run_id="run-01")
    assert paths.processed_root("procedural_v1") == Path(r"E:\Work\Data\Temporary\SAF\procedural_v1\run-01")
    manifest = paths.logical_manifest("procedural_v1")
    assert all("E:" not in value and "\\" not in value for value in manifest.values())
    assert logical_data_ref(paths.processed_root("procedural_v1"), paths) == "dataset://procedural_v1/run-01"
    assert "E:" not in logical_data_ref(r"E:\secret\mesh.obj", paths)


def test_paper_gate_rejects_absolute_paths_in_evidence(tmp_path, monkeypatch):
    from deliverables.paper.pipeline import paper_gate

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "bad.json").write_text(json.dumps({"path": r"E:\secret"}), encoding="utf-8")
    monkeypatch.setattr(paper_gate, "PAPER", tmp_path)
    report = paper_gate.run_gate(strict_zotero=False)
    assert any("absolute/local path" in item for item in report["errors"])


def test_paper_gate_strictly_reports_missing_external_data(monkeypatch, tmp_path):
    from deliverables.paper.pipeline import paper_gate

    class Missing:
        def processed_root(self, name):
            return tmp_path / name

        fusion360_root = tmp_path / "fusion"
        thingi_root = tmp_path / "thingi"

    monkeypatch.setattr(paper_gate, "resolve_data_paths", lambda: Missing())
    report = paper_gate.run_gate(strict_zotero=False)
    assert report["ok"] is True
    report = paper_gate.run_gate(strict_zotero=True)
    assert any("missing external processed data" in item for item in report["errors"])


def test_zotero_contract_contains_expected_collection_and_key_mapping():
    root = Path(__file__).resolve().parents[2]
    collection = json.loads((root / "deliverables/paper/zotero/collection.json").read_text(encoding="utf-8"))
    keys = json.loads((root / "deliverables/paper/zotero/citation_keys.json").read_text(encoding="utf-8"))
    assert collection["collection_key"] == keys["collection_key"] == "F5ITM9M6"
    assert collection["collection_name"] == "几何可达与神经预测"
    assert set(keys["citation_keys"]) == set(keys["zotero_keys"])


def test_zotero_export_filters_unused_entries_and_local_attachment_paths():
    from deliverables.paper.pipeline.zotero_sync import _portable_bibtex

    bib = (
        "@article{keep, title={Keep}, file={PDF:C:\\\\Zotero\\\\storage\\\\x.pdf}}\n\n"
        "@article{unused, title={Unused}}\n"
    )
    result = _portable_bibtex(bib, {"keep"})
    assert "keep" in result
    assert "unused" not in result
    assert "Zotero" not in result


def test_no_dvc_metadata_is_tracked_in_current_tree():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "dvc.yaml").exists()
    assert not (root / "dvc.lock").exists()
    assert not (root / ".dvcignore").exists()


def test_paper_package_has_only_canonical_figure_pairs_and_no_literature_pdfs():
    root = Path(__file__).resolve().parents[2]
    figures = root / "deliverables" / "paper" / "figures"
    for index in range(1, 11):
        stem = f"fig{index:02d}_"
        assert len(list(figures.glob(stem + "*.png"))) == 1
        assert len(list(figures.glob(stem + "*.pdf"))) == 1
    assert not list((root / "docs" / "references" / "literature").glob("*.pdf"))
    assert not (root / "deliverables" / "archive").exists()
    assert not (root / "artifacts" / "archive").exists()


def test_strict_paper_gate_requires_machine_evidence_manifest(monkeypatch):
    from deliverables.paper.pipeline import paper_gate

    monkeypatch.setattr(paper_gate, "sync_collection", lambda output, strict: {"ok": True})
    report = paper_gate.run_gate(strict_zotero=True)
    manifest = Path(paper_gate.PAPER) / "evidence" / "manifest.json"
    if manifest.exists():
        assert not any(item.endswith("evidence/manifest.json") for item in report["errors"])
    else:
        assert any(item.endswith("evidence/manifest.json") for item in report["errors"])
