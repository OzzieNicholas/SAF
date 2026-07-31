#!/usr/bin/env python3
"""Figure 6. Real CAD evidence that support-contact amount is not accessibility."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _label_rgb(labels):
    result = np.tile(np.asarray(S.ACC_RGB), (len(labels), 1))
    result[np.asarray(labels, bool)] = S.INACC_RGB
    return result


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    models, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    by_name = {model.name: model for model in models}
    pair = [by_name[item.name] for item in X.FIG06_PAIR]
    meshes = [D.load_fusion_mesh(item.name, args.root) for item in X.FIG06_PAIR]
    if any(mesh is None for mesh in meshes):
        raise FileNotFoundError("Figure 6 requires both curated Fusion meshes")

    images = []
    for item, model, mesh in zip(X.FIG06_PAIR, pair, meshes):
        Vn, F, _occ, lo, pitch = mesh
        centre = Vn.mean(axis=0)
        span = float(np.linalg.norm(Vn.max(axis=0) - Vn.min(axis=0)))
        camera = (centre - np.array([0., 0., 2.1 * span]), centre, np.array([0., 1., 0.]))
        images.append(D.render_mesh_arr(Vn, F, model.points, _label_rgb(model.labels), lo, pitch,
                                        cpos=camera, zoom=1.12, psize=22, wsize=(1100, 900)))
    area, inacc = D.per_model_area_inacc(models)
    rho = E.spearman(area, inacc)

    fig = plt.figure(figsize=S.double_column(78))
    grid = fig.add_gridspec(1, 3, width_ratios=(1, 1, 1.55), wspace=.12,
                            left=.035, right=.985, bottom=.17, top=.93)
    for index, (item, model, image) in enumerate(zip(X.FIG06_PAIR, pair, images)):
        axis = fig.add_subplot(grid[0, index]); axis.imshow(image); axis.axis("off")
        S.panel_label(axis, f"({chr(97 + index)})  {item.label}")
        axis.text(.5, .02, f"{len(model.labels)} 个接触点  |  不可达 {100 * np.mean(model.labels):.1f}%",
                  transform=axis.transAxes, ha="center", va="bottom", fontsize=7.5, color=S.INK,
                  bbox={"fc": "white", "ec": "none", "pad": 1.5, "alpha": .9})
    scatter = fig.add_subplot(grid[0, 2])
    scatter.scatter(area, inacc, s=6, alpha=.18, color=S.ACC, edgecolors="none", rasterized=True)
    for model, colour in zip(pair, (S.ACC, S.INACC)):
        scatter.scatter([len(model.labels)], [np.mean(model.labels)], s=42, c=colour,
                        edgecolors="white", linewidths=.65, zorder=4)
    scatter.set_xscale("log"); scatter.set_ylim(-.03, 1.03)
    scatter.set_xlabel("下朝面计数（支撑面积代理，对数）")
    scatter.set_ylabel("不可达点占比")
    scatter.set_title("(c) 全量 Fusion CAD", loc="left", fontsize=8.4, fontweight="bold")
    scatter.text(.04, .95, f"计数代理 ρ = {rho:.3f}\n真三角面积 ρ = 0.124",
                 transform=scatter.transAxes, va="top", fontsize=7.5, color=S.INK)
    scatter.grid(axis="y"); scatter.set_axisbelow(True)
    print("SAVED", S.save(fig, "fig06_area_vs_access"))


if __name__ == "__main__":
    main()
