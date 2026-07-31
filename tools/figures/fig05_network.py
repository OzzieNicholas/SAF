#!/usr/bin/env python3
"""Figure 5. Compact shape-conditioned predictor with two separately trained heads."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402


def _arrow(ax, start, end, colour=S.NEUTRAL, dashed=False):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, lw=1.0,
                                 color=colour, linestyle=(0, (3, 2)) if dashed else "-"))


def _block(ax, x, y, width, height, label, fill, edge, detail=""):
    ax.add_patch(Rectangle((x, y), width, height, fc=fill, ec=edge, lw=.9))
    ax.text(x + width / 2, y + height / 2 + .12, label, ha="center", va="center",
            fontsize=8.0, color=S.INK, fontweight="bold")
    if detail:
        ax.text(x + width / 2, y + height / 2 - .17, detail, ha="center", va="center",
                fontsize=7.5, color=S.NEUTRAL)


def _volume(ax, x, y):
    for index, (width, height) in enumerate(((.56, .78), (.47, .98), (.38, 1.18))):
        ax.add_patch(Rectangle((x + index * .11, y + (1.18 - height) / 2), width, height,
                               fc=S.PALE_BLUE, ec=S.ACC, lw=.75))
    ax.text(x + .42, y - .27, "特征体\n32 × 48³", ha="center", va="top", fontsize=7.5, color=S.INK)


def _output(ax, x, y, heading, detail, colour, directional=False):
    ax.plot([x, x + 2.3], [y + 1.2, y + 1.2], color=colour, lw=1.4)
    ax.text(x, y + 1.42, heading, fontsize=8.0, color=colour, fontweight="bold")
    ax.text(x, y + .18, detail, fontsize=7.5, color=S.NEUTRAL)
    if directional:
        center = (x + 1.92, y + .78)
        for dx, dy, col in ((-.28, .16, S.ACC), (0, .30, S.INACC), (.25, .12, S.ACC), (.06, -.22, S.INACC)):
            _arrow(ax, (center[0] + dx, center[1] + dy), center, col)
        ax.add_patch(Circle(center, .045, fc=S.INK, ec="white", lw=.4))
    else:
        for index, col in enumerate((S.ACC, S.INACC, S.ACC, S.INACC, S.ACC, S.INACC)):
            ax.add_patch(Circle((x + 1.50 + .17 * (index % 3), y + .58 + .19 * (index // 3)),
                                .055, fc=col, ec="white", lw=.35))


def main():
    fig, ax = plt.subplots(figsize=S.double_column(70))
    ax.set_xlim(0, 13.8); ax.set_ylim(0, 6.1); ax.axis("off")

    _block(ax, .28, 3.63, 1.24, 1.06, "占据栅格", S.PALE_BLUE, S.ACC, "1 × 48³")
    for gx in (.55, .82, 1.09): ax.plot([gx, gx], [3.63, 4.69], color="white", lw=.5)
    _arrow(ax, (1.57, 4.16), (2.02, 4.16))
    _block(ax, 2.05, 3.48, 1.83, 1.36, "编码器", S.PALE_BLUE, S.ACC, "3 × Conv3d(3³)")
    _arrow(ax, (3.94, 4.16), (4.33, 4.16))
    _volume(ax, 4.38, 3.55)
    _arrow(ax, (5.28, 4.16), (5.82, 4.16), S.NEUTRAL, dashed=True)
    _block(ax, 5.87, 3.57, 1.34, 1.18, "查询点 $p$", S.PALE_GREY, S.UNC, "归一化坐标")
    ax.add_patch(Circle((6.23, 4.06), .06, fc=S.INACC, ec="white", lw=.4))
    _arrow(ax, (7.27, 4.16), (7.67, 4.16))
    _block(ax, 7.72, 3.57, 1.34, 1.18, "拼接", S.PALE_GREY, S.UNC, "32 + 3 维")
    _arrow(ax, (9.12, 4.16), (9.49, 4.16))
    _block(ax, 9.54, 3.57, 1.34, 1.18, "MLP", S.PALE_ORANGE, S.ORANGE, "35 → 64 → 64")

    ax.plot([.28, 10.88], [5.37, 5.37], color="#D9DDDF", lw=.8)
    ax.text(.28, 5.56, "共享的形状条件解码器", fontsize=8.2, color=S.INK, fontweight="bold")
    ax.text(10.88, 5.56, "按任务独立训练", ha="right", fontsize=7.5, color=S.NEUTRAL)
    ax.plot([10.98, 10.98], [1.08, 4.78], color="#D9DDDF", lw=.8)
    _arrow(ax, (10.90, 4.02), (11.35, 4.84), S.ACC)
    _arrow(ax, (10.90, 3.86), (11.35, 1.58), S.ORANGE)
    _output(ax, 11.18, 3.08, "点级头", "每接触点 1 个不可达 logit", S.ACC)
    _output(ax, 11.18, .46, "方向级头", "每接触点 64 个被挡 logit", S.ORANGE, directional=True)
    ax.text(6.2, 2.55, "三线性采样局部特征，并拼接查询坐标", ha="center", fontsize=7.5, color=S.NEUTRAL)

    print("SAVED", S.save(fig, "fig05_network"))


if __name__ == "__main__":
    main()
