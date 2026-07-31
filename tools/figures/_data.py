"""图件数据 / 渲染助手（tools/figures/*）。

- voxel_surface(occ)：占据栅格 → pyvista blocky 表面（程序化件用）。
- render_voxel_arr(...)：离屏渲染"零件本体 + 下朝接触点（红=不可达/蓝=可达）"→ RGB 数组（供 matplotlib 组图）。
- load_fusion_mesh(name, root)：Fusion .obj → (Vn,F,occ,lo,pitch)，占据与 npz 逐比特校验（同 eval_e5 --root）。
- per_model_area_inacc(ms)：每件（下朝面计数, 不可达占比），供图6(c) 散点。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # style


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


def _finish_camera(plotter, cpos, zoom, azimuth=0.0, elevation=0.0):
    """统一论文 CAD 相机：正交投影消除跨面板透视差，并应用固定视角变换。"""
    plotter.camera_position = cpos
    if azimuth:
        plotter.camera.azimuth += azimuth
    if elevation:
        plotter.camera.elevation += elevation
    plotter.enable_parallel_projection()
    plotter.camera.zoom(zoom)


def _add_part(plotter, surface, color, opacity=0.94, smooth=True):
    """Neutral opaque CAD material; data marks are never revealed by transparency."""
    plotter.add_mesh(surface, color=color, smooth_shading=smooth, show_edges=False,
                     opacity=opacity, ambient=0.32, diffuse=0.62, specular=0.10,
                     specular_power=16)


def _clip(surface, clip_origin=None, clip_normal=None):
    """Apply an explicit section plane only when a figure declares one."""
    if clip_origin is None or clip_normal is None:
        return surface
    return surface.clip(normal=clip_normal, origin=clip_origin, invert=False)


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
    """只渲染零件网格（无接触点，近不透明）→ RGB 数组，供图7「零件外观」列。lo/pitch 仅为对齐相机与含点列一致。"""
    import numpy as np  # noqa: F401
    import pyvista as pv
    import style as S
    S.pv_theme()
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    surf = _clip(pv.PolyData(np.asarray(Vn, float), faces), clip_origin, clip_normal)
    p = pv.Plotter(off_screen=True, window_size=wsize)
    _add_part(p, surf, S.PART_RGB, opacity)
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


def render_mesh_faces_arr(Vn, F, hi_idx, d=None, cpos="iso", zoom=1.3, hi_rgb=(0.867, 0.518, 0.322),
                          base_opacity=0.94, azimuth=0.0, elevation=0.0, wsize=(900, 840),
                          clip_origin=None, clip_normal=None):
    """渲染网格并**面积保真**高亮指定面（hi_idx）→ RGB 数组，供图2「支撑接触区 S(P,d)」。
    做法：整网格半透明灰 + 高亮子面不透明橙（大平面下朝面如实显整片，且透过半透明本体可见，解决遮挡）。
    d 给定则在零件上方沿 +d 画构建方向黑箭头（同相机）。hi_rgb 默认橙（避开红/蓝语义）。"""
    import numpy as np
    import pyvista as pv
    import style as S
    S.pv_theme()
    V = np.asarray(Vn, float)
    Fa = np.asarray(F, np.int64)
    faces = np.hstack([np.full((len(Fa), 1), 3), Fa]).astype(np.int64).ravel()
    p = pv.Plotter(off_screen=True, window_size=wsize)
    # Do not draw highlight faces twice: coplanar grey/orange triangles cause
    # depth-buffer fighting and make the support region disappear in print.
    keep = np.ones(len(Fa), dtype=bool)
    keep[np.asarray(hi_idx, int)] = False
    base_faces = np.hstack([np.full((int(keep.sum()), 1), 3), Fa[keep]]).astype(np.int64).ravel()
    base = _clip(pv.PolyData(V, base_faces), clip_origin, clip_normal)
    p.add_mesh(base, color=S.PART_RGB, opacity=base_opacity, smooth_shading=True,
               show_edges=False, ambient=0.35, diffuse=0.65, specular=0.08)
    if len(hi_idx):
        hf = Fa[np.asarray(hi_idx, int)]
        faces_hi = np.hstack([np.full((len(hf), 1), 3), hf]).astype(np.int64).ravel()
        high = _clip(pv.PolyData(V, faces_hi), clip_origin, clip_normal)
        p.add_mesh(high, color=hi_rgb, opacity=1.0, smooth_shading=False,
                   show_edges=False, ambient=0.45, diffuse=0.6, specular=0.1)
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
    S.pv_theme()
    V = np.asarray(Vn, float)
    faces = np.hstack([np.full((len(F), 1), 3), np.asarray(F)]).astype(np.int64).ravel()
    p = pv.Plotter(off_screen=True, window_size=wsize)
    surf = _clip(pv.PolyData(V, faces), clip_origin, clip_normal)
    p.add_mesh(surf, color=S.PART_RGB, opacity=opacity, smooth_shading=True,
               show_edges=False, ambient=0.35, diffuse=0.65)
    pw = np.asarray(p_world, float)
    d = np.asarray(direction, float); d = d / np.linalg.norm(d)
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    tail = pw - d * 0.5 * diag                                   # 尾在 p 外侧，箭头指向 p（逼近）
    p.add_mesh(pv.Arrow(start=tail, direction=d, scale=0.5 * diag, tip_length=0.28,
                        tip_radius=0.07, shaft_radius=0.028), color=arrow_rgb)
    p.add_points(pw.reshape(1, 3), color="black", render_points_as_spheres=True, point_size=20)
    _finish_camera(p, cpos, zoom, azimuth, elevation)
    arr = p.screenshot(return_img=True)
    p.close()
    return arr


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


def load_thingi_mesh(name, root):
    """Thingi 设计名 → (Vn, F, occ, lo, pitch)；镜像 build_thingi 的归一/占据口径（res=48），故与 thingi_v1 点帧一致。"""
    import numpy as np  # noqa: F401
    from support_accessibility.data.thingi import iter_thingi_meshes, load_mesh
    from support_accessibility.data.fusion360 import normalize
    from support_accessibility.data import mesh as MESH
    path = dict(iter_thingi_meshes(root)).get(name)
    if path is None:
        return None
    V, F, _N = load_mesh(path)
    Vn, _s = normalize(V)
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=48)
    return Vn, F, occ, lo, pitch


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
