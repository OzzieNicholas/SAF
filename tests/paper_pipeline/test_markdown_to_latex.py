"""Markdown 源稿到 LaTeX 的渲染：行内格式、引用、交叉引用、公式、图、表、算法。"""

import re

import pytest

from paper.pipeline import markdown_to_latex as M
from paper.pipeline.paths import MANUSCRIPT_BODY, REFERENCES_BIB

KEYS = ["alpha2020", "beta2021", "gamma2022"]


def _body(md):
    return "\n\n".join(M.render(md, KEYS).body)


def test_inline_formatting_escaping_and_math():
    out = _body("## 1 节\n\n命中率 7.5% 与 **粗体**、*斜体*、`a_b` 和 $x_1\\%$。")
    assert r"7.5\%" in out and r"\textbf{粗体}" in out and r"\emph{斜体}" in out
    assert r"\texttt{a\_b}" in out and r"$x_1\%$" in out


def test_citations_expand_ranges_and_lists_but_not_math_intervals():
    out = _body("## 1 节\n\n见[1]、[2-3]、[1,3]，区间 $[0.1,0.2]$。")
    assert r"\cite{alpha2020}" in out
    assert r"\cite{beta2021,gamma2022}" in out
    assert r"\cite{alpha2020,gamma2022}" in out
    assert "$[0.1,0.2]$" in out


def test_citation_beyond_bibliography_is_an_error():
    with pytest.raises(M.RenderError):
        _body("## 1 节\n\n见[4]。")


def test_sections_figures_tables_and_cross_references():
    md = (
        "# 题\n\n## 1 引言\n\n如图 1 和表 1、式（1）所示。\n\n"
        "![图 1 说明](../figures/demo_figure.png)\n\n*图 1  流程说明*\n\n"
        "**表 1  对比**\n\n| 甲 | 乙 |\n|---|---:|\n| 1 | 2 |\n\n"
        "$$\nx=1\n\\tag{1}\n$$\n\n## 附录\n\n无编号节。\n"
    )
    out = _body(md)
    assert r"\section{引言}" in out and r"\section*{附录}" in out
    assert r"图~\ref{fig:demo-figure}" in out and r"表~\ref{tab:1}" in out and r"式~\eqref{eq:1}" in out
    assert r"\includegraphics[width=\textwidth]{demo_figure}" in out
    assert r"\caption{流程说明}" in out and r"\label{fig:demo-figure}" in out
    assert r"\caption{对比}" in out and r"\begin{tabular}" in out and r"甲 & 乙" in out
    assert r"\label{eq:1}" in out and r"\tag" not in out


def test_algorithm_block_becomes_algorithm2e():
    md = "## 1 节\n\n**算法 1  示例**\n\n输入：甲。\n输出：乙。\n\n1. 第一步\n2. 第二步\n"
    out = _body(md)
    assert r"\KwIn{甲}" in out and r"\KwOut{乙}" in out and out.count(r"\;") == 2


def test_render_files_fills_the_template(tmp_path):
    md = tmp_path / "论文.md"
    md.write_text("# 题目\n\n**英文题目：Title**\n\n## 摘要\n\n中文摘要。\n\n**关键词：** 甲；乙\n\n"
                  "## Abstract\n\nEnglish.\n\n**Key words:** a; b\n\n## 1 引言\n\n正文。\n\n## 参考文献\n\n[1] A.\n",
                  encoding="utf-8")
    bib = tmp_path / "r.bib"
    bib.write_text("@article{k1,\n  title = {T}\n}\n", encoding="utf-8")
    template = tmp_path / "t.tex"
    template.write_text("%%TITLE%%|%%TITLE_EN%%|%%ABSTRACT_ZH%%|%%KEYWORDS_ZH%%|%%ABSTRACT_EN%%|%%KEYWORDS_EN%%", encoding="utf-8")
    M.render_files(md, bib, template, tmp_path / "out")
    assert (tmp_path / "out" / "main.tex").read_text(encoding="utf-8") == "题目|Title|中文摘要。|甲；乙|English.|a; b"
    assert r"\section{引言}" in (tmp_path / "out" / "body.tex").read_text(encoding="utf-8")


def test_the_real_manuscript_renders_with_balanced_environments():
    keys = M.bibliography_keys(REFERENCES_BIB.read_text(encoding="utf-8"))
    doc = M.render(MANUSCRIPT_BODY.read_text(encoding="utf-8"), keys)
    body = "\n".join(doc.body)
    for env in set(re.findall(r"\begin\{([\w*]+)\}", body)):
        assert body.count("\\begin{%s}" % env) == body.count("\\end{%s}" % env), env
    assert doc.title and doc.abstract_zh and doc.abstract_en and doc.keywords_zh and doc.keywords_en
    assert "\x00" not in body
