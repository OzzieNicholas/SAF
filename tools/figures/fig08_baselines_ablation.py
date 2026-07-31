#!/usr/bin/env python3
"""图 8 基线与消融对比（写作指引 §5.4 / 图8）：双面板统计图。

(a) 五类方法不可达 F1（点级总体）——数据源 `runs/baselines/latest.json`（tools/eval_baselines.py 产出）。
(b) 消融四变体不可达 F1——数据源 `charter/results.md` 消融行（tools/eval_ablation.py，procedural@128 定稿；
    eval_ablation 现仅打印不落 JSON，故此处以账本定稿值为常量，改动随账本同步）。
(a) 圆点/误差棒为零件级 F1 均值±std，菱形另示点级总体 F1，避免混用统计层级。
用法：conda run -n saf python tools/figures/fig08_baselines_ablation.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    base = json.load(open(os.path.join(_ROOT, "runs", "baselines", "latest.json"), encoding="utf-8"))["methods"]
    # (a) 五基线：零件级均值/std 与点级总体 F1 分层表达
    order = [("majority", "多数类"), ("local_rule", "局部规则"), ("ray_visibility", "射线可见性"),
             ("tiny_local", "局部形状"), ("convonet", "本文")]
    f1 = [base[k]["f1_model_mean"] for k, _ in order]
    std = [base[k]["f1_model_std"] for k, _ in order]
    overall = [base[k]["f1_overall"] for k, _ in order]
    labs = [z for _, z in order]
    cols_a = [S.UNC, S.NEUTRAL, S.ACC, S.ORANGE, S.INK]

    # (b) 消融（results.md 消融行，procedural@128）
    abl_labs = ["无形状", "局部(RF3)", "本文(RF7)", "过度池化"]
    abl_f1 = [0.434, 0.859, 0.926, 0.803]
    cols_b = [S.UNC, S.ACC, S.INK, S.NEUTRAL]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=S.double_column(66), gridspec_kw={"width_ratios": [1.15, 1]})
    x = range(len(labs))
    ax1.errorbar(x, f1, yerr=std, fmt="o", ms=7, color="#222", ecolor="#999", capsize=3, lw=1.1)
    ax1.scatter(x, overall, s=42, marker="D", c=cols_a, edgecolors="white", zorder=3)
    for i, (v, ov) in enumerate(zip(f1, overall)):
        ax1.text(i, min(v + std[i] + 0.035, 1.13), f"{v:.3f}", ha="center", fontsize=7.5)
        ax1.text(i + 0.08, ov - 0.025, f"{ov:.3f}", ha="left", va="top", fontsize=7.5, color=cols_a[i])
        ax1.plot([i, i], [ov, v], color="#C8C8C8", lw=0.8, zorder=0)
    ax1.set_xticks(list(x), labs)
    ax1.set_ylabel("不可达类 F1"); ax1.set_ylim(0, 1.18); ax1.set_title("(a) 基线：零件级分布", loc="left", fontsize=8.4)
    ax1.legend([plt.Line2D([], [], marker="o", color="#222", ls="none"),
                plt.Line2D([], [], marker="D", color=S.INACC, ls="none")],
               ["模型 F1 均值 ± std", "点级总体 F1"], frameon=False, fontsize=8, loc="lower right")
    plt.setp(ax1.get_xticklabels(), rotation=18, ha="right")

    ax2.plot(range(len(abl_labs)), abl_f1, color="#444", lw=1.2, zorder=1)
    ax2.scatter(range(len(abl_labs)), abl_f1, s=80, c=cols_b, edgecolors="white", linewidths=1, zorder=2)
    ax2.set_xticks(range(len(abl_labs)), abl_labs)
    ax2.set_ylabel("不可达类 F1"); ax2.set_ylim(0, 1.08); ax2.set_title("(b) 消融：形状上下文", loc="left", fontsize=8.4)
    for i, v in enumerate(abl_f1):
        ax2.text(i, v + 0.035, f"{v:.3f}", ha="center", fontsize=8)
    ax2.text(0.02, 0.02, "受控子集、单种子；仅比较相对趋势", transform=ax2.transAxes, fontsize=7.5, color=S.NEUTRAL)
    plt.setp(ax2.get_xticklabels(), rotation=18, ha="right")

    fig.subplots_adjust(left=.07, right=.985, bottom=.25, top=.90, wspace=.28)

    print("SAVED", S.save(fig, "fig08_baselines_ablation"))


if __name__ == "__main__":
    main()
