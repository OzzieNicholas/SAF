"""中文期刊图件样式：中文宋体、数字与字母 Times New Roman、变量斜体，图中文字 6 号（7.5 pt）。

依据《计算机辅助设计与图形学学报》征稿简则（图中文字及图序写清楚、变量斜体数字正体）与中文期刊通行的
6 号字要求。颜色按语义固定，并保证灰度打印下仍可区分（误差面另加深色轮廓作冗余编码）。
成品输出到 paper/figures/，布局诊断写入 artifacts/runs/figure_qa/。
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paper.pipeline.paths import REPO_ROOT

MM = 1 / 25.4
DOUBLE_MM = 175.0
SINGLE_MM = 85.0
FONT_PT = 7.5          # 6 号字

RC = {
    # 拉丁字符 Times，汉字回落宋体，数学斜体字母回落 STIX。图中不用 mathtext：它不支持字体回退，
    # 与汉字混排会缺字；变量用 var() 生成的 Unicode 数学斜体字符。
    "font.family": ["Times New Roman", "SimSun", "STIXGeneral"],
    "axes.unicode_minus": False,
    "font.size": FONT_PT,
    "axes.titlesize": FONT_PT,
    "axes.labelsize": FONT_PT,
    "xtick.labelsize": FONT_PT,
    "ytick.labelsize": FONT_PT,
    "legend.fontsize": FONT_PT,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.0,
    "lines.markersize": 4.0,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 600,
    "figure.dpi": 150,
}
plt.rcParams.update(RC)

# 语义色（灰度亮度递减：可达 > 误报 > 不可达 > 漏报）
ACCESSIBLE = "#B7D3EC"        # 判对的可达接触面
INACCESSIBLE = "#C0392B"      # 判对的不可达接触面
FALSE_ALARM = "#F2B035"       # 误报：实可达、判不可达
MISSED = "#3D1E5C"            # 漏报：实不可达、判可达
ERROR_EDGE = "#111111"
PART = (0.80, 0.81, 0.82)     # 零件本体
INK = "#1A1A1A"
GREY = "#7A7F84"
NETWORK = "#C0392B"
GEOMETRY = "#2C5F8A"

_ITALIC = {c: chr(0x1D434 + i) for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
_ITALIC.update({c: chr(0x1D44E + i) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
_ITALIC["h"] = "ℎ"                       # 数学斜体 h 位于字母类符号区
_ITALIC.update({"ε": "\U0001D700", "θ": "\U0001D703", "ρ": "\U0001D70C", "φ": "\U0001D711"})
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def var(name, sub=""):
    """变量的斜体写法（可带数字下标），如 var("F", "1") → 𝐹₁。"""
    return "".join(_ITALIC.get(c, c) for c in name) + sub.translate(_SUB)


F1 = var("F", "1")

QA_DIR = os.path.join(str(REPO_ROOT), "artifacts", "runs", "figure_qa")


def figure(width_mm, height_mm):
    plt.rcParams.update(RC)
    return plt.figure(figsize=(width_mm * MM, height_mm * MM))


def save(fig, name):
    """写布局诊断，再输出 600 dpi PNG 与嵌入字体的矢量 PDF 到 paper/figures/，返回 PNG 路径。

    PDF 先写临时文件，核对 %%EOF 后再替换，避免半截文件进入构建。
    """
    from paper.pipeline.paths import FIGURE_DIR
    from paper.pipeline.figure_scripts.figure_qa import inspect_figure
    from support_accessibility.runtime.run_records import write_result

    out_dir = str(FIGURE_DIR)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(QA_DIR, exist_ok=True)
    fig.canvas.draw()
    write_result("figure_qa", inspect_figure(fig, name), os.path.join(QA_DIR, name + ".json"))
    metadata = {"Creator": "SAF reproducible figure pipeline", "Title": name}
    png = os.path.join(out_dir, name + ".png")
    fig.savefig(png, dpi=600, facecolor="white", metadata=metadata)
    pdf = os.path.join(out_dir, name + ".pdf")
    fig.savefig(pdf + ".tmp", format="pdf", facecolor="white",
                metadata={**metadata, "CreationDate": None})   # 不写创建时间：同一输入重建得到逐字节相同的 PDF
    with open(pdf + ".tmp", "rb") as handle:
        data = handle.read()
    if not data.rstrip().endswith(b"%%EOF"):
        raise RuntimeError(f"figure PDF is incomplete after writing: {pdf}")
    os.replace(pdf + ".tmp", pdf)
    plt.close(fig)
    return png
