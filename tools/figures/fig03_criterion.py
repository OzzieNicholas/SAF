#!/usr/bin/env python3
"""图 3 可达性判据示意（写作指引 §3.2 / 图3）：2D 剖面三联。

(a) 开阔下朝面——工具球沿某方向直线可达；
(b) 盲腔（再入腔）——任意方向直线均碰撞 → 不可达；
(c) 窄缝——同一点 r=0 射线可见、半径 r 球进不去 → 工具尺寸效应（呼应 5.2）。
球、射线、碰撞点显式画出。纯示意（matplotlib 矢量 PDF）。用法：conda run -n saf python tools/figures/fig03_criterion.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon, FancyArrowPatch  # noqa: E402

SOLID = "#C9CDD4"
SOLID_E = "#8A8A8A"


def _solid(ax, pts):
    ax.add_patch(Polygon(pts, closed=True, fc=SOLID, ec=SOLID_E, lw=1.2, zorder=1))


def _cut(ax, pts):
    """白色挖去（腔/缝）——盖在实体上模拟布尔差。"""
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec=SOLID_E, lw=1.2, zorder=2))


def _pt(ax, xy, lab="p", dx=0.18, dy=-0.16):
    ax.scatter([xy[0]], [xy[1]], s=42, color="black", zorder=6)
    ax.text(xy[0] + dx, xy[1] + dy, lab, fontsize=11, zorder=6, style="italic")


def _ray(ax, xy0, xy1, color, style="--", lw=1.5):
    ax.add_patch(FancyArrowPatch(xy0, xy1, arrowstyle="-|>", mutation_scale=12,
                                 lw=lw, color=color, linestyle=style, zorder=5))


def _hit(ax, xy):
    ax.scatter([xy[0]], [xy[1]], marker="x", s=80, color=S.INACC, lw=2.4, zorder=7)


def _ball(ax, c, r, ec, fc):
    ax.add_patch(Circle(c, r, fc=fc, ec=ec, lw=1.6, alpha=0.85, zorder=4))
    ax.scatter([c[0]], [c[1]], s=10, color=ec, zorder=5)


def panel_a(ax):
    """开阔下朝面：立柱 + 顶板悬臂，下方开阔；球自下逼近可达。"""
    _solid(ax, [(0, 0), (1.4, 0), (1.4, 4.4), (0, 4.4)])           # 立柱
    _solid(ax, [(0, 3.6), (6.4, 3.6), (6.4, 4.4), (0, 4.4)])       # 顶板
    p = (4.3, 3.6)
    r = 0.62
    _ray(ax, (5.7, 0.3), (p[0] + 0.34, p[1] - 0.95 + r), S.ACC, lw=1.7)  # 逼近方向 v
    _ball(ax, (p[0], p[1] - r), r, S.ACC, "#CFE0F0")
    _pt(ax, p, "p", dx=0.14, dy=0.16)
    ax.annotate("逼近方向 v", (5.2, 1.15), fontsize=9.5, color=S.ACC, rotation=32)
    ax.annotate("工具球 (半径 r)", (p[0] - 0.2, p[1] - 2 * r - 0.42), fontsize=9, ha="center")
    ax.set_title("(a) 开阔下朝面：存在方向 v 直线可达 → 可达", fontsize=10, color=S.ACC)
    ax.set_xlim(-0.5, 7.2); ax.set_ylim(-0.4, 5.4)


def panel_b(ax):
    """盲腔（L 形再入腔）：p 在水平腔右端下朝顶，任意直线均穿实体。"""
    _solid(ax, [(0, 0), (7.2, 0), (7.2, 5.4), (0, 5.4)])
    _cut(ax, [(1.0, 0), (2.4, 0), (2.4, 3.0), (6.2, 3.0), (6.2, 4.1), (1.0, 4.1)])  # L 腔（竖臂+横臂）
    p = (5.6, 4.1)
    _pt(ax, p, "p", dx=0.02, dy=0.22)
    for tgt, hit in [((5.6, 3.0), (5.6, 3.0)), ((3.2, 0.0), (2.75, 2.55)), ((6.6, 2.2), (6.2, 3.35))]:
        _ray(ax, p, tgt, "#B0562A", style=(0, (4, 2)), lw=1.4)
        _hit(ax, hit)
    ax.annotate("各方向均碰撞 ×", (3.0, 1.15), fontsize=9.5, color=S.INACC)
    ax.set_title("(b) 盲腔：任意方向直线均碰撞 → 不可达", fontsize=10, color=S.INACC)
    ax.set_xlim(-0.5, 7.7); ax.set_ylim(-0.4, 5.9)


def panel_c(ax):
    """窄缝：自底开的窄槽（宽<2r），p 在槽顶下朝面。r=0 射线可见，半径 r 球卡在缝口。"""
    w = 0.62
    _solid(ax, [(0, 0), (7.2, 0), (7.2, 5.4), (0, 5.4)])
    _cut(ax, [(3.6 - w / 2, 0), (3.6 + w / 2, 0), (3.6 + w / 2, 3.4), (3.6 - w / 2, 3.4)])  # 窄槽
    p = (3.6, 3.4)
    _pt(ax, p, "p", dx=0.22, dy=0.06)
    _ray(ax, (3.6, -0.3), (3.6, 3.15), S.ACC, style=(0, (2, 2)), lw=1.4)   # r=0 射线
    ax.annotate("r=0 射线可见", (3.85, 1.0), fontsize=9, color=S.ACC)
    r = 0.62
    _ball(ax, (3.6, -0.05 + r), r, S.INACC, "#F3D6D0")                     # 球卡缝口
    _hit(ax, (3.6 - w / 2, 0.6)); _hit(ax, (3.6 + w / 2, 0.6))
    ax.annotate("半径 r 球卡在缝口\n（缝宽 < 2r）", (3.6, -0.15 + 2 * r + 0.3), fontsize=9,
                ha="center", color=S.INACC)
    ax.set_title("(c) 窄缝：射线可见但工具进不去 → 工具尺寸效应", fontsize=10, color=S.INACC)
    ax.set_xlim(-0.5, 7.7); ax.set_ylim(-0.5, 5.9)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.9))
    panel_a(axes[0]); panel_b(axes[1]); panel_c(axes[2])
    for ax in axes:
        ax.set_aspect("equal"); ax.axis("off")
    print("SAVED", S.save(fig, "fig03_criterion"))


if __name__ == "__main__":
    main()
