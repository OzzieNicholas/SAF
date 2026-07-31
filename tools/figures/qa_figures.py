"""Non-mutating figure QA and final-scale contact-sheet generator."""
import argparse
import json
import os
import re
import shutil
import subprocess

import numpy as np


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIGURE_DIR = os.path.join(ROOT, "paper", "figures")
QA_DIR = os.path.join(ROOT, "runs", "figure_qa")
EXPECTED = [f"fig{i:02d}_" for i in range(1, 11)]


def _intersection(a, b):
    left, bottom = max(a.x0, b.x0), max(a.y0, b.y0)
    right, top = min(a.x1, b.x1), min(a.y1, b.y1)
    return max(0.0, right - left) * max(0.0, top - bottom)


def _tick_like(text):
    """Matplotlib can retain off-canvas locator ticks even after axis('off')."""
    compact = text.replace("$", "").replace("\\mathdefault", "")
    compact = compact.replace("{", "").replace("}", "")
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:\^[-+]?\d+)?", compact))


def inspect_figure(fig, name):
    """Inspect matplotlib text geometry before export; do not reject intentional overlap."""
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    texts = []
    tick_texts = set()
    for axis in fig.axes:
        tick_texts.update(axis.get_xticklabels())
        tick_texts.update(axis.get_yticklabels())
    for artist in fig.findobj(lambda item: hasattr(item, "get_window_extent")):
        if (not hasattr(artist, "get_text") or not hasattr(artist, "get_fontsize")
                or not artist.get_visible()):
            continue
        if hasattr(artist, "axes") and artist.axes is not None:
            if not artist.axes.get_visible() or not artist.axes.axison:
                continue
        if artist in tick_texts:
            continue
        text = artist.get_text().strip()
        if not text:
            continue
        try:
            bbox = artist.get_window_extent(renderer)
        except (AttributeError, RuntimeError, ValueError):
            continue
        if bbox.width <= 0 or bbox.height <= 0:
            continue
        texts.append({"text": text, "font_pt": float(artist.get_fontsize()), "bbox": bbox,
                      "axes": getattr(artist, "axes", None)})
    warnings = []
    for i, left in enumerate(texts):
        for right in texts[i + 1:]:
            if left["axes"] is not right["axes"]:
                continue
            overlap = _intersection(left["bbox"], right["bbox"])
            small = min(left["bbox"].width * left["bbox"].height,
                        right["bbox"].width * right["bbox"].height)
            if small and overlap / small > 0.55:
                warnings.append({"kind": "text_overlap_candidate", "left": left["text"],
                                 "right": right["text"], "fraction": round(overlap / small, 3)})
    for item in texts:
        bbox = item["bbox"]
        if item["font_pt"] < 7.45:
            warnings.append({"kind": "small_text", "text": item["text"],
                             "font_pt": round(item["font_pt"], 2)})
        if (not _tick_like(item["text"]) and
                (bbox.x0 < -5 or bbox.y0 < -5 or bbox.x1 > width + 5 or bbox.y1 > height + 5)):
            warnings.append({"kind": "text_outside_canvas", "text": item["text"]})
    return {"figure": name, "canvas_px": [width, height], "text_count": len(texts),
            "warnings": warnings}


def _image_report(path):
    from PIL import Image

    image = Image.open(path).convert("RGB")
    pixels = np.asarray(image)
    non_white = np.any(pixels < 246, axis=2)
    content_fraction = float(non_white.mean())
    ys, xs = np.where(non_white)
    if len(xs):
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    else:
        bbox = None
    return {"path": os.path.basename(path), "size_px": list(image.size),
            "content_fraction": round(content_fraction, 5), "content_bbox": bbox,
            "blank": content_fraction < 0.01}


def _pdf_font_report(path):
    command = shutil.which("pdffonts")
    if command is None:
        return {"available": False, "embedded": None}
    output = subprocess.run([command, path], check=False, capture_output=True, text=True).stdout.splitlines()
    rows = [line.split() for line in output[2:] if line.strip()]
    embedded = bool(rows) and all(len(row) >= 4 and row[3].lower() == "yes" for row in rows)
    return {"available": True, "embedded": embedded, "font_rows": len(rows)}


def build_report():
    report = {"figures": [], "layout_reports": []}
    for prefix in EXPECTED:
        pngs = [name for name in os.listdir(FIGURE_DIR) if name.startswith(prefix) and name.endswith(".png")]
        pdfs = [name for name in os.listdir(FIGURE_DIR) if name.startswith(prefix) and name.endswith(".pdf")]
        if len(pngs) != 1 or len(pdfs) != 1:
            report["figures"].append({"prefix": prefix, "missing_or_duplicate": True,
                                      "png": pngs, "pdf": pdfs})
            continue
        item = _image_report(os.path.join(FIGURE_DIR, pngs[0]))
        item["pdf_fonts"] = _pdf_font_report(os.path.join(FIGURE_DIR, pdfs[0]))
        report["figures"].append(item)
    if os.path.isdir(QA_DIR):
        for name in sorted(os.listdir(QA_DIR)):
            if name.startswith("fig") and name.endswith(".json"):
                with open(os.path.join(QA_DIR, name), encoding="utf-8") as handle:
                    layout = json.load(handle)
                    layout["warnings"] = [warning for warning in layout.get("warnings", [])
                                          if not (warning.get("kind") == "text_outside_canvas"
                                                  and _tick_like(warning.get("text", "")))]
                    report["layout_reports"].append(layout)
    return report


def contact_sheet():
    from PIL import Image, ImageDraw

    names = []
    for prefix in EXPECTED:
        names.extend(sorted(name for name in os.listdir(FIGURE_DIR)
                            if name.startswith(prefix) and name.endswith(".png")))
    thumbs = []
    for name in names:
        image = Image.open(os.path.join(FIGURE_DIR, name)).convert("RGB")
        image.thumbnail((980, 760))
        thumbs.append((name, image.copy()))
    cell_w, cell_h = 1040, 820
    sheet = Image.new("RGB", (cell_w * 2, cell_h * 5), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        x, y = (index % 2) * cell_w, (index // 2) * cell_h
        sheet.paste(image, (x + (cell_w - image.width) // 2, y + 42))
        draw.text((x + 28, y + 16), name.replace(".png", ""), fill="#1F2930")
    path = os.path.join(FIGURE_DIR, "contact_sheet.png")
    sheet.save(path, dpi=(300, 300))
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = build_report()
    os.makedirs(QA_DIR, exist_ok=True)
    output = os.path.join(QA_DIR, "report.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    path = contact_sheet()
    warnings = sum(len(item.get("warnings", ())) for item in report["layout_reports"])
    blanks = sum(1 for item in report["figures"] if item.get("blank"))
    print(json.dumps({"report": output, "contact_sheet": path, "warnings": warnings,
                      "blank_images": blanks}, ensure_ascii=False))
    if args.strict and (warnings or blanks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
