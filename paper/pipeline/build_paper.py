"""构建论文：冻结证据 → 出图 → 图件 QA → 源稿审计 → 渲染 LaTeX → 编译 PDF → 论文门。

LaTeX 在临时目录 paper/build/ 中编译，成功后 PDF 复制到 paper/outputs/ 并删除构建目录。

用法（仓库根目录）：
  python -m paper.pipeline.build_paper
  python -m paper.pipeline.build_paper --skip-figures --skip-latex   # 只做证据与审计的阶段性检查
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from paper.pipeline.figure_scripts import FIGURE_NAMES
from paper.pipeline.markdown_to_latex import render_files
from paper.pipeline.paper_gate import run_gate
from paper.pipeline.paths import (
    BUILD_DIR, FIGURE_DIR, LATEX_TEMPLATE, MANUSCRIPT_BODY, OUTPUT_DIR, PAPER_PDF, REFERENCES_BIB,
)
from support_accessibility.runtime.data_paths import REPO_ROOT


def _write_verified(target: Path, data: bytes) -> None:
    """原子写出并核对：逻辑长度与内容都必须与 data 一致。"""
    temp = target.with_name(target.name + ".staging")
    temp.write_bytes(data)
    temp.replace(target)
    if target.stat().st_size != len(data) or target.read_bytes() != data:
        raise RuntimeError(f"staged file does not match its content: {target}")


def _stage_inputs(build_dir: Path) -> None:
    """把图件和参考文献暂存进构建目录；编译器只读取这些副本。

    源文件在 Windows 上可能出现逻辑长度比有效字节多出一页的情况（读取只能得到有效字节）。
    因此这里按有效字节写出副本，并要求 PDF 以 %%EOF 结尾，否则失败而不是交给编译器报错。
    """
    figure_dir = build_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(FIGURE_DIR.iterdir()):
        if source.suffix.lower() not in {".pdf", ".png"}:
            continue
        data = source.read_bytes()
        if source.suffix.lower() == ".pdf" and not data.rstrip().endswith(b"%%EOF"):
            raise RuntimeError(f"figure PDF is incomplete: {source}")
        if source.stat().st_size != len(data):
            print(f"PAPER_STAGE note: {source.name} 的逻辑长度与有效字节不一致，按有效字节暂存", flush=True)
        _write_verified(figure_dir / source.name, data)
    _write_verified(build_dir / REFERENCES_BIB.name, REFERENCES_BIB.read_bytes())


def _run_stage(label: str, command: list[str]) -> None:
    """运行一个构建阶段；非零退出码转成带阶段名的失败。"""
    print(f"PAPER_STAGE {label}: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    if completed.returncode:
        raise RuntimeError(f"paper stage {label!r} failed with exit code {completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-evidence", action="store_true", help="不重新冻结证据清单")
    parser.add_argument("--skip-figures", action="store_true", help="沿用现有成品图")
    parser.add_argument("--skip-qa", action="store_true", help="跳过源稿审计")
    parser.add_argument("--skip-latex", action="store_true", help="不渲染也不编译 LaTeX")
    args = parser.parse_args()

    try:
        if not args.skip_evidence:
            _run_stage("freeze-evidence", [sys.executable, "-m", "paper.pipeline.audits.freeze_evidence"])
        if not args.skip_figures:
            for name in FIGURE_NAMES:
                _run_stage(name, [sys.executable, "-m", f"paper.pipeline.figure_scripts.{name}"])
            _run_stage("figure-qa", [sys.executable, "-m", "paper.pipeline.figure_scripts.figure_qa", "--strict"])
        if not args.skip_qa:
            _run_stage("manuscript-audit", [sys.executable, "-m", "paper.pipeline.audits.check_manuscript"])
    except RuntimeError as error:
        print(f"PAPER_BUILD_ERROR: {error}", file=sys.stderr)
        return 2

    if not args.skip_latex:
        render_files(MANUSCRIPT_BODY, REFERENCES_BIB, LATEX_TEMPLATE, BUILD_DIR)
        try:
            _stage_inputs(BUILD_DIR)
        except RuntimeError as error:
            print(f"PAPER_BUILD_ERROR: {error}", file=sys.stderr)
            return 2
        try:
            completed = subprocess.run(["tectonic", "main.tex", "--outdir", "."], cwd=BUILD_DIR, check=False)
        except OSError as error:
            print(f"PAPER_BUILD_ERROR: LaTeX compiler unavailable: {error}", file=sys.stderr)
            return 2
        if completed.returncode:
            return completed.returncode
        built_pdf = BUILD_DIR / "main.pdf"
        if not built_pdf.is_file():
            print(f"LaTeX completed without expected output: {built_pdf}", file=sys.stderr)
            return 2
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built_pdf, PAPER_PDF)
        shutil.rmtree(BUILD_DIR)                       # 构建目录是临时的；编译失败时保留以便排查

    report = run_gate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
