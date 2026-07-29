#!/usr/bin/env python3
"""H2 复现器：工具尺寸不可忽略。算**射线可见但工具够不到**的点占比 = (r=0 可达/射线可见) ∧ (r>0 oracle 不可达)。
非零 ⟺ 有限工具半径改变可达性（把点级可见的位置判为够不到）。真实(Fusion) + 程序化两口径都报，n_dir 冻结 128。
`baselines.ray_visibility` 语义：True=射线全遮挡(r=0 不可达)；故"射线可见"= ~ray_vis。self-add src。
注：程序化 gold 标签建于 32 方向、本工具 rv 用 128——实测两口径对 H2 占比等价（~0.09% 点差），见 results.md。

用法：conda run -n saf python tools/eval_h2.py
"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


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
    ap = argparse.ArgumentParser(description="H2 工具尺寸不可忽略：射线可见但够不到占比")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--n-directions", type=int, default=128)   # D-021 冻结
    ap.add_argument("--max-models", type=int, default=600)     # 控时（真实件多）
    a = ap.parse_args()
    import json
    nf, ff, gf = _frac(a.fusion, a.n_directions, a.max_models)
    npc, fp, gp = _frac(a.procedural, a.n_directions, None)
    print("H2_RESULT " + json.dumps({
        "n_directions": a.n_directions,
        "fusion": {"pts": nf, "ray_visible_but_tool_blocked_frac": round(ff, 4), "oracle_inacc_frac": round(gf, 4)},
        "procedural": {"pts": npc, "ray_visible_but_tool_blocked_frac": round(fp, 4), "oracle_inacc_frac": round(gp, 4)},
        "interpretation": "非零占比 ⟺ 有限工具半径改变可达性（H2）",
    }))


if __name__ == "__main__":
    main()
