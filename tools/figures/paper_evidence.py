"""Load figure inputs only when they match the frozen paper evidence manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


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
    """Load and validate the paper-rewrite manifest itself."""
    repo_root = Path(root).resolve()
    manifest_path = _inside_root(Path(path), repo_root)
    manifest = _read_json(manifest_path)
    if manifest.get("artifact_schema_version") != SCHEMA_VERSION:
        raise RuntimeError(
            f"Paper manifest schema must be {SCHEMA_VERSION}: {manifest.get('artifact_schema_version')}"
        )
    if manifest.get("kind") != "paper_rewrite":
        raise RuntimeError(f"Expected paper_rewrite manifest, got {manifest.get('kind')!r}")
    if not isinstance(manifest.get("canonical_runs"), dict):
        raise RuntimeError("Paper manifest has no canonical_runs object")
    return manifest


def load_canonical_artifact(
    manifest: dict[str, Any],
    key: str,
    expected_kind: str,
    root: str | Path,
) -> dict[str, Any]:
    """Load one manifest entry and reject path, hash, schema, kind, or run drift."""
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
            f"Canonical artifact SHA-256 mismatch for {key}: "
            f"expected {entry['sha256']}, got {actual_hash}"
        )

    artifact = _read_json(artifact_path)
    if artifact.get("artifact_schema_version") != SCHEMA_VERSION:
        raise RuntimeError(
            f"Canonical artifact schema must be {SCHEMA_VERSION} for {key}: "
            f"{artifact.get('artifact_schema_version')}"
        )
    if artifact.get("kind") != expected_kind:
        raise RuntimeError(
            f"Canonical artifact kind mismatch for {key}: "
            f"expected {expected_kind!r}, got {artifact.get('kind')!r}"
        )
    if artifact.get("run_id") != entry["run_id"]:
        raise RuntimeError(
            f"Canonical artifact run_id mismatch for {key}: "
            f"expected {entry['run_id']!r}, got {artifact.get('run_id')!r}"
        )
    return artifact
