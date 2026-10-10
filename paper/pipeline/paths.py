"""论文下游包的目录常量。所有论文脚本只从这里取路径，避免各自推算仓库根。"""

from support_accessibility.runtime.data_paths import REPO_ROOT

PAPER_DIR = REPO_ROOT / "paper"
MANUSCRIPT_DIR = PAPER_DIR / "manuscript"
FIGURE_DIR = PAPER_DIR / "figures"
EVIDENCE_DIR = PAPER_DIR / "evidence"
OUTPUT_DIR = PAPER_DIR / "outputs"
BUILD_DIR = PAPER_DIR / "build"

MANUSCRIPT_BODY = MANUSCRIPT_DIR / "论文正文.md"
REFERENCES_BIB = MANUSCRIPT_DIR / "references.bib"
LATEX_TEMPLATE = MANUSCRIPT_DIR / "latex" / "template.tex"
NUMERIC_CLAIMS = MANUSCRIPT_DIR / "numeric_claims.yaml"
EVIDENCE_MANIFEST = EVIDENCE_DIR / "manifest.json"
PAPER_PDF = OUTPUT_DIR / "SAF_中文论文匿名稿.pdf"
