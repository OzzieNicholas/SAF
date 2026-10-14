"""全分布筛查：固定留出模型在全部未参与训练的 Fusion 零件（含全可达件）上的零件级与点级表现。

(a) 零件级 ROC：以零件内最大不可达概率排序（5 个训练种子各一条），并标出三种方法在各自工作点
    （任一点判不可达即报警）的检出率与误报率；
(b) 三种方法的零件检出率、全可达件误报率与点池 F1。
数据：artifacts/runs/screening_evaluation。

用法：python -m paper.pipeline.figure_scripts.screening_figure
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run

ROWS = (("ray_r0_128", "零半径射线", S.GREY, "s"), ("coarse_16", "16 方向粗判定", S.GEOMETRY, "D"),
        ("network", "形状条件网络", S.NETWORK, "o"))


def main():
    import numpy as np
    run = load_run("screening_evaluation")
    meth = run["methods"]

    fig = S.figure(S.DOUBLE_MM, 62.0)
    ax = fig.add_axes([0.07, 0.24, 0.36, 0.66])
    for i, roc in enumerate(run["network_roc_by_seed"]):
        ax.plot(roc["fpr"], roc["tpr"], color=S.NETWORK, lw=0.7, alpha=0.55 if i else 1.0)
    for key, name, colour, marker in ROWS:
        m = meth[key]
        ax.plot(m["part_false_alarm_rate"], m["part_detection_rate"], marker, color=colour, ms=5,
                mfc=colour if key != "network" else "white", mew=1.0, zorder=5)
        ax.annotate(name, (m["part_false_alarm_rate"], m["part_detection_rate"]), xytext=(6, -2),
                    textcoords="offset points", ha="left", va="top", color=colour)
    ax.set_xlim(0, 0.4); ax.set_ylim(0, 1.0)
    ax.set_xlabel("全可达零件误报率")
    ax.set_ylabel("风险零件检出率")
    ax.grid(color="#E3E5E7", lw=0.4); ax.set_axisbelow(True)
    auc, sd = run["network_part_auroc_max_prob"], run["network_part_auroc_max_prob_std"]
    ax.text(0.97, 0.06, f"网络 AUROC = {auc:.3f} ± {sd:.3f}", transform=ax.transAxes, ha="right", color=S.NETWORK)
    fig.text(0.25, 0.015, f"(a) 零件级 ROC（{run['n_parts_with_risk']:,} 件含风险，{run['n_safe_parts']:,} 件全可达）",
             ha="center", va="bottom", color=S.INK)

    bx = fig.add_axes([0.58, 0.24, 0.40, 0.66])
    metrics = (("part_detection_rate", "风险零件检出率"), ("part_false_alarm_rate", "全可达零件误报率"),
               ("pooled_f1", f"点池不可达类 {S.F1}"))
    width = 0.24
    x = np.arange(len(metrics))
    for j, (key, name, colour, _m) in enumerate(ROWS):
        vals = [meth[key][k] for k, _n in metrics]
        errs = [meth[key].get(k + "_std", 0.0) for k, _n in metrics]
        bars = bx.bar(x + (j - 1) * width, vals, width, color=colour, alpha=0.9 if key == "network" else 0.75,
                      yerr=errs if key == "network" else None, error_kw=dict(lw=0.7, capsize=1.5), label=name)
        for b, v in zip(bars, vals):
            bx.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                    color=S.INK)
    bx.set_xticks(x, [n for _k, n in metrics])
    bx.set_ylim(0, 1.0)
    bx.set_ylabel("比例 / 得分")
    bx.grid(axis="y", color="#E3E5E7", lw=0.4); bx.set_axisbelow(True)
    bx.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, handlelength=1.0, borderaxespad=0.2,
              columnspacing=1.0)
    fig.text(0.78, 0.015, f"(b) {run['n_eval_parts']:,} 个未见零件、{run['n_eval_points']:,} 个接触点上的筛查指标",
             ha="center", va="bottom", color=S.INK)
    print("SAVED", S.save(fig, "screening_figure"))


if __name__ == "__main__":
    main()
