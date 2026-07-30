#!/usr/bin/env python3
"""图 7 跨模型预测热图对比（写作指引 §5.4·§4.1 / 图7）：在**未见（留出）件**上三列对照。

列：(1) 零件外观（裸网格）；(2) 判定器标签着色（红=不可达 / 蓝=可达）；(3) 网络预测「不可达概率」热图（蓝→红）。
行：Fusion 留出典型件（含深腔/盲孔/开阔混合）+ Thingi10K 跨域件（真实打印网格，恒 test、从不训练）；
每行注不可达占比与点级准确率。预测与标签高度一致处即说服力；Thingi 行同时是跨数据集泛化的存在性证明。
模型 = runs/figures/ckpt_point.pt（1200 件 / 150 轮，留出 seed=0；Thingi 对该模型天然未见）。
用法：conda run -n saf python tools/figures/fig07_prediction_heatmap.py
      [--root E:/Fusion360Gallery/reconstruction] [--thingi-root E:/Thingi10K/raw_meshes]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import cm  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CMAP = mcolors.LinearSegmentedColormap.from_list("acc", [S.ACC, "#EDEDED", S.INACC])

# 未见件中 curate 的可读双类件（source, name, 展示名, zoom）；source∈{fusion(留出), thingi(跨域恒 test)}
PARTS = [
    ("fusion", "49896_6387ac02_0000", "Fusion A", 1.5),
    ("fusion", "23630_84ec484d_0000", "Fusion B", 1.5),
    ("fusion", "23954_a8c09819_0000", "Fusion C", 1.5),
    ("thingi", "100035", "Thingi D（跨域）", 1.5),
    ("thingi", "101952", "Thingi E（跨域）", 1.5),
]


def _label_rgb(lab):
    rgb = np.tile(np.asarray(S.ACC_RGB, float), (len(lab), 1))
    rgb[np.asarray(lab, bool)] = S.INACC_RGB
    return rgb


def main():
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    ap.add_argument("--thingi-root", default="E:/Thingi10K/raw_meshes")
    a = ap.parse_args()

    ck = torch.load(os.path.join(_ROOT, "runs", "figures", "ckpt_point.pt"), map_location="cpu")
    net = ConvONetLite(); net.load_state_dict(ck["state_dict"]); net.eval()
    fus, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "fusion360_full"))
    thi, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "thingi_v1"))
    byname = {"fusion": {m.name: m for m in fus}, "thingi": {m.name: m for m in thi}}

    n = len(PARTS)
    fig = plt.figure(figsize=(8.2, 2.55 * n))
    gs = fig.add_gridspec(n, 3, wspace=0.02, hspace=0.05, left=0.085, right=0.87, top=0.955, bottom=0.045)
    titles = ["零件外观", "判定器标签", "网络预测（不可达概率热图）"]

    for i, (src, name, disp, zm) in enumerate(PARTS):
        m = byname[src][name]
        lab = np.asarray(m.labels, bool)
        with torch.no_grad():
            occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape)
            gc = to_grid_coords(m.points, m.occ.shape)
            prob = torch.sigmoid(net(occ, gc)).numpy().ravel()
        acc = float(((prob >= 0.5) == lab).mean())
        Vn, F, _o, lo, pitch = (D.load_fusion_mesh(name, a.root) if src == "fusion"
                                else D.load_thingi_mesh(name, a.thingi_root))
        imgs = [
            D.render_mesh_plain(Vn, F, lo, pitch, zoom=zm, opacity=0.98),
            D.render_mesh_arr(Vn, F, m.points, _label_rgb(lab), lo, pitch, zoom=zm, psize=20, opacity=0.5),
            D.render_mesh_arr(Vn, F, m.points, _CMAP(np.clip(prob, 0, 1))[:, :3], lo, pitch, zoom=zm, psize=20, opacity=0.5),
        ]
        ax0 = None
        for j, img in enumerate(imgs):
            ax = fig.add_subplot(gs[i, j]); ax.imshow(img); ax.axis("off")
            if i == 0:
                ax.set_title(titles[j], fontsize=10)
            if j == 0:
                ax0 = ax
        ax0.text(-0.05, 0.5, f"{disp}\n不可达 {100 * lab.mean():.0f}%\n准确率 {100 * acc:.0f}%",
                 transform=ax0.transAxes, rotation=90, va="center", ha="center", fontsize=8.5)

    sm = cm.ScalarMappable(cmap=_CMAP, norm=mcolors.Normalize(0, 1)); sm.set_array([])
    cax = fig.add_axes([0.885, 0.34, 0.016, 0.34])
    cb = fig.colorbar(sm, cax=cax); cb.set_label("不可达概率", fontsize=9)
    cb.set_ticks([0, 0.5, 1]); cb.set_ticklabels(["0 可达", "0.5", "1 不可达"]); cb.ax.tick_params(labelsize=8)
    fig.legend(handles=[Patch(color=S.INACC, label="不可达"), Patch(color=S.ACC, label="可达")],
               loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=9)

    print("SAVED", S.save(fig, "fig07_prediction_heatmap"))


if __name__ == "__main__":
    main()
