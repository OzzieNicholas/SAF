#!/usr/bin/env python3
"""图 1 方法总体框架（写作指引 §4.1 / 图1）：横向流程条。

上行 = 几何判定器（离线自动标注，产真值标签）：输入网格→归一→占据栅格→支撑接触区 S(P,d)→两级判定器→标签。
下行 = 形状条件网络（未见件跨模型预测）：网络（双头）→输出（热图/方向评分）。
训练/标注流 = 实线；推理流（新件占据→网络）= 虚线。纯示意（matplotlib 矢量 PDF），无数据依赖。
用法：conda run -n saf python tools/figures/fig01_framework.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch  # noqa: E402


def _box(ax, cx, cy, w, h, text, fc, ec, fs=9.5, sub=None):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.4, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=4, linespacing=1.25)
    if sub:
        ax.text(cx, cy - h / 2 - 0.22, sub, ha="center", va="top", fontsize=6.6,
                color="#555", zorder=4, linespacing=1.2)


def _arrow(ax, xy0, xy1, style="-", color="#333", lw=1.6, rad=0.0, label=None, lxy=None, lfs=8):
    ax.add_patch(FancyArrowPatch(xy0, xy1, arrowstyle="-|>", mutation_scale=14,
                                 lw=lw, color=color, linestyle=style,
                                 connectionstyle=f"arc3,rad={rad}", zorder=2))
    if label:
        ax.text(*(lxy or ((xy0[0] + xy1[0]) / 2, (xy0[1] + xy1[1]) / 2)), label,
                ha="center", va="center", fontsize=lfs, color=color, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.6))


def main():
    fig, ax = plt.subplots(figsize=(11.0, 4.3))
    ax.set_xlim(0, 16.4); ax.set_ylim(0, 7.2); ax.axis("off")

    BLUEF, BLUEE = "#DCE7F2", "#2C6FB2"
    GRAYF, GRAYE = "#ECECEC", "#8A8A8A"
    GREENF, GREENE = "#DCEAE0", "#4E9A63"
    ORF, ORE = "#F6E4D6", "#DD8452"

    yt, w, h = 5.15, 2.28, 1.15
    xs = [1.45, 4.02, 6.59, 9.16, 11.9, 14.7]
    top = [
        ("输入网格\n公开CAD/程序化", GRAYF, GRAYE, None),
        ("归一化\n最长边=1", GRAYF, GRAYE, None),
        ("占据栅格\n缠绕数·res 48", BLUEF, BLUEE, None),
        ("支撑接触区\nS(P,d)·45°下朝", BLUEF, BLUEE, None),
        ("两级几何判定器", GREENF, GREENE, "①距离场腐蚀 ②边界带精确细化"),
        ("几何代理标签\n可达/不可达", GREENF, GREENE, None),
    ]
    for cx, (t, fc, ec, sub) in zip(xs, top):
        _box(ax, cx, yt, w, h, t, fc, ec, sub=sub)
    for i in range(5):
        _arrow(ax, (xs[i] + w / 2, yt), (xs[i + 1] - w / 2, yt))

    yb = 1.55
    _box(ax, 7.7, yb, 3.5, 1.35, "形状条件网络\n3D-CNN + 点查询 · 双头", ORF, ORE, fs=9.5)
    _box(ax, 12.9, yb, 3.0, 1.35, "输出\n接触区热图 / 方向评分", ORF, ORE, fs=9.5)
    _arrow(ax, (7.7 + 3.5 / 2, yb), (12.9 - 3.0 / 2, yb))

    # 训练/标注流（实线）：标签 → 网络（监督）
    _arrow(ax, (xs[5], yt - h / 2), (8.7, yb + 1.35 / 2), rad=-0.18,
           label="监督训练", lxy=(12.4, 3.5))
    # 推理流（虚线）：新件占据栅格 → 网络
    _arrow(ax, (xs[2], yt - h / 2), (6.9, yb + 1.35 / 2), style=(0, (5, 3)), color="#B0562A",
           rad=0.15, label="推理：新件形状条件", lxy=(5.05, 3.25), lfs=8)

    # 分组括号 + 相位标题
    ax.annotate("", xy=(0.25, 6.35), xytext=(15.9, 6.35),
                arrowprops=dict(arrowstyle="-", color=GREENE, lw=1.2,
                                connectionstyle="bar,fraction=0.03"))
    ax.text(8.1, 6.78, "几何判定器 · 离线自动标注（真值）", ha="center", fontsize=10, color=GREENE)
    ax.annotate("", xy=(5.9, 0.55), xytext=(14.45, 0.55),
                arrowprops=dict(arrowstyle="-", color=ORE, lw=1.2,
                                connectionstyle="bar,fraction=-0.05"))
    ax.text(10.2, 0.15, "形状条件网络 · 未见件跨模型预测", ha="center", fontsize=10, color=ORE)

    # 线型图例
    ax.plot([0.4, 1.3], [3.15, 3.15], color="#333", lw=1.6)
    ax.text(1.45, 3.15, "训练 / 标注流", va="center", fontsize=8.2)
    ax.plot([0.4, 1.3], [2.6, 2.6], color="#B0562A", lw=1.6, linestyle=(0, (5, 3)))
    ax.text(1.45, 2.6, "推理流", va="center", fontsize=8.2)

    print("SAVED", S.save(fig, "fig01_framework"))


if __name__ == "__main__":
    main()
