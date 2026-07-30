"""论文图件统一样式（tools/figures/*）——中文字体 + 配色 + 300dpi + 保存助手 + pyvista 离屏主题。

配色红线（写作指引 §1.2 决定点）：**不可达 = 红、可达 = 蓝、不确定 = 灰**（红绿色盲友好）。
输出到 paper/figures/：每图存 PNG(300dpi 位图) + PDF(矢量)。中文用 SimHei（Windows）。
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # torch(libiomp5)+vtk(libomp) 同进程共存（图7/9 用）

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# —— 中文字体（Windows SimHei 优先，回落 msyh）——
_FONTNAME = "sans-serif"
for _p in ("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc"):
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
        _FONTNAME = fm.FontProperties(fname=_p).get_name()
        break

plt.rcParams.update({
    "font.family": _FONTNAME,
    "axes.unicode_minus": False,
    "figure.dpi": 300, "savefig.dpi": 300,
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "lines.linewidth": 1.6,
})

# —— 配色（语义固定）——
INACC = "#C0392B"    # 不可达 = 红
ACC = "#2C6FB2"      # 可达 = 蓝
UNC = "#8A8A8A"      # 不确定 / 边界 = 灰
NEUTRAL = "#6E6E6E"
GREEN = "#4E9A63"
ORANGE = "#DD8452"

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(_ROOT, "paper", "figures")
os.makedirs(OUTDIR, exist_ok=True)


def save(fig, name):
    """保存 PNG(300dpi) + PDF(矢量) 到 paper/figures/；返回 PNG 路径。"""
    png = os.path.join(OUTDIR, name + ".png")
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(os.path.join(OUTDIR, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return png


def pv_theme():
    """pyvista 论文主题：离屏、白底、SSAA 抗锯齿、黑字。返回 pyvista 模块。"""
    import pyvista as pv
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.anti_aliasing = "ssaa"
    pv.global_theme.font.color = "black"
    pv.global_theme.font.family = "arial"
    return pv


# 离屏渲染对应的 RGB（0–1），pyvista 按点/面着色用
INACC_RGB = (0.753, 0.224, 0.169)
ACC_RGB = (0.173, 0.435, 0.698)
PART_RGB = (0.80, 0.80, 0.82)     # 零件本体（浅灰）
