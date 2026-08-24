"""Build the SAF paper package from external Zotero/data inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

try:
    from .paper_gate import ROOT, PAPER, run_gate
    from .zotero_sync import ZoteroSyncError, sync_collection
except ImportError:  # direct script entrypoint
    from paper_gate import ROOT, PAPER, run_gate
    from zotero_sync import ZoteroSyncError, sync_collection


def _run_stage(label: str, command: list[str]) -> None:
    """Run one paper stage and turn a non-zero exit into a named failure."""
    print(f"PAPER_STAGE {label}: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise RuntimeError(f"paper stage {label!r} failed with exit code {completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the SAF paper downstream package")
    parser.add_argument(
        "--strict-zotero",
        action="store_true",
        default=True,
        help="require the declared Zotero collection and keys (mandatory for a paper build)",
    )
    parser.add_argument("--skip-evidence", action="store_true", help="do not freeze the machine evidence manifest")
    parser.add_argument("--skip-figures", action="store_true", help="reuse existing canonical figures")
    parser.add_argument("--skip-qa", action="store_true", help="skip manuscript/sidecar QA stages")
    parser.add_argument("--skip-latex", action="store_true")
    args = parser.parse_args()
    build = PAPER / "build"
    build.mkdir(parents=True, exist_ok=True)
    try:
        sync_collection(build / "references.bib", strict=args.strict_zotero)
    except ZoteroSyncError as error:
        print(f"ZOTERO_ERROR: {error}", file=sys.stderr)
        return 2
    try:
        if not args.skip_evidence:
            _run_stage(
                "freeze-evidence",
                [sys.executable, str(PAPER / "pipeline" / "qa" / "freeze_submission_evidence.py")],
            )
        if not args.skip_figures:
            figure_dir = PAPER / "pipeline" / "figures"
            for script in sorted(figure_dir.glob("fig[0-9][0-9]_*.py")):
                _run_stage(script.stem, [sys.executable, str(script)])
            _run_stage(
                "figure-qa",
                [sys.executable, str(figure_dir / "qa_figures.py"), "--strict"],
            )
        if not args.skip_qa:
            _run_stage(
                "integrity-sidecar",
                [sys.executable, str(PAPER / "pipeline" / "qa" / "build_integrity_sidecar.py")],
            )
            _run_stage(
                "manuscript-qa",
                [
                    sys.executable,
                    str(PAPER / "pipeline" / "qa" / "qa_manuscript.py"),
                    "--paper-dir",
                    str(PAPER),
                    "--manifest",
                    str(PAPER / "evidence" / "manifest.json"),
                    "--strict",
                ],
            )
            _run_stage(
                "integrity-qa",
                [
                    sys.executable,
                    str(PAPER / "pipeline" / "qa" / "qa_integrity.py"),
                    "--sidecar",
                    str(PAPER / "evidence" / "integrity_sidecar.json"),
                    "--out",
                    str(build / "qa_integrity.json"),
                ],
            )
    except RuntimeError as error:
        print(f"PAPER_BUILD_ERROR: {error}", file=sys.stderr)
        return 2

    if not args.skip_latex:
        main_tex = PAPER / "manuscript" / "latex" / "main.tex"
        if not main_tex.is_file():
            print(f"missing LaTeX source: {main_tex}", file=sys.stderr)
            return 2
        # Keep all generated files under the ignored paper build directory.
        try:
            completed = subprocess.run(
                ["tectonic", str(main_tex), "--outdir", str(build)],
                cwd=ROOT,
                check=False,
            )
        except OSError as error:
            print(f"PAPER_BUILD_ERROR: LaTeX compiler unavailable: {error}", file=sys.stderr)
            return 2
        if completed.returncode:
            return completed.returncode
        built_pdf = build / "main.pdf"
        if built_pdf.is_file():
            output_pdf = PAPER / "outputs" / "SAF_中文论文匿名稿.pdf"
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(built_pdf, output_pdf)
        else:
            print(f"LaTeX completed without expected output: {built_pdf}", file=sys.stderr)
            return 2
    report = run_gate(strict_zotero=args.strict_zotero)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
