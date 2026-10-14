"""两级几何判定示意：(a) 二维占据栅格上的自由空间距离场与一条方向的步进采样（数值实际计算）；
(b) 方向净空 c 的三段判定：明确碰撞 / 边界带交给胶囊–网格精确求交 / 明确无碰撞。

用法：python -m paper.pipeline.figure_scripts.labeler_schematic
"""
import numpy as np

from paper.pipeline.figure_scripts import journal_style as S

R_VOX = 2.4          # 示意中的工具半径（体素）
EPS = 1.5            # 边界带半宽（体素），与冻结口径一致
ZONE_BAND = "边界带→精确求交"
ZONE_DOT = {"hit": "#C0392B", "band": "#D7833F", "clear": "#2C6FB2"}


def zone(c):
    return "hit" if c <= R_VOX - EPS else ("band" if c <= R_VOX + EPS else "clear")


def occupancy():
    """二维示意零件：带台阶的悬垂结构，True = 实体。"""
    occ = np.zeros((34, 44), bool)                 # (行 y, 列 x)，行 0 在上
    occ[2:8, 2:42] = True                          # 顶板
    occ[8:30, 2:7] = True                          # 左立柱
    occ[8:14, 30:42] = True                        # 右侧下垂台阶
    occ[22:26, 15:28] = True                       # 下方障碍
    return occ


def main():
    from scipy import ndimage
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Circle, Rectangle

    occ = occupancy()
    phi = ndimage.distance_transform_edt(~occ)
    fig = S.figure(S.SINGLE_MM, 70.0)
    ax = fig.add_axes([0.02, 0.37, 0.80, 0.61])
    cmap = LinearSegmentedColormap.from_list("free", ["#FFFFFF", "#9FC2E0", "#2C5F8A"])
    field = np.ma.masked_where(occ, phi)
    im = ax.imshow(field, cmap=cmap, vmin=0, vmax=phi.max(), origin="upper", interpolation="nearest")
    solid = np.ma.masked_where(~occ, occ)
    ax.imshow(solid, cmap=LinearSegmentedColormap.from_list("s", ["#C9CDD1", "#C9CDD1"]), origin="upper",
              interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, occ.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, occ.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.15)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    for side in ax.spines.values():
        side.set_visible(False)

    p = np.array([20.0, 10.6])                     # (x, y) 查询点，位于顶板下方
    v = np.array([0.62, 0.78]); v /= np.linalg.norm(v)      # 图像坐标 y 向下：工具从下方逼近
    ts = np.arange(R_VOX, 40.0, 1.0)
    centres = p[None, :] + ts[:, None] * v[None, :]
    inside = (centres[:, 0] >= 0) & (centres[:, 0] < occ.shape[1] - 0.5) & (centres[:, 1] < occ.shape[0] - 0.5)
    centres = centres[inside]
    clear = np.array([phi[int(round(c[1])), int(round(c[0]))] for c in centres])
    k = int(np.argmin(clear))
    ax.plot(*centres.T, color=S.INK, lw=0.6, zorder=3)
    ax.scatter(*centres.T, s=7, c=[ZONE_DOT[zone(c)] for c in clear],
               edgecolors="white", linewidths=0.3, zorder=4)
    ax.add_patch(Circle(centres[k], R_VOX, fill=False, ec=S.INK, lw=0.7, ls=(0, (2, 1.5)), zorder=5))
    ax.plot(*p, "o", color=S.INK, ms=3, zorder=6)
    ax.text(p[0] - 0.8, p[1] - 0.6, S.var("p"), ha="right", va="bottom", color=S.INK)
    ax.annotate(f"{S.var('c')} = min {S.var('φ')}（{clear[k]:.1f}）", xy=centres[k], xytext=(30.5, 19.5),
                color=S.INK, arrowprops=dict(arrowstyle="-", color=S.INK, lw=0.5))
    ax.text(0.5, -0.03, f"(a) 距离场 {S.var('φ')} 上沿方向 {S.var('v')} 步进，记录最小净空 {S.var('c')}",
            transform=ax.transAxes, ha="center", va="top", color=S.INK)
    cax = fig.add_axes([0.85, 0.52, 0.022, 0.30])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label(f"{S.var('φ')}/体素", labelpad=1)
    cb.ax.tick_params(length=1.5, width=0.4, pad=1)
    cb.outline.set_linewidth(0.4)

    # (b) 净空数轴
    bx = fig.add_axes([0.05, 0.13, 0.90, 0.07])
    lo, hi = 0.0, R_VOX + EPS + 3.0
    zones = ((lo, R_VOX - EPS, "#F3D6D2", "明确碰撞"),
             (R_VOX - EPS, R_VOX + EPS, "#FBE6CF", ZONE_BAND),
             (R_VOX + EPS, hi, "#D6E6F4", "明确无碰撞"))
    for a, b, colour, name in zones:
        bx.add_patch(Rectangle((a, 0), b - a, 1, facecolor=colour, edgecolor="none"))
        bx.text((a + b) / 2, 1.12, name, ha="center", va="bottom", color=S.INK)
    for x, name in ((R_VOX - EPS, f"{S.var('r')}−{S.var('ε')}"), (R_VOX, S.var("r")), (R_VOX + EPS, f"{S.var('r')}+{S.var('ε')}")):
        bx.axvline(x, color=S.INK, lw=0.6, ls="-" if x == R_VOX else ":")
        bx.text(x, -0.15, name, ha="center", va="top", color=S.INK)
    bx.set_xlim(lo, hi); bx.set_ylim(0, 1)
    bx.set_yticks([]); bx.set_xticks([])
    for side in ("left", "right", "top"):
        bx.spines[side].set_visible(False)
    bx.text(hi, -0.15, f"方向净空 {S.var('c')}", ha="right", va="top", color=S.INK)
    fig.text(0.5, 0.025, "(b) 按净空分流：只有边界带内的方向进入精确求交", ha="center", va="bottom", color=S.INK)
    print("SAVED", S.save(fig, "labeler_schematic"))


if __name__ == "__main__":
    main()
