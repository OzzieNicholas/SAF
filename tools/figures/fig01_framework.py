#!/usr/bin/env python3
"""Figure 1. End-to-end SAF workflow with real CAD evidence at both ends."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402


def _arrow(ax, x0, y0, x1, y1, colour=S.NEUTRAL, dashed=False):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9,
                                 linewidth=1.0, color=colour,
                                 linestyle=(0, (3, 2)) if dashed else "-"))


def _stage(ax, label, detail, colour=S.INK):
    ax.text(0.5, -0.10, label, transform=ax.transAxes, ha="center", va="top",
            fontsize=8.0, color=colour, fontweight="bold", clip_on=False)
    ax.text(0.5, -0.23, detail, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color=S.NEUTRAL, clip_on=False)


def _network(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    for i, h in enumerate((0.44, 0.63, 0.78)):
        ax.add_patch(Rectangle((0.08 + i * 0.10, 0.50 - h / 2), 0.055, h,
                               fc=S.PALE_BLUE, ec=S.ACC, lw=0.7))
    _arrow(ax, 0.41, 0.50, 0.55, 0.50, S.NEUTRAL)
    for x, h in ((0.59, .26), (.67, .43), (.75, .60)):
        ax.add_patch(Rectangle((x, 0.50 - h / 2), .043, h, fc=S.PALE_ORANGE, ec=S.ORANGE, lw=.6))
    ax.text(.18, .08, "3D-CNN", ha="center", fontsize=7.5, color=S.INK)
    ax.text(.69, .08, "MLP", ha="center", fontsize=7.5, color=S.INK)


def _direction_glyph(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Circle((.5, .54), .31, ec=S.NEUTRAL, fc="none", lw=.8))
    ax.scatter([.37, .47, .64, .58], [.60, .75, .64, .40], s=22,
               c=[S.ACC, S.INACC, S.ACC, S.INACC], edgecolors="white", linewidths=.4)
    ax.text(.5, .08, "方向风险", ha="center", fontsize=7.5, color=S.INK)


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data.overhang import face_normals_centroids, support_contact_faces

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()

    mesh = D.load_fusion_mesh(X.FIG02.name, args.root)
    if mesh is None:
        raise FileNotFoundError(f"Missing Fusion mesh: {X.FIG02.name}")
    Vn, F, _occ, lo, pitch = mesh
    models, _ = load_dataset(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                          "data", "processed", "fusion360_full"))
    model = {item.name: item for item in models}[X.FIG02.name]
    contacts = support_contact_faces(Vn, F, np.array([0.0, 0.0, 1.0]))
    labels = np.asarray(model.labels, bool)
    rgb = np.tile(np.asarray(S.ACC_RGB), (len(labels), 1)); rgb[labels] = S.INACC_RGB

    raw = D.render_mesh_plain(Vn, F, lo, pitch, zoom=1.42, azimuth=X.FIG02.azimuth,
                              elevation=X.FIG02.elevation, wsize=(1000, 700))
    support = D.render_mesh_faces_arr(Vn, F, contacts.indices, d=np.array([0., 0., 1.]),
                                      zoom=1.42, azimuth=X.FIG02.azimuth, elevation=X.FIG02.elevation,
                                      wsize=(1000, 700))
    field = D.render_mesh_arr(Vn, F, model.points, rgb, lo, pitch, zoom=1.42, psize=17,
                              azimuth=X.FIG02.azimuth, elevation=X.FIG02.elevation, wsize=(1000, 700))

    fig = plt.figure(figsize=S.double_column(98))
    grid = fig.add_gridspec(2, 6, height_ratios=(1.0, .92), wspace=.20, hspace=.76,
                            left=.035, right=.985, bottom=.17, top=.93)
    top_axes = [fig.add_subplot(grid[0, i]) for i in (0, 2, 4, 5)]
    top_axes[0].imshow(raw); top_axes[1].imshow(support); top_axes[3].imshow(field)
    for axis in top_axes:
        axis.axis("off")
    _stage(top_axes[0], "输入 CAD 网格", "")
    _stage(top_axes[1], "支撑接触区", r"$S(P,\mathbf{d})$", S.ORANGE)
    _stage(top_axes[2], "两级几何判定", "距离场 + 精确细化")
    _stage(top_axes[3], "监督标签", "蓝：可达；红：不可达")
    top_axes[2].set_xlim(0, 1); top_axes[2].set_ylim(0, 1)
    for y, colour, text in ((.72, S.ACC, "明确无碰撞"), (.50, S.ORANGE, "边界带细化"), (.28, S.INACC, "明确碰撞")):
        top_axes[2].plot([.14, .86], [y, y], color=colour, lw=2.2)
        top_axes[2].text(.5, y + .09, text, ha="center", fontsize=7.5, color=S.INK)
    for left, right in zip(top_axes[:-1], top_axes[1:]):
        p0, p1 = left.get_position(), right.get_position()
        fig.add_artist(FancyArrowPatch((p0.x1 + .006, (p0.y0 + p0.y1) / 2),
                                       (p1.x0 - .006, (p1.y0 + p1.y1) / 2),
                                       transform=fig.transFigure, arrowstyle="-|>", mutation_scale=10,
                                       lw=1.0, color=S.NEUTRAL))

    infer = fig.add_subplot(grid[1, 0]); infer.imshow(raw); infer.axis("off")
    _stage(infer, "未见 CAD", "形状 + 查询点")
    net = fig.add_subplot(grid[1, 2]); _network(net); _stage(net, "形状条件预测网络", "")
    point = fig.add_subplot(grid[1, 4]); point.imshow(field); point.axis("off")
    _stage(point, "点级输出", "不可达概率场", S.INACC)
    direction = fig.add_subplot(grid[1, 5]); _direction_glyph(direction)
    _stage(direction, "方向级输出", "被挡概率", S.INACC)
    for left, right in ((infer, net), (net, point), (point, direction)):
        p0, p1 = left.get_position(), right.get_position()
        fig.add_artist(FancyArrowPatch((p0.x1 + .006, (p0.y0 + p0.y1) / 2),
                                       (p1.x0 - .006, (p1.y0 + p1.y1) / 2),
                                       transform=fig.transFigure, arrowstyle="-|>", mutation_scale=10,
                                       lw=1.0, color=S.NEUTRAL,
                                       linestyle=(0, (3, 2))))
    fig.text(.035, .972, "(a) 几何标签生成", fontsize=8.4, color=S.INK, fontweight="bold")
    fig.text(.035, .505, "(b) 训练后对未见零件推理", fontsize=8.4, color=S.INK, fontweight="bold")
    print("SAVED", S.save(fig, "fig01_framework"))


if __name__ == "__main__":
    main()
