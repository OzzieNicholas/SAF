#!/usr/bin/env python3
"""物化程序化数据集 CLI（D-016）。

用法：
  python tools/build_procedural_dataset.py --dataset procedural --n-models 24 --seed 0
"""
import argparse
import os

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()


def main():
    ap = argparse.ArgumentParser(description="物化程序化数据集（统一 processed 记录，D-016）")
    ap.add_argument("--dataset", default="procedural")
    ap.add_argument("--out", default=None, help="输出目录；默认 <数据根>/processed/<dataset>")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--n-models", type=int, default=16)
    ap.add_argument("--N", type=int, default=28)
    ap.add_argument("--max-points", type=int, default=24)
    ap.add_argument("--radius", type=float, default=3.0)
    ap.add_argument(
        "--n-directions",
        type=int,
        default=FROZEN.n_directions,
        help="方向数；默认采用 configs/oracle_params.yaml / D-021 的冻结值 128",
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    a = ap.parse_args()

    from support_accessibility.data.dataset import build_procedural, load_dataset
    import numpy as np

    paths = resolve_data_paths(a.data_root)
    out = a.out or str(paths.processed_root(a.dataset))
    out = build_procedural(out, n_models=a.n_models, N=a.N, max_points=a.max_points,
                           radius=a.radius, n_directions=a.n_directions, seed=a.seed,
                           frac_train=a.frac_train, frac_val=a.frac_val)
    models, rows = load_dataset(out)
    lab = np.concatenate([m.labels for m in models]) if models else np.zeros(0, bool)
    counts = {s: sum(r["split"] == s for r in rows) for s in ("train", "val", "test")}
    both = bool(lab.any() and (~lab).any())
    print(f"物化 {len(models)} 件 → {out}")
    print(f"  切分 train{counts['train']}/val{counts['val']}/test{counts['test']}（按模型，无泄漏）")
    print(f"  不可达 {int(lab.sum())}/{lab.size}"
          f"（占比 {100 * lab.mean():.0f}%，两类俱在={both}）" if lab.size else "  （空）")
    print(f"  产物：{os.path.join(out, 'models')}/*.npz + {os.path.join(out, 'manifest.csv')} + {os.path.join(out, 'dataset.json')}")


if __name__ == "__main__":
    main()
