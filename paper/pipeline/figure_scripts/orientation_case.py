"""方向评价示例：同一留出零件在 6 个轴向构建方向下的支撑接触区可达性风险。

上排：零件旋转到各候选方向（构建方向朝上）后的仰视渲染，接触面按几何标签着色（红：不可达）；
下排：各方向的下朝接触总面积、真实不可达接触面积与网络预测的不可达接触面积。
选件规则（固定）：在「接触面积最小的方向」不属于真实最低风险方向的零件中，取真实不可达面积在方向间
极差最大者。条形图数值取自 orientation_evaluation 的逐件记录；渲染时重算标签并核对面积与记录一致。

用法：python -m paper.pipeline.figure_scripts.orientation_case
"""

from paper.pipeline.figure_scripts import cad_render, journal_style as S
from paper.pipeline.figure_scripts.figure_data import load_run
from support_accessibility.data.overhang import AXIS_BUILD_ROTATIONS

ORDER = tuple(AXIS_BUILD_ROTATIONS)


def _axis_label(key):
    """'+z' / '-z' → 排版用的 +z / −z（真负号、斜体轴名）。"""
    return ("−" if key[0] == "-" else "+") + S.var(key[1])


def choose(parts):
    import numpy as np
    best, score = None, -1.0
    for p in parts:
        o = p["orientations"]
        true = np.array([o[k]["true_inacc_area"] for k in ORDER])
        area = np.array([o[k]["contact_area"] for k in ORDER])
        if np.isclose(true[int(np.argmin(area))], true.min(), rtol=0, atol=1e-12):
            continue                                   # 接触面积已选中最低风险方向：不是反例
        spread = float(true.max() - true.min())
        if spread > score:
            best, score = p, spread
    return best


def main():
    import numpy as np
    from matplotlib.colors import to_rgb
    from support_accessibility.data import mesh as MESH
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility.runtime.data_paths import resolve_data_paths

    run = load_run("orientation_evaluation")
    part = choose(run["parts"])
    paths = resolve_data_paths()
    V, F = load_obj(dict(iter_final_designs(str(paths.fusion360_root)))[part["name"]])

    images = []
    for key in ORDER:
        Vr, _ = normalize(np.asarray(V, float) @ np.asarray(AXIS_BUILD_ROTATIONS[key], float).T)
        lab = MESH.label_mesh(Vr, F)
        gold = lab["labels"]
        inacc_area = MESH.face_areas(Vr, F, lab["faces"][gold]).sum()
        recorded = part["orientations"][key]["true_inacc_area"]
        if not np.isclose(inacc_area, recorded, rtol=1e-6, atol=1e-9):
            raise RuntimeError(f"{part['name']} {key}: 重算不可达面积 {inacc_area} ≠ 记录 {recorded}")
        rgb = np.where(gold[:, None], to_rgb(S.INACCESSIBLE), to_rgb(S.ACCESSIBLE))
        images.append(cad_render.render(Vr, F, lab["faces"], rgb, key_mask=gold, wsize=(900, 900)))
        print(f"rendered {key}", flush=True)

    fig = S.figure(S.DOUBLE_MM, 74.0)
    cell = 1.0 / len(ORDER)
    for i, (key, img) in enumerate(zip(ORDER, images)):
        ax = fig.add_axes([i * cell + 0.006, 0.50, cell - 0.012, 0.42])
        ax.imshow(img, interpolation="lanczos"); ax.set_axis_off(); ax.set_anchor("S")
        fig.text((i + 0.5) * cell, 0.95, f"{S.var('d')} = {_axis_label(key)}", ha="center", va="bottom")

    bx = fig.add_axes([0.07, 0.10, 0.91, 0.30])
    x = np.arange(len(ORDER))
    o = part["orientations"]
    contact = np.array([o[k]["contact_area"] for k in ORDER])
    true = np.array([o[k]["true_inacc_area"] for k in ORDER])
    pred = np.array([np.mean(o[k]["pred_inacc_area_by_seed"]) for k in ORDER])
    pred_sd = np.array([np.std(o[k]["pred_inacc_area_by_seed"]) for k in ORDER])
    w = 0.26
    bx.bar(x - w, contact, w, color="#C3C8CC", label="下朝接触总面积")
    bx.bar(x, true, w, color=S.INACCESSIBLE, label="真实不可达接触面积")
    bx.bar(x + w, pred, w, color="white", edgecolor=S.INACCESSIBLE, hatch="////", lw=0.7, yerr=pred_sd,
           error_kw=dict(lw=0.6, capsize=1.2), label="网络预测不可达面积（5 种子）")
    bx.set_xticks(x, [f"{_axis_label(k)}" for k in ORDER])
    bx.set_xlim(-0.6, len(ORDER) - 0.4)
    bx.set_ylabel("面积（归一化单位）")
    bx.grid(axis="y", color="#E3E5E7", lw=0.4); bx.set_axisbelow(True)
    bx.legend(loc="upper center", bbox_to_anchor=(0.5, 1.22), ncol=3, handlelength=1.4, columnspacing=1.5)
    fig.text(0.5, 0.005, "候选构建方向", ha="center", va="bottom", color=S.INK)
    print("CASE", part["name"])
    print("SAVED", S.save(fig, "orientation_case"))


if __name__ == "__main__":
    main()
