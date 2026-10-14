"""方法对照与消融：同一固定留出集（80 件）上各方法的不可达类 F1，学习类方法为 5 个训练种子。

(a) 每种方法两个量：点池 F1（实心，学习类附种子间标准差）与逐件 F1 均值及其 95% bootstrap 区间（空心+线）；
(b) 形状上下文消融：四个网络变体的点池 F1 均值 ± 种子间标准差。
数据：artifacts/runs/baseline_comparison 与 shape_context_ablation。

用法：python -m paper.pipeline.figure_scripts.method_comparison
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run

METHODS = (("majority", "多数类"), ("local_rule", "局部占据规则"), ("ray_visibility", "零半径射线"),
           ("coarse_finite_tool", "16 方向粗判定"), ("tiny_local", "局部小块 MLP"),
           ("convonet", "形状条件网络"))
VARIANTS = (("no_shape", "仅坐标", "—"), ("local", "单层卷积", "3"), ("lite", "三层卷积（本文）", "7"),
            ("pooled", "卷积 + 两次池化", "18"))


def main():
    import numpy as np
    base, abl = load_run("baseline_comparison"), load_run("shape_context_ablation")
    fig = S.figure(S.DOUBLE_MM, 62.0)
    ax = fig.add_axes([0.17, 0.19, 0.45, 0.70])
    y = np.arange(len(METHODS))[::-1]
    for yi, (key, name) in zip(y, METHODS):
        m = base["methods"][key]
        colour = S.NETWORK if key == "convonet" else (S.GEOMETRY if m["kind"] == "deterministic" else "#547F68")
        lo, hi = m["f1_model_ci95"]
        ax.plot([lo, hi], [yi - 0.16] * 2, color=colour, lw=1.0, solid_capstyle="butt")
        ax.plot(m["f1_model_mean"], yi - 0.16, "o", mfc="white", mec=colour, mew=0.9, ms=4)
        ax.errorbar(m["f1_overall"], yi + 0.16, xerr=m.get("f1_overall_std", 0) or None, fmt="o", color=colour,
                    ms=4, elinewidth=0.9, capsize=1.6)
        ax.text(1.02, yi + 0.16, f"{m['f1_overall']:.3f}", va="center", color=colour,
                transform=ax.get_yaxis_transform())
    ax.set_yticks(y, [name for _k, name in METHODS])
    ax.set_xlim(-0.02, 1.0)
    ax.set_xlabel(f"不可达类 {S.F1}")
    ax.grid(axis="x", color="#E3E5E7", lw=0.4); ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=S.INK, ms=4, label="点池（种子间标准差）"),
                       Line2D([], [], marker="o", color=S.INK, mfc="white", ms=4, lw=1.0, label="逐件均值与 95% 区间")],
              loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, handlelength=1.6, borderaxespad=0.2)
    ax.text(0.5, -0.20, f"(a) 方法对照（{base['n_test_models']} 个留出零件）",
            transform=ax.transAxes, ha="center", va="top", color=S.INK)

    bx = fig.add_axes([0.80, 0.19, 0.17, 0.70])
    yv = np.arange(len(VARIANTS))[::-1]
    for yi, (key, name, rf) in zip(yv, VARIANTS):
        colour = S.NETWORK if key == "lite" else S.GREY
        bx.errorbar(abl["f1"][key], yi, xerr=abl["f1_std"][key], fmt="o", color=colour, ms=4,
                    elinewidth=0.9, capsize=1.6)
        bx.text(abl["f1"][key], yi + 0.22, f"{abl['f1'][key]:.3f}", ha="center", va="bottom", color=colour)
    bx.set_yticks(yv, [f"{name}\n感受野 {rf}" for _k, name, rf in VARIANTS])
    bx.set_xlim(0.3, 1.0); bx.set_ylim(-0.6, len(VARIANTS) - 0.3)
    bx.set_xlabel(f"不可达类 {S.F1}")
    bx.grid(axis="x", color="#E3E5E7", lw=0.4); bx.set_axisbelow(True)
    bx.tick_params(axis="y", length=0)
    bx.text(0.5, -0.20, "(b) 形状上下文消融", transform=bx.transAxes, ha="center", va="top", color=S.INK)
    print("SAVED", S.save(fig, "method_comparison"))


if __name__ == "__main__":
    main()
