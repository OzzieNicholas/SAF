"""把论文唯一源稿 ``论文正文.md`` 渲染成 LaTeX（``paper/build/main.tex`` 与 ``body.tex``）。

源稿使用的 Markdown 子集：
  # 题目；``**英文题目：…**``；``## 摘要`` / ``## Abstract`` 与对应的关键词行；
  ``## N 标题`` / ``### N.M 标题``；无编号二级标题（如「数据与可复现性」）；
  段落、``*``/``1.`` 列表、``$行内$`` 与 ``$$…\\tag{n}$$`` 公式、``**粗体**``、``*斜体*``、`` `代码` ``；
  图：``![说明](路径)`` 紧跟 ``*图 N  图题*``；表：``**表 N  表题**`` 后接一个或多个管道表格；
  算法：``**算法 N  标题**`` 后接 ``输入：``/``输出：`` 与有序步骤；引用 ``[3]``、``[3-4]``、``[8,10]``；
  ``## 参考文献`` 及其后内容不渲染（参考文献由 BibTeX 生成，编号按 references.bib 的条目顺序）。
正文里的「图 N」「表 N」「式（N）」「算法 N」自动变成交叉引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

FIGURE_WIDTH = "\\textwidth"
SINGLE_FIGURE_WIDTH = "\\columnwidth"
SINGLE_COLUMN_MAX_MM = 90.0          # 图件物理宽度不超过此值时按单栏图排版（单栏图按 85 mm 绘制）
FIGURE_DIR = Path(__file__).resolve().parents[1] / "figures"
SPECIALS = {"%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_"}
PLACEHOLDER = "\x00{}\x00"


class RenderError(ValueError):
    """源稿不符合渲染器约定。"""


def _is_single_column(png: Path) -> bool:
    """按 PNG 的像素宽度与 pHYs 分辨率换算物理宽度；读不到文件或分辨率时按通栏图处理。"""
    try:
        data = png.read_bytes()
    except OSError:
        return False
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    width_px = int.from_bytes(data[16:20], "big")
    phys = data.find(b"pHYs")
    if phys < 0 or data[phys + 12] != 1:                 # 单位须为米
        return False
    px_per_m = int.from_bytes(data[phys + 4:phys + 8], "big")
    return px_per_m > 0 and width_px / px_per_m * 1000.0 <= SINGLE_COLUMN_MAX_MM


@dataclass
class Document:
    title: str = ""
    title_en: str = ""
    abstract_zh: str = ""
    keywords_zh: str = ""
    abstract_en: str = ""
    keywords_en: str = ""
    body: list[str] = field(default_factory=list)
    figure_labels: dict[int, str] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- 行内
def _escape_plain(text: str) -> str:
    return "".join(SPECIALS.get(ch, ch) for ch in text)


def _expand_citation(spec: str, keys: list[str]) -> str:
    numbers: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if re.fullmatch(r"\d+", part):
            numbers.append(int(part))
        else:
            low, high = re.split(r"[-–]", part)
            numbers.extend(range(int(low), int(high) + 1))
    for number in numbers:
        if not 1 <= number <= len(keys):
            raise RenderError(f"引用编号 {number} 超出 references.bib 的 {len(keys)} 条")
    return "\\cite{" + ",".join(keys[n - 1] for n in numbers) + "}"


def inline(text: str, doc: Document, keys: list[str]) -> str:
    stash: list[str] = []

    def keep(value: str) -> str:
        stash.append(value)
        return PLACEHOLDER.format(len(stash) - 1)

    text = re.sub(r"`([^`]+)`", lambda m: keep("\\texttt{" + _escape_plain(m.group(1)) + "}"), text)
    text = re.sub(r"\$([^$]+)\$", lambda m: keep("$" + m.group(1) + "$"), text)
    text = _escape_plain(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\w*])\*(?!\*)(.+?)(?<!\*)\*(?![\w*])", r"\\emph{\1}", text)
    text = re.sub(r"\[(\d+(?:[-–,]\s*\d+)*)\]", lambda m: _expand_citation(m.group(1), keys), text)
    text = re.sub(r"图\s*(\d+)", lambda m: "图~\\ref{fig:" + doc.figure_labels.get(int(m.group(1)), m.group(1)) + "}", text)
    text = re.sub(r"表\s*(\d+)", lambda m: "表~\\ref{tab:" + m.group(1) + "}", text)
    text = re.sub(r"算法\s*(\d+)", lambda m: "算法~\\ref{alg:" + m.group(1) + "}", text)
    text = re.sub(r"式（(\d+)）", lambda m: "式~\\eqref{eq:" + m.group(1) + "}", text)
    for index, value in enumerate(stash):
        text = text.replace(PLACEHOLDER.format(index), value)
    return text


# ---------------------------------------------------------------- 块
def _figure_label(path: str) -> str:
    """图件标签取文件名（下划线改为连字符），与图件名一致。"""
    return Path(path).stem.replace("_", "-")


def _split_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def _column_widths(rows: list[list[str]]) -> list[float]:
    count = len(rows[0])
    weights = []
    for column in range(count):
        longest = max(len(re.sub(r"\$[^$]*\$|\*\*|\\[a-z]+", "x", row[column])) for row in rows)
        weights.append(min(max(longest, 4), 26) + 3)
    total = sum(weights)
    return [round(0.93 * weight / total, 3) for weight in weights]


def _table(rows_md: list[str], doc: Document, keys: list[str]) -> str:
    rows = [_split_table_row(line) for line in rows_md]
    aligns = [("r" if cell.endswith(":") and not cell.startswith(":") else "l") for cell in rows[1]]
    header, body = rows[0], rows[2:]
    widths = _column_widths([header] + body)
    spec = "".join(
        (">{\\raggedleft\\arraybackslash}" if align == "r" else ">{\\raggedright\\arraybackslash}")
        + f"p{{{width}\\textwidth}}"
        for align, width in zip(aligns, widths)
    )
    lines = [f"  \\begin{{tabular}}{{@{{}}{spec}@{{}}}}", "    \\toprule",
             "    " + " & ".join(inline(cell, doc, keys) for cell in header) + " \\\\", "    \\midrule"]
    for row in body:
        lines.append("    " + " & ".join(inline(cell, doc, keys) for cell in row) + " \\\\")
    lines += ["    \\bottomrule", "  \\end{tabular}"]
    return "\n".join(lines)


def _equation(lines: list[str]) -> str:
    body = "\n".join(lines)
    match = re.search(r"\\tag\{(\d+)\}", body)
    if not match:
        raise RenderError("公式缺少 \\tag{n}")
    body = body.replace(match.group(0), "").strip()
    return ("\\begin{equation}\n\\begin{aligned}\n" + body + "\n\\end{aligned}\n"
            f"\\label{{eq:{match.group(1)}}}\n\\end{{equation}}")


def _algorithm(number: str, title: str, lines: list[str], doc: Document, keys: list[str]) -> str:
    out = ["\\begin{algorithm}[!t]", f"\\caption{{{inline(title, doc, keys)}}}", f"\\label{{alg:{number}}}",
           "\\SetKwInOut{KwIn}{输入}", "\\SetKwInOut{KwOut}{输出}"]
    for line in lines:
        if line.startswith("输入："):
            out.append("\\KwIn{" + inline(line[3:].rstrip("。"), doc, keys) + "}")
        elif line.startswith("输出："):
            out.append("\\KwOut{" + inline(line[3:].rstrip("。"), doc, keys) + "}")
        else:
            out.append(inline(re.sub(r"^\d+\.\s*", "", line).rstrip("。"), doc, keys) + "\\;")
    out.append("\\end{algorithm}")
    return "\n".join(out)


def _paragraph_block(lines: list[str], doc: Document, keys: list[str]) -> str:
    if all(re.match(r"\*\s+", line) for line in lines):
        items = [inline(re.sub(r"^\*\s+", "", line), doc, keys) for line in lines]
        return "\\begin{itemize}\n" + "\n".join(f"  \\item {item}" for item in items) + "\n\\end{itemize}"
    if all(re.match(r"\d+\.\s+", line) for line in lines):
        items = [inline(re.sub(r"^\d+\.\s+", "", line), doc, keys) for line in lines]
        return "\\begin{enumerate}\n" + "\n".join(f"  \\item {item}" for item in items) + "\n\\end{enumerate}"
    return inline(" ".join(line.strip() for line in lines), doc, keys)


def _heading(line: str, doc: Document, keys: list[str]) -> str | None:
    match = re.match(r"(#{2,3})\s+(.*)", line)
    if not match:
        return None
    level, title = match.groups()
    numbered = re.match(r"\d+(?:\.\d+)*\s+(.*)", title)
    text = inline(numbered.group(1) if numbered else title, doc, keys)
    if level == "##":
        return f"\\section{{{text}}}" if numbered else f"\\section*{{{text}}}"
    return f"\\subsection{{{text}}}"


def parse_blocks(md: str) -> list[list[str]]:
    """按空行切块；公式块和围栏内的空行保持完整。"""
    blocks: list[list[str]] = []
    current: list[str] = []
    in_math = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip() == "$$":
            in_math = not in_math
            current.append(line)
            continue
        if not line.strip() and not in_math:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def prescan(blocks: list[list[str]], doc: Document) -> None:
    """先登记图号到标签的映射，使正文里的「图 N」能解析到后面才出现的图。"""
    for position, block in enumerate(blocks[:-1]):
        match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", block[0])
        number = re.match(r"\*图\s*(\d+)", blocks[position + 1][0]) if match else None
        if number:
            doc.figure_labels[int(number.group(1))] = _figure_label(match.group(1))


def render(md: str, keys: list[str]) -> Document:
    doc = Document()
    blocks = parse_blocks(md)
    prescan(blocks, doc)
    section = ""
    index = 0
    while index < len(blocks):
        block = blocks[index]
        head = block[0]
        index += 1
        if head.startswith("# "):
            doc.title = head[2:].strip()
        elif head.startswith("**英文题目："):
            doc.title_en = head.removeprefix("**英文题目：").removesuffix("**").strip()
        elif head.startswith("## 摘要"):
            section = "abstract_zh"
        elif head.startswith("## Abstract"):
            section = "abstract_en"
        elif head.startswith("## 参考文献"):
            doc.references = [line for rest in blocks[index:] for line in rest if re.match(r"\[\d+\]", line)]
            break
        elif head.startswith("**关键词：**"):
            doc.keywords_zh = inline(head.removeprefix("**关键词：**").strip(), doc, keys)
            section = ""
        elif head.startswith("**Key words:**"):
            doc.keywords_en = inline(head.removeprefix("**Key words:**").strip(), doc, keys)
            section = ""
        elif section in ("abstract_zh", "abstract_en") and not head.startswith("#"):
            text = inline(" ".join(block), doc, keys)
            setattr(doc, section, (getattr(doc, section) + "\n" + text).strip())
        elif (heading := _heading(head, doc, keys)) is not None:
            section = ""
            doc.body.append(heading)
        elif head.strip() == "$$":
            doc.body.append(_equation(block[1:-1]))
        elif (figure := re.match(r"!\[[^\]]*\]\(([^)]+)\)", head)) is not None:
            caption = re.match(r"\*图\s*(\d+)\s+(.*)\*$", blocks[index][0]) if index < len(blocks) else None
            if not caption:
                raise RenderError(f"图缺少紧随其后的 *图 N  图题* 行：{head}")
            index += 1
            stem = Path(figure.group(1)).stem
            label = _figure_label(figure.group(1))
            single = _is_single_column(FIGURE_DIR / f"{stem}.png")
            env, width = ("figure", SINGLE_FIGURE_WIDTH) if single else ("figure*", FIGURE_WIDTH)
            doc.body.append(
                f"\\begin{{{env}}}[!t]\n  \\centering\n"
                f"  \\includegraphics[width={width}]{{{stem}}}\n"
                f"  \\caption{{{inline(caption.group(2).strip(), doc, keys)}}}\n  \\label{{fig:{label}}}\n\\end{{{env}}}")
        elif (table := re.match(r"\*\*表\s*(\d+)\s+(.*)\*\*$", head)) is not None:
            parts = [_table(block[1:], doc, keys)] if len(block) > 1 else []
            while index < len(blocks) and blocks[index][0].startswith("|"):
                parts.append(_table(blocks[index], doc, keys))
                index += 1
            if not parts:
                raise RenderError(f"表 {table.group(1)} 后面没有表格")
            doc.body.append(
                "\\begin{table*}[!t]\n  \\centering\n"
                f"  \\caption{{{inline(table.group(2).strip(), doc, keys)}}}\n  \\label{{tab:{table.group(1)}}}\n"
                "  \\zihao{-5}\n  \\setlength{\\tabcolsep}{3pt}\n" + "\n  \\vspace{3pt}\n".join(parts) + "\n\\end{table*}")
        elif (algorithm := re.match(r"\*\*算法\s*(\d+)\s+(.*)\*\*$", head)) is not None:
            steps = list(block[1:])
            while index < len(blocks) and (blocks[index][0].startswith(("输入：", "输出：")) or re.match(r"\d+\.\s", blocks[index][0])):
                steps.extend(blocks[index])
                index += 1
            doc.body.append(_algorithm(algorithm.group(1), algorithm.group(2).strip(), steps, doc, keys))
        elif head.startswith("<!--"):
            continue
        else:
            doc.body.append(_paragraph_block(block, doc, keys))
    return doc


def bibliography_keys(bib_text: str) -> list[str]:
    return re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_text)


def fill_template(template: str, doc: Document) -> str:
    values = {
        "TITLE": doc.title, "TITLE_EN": doc.title_en,
        "ABSTRACT_ZH": doc.abstract_zh, "KEYWORDS_ZH": doc.keywords_zh,
        "ABSTRACT_EN": doc.abstract_en, "KEYWORDS_EN": doc.keywords_en,
    }
    for name, value in values.items():
        if not value:
            raise RenderError(f"源稿缺少 {name}")
        template = template.replace("%%" + name + "%%", value)
    return template


def render_files(manuscript: Path, bib: Path, template: Path, out_dir: Path) -> Document:
    keys = bibliography_keys(bib.read_text(encoding="utf-8"))
    doc = render(manuscript.read_text(encoding="utf-8"), keys)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "body.tex").write_text("\n\n".join(doc.body) + "\n", encoding="utf-8")
    (out_dir / "main.tex").write_text(fill_template(template.read_text(encoding="utf-8"), doc), encoding="utf-8")
    return doc


def main() -> int:
    from paper.pipeline.paths import BUILD_DIR, LATEX_TEMPLATE, MANUSCRIPT_BODY, REFERENCES_BIB

    doc = render_files(MANUSCRIPT_BODY, REFERENCES_BIB, LATEX_TEMPLATE, BUILD_DIR)
    print(f"RENDERED {len(doc.body)} blocks -> {BUILD_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
