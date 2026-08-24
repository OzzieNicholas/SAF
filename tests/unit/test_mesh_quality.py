"""Unit tests for deterministic raw-mesh quality diagnostics."""

import numpy as np


def test_mesh_quality_reports_boundary_edges_for_single_triangle():
    from support_accessibility.data.mesh_quality import summarize_mesh_quality

    result = summarize_mesh_quality(
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float),
        np.array([[0, 1, 2]], int),
    )

    assert result["n_vertices_raw"] == 3
    assert result["n_vertices_merged"] == 3
    assert result["n_faces"] == 1
    assert result["n_degenerate_faces"] == 0
    assert result["n_boundary_edges"] == 3
    assert result["n_non_manifold_edges"] == 0
    assert result["n_components"] == 1
    assert result["is_watertight"] is False


def test_mesh_quality_counts_degenerate_and_non_manifold_faces():
    from support_accessibility.data.mesh_quality import summarize_mesh_quality

    vertices = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1]], float
    )
    faces = np.array([[0, 1, 2], [1, 0, 3], [0, 1, 4], [0, 0, 2]], int)

    result = summarize_mesh_quality(vertices, faces)

    assert result["n_degenerate_faces"] == 1
    assert result["n_non_manifold_edges"] == 1
    assert result["is_watertight"] is False


def test_mesh_quality_merges_exact_duplicate_vertices_before_topology_checks():
    from support_accessibility.data.mesh_quality import summarize_mesh_quality

    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 1, 0]], float)
    faces = np.array([[0, 1, 3]], int)

    result = summarize_mesh_quality(vertices, faces)

    assert result["n_vertices_raw"] == 4
    assert result["n_vertices_merged"] == 3
    assert result["n_degenerate_faces"] == 0
    assert result["n_boundary_edges"] == 3


def test_mesh_quality_rejects_out_of_range_face_indices():
    import pytest
    from support_accessibility.data.mesh_quality import summarize_mesh_quality

    with pytest.raises(ValueError, match="out of range"):
        summarize_mesh_quality(np.zeros((3, 3)), np.array([[0, 1, 3]], int))
