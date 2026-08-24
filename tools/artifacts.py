"""Shared lifecycle helpers for machine-generated SAF artifacts.

``artifacts/runs`` contains retained evidence.  Disposable checkpoints, logs,
and candidate images belong under ``artifacts/cache`` and are safe to prune.
The helper deliberately never deletes from the evidence tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts"
RUN_ROOT = ARTIFACT_ROOT / "runs"
CACHE_ROOT = ARTIFACT_ROOT / "cache"
SCHEMA_VERSION = 1
_ABSOLUTE_TOKEN_RE = re.compile(r"(?i)(?:[A-Za-z]:[\\/]|\\\\)[^\s\"]+")


def _portable_command(command: str) -> str:
    """Keep command provenance useful without embedding local drive paths."""
    return _ABSOLUTE_TOKEN_RE.sub("<external-path>", command)


def _portable_value(value):
    """Recursively remove machine-specific paths from JSON payloads."""
    if isinstance(value, Mapping):
        return {str(key): _portable_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_portable_value(item) for item in value]
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str):
        try:
            from data_paths import logical_data_ref
        except ImportError:
            from tools.data_paths import logical_data_ref

        if re.match(r"(?i)^(?:[A-Za-z]:[\\/]|\\\\|/)", value):
            return logical_data_ref(value)
    return value


def _cache_scope(kind: str | None = None) -> Path:
    """Resolve a cache scope and reject absolute or escaping paths."""
    root = CACHE_ROOT.resolve()
    if kind is None or kind == "":
        return root
    candidate = (root / Path(kind)).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"cache scope escapes {root}: {kind}")
    return candidate


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def input_digest(paths: Iterable[str | os.PathLike[str]]) -> str:
    """Return a stable digest of input paths and their file metadata.

    Hashing metadata keeps a run manifest cheap even for large datasets while
    still invalidating it when an input file is added, removed, or changed.
    """
    rows: list[str] = []
    for raw in paths:
        if raw is None or str(raw) == "":
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_file():
            stat = path.stat()
            rows.append(f"{_relative(path)}:{stat.st_size}:{stat.st_mtime_ns}")
        elif path.is_dir():
            for child in sorted(p for p in path.rglob("*") if p.is_file()):
                stat = child.stat()
                rows.append(f"{_relative(child)}:{stat.st_size}:{stat.st_mtime_ns}")
        else:
            rows.append(f"{_relative(path)}:missing")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:16]


def _git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_metadata(kind: str, inputs: Iterable[str | os.PathLike[str]] = ()) -> dict[str, object]:
    """Build the common evidence envelope for one tool invocation."""
    now = datetime.now(timezone.utc)
    run_id = f"{now.strftime('%Y%m%dT%H%M%S.%fZ')}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    return {
        "artifact_schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "kind": kind,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "command": _portable_command(subprocess.list2cmdline(sys.argv)),
        "tool": _relative(Path(sys.argv[0]).resolve()),
        "tool_revision": _git_revision(),
        "input_digest": input_digest(inputs),
    }


def write_result(
    kind: str,
    payload: Mapping[str, object],
    output: str | os.PathLike[str] | None = None,
    inputs: Iterable[str | os.PathLike[str]] = (),
) -> dict[str, object]:
    """Write a retained result and a run-id copy, returning the enriched payload."""
    target = Path(output) if output is not None else RUN_ROOT / kind / "latest.json"
    if not target.is_absolute():
        target = ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    enriched = dict(run_metadata(kind, inputs))
    enriched.update(_portable_value(payload))
    run_file = target.parent / f"{enriched['run_id']}.json"
    for path in (run_file, target):
        with path.open("w", encoding="utf-8") as handle:
            json.dump(enriched, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
    return enriched


def cache_path(kind: str, name: str) -> Path:
    """Return a safe path below the disposable cache root."""
    scope = _cache_scope(kind)
    path = (scope / name).resolve()
    root = CACHE_ROOT.resolve()
    if path == root or root not in path.parents:
        raise ValueError(f"cache path escapes {root}: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cache_root(kind: str | None = None) -> Path:
    path = _cache_scope(kind)
    path.mkdir(parents=True, exist_ok=True)
    return path
