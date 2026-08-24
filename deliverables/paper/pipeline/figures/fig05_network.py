#!/usr/bin/env python3
"""Figure 5. Code-faithful ConvONetLite tensor and query flow."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402


def _arrow(ax, start, end, colour=S.NEUTRAL, dashed=False):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9, lw=.9,
                                 color=colour, linestyle=(0, (3, 2)) if dashed else "-"))


def _block(ax, xy, wh, title, detail, fill, edge):
    x, y = xy; width, height = wh
    ax.add_patch(Rectangle((x, y), width, height, fc=fill, ec=edge, lw=.85))
    ax.text(x + width / 2, y + height * .62, title, ha="center", va="center",
            fontsize=7.8, fontweight="bold", color=S.INK)
    ax.text(x + width / 2, y + height * .29, detail, ha="center", va="center",
            fontsize=7.5, color=S.NEUTRAL)


def _volume(ax, x, y, width, height):
    for offset in (.16, .08, 0):
        ax.add_patch(Polygon([(x + offset, y + offset), (x + width + offset, y + offset),
                              (x + width + offset, y + height + offset), (x + offset, y + height + offset)],
                             closed=True, fc=S.PALE_BLUE, ec=S.ACC, lw=.7))


def _neighbours(ax, centre):
    cx, cy = centre
    offsets = np.array([[-.16, -.12], [.16, -.12], [-.16, .12], [.16, .12],
                        [-.08, -.04], [.24, -.04], [-.08, .20], [.24, .20]])
    ax.scatter(cx + offsets[:, 0], cy + offsets[:, 1], s=22, c=S.ACC,
               edgecolors="white", linewidths=.4, zorder=3)
    ax.scatter([cx + .04], [cy + .04], s=30, c=S.INACC, edgecolors="white", zorder=4)
    for offset in offsets:
        ax.plot([cx + .04, cx + offset[0]], [cy + .04, cy + offset[1]],
                color=S.ACC, lw=.45, alpha=.65)


def main():
    fig, ax = plt.subplots(figsize=S.double_column(82))
    ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis("off")

    ax.text(.35, 7.55, "(a) 形状编码", fontsize=8.5, fontweight="bold", color=S.INK)
    _block(ax, (.40, 5.30), (1.55, 1.18), "占据栅格", "1 通道", S.PALE_GREY, S.UNC)
    convs = ((2.45, "Conv³", "1 → 16"), (4.35, "Conv³", "16 → 32"),
             (6.25, "Conv³", "32 → 32"))
    for x, title, detail in convs:
        _block(ax, (x, 5.30), (1.55, 1.18), title, detail, S.PALE_BLUE, S.ACC)
    _volume(ax, 8.45, 5.28, 1.05, 1.18)
    ax.text(9.08, 4.84, "32 通道特征体\nn_x × n_y × n_z", ha="center", va="top",
            fontsize=7.5, color=S.INK, linespacing=1.15)
    ax.text(5.20, 6.90, "max(n)=48 · 无池化 · 感受野 7³ · 保持空间分辨率",
            ha="center", fontsize=7.5, color=S.NEUTRAL)
    for start, end in (((1.95, 5.89), (2.43, 5.89)), ((4.00, 5.89), (4.33, 5.89)),
                       ((5.90, 5.89), (6.23, 5.89)), ((7.80, 5.89), (8.42, 5.89))):
        _arrow(ax, start, end)

    ax.text(.35, 4.15, "(b) 查询与解码", fontsize=8.5, fontweight="bold", color=S.INK)
    _block(ax, (.40, 2.05), (1.55, 1.18), r"查询点 $p$", "grid [N, 3]", S.PALE_GREY, S.UNC)
    _neighbours(ax, (2.82, 2.60))
    ax.text(2.88, 1.98, "8 邻点", ha="center", fontsize=7.5, color=S.INK)
    _block(ax, (3.85, 2.05), (1.65, 1.18), "三线性采样", "[N, 32]", S.PALE_BLUE, S.ACC)
    _block(ax, (6.05, 2.05), (1.65, 1.18), "特征拼接", "[N, 35]", S.PALE_GREY, S.UNC)
    _block(ax, (8.25, 2.05), (2.05, 1.18), "MLP", "两层 64 单元", S.PALE_ORANGE, S.ORANGE)
    for start, end in (((1.95, 2.64), (2.30, 2.64)), ((3.28, 2.64), (3.83, 2.64)),
                       ((5.50, 2.64), (6.03, 2.64)), ((7.70, 2.64), (8.23, 2.64))):
        _arrow(ax, start, end)
    ax.add_patch(FancyArrowPatch((8.50, 5.22), (3.18, 3.05), connectionstyle="arc3,rad=.08",
                                 arrowstyle="-|>", mutation_scale=9, lw=.9,
                                 color=S.ACC, linestyle=(0, (3, 2))))

    ax.plot([10.85, 10.85], [1.05, 6.55], color="#D5D9DC", lw=.9)
    ax.text(11.15, 7.05, "(c) 同构实例化，权重不共享", fontsize=8.5, fontweight="bold", color=S.INK)
    _block(ax, (11.15, 4.55), (2.10, 1.30), r"点级 $\theta_p$", "out = 1", S.PALE_BLUE, S.ACC)
    _block(ax, (11.15, 1.55), (2.10, 1.30), r"方向级 $\theta_d$", "out = 64", S.PALE_ORANGE, S.ORANGE)
    _arrow(ax, (10.30, 2.80), (11.10, 5.18), S.ACC)
    _arrow(ax, (10.30, 2.48), (11.10, 2.20), S.ORANGE)
    ax.plot([13.55, 15.55], [5.58, 5.58], color=S.ACC, lw=1.3)
    ax.text(13.55, 5.82, "不可达概率", fontsize=7.8, fontweight="bold", color=S.ACC)
    ax.text(13.55, 5.08, "每接触点 1 logit", fontsize=7.5, color=S.NEUTRAL)
    for i, colour in enumerate((S.ACC, S.INACC, S.ACC, S.INACC, S.ACC)):
        ax.add_patch(Circle((14.25 + .22 * i, 4.68), .06, fc=colour, ec="white", lw=.35))
    ax.plot([13.55, 15.55], [2.58, 2.58], color=S.ORANGE, lw=1.3)
    ax.text(13.55, 2.82, "固定方向被挡概率", fontsize=7.8, fontweight="bold", color=S.ORANGE)
    ax.text(13.55, 2.08, "每接触点 64 logits", fontsize=7.5, color=S.NEUTRAL)
    centre = (14.55, 1.62)
    for angle, colour in zip(np.linspace(20, 340, 8), (S.ACC, S.INACC) * 4):
        direction = np.array([np.cos(np.radians(angle)), np.sin(np.radians(angle))])
        _arrow(ax, tuple(np.asarray(centre) + .36 * direction), centre, colour)
    ax.add_patch(Circle(centre, .05, fc=S.INK, ec="white", lw=.35))
    ax.text(8.25, .62, "训练：Adam + BCEWithLogitsLoss；点级与方向级分别优化", ha="center",
            fontsize=7.5, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "fig05_network"))


if __name__ == "__main__":
    main()
