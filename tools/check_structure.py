#!/usr/bin/env python3
"""Mechanical repository layout, naming, dependency, and path checks.

Canonical roots include ``AGENTS.md`` and ``artifacts/cache/``.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY_NAME = re.compile(r"^[a-z_][a-z0-9_]*\.py$")
DIR_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")
OLD_PATHS = {
    "charter/": re.compile(r"(?<![A-Za-z0-9_/-])charter/"),
    "conf/": re.compile(r"(?<![A-Za-z0-9_/-])conf/"),
    "paper/": re.compile(r"(?<![A-Za-z0-9_/-])paper/"),
    "runs/": re.compile(r"(?<![A-Za-z0-9_/-])runs/"),
    "hooks/": re.compile(r"(?<![A-Za-z0-9_/-])hooks/"),
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def files():
    excluded = {".git", ".pytest_cache", ".hypothesis", "__pycache__", "data", "artifacts", "tmp"}
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in excluded]
        for name in names:
            yield Path(base) / name


def check() -> list[str]:
    errors: list[str] = []
    forbidden = ("charter", "conf", "paper", "runs", "hooks", "method", "data")
    for name in forbidden:
        if (ROOT / name).exists():
            errors.append(f"forbidden root directory exists: {name}/")
    for relative in ("artifacts/archive", "deliverables/archive"):
        if (ROOT / relative).exists():
            errors.append(f"retired archive must not exist in the active tree: {relative}/")
    for relative in (".dvcignore", "dvc.yaml", "dvc.lock"):
        if (ROOT / relative).exists():
            errors.append(f"retired DVC metadata must not exist: {relative}")
    if not (ROOT / "AGENTS.md").is_file():
        errors.append("AGENTS.md is missing")
    if (ROOT / "CLAUDE.md").exists():
        errors.append("CLAUDE.md must not be an active root entrypoint")

    try:
        manifest = json.loads((ROOT / "governance" / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"project manifest unreadable: {exc}")
        manifest = {}
    for key, value in manifest.get("roots", {}).items():
        if key == "dvc":
            errors.append("project manifest must not declare a DVC root")
        elif not (ROOT / value).is_dir():
            errors.append(f"manifest root missing: {key}={value}")

    excluded = {".git", ".pytest_cache", ".hypothesis", "__pycache__", "data", "artifacts", "tmp"}
    for base, dirs, _ in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in excluded]
        base_rel = Path(base).relative_to(ROOT).parts
        if not base_rel or base_rel[0] not in {"src", "tests", "tools"}:
            continue
        for name in dirs:
            if not DIR_NAME.match(name):
                errors.append(f"Python project directory is not snake_case: {rel(Path(base) / name)}/")

    for path in files():
        name = path.name
        path_rel = rel(path)
        if path.suffix == ".py" and not PY_NAME.match(name):
            errors.append(f"Python filename is not snake_case: {path_rel}")
        if path_rel.startswith("tests/acceptance/") and name not in {"__init__.py"}:
            if not name.startswith("test_"):
                errors.append(f"acceptance test must use test_ prefix: {path_rel}")
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "def checks(" not in text:
                errors.append(f"acceptance module lacks checks(): {path_rel}")
        if path.parts[0] == "src" and path.suffix == ".py":
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if re.search(r"(?:^|\n)\s*(?:from|import)\s+(?:tools|tests)(?:\.|\s|$)", text):
                errors.append(f"src code imports tools/tests: {path_rel}")
        if path.suffix in {".md", ".py", ".yml", ".yaml", ".json", ".toml"}:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if path_rel in {"governance/decisions.md", "docs/other/GPT.md",
                            "tests/acceptance/test_governance.py", "tools/check_structure.py"}:
                continue
            for label, pattern in OLD_PATHS.items():
                if pattern.search(text):
                    errors.append(f"stale active path {label}: {path_rel}")
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
