"""Regression coverage for the submission integrity sidecar."""


def test_sidecar_tracks_the_refreshed_submission_evidence():
    from tools.paper.build_integrity_sidecar import CLAIMS, _experiment_provenance

    claims = {claim_id: text for claim_id, text, *_rest in CLAIMS}

    assert "0.793" in claims["C-H3"]
    assert "0.948" in claims["C-H3"]
    assert "0.920" in claims["C-E4"]
    assert "0.853" in claims["C-E4"]
    assert "0.901" in claims["C-E5"]
    assert "0.817" in claims["C-E5"]

    experiments = {item["experiment_id"]: item for item in _experiment_provenance()}
    mesh_audit = experiments["EXP-MESH"]
    paths = {item["path"] for item in mesh_audit["repro_lock"]["artifacts"]}

    assert "artifacts/runs/mesh_quality/latest.json" in paths
    assert "artifacts/runs/paper_review_metrics/latest.json" in {
        item["path"] for item in experiments["EXP-H3"]["repro_lock"]["artifacts"]
    }
    assert "artifacts/runs/paper_direction_audit/latest.json" in {
        item["path"] for item in experiments["EXP-E5"]["repro_lock"]["artifacts"]
    }
    assert "0.920" in experiments["EXP-REG"]["negative_results"][0]
    assert "0.893" not in experiments["EXP-REG"]["negative_results"][0]
