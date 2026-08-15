#!/usr/bin/env python3
"""Figure 7. Two large, same-ROI unseen prediction cases."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _data as D  # noqa: E402
import examples as X  # noqa: E402
import style as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CMAP = mcolors.LinearSegmentedColormap.from_list("blocked_probability", [S.ACC, "#F5F5F3", S.INACC])


def _label_rgb(labels):
    result = np.tile(np.asarray(S.ACC_RGB), (len(labels), 1))
    result[np.asarray(labels, bool)] = S.INACC_RGB
    return result


def _metrics(prediction, gold):
    prediction = np.asarray(prediction, bool); gold = np.asarray(gold, bool)
    tp = np.sum(prediction & gold); fp = np.sum(prediction & ~gold); fn = np.sum(~prediction & gold)
    f1 = 2 * tp / max(2 * tp + fp + fn, 1)
    iou = tp / max(tp + fp + fn, 1)
    return f1, iou, fp, fn


def main():
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=X.FUSION_ROOT)
    parser.add_argument("--thingi-root", default=X.THINGI_ROOT)
    args = parser.parse_args()
    checkpoint = torch.load(os.path.join(ROOT, "artifacts", "cache", "figures", "ckpt_point.pt"),
                            map_location="cpu", weights_only=False)
    network = ConvONetLite(); network.load_state_dict(checkpoint["state_dict"]); network.eval()
    fusion, _ = load_dataset(os.path.join(ROOT, "data", "processed", "fusion360_full"))
    thingi, _ = load_dataset(os.path.join(ROOT, "data", "processed", "thingi_v1"))
    datasets = {"fusion": {model.name: model for model in fusion},
                "thingi": {model.name: model for model in thingi}}

    cases = []
    for example in X.FIG07:
        X.assert_checkpoint_holdout(checkpoint, example, "Figure 7")
        model = datasets[example.source][example.name]
        labels = np.asarray(model.labels, bool)
        with torch.no_grad():
            occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape)
            probability = torch.sigmoid(network(occ, to_grid_coords(model.points, model.occ.shape))).numpy().ravel()
        prediction = probability >= .5
        if example.source == "fusion":
            V, F, raw_occ, lo, pitch = D.load_fusion_mesh(example.name, args.root)
            mapping = D.map_processed_faces(V, F, raw_occ, lo, pitch, model.points, "fusion")
        else:
            V, F, raw_occ, lo, pitch, normals = D.load_thingi_mesh(
                example.name, args.thingi_root, include_normals=True
            )
            mapping = D.map_processed_faces(V, F, raw_occ, lo, pitch, model.points,
                                            "thingi", stored_normals=normals)
        if raw_occ.shape != model.occ.shape or not np.array_equal(raw_occ, np.asarray(model.occ, bool)):
            raise RuntimeError(f"Figure 7 raw occupancy mismatch: {example.name}")
        error = prediction != labels
        focus_faces = mapping.face_indices[error]
        if not len(focus_faces):
            focus_faces = mapping.face_indices[labels]
        evidence_camera, focus = D.face_evidence_camera(V, F, focus_faces)
        roi_zoom = max(example.roi_zoom, 3.15)
        # Error faces can be much smaller than the label field, so the dedicated
        # error panel uses a tighter crop around the same evidence focus.
        error_zoom = roi_zoom * (1.50 if example.source == "fusion" else 2.0)
        error_context_opacity = 1.0
        if example.source == "thingi":
            # Some mapped source faces lie behind neighboring raw triangles. Keep
            # that context visible without letting it hide the exact error faces.
            error_zoom = max(error_zoom, 8.0)
            error_context_opacity = .10
        span = float(np.linalg.norm(V.max(0) - V.min(0)))
        face_centres = V[np.asarray(F)].mean(axis=1)
        field_mask = np.ones(len(mapping.face_indices), dtype=bool)
        context_mask = None
        if example.source == "fusion":
            field_mask = np.linalg.norm(
                face_centres[mapping.face_indices] - focus, axis=1
            ) <= .32 * span
            context_mask = np.zeros(len(F), dtype=bool)
        field_indices = mapping.face_indices[field_mask]
        if context_mask is not None:
            context_mask[field_indices] = True
        global_view = D.render_mesh_technical_arr(V, F, zoom=example.zoom,
                                                  azimuth=example.azimuth,
                                                  elevation=example.elevation,
                                                  wsize=(1350, 950))
        outline_fields = example.source == "thingi"
        oracle = D.render_face_field_arr(V, F, field_indices, _label_rgb(labels[field_mask]),
                                         cpos=evidence_camera, zoom=roi_zoom, focus=focus,
                                         wsize=(1650, 1050), context_face_mask=context_mask,
                                         selected_edges=outline_fields, selected_edge_width=12.0)
        predicted = D.render_face_field_arr(V, F, field_indices, CMAP(probability[field_mask])[:, :3],
                                            cpos=evidence_camera, zoom=roi_zoom, focus=focus,
                                            wsize=(1650, 1050), context_face_mask=context_mask,
                                            selected_edges=outline_fields,
                                            selected_edge_colors=_label_rgb(
                                                probability[field_mask] >= .5
                                            ) if outline_fields else None,
                                            selected_edge_width=12.0)
        shown_error = error & field_mask
        error_indices = mapping.face_indices[shown_error]
        error_colours = np.empty((len(error_indices), 3), float)
        fp_mask = prediction[shown_error] & ~labels[shown_error]
        error_colours[fp_mask] = mcolors.to_rgb(S.ORANGE)
        error_colours[~fp_mask] = mcolors.to_rgb(S.FN)
        errors = D.render_face_field_arr(V, F, error_indices, error_colours,
                                         cpos=evidence_camera, zoom=error_zoom, focus=focus,
                                         wsize=(1650, 1050), selected_edges=True,
                                         context_face_mask=context_mask, selected_edge_width=12.0,
                                         context_opacity=error_context_opacity)
        cases.append((example, global_view, oracle, predicted, errors,
                      _metrics(probability >= .5, labels)))

    fig = plt.figure(figsize=S.double_column(112))
    grid = fig.add_gridspec(2, 4, width_ratios=(.82, 1, 1, 1), left=.035, right=.985,
                            bottom=.11, top=.92, wspace=.055, hspace=.20)
    headings = ("全局定位", "几何判定器 ROI", "网络概率 ROI（蓝0 → 红1）", "显式误差 ROI")
    for row, (example, global_view, oracle, predicted, errors, metric) in enumerate(cases):
        images = (global_view, oracle, predicted, errors)
        for col, image in enumerate(images):
            axis = fig.add_subplot(grid[row, col])
            semantic_min = 0.0
            if col > 0:
                if example.source == "fusion":
                    semantic_min = .02 if col < 3 else .009
                else:
                    semantic_min = .002 if col < 3 else .0004
            S.imshow_cad(axis, image, semantic_min=semantic_min)
            if col == 0:
                source = "Fusion / checkpoint holdout" if example.source == "fusion" else "Thingi10K / cross-domain test"
                axis.text(.0, -.04, source, transform=axis.transAxes, ha="left", va="top",
                          fontsize=7.5, color=S.NEUTRAL, clip_on=False)
        f1, iou, fp, fn = metric
        y = .512 if row == 0 else .075
        fig.text(.985, y, f"F1 {f1:.3f}  ·  IoU {iou:.3f}  ·  FN {fn}  ·  FP {fp}",
                 ha="right", fontsize=7.5, color=S.INK)
    for xpos, heading in zip((.13, .37, .62, .865), headings):
        fig.text(xpos, .955, heading, ha="center", fontsize=8.3, fontweight="bold", color=S.INK)
    fig.text(.012, .80, "(a) Fusion 留出件", fontsize=8.4, fontweight="bold", color=S.INK)
    fig.text(.012, .37, "(b) Thingi10K 跨域件", fontsize=8.4, fontweight="bold", color=S.INK)
    fig.legend([Patch(fc=S.ACC), Patch(fc=S.INACC), Patch(fc=S.FN), Patch(fc=S.ORANGE)],
               ["可达", "不可达", "FN", "FP"], ncol=4, loc="lower center",
               bbox_to_anchor=(.54, .005), frameon=False)
    print("SAVED", S.save(fig, "fig07_prediction_heatmap"))


if __name__ == "__main__":
    main()
