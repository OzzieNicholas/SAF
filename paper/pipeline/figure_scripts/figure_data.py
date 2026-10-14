"""图件的网格数据：载入 Fusion 原网格，并把数据集里的接触点逐一映射回原始三角面。

定性图按面着色，必须保证着色的正是生成该样本点的那个面：映射按入库流程（下朝面提取 → 质心外移
2 个体素 → 剔除法向翻转面）重做一遍，点数、顺序或体素坐标不一致即报错，绝不退而求其次地给邻近面上色。
"""
from dataclasses import dataclass


def load_run(kind):
    """实验结果 artifacts/runs/<kind>/result.json 的内容。"""
    import json
    from support_accessibility.runtime.run_records import RUN_ROOT
    with open(RUN_ROOT / kind / "result.json", encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class FaceMapping:
    """数据集接触点与原始三角面的逐一对应。"""

    face_indices: object
    points_vox: object
    face_areas: object


def load_fusion_mesh(name, root):
    """Fusion 设计名 → (Vn, F, occ, lo, pitch)，归一化与占据栅格口径同入库；找不到网格时返回 None。"""
    from support_accessibility.data import mesh as MESH
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility.runtime.frozen_params import FROZEN
    path = dict(iter_final_designs(root)).get(name)
    if path is None:
        return None
    V, F = load_obj(path)
    Vn, _ = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=FROZEN.resolution)
    return Vn, F, occ, lo, pitch


def map_processed_faces(Vn, F, occ, lo, pitch, points_vox, atol=1e-2):
    """重做入库的接触区提取与查询点外移，把每个数据集样本点对应到其源三角面。"""
    import numpy as np
    from support_accessibility.data import mesh as MESH

    faces, points, _flipped = MESH.contact_queries(Vn, F, np.asarray(occ, bool), lo, pitch)
    expected = np.asarray(points_vox, np.float32).reshape(-1, 3)
    if len(faces) != len(expected) or not np.allclose(points, expected, atol=atol):
        raise RuntimeError(f"face mapping mismatch: mapped={len(faces)}, processed={len(expected)}")
    return FaceMapping(faces, points, MESH.face_areas(Vn, F, faces))
