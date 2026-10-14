"""误差位置与方向级输出。

(a) 固定留出集上按每点可达方向数分箱的误判率（5 个训练种子均值 ± 标准差），柱宽下方注明各箱样本占比；
(b) 方向级模型的方向推荐：Top-1 / Top-3 命中率与 precision@3（5 个训练种子均值 ± 标准差），对照随机排序与训练集方向先验。
数据：artifacts/runs/failure_analysis 与 direction_field_prediction。

用法：python -m paper.pipeline.figure_scripts.failure_direction
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run

BINS = (("0", "0（不可达）"), ("1-2", "1–2"), ("3-5", "3–5"), ("6+", "≥6"))


def main():
    import numpy as np
    fail, field = load_run("failure_analysis"), load_run("direction_field_prediction")
    fig = S.figure(S.DOUBLE_MM, 62.0)

    ax = fig.add_axes([0.07, 0.29, 0.40, 0.60])
    x = np.arange(len(BINS))
    rate = np.array([fail["error_rate_by_nviable"][k] for k, _n in BINS])
    std = np.array([fail["error_rate_by_nviable_std"][k] for k, _n in BINS])
    share = np.array([fail["nviable_share"][k] for k, _n in BINS])
    # 0 个可达方向的点都是不可达点，误判只能是漏报；其余各箱的点都可达，误判只能是误报
    colours = [S.MISSED if k == "0" else S.FALSE_ALARM for k, _n in BINS]
    ax.bar(x, rate, 0.6, color=colours, yerr=std, error_kw=dict(lw=0.7, capsize=1.6))
    for xi, r, e in zip(x, rate, std):
        ax.text(xi, r + e + 0.004, f"{r:.1%}", ha="center", va="bottom", color=S.INK)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=S.MISSED, label="漏报（不可达判为可达）"),
                       Patch(color=S.FALSE_ALARM, label="误报（可达判为不可达）")],
              loc="upper right", handlelength=1.0)
    ax.set_xticks(x, [f"{n}\n（占 {s:.0%}）" for (_k, n), s in zip(BINS, share)])
    ax.set_xlabel("每个接触点的可达方向数")
    ax.set_ylabel("误判率")
    ax.set_ylim(0, max(rate + std) * 1.35)
    ax.yaxis.set_major_formatter(__import__("matplotlib").ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", color="#E3E5E7", lw=0.4); ax.set_axisbelow(True)
    fig.text(0.27, 0.015, "(a) 误判率随可达方向数增加而下降", ha="center", va="bottom", color=S.INK)

    bx = fig.add_axes([0.58, 0.29, 0.40, 0.60])
    metrics = (("top1_hit", "Top-1 命中率"), ("top3_hit", "Top-3 命中率"), ("precision_at3", "precision@3"))
    net = field["network"]
    series = (("随机排序", "#C3C8CC", [field["random_baseline"][k] for k, _n in metrics], None),
              ("训练集方向先验", S.GEOMETRY, [field["global_prior_baseline"][k] for k, _n in metrics], None),
              ("方向级网络", S.NETWORK, [net[k]["mean"] for k, _n in metrics], [net[k]["std"] for k, _n in metrics]))
    width = 0.26
    xm = np.arange(len(metrics))
    for j, (name, colour, vals, err) in enumerate(series):
        xs = xm + (j - 1) * width
        bx.bar(xs, vals, width, color=colour, label=name, yerr=err, error_kw=dict(lw=0.7, capsize=1.4))
        for xi, v in zip(xs, vals):
            bx.text(xi, v + 0.03, f"{v:.2f}", ha="center", va="bottom", color=S.INK)
    bx.set_xticks(xm, [n for _k, n in metrics])
    bx.set_xlim(-0.6, len(metrics) - 0.4)
    bx.set_ylim(0, 1.12)
    bx.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    bx.set_ylabel("比例")
    bx.grid(axis="y", color="#E3E5E7", lw=0.4); bx.set_axisbelow(True)
    bx.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, handlelength=1.0, borderaxespad=0.2)
    fig.text(0.78, 0.015, f"(b) {field['n_directions']} 个方向中推荐可达方向（只统计至少有一个可达方向的点）",
             ha="center", va="bottom", color=S.INK)
    print("SAVED", S.save(fig, "failure_direction"))


if __name__ == "__main__":
    main()
