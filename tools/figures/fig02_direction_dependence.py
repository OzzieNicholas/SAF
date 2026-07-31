#!/usr/bin/env python3
"""Figure 2. The real support-contact surface changes with build direction."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


def main():
    from support_accessibility.data.overhang import support_contact_faces

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    loaded = D.load_fusion_mesh(X.FIG02.name, args.root)
    if loaded is None:
        raise FileNotFoundError(f"Missing Fusion mesh: {X.FIG02.name}")
    Vn, F, _occ, _lo, _pitch = loaded
    directions = (np.array([0., 0., 1.]), np.array([0., 1., 0.]))
    contact = [support_contact_faces(Vn, F, direction) for direction in directions]
    names = (r"$\mathbf{d}_1=+Z$", r"$\mathbf{d}_2=+Y$")
    # Canonical normal-facing views reveal each downward surface without relying
    # on whole-model transparency.  The viewpoint is explicitly tied to d.
    centre = Vn.mean(axis=0)
    span = float(np.linalg.norm(Vn.max(axis=0) - Vn.min(axis=0)))
    cameras = []
    for direction in directions:
        up = np.array([0., 1., 0.]) if abs(direction[2]) > .5 else np.array([0., 0., 1.])
        cameras.append((centre - direction * 2.1 * span, centre, up))
    images = [D.render_mesh_faces_arr(Vn, F, entry.indices, d=direction, cpos=camera, zoom=1.12,
                                      wsize=(1500, 1200))
              for entry, direction, camera in zip(contact, directions, cameras)]
    first, second = set(contact[0].indices.tolist()), set(contact[1].indices.tolist())
    union, overlap = len(first | second), len(first & second)
    jaccard = overlap / union if union else 1.0

    fig, axes = plt.subplots(1, 2, figsize=S.double_column(92), gridspec_kw={"wspace": .025})
    for index, (axis, image, entry, name) in enumerate(zip(axes, images, contact, names)):
        axis.imshow(image); axis.axis("off")
        S.panel_label(axis, f"({chr(97 + index)})  {name}")
        axis.text(.50, .01, f"{len(entry.indices):,} 个接触三角面", transform=axis.transAxes,
                  ha="center", va="bottom", fontsize=7.7, color=S.INK,
                  bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.8, "alpha": .92})
    fig.legend([Patch(fc=S.ORANGE, ec="none"), Patch(fc=S.PART, ec="none")],
               ["支撑接触区", "其余零件表面"], loc="lower center", ncol=2,
               bbox_to_anchor=(.5, .015), frameon=False, fontsize=7.5)
    fig.text(.5, .115, f"同一零件：两个构建方向的接触面 Jaccard = {jaccard:.3f}",
             ha="center", fontsize=7.7, color=S.NEUTRAL)
    fig.subplots_adjust(left=.015, right=.985, bottom=.20, top=.93)
    print("SAVED", S.save(fig, "fig02_direction_dependence"))


if __name__ == "__main__":
    main()
