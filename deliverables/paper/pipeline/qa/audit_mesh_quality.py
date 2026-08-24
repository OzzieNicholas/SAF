#!/usr/bin/env python3
"""Audit raw-mesh quality for the materialized SAF cohorts without relabeling."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (str(SRC), str(TOOLS)):
    if path not in sys.path:
        sys.path.insert(0, path)
from data_paths import resolve_data_paths


def _manifest_rows(data_root: str | os.PathLike[str], source: str) -> list[dict[str, str]]:
    manifest = Path(data_root) / "manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row.get("source") == source]


def _both_class(row: dict[str, str]) -> bool:
    try:
        points = int(row.get("n_points", 0))
        inaccessible = int(row.get("n_inaccessible", 0))
    except (TypeError, ValueError):
        return False
    return points > 0 and 0 < inaccessible < points


def _path_map(source: str, raw_root: str | os.PathLike[str]) -> dict[str, str]:
    if source == "fusion360":
        from support_accessibility.data.fusion360 import iter_final_designs

        return dict(iter_final_designs(str(raw_root)))
    if source == "thingi10k":
        from support_accessibility.data.thingi import iter_thingi_meshes

        return dict(iter_thingi_meshes(str(raw_root)))
    raise ValueError(f"unsupported source: {source}")


def _load_mesh(source: str, path: str):
    if source == "fusion360":
        from support_accessibility.data.fusion360 import load_obj

        return load_obj(path)
    if source == "thingi10k":
        from support_accessibility.data.thingi import load_mesh

        vertices, faces, _normals = load_mesh(path)
        return vertices, faces
    raise ValueError(f"unsupported source: {source}")


def _distribution(values: list[float | int]) -> dict[str, float | int | None]:
    import numpy as np

    if not values:
        return {"count": 0, "min": None, "q1": None, "median": None, "q3": None, "max": None, "mean": None}
    data = np.asarray(values, dtype=float)
    return {
        "count": int(data.size),
        "min": float(data.min()),
        "q1": float(np.quantile(data, 0.25)),
        "median": float(np.median(data)),
        "q3": float(np.quantile(data, 0.75)),
        "max": float(data.max()),
        "mean": float(data.mean()),
    }


def _fraction(values: list[bool | float]) -> float | None:
    if not values:
        return None
    return float(sum(float(value) for value in values) / len(values))


def _cohort_summary(rows: list[dict[str, str]], detail_by_name: dict[str, dict[str, object]]) -> dict[str, object]:
    selected = [detail_by_name[row["name"]] for row in rows]
    audited = [detail for detail in selected if detail["status"] == "audited"]
    qualities = [detail["quality"] for detail in audited]
    return {
        "manifest_rows": len(rows),
        "mapped": sum(detail["status"] != "missing_raw_mesh" for detail in selected),
        "audited": len(audited),
        "missing_raw_mesh": sum(detail["status"] == "missing_raw_mesh" for detail in selected),
        "unreadable_raw_mesh": sum(detail["status"] == "unreadable_raw_mesh" for detail in selected),
        "audit_exclusions": sum(detail["status"] != "audited" for detail in selected),
        "face_count": _distribution([quality["n_faces"] for quality in qualities]),
        "vertex_count_raw": _distribution([quality["n_vertices_raw"] for quality in qualities]),
        "components": _distribution([quality["n_components"] for quality in qualities]),
        "watertight_fraction": _fraction([quality["is_watertight"] for quality in qualities]),
        "mesh_fraction_with_boundary_edges": _fraction([quality["n_boundary_edges"] > 0 for quality in qualities]),
        "mesh_fraction_with_non_manifold_edges": _fraction([quality["n_non_manifold_edges"] > 0 for quality in qualities]),
        "mean_degenerate_face_fraction": _fraction([quality["degenerate_face_fraction"] for quality in qualities]),
        "mean_duplicate_faces": _fraction([quality["n_duplicate_faces"] for quality in qualities]),
    }


def audit_source(source: str, data_root: str | os.PathLike[str], raw_root: str | os.PathLike[str]):
    """Return source-level retained-cohort summaries and per-record diagnostics."""
    from support_accessibility.data.mesh_quality import summarize_mesh_quality

    rows = _manifest_rows(data_root, source)
    paths = _path_map(source, raw_root)
    details: list[dict[str, object]] = []
    for row in rows:
        name = row["name"]
        raw_path = paths.get(name)
        detail: dict[str, object] = {
            "name": name,
            "source": source,
            "both_class": _both_class(row),
            "raw_path": raw_path,
        }
        if raw_path is None:
            detail["status"] = "missing_raw_mesh"
        else:
            try:
                vertices, faces = _load_mesh(source, raw_path)
                detail["status"] = "audited"
                detail["quality"] = summarize_mesh_quality(vertices, faces)
            except Exception as error:  # A raw source failure is audit evidence, not a reason to hide a row.
                detail["status"] = "unreadable_raw_mesh"
                detail["error"] = f"{type(error).__name__}: {error}"
        details.append(detail)

    detail_by_name = {detail["name"]: detail for detail in details}
    summary = {
        "source": source,
        "raw_root": str(Path(raw_root)),
        "all_materialized": _cohort_summary(rows, detail_by_name),
        "both_class": _cohort_summary([row for row in rows if _both_class(row)], detail_by_name),
    }
    return summary, details


def _resolve_output(path: str) -> Path:
    output = Path(path)
    return output if output.is_absolute() else ROOT / output


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit retained SAF raw meshes without changing labels")
    parser.add_argument("--fusion-data", default="${SAF_TEMPORARY_ROOT}/SAF/fusion360_full/latest")
    parser.add_argument("--fusion-root", default=str(resolve_data_paths().fusion360_root))
    parser.add_argument("--thingi-data", default="${SAF_TEMPORARY_ROOT}/SAF/thingi_v1/latest")
    parser.add_argument("--thingi-root", default=str(resolve_data_paths().thingi_root))
    parser.add_argument("--out", default="artifacts/runs/mesh_quality/latest.json")
    parser.add_argument("--details-out", default="", help="current per-model JSON; default is next to --out")
    args = parser.parse_args()

    sources = []
    details = []
    for source, data_root, raw_root in (
        ("fusion360", args.fusion_data, args.fusion_root),
        ("thingi10k", args.thingi_data, args.thingi_root),
    ):
        if not Path(data_root).is_dir():
            raise FileNotFoundError(f"processed dataset does not exist: {data_root}")
        if not Path(raw_root).is_dir():
            raise FileNotFoundError(f"raw mesh root does not exist: {raw_root}")
        summary, source_details = audit_source(source, data_root, raw_root)
        sources.append(summary)
        details.extend(source_details)

    output = _resolve_output(args.out)
    details_output = _resolve_output(args.details_out) if args.details_out else output.with_name(f"{output.stem}_details.json")
    from artifacts import write_result

    payload = {
        "scope": "retained materialized cohorts only; descriptive raw-mesh audit; no relabeling",
        "metric_definitions": {
            "watertight_fraction": "fraction of successfully audited meshes with no boundary or non-manifold edges after exact vertex merge and degenerate-face exclusion",
            "mesh_fraction_with_boundary_edges": "fraction of successfully audited meshes with at least one boundary edge",
            "mesh_fraction_with_non_manifold_edges": "fraction of successfully audited meshes with at least one edge used by more than two nondegenerate faces",
            "mean_degenerate_face_fraction": "unweighted mean of per-mesh degenerate-triangle fractions",
        },
        "sources": sources,
        "details_current_path": _relative(details_output),
    }
    record = write_result(
        "mesh_quality",
        payload,
        output=args.out,
        inputs=(args.fusion_data, args.fusion_root, args.thingi_data, args.thingi_root),
    )
    details_payload = {"run_id": record["run_id"], "sources": details}
    details_output.parent.mkdir(parents=True, exist_ok=True)
    run_details = details_output.parent / f"{record['run_id']}_details.json"
    for target in (details_output, run_details):
        target.write_text(json.dumps(details_payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": record["run_id"], "sources": sources, "details": _relative(details_output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
