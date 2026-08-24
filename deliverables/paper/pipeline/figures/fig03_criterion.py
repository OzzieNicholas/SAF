#!/usr/bin/env python3
"""Figure 3. Clean section views for the finite-radius straight-approach criterion."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon  # noqa: E402


def _solid(ax, points):
    ax.add_patch(Polygon(points, closed=True, fc=S.PART, ec=S.PART_EDGE, lw=1.0, zorder=1))


def _ball(ax, centre, radius, colour, alpha=1.0):
    fill = S.PALE_BLUE if colour == S.ACC else "#F4DEDA"
    ax.add_patch(Circle(centre, radius, fc=fill, ec=colour, lw=1.2, alpha=alpha, zorder=4))


def _path(ax, start, end, colour, dashed=False):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10,
                                 lw=1.25, color=colour, zorder=5,
                                 linestyle=(0, (3, 2)) if dashed else "-"))


def _query(ax, point):
    ax.scatter(*point, s=28, c=S.INK, edgecolors="white", linewidths=.5, zorder=8)
    ax.annotate("$p$", point, xytext=(4, 5), textcoords="offset points", fontsize=8.5, color=S.INK)


def _finish(ax, title):
    ax.set_xlim(0, 7); ax.set_ylim(0, 5); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, loc="left", fontsize=8.6, fontweight="bold", pad=3)


def _open(ax):
    _solid(ax, [(0, 0), (1.2, 0), (1.2, 4.0), (0, 4.0)])
    _solid(ax, [(0, 3.35), (6.6, 3.35), (6.6, 4.0), (0, 4.0)])
    p, radius = np.array([4.35, 3.35]), .52
    _query(ax, p)
    centres = [p + np.array([.46, -.86]) * t for t in (.5, 1.35, 2.2, 3.0)]
    for index, centre in enumerate(centres):
        _ball(ax, centre, radius, S.ACC, alpha=.25 + index * .16)
    _path(ax, centres[-1], p + np.array([.05, -.08]), S.ACC)
    ax.annotate("$r$", centres[1], xytext=(-14, 3), textcoords="offset points", fontsize=7.5, color=S.ACC)
    ax.annotate(r"$\mathbf{v}$", centres[2], xytext=(8, -2), textcoords="offset points", fontsize=7.5, color=S.ACC)
    _finish(ax, "(a) 开阔下朝面")


def _blind(ax):
    _solid(ax, [(0, 0), (7, 0), (7, 4.4), (0, 4.4)])
    ax.add_patch(Polygon([(1.0, 0), (2.0, 0), (2.0, 2.6), (6.0, 2.6),
                          (6.0, 3.55), (1.0, 3.55)], closed=True,
                         fc="white", ec=S.PART_EDGE, lw=1.0, zorder=2))
    p = np.array([5.35, 3.55]); _query(ax, p)
    endpoints = ((5.35, 2.72), (2.12, .35), (6.72, 1.65))
    hits = ((5.35, 2.60), (2.02, 2.60), (6.02, 2.75))
    for endpoint, hit in zip(endpoints, hits):
        _path(ax, p, endpoint, S.INACC, dashed=True)
        ax.scatter(*hit, marker="x", s=42, c=S.INACC, lw=1.5, zorder=7)
    _ball(ax, (5.35, 2.98), .48, S.INACC, alpha=.85)
    _finish(ax, "(b) 盲腔 / 再入几何")


def _slot(ax):
    _solid(ax, [(0, 0), (7, 0), (7, 4.4), (0, 4.4)])
    cx, width = 3.5, .72
    ax.add_patch(Polygon([(cx - width / 2, 0), (cx + width / 2, 0),
                          (cx + width / 2, 3.15), (cx - width / 2, 3.15)],
                         closed=True, fc="white", ec=S.PART_EDGE, lw=1.0, zorder=2))
    p = np.array([cx, 3.15]); _query(ax, p)
    _path(ax, (cx, .15), (cx, 2.95), S.ACC, dashed=True)
    radius = .58; _ball(ax, (cx, .62), radius, S.INACC)
    ax.scatter([cx - width / 2, cx + width / 2], [.62, .62], marker="x",
               s=42, c=S.INACC, lw=1.5, zorder=7)
    ax.annotate("$w<2r$", (cx + width / 2, 1.25), xytext=(16, 2),
                textcoords="offset points", fontsize=7.5, color=S.INACC,
                arrowprops={"arrowstyle": "-", "color": S.INACC, "lw": .8})
    ax.annotate("$r=0$", (cx, 2.05), xytext=(7, 0), textcoords="offset points",
                fontsize=7.5, color=S.ACC)
    _finish(ax, "(c) 有限宽度窄缝")


def main():
    fig = plt.figure(figsize=S.double_column(70))
    grid = fig.add_gridspec(2, 3, height_ratios=(1, .17), left=.025, right=.99,
                            bottom=.07, top=.94, wspace=.09, hspace=.02)
    drawings = [fig.add_subplot(grid[0, i]) for i in range(3)]
    for function, axis in zip((_open, _blind, _slot), drawings):
        function(axis)
    formulas = (r"$\exists\,\mathbf{v}:\;\mathcal{C}(p,\mathbf{v},r)\cap P=\varnothing$",
                r"$\forall\,\mathbf{v}:\;\mathcal{C}(p,\mathbf{v},r)\cap P\ne\varnothing$",
                r"射线可见 $(r=0)$，有限半径工具不可达")
    colours = (S.ACC, S.INACC, S.INACC)
    for col, (formula, colour) in enumerate(zip(formulas, colours)):
        axis = fig.add_subplot(grid[1, col]); axis.axis("off")
        axis.plot([.02, .98], [.88, .88], color=colour, lw=1.15, transform=axis.transAxes)
        axis.text(.5, .42, formula, ha="center", va="center", fontsize=7.6,
                  color=colour, transform=axis.transAxes)
    print("SAVED", S.save(fig, "fig03_criterion"))


if __name__ == "__main__":
    main()
