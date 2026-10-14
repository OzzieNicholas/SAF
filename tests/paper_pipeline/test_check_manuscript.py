"""论文源稿审计的各项检查。"""

import hashlib
import json

from paper.pipeline.audits import check_manuscript as C
from paper.pipeline.figure_scripts import FIGURE_NAMES

BIB = """@article{a2020x,
  title = {A},
  doi   = {10.1/a}
}

@article{b2021y,
  title = {B},
  doi   = {10.1/b}
}
"""


def _codes(errors):
    return {item["code"] for item in errors}


def _figures(directory, names=FIGURE_NAMES, pdf=True):
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / f"{name}.png").write_bytes(b"png")
        if pdf:
            (directory / f"{name}.pdf").write_bytes(b"pdf")


def test_complete_figure_set_passes(tmp_path):
    _figures(tmp_path)
    assert C.check_figures(tmp_path) == []


def test_missing_figure_pair_fails(tmp_path):
    _figures(tmp_path, pdf=False)
    assert "figure_pair" in _codes(C.check_figures(tmp_path))


def test_wrong_figure_count_fails(tmp_path):
    _figures(tmp_path, names=FIGURE_NAMES[:-1])
    assert "figure_count" in _codes(C.check_figures(tmp_path))


def test_unresolvable_image_link_fails(tmp_path):
    assert "image_missing" in _codes(C.check_images("![x](../figures/none.png)", tmp_path))


def test_every_bib_entry_must_be_cited(tmp_path):
    text = "## 1 引言\n\n引用[1]。\n\n## 参考文献\n\n[1] A. DOI: 10.1/a.\n\n[2] B. DOI: 10.1/b.\n"
    assert "citation_unused" in _codes(C.check_citations(text, BIB))
    cited = text.replace("引用[1]", "引用[1-2]")
    assert C.check_citations(cited, BIB) == []


def test_first_citations_must_follow_bib_order():
    text = "## 1 引言\n\n先引[2]，再引[1]。\n\n## 参考文献\n\n[1] A. DOI: 10.1/a.\n\n[2] B. DOI: 10.1/b.\n"
    assert "citation_order" in _codes(C.check_citations(text, BIB))
    assert C.check_citations(text.replace("先引[2]，再引[1]", "先引[1]，再引[2]"), BIB) == []


def test_citation_number_beyond_the_bibliography_fails():
    text = "## 1 引言\n\n引用[3]。\n\n## 参考文献\n\n[1] A.\n"
    assert "render_error" in _codes(C.check_citations(text, BIB))


def test_reference_list_must_match_bib_order():
    ok = "## 参考文献\n\n[1] A. DOI: 10.1/a.\n\n[2] B. DOI: 10.1/b.\n"
    swapped = "## 参考文献\n\n[1] B. DOI: 10.1/b.\n\n[2] A. DOI: 10.1/a.\n"
    assert C.check_reference_list(ok, BIB) == []
    assert "reference_mismatch" in _codes(C.check_reference_list(swapped, BIB))


def test_administrative_placeholder_fails():
    assert "administrative_placeholder" in _codes(C.check_wording("作者单位待补"))


def test_unbounded_red_line_claims_fail():
    assert {"red_line_claim"} <= _codes(C.check_wording("本文首创该方法，并给出工艺认证"))


def test_explicit_negation_of_red_line_claims_is_allowed():
    assert C.check_wording("本文不声称首创，也不构成工艺认证，更不是构建方向优化") == []


def _manifest_and_root(tmp_path, value):
    path = tmp_path / "artifacts" / "runs" / "exp" / "result.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"artifact_schema_version": 1, "kind": "exp", "run_id": "r1", "m": {"f1": value}}), encoding="utf-8")
    manifest = {"canonical_runs": {"exp": {"path": "artifacts/runs/exp/result.json", "run_id": "r1",
                                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}}
    return manifest


def test_numeric_claim_must_match_evidence_and_appear_in_text(tmp_path):
    manifest = _manifest_and_root(tmp_path, 0.79312)
    claim = {"id": "f1", "experiment": "exp", "path": "m.f1", "format": ".3f", "text": "0.793"}
    assert C.check_numeric_claims("结果 0.793", [claim], manifest, tmp_path) == []
    assert "claim_stale" in _codes(C.check_numeric_claims("结果 0.793", [{**claim, "text": "0.800"}], manifest, tmp_path))
    assert "claim_not_in_text" in _codes(C.check_numeric_claims("无数字", [claim], manifest, tmp_path))


def test_numeric_claim_supports_scale_for_percentages(tmp_path):
    manifest = _manifest_and_root(tmp_path, 0.0486)
    claim = {"id": "p", "experiment": "exp", "path": "m.f1", "format": ".2f", "scale": 100, "text": "4.86"}
    assert C.check_numeric_claims("4.86%", [claim], manifest, tmp_path) == []


def test_numeric_claim_supports_derived_ratio(tmp_path):
    manifest = _manifest_and_root(tmp_path, 0.0486)
    claim = {"id": "r", "experiment": "exp", "path": "m.f1", "per": "m.f1", "format": ".0f", "scale": 100, "text": "100"}
    assert C.check_numeric_claims("100%", [claim], manifest, tmp_path) == []
