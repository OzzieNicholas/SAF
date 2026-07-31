#!/usr/bin/env python3
"""Figure 9. D-020 directional field and a held-out Top-1 approach recommendation."""
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
CMAP = mcolors.LinearSegmentedColormap.from_list("blocked_probability", [S.ACC, "#F0F1F1", S.INACC])


def _disk_coordinates(directions):
    azimuth = np.arctan2(directions[:, 1], directions[:, 0])
    radius = np.arccos(np.clip(-directions[:, 2], 0, 1)) / (np.pi / 2)
    return radius * np.cos(azimuth), radius * np.sin(azimuth)


def _disk_axis(axis, title):
    for radius, lw in ((1.0, .9), (2 / 3, .45), (1 / 3, .45)):
        axis.add_patch(Circle((0, 0), radius, fc="none", ec=S.NEUTRAL if radius == 1 else "#D9DDDF", lw=lw))
    axis.scatter([0], [0], marker="+", s=38, color=S.NEUTRAL, zorder=3)
    axis.text(0, -1.18, "圆心：竖直向下；边缘：水平", ha="center", va="top", fontsize=7.5, color=S.NEUTRAL)
    axis.set_xlim(-1.15, 1.15); axis.set_ylim(-1.28, 1.15); axis.set_aspect("equal"); axis.axis("off")
    axis.set_title(title, loc="left", fontsize=8.4, fontweight="bold", pad=3)


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility.oracle import SupportAccessibilityOracle

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    checkpoint = torch.load(os.path.join(ROOT, "runs", "figures", "ckpt_dir.pt"), map_location="cpu",
                            weights_only=False)
    if checkpoint.get("label_semantics") != "d020_refined":
        raise RuntimeError("Figure 9 requires a D-020-refined checkpoint; run _train_dir_ckpt.py --root first")
    showcase = checkpoint.get("showcase")
    if not showcase:
        raise RuntimeError("D-020 directional checkpoint has no deterministic held-out showcase")
    example = X.Example("fusion", showcase["name"], "Fusion 留出件", 1.48, -14., 7.)
    X.assert_checkpoint_holdout(checkpoint, example, "Figure 9")
    models, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    model = {item.name: item for item in models}[example.name]
    index = int(showcase["idx"])
    mesh = D.load_fusion_mesh(example.name, args.root)
    if mesh is None:
        raise FileNotFoundError(f"Missing Fusion mesh for Figure 9: {example.name}")
    Vn, F, occupancy, lo, pitch = mesh
    if occupancy.shape != model.occ.shape or not np.array_equal(occupancy, np.asarray(model.occ, bool)):
        raise RuntimeError("Figure 9 mesh occupancy does not match its processed held-out item")
    directions = np.asarray(checkpoint["dirs"], float)
    oracle = SupportAccessibilityOracle(model.occ, {"n_directions": int(checkpoint["n_directions"])},
                                        mesh=(Vn, F, lo, pitch))
    viable = oracle.direction_labels(model.points[index], model.radius)
    network = ConvONetLite(out_dim=int(checkpoint["D"])); network.load_state_dict(checkpoint["state_dict"]); network.eval()
    with torch.no_grad():
        occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape)
        coords = to_grid_coords(model.points[index:index + 1], model.occ.shape)
        blocked_probability = torch.sigmoid(network(occ, coords)).numpy().ravel()
    predicted = blocked_probability >= .5
    agreement = float((predicted == (~viable)).mean())
    top1 = int(np.argmin(blocked_probability))
    if not (.30 <= viable.mean() <= .60 and viable[top1] and agreement >= .85):
        raise RuntimeError("Stored showcase no longer satisfies mixed-direction, Top-1, and agreement constraints")
    x, y = _disk_coordinates(directions)
    point_world = np.asarray(lo) + (np.asarray(model.points[index]) + .5) * float(pitch)
    local = D.render_dir_arrow_arr(Vn, F, point_world, directions[top1], zoom=example.zoom,
                                   azimuth=example.azimuth, elevation=example.elevation, wsize=(1100, 900))

    fig = plt.figure(figsize=S.double_column(72))
    grid = fig.add_gridspec(1, 3, width_ratios=(1, 1, 1.16), wspace=.12,
                            left=.035, right=.93, bottom=.13, top=.91)
    truth = fig.add_subplot(grid[0, 0]); _disk_axis(truth, "(a) D-020 几何判定器")
    truth.scatter(x[viable], y[viable], s=27, c=S.ACC, edgecolors="white", linewidths=.35, zorder=4)
    truth.scatter(x[~viable], y[~viable], s=27, c=S.INACC, edgecolors="white", linewidths=.35, zorder=4)
    prediction_axis = fig.add_subplot(grid[0, 1]); _disk_axis(prediction_axis, f"网络预测（一致率 {agreement:.0%}）")
    prediction_axis.scatter(x, y, s=27, c=blocked_probability, cmap=CMAP, vmin=0, vmax=1,
                            edgecolors="white", linewidths=.35, zorder=4)
    render = fig.add_subplot(grid[0, 2]); render.imshow(local); render.axis("off")
    render.set_title("(b) Top-1 推荐逼近方向", loc="left", fontsize=8.4, fontweight="bold", pad=3)
    render.text(.5, .02, f"{example.name}  |  可达方向 {viable.mean():.0%}", transform=render.transAxes,
                ha="center", va="bottom", fontsize=7.5, color=S.INK,
                bbox={"fc": "white", "ec": "none", "pad": 1.5, "alpha": .9})
    colourbar_axis = fig.add_axes([.945, .30, .014, .42])
    mapper = plt.cm.ScalarMappable(cmap=CMAP, norm=mcolors.Normalize(0, 1)); mapper.set_array([])
    colourbar = fig.colorbar(mapper, cax=colourbar_axis); colourbar.set_ticks([0, .5, 1])
    colourbar.set_ticklabels(["0", ".5", "1"]); colourbar.ax.tick_params(labelsize=7.5)
    colourbar_axis.text(-.72, .5, "被挡概率", transform=colourbar_axis.transAxes, rotation=90,
                        ha="center", va="center", fontsize=7.5, color=S.INK)
    fig.legend([Patch(fc=S.ACC), Patch(fc=S.INACC)], ["可达方向", "被挡方向"],
               loc="lower left", bbox_to_anchor=(.04, .008), frameon=False, ncol=2, fontsize=7.5)
    print("SAVED", S.save(fig, "fig09_direction_field"))


if __name__ == "__main__":
    main()
