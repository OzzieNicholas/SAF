"""论文证据清单（``paper/evidence/manifest.json``）的读取与校验。

论文和图件只引用被清单冻结了路径、SHA-256 与运行号的实验结果；
结果文件一旦改动或被重跑，加载时即失败，必须重新冻结清单。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MANIFEST_KIND = "paper_evidence"


def _inside_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Evidence path escapes repository root: {resolved}") from exc
    return resolved


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read evidence JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Evidence JSON must contain an object: {path}")
    return value


def load_manifest(path: str | Path, root: str | Path) -> dict[str, Any]:
    """读取并校验证据清单本身。"""
    repo_root = Path(root).resolve()
    manifest = _read_json(_inside_root(Path(path), repo_root))
    if manifest.get("artifact_schema_version") != SCHEMA_VERSION:
        raise RuntimeError(
            f"Paper manifest schema must be {SCHEMA_VERSION}: {manifest.get('artifact_schema_version')}"
        )
    if manifest.get("kind") != MANIFEST_KIND:
        raise RuntimeError(f"Expected {MANIFEST_KIND} manifest, got {manifest.get('kind')!r}")
    if not isinstance(manifest.get("canonical_runs"), dict):
        raise RuntimeError("Paper manifest has no canonical_runs object")
    return manifest


def load_canonical_artifact(manifest: dict[str, Any], key: str, root: str | Path) -> dict[str, Any]:
    """读取清单里的一份实验结果，并拒绝路径、哈希、模式、实验名或运行号漂移。

    清单的键就是实验名，结果文件里的 ``kind`` 必须与之相同。
    """
    runs = manifest.get("canonical_runs")
    if not isinstance(runs, dict) or not isinstance(runs.get(key), dict):
        raise RuntimeError(f"Paper manifest has no canonical run entry for {key!r}")
    entry = runs[key]
    for field in ("path", "sha256", "run_id"):
        if not isinstance(entry.get(field), str) or not entry[field]:
            raise RuntimeError(f"Canonical run {key!r} has no valid {field}")

    repo_root = Path(root).resolve()
    artifact_path = _inside_root(repo_root / entry["path"], repo_root)
    if not artifact_path.is_file():
        raise RuntimeError(f"Canonical artifact is missing: {artifact_path}")

    actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if actual_hash.lower() != entry["sha256"].lower():
        raise RuntimeError(
            f"Canonical artifact SHA-256 mismatch for {key}: expected {entry['sha256']}, got {actual_hash}"
        )

    artifact = _read_json(artifact_path)
    if artifact.get("artifact_schema_version") != SCHEMA_VERSION:
        raise RuntimeError(
            f"Canonical artifact schema must be {SCHEMA_VERSION} for {key}: {artifact.get('artifact_schema_version')}"
        )
    if artifact.get("kind") != key:
        raise RuntimeError(f"Canonical artifact kind mismatch for {key}: got {artifact.get('kind')!r}")
    if artifact.get("run_id") != entry["run_id"]:
        raise RuntimeError(
            f"Canonical artifact run_id mismatch for {key}: "
            f"expected {entry['run_id']!r}, got {artifact.get('run_id')!r}"
        )
    return artifact
