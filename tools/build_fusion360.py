#!/usr/bin/env python3
"""物化 Fusion 360 Gallery reconstruction 网格数据集 CLI（D-017）。纯 stdlib 顶层运行器：
self-add src → fusion360.build_from_root（同 tools/build_dataset.py 模式，免 editable 安装、跨平台）。

用法：
  conda run -n saf python tools/build_fusion360.py --root E:/Work/Data/Fusion360Gallery/reconstruction
  （--root 空则使用 tools/data_paths.py 的外部数据根，支持 SAF_FUSION360_ROOT 覆盖）

只用最终零件 .obj（不碰构造序列/B-Rep）。数据未落地 → 清晰 FileNotFoundError（exit 2）。
**命门（D-018）**：物化后须人审 <out>/audit/*.png 再签收（翻 dataset.json human_signoff），方可用于训练。
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))          # tools/
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

try:
    from data_paths import resolve_data_paths
except ImportError:
    from tools.data_paths import resolve_data_paths

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main():
    ap = argparse.ArgumentParser(description="物化 Fusion360 reconstruction 网格数据集（统一 processed 记录，D-017）")
    ap.add_argument("--root", default="", help="reconstruction 目录；空则使用外部数据根布局")
    ap.add_argument("--out", default=None, help="输出目录；默认外部 Temporary/SAF/fusion360_full/<run>")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--temporary-root", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--resolution", type=int, default=48)
    ap.add_argument("--radius-world", type=float, default=0.05)
    ap.add_argument("--n-directions", type=int, default=128)  # D-021 冻结值（收敛证据见 D-020；细化默认开，见 _label_one）
    ap.add_argument("--overhang-deg", type=float, default=45.0)
    ap.add_argument("--max-models", type=int, default=None)
    ap.add_argument("--frac-train", type=float, default=0.6)
    ap.add_argument("--frac-val", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    paths = resolve_data_paths(a.data_root, a.temporary_root, a.run_id)
    root = a.root or str(paths.fusion360_root)
    out_dir = a.out or str(paths.processed_root("fusion360_full", a.run_id))
    from support_accessibility.data.fusion360 import build_from_root
    try:                                                    # root 缺失在 numpy 之前就报（裸环境也友好）
        out = build_from_root(out_dir, root, resolution=a.resolution, radius_world=a.radius_world,
                              n_directions=a.n_directions, overhang_deg=a.overhang_deg,
                              max_models=a.max_models, frac_train=a.frac_train,
                              frac_val=a.frac_val, seed=a.seed)
    except FileNotFoundError as e:
        sys.stderr.write(
            f"数据未就绪：{e}\n"
            "  → 下好数据后传 --root，或设置 SAF_DATA_ROOT/SAF_FUSION360_ROOT\n"
        )
        sys.exit(2)

    from support_accessibility.data.dataset import load_dataset
    import numpy as np
    models, rows = load_dataset(out)
    lab = np.concatenate([m.labels for m in models]) if models else np.zeros(0, bool)
    counts = {s: sum(r["split"] == s for r in rows) for s in ("train", "val", "test")}
    both = bool(lab.any() and (~lab).any())
    print(f"物化 {len(models)} 件 → {out}")
    print(f"  切分 train{counts['train']}/val{counts['val']}/test{counts['test']}（按模型，无泄漏）")
    if lab.size:
        print(f"  不可达 {int(lab.sum())}/{lab.size}（占比 {100 * lab.mean():.0f}%，两类俱在={both}）")
    print(f"  审计图：{os.path.join(out, 'audit')}/*.png —— 命门：人审后签收（dataset.json human_signoff），见 D-018")
    print(f"  产物：{os.path.join(out, 'models')}/*.npz + manifest.csv + dataset.json")


if __name__ == "__main__":
    main()
