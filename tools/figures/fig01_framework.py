#!/usr/bin/env python3
"""图 1 方法总体框架：几何标签生成、形状条件学习与未见件推理。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402


INK = "#263238"
PALE_BLUE = "#E8F0F7"
PALE_GREEN = "#E7F1EA"
PALE_ORANGE = "#FAEDE3"
PALE_GREY = "#F2F3F4"


def _panel(ax, x, y, w, h, fc="white", ec="#D3D7DA", radius=0.12, lw=0.9, z=0):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={radius}",
                           facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(patch)
    return patch


def _arrow(ax, p0, p1, color=INK, ls="-", lw=1.35, rad=0, label=None, label_xy=None):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10, color=color,
                                 linewidth=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=5))
    if label:
        xy = label_xy or ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        ax.text(*xy, label, ha="center", va="center", fontsize=7.2, color=color,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.8), zorder=6)


def _voxel(ax, x, y, s=0.42, fc="#D7E2EC", ec=S.ACC):
    d = 0.13
    ax.add_patch(Rectangle((x, y), s, s, facecolor=fc, edgecolor=ec, lw=1.0, zorder=3))
    ax.add_patch(Polygon([(x, y + s), (x + d, y + s + d), (x + s + d, y + s + d),
                          (x + s, y + s)], facecolor="#EEF3F7", edgecolor=ec, lw=1.0, zorder=3))
    ax.add_patch(Polygon([(x + s, y), (x + s + d, y + d), (x + s + d, y + s + d),
                          (x + s, y + s)], facecolor="#BECFDE", edgecolor=ec, lw=1.0, zorder=3))
    for q in (0.14, 0.28):
        ax.plot([x + q, x + q], [y, y + s], color="white", lw=0.45, alpha=0.9, zorder=4)
        ax.plot([x, x + s], [y + q, y + q], color="white", lw=0.45, alpha=0.9, zorder=4)


def _mesh(ax, x, y, scale=1.0, contacts=False):
    pts = [(x, y), (x + 0.42 * scale, y + 0.1 * scale), (x + 0.62 * scale, y + 0.56 * scale),
           (x + 0.18 * scale, y + 0.72 * scale), (x - 0.12 * scale, y + 0.38 * scale)]
    ax.add_patch(Polygon(pts, closed=True, facecolor="#E1E3E5", edgecolor=S.NEUTRAL, lw=1.0, zorder=3))
    for a, b in ((0, 2), (0, 3), (1, 3), (1, 4)):
        ax.plot([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]], color="#AEB3B7", lw=0.55, zorder=4)
    if contacts:
        for i, c in enumerate((S.INACC, S.ACC, S.INACC, S.ACC)):
            ax.add_patch(Circle((x + (0.02 + i * 0.15) * scale, y + (0.09 + 0.03 * (i % 2)) * scale),
                                0.035 * scale, facecolor=c, edgecolor="white", lw=0.45, zorder=5))


def _stage(ax, x, title, subtitle, kind, color, pale):
    _panel(ax, x, 4.03, 1.58, 1.25, fc="white", ec="#D8DCDF", radius=0.08)
    ax.add_patch(Rectangle((x, 5.16), 1.58, 0.12, facecolor=color, edgecolor="none", zorder=2))
    if kind == "mesh":
        _mesh(ax, x + 0.48, 4.48, 0.8)
    elif kind == "voxel":
        _voxel(ax, x + 0.48, 4.47, 0.43, pale, color)
    elif kind == "contact":
        _mesh(ax, x + 0.48, 4.48, 0.8, contacts=True)
    elif kind == "oracle":
        for i, c in enumerate((S.ACC, S.UNC, S.INACC)):
            ax.add_patch(Circle((x + 0.43 + i * 0.35, 4.73), 0.13, fc="white", ec=c, lw=1.3))
        ax.plot([x + 0.56, x + 0.65], [4.73, 4.73], color=INK, lw=1)
        ax.plot([x + 0.91, x + 1.0], [4.73, 4.73], color=INK, lw=1)
    else:
        for i, c in enumerate((S.ACC, S.INACC, S.ACC, S.INACC, S.INACC)):
            ax.add_patch(Circle((x + 0.35 + i * 0.22, 4.72), 0.065, fc=c, ec="white", lw=0.4))
    ax.text(x + 0.79, 4.32, title, ha="center", va="center", fontsize=8.2, weight="bold", color=INK)
    ax.text(x + 0.79, 4.12, subtitle, ha="center", va="center", fontsize=6.6, color=S.NEUTRAL)


def main():
    fig, ax = plt.subplots(figsize=(11.8, 5.35))
    ax.set_xlim(0, 15.8)
    ax.set_ylim(0, 7.45)
    ax.axis("off")

    ax.text(0.15, 7.12, "从几何定义到未见零件的可达性场预测", fontsize=14, weight="bold", color=INK)
    ax.text(0.15, 6.78, "Support Accessibility Field · 仅评价支撑接触区的几何可达性代理",
            fontsize=8.5, color=S.NEUTRAL)

    ax.text(0.15, 6.18, "A", fontsize=12, weight="bold")
    ax.text(0.55, 6.18, "离线几何判定器", fontsize=10.5, weight="bold", color=S.GREEN)
    ax.text(2.55, 6.18, "确定性标签生成", fontsize=7.5, color=S.NEUTRAL)
    ax.plot([0.55, 15.55], [5.88, 5.88], color="#D9E5DC", lw=1.0)

    stages = [
        (0.55, "CAD 网格", "公开 / 程序化", "mesh", S.NEUTRAL, PALE_GREY),
        (3.05, "归一化", "最长边 = 1", "mesh", S.NEUTRAL, PALE_GREY),
        (5.55, "占据栅格", "缠绕数 · 48³", "voxel", S.ACC, PALE_BLUE),
        (8.05, "接触区 S(P,d)", "n·d < −cos45°", "contact", S.ORANGE, PALE_ORANGE),
        (10.55, "两级判定", "距离场 → 精确细化", "oracle", S.GREEN, PALE_GREEN),
        (13.05, "监督标签", "蓝 可达 · 红 不可达", "labels", S.GREEN, PALE_GREEN),
    ]
    for item in stages:
        _stage(ax, *item)
    for x in (2.13, 4.63, 7.13, 9.63, 12.13):
        _arrow(ax, (x, 4.66), (x + 0.78, 4.66), color="#5B6267")

    _panel(ax, 9.95, 5.42, 2.05, 0.34, fc=PALE_GREEN, ec="none", radius=0.08)
    ax.text(10.98, 5.59, "球工具 · 下半球直线逼近", ha="center", va="center", fontsize=6.8, color=S.GREEN)

    ax.text(0.15, 3.37, "B", fontsize=12, weight="bold")
    ax.text(0.55, 3.37, "形状条件学习", fontsize=10.5, weight="bold", color=S.ORANGE)
    ax.text(2.15, 3.37, "按模型切分 · 两种输出任务分别训练", fontsize=7.5, color=S.NEUTRAL)
    ax.plot([0.55, 15.55], [3.08, 3.08], color="#EEE0D7", lw=1.0)

    _panel(ax, 0.55, 0.50, 3.1, 2.18, fc="#FBFBFB", ec="#D7DADC")
    ax.text(0.75, 2.42, "未见 CAD", fontsize=8.5, weight="bold", color=INK)
    _mesh(ax, 0.92, 1.20, 1.0)
    _arrow(ax, (1.85, 1.56), (2.45, 1.56), color=S.ORANGE, ls=(0, (3, 2)))
    _voxel(ax, 2.63, 1.35, 0.52, PALE_BLUE, S.ACC)
    ax.text(2.90, 0.86, "仅形状 + 查询点", ha="center", fontsize=6.8, color=S.NEUTRAL)

    _panel(ax, 4.15, 0.50, 4.8, 2.18, fc=PALE_ORANGE, ec="#E8CDBB")
    ax.text(4.40, 2.42, "ConvONet-lite", fontsize=9.2, weight="bold", color="#A9562D")
    for i, h in enumerate((0.72, 1.00, 1.28)):
        ax.add_patch(Rectangle((4.65 + i * 0.25, 1.05 + (1.28 - h) / 2), 0.13, h,
                               fc="#AFC6DC", ec=S.ACC, lw=0.6))
    ax.text(5.00, 0.82, "3D-CNN\n特征体", ha="center", fontsize=6.8)
    ax.add_patch(Circle((6.08, 1.58), 0.09, fc=S.INACC, ec="white", lw=0.6, zorder=4))
    ax.text(6.08, 0.91, "点查询 p\n三线性采样", ha="center", fontsize=6.8)
    _arrow(ax, (5.42, 1.58), (5.95, 1.58), color=INK)
    _arrow(ax, (6.22, 1.58), (6.75, 1.58), color=INK)
    for i, w in enumerate((0.55, 0.42, 0.30)):
        ax.add_patch(Rectangle((6.78 + i * 0.34, 1.58 - w / 2), 0.12, w, fc="#E3B99E", ec=S.ORANGE, lw=0.6))
    ax.text(7.25, 0.91, "坐标拼接\nMLP", ha="center", fontsize=6.8)
    ax.text(8.15, 1.58, "f(P,p)", ha="center", va="center", fontsize=9, style="italic", color=INK)
    _arrow(ax, (7.78, 1.58), (8.00, 1.58), color=INK)

    ax.text(9.40, 2.56, "独立训练配置", ha="center", fontsize=7.1, color=S.NEUTRAL)
    _arrow(ax, (8.95, 1.72), (9.72, 2.22), color=S.ACC, rad=-0.10)
    _arrow(ax, (8.95, 1.42), (9.72, 0.95), color=S.ORANGE, rad=0.10)

    _panel(ax, 9.75, 1.68, 5.80, 0.98, fc=PALE_BLUE, ec="#BFD0E0", radius=0.09)
    ax.text(10.02, 2.42, "点级模型", fontsize=8.4, weight="bold", color=S.ACC)
    ax.text(11.50, 2.15, "1 logit / 点", fontsize=8.2, weight="bold")
    ax.text(13.20, 2.15, "不可达概率热图", fontsize=7.5, color=S.NEUTRAL)
    for i, c in enumerate((S.ACC, S.ACC, S.INACC, S.INACC, S.ACC, S.INACC)):
        ax.add_patch(Circle((14.00 + (i % 3) * 0.28, 2.04 + (i // 3) * 0.27), 0.065, fc=c, ec="white", lw=0.4))

    _panel(ax, 9.75, 0.50, 5.80, 0.98, fc=PALE_ORANGE, ec="#E8CDBB", radius=0.09)
    ax.text(10.02, 1.24, "方向级模型", fontsize=8.4, weight="bold", color=S.ORANGE)
    ax.text(11.50, 0.97, "D=64 logits / 点", fontsize=8.2, weight="bold")
    ax.text(13.20, 0.97, "逐逼近方向被挡概率", fontsize=7.5, color=S.NEUTRAL)
    center = (14.34, 0.96)
    for dx, dy, c in ((-.34, .20, S.ACC), (-.18, .34, S.ACC), (.0, .38, S.INACC),
                      (.18, .34, S.INACC), (.34, .20, S.ACC)):
        _arrow(ax, (center[0] + dx, center[1] + dy), center, color=c, lw=1.0)

    _arrow(ax, (13.86, 4.02), (7.62, 2.68), color=S.GREEN, rad=0.08,
           label="监督", label_xy=(11.4, 3.23))
    ax.plot([0.72, 1.35], [0.25, 0.25], color=S.GREEN, lw=1.4)
    ax.text(1.47, 0.25, "标签 / 训练流", va="center", fontsize=6.7, color=S.NEUTRAL)
    ax.plot([2.65, 3.28], [0.25, 0.25], color=S.ORANGE, lw=1.4, ls=(0, (3, 2)))
    ax.text(3.40, 0.25, "未见件推理流", va="center", fontsize=6.7, color=S.NEUTRAL)

    print("SAVED", S.save(fig, "fig01_framework"))


if __name__ == "__main__":
    main()
