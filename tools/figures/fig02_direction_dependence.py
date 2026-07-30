#!/usr/bin/env python3
"""图 2 支撑接触区定义与方向依赖（写作指引 §3.1 / 图2）：同一 Fusion 件、两个构建方向 d 下的 S(P,d)。

双联：(a) d₁、(b) d₂——高亮支撑接触区（下朝悬垂面，橙），黑箭头标构建方向 d，标注面数与 θc=45°。
结论：支撑接触区随构建方向变化。判据用 src/.../data/overhang.support_contact_faces（n·d̂<-cos45°）。
用法：conda run -n saf python tools/figures/fig02_direction_dependence.py [--root ...] [--name ...]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: E402
import _data as D  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HI_RGB = (0.867, 0.518, 0.322)   # 橙 = 支撑接触区高亮


def main():
    from support_accessibility.data.overhang import support_contact_faces
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="E:/Fusion360Gallery/reconstruction")
    ap.add_argument("--name", default="23954_a8c09819_0000")
    ap.add_argument("--zoom", type=float, default=1.4)
    a = ap.parse_args()

    Vn, F, _o, _lo, _p = D.load_fusion_mesh(a.name, a.root)
    dirs = [(np.array([0.0, 0.0, 1.0]), "$d_1$ = +Z（竖直构建）"),
            (np.array([0.0, 1.0, 0.0]), "$d_2$ = +Y（侧卧构建）")]

    fig = plt.figure(figsize=(7.4, 4.1))
    gs = fig.add_gridspec(1, 2, wspace=0.03, left=0.02, right=0.98, top=0.9, bottom=0.12)
    for j, (d, lab) in enumerate(dirs):
        sc = support_contact_faces(Vn, F, d)
        img = D.render_mesh_faces_arr(Vn, F, sc.indices, d=d, zoom=a.zoom, hi_rgb=HI_RGB)
        ax = fig.add_subplot(gs[j]); ax.imshow(img); ax.axis("off")
        ax.set_title(f"({'ab'[j]}) {lab}\n支撑接触面 {len(sc.indices)} · θ$_c$=45°", fontsize=10)

    fig.legend(handles=[Patch(color=HI_RGB, label="支撑接触区 S(P,d)（下朝悬垂面）")],
               loc="lower center", bbox_to_anchor=(0.5, 0.0), frameon=False, fontsize=9.5)
    print("SAVED", S.save(fig, "fig02_direction_dependence"))


if __name__ == "__main__":
    main()
