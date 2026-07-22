#!/usr/bin/env python3
"""物化程序化数据集 CLI（D-016）。纯 stdlib 顶层运行器：self-add src → dataset.build_procedural。

用法：
  conda run -n saf python tools/build_dataset.py --out data/processed/procedural_v1 --n-models 24 --seed 0
（`python -m` 需包已安装；本运行器 self-add src，免 editable 安装、跨平台，同 tests/gate.py 模式。）
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))          # tools/
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main():
    ap = argparse.ArgumentParser(description="物化程序化数据集（统一 processed 记录，D-016）")
    ap.add_argument("--out", default="data/processed/procedural_v1", help="输出目录")
    ap.add_argument("--n-models", type=int, default=16)
    ap.add_argument("--N", type=int, default=28)
    ap.add_argument("--max-points", type=int, default=24)
    ap.add_argument("--radius", type=float, default=3.0)
    ap.add_argument("--n-directions", type=int, default=32)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    a = ap.parse_args()

    from support_accessibility.data.dataset import build_procedural, load_dataset
    import numpy as np

    out = build_procedural(a.out, n_models=a.n_models, N=a.N, max_points=a.max_points,
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
