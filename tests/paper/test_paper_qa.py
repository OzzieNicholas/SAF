import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def _write_valid_paper_tree(root: Path) -> tuple[Path, Path]:
    paper_dir = root / "paper"
    figures = paper_dir / "figures"
    manuscript = paper_dir / "manuscript"
    latex = manuscript / "latex"
    build = paper_dir / "build"
    figures.mkdir(parents=True)
    manuscript.mkdir(parents=True)
    latex.mkdir()
    build.mkdir()

    (manuscript / "paper.md").write_text(
        "# 稿件\n\n结果为 0.893，并引用方法 [@alpha; @beta]。\n",
        encoding="utf-8",
    )
    (manuscript / "tables.md").write_text("# 表格\n\n0.893\n", encoding="utf-8")
    (manuscript / "captions.md").write_text("# 图注\n", encoding="utf-8")
    (latex / "body.tex").write_text(
        r"结果为 0.893。\cite{alpha,beta}",
        encoding="utf-8",
    )
    (build / "references.bib").write_text(
        "@article{alpha, author={A, A}, title={Alpha}, journal={J}, year={2020}}\n"
        "@article{beta, author={B, B}, title={Beta}, journal={J}, year={2021}}\n",
        encoding="utf-8",
    )
    for index in range(1, 11):
        stem = f"fig{index:02d}_sample"
        (figures / f"{stem}.png").write_bytes(b"png")
        (figures / f"{stem}.pdf").write_bytes(b"pdf")

    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps({"manuscript_version": "test", "display_strings": ["0.893"]}),
        encoding="utf-8",
    )
    return paper_dir, manifest


def _run_cli(paper_dir: Path, manifest: Path, *extra: str):
    command = [
        sys.executable,
        "-m",
        "deliverables.paper.pipeline.qa.qa_manuscript",
        "--paper-dir",
        str(paper_dir),
        "--manifest",
        str(manifest),
        "--strict",
        *extra,
    ]
    result = subprocess.run(
        command, cwd=ROOT, text=True, encoding="utf-8", capture_output=True
    )
    assert result.stdout.strip(), result.stderr
    return result, json.loads(result.stdout)


def _codes(report: dict) -> set[str]:
    return {item["code"] for item in report["errors"]}


def test_complete_paper_tree_passes(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 0
    assert report["ok"] is True
    assert report["errors"] == []


def test_missing_figure_pair_fails(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    (paper_dir / "figures" / "fig07_sample.pdf").unlink()

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "figure_pair" in _codes(report)


def test_citation_used_but_absent_from_bibtex_fails(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    body = paper_dir / "manuscript" / "latex" / "body.tex"
    body.write_text(body.read_text(encoding="utf-8") + r"\cite{gamma}", encoding="utf-8")

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "citation_missing" in _codes(report)


def test_unused_bibtex_entry_fails_in_strict_mode(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    (paper_dir / "manuscript" / "paper.md").write_text("# 稿件\n\n结果为 0.893 [@alpha]。\n", encoding="utf-8")
    (paper_dir / "manuscript" / "latex" / "body.tex").write_text(
        r"结果为 0.893。\cite{alpha}", encoding="utf-8"
    )

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "citation_unused" in _codes(report)


def test_administrative_placeholder_in_scientific_file_fails(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    paper = paper_dir / "manuscript" / "paper.md"
    paper.write_text(paper.read_text(encoding="utf-8") + "\n通信作者：待补\n", encoding="utf-8")

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "administrative_placeholder" in _codes(report)


def test_supplied_stale_result_token_fails(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    paper = paper_dir / "manuscript" / "paper.md"
    paper.write_text(paper.read_text(encoding="utf-8") + "\n旧结果 0.925。\n", encoding="utf-8")

    result, report = _run_cli(paper_dir, manifest, "--deny-token", "0.925")

    assert result.returncode == 1
    assert "stale_value" in _codes(report)


def test_unbounded_red_line_claims_fail(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    paper = paper_dir / "manuscript" / "paper.md"
    paper.write_text(
        paper.read_text(encoding="utf-8")
        + "\n本文首创该方法，并可用于工艺认证和构建方向优化。\n",
        encoding="utf-8",
    )

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "red_line_claim" in _codes(report)


def test_explicit_negation_of_red_line_claims_is_allowed(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    paper = paper_dir / "manuscript" / "paper.md"
    paper.write_text(
        paper.read_text(encoding="utf-8")
        + "\n本文不声称首创，不构成工艺认证，也不进行构建方向优化。\n",
        encoding="utf-8",
    )

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 0
    assert report["ok"] is True


def test_manifest_display_string_must_match_markdown_and_tex(tmp_path):
    paper_dir, manifest = _write_valid_paper_tree(tmp_path)
    body = paper_dir / "manuscript" / "latex" / "body.tex"
    body.write_text(body.read_text(encoding="utf-8").replace("0.893", "0.892"), encoding="utf-8")

    result, report = _run_cli(paper_dir, manifest)

    assert result.returncode == 1
    assert "display_string_missing" in _codes(report)
