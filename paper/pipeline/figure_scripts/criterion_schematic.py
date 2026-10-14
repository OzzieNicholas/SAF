"""判据示意：有限球工具的多方向直线逼近（二维剖面，几何按判据精确计算）。

三幅剖面：(a) 开阔下朝面——存在无碰撞方向；(b) 颈口窄于工具的内腔——腔内放得下工具球，
但所有方向的扫掠都撞壁；(c) 窄缝——零半径射线可见，有限半径工具进不去。
胶囊 = 从相切球心 p + r·v 起沿 v 扫掠的球；碰撞位置由球心到实体的距离逐步求出，图上画到碰撞处为止。

用法：python -m paper.pipeline.figure_scripts.criterion_schematic
"""
import numpy as np

from paper.pipeline.figure_scripts import journal_style as S

R = 0.9                      # 工具半径（示意单位）
SOLID = "#D5D8DB"
SOLID_EDGE = "#4A5055"
CLEAR = "#2C6FB2"
BLOCKED = "#C0392B"
PANEL = (0.0, 10.0, 0.0, 8.0)


def rect_distance(p, rects):
    """点到矩形并集的欧氏距离（在内部为 0）。rects: [(x0, x1, y0, y1)]。"""
    best = np.inf
    for x0, x1, y0, y1 in rects:
        dx = max(x0 - p[0], 0.0, p[0] - x1)
        dy = max(y0 - p[1], 0.0, p[1] - y1)
        best = min(best, float(np.hypot(dx, dy)))
    return best


def sweep(p, v, r, rects, t_max=14.0, step=0.01):
    """球心沿 p + t·v（t ≥ r）前进，返回 (终止 t, 是否碰撞)。出面板视为逃逸。"""
    x0, x1, y0, y1 = PANEL
    t = r
    while t <= t_max:
        c = p + t * v
        if rect_distance(c, rects) < r - 1e-9:
            return t, True
        if not (x0 - r <= c[0] <= x1 + r and y0 - r <= c[1] <= y1 + r):
            return t, False
        t += step
    return t, False


def unit(angle_deg):
    a = np.radians(angle_deg)
    return np.array([np.cos(a), np.sin(a)])


def draw_capsule(ax, p, v, r, t_end, colour, blocked, alpha=0.20):
    """画胶囊（扫掠带 + 起止球）与逼近箭头；碰撞时在终点标 ×。"""
    from matplotlib.patches import Circle, Polygon
    n = np.array([-v[1], v[0]])
    a, b = p + r * v, p + t_end * v
    band = Polygon([a + r * n, b + r * n, b - r * n, a - r * n], closed=True,
                   facecolor=colour, edgecolor="none", alpha=alpha, zorder=2)
    ax.add_patch(band)
    ax.plot(*np.c_[a + r * n, b + r * n], color=colour, lw=0.6, zorder=3)
    ax.plot(*np.c_[a - r * n, b - r * n], color=colour, lw=0.6, zorder=3)
    ax.add_patch(Circle(a, r, facecolor="white", edgecolor=colour, lw=0.9, zorder=4))
    ax.add_patch(Circle(b, r, facecolor=colour, edgecolor=colour, lw=0.6, alpha=alpha, zorder=2))
    if blocked:
        ax.plot(*b, marker="x", color=colour, ms=5.5, mew=1.4, zorder=6)
    tail = p + min(t_end, 3.4 + r) * v                  # 箭头沿轴线指向相切球心：工具的逼近方向为 −v
    if np.linalg.norm(tail - a) > 0.3:
        ax.annotate("", xy=a, xytext=tail, zorder=5,
                    arrowprops=dict(arrowstyle="-|>", color=colour, lw=0.9, shrinkA=0, shrinkB=0,
                                    mutation_scale=7))


def setup(ax, rects, outline):
    from matplotlib.patches import Rectangle
    for x0, x1, y0, y1 in rects:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=SOLID, edgecolor="none", zorder=1))
    for line in outline:
        ax.plot(*np.asarray(line).T, color=SOLID_EDGE, lw=0.9, zorder=3, solid_capstyle="round")
    x0, x1, y0, y1 = PANEL
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect("equal"); ax.set_axis_off()


NUDGE = 1.2 * R              # 查询点沿外法向外移量（入库口径为 2 体素 ≈ 1.17 r）


def query_point(ax, c, normal=(0.0, -1.0), label_side=1.0):
    """面上接触点 c（空心）沿外法向外移得查询点 p（实心），返回 p。"""
    c = np.asarray(c, float)
    p = c + NUDGE * np.asarray(normal, float)
    ax.plot(*np.c_[c, p], color=S.INK, lw=0.5, ls=(0, (1.5, 1.2)), zorder=7)
    ax.plot(*c, marker="o", ms=3.4, mfc="white", mec=S.INK, mew=0.8, zorder=8)
    ax.plot(*p, marker="o", ms=3.4, color=S.INK, zorder=8)
    ax.text(c[0] + 0.28 * label_side, c[1] + 0.12, S.var("c"), color=S.INK, zorder=8,
            ha="left" if label_side > 0 else "right")
    ax.text(p[0] + 0.28 * label_side, p[1] - 0.05, S.var("p"), color=S.INK, zorder=8, va="top",
            ha="left" if label_side > 0 else "right")
    return p


