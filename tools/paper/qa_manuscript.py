"""Deterministic source-level QA for the anonymous SAF manuscript package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Iterable


FIGURE_NAME_RE = re.compile(r"^(fig(?P<number>\d{2})_.+)\.(?P<suffix>png|pdf)$", re.IGNORECASE)
BIB_KEY_RE = re.compile(r"@(?!(?:comment|string|preamble)\b)[A-Za-z]+\s*\{\s*([^,\s]+)", re.IGNORECASE)
MARKDOWN_CITATION_RE = re.compile(r"(?<![\w.+-])@([A-Za-z0-9][A-Za-z0-9_:./+\-]*)")
TEX_CITATION_RE = re.compile(
    r"\\(?:[A-Za-z]*cite[A-Za-z]*|cite)\*?(?:\s*\[[^]]*\]){0,2}\s*\{([^}]*)\}",
    re.IGNORECASE,
)

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


def _finding(code: str, path: Path | None, message: str, **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message}
    if path is not None:
        item["path"] = path.as_posix()
    item.update(details)
    return item


def _read_text(path: Path, errors: list[dict[str, Any]]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(_finding("read_error", path, f"Unable to read UTF-8 text: {exc}"))
        return ""


def _scientific_paths(paper_dir: Path) -> list[Path]:
    paths = [
        paper_dir / "paper.md",
        paper_dir / "tables.md",
        paper_dir / "figures" / "captions.md",
    ]
    latex_dir = paper_dir / "latex"
    if latex_dir.is_dir():
        paths.extend(sorted(latex_dir.glob("*.tex")))
    return paths


def _check_required_texts(paths: Iterable[Path], errors: list[dict[str, Any]]) -> dict[Path, str]:
    texts: dict[Path, str] = {}
    for path in paths:
        if not path.is_file():
            errors.append(_finding("scientific_file_missing", path, "Required scientific file is missing"))
            continue
        texts[path] = _read_text(path, errors)
    return texts


def _check_figure_pairs(paper_dir: Path, errors: list[dict[str, Any]]) -> None:
    figures_dir = paper_dir / "figures"
    assets: dict[int, dict[str, list[Path]]] = {}
    if figures_dir.is_dir():
        for path in sorted(figures_dir.iterdir()):
            if not path.is_file():
                continue
            match = FIGURE_NAME_RE.match(path.name)
            if match is None:
                continue
            number = int(match.group("number"))
            suffix = match.group("suffix").lower()
            assets.setdefault(number, {}).setdefault(suffix, []).append(path)

    expected = set(range(1, 11))
    observed = set(assets)
    if observed != expected:
        errors.append(
            _finding(
                "figure_count",
                figures_dir,
                "Figures must be numbered exactly fig01 through fig10",
                missing=sorted(expected - observed),
                unexpected=sorted(observed - expected),
            )
        )

    for number in sorted(expected | observed):
        formats = assets.get(number, {})
        pngs = formats.get("png", [])
        pdfs = formats.get("pdf", [])
        png_stems = {path.stem.lower() for path in pngs}
        pdf_stems = {path.stem.lower() for path in pdfs}
        if len(pngs) != 1 or len(pdfs) != 1 or png_stems != pdf_stems:
            errors.append(
                _finding(
                    "figure_pair",
                    figures_dir,
                    f"Figure {number:02d} must have one PNG/PDF pair with the same stem",
                    png=[path.name for path in pngs],
                    pdf=[path.name for path in pdfs],
                )
            )


def _markdown_citations(texts: Iterable[str]) -> set[str]:
    return {match.group(1) for text in texts for match in MARKDOWN_CITATION_RE.finditer(text)}


def _tex_citations(texts: Iterable[str]) -> set[str]:
    keys: set[str] = set()
    for text in texts:
        for match in TEX_CITATION_RE.finditer(text):
            keys.update(key.strip() for key in match.group(1).split(",") if key.strip() and key.strip() != "*")
    return keys


def _check_citations(
    paper_dir: Path,
    texts: dict[Path, str],
    strict: bool,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    bib_path = paper_dir / "latex" / "references.bib"
    if not bib_path.is_file():
        errors.append(_finding("bibliography_missing", bib_path, "BibTeX bibliography is missing"))
        return

    bib_text = _read_text(bib_path, errors)
    bib_keys = {match.group(1) for match in BIB_KEY_RE.finditer(bib_text)}
    markdown_texts = [text for path, text in texts.items() if path.suffix.lower() == ".md"]
    tex_texts = [text for path, text in texts.items() if path.suffix.lower() == ".tex"]
    used_keys = _markdown_citations(markdown_texts) | _tex_citations(tex_texts)

    for key in sorted(used_keys - bib_keys):
        errors.append(
            _finding("citation_missing", bib_path, f"Citation key is absent from BibTeX: {key}", key=key)
        )

    unused = sorted(bib_keys - used_keys)
    target = errors if strict else warnings
    for key in unused:
        target.append(
            _finding("citation_unused", bib_path, f"BibTeX entry is not cited by manuscript sources: {key}", key=key)
        )


def _is_negated(text: str, phrase_start: int) -> bool:
    clause_start = 0
    for boundary in CLAUSE_BOUNDARY_RE.finditer(text, 0, phrase_start):
        clause_start = boundary.end()
    prefix = text[clause_start:phrase_start][-24:]
    return NEGATION_RE.search(prefix) is not None


def _check_scientific_text(
    texts: dict[Path, str], deny_tokens: Iterable[str], errors: list[dict[str, Any]]
) -> None:
    for path, text in texts.items():
        for pattern in ADMINISTRATIVE_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                errors.append(
                    _finding(
                        "administrative_placeholder",
                        path,
                        f"Administrative placeholder appears in a scientific file: {match.group(0)}",
                        token=match.group(0),
                    )
                )

        for token in deny_tokens:
            if token and token in text:
                errors.append(
                    _finding("stale_value", path, f"Denied stale token appears in manuscript: {token}", token=token)
                )

        for phrase in RED_LINE_PHRASES:
            for match in re.finditer(re.escape(phrase), text):
                if _is_negated(text, match.start()):
                    continue
                snippet_start = max(0, match.start() - 24)
                snippet_end = min(len(text), match.end() + 24)
                errors.append(
                    _finding(
                        "red_line_claim",
                        path,
                        f"Unbounded prohibited claim: {phrase}",
                        phrase=phrase,
                        context=text[snippet_start:snippet_end].replace("\n", " "),
                    )
                )


def _display_strings(manifest: dict[str, Any]) -> list[str]:
    declared = manifest.get("display_strings")
    if declared is None:
        return []
    if isinstance(declared, dict):
        values = declared.values()
    elif isinstance(declared, list):
        values = declared
    else:
        return []
    return [str(value) for value in values if isinstance(value, (str, int, float)) and str(value)]


def _check_display_strings(
    paper_dir: Path,
    manifest: dict[str, Any],
    texts: dict[Path, str],
    errors: list[dict[str, Any]],
) -> None:
    markdown_path = paper_dir / "paper.md"
    markdown = texts.get(markdown_path, "")
    tex = "\n".join(text for path, text in texts.items() if path.suffix.lower() == ".tex")
    for value in _display_strings(manifest):
        missing_from = []
        if value not in markdown:
            missing_from.append("paper.md")
        if value not in tex:
            missing_from.append("latex")
        if missing_from:
            errors.append(
                _finding(
                    "display_string_missing",
                    paper_dir,
                    f"Manifest display string is missing from manuscript representation(s): {value}",
                    value=value,
                    missing_from=missing_from,
                )
            )


def audit_manuscript(
    paper_dir: Path,
    manifest_path: Path,
    *,
    strict: bool = False,
    deny_tokens: Iterable[str] = (),
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    paper_dir = paper_dir.resolve()
    manifest_path = manifest_path.resolve()

    if not paper_dir.is_dir():
        errors.append(_finding("paper_dir_missing", paper_dir, "Paper directory does not exist"))
        manifest: dict[str, Any] = {}
    else:
        manifest = {}

    if not manifest_path.is_file():
        errors.append(_finding("manifest_missing", manifest_path, "Evidence manifest does not exist"))
    else:
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("top-level JSON value must be an object")
            manifest = loaded
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(_finding("manifest_invalid", manifest_path, f"Evidence manifest is invalid: {exc}"))

    scientific_paths = _scientific_paths(paper_dir)
    texts = _check_required_texts(scientific_paths, errors)
    _check_figure_pairs(paper_dir, errors)
    _check_citations(paper_dir, texts, strict, errors, warnings)
    _check_scientific_text(texts, deny_tokens, errors)
    _check_display_strings(paper_dir, manifest, texts, errors)

    errors.sort(key=lambda item: (item["code"], item.get("path", ""), item.get("message", "")))
    warnings.sort(key=lambda item: (item["code"], item.get("path", ""), item.get("message", "")))
    return {
        "ok": not errors,
        "paper_dir": paper_dir.as_posix(),
        "manifest": manifest_path.as_posix(),
        "strict": strict,
        "checks": {
            "scientific_files": len(texts),
            "display_strings": len(_display_strings(manifest)),
        },
        "errors": errors,
        "warnings": warnings,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--deny-token", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = audit_manuscript(
        args.paper_dir,
        args.manifest,
        strict=args.strict,
        deny_tokens=args.deny_token,
    )
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
