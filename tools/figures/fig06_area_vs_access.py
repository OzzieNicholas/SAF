#!/usr/bin/env python3
"""Figure 6. Matched real parts and full-data evidence that area is not access."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _colours(labels):
    result = np.tile(np.asarray(S.ACC_RGB), (len(labels), 1))
    result[np.asarray(labels, bool)] = S.INACC_RGB
    return result


def _scatter(ax, x, y, pair_rows, xkey, ykey, title, rho, xlabel, log=False):
    ax.scatter(x, y, s=5, alpha=.16, color=S.ACC, edgecolors="none", rasterized=True)
    for row, colour, marker in zip(pair_rows, (S.ACC, S.INACC), ("o", "s")):
        ax.scatter([row[xkey]], [row[ykey]], s=46, c=colour, marker=marker,
                   edgecolors="white", linewidths=.7, zorder=4)
    if log:
        ax.set_xscale("log")
    ax.set_ylim(-.03, 1.03)
    ax.set_xlabel(xlabel); ax.set_ylabel("不可达占比")
    ax.set_title(title, loc="left", fontsize=8.4, fontweight="bold", pad=3)
    ax.text(.98, .94, rf"Spearman $\rho={rho:.3f}$", transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5, color=S.INK)
    ax.grid(axis="y"); ax.set_axisbelow(True)


def main():
    from support_accessibility.data.dataset import load_dataset

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    parser.add_argument("--area-json", default=os.path.join(ROOT, "runs", "true_area", "latest.json"))
    args = parser.parse_args()
    if not os.path.exists(args.area_json):
        raise FileNotFoundError("Figure 6 requires runs/true_area/latest.json; run tools/eval_true_area.py")
    with open(args.area_json, encoding="utf-8") as handle:
        area_report = json.load(handle)
    records = area_report.get("per_model", [])
    if not records:
        raise RuntimeError("true-area artifact has no per-model records")
    records_by_name = {item["name"]: item for item in records}

    models, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    by_name = {model.name: model for model in models}
    images = []
    pair_rows = []
    for example in X.FIG06_PAIR:
        model = by_name[example.name]
        loaded = D.load_fusion_mesh(example.name, args.root)
        if loaded is None:
            raise FileNotFoundError(f"Missing Fusion mesh: {example.name}")
        V, F, occ, lo, pitch = loaded
        mapping = D.map_processed_faces(V, F, occ, lo, pitch, model.points)
        record = records_by_name.get(example.name)
        if record is None:
            raise RuntimeError(f"true-area artifact does not contain {example.name}")
        if int(record["contact_count"]) != 84:
            raise RuntimeError("Figure 6 matched pair no longer has 84 contact faces each")
        global_view = D.render_mesh_technical_arr(V, F, zoom=example.zoom,
                                                  azimuth=example.azimuth,
                                                  elevation=example.elevation,
                                                  wsize=(1300, 950))
        labels = np.asarray(model.labels, bool)
        selected = mapping.face_indices[labels] if labels.any() else mapping.face_indices
        focus = V[np.asarray(F)[selected]].mean(axis=(0, 1))
        evidence_camera = D.underside_camera(V)
        roi = D.render_face_field_arr(V, F, mapping.face_indices, _colours(labels),
                                      cpos=evidence_camera, zoom=example.roi_zoom,
                                      focus=focus,
                                      wsize=(1700, 1050))
        images.append((global_view, roi, example, model, mapping, record))
        pair_rows.append(record)

    count_x = np.asarray([item["contact_count"] for item in records], float)
    count_y = np.asarray([item["inaccessible_count_fraction"] for item in records], float)
    area_x = np.asarray([item["contact_area"] for item in records], float)
    area_y = np.asarray([item["inaccessible_area_fraction"] for item in records], float)

    fig = plt.figure(figsize=S.double_column(100))
    outer = fig.add_gridspec(1, 2, width_ratios=(1.24, 1), left=.035, right=.985,
                             bottom=.12, top=.925, wspace=.16)
    parts = outer[0].subgridspec(4, 2, width_ratios=(.78, 1.12),
                                 height_ratios=(.16, 1, .16, 1),
                                 wspace=.08, hspace=.08)
    for row, (global_view, roi, example, model, mapping, record) in enumerate(images):
        image_row = 2 * row + 1
        global_axis = fig.add_subplot(parts[image_row, 0])
        roi_axis = fig.add_subplot(parts[image_row, 1])
        S.imshow_cad(global_axis, global_view)
        S.imshow_cad(roi_axis, roi, semantic=True)
        metric_axis = fig.add_subplot(parts[image_row - 1, :])
        metric_axis.set_axis_off()
        inaccessible = int(np.asarray(model.labels, bool).sum())
        metric_axis.text(0, .5, f"({chr(97 + row)}) {example.label}",
                         ha="left", va="center", fontsize=8.4, fontweight="bold",
                         transform=metric_axis.transAxes)
        metric_axis.text(.22, .5,
                         f"84 个保留面  ·  接触面积 {record['contact_area']:.4f}  ·  "
                         f"不可达 {inaccessible}/84（{100 * np.mean(model.labels):.1f}%）",
                         ha="left", va="center", fontsize=7.5, color=S.INK,
                         transform=metric_axis.transAxes)
    fig.text(.13, .955, "全局零件", ha="center", fontsize=8.0, color=S.INK)
    fig.text(.335, .955, "下视三分之四 ROI：真实接触面", ha="center",
             fontsize=8.0, color=S.INK)

    charts = outer[1].subgridspec(2, 1, hspace=.43)
    count_axis = fig.add_subplot(charts[0])
    _scatter(count_axis, count_x, count_y, pair_rows, "contact_count",
             "inaccessible_count_fraction", "(c) 接触面计数代理",
             area_report["count_proxy_same_models"]["spearman_all"],
             "保留接触面数（对数）", log=True)
    area_axis = fig.add_subplot(charts[1])
    _scatter(area_axis, area_x, area_y, pair_rows, "contact_area",
             "inaccessible_area_fraction", "(d) 真实三角面积",
             area_report["true_area"]["spearman_all"],
             "归一化接触面积（对数）", log=True)
    fig.text(.035, .045, "蓝：可达  ·  红：不可达  ·  选中方/圆点对应左侧匹配零件",
             fontsize=7.5, color=S.NEUTRAL)
    print("SAVED", S.save(fig, "fig06_area_vs_access"))


if __name__ == "__main__":
    main()
