#!/usr/bin/env python3
"""Figure 10. Error regime statistics and a fixed complex held-out case."""
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
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "runs", "failure_audit")
PAPER_EVIDENCE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "assets", "fig10_failure_evidence.png")


def plot_paper_ledger(evidence_path):
    """Render audited failure summaries without reconstructing absent raw runs."""
    if not os.path.isfile(evidence_path):
        raise FileNotFoundError(f"Paper evidence image not found: {evidence_path}")

    bins = ("全被挡\n(0)", "临界\n(1–2)", "边界\n(3–5)", "开阔\n(≥6)")
    rates = np.asarray((2.9, 15.7, 10.7, 3.9))
    bar_colours = (S.UNC, S.ORANGE, S.ORANGE, S.UNC)
    error_names = ("误报 FP", "漏报 FN")
    error_values = np.asarray((1.4, 3.3))
    evidence = plt.imread(evidence_path)

    fig = plt.figure(figsize=S.double_column(92))
    outer = fig.add_gridspec(1, 2, width_ratios=(.94, 1.42),
                             left=.075, right=.985, bottom=.16, top=.92, wspace=.16)
    stats = outer[0].subgridspec(2, 1, height_ratios=(1.0, .42), hspace=.38)
    rate_axis = fig.add_subplot(stats[0])
    x = np.arange(len(rates))
    bars = rate_axis.bar(x, rates, width=.62, color=bar_colours)
    for bar, value in zip(bars, rates):
        rate_axis.text(bar.get_x() + bar.get_width() / 2, value + .45,
                       f"{value:.1f}%", ha="center", fontsize=7.5)
    rate_axis.axhline(4.7, color=S.NEUTRAL, ls=(0, (3, 2)), lw=.9)
    rate_axis.text(3.45, 5.05, "总体 4.7% ± 0.3%", ha="right", va="bottom",
                   fontsize=7.0, color=S.NEUTRAL)
    rate_axis.set_xticks(x, bins)
    rate_axis.set_ylabel("误判率 (%)")
    rate_axis.set_ylim(0, 19.2)
    rate_axis.set_title("(a) 误判集中于临界可达方向", loc="left",
                        fontsize=8.4, fontweight="bold", pad=3)
    rate_axis.grid(axis="y")
    rate_axis.set_axisbelow(True)

    composition_axis = fig.add_subplot(stats[1])
    composition_bars = composition_axis.bar(np.arange(2), error_values, width=.55,
                                             color=(S.ORANGE, S.FN))
    for bar, value in zip(composition_bars, error_values):
        composition_axis.text(bar.get_x() + bar.get_width() / 2, value + .12,
                              f"{value:.1f}%", ha="center", fontsize=7.4)
    composition_axis.set_xticks(np.arange(2), error_names)
    composition_axis.set_ylabel("占比 (%)", fontsize=7.5)
    composition_axis.set_ylim(0, 4.15)
    composition_axis.set_title("(b) 总误判构成", loc="left", fontsize=8.2,
                               fontweight="bold", pad=2)
    composition_axis.grid(axis="y")
    composition_axis.set_axisbelow(True)

    evidence_axis = fig.add_subplot(outer[1])
    S.imshow_cad(evidence_axis, evidence, semantic=True)
    evidence_axis.set_title("(c) 代表性留出件的定性误差面", loc="left",
                            fontsize=8.4, fontweight="bold", pad=3)
    fig.legend([Patch(fc=S.FN), Patch(fc=S.ORANGE), Patch(fc=S.PART)],
               ["漏报不可达（FN）", "误报（FP）", "零件"], ncol=3,
               loc="lower right", bbox_to_anchor=(.985, .012), frameon=False)
    fig.text(.075, .045, "Fusion 400 件子集、5 次聚合；分箱仅报告账本可核验的误判率。",
             fontsize=7.0, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "fig10_failure"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    parser.add_argument("--paper-ledger", action="store_true",
                        help="render the ledger-backed paper summary without raw audit artifacts")
    parser.add_argument("--evidence-image", default=PAPER_EVIDENCE,
                        help="qualitative fixed-case image used only by --paper-ledger")
    args = parser.parse_args()
    if args.paper_ledger:
        plot_paper_ledger(args.evidence_image)
        return

    from support_accessibility.data.dataset import load_dataset
    with open(os.path.join(AUDIT, "failure.json"), encoding="utf-8") as handle:
        report = json.load(handle)
    artifact_path = os.path.join(AUDIT, "fig10_case.npz")
    if not os.path.exists(artifact_path):
        raise FileNotFoundError("Figure 10 requires fig10_case.npz; rerun tools/failure_cases.py")
    artifact = np.load(artifact_path, allow_pickle=True)
    name = str(artifact["name"])
    if name != X.FIG10.name or str(artifact["split"]) != "test":
        raise RuntimeError("Figure 10 artifact is not the fixed held-out case")

    models, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    model = {item.name: item for item in models}[name]
    V, F, occ, lo, pitch = D.load_fusion_mesh(name, args.root)
    mapping = D.map_processed_faces(V, F, occ, lo, pitch, artifact["points"], "fusion")
    fp = np.asarray(artifact["fp"], bool); fn = np.asarray(artifact["fn"], bool)
    errors = fp | fn
    if not errors.any():
        raise RuntimeError("Figure 10 fixed case has no errors")
    error_indices = mapping.face_indices[errors]
    colours = np.empty((len(error_indices), 3), float)
    colours[fp[errors]] = mcolors.to_rgb(S.ORANGE)
    colours[fn[errors]] = mcolors.to_rgb(S.FN)
    focus = V[np.asarray(F)[error_indices]].mean(axis=(0, 1))
    evidence_camera = D.underside_camera(V)
    global_view = D.render_mesh_technical_arr(V, F, zoom=X.FIG10.zoom,
                                              azimuth=X.FIG10.azimuth,
                                              elevation=X.FIG10.elevation,
                                              wsize=(1500, 1000))
    section_view = D.render_mesh_technical_arr(
        V, F, cpos="iso", zoom=1.75, focus=focus,
        azimuth=X.FIG10.azimuth, elevation=X.FIG10.elevation,
        clip_origin=focus, clip_normal=(1., 0., 0.), wsize=(1500, 1000)
    )
    local_view = D.render_face_field_arr(
        V, F, error_indices, colours, cpos=evidence_camera,
        zoom=3.05, focus=focus, wsize=(1800, 1050), selected_edges=True
    )

    order = (("0", "0"), ("1-2", "1–2"), ("3-5", "3–5"), ("6+", "≥6"))
    values = np.asarray([100 * report["error_rate_by_nviable"][key] for key, _ in order])
    std = np.asarray([100 * report["error_rate_by_nviable_std"][key] for key, _ in order])
    shares = np.asarray([100 * report["nviable_share"][key] for key, _ in order])
    labels = [label for _, label in order]
    colours_bar = [S.UNC, S.INACC, S.INACC, S.UNC]

    fig = plt.figure(figsize=S.double_column(92))
    outer = fig.add_gridspec(1, 2, width_ratios=(1, 1.42),
                             left=.075, right=.985, bottom=.16, top=.92, wspace=.13)
    stats = outer[0].subgridspec(2, 1, height_ratios=(1, .25), hspace=.08)
    main_axis = fig.add_subplot(stats[0])
    x = np.arange(4)
    bars = main_axis.bar(x, values, width=.62, color=colours_bar, yerr=std, capsize=3,
                         error_kw={"elinewidth": .8, "ecolor": S.NEUTRAL})
    for bar, value, error in zip(bars, values, std):
        main_axis.text(bar.get_x() + bar.get_width() / 2, value + error + .55,
                       f"{value:.1f}%", ha="center", fontsize=7.5)
    main_axis.axhline(100 * report["error_rate"], color=S.NEUTRAL,
                      ls=(0, (3, 2)), lw=.9)
    main_axis.set_xticks(x, labels); main_axis.tick_params(axis="x", labelbottom=False)
    main_axis.set_ylabel("误判率 (%)")
    main_axis.set_ylim(0, max(values + std) * 1.35)
    main_axis.set_title("(a) 误判集中于勉强/边界可达点", loc="left",
                        fontsize=8.4, fontweight="bold", pad=3)
    main_axis.grid(axis="y"); main_axis.set_axisbelow(True)
    share_axis = fig.add_subplot(stats[1], sharex=main_axis)
    share_axis.bar(x, shares, color=colours_bar, width=.62)
    share_axis.set_ylim(0, max(shares) * 1.25)
    share_axis.set_ylabel("样本占比", fontsize=7.5)
    share_axis.set_xlabel(r"每点可达方向数 $n_{\mathrm{viable}}$")
    share_axis.tick_params(axis="both", labelsize=7.5, length=2)

    evidence = outer[1].subgridspec(2, 2, height_ratios=(.92, 1.08),
                                    wspace=.08, hspace=.20)
    global_axis = fig.add_subplot(evidence[0, 0])
    section_axis = fig.add_subplot(evidence[0, 1])
    local_axis = fig.add_subplot(evidence[1, :])
    S.imshow_cad(global_axis, global_view)
    S.imshow_cad(section_axis, section_view)
    S.imshow_cad(local_axis, local_view, semantic=True)
    global_axis.set_title("(b) 全局定位（test）", loc="left", fontsize=8.4,
                          fontweight="bold", pad=3)
    section_axis.set_title("(c) 局部剖切", loc="left", fontsize=8.4, fontweight="bold", pad=3)
    local_axis.set_title(f"(d) 真实误差面 ROI（{int(artifact['error_count'])}）", loc="left", fontsize=8.4,
                         fontweight="bold", pad=3)
    fig.legend([Patch(fc=S.FN), Patch(fc=S.ORANGE)], ["FN：漏报不可达", "FP：误报"],
               ncol=2, loc="lower right", bbox_to_anchor=(.985, .012), frameon=False)
    print("SAVED", S.save(fig, "fig10_failure"))


if __name__ == "__main__":
    main()