def main():
    fig = S.figure(S.DOUBLE_MM, 62.0)
    w = 0.315
    axes = [fig.add_axes([0.012 + i * (w + 0.021), 0.20, w, 0.78]) for i in range(3)]

    # (a) 开阔下朝面：悬伸板下表面，一个方向无碰撞逃逸，另一个方向撞到立柱
    rects = [(0.0, 10.0, 5.0, 6.4), (0.0, 1.4, 0.0, 5.0)]
    outline = [[(10, 6.4), (0, 6.4)], [(10, 5.0), (1.4, 5.0), (1.4, 0.0)]]
    setup(axes[0], rects, outline)
    p = query_point(axes[0], (5.4, 5.0))
    for ang in (-62.0, -158.0):
        v = unit(ang)
        t, hit = sweep(p, v, R, rects)
        draw_capsule(axes[0], p, v, R, t, BLOCKED if hit else CLEAR, hit)

    # (b) 内腔：腔内放得下工具球，但经窄颈出不去
    rects = [(0.0, 1.0, 0.6, 7.6), (9.0, 10.0, 0.6, 7.6), (1.0, 9.0, 6.6, 7.6),
             (1.0, 2.05, 0.6, 2.0), (2.95, 9.0, 0.6, 2.0)]
    outline = [[(0, 7.6), (10, 7.6)], [(0, 0.6), (2.05, 0.6), (2.05, 2.0), (1.0, 2.0), (1.0, 6.6),
                                       (9.0, 6.6), (9.0, 2.0), (2.95, 2.0), (2.95, 0.6), (10, 0.6)]]
    setup(axes[1], rects, outline)
    p = query_point(axes[1], (6.2, 6.6), label_side=1.0)
    toward_neck = np.degrees(np.arctan2(1.3 - p[1], 2.5 - p[0]))     # 正对颈口中心
    for ang in (toward_neck, -90.0, -28.0):
        v = unit(ang)
        t, hit = sweep(p, v, R, rects)
        draw_capsule(axes[1], p, v, R, t, BLOCKED if hit else CLEAR, hit, alpha=0.16)

    # (c) 窄缝：宽度 w < 2r，零半径射线可直达外部，有限半径工具进不去
    rects = [(0.0, 4.55, 1.2, 7.4), (5.45, 10.0, 1.2, 7.4), (4.55, 5.45, 5.6, 7.4)]
    outline = [[(0, 7.4), (10, 7.4)], [(0, 1.2), (4.55, 1.2), (4.55, 5.6), (5.45, 5.6), (5.45, 1.2), (10, 1.2)]]
    setup(axes[2], rects, outline)
    p = query_point(axes[2], (5.0, 5.6), label_side=1.0)
    axes[2].annotate("", xy=p + np.array([0, -0.15]), xytext=(5.0, 0.15),
                     arrowprops=dict(arrowstyle="-|>", color=CLEAR, lw=0.9, ls=(0, (3, 2)), mutation_scale=7))
    v = unit(-90.0)
    t, hit = sweep(p, v, R, rects)
    draw_capsule(axes[2], p, v, R, max(t, R + 0.02), BLOCKED, True, alpha=0.18)
    axes[2].text(5.75, 0.55, f"{S.var('r')} = 0 射线可达", color=CLEAR, va="center")
    axes[2].annotate(f"{S.var('w')} < 2{S.var('r')}", xy=(4.55, 3.0), xytext=(1.0, 3.0),
                     va="center", color=S.INK,
                     arrowprops=dict(arrowstyle="-", color=S.INK, lw=0.5))

    captions = ("(a) 开阔下朝面：存在无碰撞方向",
                "(b) 窄颈内腔：容得下工具球，但各方向均碰撞",
                "(c) 窄缝：射线可见，有限半径工具不可达")
    for ax, cap in zip(axes, captions):
        ax.text(0.5, -0.04, cap, transform=ax.transAxes, ha="center", va="top", color=S.INK)

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=SOLID, edgecolor=SOLID_EDGE, lw=0.6, label="零件实体"),
               Patch(facecolor=CLEAR, alpha=0.3, edgecolor=CLEAR, label="无碰撞扫掠"),
               Patch(facecolor=BLOCKED, alpha=0.3, edgecolor=BLOCKED, label="碰撞扫掠（× 为首次接触）"),
               Line2D([], [], marker="o", ls="", ms=3.4, mfc="white", mec=S.INK, label=f"接触点 {S.var('c')}"),
               Line2D([], [], marker="o", ls="", ms=3.4, color=S.INK, label=f"外移查询点 {S.var('p')}")]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.0), handlelength=1.5,
               columnspacing=1.2)
    print("SAVED", S.save(fig, "criterion_schematic"))


if __name__ == "__main__":
    main()
