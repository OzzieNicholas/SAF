"""Shared publication style and export helpers for the SAF figure set.

The paper figures are composed at their final physical size.  Vector marks and
text stay in PDF; PyVista renderings are embedded as 600 dpi raster evidence.
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
# VTK and the MKL-backed scientific stack load separate OpenMP runtimes on the
# Windows workstation used for off-screen CAD rendering.  Sequential MKL keeps
# the figure process deterministic and prevents native runtime termination.
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


MM_PER_INCH = 25.4
DOUBLE_COLUMN_MM = 175.0
SINGLE_COLUMN_MM = 85.0
MIN_FONT_PT = 7.5

_CJK_FONTS = ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC",
              "WenQuanYi Micro Hei", "PingFang SC")


def _pick_font():
    """按字体族名选取第一个已安装的中文字体，不依赖任何系统字体路径。"""
    installed = {font.name for font in fm.fontManager.ttflist}
    return next((name for name in _CJK_FONTS if name in installed), "sans-serif")


_FONTNAME = _pick_font()

plt.rcParams.update({
    "font.family": _FONTNAME,
    "axes.unicode_minus": False,
    "figure.dpi": 180,
    "savefig.dpi": 600,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.size": 8.0,
    "axes.titlesize": 8.8,
    "axes.labelsize": 8.2,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.7,
    "lines.linewidth": 1.15,
    "axes.titleweight": "normal",
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "grid.color": "#D6D9DB",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.6,
})

# Semantic colours.  These are the only categorical meanings used in result figures.
ACC = "#2C6FB2"          # accessible
INACC = "#C0392B"        # inaccessible / blocked
FN = "#7A3E9D"           # false negative (missed inaccessible point)
ORANGE = "#D7833F"       # support-contact region / false positive
UNC = "#8A8F93"          # neutral / uncertain
NEUTRAL = "#626A70"
INK = "#1F2930"
PAPER = "#FFFFFF"
PART = "#BBC2C7"
PART_DARK = "#7F8990"
PART_EDGE = "#48535B"
PALE_BLUE = "#E8F0F7"
PALE_RED = "#F7E8E5"
PALE_ORANGE = "#FAEEE3"
PALE_GREY = "#F2F4F5"

# Legacy aliases retained while all figure scripts are migrated.
GREEN = "#547F68"
INACC_RGB = (0.753, 0.224, 0.169)
ACC_RGB = (0.173, 0.435, 0.698)
PART_RGB = (0.733, 0.761, 0.780)

from paper.pipeline.paths import FIGURE_DIR, REPO_ROOT
from support_accessibility.runtime.run_records import write_result

OUTDIR = str(FIGURE_DIR)
QA_DIR = os.path.join(str(REPO_ROOT), "artifacts", "runs", "figure_qa")
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(QA_DIR, exist_ok=True)


def mm(value):
    """Convert a physical paper dimension to inches for matplotlib."""
    return value / MM_PER_INCH


def double_column(height_mm):
    """Return a final-size double-column matplotlib figure size in inches."""
    return mm(DOUBLE_COLUMN_MM), mm(height_mm)


def panel_label(ax, text, x=0.0, y=1.01):
    """Place a compact, consistently aligned panel label."""
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8.4, fontweight="bold", color=INK, clip_on=False)


def imshow_cad(ax, image, label=None, semantic=False, semantic_min=None):
    """Place a cropped technical render without allowing text into its data region."""
    artist = ax.imshow(image, interpolation="lanczos")
    ax.set_axis_off()
    ax._saf_cad_artist = artist
    if semantic_min is None:
        semantic_min = .02 if semantic else 0.0
    ax._saf_semantic_min = float(semantic_min)
    if label:
        panel_label(ax, label)
    return artist


def _write_pdf(fig, path, metadata):
    """先写临时文件再原子替换，并核对写出的 PDF 完整：逻辑长度等于字节数，且以 %%EOF 结尾。"""
    temp = path + ".tmp"
    fig.savefig(temp, format="pdf", dpi=600, facecolor="white", metadata=metadata, bbox_inches=None)
    with open(temp, "rb") as handle:
        data = handle.read()
    if os.path.getsize(temp) != len(data) or not data.rstrip().endswith(b"%%EOF"):
        raise RuntimeError(f"figure PDF is incomplete after writing: {path}")
    os.replace(temp, path)


def save(fig, name):
    """Export fixed-size PNG/PDF and write non-destructive layout diagnostics."""
    from paper.pipeline.figure_scripts.figure_qa import inspect_figure

    fig.canvas.draw()
    report = inspect_figure(fig, name)
    write_result("figure_qa", report, os.path.join(QA_DIR, name + ".json"), (OUTDIR,))

    png = os.path.join(OUTDIR, name + ".png")
    pdf = os.path.join(OUTDIR, name + ".pdf")
    metadata = {"Creator": "SAF reproducible figure pipeline", "Title": name}
    fig.savefig(png, dpi=600, facecolor="white", metadata=metadata, bbox_inches=None)
    _write_pdf(fig, pdf, metadata)
    plt.close(fig)
    return png


def pv_theme():
    """Configure an off-screen CAD render with a neutral publication material."""
    import pyvista as pv

    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.anti_aliasing = "ssaa"
    pv.global_theme.font.color = "black"
    pv.global_theme.font.family = "arial"
    pv.global_theme.lighting = True
    return pv
