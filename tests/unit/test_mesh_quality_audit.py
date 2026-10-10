"""Fixture-level tests for retained-cohort raw-mesh quality audits."""

import csv


def test_fusion_audit_maps_manifest_record_to_final_obj(tmp_path):
    from experiments.mesh_quality_audit import audit_source

    data_root = tmp_path / "processed"
    data_root.mkdir()
    with (data_root / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "source", "n_points", "n_inaccessible"])
        writer.writeheader()
        writer.writerow({"name": "piece_0000", "source": "fusion360", "n_points": 5, "n_inaccessible": 2})

    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    (raw_root / "piece_0000.json").write_text("{}", encoding="utf-8")
    (raw_root / "piece_0000.obj").write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8"
    )

    summary, details = audit_source("fusion360", data_root, raw_root)

    assert summary["all_materialized"]["manifest_rows"] == 1
    assert summary["all_materialized"]["mapped"] == 1
    assert summary["all_materialized"]["missing_raw_mesh"] == 0
    assert summary["both_class"]["manifest_rows"] == 1
    assert details[0]["status"] == "audited"
    assert details[0]["quality"]["n_faces"] == 1
    assert details[0]["quality"]["n_boundary_edges"] == 3
