"""可视化 = **命门审计仪器**（D-018；无导师 → 厚可视化 + 趋势证据替代外部评审）。

纯 numpy 光栅化 + `_png` 写盘，不引 matplotlib/Pillow（与 D-009「numpy/stdlib 绕重依赖」同源）。
`accessibility_montage(occ, points, labels, out)`：把占据栅格的两个**侧投影**（XZ / YZ）画成灰色
剪影，支撑接触点按标签上色（红=不可达/风险正类、绿=可达），供人眼审核标签是否落在直觉位置
（深腔顶=红、开阔底面=绿）——这是真实网格标签「人签收」（铁律 #7）赖以进行的图。

numpy 在函数内 import（沿袭包约定：模块级只 stdlib，裸环境仍可 `import viz`）。
"""

import os


def _base_panel(occ, pts, labels, h_axis):
    """一个侧视面板 (H,W,3) uint8：竖直=z（上），水平=h_axis（0=x/1=y），沿第三轴投影剪影。"""
    import numpy as np
    occ = np.asarray(occ, bool)
    nz = occ.shape[2]
    proj_axis = 1 if h_axis == 0 else 0                 # 投影掉的轴（非 h_axis、非 z）
    sil = occ.any(axis=proj_axis).T[::-1]               # (nz, h_dim)，row0 = 顶(z 最大)
    H, W = sil.shape
    img = np.full((H, W, 3), 255, np.uint8)
    img[sil] = (205, 205, 205)                          # 实体剪影 = 灰
    pts = np.asarray(pts, float).reshape(-1, 3)
    if pts.shape[0]:
        labels = np.asarray(labels, bool).reshape(-1)
        cols = np.round(pts[:, h_axis]).astype(int)
        rows = (nz - 1) - np.round(pts[:, 2]).astype(int)
        for r, c, lab in zip(rows, cols, labels):
            if 0 <= r < H and 0 <= c < W:
                img[r, c] = (220, 40, 40) if lab else (40, 160, 40)   # 红=不可达 绿=可达
    return img


def accessibility_montage(occ, points, labels, out_path, scale=4, pad=6, gap=8):
    """占据栅格 + 支撑接触点标签 → 侧视审计 PNG（XZ|YZ 双面板）。返回 out_path。"""
    import numpy as np
    from . import _png
    panels = [np.repeat(np.repeat(_base_panel(occ, points, labels, h), scale, 0), scale, 1)
              for h in (0, 1)]                          # XZ、YZ，各放大 scale 倍
    H = max(p.shape[0] for p in panels)
    canv_w = sum(p.shape[1] for p in panels) + gap
    canvas = np.full((H, canv_w, 3), 255, np.uint8)
    x = 0
    for p in panels:                                    # 顶对齐拼接 + 白缝
        canvas[0:p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + gap
    out = np.full((H + 2 * pad, canv_w + 2 * pad, 3), 255, np.uint8)   # 外白边
    out[pad:pad + H, pad:pad + canv_w] = canvas
    d = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(d, exist_ok=True)
    _png.write_png(out_path, [out[r].tobytes() for r in range(out.shape[0])],
                   out.shape[1], out.shape[0])
    return out_path


def audit_model(model, out_path, **kw):
    """LabeledModel → 审计 PNG（occ 剪影 + 接触点标签）。"""
    return accessibility_montage(model.occ, model.points, model.labels, out_path, **kw)
