#!/usr/bin/env python3
"""Figure 2. Build direction changes the real support-contact surface."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Patch  # noqa: E402


def main():
    from support_accessibility.data.overhang import support_contact_faces

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    loaded = D.load_fusion_mesh(X.FIG02.name, args.root)
    if loaded is None:
        raise FileNotFoundError(f"Missing Fusion mesh: {X.FIG02.name}")
    V, F, _occ, _lo, _pitch = loaded
    directions = (np.array([0., 0., 1.]), np.array([0., 1., 0.]))
    contacts = [support_contact_faces(V, F, direction) for direction in directions]
    triangles = V[np.asarray(F, int)]
    areas = .5 * np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0],
                                         triangles[:, 2] - triangles[:, 0]), axis=1)
    total_area = float(areas.sum())
    contact_areas = [float(areas[item.indices].sum()) for item in contacts]
    fractions = [value / total_area for value in contact_areas]
    sets = [set(item.indices.tolist()) for item in contacts]
    jaccard = len(sets[0] & sets[1]) / len(sets[0] | sets[1])

    centre = V.mean(0)
    span = float(np.linalg.norm(V.max(0) - V.min(0)))
    cameras = []
    for direction in directions:
        up = np.array([0., 1., 0.]) if abs(direction[2]) > .5 else np.array([0., 0., 1.])
        cameras.append((centre - direction * 2.1 * span, centre, up))
    orange = np.asarray(mcolors.to_rgb(S.ORANGE))
    directional = [D.render_face_field_arr(V, F, item.indices,
                                            np.tile(orange, (len(item.indices), 1)),
                                            cpos=camera, zoom=1.12, wsize=(1700, 1300))
                   for item, camera in zip(contacts, cameras)]
    global_view = D.render_mesh_technical_arr(V, F, zoom=X.FIG02.zoom,
                                              azimuth=X.FIG02.azimuth,
                                              elevation=X.FIG02.elevation,
                                              wsize=(1800, 1400))

    fig = plt.figure(figsize=S.double_column(92))
    grid = fig.add_gridspec(2, 3, height_ratios=(1, .18), width_ratios=(1, 1.18, 1),
                            left=.035, right=.985, bottom=.12, top=.93, wspace=.10, hspace=.08)
    axes = [fig.add_subplot(grid[0, i]) for i in range(3)]
    S.imshow_cad(axes[0], directional[0], semantic=True)
    S.imshow_cad(axes[1], global_view)
    S.imshow_cad(axes[2], directional[1], semantic=True)
    axes[0].set_title(r"(a) $\mathbf{d}_1=+Z$ · 下视接触面", loc="left", fontsize=8.5, fontweight="bold", pad=3)
    axes[1].set_title("(b) 同一真实 Fusion 零件", loc="left", fontsize=8.5, fontweight="bold", pad=3)
    axes[2].set_title(r"(c) $\mathbf{d}_2=+Y$ · 侧视接触面", loc="left", fontsize=8.5, fontweight="bold", pad=3)
    for axis, label in ((axes[0], "+Z"), (axes[2], "+Y")):
        axis.add_artist(FancyArrowPatch((.10, .90), (.10, .70), transform=axis.transAxes,
                                        arrowstyle="-|>", mutation_scale=11, lw=1.2,
                                        color=S.INK, clip_on=False))
        axis.text(.14, .83, label, transform=axis.transAxes, fontsize=7.5, va="center")

    for col, (area, fraction) in enumerate(zip(contact_areas, fractions)):
        metric = fig.add_subplot(grid[1, col * 2 if False else (0 if col == 0 else 2)])
        metric.set_xlim(0, 1); metric.set_ylim(0, 1); metric.axis("off")
        metric.barh([.55], [fraction], height=.24, color=S.ORANGE)
        metric.barh([.55], [1 - fraction], left=[fraction], height=.24, color=S.PALE_GREY)
        metric.text(.5, .08, f"接触面积 {area:.3f}  ·  表面积占比 {fraction:.1%}",
                    ha="center", fontsize=7.5, color=S.INK)
    centre_metric = fig.add_subplot(grid[1, 1]); centre_metric.axis("off")
    centre_metric.text(.5, .58, f"面集合 Jaccard = {jaccard:.3f}", ha="center",
                       fontsize=8.0, fontweight="bold", color=S.INK)
    centre_metric.text(.5, .12, X.FIG02.name, ha="center", fontsize=7.5, color=S.NEUTRAL)
    fig.legend([Patch(fc=S.ORANGE), Patch(fc=S.PART)], ["支撑接触区", "其余零件表面"],
               ncol=2, loc="lower center", bbox_to_anchor=(.5, .005), frameon=False)
    print("SAVED", S.save(fig, "fig02_direction_dependence"))


if __name__ == "__main__":
    main()
