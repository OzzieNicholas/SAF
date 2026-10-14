#!/usr/bin/env python3
"""支撑接触量能否预示可达性：全部 Fusion 零件上，接触量与不可达占比的 Spearman 相关。

两种口径同时报告：接触点数与不可达点占比（数据集口径，每个下朝三角面一个接触点），以及真实三角面积与
不可达面积占比（从原网格重做接触区提取与查询点外移，与数据集逐点对齐后按面积加权）。对齐失败的零件
跳过并计数。分别在全部零件与两类零件上计算。

用法：
  python experiments/contact_area_vs_accessibility.py --workers 16
"""
import argparse
import os

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import logical_data_ref, resolve_data_paths

setup_console()


def _part_areas(task):
    """工作进程：一个零件各接触点对应三角面的面积；与数据集点序对不上时返回 None。"""
    name, npz_path, radius, mesh_path = task
    import numpy as np
    from support_accessibility.data import mesh as MESH
    from support_accessibility.data.dataset import load_model
    from support_accessibility.data.fusion360 import load_obj, normalize
    from support_accessibility.runtime.frozen_params import FROZEN
    model = load_model(npz_path, name, radius)
    V, F = load_obj(mesh_path)
    Vn, _ = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=FROZEN.resolution)
    faces, points, _flipped = MESH.contact_queries(Vn, F, occ, lo, pitch)
    if len(faces) != len(model.points) or not np.allclose(points, model.points, atol=1e-2):
        return name, None
    return name, MESH.face_areas(Vn, F, faces)


def main():
    ap = argparse.ArgumentParser(description="支撑接触量（点数与真实面积）与可达性的 Spearman 相关")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root), help="Fusion 原始网格目录")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/contact_area_vs_accessibility/result.json")
    a = ap.parse_args()

    import json
    from concurrent.futures import ProcessPoolExecutor
    import numpy as np
    from support_accessibility import eval as E
    from support_accessibility.data.dataset import load_dataset, rel_npz_path
    from support_accessibility.data.fusion360 import iter_final_designs
    from support_accessibility.runtime.run_records import write_result

    parts = [m for m in load_dataset(a.fusion)[0] if m.points.shape[0] > 0]
    mesh_of = dict(iter_final_designs(a.root))
    tasks = [(m.name, os.path.join(a.fusion, rel_npz_path(m.name)), float(m.radius), mesh_of[m.name]) for m in parts]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        areas = dict(pool.map(_part_areas, tasks, chunksize=8))

    def correlations(size, frac):
        size, frac = np.asarray(size, float), np.asarray(frac, float)
        both = (frac > 0) & (frac < 1)
        return {"spearman_all": round(E.spearman(size, frac), 4), "n_all": int(size.size),
                "spearman_both_class": round(E.spearman(size[both], frac[both]), 4), "n_both_class": int(both.sum())}

    labels = {m.name: np.asarray(m.labels, bool) for m in parts}
    aligned = [m.name for m in parts if areas[m.name] is not None]
    rep = write_result("contact_area_vs_accessibility", {
        "data": logical_data_ref(a.fusion, paths), "n_parts": len(parts), "n_aligned": len(aligned),
        "contact_count": correlations([labels[n].size for n in labels], [labels[n].mean() for n in labels]),
        "true_area": correlations([areas[n].sum() for n in aligned],
                                  [areas[n][labels[n]].sum() / areas[n].sum() for n in aligned]),
    }, a.out, (a.fusion, a.root))
    print("CONTACT_AREA_VS_ACCESSIBILITY " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
