"""D-028 publication evidence must map processed samples to exact source faces."""
import os
import sys
from unittest import SkipTest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support_accessibility.runtime.data_paths import resolve_data_paths
FIGURE_TOOLS = os.path.join(ROOT, "paper", "pipeline", "figures")
if FIGURE_TOOLS not in sys.path:
    sys.path.insert(0, FIGURE_TOOLS)

from . import pending, result

try:
    from paper.pipeline.figure_scripts import figure_data as D  # noqa: E402
    from paper.pipeline.figure_scripts import figure_cases as X  # noqa: E402
    _IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - exercised by bare interpreters
    D = X = None
    _IMPORT_ERROR = exc


def checks():
    if _IMPORT_ERROR is not None:
        return [pending("figure_face_mapping", f"依赖未就绪：{_IMPORT_ERROR}", "D-028")]
    return [result("figure_face_mapping", True, "出版物样本面映射模块可加载", "D-028")]


def _require_modules():
    if _IMPORT_ERROR is not None:
        raise SkipTest(f"依赖未就绪：{_IMPORT_ERROR}")


def _require(path, description):
    if not os.path.exists(path):
        raise SkipTest(f"{description} is not available: {path}")


def _datasets():
    _require_modules()
    from support_accessibility.data.dataset import load_dataset

    paths = resolve_data_paths()
    fusion_path = str(paths.processed_root("fusion360"))
    thingi_path = str(paths.processed_root("thingi10k"))
    _require(fusion_path, "processed Fusion data")
    _require(thingi_path, "processed Thingi data")
    fusion, _ = load_dataset(fusion_path)
    thingi, _ = load_dataset(thingi_path)
    return ({item.name: item for item in fusion},
            {item.name: item for item in thingi})


def _assert_mapping(mapping, points, labels, lo, pitch):
    import numpy as np

    points = np.asarray(points, np.float32)
    assert len(mapping.face_indices) == len(points) == len(labels)
    assert np.array_equal(mapping.points_vox, points)
    assert len(np.unique(mapping.face_indices)) == len(mapping.face_indices)
    assert np.all(mapping.face_areas > 0)
    mapped_world = np.asarray(lo) + (mapping.points_vox + .5) * float(pitch)
    expected_world = np.asarray(lo) + (points + .5) * float(pitch)
    assert np.allclose(mapped_world, expected_world, atol=1e-7)


def test_fixed_fusion_face_mapping_order_and_world_coordinates():
    fusion, _ = _datasets()
    model = fusion[X.FRAMEWORK_LABEL.name]
    loaded = D.load_fusion_mesh(model.name, X.FUSION_ROOT)
    if loaded is None:
        raise SkipTest(f"Fusion raw mesh is not available: {model.name}")
    vertices, faces, occupancy, lo, pitch = loaded
    mapping = D.map_processed_faces(vertices, faces, occupancy, lo, pitch, model.points)
    _assert_mapping(mapping, model.points, model.labels, lo, pitch)


def test_fixed_thingi_face_mapping_uses_stored_normals():
    _, thingi = _datasets()
    example = X.PREDICTION_HEATMAP[1]
    model = thingi[example.name]
    _require(X.THINGI_ROOT, "Thingi raw mesh root")
    vertices, faces, occupancy, lo, pitch, normals = D.load_thingi_mesh(
        model.name, X.THINGI_ROOT, include_normals=True
    )
    mapping = D.map_processed_faces(
        vertices, faces, occupancy, lo, pitch, model.points,
        "thingi", stored_normals=normals
    )
    _assert_mapping(mapping, model.points, model.labels, lo, pitch)


def test_fixed_failure_case_mapping_and_mismatch_fail_closed():
    import numpy as np
    import pytest

    _require_modules()
    artifact_path = os.path.join(ROOT, "artifacts", "runs", "failure_analysis", "error_boundary_case.npz")
    _require(artifact_path, "Figure 10 failure artifact")
    artifact = np.load(artifact_path, allow_pickle=True)
    assert str(artifact["name"]) == X.ERROR_BOUNDARY.name
    loaded = D.load_fusion_mesh(X.ERROR_BOUNDARY.name, X.FUSION_ROOT)
    if loaded is None:
        raise SkipTest(f"Fusion raw mesh is not available: {X.ERROR_BOUNDARY.name}")
    vertices, faces, occupancy, lo, pitch = loaded
    gold = np.asarray(artifact["gold"], bool)
    mapping = D.map_processed_faces(
        vertices, faces, occupancy, lo, pitch, artifact["points"]
    )
    _assert_mapping(mapping, artifact["points"], gold, lo, pitch)
    assert len(artifact["fp"]) == len(artifact["fn"]) == len(gold)

    corrupted = np.asarray(artifact["points"], np.float32).copy()
    corrupted[0, 0] += .25
    with pytest.raises(RuntimeError, match="D-028 face mapping mismatch"):
        D.map_processed_faces(vertices, faces, occupancy, lo, pitch, corrupted)
