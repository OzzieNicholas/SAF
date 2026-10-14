"""零件渲染：不透明 CAD 材质 + 被遮挡关键面的「幽灵视图」，供结果类图件共用。

支撑接触区的风险面常在孔、槽、腔内部，外观视角看不到；整件半透明又会让前后表面混淆。这里用三遍
同相机渲染再逐像素合成：
  主图   不透明零件（光照 + 环境光遮蔽），指定面按给定颜色着色；
  可见性 关键面黑、其余白、无光照，得到相机可直接看到的关键面像素；
  关键层 只画关键面（无遮挡），得到全部关键面像素及其颜色。
关键层中不可见的像素即被遮挡的关键面，以半透明色块叠加并描虚线轮廓，形状本身保持不透明。
相机一律正交投影，跨面板没有透视差。
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")      # VTK 与 MKL 各带一份 OpenMP 运行库
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")

import numpy as np

GHOST_ALPHA = 0.62
PART_RGB = (0.80, 0.81, 0.82)


def _plotter(window_size):
    import pyvista as pv
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.anti_aliasing = "ssaa"
    plotter = pv.Plotter(off_screen=True, window_size=window_size)
    try:
        plotter.enable_ssao(radius=0.08, bias=0.004, kernel_size=128, blur=True)
    except (AttributeError, RuntimeError):
        pass
    return pv, plotter


def _poly(pv, V, Fa, rows):
    cells = np.hstack([np.full((len(rows), 1), 3), Fa[rows]]).astype(np.int64).ravel()
    return pv.PolyData(V, cells)


def underside_camera(vertices, direction=(1.15, -0.90, -1.70)):
    """仰视三分之四视角 (position, focal, up)：下朝接触面朝向相机。"""
    vertices = np.asarray(vertices, float)
    centre = vertices.mean(0)
    span = float(np.linalg.norm(vertices.max(0) - vertices.min(0)))
    offset = np.asarray(direction, float)
    offset /= np.linalg.norm(offset)
    return tuple(centre + offset * (2.2 * span)), tuple(centre), (0.0, 0.0, 1.0)


def _shoot(plotter, camera, zoom):
    plotter.camera_position = camera
    plotter.enable_parallel_projection()
    plotter.camera.zoom(zoom)
    image = plotter.screenshot(return_img=True)[..., :3]
    plotter.close()
    return image


def crop_render(image, pad_fraction=0.05):
    """裁掉白边，保留按图像尺寸比例的留白。"""
    rgb = np.asarray(image)[..., :3]
    yy, xx = np.where(np.any(rgb < 248, axis=2))
    if not len(xx):
        return rgb
    pad = max(6, int(round(max(xx.max() - xx.min() + 1, yy.max() - yy.min() + 1) * pad_fraction)))
    return rgb[max(0, yy.min() - pad):min(rgb.shape[0], yy.max() + pad + 1),
               max(0, xx.min() - pad):min(rgb.shape[1], xx.max() + pad + 1)]


def render(Vn, F, faces=(), rgb=None, key_mask=None, error_mask=None, camera=None, zoom=1.0,
           wsize=(1200, 1100), edges=True, crop=True, pad_fraction=0.03):
    """渲染零件，返回 RGB uint8 图像。

    faces     需要着色的面行号；rgb 为对应颜色 (k,3)，0–1。
    key_mask  faces 中的关键面（被遮挡时以幽灵视图透出）；默认全部。
    error_mask faces 中需要加深色实线轮廓的面（误差面）。
    camera    (position, focal, up)；默认仰视三分之四视角。
    """
    from scipy import ndimage

    V = np.asarray(Vn, float)
    Fa = np.asarray(F, np.int64)
    faces = np.asarray(faces, int).reshape(-1)
    rgb = np.zeros((0, 3)) if rgb is None else np.asarray(rgb, float).reshape(-1, 3)
    key_mask = np.ones(len(faces), bool) if key_mask is None else np.asarray(key_mask, bool)
    camera = camera or underside_camera(V)

    def shot(plotter):
        return _shoot(plotter, camera, zoom).astype(float) / 255.0

    body = np.ones(len(Fa), bool)
    body[faces] = False
    pv, main = _plotter(wsize)
    main.add_mesh(_poly(pv, V, Fa, np.flatnonzero(body)), color=PART_RGB, smooth_shading=False,
                  ambient=0.30, diffuse=0.70, specular=0.12, specular_power=20)
    if len(faces):
        coloured = _poly(pv, V, Fa, faces)
        coloured.cell_data["rgb"] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
        main.add_mesh(coloured, scalars="rgb", rgb=True, smooth_shading=False,
                      ambient=0.62, diffuse=0.42, specular=0.04)
    if edges:
        lines = _poly(pv, V, Fa, np.arange(len(Fa))).extract_feature_edges(
            boundary_edges=True, feature_edges=True, manifold_edges=False, non_manifold_edges=False,
            feature_angle=30.0)
        if lines.n_cells:
            main.add_mesh(lines, color="#454B50", line_width=1.2, lighting=False)
    if error_mask is not None and np.any(error_mask):
        outline = _poly(pv, V, Fa, faces[np.asarray(error_mask, bool)]).extract_feature_edges(
            boundary_edges=True, feature_edges=False, manifold_edges=False, non_manifold_edges=True)
        if outline.n_cells:
            main.add_mesh(outline, color="#111111", line_width=2.6, lighting=False)
    image = shot(main)

    if len(faces) and key_mask.any():
        vis = pv.Plotter(off_screen=True, window_size=wsize)
        vis.disable_anti_aliasing()
        vis.add_mesh(_poly(pv, V, Fa, np.r_[np.flatnonzero(body), faces[~key_mask]]), color="white", lighting=False)
        vis.add_mesh(_poly(pv, V, Fa, faces[key_mask]), color="black", lighting=False)
        visible = shot(vis).mean(axis=2) < 0.5
        layer = pv.Plotter(off_screen=True, window_size=wsize)
        layer.disable_anti_aliasing()
        key = _poly(pv, V, Fa, faces[key_mask])
        key.cell_data["rgb"] = np.clip(rgb[key_mask] * 255, 0, 255).astype(np.uint8)
        layer.add_mesh(key, scalars="rgb", rgb=True, lighting=False)
        colour = shot(layer)
        hidden = (colour.min(axis=2) < 0.97) & ~ndimage.binary_dilation(visible, iterations=1)
        hidden = ndimage.binary_opening(hidden, iterations=1)
        if hidden.any():
            image[hidden] = (1 - GHOST_ALPHA) * image[hidden] + GHOST_ALPHA * colour[hidden]
            border = hidden & ~ndimage.binary_erosion(hidden, iterations=2)
            yy, xx = np.nonzero(border)
            dashed = ((xx + yy) // 7) % 2 == 0
            image[yy[dashed], xx[dashed]] = 0.35 * colour[yy[dashed], xx[dashed]]

    out = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    return crop_render(out, pad_fraction=pad_fraction) if crop else out


def render_voxels(occ, lo, pitch, camera, zoom=1.0, wsize=(1200, 1100), pad_fraction=0.03):
    """占据栅格的体素块渲染，体素经 lo + 索引 × pitch 变换到网格的世界坐标，可与网格共用相机。"""
    import warnings
    pv, plotter = _plotter(wsize)
    occ = np.asarray(occ, bool)
    grid = pv.ImageData(dimensions=tuple(np.array(occ.shape) + 1))     # 点数 = 单元数 + 1
    grid.cell_data["occ"] = occ.flatten(order="F").astype(np.uint8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        surf = grid.threshold(0.5, scalars="occ").extract_surface()
    surf.points = np.asarray(lo, float) + np.asarray(surf.points, float) * float(pitch)
    plotter.add_mesh(surf, color=PART_RGB, smooth_shading=False, show_edges=True, edge_color="#8A9096",
                     line_width=0.4, ambient=0.32, diffuse=0.68, specular=0.08)
    return crop_render(_shoot(plotter, camera, zoom), pad_fraction=pad_fraction)
