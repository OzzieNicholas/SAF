#!/usr/bin/env python3
"""图 8 基线与消融对比（写作指引 §5.4 / 图8）：双面板柱状。

(a) 五类方法不可达 F1（点级总体）——数据源 `runs/baselines/latest.json`（tools/eval_baselines.py 产出）。
(b) 消融四变体不可达 F1——数据源 `charter/results.md` 消融行（tools/eval_ablation.py，procedural@128 定稿；
    eval_ablation 现仅打印不落 JSON，故此处以账本定稿值为常量，改动随账本同步）。
误差棒：(a) 用零件级 std（f1_model_std）。用法：conda run -n saf python tools/figures/fig08_baselines_ablation.py
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
    # (a) 五基线（点级总体 F1 + 零件级 std）
    order = [("majority", "多数类"), ("local_rule", "局部规则"), ("ray_visibility", "射线可见性"),
             ("tiny_local", "局部形状"), ("convonet", "本文")]
    f1 = [base[k]["f1_overall"] for k, _ in order]
    std = [base[k]["f1_model_std"] for k, _ in order]
    labs = [z for _, z in order]
    cols_a = [S.UNC, S.NEUTRAL, S.ACC, S.GREEN, S.INACC]

    # (b) 消融（results.md 消融行，procedural@128）
    abl_labs = ["无形状", "局部(RF3)", "本文(RF7)", "过度池化"]
    abl_f1 = [0.434, 0.859, 0.926, 0.803]
    cols_b = [S.UNC, S.GREEN, S.INACC, S.NEUTRAL]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.8, 3.5))
    b1 = ax1.bar(labs, f1, color=cols_a, yerr=std, capsize=2.5,
                 error_kw={"elinewidth": 0.8, "ecolor": "#8a8a8a", "alpha": 0.7})
    ax1.set_ylabel("不可达类 F1"); ax1.set_ylim(0, 1.12); ax1.set_title("(a) 基线对比（点级总体 F1；误差棒=零件级 std）")
    for r, v in zip(b1, f1):
        ax1.text(r.get_x() + r.get_width() / 2, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5)
    plt.setp(ax1.get_xticklabels(), rotation=18, ha="right")

    b2 = ax2.bar(abl_labs, abl_f1, color=cols_b)
    ax2.set_ylabel("不可达类 F1"); ax2.set_ylim(0, 1.12); ax2.set_title("(b) 消融：形状上下文")
    for r, v in zip(b2, abl_f1):
        ax2.text(r.get_x() + r.get_width() / 2, v + 0.02, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5)
    plt.setp(ax2.get_xticklabels(), rotation=18, ha="right")

    print("SAVED", S.save(fig, "fig08_baselines_ablation"))


if __name__ == "__main__":
    main()
