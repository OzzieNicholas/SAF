"""论文图件统一样式：出版尺寸、字体嵌入、科学配色与离屏 CAD 渲染。

配色红线（写作指引 §1.2 决定点）：**不可达 = 红、可达 = 蓝、不确定 = 灰**（红绿色盲友好）。
输出到 paper/figures/：每图存 PNG(600 dpi) + 字体嵌入 PDF。中文优先微软雅黑。
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # torch(libiomp5)+vtk(libomp) 同进程共存（图7/9 用）

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# —— 中文字体：微软雅黑的小字号印刷效果优于黑体，缺失时再回落 ——
_FONTNAME = "sans-serif"
for _p in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
        _FONTNAME = fm.FontProperties(fname=_p).get_name()
        break

plt.rcParams.update({
    "font.family": _FONTNAME,
    "axes.unicode_minus": False,
    "figure.dpi": 180, "savefig.dpi": 600,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.75, "lines.linewidth": 1.4,
    "axes.titleweight": "bold",
    "axes.facecolor": "#FCFCFB", "figure.facecolor": "white",
    "grid.color": "#D9D9D6", "grid.linewidth": 0.55, "grid.alpha": 0.55,
})

# —— 配色（语义固定）——
INACC = "#C0392B"    # 不可达 = 红
ACC = "#2C6FB2"      # 可达 = 蓝
UNC = "#8A8A8A"      # 不确定 / 边界 = 灰
NEUTRAL = "#6E6E6E"
GREEN = "#4E9A63"
ORANGE = "#DD8452"
FN = "#7A3E9D"       # 漏报不可达：与“真实不可达”红分离，避免一色多义
INK = "#20252B"
PAPER = "#FCFCFB"

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(_ROOT, "paper", "figures")
os.makedirs(OUTDIR, exist_ok=True)


def save(fig, name):
    """保存出版级 PNG 与字体嵌入 PDF；写入稳定元数据。"""
    png = os.path.join(OUTDIR, name + ".png")
    metadata = {"Creator": "SAF reproducible figure pipeline", "Title": name}
    fig.savefig(png, bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.join(OUTDIR, name + ".pdf"), bbox_inches="tight",
                facecolor="white", metadata=metadata)
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
    pv.global_theme.lighting = True
    return pv


# 离屏渲染对应的 RGB（0–1），pyvista 按点/面着色用
INACC_RGB = (0.753, 0.224, 0.169)
ACC_RGB = (0.173, 0.435, 0.698)
PART_RGB = (0.80, 0.80, 0.82)     # 零件本体（浅灰）
