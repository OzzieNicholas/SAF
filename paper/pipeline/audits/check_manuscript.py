"""论文源稿审计：图件成对、图片链接、引用与参考文献、红线措辞、数值与证据一致。

检查对象是唯一源稿 ``论文正文.md`` 及其引用的 ``references.bib``、``numeric_claims.yaml``、``figures/``。
任何一项不通过都会以非零退出码结束。

用法：
  python -m paper.pipeline.audits.check_manuscript
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml

from paper.pipeline.evidence import load_canonical_artifact, load_manifest
from paper.pipeline.figure_scripts import FIGURE_NAMES
from paper.pipeline.markdown_to_latex import RenderError, bibliography_keys, render
from paper.pipeline.paths import (
    EVIDENCE_MANIFEST, MANUSCRIPT_BODY, NUMERIC_CLAIMS, PAPER_DIR, REFERENCES_BIB,
)
from support_accessibility.runtime.data_paths import REPO_ROOT

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
CITE_RE = re.compile(r"\\cite\{([^}]*)\}")
BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
REFERENCE_LINE_RE = re.compile(r"^\[(\d+)\]\s+(.*)$", re.M)

ADMINISTRATIVE_PATTERNS = (
    re.compile(r"待补"),
    re.compile(r"待定"),
    re.compile(r"\b(?:TBD|TODO)\b", re.IGNORECASE),
    re.compile(r"\[(?:作者|单位|机构|基金|通信作者|邮箱|期刊)\]"),
    re.compile(r"<(?:作者|单位|机构|基金|通信作者|邮箱|期刊)>"),
)
RED_LINE_PHRASES = ("首创", "工艺认证", "构建方向优化")
CLAUSE_BOUNDARY_RE = re.compile(r"[，,；;。！？!?\n]")
NEGATION_RE = re.compile(
    r"(?:不(?:声称|宣称|主张|构成|代表|等同于|用于|进行|涉及|包含|是|属于)?|"
    r"并非|并不|非|未|无|不能|不可|避免|禁止|排除|超出)"
)


def _finding(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **details}


def check_figures(figure_dir: Path) -> list[dict[str, Any]]:
    """FIGURE_NAMES 中的每幅图恰好有一对同名 PNG / PDF，且目录中没有多余的图件。"""
    present: dict[str, set[str]] = {}
    if figure_dir.is_dir():
        for path in figure_dir.iterdir():
            if path.is_file() and path.suffix.lower() in {".png", ".pdf"}:
                present.setdefault(path.stem, set()).add(path.suffix.lower())
    errors = []
    expected = set(FIGURE_NAMES)
    if set(present) != expected:
        errors.append(_finding("figure_count", "图件目录必须恰好包含 FIGURE_NAMES 中的十幅图",
                               missing=sorted(expected - set(present)), unexpected=sorted(set(present) - expected)))
    for name in sorted(expected & set(present)):
        if present[name] != {".png", ".pdf"}:
            errors.append(_finding("figure_pair", f"图件 {name} 必须同时有 PNG 与 PDF", formats=sorted(present[name])))
    return errors


def check_images(text: str, base: Path) -> list[dict[str, Any]]:
    errors = []
    for target in IMAGE_RE.findall(text):
        target = target.strip().split(" ", 1)[0]
        if not (base / target).resolve().is_file():
            errors.append(_finding("image_missing", f"源稿图片链接无法解析：{target}", target=target))
    return errors


def check_citations(text: str, bib_text: str) -> list[dict[str, Any]]:
    """引用编号在 references.bib 的条目数之内，且每条文献都被引用。"""
    keys = bibliography_keys(bib_text)
    try:
        doc = render(text, keys)
    except RenderError as exc:
        return [_finding("render_error", str(exc))]
    cited = {key for block in doc.body for group in CITE_RE.findall(block) for key in group.split(",")}
    errors = [_finding("citation_unused", f"文献条目未被正文引用：{key}", key=key) for key in keys if key not in cited]
    if len(doc.references) != len(keys):
        errors.append(_finding("reference_count", f"参考文献列表 {len(doc.references)} 条，references.bib 有 {len(keys)} 条"))
    return errors


def check_reference_list(text: str, bib_text: str) -> list[dict[str, Any]]:
    """正文末尾的参考文献列表与 references.bib 按顺序一一对应（以 DOI 或网址核对）。"""
    section = text.split("## 参考文献", 1)[-1]
    listed = REFERENCE_LINE_RE.findall(section)
    entries = BIB_ENTRY_RE.findall(bib_text)
    errors = []
    for (number, line), (key, body) in zip(listed, entries):
        identifier = re.search(r"\b(?:doi|url)\s*=\s*\{([^}]*)\}", body, re.I)
        if identifier and identifier.group(1).lower() not in line.lower():
            errors.append(_finding("reference_mismatch", f"参考文献 [{number}] 与 references.bib 条目 {key} 不一致",
                                   number=int(number), key=key))
    return errors


def _is_negated(text: str, phrase_start: int) -> bool:
    clause_start = 0
    for boundary in CLAUSE_BOUNDARY_RE.finditer(text, 0, phrase_start):
        clause_start = boundary.end()
    return NEGATION_RE.search(text[clause_start:phrase_start][-24:]) is not None


def check_wording(text: str) -> list[dict[str, Any]]:
    errors = []
    for pattern in ADMINISTRATIVE_PATTERNS:
        match = pattern.search(text)
        if match:
            errors.append(_finding("administrative_placeholder", f"科学稿中出现行政占位：{match.group(0)}"))
    for phrase in RED_LINE_PHRASES:
        for match in re.finditer(re.escape(phrase), text):
            if not _is_negated(text, match.start()):
                context = text[max(0, match.start() - 24):match.end() + 24].replace("\n", " ")
                errors.append(_finding("red_line_claim", f"未加限定的禁用表述：{phrase}", context=context))
    return errors


def _lookup(value: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def check_numeric_claims(text: str, claims: list[dict[str, Any]], manifest: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    """每条数值声明：源稿里出现该文字，且等于证据按指定格式取整后的值。"""
    errors = []
    artifacts: dict[str, dict[str, Any]] = {}
    for claim in claims:
        name, shown = claim["experiment"], str(claim["text"])
        try:
            if name not in artifacts:
                artifacts[name] = load_canonical_artifact(manifest, name, root)
            value = float(_lookup(artifacts[name], claim["path"])) * float(claim.get("scale", 1))
        except (KeyError, IndexError, TypeError, ValueError, RuntimeError) as exc:
            errors.append(_finding("claim_unresolved", f"数值声明 {claim['id']} 无法从证据取值：{exc}", id=claim["id"]))
            continue
        expected = format(value, claim.get("format", ".3f"))
        if expected != shown:
            errors.append(_finding("claim_stale", f"数值声明 {claim['id']}：证据为 {expected}，声明写的是 {shown}",
                                   id=claim["id"], expected=expected, declared=shown))
        if shown not in text:
            errors.append(_finding("claim_not_in_text", f"数值声明 {claim['id']} 的文字 {shown} 未出现在源稿中", id=claim["id"]))
    return errors


def audit(paper_dir: Path = PAPER_DIR) -> dict[str, Any]:
    text = MANUSCRIPT_BODY.read_text(encoding="utf-8") if MANUSCRIPT_BODY.is_file() else ""
    bib_text = REFERENCES_BIB.read_text(encoding="utf-8") if REFERENCES_BIB.is_file() else ""
    errors: list[dict[str, Any]] = []
    if not text:
        errors.append(_finding("manuscript_missing", f"缺少源稿：{MANUSCRIPT_BODY.name}"))
    if not bib_text:
        errors.append(_finding("bibliography_missing", f"缺少 {REFERENCES_BIB.name}"))
    errors += check_figures(paper_dir / "figures")
    if text:
        errors += check_images(text, MANUSCRIPT_BODY.parent)
        errors += check_wording(text)
    if text and bib_text:
        errors += check_citations(text, bib_text)
        errors += check_reference_list(text, bib_text)
    if EVIDENCE_MANIFEST.is_file() and NUMERIC_CLAIMS.is_file():
        manifest = load_manifest(EVIDENCE_MANIFEST, REPO_ROOT)
        claims = yaml.safe_load(NUMERIC_CLAIMS.read_text(encoding="utf-8")) or []
        errors += check_numeric_claims(text, claims, manifest, REPO_ROOT)
    else:
        errors.append(_finding("evidence_missing", "缺少证据清单或 numeric_claims.yaml，无法核对数值"))
    return {"ok": not errors, "errors": errors}


def main() -> int:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
