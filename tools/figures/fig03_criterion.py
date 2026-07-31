#!/usr/bin/env python3
"""图 3 球工具直线逼近的几何可达性判据。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402


SOLID = "#D4D7DA"
EDGE = "#687177"
INK = "#263238"
ACC_FILL = "#DCEAF5"
INACC_FILL = "#F3DDD9"


def _solid(ax, points):
    ax.add_patch(Polygon(points, closed=True, fc=SOLID, ec=EDGE, lw=1.0, zorder=1))


def _cut(ax, points):
    ax.add_patch(Polygon(points, closed=True, fc="white", ec=EDGE, lw=1.0, zorder=2))


def _point(ax, p, offset=(0.14, 0.14)):
    ax.scatter(*p, s=32, color=INK, edgecolors="white", linewidths=0.5, zorder=8)
    ax.text(p[0] + offset[0], p[1] + offset[1], "$p$", fontsize=10.5, color=INK, zorder=9)


def _arrow(ax, start, end, color, ls="-", lw=1.35, alpha=1.0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, color=color,
                                 lw=lw, linestyle=ls, alpha=alpha, zorder=6))


def _ball(ax, center, r, color, fill, alpha=0.82):
    ax.add_patch(Circle(center, r, fc=fill, ec=color, lw=1.25, alpha=alpha, zorder=5))
    ax.scatter(*center, s=8, color=color, zorder=6)


def _hit(ax, p):
    ax.scatter(*p, marker="x", s=58, color=S.INACC, linewidths=1.8, zorder=8)


def _badge(ax, text, color):
    ax.text(0.04, 0.94, text, transform=ax.transAxes, fontsize=7.5, weight="bold", color=color,
            ha="left", va="top")


def panel_open(ax):
    _solid(ax, [(0, 0), (1.25, 0), (1.25, 4.4), (0, 4.4)])
    _solid(ax, [(0, 3.65), (6.5, 3.65), (6.5, 4.4), (0, 4.4)])
    p = (4.4, 3.65)
    r = 0.55
    centers = [(p[0] + 1.2, p[1] - 2.8), (p[0] + 0.78, p[1] - 1.88), (p[0] + 0.36, p[1] - 0.95)]
    for c, alpha in zip(centers, (0.22, 0.38, 0.62)):
        _ball(ax, c, r, S.ACC, ACC_FILL, alpha)
    _arrow(ax, (5.9, 0.25), (p[0] + 0.08, p[1] - 0.18), S.ACC, lw=1.7)
    _ball(ax, (p[0], p[1] - r), r, S.ACC, ACC_FILL, 0.95)
    _point(ax, p)
    ax.text(4.95, 1.42, r"存在 $\mathbf{v}$", fontsize=8.5, color=S.ACC, rotation=27)
    ax.text(4.40, 2.55, "$r$", fontsize=8, color=S.ACC, ha="center")
    _badge(ax, "EXISTS", S.ACC)
    ax.set_title("(a) 开阔下朝面", loc="left", fontsize=10, weight="bold", color=INK)
    ax.text(0.03, 0.035, r"$\exists\,\mathbf{v}$：扫掠球不碰撞", transform=ax.transAxes,
            fontsize=8.2, color=S.ACC, weight="bold")


def panel_blind(ax):
    _solid(ax, [(0, 0), (7.2, 0), (7.2, 5.0), (0, 5.0)])
    _cut(ax, [(0.85, 0), (2.15, 0), (2.15, 2.75), (6.18, 2.75), (6.18, 3.85), (0.85, 3.85)])
    p = (5.55, 3.85)
    _point(ax, p, (0.08, 0.17))
    paths = [((5.55, 3.85), (5.55, 2.84), (5.55, 2.75)),
             ((5.55, 3.85), (2.55, 0.20), (2.18, 2.75)),
             ((5.55, 3.85), (6.78, 2.00), (6.18, 2.92))]
    for start, end, hit in paths:
        _arrow(ax, start, end, S.INACC, ls=(0, (3, 2)), lw=1.2)
        _hit(ax, hit)
    _ball(ax, (5.55, 3.15), 0.45, S.INACC, INACC_FILL, 0.72)
    ax.text(3.0, 1.0, "所有采样逼近方向\n均与零件相交", fontsize=8.3, color=S.INACC, ha="center")
    _badge(ax, "FOR ALL", S.INACC)
    ax.set_title("(b) 盲腔 / 再入几何", loc="left", fontsize=10, weight="bold", color=INK)
    ax.text(0.03, 0.035, r"$\forall\,\mathbf{v}$：扫掠球发生碰撞", transform=ax.transAxes,
            fontsize=8.2, color=S.INACC, weight="bold")


def panel_slot(ax):
    w, cx = 0.78, 3.6
    _solid(ax, [(0, 0), (7.2, 0), (7.2, 5.0), (0, 5.0)])
    _cut(ax, [(cx - w / 2, 0), (cx + w / 2, 0), (cx + w / 2, 3.45), (cx - w / 2, 3.45)])
    p = (cx, 3.45)
    _point(ax, p, (0.18, 0.10))
    _arrow(ax, (cx, -0.20), (cx, 3.22), S.ACC, ls=(0, (2, 2)), lw=1.3)
    ax.text(cx + 0.20, 2.15, "$r=0$ 射线", fontsize=8.2, color=S.ACC, rotation=90, va="center")
    r = 0.62
    _ball(ax, (cx, r - 0.02), r, S.INACC, INACC_FILL, 0.92)
    _hit(ax, (cx - w / 2, 0.56))
    _hit(ax, (cx + w / 2, 0.56))
    ax.annotate("缝宽 < 2r", xy=(cx - w / 2, 1.38), xytext=(cx + 1.0, 1.50),
                fontsize=8.3, color=S.INACC,
                arrowprops=dict(arrowstyle="-[,widthB=2.0", color=S.INACC, lw=1.0))
    _badge(ax, "FINITE SIZE", S.INACC)
    ax.set_title("(c) 窄缝", loc="left", fontsize=10, weight="bold", color=INK)
    ax.text(0.03, 0.035, "射线可见，但有限半径工具不可达", transform=ax.transAxes,
            fontsize=8.2, color=S.INACC, weight="bold")


def main():
    fig, axes = plt.subplots(1, 3, figsize=S.double_column(68), gridspec_kw={"wspace": 0.06})
    for fn, ax in zip((panel_open, panel_blind, panel_slot), axes):
        fn(ax)
        ax.set_xlim(-0.35, 7.45)
        ax.set_ylim(-0.45, 5.35)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.text(.025, .975, r"存在无碰撞直线逼近方向 $\Longleftrightarrow$ 可达", ha="left", va="top",
             fontsize=8.4, color=INK, fontweight="bold")
    fig.subplots_adjust(left=.02, right=.99, bottom=.04, top=.90)
    print("SAVED", S.save(fig, "fig03_criterion"))


if __name__ == "__main__":
    main()
