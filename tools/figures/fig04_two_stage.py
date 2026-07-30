#!/usr/bin/env python3
"""图 4 两级几何判定器（写作指引 §4.2 / 图4）：2D 剖面双联。

(a) 第一级——自由空间**欧氏距离场**着色（真 scipy EDT）+ 球心沿方向 v 步进射线，标 free_dist>r 判据；
(b) 第二级——净空落在 r±ε 边界带的方向进放大镜：精确「胶囊–三角网格」求交示意（无离散误差）。
纯示意（matplotlib，(a) 距离场为真值计算）。用法：conda run -n saf python tools/figures/fig04_two_stage.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon, FancyArrowPatch  # noqa: E402

SOLID_E = "#6E6E6E"


def panel_a(ax, fig):
    from scipy.ndimage import distance_transform_edt
    nx, ny = 200, 150
    ext = [0.0, 8.0, 0.0, 6.0]
    px = (ext[1] - ext[0]) / nx
    xs = (np.arange(nx) + 0.5) * px
    ys = (np.arange(ny) + 0.5) * px
    X, Y = np.meshgrid(xs, ys)
    solid = ((X <= 1.4) & (Y <= 4.4)) | ((X <= 6.4) & (Y >= 3.6) & (Y <= 4.4))   # 立柱 + 顶板悬臂
    free = ~solid
    dist = distance_transform_edt(free) * px
    dshow = np.where(free, dist, np.nan)
    im = ax.imshow(dshow, origin="lower", extent=ext, cmap="YlGnBu", alpha=0.92, zorder=1)
    ax.imshow(np.where(solid, 1.0, np.nan), origin="lower", extent=ext,
              cmap=plt.matplotlib.colors.ListedColormap([SOLID_E]), zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02)
    cb.set_label("自由空间距离场 free_dist", fontsize=8.5); cb.ax.tick_params(labelsize=7.5)

    p = np.array([4.3, 3.6]); v = np.array([0.0, -1.0]); r = 0.55
    ax.add_patch(FancyArrowPatch(p, p + v * 3.1, arrowstyle="-|>", mutation_scale=13,
                                 lw=1.7, color="#B02318", linestyle=(0, (5, 3)), zorder=5))
    for k in range(4):
        c = p + v * (r + k * 0.72)
        ax.scatter(*c, s=16, color="#B02318", zorder=6)
        if k == 1:
            ax.add_patch(Circle(c, r, fc="none", ec="#B02318", lw=1.6, zorder=6))
            ax.annotate("球心", (c[0] + 0.15, c[1] + 0.05), fontsize=8.5, color="#B02318")
    ax.scatter(*p, s=44, color="black", zorder=7); ax.text(p[0] + 0.15, p[1] + 0.12, "p", fontsize=11, style="italic")
    ax.annotate("沿 v 步进：全程 free_dist > r\n→ 该方向无碰撞", (0.3, 0.75), fontsize=9.2,
                color="#B02318", zorder=6)
    ax.annotate("方向 v", (4.6, 2.05), fontsize=9.5, color="#B02318")
    ax.set_title("(a) 第一级：距离场腐蚀（半径一次摊销）", fontsize=10)
    ax.set_xlim(0, 8); ax.set_ylim(0, 6); ax.set_aspect("equal")


def _capsule(ax, a, b, r, fc, ec):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a; L = np.linalg.norm(d); u = d / L
    n = np.array([-u[1], u[0]]) * r
    ax.add_patch(Polygon([a + n, b + n, b - n, a - n], closed=True, fc=fc, ec="none", alpha=0.5, zorder=3))
    for c in (a, b):
        ax.add_patch(Circle(c, r, fc=fc, ec="none", alpha=0.5, zorder=3))
    ax.plot([a[0], b[0]], [a[1], b[1]], color=ec, lw=1.3, zorder=4)


def panel_b(ax):
    # 背景体素网格（示离散）
    for gx in np.arange(0, 8.1, 1.0):
        ax.plot([gx, gx], [0, 6], color="#E2E2E2", lw=0.7, zorder=0)
    for gy in np.arange(0, 6.1, 1.0):
        ax.plot([0, 8], [gy, gy], color="#E2E2E2", lw=0.7, zorder=0)
    # 真实表面（几段三角网格边）——一条斜面
    surf = np.array([(0.6, 4.6), (3.2, 3.1), (5.4, 3.5), (7.4, 2.2)])
    ax.add_patch(Polygon(np.vstack([surf, [7.4, 0.2], [0.6, 0.2]]), closed=True,
                         fc="#C9CDD4", ec=SOLID_E, lw=1.4, zorder=1))
    for i in range(len(surf) - 1):
        ax.plot(surf[[i, i + 1], 0], surf[[i, i + 1], 1], color=SOLID_E, lw=1.8, zorder=2)
    ax.scatter(surf[:, 0], surf[:, 1], s=18, color=SOLID_E, zorder=3)

    p = np.array([3.2, 3.1]); v = np.array([0.55, 1.0]); v = v / np.linalg.norm(v); r = 0.6
    a = p + v * 0.15; b = p + v * 2.35
    _capsule(ax, a, b, r, "#DD8452", "#B0562A")
    ax.add_patch(FancyArrowPatch(p, b + v * 0.25, arrowstyle="-|>", mutation_scale=12,
                                 lw=1.4, color="#B0562A", zorder=5))
    # 最近点（胶囊轴到相邻三角边）——净空≈r
    q = np.array([5.4, 3.5]); foot = np.array([4.55, 4.02])
    ax.plot([q[0], foot[0]], [q[1], foot[1]], color=S.INACC, lw=1.6, zorder=6)
    ax.scatter(*q, s=40, color=S.INACC, zorder=7)
    ax.annotate("精确最近距离 ≈ r", ((q[0] + foot[0]) / 2 + 0.15, (q[1] + foot[1]) / 2), fontsize=9,
                color=S.INACC, zorder=7)
    ax.scatter(*p, s=44, color="black", zorder=7); ax.text(p[0] - 0.32, p[1] - 0.02, "p", fontsize=11, style="italic")
    ax.annotate("净空落在 r ± ε 边界带：\n体素判定含糊 → 改用精确\n胶囊–三角网格求交（无离散误差）",
                (0.3, 0.55), fontsize=9.2, color="#B0562A", zorder=6)
    ax.set_title("(b) 第二级：边界带精确细化", fontsize=10)
    ax.set_xlim(0, 8); ax.set_ylim(0, 6); ax.set_aspect("equal")


def main():
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    panel_a(axes[0], fig); panel_b(axes[1])
    for ax in axes:
        ax.axis("off")
    print("SAVED", S.save(fig, "fig04_two_stage"))


if __name__ == "__main__":
    main()
