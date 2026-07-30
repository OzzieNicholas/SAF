#!/usr/bin/env python3
"""图 10 失败案例分析（写作指引 §5.6 / 图10）：双联。

(a) 误判率 vs 每点可达方向数分箱柱状（0 / 1–2 / 3–5 / ≥6）——误判集中在 1–5「勉强可达」边界档；
(b) 误判最多件 3D 渲染，误判点高亮：假负 FN（漏报不可达，红，最糟）/ 假正 FP（误报，橙）。
数据源 = runs/failure_audit/{failure.json, fig10_worst.npz}（tools/failure_cases.py --max-models 400 产出，
与 results.md 失败案例行同源）。用法：conda run -n saf python tools/figures/fig10_failure.py [--root ...]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_AUD = os.path.join(_ROOT, "runs", "failure_audit")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    a = ap.parse_args()

    rep = json.load(open(os.path.join(_AUD, "failure.json"), encoding="utf-8"))
    ebn = rep["error_rate_by_nviable"]
    ebs = rep.get("error_rate_by_nviable_std", {})
    order = [("0", "0\n(不可达)"), ("1-2", "1–2\n(勉强)"), ("3-5", "3–5\n(边界)"), ("6+", "≥6\n(开阔)")]
    vals = [100 * (ebn.get(k) or 0.0) for k, _ in order]
    errs = [100 * (ebs.get(k) or 0.0) for k, _ in order]
    labs = [z for _, z in order]
    hot = {"1-2", "3-5"}                                        # 边界/勉强档（稳健结论：此二档显著高于 0 与 ≥6）
    cols = [S.INACC if k in hot else S.NEUTRAL for k, _ in order]
    seeds = rep.get("seeds", 1)

    fig = plt.figure(figsize=(9.6, 3.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.16, left=0.08, right=0.98, top=0.9, bottom=0.14)

    ax = fig.add_subplot(gs[0])
    bars = ax.bar(labs, vals, color=cols, width=0.68, yerr=errs, capsize=3,
                  error_kw={"elinewidth": 0.9, "ecolor": "#555", "alpha": 0.8})
    for r, v, e in zip(bars, vals, errs):
        ax.text(r.get_x() + r.get_width() / 2, v + e + 0.35, f"{v:.1f}", ha="center", va="bottom", fontsize=8.5)
    ax.axhline(100 * rep["error_rate"], ls="--", lw=1.2, color="#888")
    ax.text(-0.38, 100 * rep["error_rate"] + 0.3, f"总体 {100 * rep['error_rate']:.1f}%", ha="left",
            va="bottom", fontsize=8.3, color="#888")
    ax.set_ylabel("误判率 (%)"); ax.set_xlabel("每点可达方向数 n_viable（几何难度代理）")
    ax.set_ylim(0, max(v + e for v, e in zip(vals, errs)) * 1.3 + 1)
    fpm, fnm = 100 * rep["false_pos_rate"], 100 * rep["false_neg_rate"]
    fps, fns = 100 * rep.get("false_pos_rate_std", 0), 100 * rep.get("false_neg_rate_std", 0)
    ax.set_title(f"(a) 误判随几何难度分布（{seeds} 种子；FP {fpm:.1f}±{fps:.1f}% / FN {fnm:.1f}±{fns:.1f}%）",
                 fontsize=9.5)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    axb = fig.add_subplot(gs[1])
    npz = np.load(os.path.join(_AUD, "fig10_worst.npz"), allow_pickle=True)
    name = str(npz["name"])
    Vn, F, _o, lo, pitch = D.load_fusion_mesh(name, a.root)
    img = D.render_fp_fn_arr(Vn, F, npz["points"], npz["fp"], npz["fn"], lo, pitch, zoom=1.5)
    axb.imshow(img); axb.axis("off")
    nfp, nfn = int(npz["fp"].sum()), int(npz["fn"].sum())
    axb.set_title(f"(b) 误判最多件（FN {nfn} · FP {nfp}）", fontsize=10)
    axb.legend(handles=[Patch(color=S.INACC, label="假负 FN（漏报不可达）"),
                        Patch(color=S.ORANGE, label="假正 FP（误报）"),
                        Patch(color=(0.62, 0.64, 0.67), label="判对")],
               loc="lower center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False, fontsize=8.3)

    print("SAVED", S.save(fig, "fig10_failure"))


if __name__ == "__main__":
    main()
