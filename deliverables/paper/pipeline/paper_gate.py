"""Strict static gate for the SAF paper downstream package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

try:
    from tools.data_paths import resolve_data_paths
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
    from data_paths import resolve_data_paths

try:
    from .zotero_sync import ZoteroSyncError, sync_collection
except ImportError:  # direct `python path/to/paper_gate.py` entrypoint
    from zotero_sync import ZoteroSyncError, sync_collection


ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "deliverables" / "paper"
ABSOLUTE_RE = re.compile(r"(?i)(?:[a-z]:[\\\\/]|/home/|/mnt/|file://)")


def _display_path(path: Path) -> str:
    """Format a path even when tests point the gate at an external temp root."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _required_files(paper: Path, *, strict: bool) -> tuple[Path, ...]:
    required = [
        paper / "manuscript" / "paper.md",
        paper / "manuscript" / "tables.md",
        paper / "manuscript" / "captions.md",
        paper / "manuscript" / "latex" / "main.tex",
        paper / "manuscript" / "latex" / "body.tex",
        paper / "evidence" / "manifest.md",
        paper / "evidence" / "integrity_sidecar.json",
    ]
    if strict:
        required.append(paper / "evidence" / "manifest.json")
    return tuple(required)


def _required_outputs(paper: Path) -> tuple[Path, ...]:
    return (paper / "outputs" / "SAF_中文论文匿名稿.pdf",)


def _figure_pairs(errors: list[str], paper: Path) -> None:
    figures = paper / "figures"
    for index in range(1, 11):
        stem = f"fig{index:02d}_"
        png = list(figures.glob(stem + "*.png"))
        pdf = list(figures.glob(stem + "*.pdf"))
        if len(png) != 1 or len(pdf) != 1:
            errors.append(f"{stem}: expected exactly one canonical PNG/PDF pair")
    if any(figures.glob("contact_sheet.*")):
        errors.append("contact_sheet.* is QA-only and must not be in canonical figures")


def _integrity_check(errors: list[str], paper: Path) -> None:
    sidecar = paper / "evidence" / "integrity_sidecar.json"
    if not sidecar.is_file():
        return  # required-file check emits the concise missing-file error
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        from .qa.qa_integrity import validate
    except ImportError:  # direct script entrypoint
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from qa.qa_integrity import validate
    except Exception as error:
        errors.append(f"integrity sidecar is unreadable: {_display_path(sidecar)} ({error})")
        return
    try:
        report = validate(payload, root=paper.parent.parent, paper_dir=paper)
    except Exception as error:
        errors.append(f"integrity sidecar validation crashed: {error}")
        return
    for item in report.get("errors", []):
        errors.append(f"integrity sidecar: {item}")


def _machine_manifest_check(errors: list[str], paper: Path) -> None:
    path = paper / "evidence" / "manifest.json"
    if not path.is_file():
        return  # strict required-file check owns the missing-file message
    try:
        from .figures.paper_evidence import load_manifest
    except ImportError:  # direct script entrypoint
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from figures.paper_evidence import load_manifest
    try:
        load_manifest(path, paper.parent.parent)
    except Exception as error:
        errors.append(f"paper evidence manifest is invalid: {error}")


def _manuscript_qa_check(errors: list[str], paper: Path, *, strict: bool) -> None:
    """Run source-level citation/claim QA when the machine manifest is present."""
    manifest = paper / "evidence" / "manifest.json"
    if not manifest.is_file():
        return
    try:
        from .qa.qa_manuscript import audit_manuscript
    except ImportError:  # direct script entrypoint
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from qa.qa_manuscript import audit_manuscript
    report = audit_manuscript(paper, manifest, strict=strict)
    for item in report.get("errors", []):
        code = item.get("code", "unknown") if isinstance(item, dict) else "unknown"
        message = item.get("message", item) if isinstance(item, dict) else item
        errors.append(f"manuscript QA [{code}]: {message}")


def run_gate(*, strict_zotero: bool = True) -> dict[str, object]:
    errors: list[str] = []
    for path in _required_files(PAPER, strict=strict_zotero):
        if not path.is_file():
            errors.append(f"missing paper file: {_display_path(path)}")
    for path in _required_outputs(PAPER):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing paper output: {_display_path(path)}")
    _figure_pairs(errors, PAPER)
    _machine_manifest_check(errors, PAPER)
    _manuscript_qa_check(errors, PAPER, strict=strict_zotero)
    _integrity_check(errors, PAPER)
    if strict_zotero:
        paths = resolve_data_paths()
        for dataset in ("fusion360_full", "procedural_v1", "thingi_v1"):
            root = paths.processed_root(dataset)
            for required in ("manifest.csv", "dataset.json"):
                if not (root / required).is_file():
                    errors.append(f"missing external processed data: {root / required}")
        for name, root in (("Fusion360", paths.fusion360_root), ("Thingi10K", paths.thingi_root)):
            if not root.is_dir():
                errors.append(f"missing external raw data root ({name}): {root}")
    for path in (PAPER / "evidence").rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if ABSOLUTE_RE.search(text):
                errors.append(f"evidence contains an absolute/local path: {_display_path(path)}")
    bib = PAPER / "build" / "references.bib"
    try:
        zotero = sync_collection(bib, strict=strict_zotero)
    except ZoteroSyncError as error:
        errors.append(str(error))
        zotero = {"ok": False}
    return {"ok": not errors, "errors": errors, "zotero": zotero}


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict SAF paper package gate")
    parser.add_argument("--strict", action="store_true", help="require all declared Zotero keys")
    args = parser.parse_args()
    report = run_gate(strict_zotero=args.strict)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
