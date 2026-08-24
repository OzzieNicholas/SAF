"""Resolve SAF's external data and temporary-run locations.

SAF deliberately keeps datasets outside the repository so the same public
corpora can be shared by multiple projects.  This module is the single path
contract used by command-line tools and the paper pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
import ntpath
import os
from pathlib import Path


DEFAULT_DATA_ROOT = Path(r"E:\Work\Data")
DEFAULT_RUN_ID = "latest"
_PROCESSED_DATASETS = ("fusion360_full", "procedural_v1", "thingi_v1")


@dataclass(frozen=True)
class DataPaths:
    """Logical SAF data roots and external dataset locations."""

    data_root: Path
    temporary_root: Path
    fusion360_root: Path
    thingi_root: Path
    run_id: str = DEFAULT_RUN_ID

    def processed_root(self, dataset: str, run_id: str | None = None) -> Path:
        """Return the external processed-data directory for one run."""
        name = str(dataset).strip().replace("\\", "/").strip("/")
        if not name or name in {".", ".."} or ".." in name.split("/"):
            raise ValueError(f"invalid dataset name: {dataset!r}")
        rid = str(run_id or self.run_id).strip()
        if not rid or rid in {".", ".."} or any(ch in rid for ch in "\\/"):
            raise ValueError(f"invalid run id: {run_id!r}")
        return self.temporary_root / "SAF" / name / rid

    def logical_manifest(self, dataset: str, run_id: str | None = None) -> dict[str, str]:
        """Return a machine-independent manifest fragment."""
        return {
            "project": "SAF",
            "dataset": str(dataset),
            "run_id": str(run_id or self.run_id),
            "source_root_id": str(dataset),
        }


def resolve_data_paths(
    data_root: str | os.PathLike[str] | None = None,
    temporary_root: str | os.PathLike[str] | None = None,
    run_id: str | None = None,
) -> DataPaths:
    """Resolve external roots from arguments, environment, then defaults."""
    root = Path(data_root or os.environ.get("SAF_DATA_ROOT") or DEFAULT_DATA_ROOT)
    temp = Path(
        temporary_root
        or os.environ.get("SAF_TEMPORARY_ROOT")
        or root / "Temporary"
    )
    fusion = Path(
        os.environ.get("SAF_FUSION360_ROOT")
        or root / "Fusion360Gallery" / "reconstruction"
    )
    thingi = Path(
        os.environ.get("SAF_THINGI_ROOT")
        or root / "Thingi10K" / "raw_meshes"
    )
    rid = str(run_id or os.environ.get("SAF_RUN_ID") or DEFAULT_RUN_ID)
    return DataPaths(root, temp, fusion, thingi, rid)


def _relative_to(path: Path, root: Path) -> str | None:
    """Return a POSIX relative path without requiring either path to exist."""
    raw_path, raw_root = str(path), str(root)
    if ntpath.splitdrive(raw_path)[0] or ntpath.splitdrive(raw_root)[0]:
        path_norm = ntpath.normcase(ntpath.normpath(raw_path))
        root_norm = ntpath.normcase(ntpath.normpath(raw_root))
        try:
            relative = ntpath.relpath(path_norm, root_norm)
        except ValueError:
            return None
        if relative == ".." or relative.startswith("..\\"):
            return None
        return relative.replace("\\", "/")
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return None


def _looks_absolute(raw: str) -> bool:
    """Recognize Windows paths even when a manifest is inspected on POSIX."""
    return Path(raw).is_absolute() or ntpath.isabs(raw) or bool(ntpath.splitdrive(raw)[0])


def logical_data_ref(
    raw: str | os.PathLike[str] | None, paths: DataPaths | None = None
) -> str:
    """Convert a local data path to a portable logical reference.

    Processed datasets are represented as ``dataset://<name>/<run_id>`` and
    source meshes as ``source://...``.  Unknown absolute paths intentionally
    collapse to ``external://unidentified`` so a run envelope cannot leak a
    machine-specific location.
    """
    if raw is None or str(raw) == "":
        return ""
    text = str(raw)
    if text.startswith("${SAF_") or text.startswith(("dataset://", "source://", "external://")):
        return text.replace("\\", "/")
    if not _looks_absolute(text):
        return Path(text).as_posix()

    resolved = Path(text)
    paths = paths or resolve_data_paths()
    for dataset in _PROCESSED_DATASETS:
        root = paths.processed_root(dataset)
        relative = _relative_to(resolved, root)
        if relative is not None:
            suffix = f"/{relative}" if relative != "." else ""
            return f"dataset://{dataset}/{root.name}{suffix}"
    for source, root in (
        ("fusion360_gallery/reconstruction", paths.fusion360_root),
        ("thingi10k/raw_meshes", paths.thingi_root),
    ):
        relative = _relative_to(resolved, root)
        if relative is not None:
            suffix = f"/{relative}" if relative != "." else ""
            return f"source://{source}{suffix}"
    return "external://unidentified"


def resolve_logical_data_ref(
    reference: str, paths: DataPaths | None = None
) -> Path | None:
    """Resolve a ``logical_data_ref`` for local consumers such as gate checks."""
    if not isinstance(reference, str) or not reference.startswith("dataset://"):
        return None
    parts = reference.removeprefix("dataset://").split("/")
    if len(parts) < 2 or parts[0] not in _PROCESSED_DATASETS:
        return None
    dataset, run_id = parts[:2]
    root = (paths or resolve_data_paths()).processed_root(dataset, run_id)
    if len(parts) > 2:
        root = root.joinpath(*parts[2:])
    return root


def ensure_run_root(paths: DataPaths, dataset: str, run_id: str | None = None) -> Path:
    """Create and return an external temporary run directory."""
    target = paths.processed_root(dataset, run_id)
    target.mkdir(parents=True, exist_ok=True)
    return target


def default_processed(dataset: str) -> str:
    """Return the default external processed path for a CLI argument."""
    return str(resolve_data_paths().processed_root(dataset))
