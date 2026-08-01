#!/usr/bin/env python3
"""Figure 4. Complete two-stage geometry-label decision flow."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
from scipy.ndimage import distance_transform_edt  # noqa: E402


def _connect(fig, left, right):
    a, b = left.get_position(), right.get_position()
    fig.add_artist(FancyArrowPatch((a.x1 + .002, (a.y0 + a.y1) / 2),
                                   (b.x0 - .002, (b.y0 + b.y1) / 2),
                                   transform=fig.transFigure, arrowstyle="-|>", mutation_scale=8,
                                   lw=.9, color=S.NEUTRAL))


def _finish(ax, title, code):
    ax.set_title(title, fontsize=7.8, fontweight="bold", pad=3)
    ax.text(.5, -.04, code, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color=S.NEUTRAL, clip_on=False)
    ax.set_axis_off()


def _occupancy(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((.15, .18), .28, .62, fc=S.PART_DARK, ec=S.PART_EDGE, lw=.8))
    ax.add_patch(Rectangle((.15, .62), .70, .18, fc=S.PART_DARK, ec=S.PART_EDGE, lw=.8))
    for value in np.linspace(.2, .8, 7):
        ax.plot([value, value], [.18, .80], color="white", lw=.25, alpha=.65)
        ax.plot([.15, .85], [value, value], color="white", lw=.25, alpha=.65)
    _finish(ax, "占据栅格", r"$O\in\{0,1\}^{48^3}$")


def _distance(ax):
    n = 150
    yy, xx = np.mgrid[0:n, 0:n]
    solid = ((xx < 42) & (yy < 120)) | ((xx < 120) & (yy > 94))
    dist = distance_transform_edt(~solid)
    ax.imshow(np.where(~solid, dist, np.nan), cmap="Blues", origin="lower")
    ax.imshow(np.where(solid, 1, np.nan), cmap=plt.matplotlib.colors.ListedColormap([S.PART_DARK]), origin="lower")
    _finish(ax, "距离场 EDT", r"$D=\mathrm{EDT}(\neg O)$")


def _sample(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Polygon([(0, .10), (.58, .22), (1, .12), (1, 0), (0, 0)],
                         fc=S.PART, ec=S.PART_EDGE, lw=.8))
    point = np.array([.56, .22]); ax.scatter(*point, s=24, c=S.INK, zorder=5)
    for angle, colour in ((65, S.ACC), (90, S.ORANGE), (120, S.INACC)):
        end = point + .62 * np.array([np.cos(np.radians(angle)), np.sin(np.radians(angle))])
        ax.add_patch(FancyArrowPatch(point, end, arrowstyle="-|>", mutation_scale=8,
                                     lw=1.0, color=colour))
        for t in (.25, .45, .65):
            sample = point + t * (end - point)
            ax.scatter(*sample, s=10, fc="white", ec=colour, lw=.6, zorder=4)
    _finish(ax, "方向 ray-march", r"$p+t\mathbf{v}_i$")


def _clearance(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    values = (.78, .50, .23)
    colours = (S.ACC, S.ORANGE, S.INACC)
    for row, (value, colour) in enumerate(zip(values, colours)):
        y = .72 - row * .25
        ax.plot([.18, .82], [y, y], color=S.PALE_GREY, lw=5, solid_capstyle="round")
        ax.plot([.18, .18 + .64 * value], [y, y], color=colour, lw=5, solid_capstyle="round")
        ax.text(.08, y, f"$c_{row + 1}$", ha="center", va="center", fontsize=7.5)
    _finish(ax, "最小净空", r"$c_i=\min_t D(p+t\mathbf{v}_i)$")


def _triage(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    bounds = (.14, .35, .65, .86)
    ax.plot([bounds[0], bounds[-1]], [.52, .52], color=S.PART_EDGE, lw=1)
    ax.axvspan(bounds[0], bounds[1], ymin=.38, ymax=.66, color=S.PALE_RED)
    ax.axvspan(bounds[1], bounds[2], ymin=.38, ymax=.66, color=S.PALE_ORANGE)
    ax.axvspan(bounds[2], bounds[3], ymin=.38, ymax=.66, color=S.PALE_BLUE)
    for x, text in ((bounds[1], r"$r-\varepsilon$"), (bounds[2], r"$r+\varepsilon$")):
        ax.plot([x, x], [.40, .64], color=S.PART_EDGE, lw=.8)
        ax.text(x, .29, text, ha="center", fontsize=7.5)
    ax.text(.245, .72, "挡", ha="center", fontsize=7.5, color=S.INACC)
    ax.text(.50, .72, "细化", ha="center", fontsize=7.5, color=S.ORANGE)
    ax.text(.755, .72, "清", ha="center", fontsize=7.5, color=S.ACC)
    _finish(ax, "三态分流", r"$c_i$ 对比 $r\pm\varepsilon$")


def _refine(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    surface = np.array([[.05, .25], [.32, .38], [.52, .30], [.76, .43], [.95, .22]])
    ax.add_patch(Polygon(np.vstack([surface, [.95, .05], [.05, .05]]),
                         fc=S.PART, ec=S.PART_EDGE, lw=.8))
    ax.plot(surface[:, 0], surface[:, 1], color=S.PART_EDGE, lw=1.0)
    ax.plot([.45, .73], [.34, .86], color=S.ORANGE, lw=10, alpha=.32, solid_capstyle="round")
    ax.plot([.45, .73], [.34, .86], color="#A9562D", lw=1.0)
    ax.scatter([.64], [.37], marker="x", s=30, c=S.INACC, lw=1.4, zorder=4)
    _finish(ax, "连续几何细化", r"$\mathcal{C}_i\cap P\;?$")


def main():
    fig = plt.figure(figsize=S.double_column(88))
    grid = fig.add_gridspec(2, 6, height_ratios=(1, .44), left=.025, right=.985,
                            bottom=.10, top=.93, wspace=.22, hspace=.36)
    top = [fig.add_subplot(grid[0, i]) for i in range(6)]
    for function, axis in zip((_occupancy, _distance, _sample, _clearance, _triage, _refine), top):
        function(axis)
    for left, right in zip(top[:-1], top[1:]):
        _connect(fig, left, right)

    decision = fig.add_subplot(grid[1, :3])
    decision.set_xlim(0, 1); decision.set_ylim(0, 1); decision.axis("off")
    decision.set_title("(a) 每方向判定与点级归约", loc="left", fontsize=8.4, fontweight="bold", pad=2)
    for x, colour in ((.10, S.ACC), (.18, S.INACC), (.26, S.ACC), (.34, S.INACC)):
        decision.add_patch(Circle((x, .49), .025, fc=colour, ec="white", lw=.4))
    decision.add_patch(FancyArrowPatch((.39, .49), (.48, .49), arrowstyle="-|>", mutation_scale=8,
                                       color=S.NEUTRAL, lw=.8))
    decision.add_patch(Rectangle((.49, .34), .18, .30, fc=S.PALE_GREY, ec=S.UNC, lw=.8))
    decision.text(.58, .49, r"$[a_1,\ldots,a_D]$", ha="center", va="center", fontsize=8)
    decision.add_patch(FancyArrowPatch((.68, .49), (.75, .49), arrowstyle="-|>", mutation_scale=8,
                                       color=S.NEUTRAL, lw=.8))
    decision.text(.82, .49, r"$y=\neg\bigvee_i a_i$", ha="center", va="center",
                  fontsize=7.5, color=S.INK)

    stability = fig.add_subplot(grid[1, 3:])
    x = np.arange(3); values = np.array([.865, .899, 1.000])
    stability.plot(x, values, color=S.NEUTRAL, lw=1.0, zorder=1)
    stability.scatter(x[:2], values[:2], s=34, c=S.UNC, edgecolors="white", zorder=2)
    stability.scatter(x[2], values[2], s=38, c=S.ACC, edgecolors="white", zorder=2)
    for xx, value in zip(x, values):
        stability.text(xx, value + .012, f"{value:.3f}", ha="center", fontsize=7.5)
    stability.set_xticks(x, ["48/96", "96/192", "两级细化"])
    stability.set_ylim(.83, 1.025); stability.set_yticks([.85, .90, .95, 1.00])
    stability.set_title("(b) 边界细化后的跨分辨率稳定性", loc="left",
                        fontsize=8.4, fontweight="bold", pad=2)
    stability.grid(axis="y"); stability.set_axisbelow(True)
    print("SAVED", S.save(fig, "fig04_two_stage"))


if __name__ == "__main__":
    main()
