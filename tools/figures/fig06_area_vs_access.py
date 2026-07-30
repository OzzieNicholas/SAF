#!/usr/bin/env python3
"""图 6 支撑面积与可达性解耦（写作指引 §5.2 / 图6）：三联。

(a)(b) 旗舰对（同下朝面计数、可达性相反）3D 渲染——data.flagship_pair 构造。
(c) 全量零件"下朝面计数（支撑面积代理，对数）vs 不可达点占比"散点 + Spearman ρ——fusion360_full。
用法：conda run -n saf python tools/figures/fig06_area_vs_access.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from support_accessibility.data import flagship_pair
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    a, b = flagship_pair()                                   # a=open_ledge(可达)、b=deep_narrow_cavity(不可达)
    img_a = D.render_voxel_arr(a.occ, a.points, a.labels, cpos="iso", zoom=1.35)
    img_b = D.render_voxel_arr(b.occ, b.points, b.labels, cpos="iso", zoom=1.35)

    ms, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "fusion360_full"))
    area, inacc = D.per_model_area_inacc(ms)
    rho = E.spearman(area, inacc)

    fig = plt.figure(figsize=(9.6, 3.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.15], wspace=0.08)
    ax0 = fig.add_subplot(gs[0]); ax0.imshow(img_a); ax0.axis("off")
    ax0.set_title(f"(a) 悬空薄板\n下朝点 {a.points.shape[0]}·可达 {100*(1-a.labels.mean()):.0f}%", fontsize=9.5)
    ax1 = fig.add_subplot(gs[1]); ax1.imshow(img_b); ax1.axis("off")
    ax1.set_title(f"(b) 深窄腔\n下朝点 {b.points.shape[0]}·不可达 {100*b.labels.mean():.0f}%", fontsize=9.5)

    ax2 = fig.add_subplot(gs[2])
    ax2.scatter(area, inacc, s=5, alpha=0.18, color=S.ACC, edgecolors="none", rasterized=True)
    ax2.set_xscale("log")
    ax2.set_xlabel("下朝面计数（支撑面积代理，对数轴）")
    ax2.set_ylabel("不可达点占比")
    ax2.set_ylim(-0.03, 1.03)
    ax2.set_title(f"(c) 全量 {len(area)} 件：ρ={rho:.3f}（弱相关）", fontsize=9.5)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

    print("SAVED", S.save(fig, "fig06_area_vs_access"))


if __name__ == "__main__":
    main()
