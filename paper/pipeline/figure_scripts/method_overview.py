"""方法总览：离线几何标注与在线形状条件预测两条泳道，所有渲染为同一留出零件、同一相机。

上泳道：零件与构建方向 → 下朝接触区 → 两级几何判定 → 点级标签；
下泳道：占据栅格 → 形状条件网络 → 未见零件上的不可达概率。标签只在训练时监督网络。
预测来自 experiments/holdout_model.py 的训练种子 0（该零件属于留出集）。

用法：python -m paper.pipeline.figure_scripts.method_overview
"""

from paper.pipeline.figure_scripts import cad_render, figure_cases, journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_fusion_mesh, load_run, map_processed_faces

PART = figure_cases.METHOD_OVERVIEW
ORANGE = "#E08A3C"


def probability_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("saf_prob", [S.ACCESSIBLE, "#EEE2DF", S.INACCESSIBLE])


def main():
    import numpy as np
    from matplotlib.colors import to_rgb
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    from support_accessibility.runtime.data_paths import resolve_data_paths
    from support_accessibility.data.dataset import load_dataset

    paths = resolve_data_paths()
    model = next(m for m in load_dataset(str(paths.processed_root("fusion360")))[0] if m.name == PART)
    per_model = load_run("holdout_model")["runs"][0]["per_model"]
    figure_cases.assert_holdout({"test_names": [r["name"] for r in per_model]}, PART, "method_overview")
    rec = next(r for r in per_model if r["name"] == PART)
    Vn, F, occ, lo, pitch = load_fusion_mesh(PART, str(paths.fusion360_root))
    faces = map_processed_faces(Vn, F, occ, lo, pitch, model.points).face_indices
    gold = np.asarray(model.labels, bool)
    prob = np.asarray(rec["prob"], float)
    cam = cad_render.underside_camera(Vn)

    img_part = cad_render.render(Vn, F, camera=cam)
    img_contact = cad_render.render(Vn, F, faces, np.tile(to_rgb(ORANGE), (len(faces), 1)), camera=cam)
    label_rgb = np.where(gold[:, None], to_rgb(S.INACCESSIBLE), to_rgb(S.ACCESSIBLE))
    img_label = cad_render.render(Vn, F, faces, label_rgb, key_mask=gold, camera=cam)
    img_vox = cad_render.render_voxels(occ, lo, pitch, cam)
    cmap = probability_cmap()
    img_prob = cad_render.render(Vn, F, faces, cmap(prob)[:, :3], key_mask=prob >= 0.5, camera=cam)

    W, H = S.DOUBLE_MM, 84.0
    fig = S.figure(W, H)

    def box(x, y, w, h):                     # 毫米坐标 → 图坐标
        return [x / W, y / H, w / W, h / H]

    def image(img, x, y, w, h, caption):
        ax = fig.add_axes(box(x, y, w, h))
        ax.imshow(img, interpolation="lanczos"); ax.set_axis_off(); ax.set_anchor("C")
        fig.text((x + w / 2) / W, (y - 1.0) / H, caption, ha="center", va="top", color=S.INK)
        return ax

    def arrow(x0, y0, x1, y1, text=None, dx=0.0, dy=1.5, ha="center"):
        fig.patches.append(FancyArrowPatch((x0 / W, y0 / H), (x1 / W, y1 / H), transform=fig.transFigure,
                                           arrowstyle="-|>", mutation_scale=7, lw=0.8, color=S.GREY))
        if text:
            fig.text(((x0 + x1) / 2 + dx) / W, ((y0 + y1) / 2 + dy) / H, text, ha=ha, va="bottom",
                     color=S.GREY)

    def block(x, y, w, h, text, face="#F4F5F6", edge="#8A9096"):
        fig.patches.append(FancyBboxPatch((x / W, y / H), w / W, h / H, transform=fig.transFigure,
                                          boxstyle="round,pad=0.002,rounding_size=0.006",
                                          facecolor=face, edgecolor=edge, lw=0.6))
        fig.text((x + w / 2) / W, (y + h / 2) / H, text, ha="center", va="center", color=S.INK,
                 linespacing=1.35)

    # 泳道：细边框 + 标题（白底，避免渲染图显出底框）
    for y0, h, title in ((44.0, 39.0, "几何判定（离线生成标签）"), (1.0, 41.0, "形状条件预测（在线查询）")):
        fig.patches.append(FancyBboxPatch((1.0 / W, y0 / H), (W - 2.0) / W, h / H, transform=fig.transFigure,
                                          boxstyle="round,pad=0,rounding_size=0.008", facecolor="none",
                                          edgecolor="#D5D8DB", lw=0.5, zorder=-5))
        fig.text((W - 3.0) / W, (y0 + h - 1.4) / H, title, ha="right", va="top", color=S.INK, fontweight="bold")

    # 上泳道
    ax = image(img_part, 4.0, 49.0, 34.0, 28.0, f"(a) 零件与构建方向 {S.var('d')}")
    ax.annotate("", xy=(0.04, 0.92), xytext=(0.04, 0.60), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=S.INK, lw=0.9, mutation_scale=7))
    ax.text(0.08, 0.82, S.var("d"), transform=ax.transAxes, color=S.INK)
    arrow(38.5, 63.0, 43.5, 63.0)
    image(img_contact, 44.0, 49.0, 34.0, 28.0, f"(b) 下朝接触区 {S.var('S')}({S.var('P')}, {S.var('d')})")
    arrow(78.5, 63.0, 83.5, 63.0)
    block(84.0, 54.0, 44.0, 18.0, "两级几何判定\n距离场筛选 64 个下半球方向\n边界带内以胶囊–网格精确求交")
    arrow(128.5, 63.0, 133.5, 63.0)
    image(img_label, 134.0, 49.0, 34.0, 28.0, "(c) 点级标签（红：不可达）")

    # 下泳道
    arrow(21.0, 45.5, 21.0, 38.5, "体素化", dx=1.5, dy=-1.2, ha="left")
    image(img_vox, 4.0, 7.0, 34.0, 28.0, "(d) 占据栅格（最长边 48）")
    arrow(38.5, 21.0, 43.5, 21.0)
    block(44.0, 14.0, 26.0, 14.0, f"三维卷积编码\n{S.var('Z')} = {S.var('E')}({S.var('O')})")
    arrow(70.5, 21.0, 74.5, 21.0)
    block(75.0, 14.0, 26.0, 14.0, f"查询点三线性采样\n[{S.var('z')}({S.var('p')}), {S.var('p')}]")
    arrow(101.5, 21.0, 105.5, 21.0)
    block(106.0, 14.0, 22.0, 14.0, "MLP 解码\n点级 / 方向级输出")
    arrow(128.5, 21.0, 133.5, 21.0)
    image(img_prob, 134.0, 7.0, 34.0, 28.0, "(e) 未见零件上的不可达概率")
    arrow(140.0, 45.0, 120.0, 28.5, "训练监督", dx=-3.0, dy=0.5, ha="right")

    cax = fig.add_axes(box(168.5, 10.0, 1.6, 20.0))
    import matplotlib as mpl
    cb = fig.colorbar(mpl.cm.ScalarMappable(cmap=cmap), cax=cax, ticks=[0, 0.5, 1])
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(length=1.5, width=0.4, pad=1)
    print("SAVED", S.save(fig, "method_overview"))


if __name__ == "__main__":
    main()
