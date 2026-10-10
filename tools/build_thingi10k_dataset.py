#!/usr/bin/env python3
"""物化 Thingi10K 跨域测试子集 CLI（跨域鲁棒性；D-022）。

用法：
  python tools/build_thingi10k_dataset.py [--max-models N]
  原始网格目录与输出目录默认取自 configs/paths.yaml（--root / --out 可覆盖）。

Thingi = **跨域鲁棒性测试源**（跨域鲁棒性），**恒 split=test、绝不进训练**（D-016/研究背景与设计 §6.2）。野网格：缠绕不一致/
非流形/退化三角——占据用 igl winding、下朝面用 STL stored 法向、胶囊细化跳过退化面（D-022）。采样上限
（--max-points/--max-faces）控密扫描件成本（D-022，非 oracle 口径；Thingi 恒 test 故不触 D-021 冻结）。
"""
import argparse
import os
import sys

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()


def main():
    ap = argparse.ArgumentParser(description="Thingi10K 跨域测试子集物化（跨域鲁棒性，D-022）")
    ap.add_argument("--root", default="", help="Thingi raw_meshes 目录；空则取 configs/paths.yaml 的布局")
    ap.add_argument("--out", default=None, help="输出目录；默认 <数据根>/processed/thingi10k")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--max-models", type=int, default=300)
    ap.add_argument("--max-points", type=int, default=400, help="每模型接触点上限（密扫描件封顶，确定性无放回）")
    ap.add_argument("--max-faces", type=int, default=80000, help="面数上限（超高面 res 下已降采样、跳过控剪枝成本）")
    ap.add_argument("--resolution", type=int, default=FROZEN.resolution)
    ap.add_argument("--radius-world", type=float, default=FROZEN.radius_world)
    ap.add_argument("--n-directions", type=int, default=FROZEN.n_directions)   # D-021 冻结值
    ap.add_argument("--overhang-deg", type=float, default=FROZEN.overhang_deg)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    paths = resolve_data_paths(a.data_root)
    root = a.root or str(paths.thingi_root)
    out_dir = a.out or str(paths.processed_root("thingi10k"))
    if not root or not os.path.isdir(root):
        sys.stderr.write(f"Thingi root 无效：{root!r}\n  → 传 --root 或按 configs/paths.yaml 的说明配置数据根\n")
        sys.exit(2)

    from support_accessibility.data.thingi import build_thingi
    out = build_thingi(root, out_dir, max_models=a.max_models, resolution=a.resolution,
                       radius_world=a.radius_world, overhang_deg=a.overhang_deg,
                       n_directions=a.n_directions, max_points=a.max_points,
                       max_faces=a.max_faces, seed=a.seed)

    from support_accessibility.data.dataset import load_dataset
    import numpy as np
    models, rows = load_dataset(out)
    both = sum(1 for m in models if np.asarray(m.labels).size
               and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any())
    lab = np.concatenate([m.labels for m in models]) if models else np.zeros(0, bool)
    print(f"物化 {len(models)} 件 → {out}（source=thingi10k，split 恒 test）")
    print(f"  两类俱在 {both} 件；不可达点占比 {100 * lab.mean():.1f}%" if lab.size else "  （无标签点）")
    print(f"  产物：{os.path.join(out, 'models')}/*.npz + manifest.csv + dataset.json")
    print("  注：Thingi 恒 test、绝不进训练；非水密件 winding 不稳→标签含噪（跨域挑战本身，非 bug）")


if __name__ == "__main__":
    main()
