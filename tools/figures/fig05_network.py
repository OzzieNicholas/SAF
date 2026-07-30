#!/usr/bin/env python3
"""图 5 形状条件网络结构（写作指引 §4.1 / 图5）。

占据栅格 → 3×(3³ 卷积, 无池化) 编码为特征体 → 查询点 p 处三线性采样局部特征 ⊕ 归一化坐标 → MLP → 双输出头
（点级 1 维 / 方向级 D=64 维）。维数照 src/.../models/convonet.py：编码 1→16→32→32（感受野 7³）、解码 35→64→64。
纯示意（matplotlib 矢量 PDF）。用法：conda run -n saf python tools/figures/fig05_network.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon  # noqa: E402


def _box(ax, cx, cy, w, h, text, fc, ec, fs=9.0):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                fc=fc, ec=ec, lw=1.4, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=4, linespacing=1.25)


def _cube(ax, cx, cy, s, fc, ec, d=0.34, label=None, lfs=8.5):
    """伪 3D 立方体（占据/特征体 glyph）。"""
    x, y = cx - s / 2, cy - s / 2
    ax.add_patch(Polygon([(x, y), (x + s, y), (x + s, y + s), (x, y + s)], closed=True, fc=fc, ec=ec, lw=1.3, zorder=3))
    ax.add_patch(Polygon([(x, y + s), (x + d, y + s + d), (x + s + d, y + s + d), (x + s, y + s)],
                         closed=True, fc=fc, ec=ec, lw=1.3, zorder=3, alpha=0.85))
    ax.add_patch(Polygon([(x + s, y), (x + s + d, y + d), (x + s + d, y + s + d), (x + s, y + s)],
                         closed=True, fc=fc, ec=ec, lw=1.3, zorder=3, alpha=0.7))
    if label:
        ax.text(cx + d / 2, y - 0.42, label, ha="center", va="top", fontsize=lfs, linespacing=1.2)


def _slabs(ax, cx, cy, n, s, fc, ec, gap=0.22, label=None):
    """若干堆叠板（编码器/特征体的多通道感）。"""
    for i in range(n):
        x = cx - (n * gap) / 2 + i * gap
        ax.add_patch(Polygon([(x, cy - s / 2), (x, cy + s / 2), (x + 0.16, cy + s / 2 + 0.22),
                              (x + 0.16, cy - s / 2 + 0.22)], closed=True, fc=fc, ec=ec, lw=1.0, zorder=3))
    if label:
        ax.text(cx, cy - s / 2 - 0.5, label, ha="center", va="top", fontsize=8.5, linespacing=1.2)


def _arrow(ax, xy0, xy1, style="-", color="#333", lw=1.6, rad=0.0, label=None, lxy=None, lfs=8):
    ax.add_patch(FancyArrowPatch(xy0, xy1, arrowstyle="-|>", mutation_scale=13,
                                 lw=lw, color=color, linestyle=style,
                                 connectionstyle=f"arc3,rad={rad}", zorder=2))
    if label:
        ax.text(*(lxy or ((xy0[0] + xy1[0]) / 2, (xy0[1] + xy1[1]) / 2 + 0.28)), label,
                ha="center", va="center", fontsize=lfs, color=color, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.5))


def main():
    fig, ax = plt.subplots(figsize=(11.6, 4.0))
    ax.set_xlim(0, 17.2); ax.set_ylim(0, 7.0); ax.axis("off")

    BLUEF, BLUEE = "#DCE7F2", "#2C6FB2"
    ORF, ORE = "#F6E4D6", "#DD8452"
    GRF, GRE = "#ECECEC", "#8A8A8A"
    yb = 4.3

    _cube(ax, 1.35, yb, 1.15, "#E3E9F0", BLUEE, label="占据栅格\n1 × $48^3$")
    _arrow(ax, (2.2, yb), (3.05, yb))
    _box(ax, 4.25, yb, 2.15, 1.7, "编码器\n3 × Conv3d($3^3$)\n+ ReLU（无池化）\n1→16→32→32\n感受野 $7^3$", BLUEF, BLUEE, fs=8.3)
    _arrow(ax, (5.35, yb), (6.15, yb))
    _slabs(ax, 7.05, yb, 6, 1.5, "#CBD9EA", BLUEE, label="特征体\n32 × $48^3$")

    # 查询点分支
    ax.scatter([7.05], [1.35], s=70, color=S.INACC, zorder=5, edgecolors="white", linewidths=1.0)
    ax.text(7.05, 0.95, "查询点 p (x,y,z)", ha="center", va="top", fontsize=8.5)
    _arrow(ax, (7.05, 1.75), (7.05, yb - 0.85), style=(0, (4, 3)), color="#666",
           label="三线性采样", lxy=(8.35, 2.7), lfs=8)

    _box(ax, 9.55, yb, 1.9, 1.35, "拼接\n采样 32 维\n⊕ 坐标 3 维\n= 35 维", GRF, GRE, fs=8.3)
    _arrow(ax, (7.9, yb), (8.6, yb), label="32 维", lxy=(8.25, yb + 0.32), lfs=7.5)
    # 坐标进拼接（"⊕ 坐标 3 维" 已在拼接框注明，此处仅短标）
    _arrow(ax, (7.5, 1.35), (9.1, yb - 0.68), style=(0, (4, 3)), color="#666", rad=-0.2,
           label="坐标", lxy=(8.75, 2.05), lfs=7.8)

    _arrow(ax, (10.5, yb), (11.25, yb))
    _box(ax, 12.5, yb, 2.0, 1.2, "MLP\n35→64→64", ORF, ORE, fs=9.0)

    # 双头
    _box(ax, 15.7, 5.55, 2.7, 1.15, "点级头 → 1 维 logit\n不可达概率", ORF, ORE, fs=8.5)
    _box(ax, 15.7, 3.0, 2.7, 1.15, "方向级头 → 64 维 logit\n逐逼近方向被挡概率", ORF, ORE, fs=8.5)
    _arrow(ax, (13.5, yb + 0.2), (14.35, 5.55), rad=-0.15)
    _arrow(ax, (13.5, yb - 0.2), (14.35, 3.0), rad=0.15)
    ax.text(14.15, 4.35, "双头", ha="center", fontsize=8.2, color=ORE)

    print("SAVED", S.save(fig, "fig05_network"))


if __name__ == "__main__":
    main()
