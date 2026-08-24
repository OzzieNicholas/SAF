"""图件数据 / 渲染助手（deliverables/paper/pipeline/figures/*）。

- voxel_surface(occ)：占据栅格 → pyvista blocky 表面（程序化件用）。
- render_voxel_arr(...)：离屏渲染"零件本体 + 下朝接触点（红=不可达/蓝=可达）"→ RGB 数组（供 matplotlib 组图）。
- load_fusion_mesh(name, root)：Fusion .obj → (Vn,F,occ,lo,pitch)，占据与 npz 逐比特校验（同 eval_e5 --root）。
- per_model_area_inacc(ms)：每件（下朝面计数, 不可达占比），供图6(c) 散点。
"""
import os
import sys
from dataclasses import dataclass

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))
if os.path.join(_ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "tools"))
from data_paths import resolve_data_paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # style


def processed_dataset(name):
    """Resolve one external processed dataset without embedding local paths."""
    return str(resolve_data_paths().processed_root(name))


def voxel_surface(occ):
    import warnings
    import numpy as np
    import pyvista as pv
    occ = np.asarray(occ, bool)
    g = pv.ImageData(dimensions=tuple(np.array(occ.shape) + 1))   # 点数=cell+1 → cells=occ.shape
    g.cell_data["occ"] = occ.flatten(order="F").astype(np.uint8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return g.threshold(0.5, scalars="occ").extract_surface()


@dataclass(frozen=True)
class FaceMapping:
    """Exact correspondence between processed contact samples and source faces."""

    face_indices: object
    points_vox: object
    face_areas: object

    @property
    def contact_area(self):
        return float(self.face_areas.sum())


def _finish_camera(plotter, cpos, zoom, azimuth=0.0, elevation=0.0, focus=None):
    """统一论文 CAD 相机：正交投影消除跨面板透视差，并应用固定视角变换。"""
    plotter.camera_position = cpos
    if azimuth:
        plotter.camera.azimuth += azimuth
    if elevation:
        plotter.camera.elevation += elevation
    if focus is not None:
        import numpy as np
        old_focus = np.asarray(plotter.camera.focal_point, float)
        delta = np.asarray(focus, float) - old_focus
        plotter.camera.position = tuple(np.asarray(plotter.camera.position, float) + delta)
        plotter.camera.focal_point = tuple(np.asarray(focus, float))
    plotter.enable_parallel_projection()
    plotter.camera.zoom(zoom)


def underside_camera(vertices, direction=(1.15, -0.90, -1.70)):
    """Return a stable underside three-quarter camera for down-facing evidence."""
    import numpy as np

    vertices = np.asarray(vertices, float)
    centre = vertices.mean(0)
    span = float(np.linalg.norm(vertices.max(0) - vertices.min(0)))
    offset = np.asarray(direction, float)
    offset /= np.linalg.norm(offset)
    position = centre + offset * (2.2 * span)
    return tuple(position), tuple(centre), (0.0, 0.0, 1.0)


def _context_feature_edges_enabled(opacity):
    """Keep low-opacity CAD context subordinate to explicitly selected faces."""
    try:
        value = float(opacity)
    except (TypeError, ValueError) as error:
        raise ValueError("context_opacity must be between 0 and 1") from error
    if not 0.0 <= value <= 1.0:
        raise ValueError("context_opacity must be between 0 and 1")
    return value >= 0.5


def _add_part(plotter, surface, color, opacity=0.94, smooth=True):
    """Opaque technical-CAD material with a separate feature-line pass."""
    plotter.add_mesh(surface, color=color, smooth_shading=smooth, show_edges=False,
                     opacity=opacity, ambient=0.24, diffuse=0.70, specular=0.13,
                     specular_power=22)
    if not _context_feature_edges_enabled(opacity):
        return
    try:
        edges = surface.extract_feature_edges(boundary_edges=True, feature_edges=True,
                                              manifold_edges=False, non_manifold_edges=True,
                                              feature_angle=34.0)
        if edges.n_cells:
            plotter.add_mesh(edges, color="#48535B", line_width=1.15, opacity=0.72,
                             lighting=False)
    except (AttributeError, ValueError):
        pass


def _new_plotter(window_size):
    import style as S

    pv = S.pv_theme()
    plotter = pv.Plotter(off_screen=True, window_size=window_size)
    try:
        plotter.enable_ssao(radius=0.08, bias=0.004, kernel_size=128, blur=True)
    except (AttributeError, RuntimeError):
        pass
    return pv, plotter


def crop_render(image, pad_fraction=0.05):
    """Crop white render margins deterministically while retaining print-safe padding."""
    import numpy as np

    rgb = np.asarray(image)[..., :3]
    mask = np.any(rgb < 248, axis=2)
    yy, xx = np.where(mask)
    if not len(xx):
        return rgb
    width, height = xx.max() - xx.min() + 1, yy.max() - yy.min() + 1
    pad = max(6, int(round(max(width, height) * pad_fraction)))
    x0, x1 = max(0, xx.min() - pad), min(rgb.shape[1], xx.max() + pad + 1)
    y0, y1 = max(0, yy.min() - pad), min(rgb.shape[0], yy.max() + pad + 1)
    return rgb[y0:y1, x0:x1]


def _clip(surface, clip_origin=None, clip_normal=None):
    """Apply an explicit section plane only when a figure declares one."""
    if clip_origin is None or clip_normal is None:
        return surface
    return surface.clip(normal=clip_normal, origin=clip_origin, invert=False)


def map_processed_faces(Vn, F, occ, lo, pitch, points_vox, source="fusion",
                        stored_normals=None, direction=(0.0, 0.0, 1.0),
                        overhang_deg=45.0, nudge_voxels=2.0, thingi_max_points=400,
                        seed=0, atol=1e-2):
    """Reproduce D-028 ingest and map every processed point to its source face.

    The processed point order is part of the evidence contract.  Any mismatch
    fails closed so a figure can never colour a merely nearby triangle.
    """
    import numpy as np
    from support_accessibility.data import mesh as MESH
    from support_accessibility.data import overhang as OVH

    V = np.asarray(Vn, float)
    Fa = np.asarray(F, np.int64)
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    if source == "thingi":
        from support_accessibility.data.thingi import _outward_normals, _select_points

        normals, centres = _outward_normals(V, Fa, stored_normals)
        mask = np.sum(normals * d[None, :], axis=1) < -np.cos(np.radians(overhang_deg))
        face_indices = np.flatnonzero(mask)
        centres, normals = centres[mask], normals[mask]
        selected = _select_points(len(centres), thingi_max_points, seed)
        if selected is not None:
            centres, normals, face_indices = centres[selected], normals[selected], face_indices[selected]
    else:
        contact = OVH.support_contact_faces(V, Fa, d, overhang_deg)
        face_indices = np.asarray(contact.indices, int)
        centres = np.asarray(contact.centroids, float)
        normals = np.asarray(contact.normals, float)

    kept_faces, kept_points = [], []
    for face_index, centre, normal in zip(face_indices, centres, normals):
        status, point = MESH.nudge_to_free(
            np.asarray(occ, bool), centre, normal, nudge_voxels * float(pitch), lo, pitch
        )
        if status == "flipped":
            continue
        kept_faces.append(int(face_index))
        kept_points.append(point)
    kept_points = np.asarray(kept_points, np.float32).reshape(-1, 3)
    expected = np.asarray(points_vox, np.float32).reshape(-1, 3)
    if len(kept_faces) != len(expected) or not np.allclose(kept_points, expected, atol=atol):
        delta = float(np.max(np.abs(kept_points - expected))) if kept_points.shape == expected.shape and len(expected) else None
        raise RuntimeError(
            f"D-028 face mapping mismatch: source={source}, mapped={len(kept_faces)}, "
            f"processed={len(expected)}, max_delta={delta}"
        )
    triangles = V[Fa[np.asarray(kept_faces, int)]]
    areas = 0.5 * np.linalg.norm(
        np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1
    )
    return FaceMapping(np.asarray(kept_faces, int), kept_points, np.asarray(areas, float))


def render_face_field_arr(Vn, F, face_indices, colors_rgb, cpos="iso", zoom=1.3,
                          azimuth=0.0, elevation=0.0, wsize=(1400, 1000),
                          focus=None, clip_origin=None, clip_normal=None,
                          crop=True, base_color=None, selected_edges=False,
                          context_face_mask=None, selected_edge_colors=None,
                          selected_edge_width=5.0, context_opacity=1.0):
    """Render exact source faces with opaque selections and optional CAD context."""
    import numpy as np
    import pyvista as pv
    import style as S

    V = np.asarray(Vn, float)
    Fa = np.asarray(F, np.int64)
    selected = np.asarray(face_indices, int)
    colors = np.asarray(colors_rgb, float).reshape(-1, 3)
    if len(selected) != len(colors):
        raise ValueError("face_indices and colors_rgb must have equal length")
    opacity = float(context_opacity)
    show_context_feature_edges = _context_feature_edges_enabled(opacity)
    _pv, plotter = _new_plotter(wsize)
    keep = (np.ones(len(Fa), dtype=bool) if context_face_mask is None
            else np.asarray(context_face_mask, bool).copy())
    if keep.shape != (len(Fa),):
        raise ValueError("context_face_mask must have one value per source face")
    if len(selected) and not np.all(keep[selected]):
        raise ValueError("selected faces must be included in context_face_mask")
    keep[selected] = False
    base_faces = np.hstack([np.full((int(keep.sum()), 1), 3), Fa[keep]]).astype(np.int64).ravel()
    base = _clip(pv.PolyData(V, base_faces), clip_origin, clip_normal)
    _add_part(plotter, base, base_color or S.PART_RGB, opacity=opacity)
    if len(selected):
        coloured_faces = np.hstack([np.full((len(selected), 1), 3), Fa[selected]]).astype(np.int64).ravel()
        coloured_raw = pv.PolyData(V, coloured_faces)
        coloured_raw.cell_data["rgb"] = np.clip(colors * 255, 0, 255).astype(np.uint8)
        coloured = _clip(coloured_raw, clip_origin, clip_normal)
        if coloured.n_cells:
            plotter.add_mesh(coloured, scalars="rgb", rgb=True, smooth_shading=False,
                             show_edges=False, lighting=False)
            if selected_edges:
                edge_colours = (colors if selected_edge_colors is None
                                else np.asarray(selected_edge_colors, float).reshape(-1, 3))
                if len(edge_colours) != len(selected):
                    raise ValueError("selected_edge_colors must match face_indices")
                quantized = np.clip(np.round(edge_colours * 255), 0, 255).astype(np.uint8)
                for rgb in np.unique(quantized, axis=0):
                    group = np.all(quantized == rgb, axis=1)
                    group_faces = np.hstack([
                        np.full((int(group.sum()), 1), 3), Fa[selected[group]]
                    ]).astype(np.int64).ravel()
                    lines = pv.PolyData(V, group_faces).extract_feature_edges(
                        boundary_edges=True, feature_edges=False, manifold_edges=False,
                        non_manifold_edges=True
                    )
                    if lines.n_cells:
                        plotter.add_mesh(lines, color=tuple((rgb / 255.0).tolist()),
                                         line_width=float(selected_edge_width), lighting=False)
    # Selected error boundaries remain visible even when context is faded.
    if show_context_feature_edges:
        shown = keep.copy()
        shown[selected] = True
        all_faces = np.hstack([
            np.full((int(shown.sum()), 1), 3), Fa[shown]
        ]).astype(np.int64).ravel()
        full = _clip(pv.PolyData(V, all_faces), clip_origin, clip_normal)
        try:
            edges = full.extract_feature_edges(boundary_edges=True, feature_edges=True,
                                               manifold_edges=False, non_manifold_edges=True,
                                               feature_angle=34.0)
            if edges.n_cells:
                plotter.add_mesh(edges, color="#48535B", line_width=1.2,
                                 opacity=0.78, lighting=False)
        except (AttributeError, ValueError):
            pass
    _finish_camera(plotter, cpos, zoom, azimuth, elevation, focus=focus)
    image = plotter.screenshot(return_img=True)
    plotter.close()
    return crop_render(image) if crop else np.asarray(image)[..., :3]


def dense_face_focus(vertices, faces, face_indices, radius_fraction=0.20):
    """Focus an ROI on the densest deterministic cluster of selected faces."""
    import numpy as np

    vertices = np.asarray(vertices, float)
    indices = np.asarray(face_indices, int)
    if not len(indices):
        return vertices.mean(0)
    centres = vertices[np.asarray(faces, int)[indices]].mean(axis=1)
    span = float(np.linalg.norm(vertices.max(0) - vertices.min(0)))
    distances = np.linalg.norm(centres[:, None, :] - centres[None, :, :], axis=2)
    neighbour = distances <= radius_fraction * span
    seed = int(np.argmax(neighbour.sum(axis=1)))
    return centres[neighbour[seed]].mean(axis=0)


def face_evidence_camera(vertices, faces, face_indices, radius_fraction=0.20):
    """Aim at a dense selected-face cluster from its exposed side."""
    import numpy as np

    vertices = np.asarray(vertices, float)
    faces = np.asarray(faces, int)
    indices = np.asarray(face_indices, int)
    focus = dense_face_focus(vertices, faces, indices, radius_fraction)
    triangles = vertices[faces[indices]]
    centres = triangles.mean(axis=1)
    span = float(np.linalg.norm(vertices.max(0) - vertices.min(0)))
    cluster = np.linalg.norm(centres - focus, axis=1) <= radius_fraction * span
    local = triangles[cluster] if cluster.any() else triangles
    normals = np.cross(local[:, 1] - local[:, 0], local[:, 2] - local[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    normal = normals.mean(axis=0)
    normal /= np.linalg.norm(normal)
    radial = focus - vertices.mean(axis=0)
    if np.linalg.norm(radial) > 1e-9:
        radial /= np.linalg.norm(radial)
    view = normal + 0.42 * radial
    view /= np.linalg.norm(view)
    up = np.array([0., 1., 0.]) if abs(view[2]) > .72 else np.array([0., 0., 1.])
    return (tuple(focus + view * (2.2 * span)), tuple(focus), tuple(up)), focus


def render_mesh_technical_arr(Vn, F, cpos="iso", zoom=1.3, azimuth=0.0,
                              elevation=0.0, wsize=(1400, 1000), focus=None,
                              clip_origin=None, clip_normal=None, crop=True):
    """Opaque edge-enhanced global/ROI CAD view."""
    import numpy as np
    import pyvista as pv
    import style as S

    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    surface = _clip(pv.PolyData(np.asarray(Vn, float), faces), clip_origin, clip_normal)
    _pv, plotter = _new_plotter(wsize)
    _add_part(plotter, surface, S.PART_RGB, opacity=1.0)
    _finish_camera(plotter, cpos, zoom, azimuth, elevation, focus=focus)
    image = plotter.screenshot(return_img=True)
    plotter.close()
    return crop_render(image) if crop else np.asarray(image)[..., :3]


def render_voxel_arr(occ, points, labels, cpos="iso", zoom=1.3, psize=22, opacity=0.94,
                     azimuth=0.0, elevation=0.0, wsize=(900, 840)):
    """Render a procedural part with opaque material and visible contact markers."""
    import numpy as np
    import style as S
    pv = S.pv_theme()
    surf = voxel_surface(occ)
    p = pv.Plotter(off_screen=True, window_size=wsize)
    _add_part(p, surf, S.PART_RGB, opacity, smooth=False)
    pts = np.asarray(points, float)
    lab = np.asarray(labels, bool)
    if (~lab).any():
        p.add_points(pts[~lab], color=S.ACC_RGB, render_points_as_spheres=True, point_size=psize)
    if lab.any():
        p.add_points(pts[lab], color=S.INACC_RGB, render_points_as_spheres=True, point_size=psize)
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


def render_mesh_arr(Vn, F, points_vox, colors_rgb, lo, pitch, cpos="iso", zoom=1.3, psize=15,
                    opacity=0.94, azimuth=0.0, elevation=0.0, wsize=(900, 840),
                    clip_origin=None, clip_normal=None):
    """Render a real mesh and contact-level colour field; clipping is explicit."""
    import numpy as np
    import pyvista as pv
    import style as S
    S.pv_theme()
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    surf = _clip(pv.PolyData(np.asarray(Vn, float), faces), clip_origin, clip_normal)
    pw = np.asarray(lo, float) + (np.asarray(points_vox, float) + 0.5) * float(pitch)   # 体素→世界（world_to_voxel 逆）
    p = pv.Plotter(off_screen=True, window_size=wsize)
    _add_part(p, surf, S.PART_RGB, opacity)
    cloud = pv.PolyData(pw)
    cloud["rgb"] = (np.asarray(colors_rgb, float) * 255).astype(np.uint8)
    p.add_points(cloud, scalars="rgb", rgb=True, render_points_as_spheres=True, point_size=psize)
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


def render_mesh_plain(Vn, F, lo, pitch, cpos="iso", zoom=1.3, opacity=0.98, azimuth=0.0, elevation=0.0,
                      wsize=(900, 840), clip_origin=None, clip_normal=None):
    """Compatibility wrapper for the edge-enhanced technical CAD renderer."""
    return render_mesh_technical_arr(Vn, F, cpos=cpos, zoom=zoom, azimuth=azimuth,
                                     elevation=elevation, wsize=wsize,
                                     clip_origin=clip_origin, clip_normal=clip_normal)


def render_mesh_faces_arr(Vn, F, hi_idx, d=None, cpos="iso", zoom=1.3, hi_rgb=(0.867, 0.518, 0.322),
                          base_opacity=0.94, azimuth=0.0, elevation=0.0, wsize=(900, 840),
                          clip_origin=None, clip_normal=None):
    """渲染网格并**面积保真**高亮指定面（hi_idx）→ RGB 数组，供图2「支撑接触区 S(P,d)」。
    做法：整网格半透明灰 + 高亮子面不透明橙（大平面下朝面如实显整片，且透过半透明本体可见，解决遮挡）。
    d 给定则在零件上方沿 +d 画构建方向黑箭头（同相机）。hi_rgb 默认橙（避开红/蓝语义）。"""
    import numpy as np

    colors = np.tile(np.asarray(hi_rgb, float), (len(hi_idx), 1))
    return render_face_field_arr(Vn, F, hi_idx, colors, cpos=cpos, zoom=zoom,
                                 azimuth=azimuth, elevation=elevation, wsize=wsize,
                                 clip_origin=clip_origin, clip_normal=clip_normal)


def render_contact_region_arr(Vn, F, pts_world, d=None, cpos="iso", zoom=1.3, hi_rgb=(0.867, 0.518, 0.322),
                              opacity=0.94, psize=12, azimuth=0.0, elevation=0.0, wsize=(900, 840),
                              clip_origin=None, clip_normal=None):
    """半透明网格 + 支撑接触区点球（世界坐标，橙）+ 可选构建方向箭头 → RGB 数组。图2 用。
    点用球渲染故下朝面朝背相机也可见（半透明网格让底面点透出），解决面高亮被遮挡问题。"""
    import numpy as np
    import pyvista as pv
    import style as S
    S.pv_theme()
    V = np.asarray(Vn, float)
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    surf = _clip(pv.PolyData(V, faces), clip_origin, clip_normal)
    p = pv.Plotter(off_screen=True, window_size=wsize)
    p.add_mesh(surf, color=S.PART_RGB, opacity=opacity, smooth_shading=True, show_edges=False,
               ambient=0.35, diffuse=0.65, specular=0.1)
    pw = np.asarray(pts_world, float)
    if len(pw):
        p.add_points(pv.PolyData(pw), color=hi_rgb, render_points_as_spheres=True, point_size=psize)
    if d is not None:
        d = np.asarray(d, float); d = d / np.linalg.norm(d)
        c = V.mean(0); diag = float(np.linalg.norm(V.max(0) - V.min(0)))
        tail = c + d * 0.62 * diag
        p.add_mesh(pv.Arrow(start=tail, direction=d, scale=0.42 * diag, tip_length=0.32,
                            tip_radius=0.09, shaft_radius=0.035), color="black")
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


def render_fp_fn_arr(Vn, F, points_vox, fp, fn, lo, pitch, cpos="iso", zoom=1.4, opacity=0.94,
                     azimuth=0.0, elevation=0.0, wsize=(900, 840), show_correct=False,
                     clip_origin=None, clip_normal=None, psize=20):
    """半透明网格 + 逐点误判着色（图10b）：正确=浅灰小点、假正 FP=橙、假负 FN=红（漏报最糟，最大最亮）。"""
    import numpy as np
    import pyvista as pv
    import style as S
    S.pv_theme()
    V = np.asarray(Vn, float)
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    p = pv.Plotter(off_screen=True, window_size=wsize)
    surf = _clip(pv.PolyData(V, faces), clip_origin, clip_normal)
    p.add_mesh(surf, color=S.PART_RGB, opacity=opacity, smooth_shading=True,
               show_edges=False, ambient=0.35, diffuse=0.65)
    pw = np.asarray(lo, float) + (np.asarray(points_vox, float) + 0.5) * float(pitch)
    fp = np.asarray(fp, bool); fn = np.asarray(fn, bool); ok = ~(fp | fn)
    if show_correct and ok.any():
        p.add_points(pw[ok], color=(0.62, 0.64, 0.67), render_points_as_spheres=True, point_size=7)
    if fp.any():
        p.add_points(pw[fp], color=S.ORANGE, render_points_as_spheres=True, point_size=max(12, psize - 3))
    if fn.any():
        p.add_points(pw[fn], color=S.FN, render_points_as_spheres=True, point_size=psize)
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


def render_dir_arrow_arr(Vn, F, p_world, direction, cpos="iso", zoom=1.5, opacity=0.94,
                         arrow_rgb=(0.173, 0.435, 0.698), azimuth=0.0, elevation=0.0, wsize=(900, 840),
                         clip_origin=None, clip_normal=None):
    """半透明网格 + 接触点 p（黑球）+ 沿 direction 的推荐逼近方向箭头（图9b Top-1）。箭头尾在 p 外侧、指向 p。"""
    import numpy as np
    import pyvista as pv
    import style as S
    V = np.asarray(Vn, float)
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    _pv, p = _new_plotter(wsize)
    surf = _clip(pv.PolyData(V, faces), clip_origin, clip_normal)
    _add_part(p, surf, S.PART_RGB, opacity=1.0)
    pw = np.asarray(p_world, float)
    d = np.asarray(direction, float); d = d / np.linalg.norm(d)
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    tail = pw - d * 0.5 * diag                                   # 尾在 p 外侧，箭头指向 p（逼近）
    halo = pv.Arrow(start=tail, direction=d, scale=0.5 * diag, tip_length=0.28,
                    tip_radius=0.092, shaft_radius=0.044)
    arrow = pv.Arrow(start=tail, direction=d, scale=0.5 * diag, tip_length=0.28,
                     tip_radius=0.072, shaft_radius=0.030)
    p.add_mesh(halo, color="white", lighting=False)
    p.add_mesh(arrow, color=arrow_rgb, lighting=False)
    p.add_points(pw.reshape(1, 3), color="white", render_points_as_spheres=True, point_size=44)
    p.add_points(pw.reshape(1, 3), color="#1F2930", render_points_as_spheres=True, point_size=24)
    _finish_camera(p, cpos, zoom, azimuth, elevation, focus=pw)
    arr = p.screenshot(return_img=True)
    p.close()
    return crop_render(arr)


def load_fusion_mesh(name, root):
    """Fusion 设计名 → (Vn, F, occ, lo, pitch)；占据与 npz 一致性由调用方按需校验。res=48（D-021）。"""
    import numpy as np  # noqa: F401
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility.data import mesh as MESH
    path = dict(iter_final_designs(root)).get(name)
    if path is None:
        return None
    V, F = load_obj(path)
    Vn, _s = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=48)
    return Vn, F, occ, lo, pitch


def load_thingi_mesh(name, root, include_normals=False):
    """Thingi 设计名 → (Vn, F, occ, lo, pitch)；镜像 build_thingi 的归一/占据口径（res=48），故与 thingi_v1 点帧一致。"""
    import numpy as np  # noqa: F401
    from support_accessibility.data.thingi import iter_thingi_meshes, load_mesh
    from support_accessibility.data.fusion360 import normalize
    from support_accessibility.data import mesh as MESH
    path = dict(iter_thingi_meshes(root)).get(name)
    if path is None:
        return None
    V, F, normals = load_mesh(path)
    Vn, _s = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=48)
    result = (Vn, F, occ, lo, pitch)
    return result + (normals,) if include_normals else result


def per_model_area_inacc(ms):
    """每件（下朝面计数, 不可达占比）——图6(c) 散点数据。"""
    import numpy as np
    area, inacc = [], []
    for m in ms:
        lab = np.asarray(m.labels, bool)
        if lab.size == 0:
            continue
        area.append(int(lab.size))
        inacc.append(float(lab.mean()))
    return np.array(area), np.array(inacc)
