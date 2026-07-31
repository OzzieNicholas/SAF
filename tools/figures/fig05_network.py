#!/usr/bin/env python3
"""图 5 ConvONet-lite：点级与方向级是两种分别训练的模型配置。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402


INK = "#263238"
BLUEF, BLUEE = "#E7F0F7", S.ACC
ORANGEF, ORANGEE = "#FAEDE3", S.ORANGE
GREYF, GREYE = "#F1F2F3", S.NEUTRAL


def _box(ax, x, y, w, h, text, fc, ec, fs=8.2, lw=1.1, radius=0.09):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={radius}",
                                fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, zorder=4, linespacing=1.22)


def _arrow(ax, p0, p1, color=INK, ls="-", lw=1.3, label=None, xy=None, rad=0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10, color=color,
                                 lw=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=2))
    if label:
        x, y = xy or ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.18)
        ax.text(x, y, label, ha="center", va="center", fontsize=6.9, color=color,
                bbox=dict(fc="white", ec="none", pad=0.7), zorder=6)


def _cube(ax, x, y, s, label):
    d = 0.16
    ax.add_patch(Rectangle((x, y), s, s, fc="#D7E4EF", ec=BLUEE, lw=1.0, zorder=3))
    ax.add_patch(Polygon([(x, y + s), (x + d, y + s + d), (x + s + d, y + s + d),
                          (x + s, y + s)], fc="#EDF3F8", ec=BLUEE, lw=1.0, zorder=3))
    ax.add_patch(Polygon([(x + s, y), (x + s + d, y + d), (x + s + d, y + s + d),
                          (x + s, y + s)], fc="#B9CDDF", ec=BLUEE, lw=1.0, zorder=3))
    for i in range(3):
        ax.plot([x + 0.16 + i * 0.18, x + 0.16 + i * 0.18], [y, y + s], color="white", lw=0.4, zorder=4)
    ax.text(x + s / 2 + d / 2, y - 0.25, label, ha="center", va="top", fontsize=7.1, color=INK)


def _feature_stack(ax, x, y):
    for i, (w, h) in enumerate(((0.60, 0.78), (0.54, 1.02), (0.48, 1.24), (0.42, 1.43), (0.36, 1.60))):
        xx = x + i * 0.12
        ax.add_patch(Polygon([(xx, y), (xx + w, y), (xx + w, y + h), (xx, y + h)],
                             fc="#C5D7E8", ec=BLUEE, lw=0.75, zorder=3))
    ax.text(x + 0.52, y - 0.25, "特征体\n32 × 48³", ha="center", va="top", fontsize=7.1)


def _mlp(ax, x, y):
    for i, n in enumerate((4, 5, 5, 3)):
        for j in range(n):
            ax.add_patch(Circle((x + i * 0.28, y + 0.25 + j * 0.19), 0.038,
                                fc="#E8B99C" if i > 0 else "#CFD3D6", ec=ORANGEE, lw=0.45, zorder=4))
        if i < 3:
            for j in range(n):
                for k in range((4, 5, 5, 3)[i + 1]):
                    ax.plot([x + i * 0.28 + 0.04, x + (i + 1) * 0.28 - 0.04],
                            [y + 0.25 + j * 0.19, y + 0.25 + k * 0.19],
                            color="#B9A193", lw=0.28, alpha=0.55, zorder=2)
    ax.text(x + 0.42, y - 0.25, "MLP\n35 → 64 → 64", ha="center", va="top", fontsize=7.1)


def _output_glyph(ax, x, y, directional=False):
    if not directional:
        for i, c in enumerate((S.ACC, S.ACC, S.INACC, S.INACC, S.ACC, S.INACC)):
            ax.add_patch(Circle((x + (i % 3) * 0.22, y + (i // 3) * 0.22), 0.06, fc=c, ec="white", lw=0.35))
        ax.text(x + 0.22, y - 0.28, "1 logit / point\n" + r"$\hat y_p$: inaccessible",
                ha="center", va="top", fontsize=7.0)
    else:
        center = (x + 0.22, y + 0.20)
        for dx, dy, c in ((-.32, .18, S.ACC), (-.18, .34, S.ACC), (0, .39, S.INACC),
                          (.18, .34, S.INACC), (.32, .18, S.ACC), (0, -.16, S.INACC)):
            _arrow(ax, (center[0] + dx, center[1] + dy), center, color=c, lw=0.9)
        ax.add_patch(Circle(center, 0.055, fc=INK, ec="white", lw=0.4, zorder=5))
        ax.text(x + 0.22, y - 0.30, "$D=64$ logits / point\n" + r"$\hat y_{p,i}$: blocked direction",
                ha="center", va="top", fontsize=7.0)


def main():
    fig, ax = plt.subplots(figsize=(11.8, 5.9))
    ax.set_xlim(0, 17.4); ax.set_ylim(0, 8.1); ax.axis("off")
    ax.text(0.18, 7.78, "同一形状条件解码器，两种输出粒度、两次独立训练", fontsize=13.2,
            weight="bold", color=INK)
    ax.text(0.18, 7.43, "共享的是架构模板，不是同时优化的双头网络；点级任务与方向级任务分别实例化 ConvONet-lite",
            fontsize=8.4, color=S.NEUTRAL)

    _box(ax, 0.35, 5.77, 1.72, 1.0, "占据栅格\n1 × 48³", BLUEF, BLUEE, fs=8.5)
    _cube(ax, 0.78, 6.00, 0.42, "")
    _arrow(ax, (2.15, 6.27), (2.72, 6.27))
    _box(ax, 2.72, 5.67, 2.02, 1.2, "编码器\n3 × Conv3d(3³)\nReLU · 无池化\n1 → 16 → 32 → 32", BLUEF, BLUEE, fs=7.6)
    _arrow(ax, (4.84, 6.27), (5.34, 6.27))
    _feature_stack(ax, 5.40, 5.36)
    _box(ax, 7.18, 5.75, 1.72, 1.04, "查询点 p\n归一坐标 (x,y,z)", GREYF, GREYE, fs=8.0)
    ax.add_patch(Circle((7.60, 6.13), 0.075, fc=S.INACC, ec="white", lw=0.7, zorder=5))
    _arrow(ax, (6.52, 5.32), (7.43, 5.75), color="#666", ls=(0, (3, 2)), label="三线性采样", xy=(7.02, 5.30))
    _arrow(ax, (8.04, 5.76), (8.65, 5.76), color="#666", ls=(0, (3, 2)), label="坐标", xy=(8.35, 5.40))
    _box(ax, 8.64, 5.55, 1.74, 0.84, "拼接\n32 + 3 = 35 维", GREYF, GREYE, fs=8.0)
    _arrow(ax, (10.43, 5.97), (10.82, 5.97))
    _mlp(ax, 10.88, 5.48)
    ax.text(11.30, 7.05, "局部特征 ⊕ 归一化坐标", ha="center", fontsize=7.4, color=S.NEUTRAL)

    # The split is deliberate: each branch is a separately trained model.
    ax.plot([12.08, 12.08], [1.0, 6.45], color="#D9DCDD", lw=1.0, ls=(0, (2, 3)))
    ax.text(12.08, 6.74, "独立实例化 / 独立训练", ha="center", fontsize=8.0, weight="bold", color=INK)
    _arrow(ax, (11.98, 5.93), (12.62, 4.62), color=BLUEE, rad=-0.12)
    _arrow(ax, (11.98, 5.93), (12.62, 2.08), color=ORANGEE, rad=0.12)

    _box(ax, 12.62, 3.63, 4.28, 1.74, "点级 ConvONet-lite\n\n输出：每个接触点 1 个 logit\n标签：不可达 / 可达（二分类）", BLUEF, BLUEE, fs=8.3, lw=1.4)
    _output_glyph(ax, 16.02, 4.00, directional=False)
    ax.text(12.86, 3.79, "H3 / H5 主线", fontsize=6.8, color=BLUEE, weight="bold")

    _box(ax, 12.62, 0.90, 4.28, 1.74, "方向级 ConvONet-lite\n\n输出：每个接触点 × 每个方向 1 个 logit\n标签：逐方向 blocked（不先做 any）", ORANGEF, ORANGEE, fs=8.1, lw=1.4)
    _output_glyph(ax, 16.02, 1.24, directional=True)
    ax.text(12.86, 1.06, "E5 · D=64（128 采样的下半球）", fontsize=6.8, color=ORANGEE, weight="bold")

    ax.add_patch(FancyBboxPatch((0.35, 0.54), 16.55, 0.24, boxstyle="round,pad=0.01,rounding_size=0.04",
                                fc="#F5F6F6", ec="none", zorder=0))
    ax.text(8.62, 0.66,
            r"方向场的 any-归约：$\mathrm{any}_i(\mathrm{accessible}_{p,i})$ = 点级可达性判定（oracle 不变量）",
            ha="center", va="center", fontsize=7.5, color=INK)
    print("SAVED", S.save(fig, "fig05_network"))


if __name__ == "__main__":
    main()
