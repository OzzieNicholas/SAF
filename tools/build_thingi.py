#!/usr/bin/env python3
"""物化 Thingi10K 跨域测试子集 CLI（H5；D-022）。纯 stdlib 顶层运行器：
self-add src → thingi.build_thingi（同 tools/build_fusion360.py 模式，免 editable 安装、跨平台）。

用法：
  conda run -n saf python tools/build_thingi.py --root E:/Thingi10K/raw_meshes --out data/processed/thingi_v1
  （壳内激活亦可：source .../conda.sh && conda activate saf && python tools/build_thingi.py ...）

Thingi = **跨域鲁棒性测试源**（H5），**恒 split=test、绝不进训练**（D-016/docs §4.6）。野网格：缠绕不一致/
非流形/退化三角——占据用 igl winding、下朝面用 STL stored 法向、胶囊细化跳过退化面（D-022）。采样上限
（--max-points/--max-faces）控密扫描件成本（D-022，非 oracle 口径；Thingi 恒 test 故不触 D-021 冻结）。
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))          # tools/
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main():
    ap = argparse.ArgumentParser(description="Thingi10K 跨域测试子集物化（H5，D-022）")
    ap.add_argument("--root", default="", help="Thingi raw_meshes 目录（含 .stl/.obj）")
    ap.add_argument("--out", default="data/processed/thingi_v1")
    ap.add_argument("--max-models", type=int, default=300)
    ap.add_argument("--max-points", type=int, default=400, help="每模型接触点上限（密扫描件封顶，确定性无放回）")
    ap.add_argument("--max-faces", type=int, default=80000, help="面数上限（超高面 res 下已降采样、跳过控剪枝成本）")
    ap.add_argument("--resolution", type=int, default=48)
    ap.add_argument("--radius-world", type=float, default=0.05)
    ap.add_argument("--n-directions", type=int, default=128)   # D-021 冻结值
    ap.add_argument("--overhang-deg", type=float, default=45.0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if not a.root or not os.path.isdir(a.root):
        sys.stderr.write(f"Thingi root 无效：{a.root!r}\n  → 传 --root 指向 Thingi10K raw_meshes 目录\n")
        sys.exit(2)

    from support_accessibility.data.thingi import build_thingi
    out = build_thingi(a.root, a.out, max_models=a.max_models, resolution=a.resolution,
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
