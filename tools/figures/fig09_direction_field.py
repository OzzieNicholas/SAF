#!/usr/bin/env python3
"""Figure 9. Fixed D-020 direction field and held-out Top-1 recommendation."""
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
from matplotlib.patches import Circle, Patch  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CMAP = mcolors.LinearSegmentedColormap.from_list("blocked_probability", [S.ACC, "#F5F5F3", S.INACC])


def _coordinates(directions):
    azimuth = np.arctan2(directions[:, 1], directions[:, 0])
    radius = np.arccos(np.clip(-directions[:, 2], 0, 1)) / (np.pi / 2)
    return radius * np.cos(azimuth), radius * np.sin(azimuth)


def _disk(axis, title):
    for radius, width in ((1, .9), (2 / 3, .45), (1 / 3, .45)):
        axis.add_patch(Circle((0, 0), radius, fill=False,
                              ec=S.PART_EDGE if radius == 1 else "#D8DCDE", lw=width))
    axis.scatter([0], [0], marker="+", s=34, color=S.NEUTRAL, zorder=3)
    axis.set_xlim(-1.08, 1.08); axis.set_ylim(-1.08, 1.08)
    axis.set_aspect("equal"); axis.axis("off")
    axis.set_title(title, loc="left", fontsize=8.4, fontweight="bold", pad=3)


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility.oracle import SupportAccessibilityOracle

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    checkpoint = torch.load(os.path.join(ROOT, "runs", "figures", "ckpt_dir.pt"),
                            map_location="cpu", weights_only=False)
    showcase = checkpoint.get("showcase", {})
    if (checkpoint.get("label_semantics") != "d020_refined"
            or showcase.get("name") != X.FIG09.name
            or int(showcase.get("idx", -1)) != X.FIG09_POINT_INDEX):
        raise RuntimeError("Figure 9 requires the fixed D-020-refined showcase")
    X.assert_checkpoint_holdout(checkpoint, X.FIG09, "Figure 9")
    models, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    model = {item.name: item for item in models}[X.FIG09.name]
    index = X.FIG09_POINT_INDEX
    V, F, occupancy, lo, pitch = D.load_fusion_mesh(X.FIG09.name, args.root)
    if occupancy.shape != model.occ.shape or not np.array_equal(occupancy, np.asarray(model.occ, bool)):
        raise RuntimeError("Figure 9 raw occupancy mismatch")
    directions = np.asarray(checkpoint["dirs"], float)
    oracle = SupportAccessibilityOracle(model.occ, {"n_directions": checkpoint["n_directions"]},
                                        mesh=(V, F, lo, pitch))
    viable = oracle.direction_labels(model.points[index], model.radius)
    network = ConvONetLite(out_dim=int(checkpoint["D"])); network.load_state_dict(checkpoint["state_dict"]); network.eval()
    with torch.no_grad():
        tensor = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape)
        probability = torch.sigmoid(network(
            tensor, to_grid_coords(model.points[index:index + 1], model.occ.shape)
        )).numpy().ravel()
    prediction = probability >= .5
    agreement = float((prediction == (~viable)).mean())
    top1 = int(np.argmin(probability))
    if not (.30 <= viable.mean() <= .60 and viable[top1] and agreement >= .85):
        raise RuntimeError("Figure 9 showcase constraints no longer hold")
    x, y = _coordinates(directions)
    point_world = np.asarray(lo) + (np.asarray(model.points[index]) + .5) * pitch
    direction = directions[top1] / np.linalg.norm(directions[top1])
    render = D.render_dir_arrow_arr(V, F, point_world, direction,
                                    cpos=D.underside_camera(V),
                                    zoom=1.42,
                                    wsize=(1900, 1350))

    fig = plt.figure(figsize=S.double_column(78))
    grid = fig.add_gridspec(1, 3, width_ratios=(1, 1, 1.32), left=.035, right=.94,
                            bottom=.14, top=.91, wspace=.12)
    truth = fig.add_subplot(grid[0, 0]); _disk(truth, "(a) D-020 几何判定器")
    truth.scatter(x[viable], y[viable], s=28, c=S.ACC, edgecolors="white", linewidths=.35)
    truth.scatter(x[~viable], y[~viable], s=28, c=S.INACC, edgecolors="white", linewidths=.35)
    predicted = fig.add_subplot(grid[0, 1]); _disk(predicted, f"(b) 网络预测 · 一致率 {agreement:.1%}")
    predicted.scatter(x, y, s=28, c=probability, cmap=CMAP, vmin=0, vmax=1,
                      edgecolors="white", linewidths=.35)
    cad = fig.add_subplot(grid[0, 2]); S.imshow_cad(cad, render)
    cad.set_title("(c) Top-1 推荐逼近方向", loc="left", fontsize=8.4, fontweight="bold", pad=3)
    cad.annotate("", xy=(.43, .52), xytext=(.90, .18), xycoords="axes fraction",
                 arrowprops={"arrowstyle": "-|>", "mutation_scale": 13,
                             "lw": 3.8, "color": "white"})
    cad.annotate("", xy=(.43, .52), xytext=(.90, .18), xycoords="axes fraction",
                 arrowprops={"arrowstyle": "-|>", "mutation_scale": 12,
                             "lw": 2.1, "color": S.ACC})
    fig.text(.035, .075, "圆心：竖直向下  ·  圆周：水平逼近", fontsize=7.5, color=S.NEUTRAL)
    fig.text(.75, .075, f"query #{index}  ·  可达方向 {viable.mean():.1%}",
             ha="center", fontsize=7.5, color=S.INK)
    bar_axis = fig.add_axes([.955, .28, .013, .44])
    mapper = plt.cm.ScalarMappable(cmap=CMAP, norm=mcolors.Normalize(0, 1)); mapper.set_array([])
    bar = fig.colorbar(mapper, cax=bar_axis); bar.set_ticks([0, .5, 1]); bar.ax.tick_params(labelsize=7.5)
    bar_axis.set_title("被挡\n概率", fontsize=7.5, pad=2)
    fig.legend([Patch(fc=S.ACC), Patch(fc=S.INACC)], ["可达", "被挡"], ncol=2,
               loc="lower center", bbox_to_anchor=(.43, .005), frameon=False)
    print("SAVED", S.save(fig, "fig09_direction_field"))


if __name__ == "__main__":
    main()
