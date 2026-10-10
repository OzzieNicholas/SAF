#!/usr/bin/env python3
"""Figure 8. Baseline comparison and controlled ablation.

Inputs are read through the frozen paper evidence manifest.
"""

from paper.pipeline import evidence as E
from paper.pipeline.figure_scripts import figure_style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


from paper.pipeline.paths import EVIDENCE_MANIFEST
from support_accessibility.runtime.data_paths import REPO_ROOT

ROOT = str(REPO_ROOT)
PAPER_MANIFEST = str(EVIDENCE_MANIFEST)

_METHOD_ROLES = (
    ("majority", "trivial_class_reference"),
    ("local_rule", "local_geometric_heuristic"),
    ("ray_visibility", "zero_radius_semantic_ablation"),
    ("coarse_finite_tool", "coarse_geometric_proxy"),
    ("tiny_local", "local_learned_reference"),
    ("convonet", "shape_conditioned_surrogate"),
)
_METHOD_LABELS = {
    "majority": "多数类",
    "local_rule": "局部规则",
    "ray_visibility": "零半径射线",
    "coarse_finite_tool": "粗有限工具 proxy",
    "tiny_local": "局部学习参照",
    "convonet": "形状条件 surrogate",
}
_METHOD_COLOURS = {
    "majority": S.UNC,
    "local_rule": S.NEUTRAL,
    "ray_visibility": S.ORANGE,
    "coarse_finite_tool": S.ACC,
    "tiny_local": "#5E7D67",
    "convonet": S.INK,
}


def baseline_method_entries(baseline):
    """Return the six declared methods only if their evidence roles are intact."""
    roles = baseline.get("method_roles")
    if not isinstance(roles, dict):
        raise RuntimeError("Baseline artifact has no method_roles mapping")
    entries = []
    for key, expected_role in _METHOD_ROLES:
        role = roles.get(key)
        if role != expected_role:
            raise RuntimeError(
                f"Baseline method role mismatch for {key}: expected {expected_role!r}, got {role!r}"
            )
        entries.append((key, _METHOD_LABELS[key], role))
    return tuple(entries)


def load_inputs():
    manifest = E.load_manifest(PAPER_MANIFEST, ROOT)
    baseline = E.load_canonical_artifact(manifest, "baseline_comparison", ROOT)
    ablation = E.load_canonical_artifact(manifest, "shape_context_ablation", ROOT)
    return baseline, ablation


def main():
    baseline, ablation = load_inputs()
    if any("f1_by_model" not in item for item in baseline["methods"].values()):
        raise RuntimeError("Figure 8 requires the extended per-model baseline artifact")

    entries = baseline_method_entries(baseline)
    order = tuple((key, label) for key, label, _role in entries)
    colours = tuple(_METHOD_COLOURS[key] for key, _label, _role in entries)
    fig, (left, right) = plt.subplots(1, 2, figsize=S.double_column(88),
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
    left.set_title("(a) 固定参考标签的近似与预测", loc="left",
                   fontsize=8.4, fontweight="bold", pad=4)
    left.grid(axis="x"); left.set_axisbelow(True)
    delta = baseline["paired_delta_convonet_minus_ray"]

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
    fig.subplots_adjust(left=.15, right=.965, bottom=.31, top=.91)
    fig.text(.10, .055, f"本文 − 射线基线：ΔF1={delta['mean']:.3f}  "
                        f"95% CI [{delta['ci95'][0]:.3f}, {delta['ci95'][1]:.3f}]",
             fontsize=7.5, color=S.INK)
    fig.text(.635, .055,
             f"{ablation['max_models']} 件 · seed={ablation['seed']} · {ablation['epochs']} 轮",
             fontsize=7.5, color=S.NEUTRAL)
    fig.text(.10, .145,
             "实心圆：零件均值和 95% CI；空心菱形：点池 F1。完整 oracle 仅提供标签。",
             fontsize=7.5, color=S.NEUTRAL)
    fig.text(.10, .105,
             "粗 proxy：16 全局/8 下半球方向；形状条件网络近似固定的 128/64 方向标签。",
             fontsize=7.5, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "baselines_ablation"))


if __name__ == "__main__":
    main()
