#!/usr/bin/env python3
"""Figure 1. Auditable SAF label, point-query, and directional-query chains."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PROB_CMAP = mcolors.LinearSegmentedColormap.from_list("blocked", [S.ACC, "#F5F5F3", S.INACC])


def _arrow(fig, left, right, dashed=False):
    a, b = left.get_position(), right.get_position()
    fig.add_artist(FancyArrowPatch((a.x1 + .003, (a.y0 + a.y1) / 2),
                                   (b.x0 - .003, (b.y0 + b.y1) / 2),
                                   transform=fig.transFigure, arrowstyle="-|>", mutation_scale=8,
                                   lw=.9, color=S.NEUTRAL,
                                   linestyle=(0, (3, 2)) if dashed else "-"))


def _stage_title(ax, title, detail=""):
    ax.set_title(title, fontsize=7.7, color=S.INK, pad=2, fontweight="bold")
    if detail:
        ax.text(.5, -.04, detail, transform=ax.transAxes, ha="center", va="top",
                fontsize=7.5, color=S.NEUTRAL, clip_on=False)


def _edt(ax):
    y, x = np.mgrid[-1:1:180j, -1:1:220j]
    solid = (np.abs(x) < .62) & (np.abs(y) < .28)
    distance = np.hypot(np.maximum(np.abs(x) - .62, 0), np.maximum(np.abs(y) - .28, 0))
    ax.imshow(distance, cmap="Blues", origin="lower", extent=(0, 1, 0, 1))
    ax.add_patch(Rectangle((.19, .36), .62, .28, fc=S.PART_DARK, ec=S.PART_EDGE, lw=.7))
    ax.plot([.72, .58, .43], [.34, .18, .04], "o--", color=S.ACC, ms=2.8, lw=.9)
    ax.add_patch(Circle((.58, .18), .10, fill=False, ec=S.ACC, lw=1.0))
    ax.set_axis_off(); _stage_title(ax, "距离场 + ray-march", r"每方向净空 $c_i$")


def _capsule(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Polygon([(0, .15), (.58, .28), (1, .18), (1, 0), (0, 0)],
                         fc=S.PART, ec=S.PART_EDGE, lw=.8))
    ax.plot([.46, .75], [.30, .83], color=S.ORANGE, lw=10, alpha=.30, solid_capstyle="round")
    ax.plot([.46, .75], [.30, .83], color="#A9562D", lw=1.0)
    ax.scatter([.46], [.30], s=18, c=S.INK, zorder=4)
    ax.scatter([.62], [.25], marker="x", s=30, c=S.INACC, lw=1.4, zorder=5)
    _stage_title(ax, "边界带精确细化", "胶囊-三角求交")


def _network(ax, out_dim):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    blocks = ((.05, .23, S.PALE_GREY, S.UNC, "$O$"),
              (.385, .23, S.PALE_BLUE, S.ACC, "$F(p)$"),
              (.72, .23, S.PALE_ORANGE, S.ORANGE, "MLP"))
    for x, width, fill, edge, label in blocks:
        ax.add_patch(Rectangle((x, .39), width, .28, fc=fill, ec=edge, lw=.8))
        ax.text(x + width / 2, .53, label, ha="center", va="center", fontsize=7.5)
    for start, end in ((.28, .385), (.615, .72)):
        ax.add_patch(FancyArrowPatch((start, .53), (end, .53), arrowstyle="-|>",
                                     mutation_scale=7, lw=.7, color=S.NEUTRAL))
    ax.text(.5, .16, f"编码 · 三线性采样 · {out_dim} logit", ha="center",
            fontsize=7.5, color=S.NEUTRAL)


def _disk(ax, directions, values, categorical=False):
    az = np.arctan2(directions[:, 1], directions[:, 0])
    radius = np.arccos(np.clip(-directions[:, 2], 0, 1)) / (np.pi / 2)
    x, y = radius * np.cos(az), radius * np.sin(az)
    ax.add_patch(Circle((0, 0), 1, fill=False, ec=S.PART_EDGE, lw=.8))
    if categorical:
        colours = np.where(values[:, None], np.asarray(mcolors.to_rgb(S.ACC)),
                           np.asarray(mcolors.to_rgb(S.INACC)))
        ax.scatter(x, y, c=colours, s=12, edgecolors="white", linewidths=.25)
    else:
        ax.scatter(x, y, c=values, cmap=PROB_CMAP, vmin=0, vmax=1, s=12,
                   edgecolors="white", linewidths=.25)
    ax.set_xlim(-1.08, 1.08); ax.set_ylim(-1.08, 1.08); ax.set_aspect("equal"); ax.axis("off")


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility.oracle import SupportAccessibilityOracle

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    models, _ = load_dataset(D.processed_dataset("fusion360_full"))
    by_name = {model.name: model for model in models}

    label_model = by_name[X.FIG01_LABEL.name]
    V, F, occ, lo, pitch = D.load_fusion_mesh(X.FIG01_LABEL.name, args.root)
    mapping = D.map_processed_faces(V, F, occ, lo, pitch, label_model.points)
    label_rgb = np.tile(np.asarray(S.ACC_RGB), (len(label_model.labels), 1))
    label_rgb[np.asarray(label_model.labels, bool)] = S.INACC_RGB
    raw = D.render_mesh_technical_arr(V, F, zoom=X.FIG01_LABEL.zoom,
                                      azimuth=X.FIG01_LABEL.azimuth, elevation=X.FIG01_LABEL.elevation)
    support_camera = D.underside_camera(V)
    contact = D.render_face_field_arr(V, F, mapping.face_indices,
                                      np.tile(mcolors.to_rgb(S.ORANGE), (len(mapping.face_indices), 1)),
                                      cpos=support_camera, zoom=1.10)
    labelled = D.render_face_field_arr(V, F, mapping.face_indices, label_rgb,
                                       cpos=support_camera, zoom=1.10)

    point_checkpoint = torch.load(os.path.join(ROOT, "artifacts", "cache", "figures", "ckpt_point.pt"),
                                  map_location="cpu", weights_only=False)
    X.assert_checkpoint_holdout(point_checkpoint, X.FIG01_POINT, "Figure 1")
    point_model = by_name[X.FIG01_POINT.name]
    network = ConvONetLite(); network.load_state_dict(point_checkpoint["state_dict"]); network.eval()
    with torch.no_grad():
        tensor = torch.as_tensor(np.asarray(point_model.occ, np.float32)).view(1, 1, *point_model.occ.shape)
        probability = torch.sigmoid(network(tensor, to_grid_coords(point_model.points, point_model.occ.shape))).numpy()
    Vp, Fp, occp, lop, pitchp = D.load_fusion_mesh(X.FIG01_POINT.name, args.root)
    point_map = D.map_processed_faces(Vp, Fp, occp, lop, pitchp, point_model.points)
    point_camera = D.underside_camera(Vp)
    predicted = D.render_face_field_arr(Vp, Fp, point_map.face_indices, PROB_CMAP(probability)[:, :3],
                                        cpos=point_camera, zoom=1.10)

    direction_checkpoint = torch.load(os.path.join(ROOT, "artifacts", "cache", "figures", "ckpt_dir.pt"),
                                      map_location="cpu", weights_only=False)
    showcase = direction_checkpoint.get("showcase", {})
    if (direction_checkpoint.get("label_semantics") != "d020_refined"
            or showcase.get("name") != X.FIG09.name or int(showcase.get("idx", -1)) != X.FIG09_POINT_INDEX):
        raise RuntimeError("Figure 1 requires the fixed D-020 directional showcase")
    X.assert_checkpoint_holdout(direction_checkpoint, X.FIG09, "Figure 1")
    direction_model = by_name[X.FIG09.name]
    Vd, Fd, occd, lod, pitchd = D.load_fusion_mesh(X.FIG09.name, args.root)
    oracle = SupportAccessibilityOracle(direction_model.occ,
                                        {"n_directions": direction_checkpoint["n_directions"]},
                                        mesh=(Vd, Fd, lod, pitchd))
    viable = oracle.direction_labels(direction_model.points[X.FIG09_POINT_INDEX], direction_model.radius)
    dnet = ConvONetLite(out_dim=int(direction_checkpoint["D"])); dnet.load_state_dict(direction_checkpoint["state_dict"]); dnet.eval()
    with torch.no_grad():
        tensor = torch.as_tensor(np.asarray(direction_model.occ, np.float32)).view(1, 1, *direction_model.occ.shape)
        coords = to_grid_coords(direction_model.points[X.FIG09_POINT_INDEX:X.FIG09_POINT_INDEX + 1], direction_model.occ.shape)
        blocked = torch.sigmoid(dnet(tensor, coords)).numpy().ravel()
    directions = np.asarray(direction_checkpoint["dirs"], float)
    top1 = int(np.argmin(blocked))
    point_world = np.asarray(lod) + (np.asarray(direction_model.points[X.FIG09_POINT_INDEX]) + .5) * pitchd
    recommended = D.render_dir_arrow_arr(Vd, Fd, point_world, directions[top1],
                                         cpos=D.underside_camera(Vd), zoom=1.15,
                                         wsize=(1500, 1000))

    fig = plt.figure(figsize=S.double_column(112))
    grid = fig.add_gridspec(3, 6, width_ratios=(.36, 1, 1, 1, 1, 1.08),
                            height_ratios=(1.08, .88, .88), left=.025, right=.99,
                            bottom=.055, top=.965, wspace=.22, hspace=.48)
    lane_text = (("(a)", "几何标签"), ("(b)", "点级查询"), ("(c)", "方向查询"))
    for row, (letter, title) in enumerate(lane_text):
        ax = fig.add_subplot(grid[row, 0]); ax.axis("off")
        ax.text(.02, .70, letter, fontsize=8.8, fontweight="bold", color=S.INK)
        ax.text(.02, .46, title, fontsize=8.0, fontweight="bold", color=S.INK)

    top = [fig.add_subplot(grid[0, i]) for i in range(1, 6)]
    S.imshow_cad(top[0], raw); _stage_title(top[0], "真实 CAD", "归一化网格")
    S.imshow_cad(top[1], contact, semantic=True); _stage_title(top[1], "支撑接触区", r"$S(P,\mathbf{d})$")
    _edt(top[2]); _capsule(top[3])
    S.imshow_cad(top[4], labelled, semantic=True); _stage_title(top[4], "几何监督", "蓝：可达  红：不可达")
    for a, b in zip(top[:-1], top[1:]): _arrow(fig, a, b)

    point_axes = [fig.add_subplot(grid[1, i]) for i in range(1, 6)]
    S.imshow_cad(point_axes[0], labelled, semantic=True); _stage_title(point_axes[0], "训练标签", "多零件面级监督")
    _network(point_axes[1], 1); _stage_title(point_axes[1], "点级 ConvONet", r"独立参数 $\theta_p$")
    point_axes[2].set_xlim(0, 1); point_axes[2].set_ylim(0, 1); point_axes[2].axis("off")
    point_axes[2].add_patch(Rectangle((.16, .22), .68, .56, fc=S.PALE_GREY, ec=S.UNC, lw=.8))
    for value in np.linspace(.25, .75, 5):
        point_axes[2].plot([.16, .84], [value, value], color="white", lw=.45)
        point_axes[2].plot([value, value], [.22, .78], color="white", lw=.45)
    point_axes[2].scatter([.58], [.44], s=52, c=S.INACC, edgecolors="white", zorder=3)
    _stage_title(point_axes[2], "未见件查询点", r"$p\in S(P,\mathbf{d})$")
    point_axes[3].axis("off"); point_axes[3].text(.5, .53, r"$\sigma(q_{\theta_p})$", ha="center", fontsize=12, color=S.INACC)
    _stage_title(point_axes[3], "不可达概率", "每点 1 个 logit")
    S.imshow_cad(point_axes[4], predicted, semantic=True); _stage_title(point_axes[4], "真实网络输出", X.FIG01_POINT.name)
    for a, b in zip(point_axes[:-1], point_axes[1:]): _arrow(fig, a, b, dashed=True)

    direction_axes = [fig.add_subplot(grid[2, i]) for i in range(1, 6)]
    _disk(direction_axes[0], directions, viable, categorical=True); _stage_title(direction_axes[0], "D-020 方向标签", "64 个固定方向")
    _network(direction_axes[1], 64); _stage_title(direction_axes[1], "方向级 ConvONet", r"独立参数 $\theta_d$")
    _disk(direction_axes[2], directions, blocked); _stage_title(direction_axes[2], "被挡概率场", "每方向 1 个 logit")
    direction_axes[3].axis("off"); direction_axes[3].text(.5, .55, r"$\arg\min_i\;\hat b_i$", ha="center", fontsize=11, color=S.ACC)
    _stage_title(direction_axes[3], "Top-1 筛选", "最低被挡概率")
    S.imshow_cad(direction_axes[4], recommended); _stage_title(direction_axes[4], "推荐逼近方向", X.FIG09.name)
    for a, b in zip(direction_axes[:-1], direction_axes[1:]): _arrow(fig, a, b, dashed=True)
    print("SAVED", S.save(fig, "fig01_framework"))


if __name__ == "__main__":
    main()
