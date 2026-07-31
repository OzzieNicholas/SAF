#!/usr/bin/env python3
"""图 4 距离场筛选与边界带精确胶囊细化的两级判定器。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402


INK = "#263238"
SOLID = "#AEB4B8"
EDGE = "#515A60"


def _capsule(ax, a, b, r, fc=S.ORANGE, ec="#A9562D", alpha=0.34):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    n = np.array([-u[1], u[0]]) * r
    ax.add_patch(Polygon([a + n, b + n, b - n, a - n], closed=True, fc=fc, ec="none",
                         alpha=alpha, zorder=4))
    ax.add_patch(Circle(a, r, fc=fc, ec="none", alpha=alpha, zorder=4))
    ax.add_patch(Circle(b, r, fc=fc, ec="none", alpha=alpha, zorder=4))
    ax.plot([a[0], b[0]], [a[1], b[1]], color=ec, lw=1.2, zorder=5)


def _field_panel(ax, fig):
    from scipy.ndimage import distance_transform_edt

    nx, ny = 240, 180
    ext = (0.0, 8.0, 0.0, 6.0)
    pitch = 8.0 / nx
    xs = (np.arange(nx) + 0.5) * pitch
    ys = (np.arange(ny) + 0.5) * pitch
    X, Y = np.meshgrid(xs, ys)
    solid = ((X <= 1.35) & (Y <= 4.45)) | ((X <= 6.45) & (Y >= 3.62) & (Y <= 4.45))
    dist = distance_transform_edt(~solid) * pitch
    im = ax.imshow(np.where(~solid, dist, np.nan), origin="lower", extent=ext, cmap="Blues",
                   vmin=0, vmax=2.4, zorder=1)
    ax.imshow(np.where(solid, 1.0, np.nan), origin="lower", extent=ext,
              cmap=plt.matplotlib.colors.ListedColormap([SOLID]), zorder=2)
    levels = ax.contour(X, Y, np.where(~solid, dist, np.nan), levels=[0.55, 1.10, 1.65],
                        colors="white", linewidths=0.55, alpha=0.75, zorder=3)
    ax.clabel(levels, fmt="%.2f", fontsize=7.5, inline=True)

    p = np.array([4.35, 3.62])
    v = np.array([0.10, -1.0]); v /= np.linalg.norm(v)
    r = 0.55
    centers = [p + v * (r + i * 0.63) for i in range(5)]
    ax.add_patch(FancyArrowPatch(p, p + v * 3.45, arrowstyle="-|>", mutation_scale=11,
                                 color=S.ACC, lw=1.5, ls=(0, (4, 2)), zorder=7))
    for i, c in enumerate(centers):
        ax.scatter(*c, s=14, fc="white", ec=S.ACC, lw=0.8, zorder=8)
        if i == 1:
            ax.add_patch(Circle(c, r, fc="none", ec=S.ACC, lw=1.25, zorder=8))
    ax.scatter(*p, s=35, color=INK, edgecolors="white", linewidths=0.5, zorder=9)
    ax.text(p[0] + 0.13, p[1] + 0.12, "$p$", fontsize=10, zorder=9)
    ax.text(0.28, 0.42, r"明确可达： $\min_t\;\mathrm{free\_dist}(p+t\mathbf{v}) > r+\varepsilon$",
            fontsize=7.6, color=S.ACC)
    ax.set_title("(a) 第一级 · 距离场快速筛选", loc="left", fontsize=10.5, weight="bold", color=INK)
    ax.set_xlim(0, 8); ax.set_ylim(0, 6); ax.set_aspect("equal"); ax.axis("off")
    cax = ax.inset_axes([0.08, 0.91, 0.38, 0.027])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_ticks([0, 1.2, 2.4]); cb.ax.tick_params(labelsize=7.5, length=2, pad=1)
    cb.outline.set_visible(False)
    ax.text(0.08, 0.955, "自由空间欧氏距离", transform=ax.transAxes, fontsize=7.5, color=INK)


def _refine_panel(ax):
    for x in np.arange(0, 8.1, 0.5):
        ax.plot([x, x], [0, 6], color="#EAEBEC", lw=0.42, zorder=0)
    for y in np.arange(0, 6.1, 0.5):
        ax.plot([0, 8], [y, y], color="#EAEBEC", lw=0.42, zorder=0)

    surf = np.array([(0.45, 4.65), (2.30, 3.55), (3.45, 3.10), (5.35, 3.52), (7.55, 2.12)])
    ax.add_patch(Polygon(np.vstack([surf, (7.55, 0.15), (0.45, 0.15)]), closed=True,
                         fc="#D1D4D6", ec=EDGE, lw=1.0, zorder=2))
    ax.plot(surf[:, 0], surf[:, 1], color=EDGE, lw=1.5, zorder=3)
    ax.scatter(surf[:, 0], surf[:, 1], s=14, color=EDGE, zorder=4)
    for i in range(1, len(surf) - 1):
        ax.plot([surf[i, 0], 4.6], [surf[i, 1], 0.18], color="#A4A9AC", lw=0.55, zorder=3)

    p = np.array([3.45, 3.10])
    v = np.array([0.56, 1.0]); v /= np.linalg.norm(v)
    a, b, r = p + 0.10 * v, p + 2.55 * v, 0.56
    _capsule(ax, a, b, r)
    ax.add_patch(FancyArrowPatch(p, b + v * 0.25, arrowstyle="-|>", mutation_scale=10,
                                 color="#A9562D", lw=1.2, zorder=6))
    ax.scatter(*p, s=35, color=INK, edgecolors="white", linewidths=0.5, zorder=8)
    ax.text(p[0] - 0.28, p[1] + 0.08, "$p$", fontsize=10, zorder=8)

    q = np.array([5.35, 3.52])
    foot = np.array([4.55, 4.10])
    ax.plot([q[0], foot[0]], [q[1], foot[1]], color=S.INACC, lw=1.55, zorder=8)
    ax.scatter(*q, s=34, color=S.INACC, edgecolors="white", linewidths=0.5, zorder=9)
    ax.annotate("精确最近距离", xy=((q[0] + foot[0]) / 2, (q[1] + foot[1]) / 2),
                xytext=(5.45, 4.55), fontsize=7.8, color=S.INACC,
                arrowprops=dict(arrowstyle="->", color=S.INACC, lw=0.8))
    ax.text(0.28, 0.42, r"含糊方向： $r-\varepsilon < c_i \leq r+\varepsilon$  →  胶囊–三角网格求交",
            fontsize=7.6, color="#A9562D")
    ax.set_title("(b) 第二级 · 边界带精确细化", loc="left", fontsize=10.5, weight="bold", color=INK)
    ax.set_xlim(0, 8); ax.set_ylim(0, 6); ax.set_aspect("equal"); ax.axis("off")


def _stability_inset(fig):
    """A small factual validation mark anchors the two-stage schematic."""
    ax = fig.add_axes([.715, .065, .245, .16])
    x = np.arange(3)
    vals = (.865, .899, 1.000)
    ax.plot(x, vals, color=S.NEUTRAL, lw=.9, zorder=1)
    ax.scatter(x[:2], vals[:2], s=24, color=S.UNC, edgecolors="white", zorder=2)
    ax.scatter(x[2:], vals[2:], s=28, color=S.ACC, edgecolors="white", zorder=2)
    ax.set_xticks(x, ["48/96", "96/192", "两级"])
    ax.set_ylim(.82, 1.02); ax.set_yticks([.85, 1.00])
    ax.set_ylabel("一致率", fontsize=7.5)
    ax.tick_params(labelsize=7.5, pad=1)
    ax.set_title("跨分辨率标签稳定性", fontsize=7.5, loc="left", pad=2)
    for xx, value in zip(x, vals):
        ax.text(xx, value + .012, f"{value:.3f}", ha="center", fontsize=7.5)


def main():
    fig, axes = plt.subplots(1, 2, figsize=S.double_column(84), gridspec_kw={"wspace": 0.06})
    _field_panel(axes[0], fig)
    _refine_panel(axes[1])
    fig.subplots_adjust(left=.025, right=.985, top=.89, bottom=.25)
    _stability_inset(fig)
    print("SAVED", S.save(fig, "fig04_two_stage"))


if __name__ == "__main__":
    main()
