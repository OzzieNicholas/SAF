#!/usr/bin/env python3
"""Figure 7. Three held-out qualitative prediction cases, including cross-domain mesh."""
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
from matplotlib.patches import Patch  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CMAP = mcolors.LinearSegmentedColormap.from_list("blocked_probability", [S.ACC, "#F0F1F1", S.INACC])


def _label_rgb(labels):
    result = np.tile(np.asarray(S.ACC_RGB), (len(labels), 1))
    result[np.asarray(labels, bool)] = S.INACC_RGB
    return result


def _error_rgb(prediction, gold):
    result = np.tile(np.asarray((.72, .74, .75)), (len(gold), 1))
    result[(~prediction) & gold] = mcolors.to_rgb(S.FN)
    result[prediction & (~gold)] = mcolors.to_rgb(S.ORANGE)
    return result


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    parser.add_argument("--thingi-root", default=X.THINGI_ROOT)
    args = parser.parse_args()
    checkpoint = torch.load(os.path.join(ROOT, "runs", "figures", "ckpt_point.pt"), map_location="cpu",
                            weights_only=False)
    network = ConvONetLite(); network.load_state_dict(checkpoint["state_dict"]); network.eval()
    fusion, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    thingi, _ = load_dataset(os.path.join(ROOT, "data", "processed", "thingi_v1"))
    datasets = {"fusion": {model.name: model for model in fusion},
                "thingi": {model.name: model for model in thingi}}

    fig = plt.figure(figsize=S.double_column(132))
    grid = fig.add_gridspec(3, 4, wspace=.025, hspace=.16, left=.09, right=.985, bottom=.055, top=.94)
    headings = ("全局几何", "几何判定器", "网络预测", "误差定位")
    for row, example in enumerate(X.FIG07):
        X.assert_checkpoint_holdout(checkpoint, example, "Figure 7")
        model = datasets[example.source][example.name]
        labels = np.asarray(model.labels, bool)
        with torch.no_grad():
            occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape)
            coords = to_grid_coords(model.points, model.occ.shape)
            probability = torch.sigmoid(network(occ, coords)).numpy().ravel()
        prediction = probability >= .5
        mesh = (D.load_fusion_mesh(example.name, args.root) if example.source == "fusion"
                else D.load_thingi_mesh(example.name, args.thingi_root))
        if mesh is None:
            raise FileNotFoundError(f"Missing raw mesh for Figure 7: {example.name}")
        Vn, F, _occ, lo, pitch = mesh
        images = (
            D.render_mesh_plain(Vn, F, lo, pitch, zoom=example.zoom, azimuth=example.azimuth,
                                elevation=example.elevation, wsize=(900, 680)),
            D.render_mesh_arr(Vn, F, model.points, _label_rgb(labels), lo, pitch, zoom=example.zoom,
                              psize=18, azimuth=example.azimuth, elevation=example.elevation, wsize=(900, 680)),
            D.render_mesh_arr(Vn, F, model.points, CMAP(probability)[:, :3], lo, pitch, zoom=example.zoom,
                              psize=18, azimuth=example.azimuth, elevation=example.elevation, wsize=(900, 680)),
            D.render_mesh_arr(Vn, F, model.points, _error_rgb(prediction, labels), lo, pitch, zoom=example.zoom,
                              psize=22, azimuth=example.azimuth, elevation=example.elevation, wsize=(900, 680)),
        )
        for col, image in enumerate(images):
            axis = fig.add_subplot(grid[row, col]); axis.imshow(image); axis.axis("off")
            if row == 0:
                axis.set_title(headings[col], fontsize=8.4, pad=4)
        label_axis = fig.add_subplot(grid[row, 0], frame_on=False)
        label_axis.set_axis_off()
        label_axis.text(-.01, .5, f"{example.label}\n不可达 {100 * labels.mean():.1f}%",
                        transform=label_axis.transAxes, ha="right", va="center", fontsize=7.5, color=S.INK)
    fig.legend([Patch(fc=S.ACC), Patch(fc=S.INACC), Patch(fc=S.FN), Patch(fc=S.ORANGE)],
               ["可达", "不可达", "FN", "FP"], loc="lower center", ncol=4,
               bbox_to_anchor=(.54, .004), frameon=False, fontsize=7.5)
    print("SAVED", S.save(fig, "fig07_prediction_heatmap"))


if __name__ == "__main__":
    main()
