#!/usr/bin/env python3
"""支撑面积与可达性：支撑面积（下朝面计数代理）能否预示可达性？跨零件群体算 Spearman ρ。
**代理口径注**：这里"支撑面积"= 每件下朝悬垂**面/接触点计数**，非真实三角面积——真实网格点为逐三角质心、未面积加权，
面积均匀采样未实现。可达性 = 每件不可达点占比（oracle 标签，冻结口径）。
|ρ| 越小→支撑面积越不预示可达性（该立论）。实测 |ρ|≤0.27=**弱相关**（弱预测因子，非严格独立）；
补 flagship_pair 存在性证据的**统计**半。

用法：python experiments/support_area_vs_accessibility.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import logical_data_ref, resolve_data_paths

setup_console()


def main():
    ap = argparse.ArgumentParser(description="支撑面积（接触点计数代理）与可达性的 Spearman 相关")
    ap.add_argument("--data", default=str(resolve_data_paths().processed_root("fusion360")))
    ap.add_argument("--max-models", type=int, default=None, help="截取前 N 件（None=全部）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/support_area_vs_accessibility/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()

    import json
    from support_accessibility.runtime.run_records import write_result
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
    rep = write_result("support_area_vs_accessibility", {
        "data": logical_data_ref(a.data), "n_models": int(area.size),
        "spearman_facecount_vs_inacc_frac_all": round(rho_all, 4),
        "n_both_class": int(both.sum()),
        "spearman_facecount_vs_inacc_frac_bothclass": round(rho_both, 4),
        "interpretation": "|ρ| 越小，支撑面积（下朝面计数代理，非真面积）越不预示可达性；|ρ| 不超过 0.27 为弱相关（弱预测因子，非严格独立）",
    }, a.out, (a.data,))
    print("SUPPORT_AREA_VS_ACCESSIBILITY " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
