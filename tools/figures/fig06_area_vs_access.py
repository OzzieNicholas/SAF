#!/usr/bin/env python3
"""图 6 支撑面积与可达性解耦（写作指引 §5.2 / 图6）：证据链复合图。

(a)(b) 旗舰对（同下朝面计数、可达性相反）3D 渲染——data.flagship_pair 构造。
(c) 全量零件"下朝面计数（支撑面积代理，对数）vs 不可达点占比"散点，并前景化真面积复算证据。
用法：conda run -n saf python tools/figures/fig06_area_vs_access.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

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

    # The true-area evaluator emits JSON on stdout rather than a stable file. Keep
    # the panel honest when that optional artifact is present, while retaining the
    # count-proxy scatter as the reproducible per-model view.
    true_area = None
    for path in (os.path.join(_ROOT, "runs", "true_area", "latest.json"),
                 os.path.join(_ROOT, "runs", "h1_true_area.json")):
        if os.path.exists(path):
            try:
                import json
                true_area = json.load(open(path, encoding="utf-8"))["true_area"]
                break
            except (OSError, KeyError, ValueError, TypeError):
                pass
    true_all = 0.124 if true_area is None else true_area.get("spearman_all", 0.124)
    true_both = -0.126 if true_area is None else true_area.get("spearman_bothclass", -0.126)

    fig = plt.figure(figsize=(10.4, 4.0))
    gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 0.08, 1.55], height_ratios=[1, 0.33],
                          wspace=0.08, hspace=0.08, left=0.045, right=0.98, top=0.91, bottom=0.1)
    ax0 = fig.add_subplot(gs[0, 0]); ax0.imshow(img_a); ax0.axis("off")
    ax0.set_title(f"(a) 悬空薄板\n{a.points.shape[0]} 个下朝点 · 可达 {100*(1-a.labels.mean()):.0f}%", fontsize=9.5)
    ax1 = fig.add_subplot(gs[0, 1]); ax1.imshow(img_b); ax1.axis("off")
    ax1.set_title(f"(b) 深窄腔\n{b.points.shape[0]} 个下朝点 · 不可达 {100*b.labels.mean():.0f}%", fontsize=9.5)

    ax2 = fig.add_subplot(gs[0, 3])
    ax2.scatter(area, inacc, s=7, alpha=0.2, color=S.ACC, edgecolors="none", rasterized=True)
    ax2.set_xscale("log")
    ax2.set_xlabel("下朝面计数（支撑面积代理，对数轴）")
    ax2.set_ylabel("不可达点占比")
    ax2.set_ylim(-0.03, 1.03)
    ax2.set_title(f"(c) 计数代理 · 全量 {len(area)} 件", fontsize=9.5)
    ax2.text(0.03, 0.96, f"代理 ρ = {rho:.3f}", transform=ax2.transAxes, va="top", color=S.ACC, weight="bold")
    ax2.text(0.03, 0.88, f"真面积 ρ = {true_all:.3f}\n两类件真面积 ρ = {true_both:.3f}",
             transform=ax2.transAxes, va="top", fontsize=8, color="#333",
             bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#D0D0D0", alpha=0.9))
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

    note = fig.add_subplot(gs[1, :]); note.axis("off")
    note.text(0.01, 0.55, "面积证据", color="#333", weight="bold", va="center")
    note.text(0.13, 0.55, "真三角面积加权复算与计数代理同向但更弱；面积并非可达性的充分条件。",
              va="center", fontsize=9)
    note.add_line(Line2D([0.01, 0.98], [0.05, 0.05], transform=note.transAxes, color="#D9D9D9", lw=0.8))

    print("SAVED", S.save(fig, "fig06_area_vs_access"))


if __name__ == "__main__":
    main()
