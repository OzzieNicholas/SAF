"""论文下游包的严格门：源稿审计、证据清单、成品图成对、论文 PDF，以及外部数据在位。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from paper.pipeline.audits.check_manuscript import audit
from paper.pipeline.evidence import load_canonical_artifact, load_manifest
from paper.pipeline.paths import PAPER_DIR, PAPER_PDF
from support_accessibility.runtime.data_paths import PROCESSED_DATASETS, REPO_ROOT, resolve_data_paths

ROOT = REPO_ROOT
PAPER = PAPER_DIR
ABSOLUTE_RE = re.compile(r"(?i)(?:[a-z]:[\\/]|/home/|/mnt/|file://)")


def _display_path(path: Path) -> str:
    """测试把门指向临时目录时也能显示路径。"""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _required_files(paper: Path) -> tuple[Path, ...]:
    return (
        paper / "manuscript" / "论文正文.md",
        paper / "manuscript" / "references.bib",
        paper / "manuscript" / "numeric_claims.yaml",
        paper / "manuscript" / "latex" / "template.tex",
        paper / "evidence" / "证据清单.md",
        paper / "evidence" / "manifest.json",
    )


def _evidence_check(errors: list[str], paper: Path) -> None:
    manifest_path = paper / "evidence" / "manifest.json"
    if not manifest_path.is_file():
        return  # 必需文件检查已给出缺失信息
    try:
        manifest = load_manifest(manifest_path, paper.parent)
        for name in manifest["canonical_runs"]:
            load_canonical_artifact(manifest, name, paper.parent)
    except Exception as error:
        errors.append(f"paper evidence manifest is invalid: {error}")


def run_gate(*, check_external_data: bool = True) -> dict[str, object]:
    errors: list[str] = []
    for path in _required_files(PAPER):
        if not path.is_file():
            errors.append(f"missing paper file: {_display_path(path)}")
    if not PAPER_PDF.is_file() or PAPER_PDF.stat().st_size == 0:
        errors.append(f"missing paper output: {_display_path(PAPER_PDF)}")
    for item in audit(PAPER).get("errors", []):
        errors.append(f"manuscript audit [{item.get('code', 'unknown')}]: {item.get('message', item)}")
    _evidence_check(errors, PAPER)
    if check_external_data:
        paths = resolve_data_paths()
        for dataset in PROCESSED_DATASETS:
            root = paths.processed_root(dataset)
            for required in ("manifest.csv", "dataset.json"):
                if not (root / required).is_file():
                    errors.append(f"missing external processed data: {root / required}")
        for name, root in (("Fusion360", paths.fusion360_root), ("Thingi10K", paths.thingi_root)):
            if not root.is_dir():
                errors.append(f"missing external raw data root ({name}): {root}")
    for path in (PAPER / "evidence").rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md"}:
            if ABSOLUTE_RE.search(path.read_text(encoding="utf-8", errors="replace")):
                errors.append(f"evidence contains an absolute/local path: {_display_path(path)}")
    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="论文下游包严格门")
    parser.add_argument("--skip-data", action="store_true", help="不检查外部数据（只在无数据的环境里做源稿与证据检查）")
    args = parser.parse_args()
    report = run_gate(check_external_data=not args.skip_data)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
