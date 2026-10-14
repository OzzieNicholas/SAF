"""误差位置与方向级输出。

(a) 固定留出集上按每点可达方向数分箱的误判率（5 个训练种子均值 ± 标准差），柱宽下方注明各箱样本占比；
(b) 方向级模型的离散方向推荐：Top-1 / Top-3 命中率与 precision@3，对照随机排序与训练集全局方向先验。
数据：artifacts/runs/failure_analysis、direction_field_prediction、direction_field_audit。

用法：python -m paper.pipeline.figure_scripts.failure_direction
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run

BINS = (("0", "0（全被挡）"), ("1-2", "1–2"), ("3-5", "3–5"), ("6+", "≥6"))


def main():
    import numpy as np
    fail, field, audit = load_run("failure_analysis"), load_run("direction_field_prediction"), load_run("direction_field_audit")
    fig = S.figure(S.DOUBLE_MM, 62.0)

    ax = fig.add_axes([0.07, 0.29, 0.40, 0.60])
    x = np.arange(len(BINS))
    rate = np.array([fail["error_rate_by_nviable"][k] for k, _n in BINS])
    std = np.array([fail["error_rate_by_nviable_std"][k] for k, _n in BINS])
    share = np.array([fail["nviable_share"][k] for k, _n in BINS])
    critical = np.array([k in ("1-2", "3-5") for k, _n in BINS])
    ax.bar(x, rate, 0.6, color=np.where(critical, S.INACCESSIBLE, "#AEB4B9"), yerr=std,
           error_kw=dict(lw=0.7, capsize=1.6))
    for xi, r, e in zip(x, rate, std):
        ax.text(xi, r + e + 0.005, f"{r:.1%}", ha="center", va="bottom", color=S.INK)
    ax.axhline(fail["error_rate"], color=S.GREY, lw=0.6, ls=":")
    ax.text(-0.45, fail["error_rate"] + 0.004, f"总体 {fail['error_rate']:.1%}", ha="left",
            va="bottom", color=S.GREY)
    ax.set_xticks(x, [f"{n}\n（占 {s:.0%}）" for (_k, n), s in zip(BINS, share)])
    ax.set_xlabel("每个接触点的可达方向数")
    ax.set_ylabel("误判率")
    ax.set_ylim(0, max(rate + std) * 1.25)
    ax.yaxis.set_major_formatter(__import__("matplotlib").ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", color="#E3E5E7", lw=0.4); ax.set_axisbelow(True)
    fig.text(0.27, 0.015, "(a) 误判集中在方向余量临界的接触点", ha="center", va="bottom", color=S.INK)

    bx = fig.add_axes([0.58, 0.29, 0.40, 0.60])
    metrics = (("top1", "Top-1 命中率"), ("top3", "Top-3 命中率"), ("prec3", "precision@3"))
    series = (("随机排序", S.GREY, (audit["random_baseline"]["top1_hit"], audit["random_baseline"]["top3_hit"],
                                     audit["random_baseline"]["top3_precision"])),
              ("全局方向先验", S.GEOMETRY, (audit["global_direction_prior_baseline"]["top1_hit"],
                                       audit["global_direction_prior_baseline"]["top3_hit"],
                                       audit["global_direction_prior_baseline"]["top3_precision"])),
              ("方向级网络", S.NETWORK, (field["topk_hit_top1_mean"], field["topk_hit_top3_mean"],
                                    field["topk_precision_at3_mean"])))
    offset = 0.22                                   # 点图：截断纵轴不夸大差异（柱状图需从 0 起）
    xm = np.arange(len(metrics))
    for j, (name, colour, vals) in enumerate(series):
        marker = ("s", "D", "o")[j]
        bx.plot(xm + (j - 1) * offset, vals, marker, ls="", color=colour, ms=5, label=name)
        for xi, v in zip(xm + (j - 1) * offset, vals):
            bx.text(xi, v + 0.006, f"{v:.2f}", ha="center", va="bottom", color=colour)
    bx.set_xticks(xm, [n for _k, n in metrics])
    bx.set_xlim(-0.6, len(metrics) - 0.4)
    bx.set_ylim(0.78, 1.0)
    bx.set_ylabel("比例")
    bx.grid(axis="y", color="#E3E5E7", lw=0.4); bx.set_axisbelow(True)
    bx.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, handlelength=1.0, borderaxespad=0.2)
    fig.text(0.78, 0.015, f"(b) {field['D_dirs']} 个离散方向的推荐（只统计至少有一个可达方向的点）",
             ha="center", va="bottom", color=S.INK)
    print("SAVED", S.save(fig, "failure_direction"))


if __name__ == "__main__":
    main()
