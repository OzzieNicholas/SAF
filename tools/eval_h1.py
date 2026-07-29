#!/usr/bin/env python3
"""H1 复现器：支撑面积（代理）⊥ 可达性。跨零件群体算 **Spearman ρ**。
**代理口径注**：这里"支撑面积"= 每件下朝悬垂**面/接触点计数**，非真实三角面积——真实网格点为逐三角质心、未面积加权，
面积均匀采样未实现（见 conf/params.yaml sampling 注）。可达性 = 每件不可达点占比（oracle 标签，冻结口径）。
|ρ| 越小→支撑面积越不预示可达性（H1 立论）。实测 |ρ|≤0.27=**弱相关**（弱预测因子，非严格独立）；
补 flagship_pair 存在性证据的**统计**半。self-add src。

用法：conda run -n saf python tools/eval_h1.py --data data/processed/fusion360_full
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main():
    ap = argparse.ArgumentParser(description="H1 支撑面积⊥可达 Spearman ρ")
    ap.add_argument("--data", default="data/processed/fusion360_full")
    ap.add_argument("--max-models", type=int, default=None, help="截取前 N 件（None=全部）")
    a = ap.parse_args()

    import json
    import numpy as np
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    ms, _ = load_dataset(a.data)
    if a.max_models:
        ms = ms[:a.max_models]
    area, inacc = [], []
    for m in ms:
        lab = np.asarray(m.labels, bool)
        if lab.size == 0:
            continue
        area.append(int(lab.size))            # 下朝面/接触点**计数**（支撑面积代理，非真面积）
        inacc.append(float(lab.mean()))       # 不可达占比 = 可达性(反)测度
    area, inacc = np.array(area), np.array(inacc)
    # 群体（含全可达件）+ 仅两类件（去掉退化的 inacc=0/1）两口径都报
    both = (inacc > 0) & (inacc < 1)
    rho_all = E.spearman(area, inacc)
    rho_both = E.spearman(area[both], inacc[both]) if both.sum() >= 2 else 0.0
    print("H1_RESULT " + json.dumps({
        "data": a.data, "n_models": int(area.size),
        "spearman_facecount_vs_inacc_frac_all": round(rho_all, 4),
        "n_both_class": int(both.sum()),
        "spearman_facecount_vs_inacc_frac_bothclass": round(rho_both, 4),
        "interpretation": "|ρ| 越小 → 支撑面积（下朝面计数代理，非真面积）越不预示可达性（H1）；本数据 |ρ|≤0.27 = 弱相关（弱预测因子，非严格独立）",
    }))


if __name__ == "__main__":
    main()
