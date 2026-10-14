"""D-028：定性图按面着色时，数据集样本点必须逐一映射回生成它的原始三角面。"""
from unittest import SkipTest

from support_accessibility.runtime.data_paths import resolve_data_paths

from . import pending, result

try:
    from paper.pipeline.figure_scripts import figure_cases as X
    from paper.pipeline.figure_scripts import figure_data as D
    _IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - exercised by bare interpreters
    D = X = None
    _IMPORT_ERROR = exc


def checks():
    if _IMPORT_ERROR is not None:
        return [pending("figure_face_mapping", f"依赖未就绪：{_IMPORT_ERROR}", "D-028")]
    return [result("figure_face_mapping", True, "出版物样本面映射模块可加载", "D-028")]


def _fixed_case():
    """方法总览案例的 (数据集记录, 原网格)；外部数据缺失时跳过。"""
    if _IMPORT_ERROR is not None:
        raise SkipTest(f"依赖未就绪：{_IMPORT_ERROR}")
    from support_accessibility.data.dataset import load_dataset
    paths = resolve_data_paths()
    if not paths.processed_root("fusion360").exists():
        raise SkipTest("processed Fusion data is not available")
    model = next(m for m in load_dataset(str(paths.processed_root("fusion360")))[0] if m.name == X.METHOD_OVERVIEW)
    loaded = D.load_fusion_mesh(model.name, str(paths.fusion360_root))
    if loaded is None:
        raise SkipTest(f"Fusion raw mesh is not available: {model.name}")
    return model, loaded


def test_fixed_case_maps_every_sample_to_a_distinct_source_face():
    import numpy as np
    model, (vertices, faces, occupancy, lo, pitch) = _fixed_case()
    mapping = D.map_processed_faces(vertices, faces, occupancy, lo, pitch, model.points)
    assert len(mapping.face_indices) == len(model.points) == len(model.labels)
    assert np.array_equal(mapping.points_vox, np.asarray(model.points, np.float32))
    assert len(np.unique(mapping.face_indices)) == len(mapping.face_indices)
    assert np.all(mapping.face_areas > 0)


def test_mapping_mismatch_fails_closed():
    import numpy as np
    import pytest
    model, (vertices, faces, occupancy, lo, pitch) = _fixed_case()
    corrupted = np.asarray(model.points, np.float32).copy()
    corrupted[0, 0] += .25
    with pytest.raises(RuntimeError, match="face mapping mismatch"):
        D.map_processed_faces(vertices, faces, occupancy, lo, pitch, corrupted)
