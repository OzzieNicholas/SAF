#!/usr/bin/env python3
"""工具尺寸不可忽略：算**射线可见但工具够不到**的点占比 = (r=0 可达/射线可见) ∧ (r>0 oracle 不可达)。
非零 ⟺ 有限工具半径改变可达性（把点级可见的位置判为够不到）。真实(Fusion) + 程序化两口径都报，n_dir 冻结 128。
`baselines.ray_visibility` 语义：True=射线全遮挡(r=0 不可达)；故"射线可见"= ~ray_vis。
注：程序化与真实数据 gold 标签均采用冻结的 128 方向；本工具的射线可见性对照也使用 128 方向。

用法：python experiments/tool_radius_effect.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()


def _frac(data, ndir, max_models):
    import numpy as np
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import baselines as B
    ms, _ = load_dataset(data)
    if max_models:
        ms = ms[:max_models]
    rv, gold = [], []
    for m in ms:
        if m.points.shape[0] == 0:
            continue
        rv.append(B.ray_visibility(m.occ, m.points, ndir))     # True=射线全遮挡(r=0 不可达)
        gold.append(np.asarray(m.labels, bool))                # True=oracle 不可达(r=0.05)
    rv, gold = np.concatenate(rv), np.concatenate(gold)
    visible_but_blocked = (~rv) & gold                         # 射线可见(r=0 可达) 但 工具够不到
    return int(gold.size), float(visible_but_blocked.mean()), float(gold.mean())


def main():
    ap = argparse.ArgumentParser(description="有限工具半径是否改变可达性：射线可见但工具够不到的点占比")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--n-directions", type=int, default=FROZEN.n_directions)   # D-021 冻结
    ap.add_argument("--max-models", type=int, default=600)     # 控时（真实件多）
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/tool_radius_effect/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()
    import json
    from support_accessibility.runtime.run_records import write_result
    nf, ff, gf = _frac(a.fusion, a.n_directions, a.max_models)
    npc, fp, gp = _frac(a.procedural, a.n_directions, None)
    rep = write_result("tool_radius_effect", {
        "n_directions": a.n_directions,
        "fusion": {"pts": nf, "ray_visible_but_tool_blocked_frac": round(ff, 4), "oracle_inacc_frac": round(gf, 4)},
        "procedural": {"pts": npc, "ray_visible_but_tool_blocked_frac": round(fp, 4), "oracle_inacc_frac": round(gp, 4)},
        "interpretation": "非零占比说明有限工具半径改变可达性",
    }, a.out, (a.fusion, a.procedural))
    print("TOOL_RADIUS_EFFECT " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
