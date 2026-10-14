#!/usr/bin/env python3
"""工具尺寸的影响：不可达接触点中，有多少对零半径射线是可见的。

零半径射线可见性是有限工具判据在 r = 0 时的特例。若一个点不可达（有限半径工具在所有方向上都被挡），
却存在一条无遮挡的射线，那么它的遮挡来自工具的有限尺寸而不是视线被挡。分别在全部 Fusion 零件与
程序化零件上统计这类点在全部点与不可达点中的占比。射线可见性使用与标签相同的方向集。

用法：
  python experiments/tool_radius_effect.py --workers 16
"""
import argparse
import os

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def _ray_blocked(task):
    """工作进程：一个零件的零半径射线判定（True 为没有任何方向的射线能逃逸）。"""
    name, npz_path, radius = task
    from support_accessibility import baselines as B
    from support_accessibility.data.dataset import load_model
    model = load_model(npz_path, name, radius)
    return B.ray_visibility(model.occ, model.points)


def _summary(root, workers):
    import numpy as np
    from concurrent.futures import ProcessPoolExecutor
    from support_accessibility.data.dataset import load_dataset, rel_npz_path
    parts = [m for m in load_dataset(root)[0] if m.points.shape[0] > 0]
    tasks = [(m.name, os.path.join(root, rel_npz_path(m.name)), float(m.radius)) for m in parts]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        ray_blocked = np.concatenate(list(pool.map(_ray_blocked, tasks, chunksize=8)))
    gold = np.concatenate([np.asarray(m.labels, bool) for m in parts])
    visible_but_blocked = ~ray_blocked & gold
    return {"parts": len(parts), "points": int(gold.size), "inaccessible_frac": round(float(gold.mean()), 4),
            "ray_visible_inaccessible_frac_of_points": round(float(visible_but_blocked.mean()), 4),
            "ray_visible_share_of_inaccessible": round(float(visible_but_blocked.sum() / gold.sum()), 4)}


def main():
    ap = argparse.ArgumentParser(description="不可达接触点中零半径射线可见的比例")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/tool_radius_effect/result.json")
    a = ap.parse_args()

    import json
    from support_accessibility.runtime.run_records import write_result
    rep = write_result("tool_radius_effect", {
        "fusion": _summary(a.fusion, a.workers),
        "procedural": _summary(a.procedural, a.workers),
    }, a.out, (a.fusion, a.procedural))
    print("TOOL_RADIUS_EFFECT " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
