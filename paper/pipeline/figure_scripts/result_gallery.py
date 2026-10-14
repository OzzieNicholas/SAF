"""结果画廊：固定留出模型在未见零件上的预测，按逐件 F1 排名等距选件，整件仰视渲染。

每件只用一张渲染同时表达标签、预测与误差：浅蓝 = 判对的可达接触面，红 = 判对的不可达接触面，
橙 = 误报，深紫 = 漏报；误差面另加深色轮廓，灰度打印仍可辨。选件规则固定为「80 件按 F1 升序后
等距取 12 件」，失败件按比例进入画面，不挑选。

用法：python -m paper.pipeline.figure_scripts.result_gallery
"""

from paper.pipeline.figure_scripts import cad_render, journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_fusion_mesh, load_run, map_processed_faces

N_SHOW = 12
COLS = 4


def _select(per_model, n_show):
    import numpy as np
    order = sorted(per_model, key=lambda r: (r["f1"], r["name"]))
    ranks = np.round(np.linspace(0, len(order) - 1, n_show)).astype(int)
    return [(int(k), order[k]) for k in ranks]


def main():
    import numpy as np
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Patch
    from support_accessibility.runtime.data_paths import resolve_data_paths
    from support_accessibility.data.dataset import load_dataset

    run = load_run("holdout_model")["runs"][0]                     # 训练种子 0
    paths = resolve_data_paths()
    models, _ = load_dataset(str(paths.processed_root("fusion360")))
    by_name = {m.name: m for m in models}
    chosen = _select(run["per_model"], N_SHOW)

    tiles = []
    for rank, rec in chosen:
        m = by_name[rec["name"]]
        Vn, F, occ, lo, pitch = load_fusion_mesh(m.name, str(paths.fusion360_root))
        mapping = map_processed_faces(Vn, F, occ, lo, pitch, m.points)
        gold = np.asarray(m.labels, bool)
        pred = np.asarray(rec["prob"]) >= 0.5
        colours = np.empty((gold.size, 3))
        colours[~gold & ~pred] = to_rgb(S.ACCESSIBLE)
        colours[gold & pred] = to_rgb(S.INACCESSIBLE)
        colours[~gold & pred] = to_rgb(S.FALSE_ALARM)
        colours[gold & ~pred] = to_rgb(S.MISSED)
        image = cad_render.render(Vn, F, mapping.face_indices, colours, gold | pred, gold != pred)
        tiles.append((rank, rec, int(gold.sum()), int(gold.size), int((~gold & pred).sum()),
                      int((gold & ~pred).sum()), image))
        print(f"rendered rank {rank} {m.name} f1={rec['f1']:.3f}", flush=True)

    rows = int(np.ceil(N_SHOW / COLS))
    cell_w, cell_h, text_h, legend_h = S.DOUBLE_MM / COLS, 36.0, 9.0, 7.0
    height = rows * (cell_h + text_h) + legend_h
    fig = S.figure(S.DOUBLE_MM, height)
    for i, (rank, rec, n_inacc, n_pts, n_fp, n_fn, image) in enumerate(tiles):
        r, c = divmod(i, COLS)
        top = height - r * (cell_h + text_h)
        ax = fig.add_axes([(c * cell_w + 1.0) / S.DOUBLE_MM, (top - cell_h) / height,
                           (cell_w - 2.0) / S.DOUBLE_MM, (cell_h - 1.0) / height])
        ax.imshow(image, interpolation="lanczos")
        ax.set_axis_off()
        ax.set_anchor("S")
        fig.text((c * cell_w + cell_w / 2) / S.DOUBLE_MM, (top - cell_h - 1.2) / height,
                 f"({chr(97 + i)})  {S.F1} = {rec['f1']:.2f}\n不可达 {n_inacc}/{n_pts}，误报 {n_fp}，漏报 {n_fn}",
                 ha="center", va="top", color=S.INK, linespacing=1.35)
    handles = [Patch(facecolor=S.ACCESSIBLE, label="可达（判对）"),
               Patch(facecolor=S.INACCESSIBLE, label="不可达（判对）"),
               Patch(facecolor=S.FALSE_ALARM, edgecolor=S.ERROR_EDGE, linewidth=0.8, label="误报"),
               Patch(facecolor=S.MISSED, edgecolor=S.ERROR_EDGE, linewidth=0.8, label="漏报"),
               Patch(facecolor=S.PART, label="非接触面")]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.0),
               handlelength=1.6, handleheight=0.9, columnspacing=1.6)
    print("SAVED", S.save(fig, "result_gallery"))


if __name__ == "__main__":
    main()
