#!/usr/bin/env python3
"""图 9 方向级可达性场（写作指引 §5.5 / 图9）。

(a) 选一典型接触点，下半球逼近方向以极坐标圆盘投影（方位角=角向、极角=径向，圆心=竖直↓、边缘=水平）：
    左=判定器（可达蓝/被挡红），右=网络预测（被挡概率蓝→红热图）——两盘高度一致。
(b) 零件 3D 渲染 + 该点网络 Top-1 推荐逼近方向箭头。
模型 = runs/figures/ckpt_dir.pt（方向级，留出 seed=0）；展示标签在原网格匹配时走 D-020 精确细化，否则明示占据回落。
用法：conda run -n saf python tools/figures/fig09_direction_field.py [--root ...] [--name ..] [--idx ..]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import cm, colors as mcolors  # noqa: E402
from matplotlib.patches import Circle, Patch  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CMAP = mcolors.LinearSegmentedColormap.from_list("acc", [S.ACC, "#EDEDED", S.INACC])


def _disk_xy(dirs):
    """下半球方向 (D,3) → 圆盘 (x,y)：方位角=atan2(vy,vx)，径向=极角/90°（圆心=−Z 竖直）。"""
    az = np.arctan2(dirs[:, 1], dirs[:, 0])
    rad = np.arccos(np.clip(-dirs[:, 2], 0, 1)) / (np.pi / 2)
    return rad * np.cos(az), rad * np.sin(az)


def _disk_axes(ax, title):
    ax.add_patch(Circle((0, 0), 1.0, fc="none", ec="#999", lw=1.2))
    for rr in (1 / 3, 2 / 3):
        ax.add_patch(Circle((0, 0), rr, fc="none", ec="#DDD", lw=0.8))
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.28, 1.2); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0, -1.22, "水平 →", ha="center", va="top", fontsize=8, color="#777")
    ax.scatter([0], [0], marker="+", s=60, color="#777", zorder=3)
    ax.text(0.03, 0.08, "竖直↓", fontsize=7.5, color="#777")
    ax.set_title(title, fontsize=9.8)


def main():
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    ap.add_argument("--name", default=None)
    ap.add_argument("--idx", type=int, default=None)
    a = ap.parse_args()

    ck = torch.load(os.path.join(_ROOT, "runs", "figures", "ckpt_dir.pt"), map_location="cpu", weights_only=False)
    Dd = int(ck["D"]); dirs = np.asarray(ck["dirs"], float); ndir = int(ck["n_directions"])
    net = ConvONetLite(out_dim=Dd); net.load_state_dict(ck["state_dict"]); net.eval()
    name = a.name or ck["showcase_cand"][0][0]
    idx = a.idx if a.idx is not None else ck["showcase_cand"][0][1]

    ms, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "fusion360_full"))
    m = {mm.name: mm for mm in ms}[name]
    p = np.asarray(m.points[idx], float)

    mesh = D.load_fusion_mesh(name, a.root)
    if mesh is not None:
        Vn, F, occ, lo, pitch = mesh
        refined = occ.shape == m.occ.shape and bool((occ == np.asarray(m.occ, bool)).all())
        o = SupportAccessibilityOracle(m.occ, {"n_directions": ndir}, mesh=(Vn, F, lo, pitch)) if refined else SupportAccessibilityOracle(m.occ, {"n_directions": ndir})
    else:
        refined = False
        o = SupportAccessibilityOracle(m.occ, {"n_directions": ndir})
    viable = o.direction_labels(p, m.radius)                              # (D,) True=可达
    with torch.no_grad():
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape)
        gc = to_grid_coords(p.reshape(1, 3), m.occ.shape)
        blocked_prob = torch.sigmoid(net(occ, gc)).numpy().reshape(-1)     # (D,) 被挡概率
    acc = float(((blocked_prob >= 0.5) == (~viable)).mean())               # 方向级一致率
    x, y = _disk_xy(dirs)
    rec = dirs[int(np.argmin(blocked_prob))]                               # Top-1 最可达方向（网络）

    fig = plt.figure(figsize=(10.6, 3.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.25], wspace=0.1, left=0.02, right=0.9, top=0.9, bottom=0.1)

    ax0 = fig.add_subplot(gs[0]); _disk_axes(ax0, f"(a) {'D-020 细化' if refined else '占据'}判定器")
    ax0.scatter(x[viable], y[viable], s=34, color=S.ACC, zorder=4, edgecolors="white", linewidths=0.3)
    ax0.scatter(x[~viable], y[~viable], s=34, color=S.INACC, zorder=4, edgecolors="white", linewidths=0.3)

    ax1 = fig.add_subplot(gs[1]); _disk_axes(ax1, f"网络预测（方向级一致 {100 * acc:.0f}%）")
    ax1.scatter(x, y, c=blocked_prob, cmap=_CMAP, vmin=0, vmax=1, s=34, zorder=4,
                edgecolors="white", linewidths=0.3)

    ax2 = fig.add_subplot(gs[2])
    Vn, F, _oo, lo, pitch = D.load_fusion_mesh(name, a.root)
    p_world = np.asarray(lo, float) + (p + 0.5) * float(pitch)
    img = D.render_dir_arrow_arr(Vn, F, p_world, rec, zoom=1.5)
    ax2.imshow(img); ax2.axis("off")
    ax2.set_title(f"(b) Top-1 推荐逼近方向\n{'D-020 细化标签' if refined else '占据标签（无网格）'}", fontsize=9.8)

    sm = cm.ScalarMappable(cmap=_CMAP, norm=mcolors.Normalize(0, 1)); sm.set_array([])
    cax = fig.add_axes([0.905, 0.28, 0.015, 0.42])
    cb = fig.colorbar(sm, cax=cax); cb.set_label("被挡概率", fontsize=8.5)
    cb.set_ticks([0, 0.5, 1]); cb.set_ticklabels(["0 可达", "0.5", "1 被挡"]); cb.ax.tick_params(labelsize=7.5)
    fig.legend(handles=[Patch(color=S.ACC, label="可达方向"), Patch(color=S.INACC, label="被挡方向")],
               loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=2, frameon=False, fontsize=8.5)

    print("SAVED", S.save(fig, "fig09_direction_field"))


if __name__ == "__main__":
    main()
