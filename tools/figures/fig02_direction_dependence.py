#!/usr/bin/env python3
"""图 2 支撑接触区定义与构建方向依赖。"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


HI_RGB = (0.867, 0.518, 0.322)
HI = S.ORANGE
INK = "#263238"


def _score_panel(ax, scores, mask, label, count, total):
    bins = np.linspace(-1, 1, 27)
    ax.hist(scores[~mask], bins=bins, color="#D9DCDF", edgecolor="white", linewidth=0.35,
            label="非接触面")
    ax.hist(scores[mask], bins=bins, color=HI, edgecolor="white", linewidth=0.35,
            label="支撑接触面")
    threshold = -np.cos(np.radians(45.0))
    ax.axvspan(-1, threshold, color=HI, alpha=0.09, lw=0)
    ax.axvline(threshold, color=INK, lw=1.1, ls=(0, (3, 2)))
    ax.text(threshold + 0.025, ax.get_ylim()[1] * 0.88, r"$-\cos45^{\circ}$", fontsize=7.2,
            color=INK, ha="left", va="top")
    ax.text(0.02, 0.88, f"{label}:  {count:,} / {total:,} faces",
            transform=ax.transAxes, fontsize=8, weight="bold", color=INK)
    ax.set_xlim(-1, 1)
    ax.set_xlabel(r"法向分数  $\mathbf{n}\!\cdot\!\hat{\mathbf{d}}$", fontsize=8)
    ax.set_ylabel("面数", fontsize=8)
    ax.grid(axis="y", color="#E7E8E9", lw=0.55)
    ax.set_axisbelow(True)
    ax.spines["left"].set_color("#B5BABD")
    ax.spines["bottom"].set_color("#B5BABD")


def main():
    from support_accessibility.data.overhang import face_normals_centroids, support_contact_faces

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    ap.add_argument("--name", default="23954_a8c09819_0000")
    ap.add_argument("--zoom", type=float, default=1.4)
    a = ap.parse_args()

    loaded = D.load_fusion_mesh(a.name, a.root)
    if loaded is None:
        raise FileNotFoundError(f"Fusion design not found: {a.name!r} under {a.root!r}")
    Vn, F, _occ, _lo, _pitch = loaded
    normals, _centroids = face_normals_centroids(Vn, F)
    configs = [
        (np.array([0.0, 0.0, 1.0]), r"$\mathbf{d}_1=+Z$", "竖直构建"),
        (np.array([0.0, 1.0, 0.0]), r"$\mathbf{d}_2=+Y$", "侧卧构建"),
    ]
    contacts = [support_contact_faces(Vn, F, d) for d, _lab, _desc in configs]

    fig = plt.figure(figsize=(8.0, 6.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.2, 1.18], hspace=0.06, wspace=0.08,
                          left=0.06, right=0.98, top=0.89, bottom=0.15)
    image_axes = []
    for j, ((d, lab, desc), sc) in enumerate(zip(configs, contacts)):
        ax = fig.add_subplot(gs[0, j])
        image_axes.append(ax)
        img = D.render_mesh_faces_arr(Vn, F, sc.indices, d=d, zoom=a.zoom, hi_rgb=HI_RGB,
                                      base_opacity=0.27, wsize=(1000, 900))
        ax.imshow(img)
        ax.axis("off")
        ax.text(0.02, 0.98, f"({'ab'[j]})  {lab}", transform=ax.transAxes, va="top", ha="left",
                fontsize=11, weight="bold", color=INK)
        ax.text(0.02, 0.90, desc, transform=ax.transAxes, va="top", ha="left",
                fontsize=8, color=S.NEUTRAL)
        ax.text(0.98, 0.04, f"|S| = {len(sc.indices):,} faces", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8.2, weight="bold", color=HI,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#E3E3E3", alpha=0.92))

        score = normals @ d
        mask = np.zeros(len(F), dtype=bool)
        mask[sc.indices] = True
        hist_ax = fig.add_subplot(gs[1, j])
        _score_panel(hist_ax, score, mask, lab, len(sc.indices), len(F))

    idx0 = set(contacts[0].indices.tolist())
    idx1 = set(contacts[1].indices.tolist())
    union = len(idx0 | idx1)
    overlap = len(idx0 & idx1)
    jaccard = overlap / union if union else 1.0
    fig.suptitle("同一零件的支撑接触区随构建方向改变", x=0.06, y=0.975,
                 ha="left", fontsize=13, weight="bold", color=INK)
    fig.text(0.06, 0.925,
             r"$S(P,\mathbf{d})=\{f\in F:\mathbf{n}_f\!\cdot\!\hat{\mathbf{d}}<-\cos\theta_c\}$"
             r"   ·   $\theta_c=45^{\circ}$   ·   外法向一致缠绕",
             fontsize=8.4, color=S.NEUTRAL)
    fig.text(0.50, 0.055, f"方向间接触面 Jaccard = {jaccard:.3f}   ({overlap:,} shared / {union:,} union)",
             ha="center", fontsize=8.2, color=INK,
             bbox=dict(boxstyle="round,pad=0.32", fc="#F5F6F6", ec="#D7DADB"))
    handles = [
        Patch(facecolor=HI, edgecolor="none", label=r"支撑接触区 $S(P,\mathbf{d})$"),
        Patch(facecolor="#D9DCDF", edgecolor="none", label="其余表面"),
        Line2D([0], [0], color="black", lw=1.6, marker=">", markevery=[1], label=r"构建方向 $+\mathbf{d}$"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.092), ncol=3,
               frameon=False, fontsize=7.7, handlelength=1.8, columnspacing=1.8)
    print("SAVED", S.save(fig, "fig02_direction_dependence"))


if __name__ == "__main__":
    main()
