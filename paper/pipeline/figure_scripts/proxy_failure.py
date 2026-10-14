"""廉价指标遗漏的风险：零半径射线可见性与支撑接触面积都不能替代有限工具可达性。

(a) 不可达接触点中，零半径射线可见者所占比例（Fusion 与程序化数据）；
(b) 6 个轴向候选构建方向上，逐件 Spearman ρ 的分布：接触面积 vs 真实不可达面积、网络预测 vs 真实不可达面积；
(c) 选出最低风险方向的命中率：按接触面积最小、随机、按网络预测最小。
数据：artifacts/runs/tool_radius_effect 与 orientation_evaluation（逐件 ρ 由其逐件数据直接计算）。

用法：python -m paper.pipeline.figure_scripts.proxy_failure
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run


def _caption(fig, ax, text, **_style):
    """分图标题统一放在图底同一高度，水平居中于对应坐标轴。"""
    box = ax.get_position()
    fig.text(box.x0 + box.width / 2, 0.015, text, ha="center", va="bottom", color=S.INK)


def per_part_rho(orient):
    """逐件 Spearman ρ（真实不可达面积不全相等的零件）：(接触面积, 网络种子平均)。"""
    import numpy as np
    from support_accessibility import eval as E
    keys = orient["orientations"]
    area_rho, net_rho = [], []
    for p in orient["parts"]:
        o = p["orientations"]
        true = np.array([o[k]["true_inacc_area"] for k in keys])
        if true.std() == 0:
            continue
        area_rho.append(E.spearman(np.array([o[k]["contact_area"] for k in keys]), true))
        seeds = len(o[keys[0]]["pred_inacc_area_by_seed"])
        net_rho.append(np.mean([E.spearman(np.array([o[k]["pred_inacc_area_by_seed"][j] for k in keys]), true)
                                for j in range(seeds)]))
    return np.array(area_rho), np.array(net_rho)


def main():
    import numpy as np
    tool, orient = load_run("tool_radius_effect"), load_run("orientation_evaluation")
    fig = S.figure(S.DOUBLE_MM, 56.0)

    # (a) 不可达点中射线可见的比例
    ax = fig.add_axes([0.10, 0.29, 0.24, 0.61])
    rows = (("fusion", "Fusion 零件"), ("procedural", "程序化零件"))
    for i, (key, name) in enumerate(rows):
        share = tool[key]["ray_visible_share_of_inaccessible"]
        ax.barh(i, share, color=S.INACCESSIBLE, height=0.55)
        ax.barh(i, 1 - share, left=share, color="#D9DCDF", height=0.55)
        ax.text(share / 2, i, f"{share:.0%}", ha="center", va="center", color="white")
    ax.set_yticks(range(len(rows)), [n for _k, n in rows])
    ax.set_xlim(0, 1); ax.set_ylim(-0.6, 1.6)
    ax.set_xticks([0, 0.5, 1.0], ["0", "50%", "100%"])
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.text(0.5, 1.03, "红：射线可见　灰：射线亦被挡", transform=ax.transAxes, ha="center", va="bottom",
            color=S.GREY)
    _caption(fig, ax, "(a) 不可达接触点中零半径射线可见的比例", transform=ax.transAxes, ha="center", va="top",
            color=S.INK)

    # (b) 方向排序 ρ 分布
    area_rho, net_rho = per_part_rho(orient)
    bx = fig.add_axes([0.43, 0.29, 0.24, 0.61])
    rng = np.random.default_rng(0)
    for i, (vals, name, colour) in enumerate(((area_rho, "接触面积", S.GEOMETRY), (net_rho, "网络预测", S.NETWORK))):
        bp = bx.boxplot(vals, positions=[i], widths=0.45, vert=True, patch_artist=True, showfliers=False,
                        medianprops=dict(color=S.INK, lw=0.9), whiskerprops=dict(lw=0.6), capprops=dict(lw=0.6),
                        boxprops=dict(lw=0.6))
        bp["boxes"][0].set_facecolor(colour); bp["boxes"][0].set_alpha(0.25)
        bx.scatter(i + rng.uniform(-0.17, 0.17, vals.size), vals, s=4, color=colour, alpha=0.75, lw=0, zorder=3)
        bx.text(i, 1.08, f"均值 {vals.mean():.2f}", ha="center", va="bottom", color=colour)
    bx.axhline(0, color=S.GREY, lw=0.5, ls=":")
    bx.set_xticks([0, 1], ["接触面积", "网络预测"])
    bx.set_ylim(-1.1, 1.25)
    bx.set_ylabel(f"与真实风险排序的 Spearman {S.var('ρ')}")
    _caption(fig, bx, f"(b) 6 个候选方向的风险排序（{area_rho.size} 件）", transform=bx.transAxes,
            ha="center", va="top", color=S.INK)

    # (c) 最低风险方向命中率
    cx = fig.add_axes([0.76, 0.29, 0.22, 0.61])
    names = ("接触面积\n最小", "随机\n选取", "网络预测\n最小")
    vals = (orient["lowest_risk_hit_contact_area"], orient["lowest_risk_hit_random_expected"],
            orient["lowest_risk_hit_network"])
    errs = (0.0, 0.0, orient["lowest_risk_hit_network_std"])
    colours = (S.GEOMETRY, S.GREY, S.NETWORK)
    bars = cx.bar(range(3), vals, color=colours, width=0.6)
    cx.errorbar(2, vals[2], yerr=errs[2], fmt="none", ecolor=S.INK, lw=0.7, capsize=1.5)   # 仅网络有种子间波动
    for b, v, e in zip(bars, vals, errs):
        cx.text(b.get_x() + b.get_width() / 2, v + e + 0.03, f"{v:.1%}", ha="center", va="bottom", color=S.INK)
    cx.set_xticks(range(3), names, rotation=0)
    cx.set_ylim(0, 1.0)
    cx.set_yticks([0, 0.5, 1.0], ["0", "50%", "100%"])
    cx.set_ylabel("命中最低风险方向的零件比例")
    _caption(fig, cx, f"(c) 选出最低风险方向（{orient['n_parts']} 件）", transform=cx.transAxes,
            ha="center", va="top", color=S.INK)
    print("SAVED", S.save(fig, "proxy_failure"))


if __name__ == "__main__":
    main()
