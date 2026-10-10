#!/usr/bin/env python3
"""仓库布局守卫：目录白名单、命名、依赖方向、文档规范与可移植性（已入库文本不含绝对路径）。

只用标准库。由 ``tests/acceptance/test_governance.py`` 调用，也可直接运行：
``python tools/check_structure.py``。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_DIRS = {".git", ".github", "artifacts", "configs", "data", "docs", "experiments",
                  "governance", "paper", "src", "tests", "tools"}
TOP_LEVEL_CACHES = {".claude", ".pytest_cache", ".hypothesis", ".mypy_cache", ".ruff_cache"}
TOP_LEVEL_FILES = {".gitignore", "AGENTS.md", "LICENSE", "README.md", "environment.yml", "pyproject.toml"}

PY_NAME = re.compile(r"^[a-z_][a-z0-9_]*\.py$")
DIR_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")
PYTHON_ROOTS = ("src", "experiments", "tools", "tests", "paper/pipeline")
FORBIDDEN_IN_SRC = re.compile(r"(?:^|\n)\s*(?:from|import)\s+(?:tools|experiments|tests|paper)(?:\.|\s|$)")

# 盘符绝对路径（排除 URL 的 "https://"）；路径检测器与合成反例自身须豁免。
DRIVE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:(?:\\|/(?!/))[A-Za-z0-9_.$\\{]")
ABSOLUTE_PATH_EXEMPT = {
    "tools/check_structure.py",
    "paper/pipeline/paper_gate.py",
    "src/support_accessibility/runtime/run_records.py",
    "src/support_accessibility/runtime/data_paths.py",
    "tests/paper_pipeline/test_paper_gate.py",
    "tests/unit/test_run_records.py",
}
# 文档里的日期/运行时间戳（引用文献的年份不算）。
DATE_TOKEN = re.compile(r"20\d\d-\d\d-\d\d|20\d\d年\d{1,2}月|\b20\d{6}T\d{6}")
# 参考文献年份与按运行号固定的证据清单（运行号自带时间戳）不算文档日期
DATE_EXEMPT_PREFIXES = ("paper/manuscript/", "paper/evidence/")
CJK = re.compile(r"[一-鿿]")
DOC_DIRS = ("governance", "docs", "paper")


def tracked_files() -> list[str]:
    """git 跟踪（含未跟踪但未忽略）的文件；非 git 环境回落到遍历。"""
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-files", "-co", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
        return [line for line in out.splitlines() if line and (ROOT / line).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def _read(rel: str) -> str | None:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check() -> list[str]:
    errors: list[str] = []
    files = tracked_files()

    for entry in ROOT.iterdir():
        if entry.is_dir() and entry.name not in TOP_LEVEL_DIRS | TOP_LEVEL_CACHES:
            errors.append(f"unexpected top-level directory: {entry.name}/")
        elif entry.is_file() and entry.name not in TOP_LEVEL_FILES:
            errors.append(f"unexpected top-level file: {entry.name}")

    for rel in files:
        path = Path(rel)
        if not rel.startswith(tuple(f"{root}/" for root in PYTHON_ROOTS)):
            continue
        if path.suffix != ".py" and path.name != "README.md":
            continue
        for part in path.parts[:-1]:
            if not DIR_NAME.match(part):
                errors.append(f"directory is not snake_case: {rel}")
                break
        if path.suffix == ".py" and not PY_NAME.match(path.name):
            errors.append(f"Python filename is not snake_case: {rel}")
        if rel.startswith("tests/acceptance/") and path.name != "__init__.py" and path.suffix == ".py":
            if not path.name.startswith("test_"):
                errors.append(f"acceptance test must use test_ prefix: {rel}")
            if "def checks(" not in (_read(rel) or ""):
                errors.append(f"acceptance module lacks checks(): {rel}")
        if rel.startswith("src/") and path.suffix == ".py" and FORBIDDEN_IN_SRC.search(_read(rel) or ""):
            errors.append(f"src code imports tools/experiments/tests/paper: {rel}")

    for rel in files:
        if rel.endswith((".md", ".py", ".yml", ".yaml", ".toml", ".tex")) and rel not in ABSOLUTE_PATH_EXEMPT:
            text = _read(rel)
            if text and DRIVE_PATH.search(text):
                errors.append(f"absolute drive path in tracked text: {rel}")

    for rel in files:
        path = Path(rel)
        if path.suffix != ".md" or path.name == "README.md" or path.parts[0] not in DOC_DIRS:
            continue
        if not CJK.search(path.stem):
            errors.append(f"document name should be Chinese: {rel}")
        if not rel.startswith(DATE_EXEMPT_PREFIXES) and DATE_TOKEN.search(_read(rel) or ""):
            errors.append(f"document contains a date/timestamp: {rel}")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("structure check failed")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("structure check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
