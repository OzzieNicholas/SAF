"""论文门：证据里不得含绝对路径，外部数据缺失时严格门失败。"""

import json


def test_paper_gate_rejects_absolute_paths_in_evidence(tmp_path, monkeypatch):
    from paper.pipeline import paper_gate

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "bad.json").write_text(json.dumps({"path": r"E:\secret"}), encoding="utf-8")
    monkeypatch.setattr(paper_gate, "PAPER", tmp_path)
    report = paper_gate.run_gate(check_external_data=False)
    assert any("absolute/local path" in item for item in report["errors"])


def test_paper_gate_reports_missing_external_data(monkeypatch, tmp_path):
    from paper.pipeline import paper_gate

    class Missing:
        def processed_root(self, name):
            return tmp_path / name

        fusion360_root = tmp_path / "fusion"
        thingi_root = tmp_path / "thingi"

    monkeypatch.setattr(paper_gate, "resolve_data_paths", lambda: Missing())
    skipped = paper_gate.run_gate(check_external_data=False)
    assert not any("external" in item for item in skipped["errors"])
    checked = paper_gate.run_gate(check_external_data=True)
    assert any("missing external processed data" in item for item in checked["errors"])
    assert any("missing external raw data root" in item for item in checked["errors"])


def test_paper_gate_requires_the_machine_evidence_manifest(tmp_path, monkeypatch):
    from paper.pipeline import paper_gate

    monkeypatch.setattr(paper_gate, "PAPER", tmp_path)
    report = paper_gate.run_gate(check_external_data=False)
    assert any(item.replace("\\", "/").endswith("evidence/manifest.json") for item in report["errors"])
