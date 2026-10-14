"""精度–耗时前沿：固定留出集上各几何判定口径与网络的单件耗时和不可达类 F1（以冻结两级标签为参考）。

数据来自 experiments/cost_accuracy_frontier.py 的运行产物，不在脚本内写任何结果数值。
用法：python -m paper.pipeline.figure_scripts.cost_accuracy_frontier
"""

from paper.pipeline.figure_scripts import journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run


def main():
    import numpy as np

    run = load_run("cost_accuracy_frontier")
    rows = run["methods"]
    t = lambda k: rows[k]["seconds_per_part_mean"]          # noqa: E731
    f = lambda k: rows[k]["pooled_f1"]                      # noqa: E731

    fig = S.figure(S.SINGLE_MM, 64.0)
    ax = fig.add_axes([0.15, 0.17, 0.80, 0.78])
    dirs = run["voxel_directions"]
    xs = np.array([t(f"voxel_{n}") for n in dirs]); ys = np.array([f(f"voxel_{n}") for n in dirs])
    ax.plot(xs, ys, "-o", color=S.GEOMETRY, mfc="white", mew=0.9, zorder=3)
    for n, x, y in zip(dirs, xs, ys):
        ax.annotate(str(n), (x, y), xytext=(0, -9), textcoords="offset points", ha="center",
                    color=S.GEOMETRY)
    ax.annotate("纯体素判定", (xs[-1], ys[-1]), xytext=(7, 0), textcoords="offset points",
                ha="left", va="center", color=S.GEOMETRY)
    ax.plot(t("ray_r0_128"), f("ray_r0_128"), "s", color=S.GREY, zorder=3)
    ax.annotate("零半径射线", (t("ray_r0_128"), f("ray_r0_128")), xytext=(-5, 0),
                textcoords="offset points", ha="right", va="center", color=S.GREY)
    ax.plot(t("two_stage_128"), 1.0, "*", color=S.INK, markersize=7, zorder=3)
    ax.annotate("两级标签器（参考）", (t("two_stage_128"), 1.0), xytext=(-6, 0),
                textcoords="offset points", ha="right", va="center", color=S.INK)
    # 网络精度取 5 个训练种子的均值与标准差（同一组权重在 GPU 与 CPU 上输出相同），耗时为种子 0 实测
    net_f1, net_sd = rows["network_gpu"]["pooled_f1_seed_mean"], rows["network_gpu"]["pooled_f1_seed_std"]
    for key, face, name in (("network_gpu", S.NETWORK, "网络（GPU）"), ("network_cpu", "white", "网络（CPU）")):
        ax.errorbar(t(key), net_f1, yerr=net_sd, fmt="^", color=S.NETWORK, mfc=face, mew=0.9, lw=0.7,
                    capsize=1.5, zorder=4)
        below = key == "network_gpu"                     # GPU 点靠近左轴，标签放下方以免与刻度相撞
        ax.annotate(name, (t(key), net_f1), xytext=(-4, -9) if below else (0, 8), textcoords="offset points",
                    ha="left" if below else "center", va="top" if below else "bottom", color=S.NETWORK)
    occ = run["occupancy_seconds_per_part_mean"]
    ax.axvline(occ, color=S.GREY, lw=0.6, ls=":", zorder=1)
    ax.set_ylim(0.64, 1.025)
    ax.set_xlim(1.5e-3, 3.0)
    ax.annotate("占据栅格构造", (occ, 0.645), xytext=(-2, 0), textcoords="offset points",
                color=S.GREY, rotation=90, va="bottom", ha="right")
    ax.set_xscale("log")
    ax.set_xlabel("单件耗时/s")
    ax.set_ylabel(f"不可达类 {S.F1}")
    ax.grid(axis="both", which="major", color="#E3E5E7", lw=0.4)
    ax.set_axisbelow(True)
    print("SAVED", S.save(fig, "cost_accuracy_frontier"))


if __name__ == "__main__":
    main()
