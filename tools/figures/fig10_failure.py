#!/usr/bin/env python3
"""Figure 10. Errors concentrate in marginally viable approach-direction regimes."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "runs", "failure_audit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    args = parser.parse_args()
    with open(os.path.join(AUDIT, "failure.json"), encoding="utf-8") as handle:
        report = json.load(handle)
    order = (("0", "0"), ("1-2", "1–2"), ("3-5", "3–5"), ("6+", "≥6"))
    values = [100 * float(report["error_rate_by_nviable"][key]) for key, _ in order]
    errors = [100 * float(report.get("error_rate_by_nviable_std", {}).get(key, 0)) for key, _ in order]
    shares = [100 * float(report["nviable_share"][key]) for key, _ in order]
    labels = [label for _, label in order]
    colours = [S.UNC, S.INACC, S.INACC, S.UNC]

    artifact = np.load(os.path.join(AUDIT, "fig10_worst.npz"), allow_pickle=True)
    name = str(artifact["name"])
    mesh = D.load_fusion_mesh(name, args.root)
    if mesh is None:
        raise FileNotFoundError(f"Missing audited Fusion mesh: {name}")
    Vn, F, _occ, lo, pitch = mesh
    centre = Vn.mean(axis=0)
    span = float(np.linalg.norm(Vn.max(axis=0) - Vn.min(axis=0)))
    camera = (centre - np.array([0., 0., 2.1 * span]), centre, np.array([0., 1., 0.]))
    global_view = D.render_fp_fn_arr(Vn, F, artifact["points"], artifact["fp"], artifact["fn"], lo, pitch,
                                     cpos=camera, zoom=1.08, psize=40, wsize=(1100, 820))
    local_view = D.render_fp_fn_arr(Vn, F, artifact["points"], artifact["fp"], artifact["fn"], lo, pitch,
                                    cpos=camera, zoom=1.85, psize=56, wsize=(900, 700))

    fig = plt.figure(figsize=S.double_column(86))
    grid = fig.add_gridspec(2, 2, width_ratios=(1.05, 1), height_ratios=(1, .25), wspace=.18, hspace=.10,
                            left=.08, right=.985, bottom=.16, top=.93)
    axis = fig.add_subplot(grid[0, 0])
    x = np.arange(len(labels))
    bars = axis.bar(x, values, width=.62, color=colours, yerr=errors, capsize=3,
                    error_kw={"elinewidth": .8, "ecolor": S.NEUTRAL})
    for bar, value, error in zip(bars, values, errors):
        axis.text(bar.get_x() + bar.get_width() / 2, value + error + .55, f"{value:.1f}%",
                  ha="center", va="bottom", fontsize=7.5)
    axis.axhline(100 * report["error_rate"], color=S.NEUTRAL, ls=(0, (3, 2)), lw=.9)
    axis.set_xticks(x, labels); axis.tick_params(axis="x", labelbottom=False)
    axis.set_ylabel("误判率 (%)")
    axis.set_ylim(0, max(value + error for value, error in zip(values, errors)) * 1.34)
    axis.set_title("(a) 误判集中在勉强/边界可达点", loc="left", fontsize=8.4, fontweight="bold")
    axis.grid(axis="y"); axis.set_axisbelow(True)
    share_axis = fig.add_subplot(grid[1, 0])
    share_axis.bar(x, shares, color=colours, width=.62)
    share_axis.set_xticks(x, labels); share_axis.set_ylim(0, max(shares) * 1.25)
    share_axis.set_ylabel("样本占比 (%)", fontsize=7.5)
    share_axis.set_xlabel(r"每点可达方向数 $n_{\mathrm{viable}}$")
    share_axis.tick_params(axis="both", labelsize=7.5, length=2)
    share_axis.spines["top"].set_visible(False); share_axis.spines["right"].set_visible(False)

    render = fig.add_subplot(grid[:, 1]); render.imshow(global_view); render.axis("off")
    render.set_title("(b) 最坏留出 CAD 案例", loc="left", fontsize=8.4, fontweight="bold", pad=4)
    n_fn, n_fp = int(np.sum(artifact["fn"])), int(np.sum(artifact["fp"]))
    render.text(.5, .02, f"{name}  |  FN {n_fn}  ·  FP {n_fp}", transform=render.transAxes,
                ha="center", va="bottom", fontsize=7.5, color=S.INK,
                bbox={"fc": "white", "ec": "none", "pad": 1.5, "alpha": .9})
    zoom = render.inset_axes([.56, .06, .42, .42])
    zoom.imshow(local_view); zoom.axis("off")
    fig.legend([Patch(fc=S.FN), Patch(fc=S.ORANGE)], ["FN：漏报不可达", "FP：误报"],
               loc="lower center", ncol=2, bbox_to_anchor=(.72, .008), frameon=False, fontsize=7.5)
    print("SAVED", S.save(fig, "fig10_failure"))


if __name__ == "__main__":
    main()
