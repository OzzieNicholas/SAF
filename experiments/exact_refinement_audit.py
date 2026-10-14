#!/usr/bin/env python3
"""两级判定器相对全方向精确判定的偏差：第一级「明确可达」的方向，用精确胶囊复核是否其实碰撞。

两级判定器只对净空落在边界带内的方向做胶囊—网格精确求交；净空大于 r+ε 的方向由体素距离场直接判为可达。
本审计在固定留出集（80 件）上对这些直接放行的方向逐一做精确求交，统计被体素级误放行的方向、受影响的
查询点，以及若改用全方向精确判定会由可达翻为不可达的点（标签只会朝不可达一侧变化）。

用法：
  python experiments/exact_refinement_audit.py --workers 8
"""
import argparse
from concurrent.futures import ProcessPoolExecutor

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def audit_part(task):
    """一个零件：(体素直接放行的方向数, 其中精确判定碰撞的方向数, 受影响点数, 标签翻转点数, 是否有薄轴)。"""
    name, npz_path, radius, mesh_path = task
    import numpy as np
    from support_accessibility.data import mesh as MESH
    from support_accessibility.data.dataset import load_model
    from support_accessibility.data.fusion360 import load_obj, normalize
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.runtime.frozen_params import FROZEN

    model = load_model(npz_path, name, radius)
    V, F = load_obj(mesh_path)
    Vn, _ = normalize(V)
    _occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=FROZEN.resolution)
    oracle = SupportAccessibilityOracle(model.occ, {"n_directions": FROZEN.n_directions}, mesh=(Vn, F, lo, pitch))
    r = float(model.radius)
    freed = wrong = affected = flips = 0
    for p, inaccessible in zip(model.points, model.labels):
        p = np.asarray(p, float)
        refine = oracle._make_refine(p, r)
        clear = [oracle._min_clearance_along(p, v, r) for v in oracle.dirs]
        direct = [i for i, c in enumerate(clear) if c > r + oracle.eps]
        blocked = [i for i in direct if not refine(i)]
        freed += len(direct)
        wrong += len(blocked)
        if blocked and not inaccessible:
            affected += 1
            remaining = [i for i in direct if i not in blocked] + [
                i for i, c in enumerate(clear) if r - oracle.eps < c <= r + oracle.eps and refine(i)]
            flips += int(not remaining)
    thin = bool((0.2 * (Vn.max(0) - Vn.min(0)) < FROZEN.radius_world).any())
    return freed, wrong, affected, flips, thin


def main():
    paths = resolve_data_paths()
    ap = argparse.ArgumentParser(description="两级判定器相对全方向精确判定的偏差（固定留出集）")
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/exact_refinement_audit/result.json")
    a = ap.parse_args()

    import json
    import os
    from holdout_model import holdout_split      # 同目录脚本
    from support_accessibility.data.dataset import load_dataset, rel_npz_path
    from support_accessibility.data.fusion360 import iter_final_designs
    from support_accessibility.runtime.run_records import write_result

    _train, _val, test = holdout_split(load_dataset(a.fusion)[0])
    mesh_of = dict(iter_final_designs(a.root))
    tasks = [(m.name, os.path.join(a.fusion, rel_npz_path(m.name)), float(m.radius), mesh_of[m.name]) for m in test]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        rows = list(pool.map(audit_part, tasks))
    n_points = sum(m.points.shape[0] for m in test)
    n_accessible = sum(int((~m.labels.astype(bool)).sum()) for m in test)
    freed, wrong, affected, flips = (sum(r[i] for r in rows) for i in range(4))
    thin = [r for r in rows if r[4]]
    rep = write_result("exact_refinement_audit", {
        "scope": "fixed holdout test parts; directions with voxel clearance > r + epsilon re-checked by the exact capsule test",
        "n_parts": len(test), "n_points": n_points, "n_accessible_points": n_accessible,
        "n_parts_with_thin_axis": len(thin),
        "voxel_cleared_directions": freed, "exactly_blocked_among_them": wrong,
        "exactly_blocked_fraction": round(wrong / max(freed, 1), 4),
        "accessible_points_with_missed_block": affected,
        "point_labels_flipping_to_inaccessible": flips,
        "flip_fraction_of_points": round(flips / max(n_points, 1), 4),
        "flip_fraction_of_accessible_points": round(flips / max(n_accessible, 1), 4),
        "thin_axis_parts_flips": sum(r[3] for r in thin),
    }, a.out, (a.fusion, a.root))
    print("EXACT_REFINEMENT_AUDIT " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
