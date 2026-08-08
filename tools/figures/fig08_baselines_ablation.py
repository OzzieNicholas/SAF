#!/usr/bin/env python3
"""Figure 8. Baseline comparison and controlled ablation.

The default mode renders the full per-part diagnostics from the reproducibility
artifacts.  ``--paper-ledger`` is intentionally narrower: it renders only the
audited aggregate values recorded in ``governance/results.md``.  It is appropriate
for the paper when those raw artifacts are not distributed, because it never
invents per-part dots or confidence intervals.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def plot_paper_ledger():
    """Render the paper's ledger-backed summary without unavailable raw runs."""
    order = (("多数类", 0.000, S.UNC), ("局部规则", 0.317, S.NEUTRAL),
             ("射线可见性", 0.676, S.ACC), ("局部形状", 0.851, S.ORANGE),
             ("形状条件网络", 0.925, S.INK))
    ablation = (("无形状", 0.434, S.UNC), ("局部 RF3", 0.859, S.ACC),
                ("中等 RF7", 0.926, S.INK), ("过度池化", 0.803, S.NEUTRAL))
    fig, (left, right) = plt.subplots(
        1, 2, figsize=S.double_column(78),
        gridspec_kw={"width_ratios": (1.18, 1), "wspace": .34},
    )

    for axis, entries, title in (
        (left, order, "(a) 点级基线：80 件留出集"),
        (right, ablation, "(b) 受控消融：形状上下文"),
    ):
        positions = np.arange(len(entries))[::-1]
        for y, (label, value, colour) in zip(positions, entries):
            axis.plot([0, value], [y, y], color="#D3D7DA", lw=1.0, zorder=1)
            axis.scatter([value], [y], s=62, c=colour, edgecolors="white",
                         linewidths=.8, zorder=3)
            axis.text(value + .025, y, f"{value:.3f}", va="center",
                      fontsize=7.5, color=S.INK)
        axis.set_yticks(positions, [item[0] for item in entries])
        axis.set_xlim(-.03, 1.10)
        axis.set_xlabel("不可达类 F1")
        axis.set_title(title, loc="left", fontsize=8.4, fontweight="bold", pad=4)
        axis.grid(axis="x")
        axis.set_axisbelow(True)

    fig.subplots_adjust(left=.10, right=.965, bottom=.25, top=.91)
    fig.text(.10, .055,
             "独立回归：神经 0.916，对比射线 0.676；配对差 95% CI [0.338, 0.527]",
             fontsize=7.2, color=S.INK)
    fig.text(.635, .055, "消融：400 件 · seed=0 · 60 轮",
             fontsize=7.2, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "fig08_baselines_ablation"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-ledger", action="store_true",
                        help="render only audited aggregate values from governance/results.md")
    args = parser.parse_args()
    if args.paper_ledger:
        plot_paper_ledger()
        return

    baseline_path = os.path.join(ROOT, "artifacts", "runs", "baselines", "latest.json")
    ablation_path = os.path.join(ROOT, "artifacts", "runs", "ablation", "latest.json")
    with open(baseline_path, encoding="utf-8") as handle:
        baseline = json.load(handle)
    with open(ablation_path, encoding="utf-8") as handle:
        ablation = json.load(handle)
    if any("f1_by_model" not in item for item in baseline["methods"].values()):
        raise RuntimeError("Figure 8 requires the extended per-model baseline artifact")

    order = (("majority", "多数类"), ("local_rule", "局部规则"),
             ("ray_visibility", "射线可见性"), ("tiny_local", "局部形状"),
             ("convonet", "本文"))
    colours = (S.UNC, S.NEUTRAL, S.ACC, S.ORANGE, S.INK)
    fig, (left, right) = plt.subplots(1, 2, figsize=S.double_column(78),
                                     gridspec_kw={"width_ratios": (1.18, 1), "wspace": .34})

    rng = np.random.default_rng(0)
    positions = np.arange(len(order))[::-1]
    for y, ((key, label), colour) in zip(positions, zip(order, colours)):
        item = baseline["methods"][key]
        values = np.asarray(item["f1_by_model"], float)
        jitter = rng.uniform(-.12, .12, size=len(values))
        left.scatter(values, y + jitter, s=7, color=colour, alpha=.16,
                     edgecolors="none", rasterized=True)
        ci = item["f1_model_ci95"]
        left.plot(ci, [y, y], color=colour, lw=4.0, alpha=.55, solid_capstyle="round")
        left.scatter([item["f1_model_mean"]], [y], s=42, c=colour,
                     edgecolors="white", linewidths=.7, zorder=4)
        left.scatter([item["f1_overall"]], [y], s=38, marker="D", facecolors="white",
                     edgecolors=colour, linewidths=1.1, zorder=5)
        left.text(1.025, y, f"{item['f1_overall']:.3f}", ha="left", va="center",
                  fontsize=7.5, color=colour, clip_on=False)
    left.set_yticks(positions, [label for _, label in order])
    left.set_xlim(-.03, 1.08); left.set_xlabel("不可达类 F1")
    left.set_title("(a) 基线：80 个留出零件的分布", loc="left",
                   fontsize=8.4, fontweight="bold", pad=4)
    left.grid(axis="x"); left.set_axisbelow(True)
    delta = baseline["paired_delta_convonet_minus_ray"]
    key_y = positions[0]
    left.scatter([.24], [key_y], s=38, c=S.INK, edgecolors="white", linewidths=.7, zorder=6)
    left.text(.275, key_y, "零件均值 / 95% CI", va="center", fontsize=7.5, color=S.INK)
    left.scatter([.66], [key_y], s=34, marker="D", facecolors="white",
                 edgecolors=S.INK, linewidths=1.1, zorder=6)
    left.text(.695, key_y, "点级总体", va="center", fontsize=7.5, color=S.INK)

    labels = ("无形状", "局部 RF3", "本文 RF7", "过度池化")
    keys = ("no_shape", "local", "lite", "pooled")
    values = np.asarray([ablation["f1"][key] for key in keys], float)
    ypos = np.arange(4)[::-1]
    for y, value, colour in zip(ypos, values, (S.UNC, S.ACC, S.INK, S.NEUTRAL)):
        right.plot([0, value], [y, y], color="#D3D7DA", lw=1.0)
        right.scatter([value], [y], s=62, c=colour, edgecolors="white", linewidths=.8, zorder=3)
        right.text(value + .025, y, f"{value:.3f}", va="center", fontsize=7.5, color=S.INK)
    right.set_yticks(ypos, labels); right.set_xlim(0, 1.08); right.set_xlabel("不可达类 F1")
    right.set_title("(b) 受控消融：形状上下文", loc="left",
                    fontsize=8.4, fontweight="bold", pad=4)
    right.grid(axis="x"); right.set_axisbelow(True)
    fig.subplots_adjust(left=.10, right=.965, bottom=.25, top=.91)
    fig.text(.10, .055, f"本文 − 射线基线：ΔF1={delta['mean']:.3f}  "
                        f"95% CI [{delta['ci95'][0]:.3f}, {delta['ci95'][1]:.3f}]",
             fontsize=7.5, color=S.INK)
    fig.text(.635, .055,
             f"{ablation['max_models']} 件 · seed={ablation['seed']} · {ablation['epochs']} 轮",
             fontsize=7.5, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "fig08_baselines_ablation"))


if __name__ == "__main__":
    main()
