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
    """Inspect final-size text and CAD panels before export."""
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    texts = []
    all_tick_texts, valid_tick_texts = set(), set()
    for axis in fig.axes:
        active_axis = axis.get_visible() and axis.axison
        for values, labels, limits in (
            (axis.get_xticks(), axis.get_xticklabels(), axis.get_xlim()),
            (axis.get_yticks(), axis.get_yticklabels(), axis.get_ylim()),
        ):
            low, high = sorted(limits)
            for value, label in zip(values, labels):
                all_tick_texts.add(label)
                if active_axis and low - 1e-9 <= value <= high + 1e-9:
                    valid_tick_texts.add(label)
    for artist in fig.findobj(lambda item: hasattr(item, "get_window_extent")):
        if (not hasattr(artist, "get_text") or not hasattr(artist, "get_fontsize")
                or not artist.get_visible()):
            continue
        if hasattr(artist, "axes") and artist.axes is not None:
            if not artist.axes.get_visible() or not artist.axes.axison:
                continue
        if artist in all_tick_texts and artist not in valid_tick_texts:
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
            if small and overlap > 2.0 and overlap / small > 0.08:
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
    cad_panels = []
    for axis in fig.axes:
        artist = getattr(axis, "_saf_cad_artist", None)
        if artist is None:
            continue
        image = np.asarray(artist.get_array())[..., :3]
        mask = np.any(image < 248, axis=2)
        yy, xx = np.where(mask)
        bbox_fraction = 0.0
        if len(xx):
            bbox_fraction = ((xx.max() - xx.min() + 1) * (yy.max() - yy.min() + 1)
                             / float(image.shape[0] * image.shape[1]))
        semantic = np.zeros(mask.shape, dtype=bool)
        for rgb in ((44, 111, 178), (192, 57, 43), (122, 62, 157), (215, 131, 63)):
            semantic |= np.linalg.norm(image.astype(float) - np.asarray(rgb), axis=2) < 38
        semantic_fraction = float(semantic.mean())
        semantic_min = float(getattr(axis, "_saf_semantic_min", 0.0))
        item = {"bbox_fraction": round(float(bbox_fraction), 4),
                "semantic_fraction": round(semantic_fraction, 4),
                "semantic_min": round(semantic_min, 4)}
        cad_panels.append(item)
        if bbox_fraction < .55:
            warnings.append({"kind": "cad_underfilled", "fraction": round(float(bbox_fraction), 3)})
        if semantic_fraction < semantic_min:
            warnings.append({"kind": "semantic_area_too_small",
                             "fraction": round(semantic_fraction, 3),
                             "minimum": round(semantic_min, 3)})
        axis_bbox = axis.get_window_extent(renderer)
        for text_item in texts:
            if text_item["axes"] is axis and _intersection(text_item["bbox"], axis_bbox) > 2:
                warnings.append({"kind": "text_inside_cad_panel", "text": text_item["text"]})
    return {"figure": name, "canvas_px": [width, height], "text_count": len(texts),
            "cad_panels": cad_panels, "warnings": warnings}


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
    dpi = image.info.get("dpi", (0, 0))
    return {"path": os.path.basename(path), "size_px": list(image.size),
            "dpi": [round(float(dpi[0]), 1), round(float(dpi[1]), 1)],
            "content_fraction": round(content_fraction, 5), "content_bbox": bbox,
            "blank": content_fraction < 0.01,
            "dpi_ok": all(abs(float(value) - 600.0) < 2.0 for value in dpi)}


def _pdf_font_report(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return {"available": False, "embedded": False, "type3": None, "page_mm": None}
    reader = PdfReader(path)
    fonts, embedded, type3 = 0, True, False
    for page in reader.pages:
        resources = page.get("/Resources", {})
        for ref in resources.get("/Font", {}).values():
            font = ref.get_object(); fonts += 1
            subtype = str(font.get("/Subtype", ""))
            type3 |= subtype == "/Type3"
            candidates = [font]
            if subtype == "/Type0":
                candidates = [item.get_object() for item in font.get("/DescendantFonts", [])]
            for candidate in candidates:
                descriptor = candidate.get("/FontDescriptor")
                if descriptor is None:
                    embedded = False
                    continue
                descriptor = descriptor.get_object()
                embedded &= any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    page = reader.pages[0]
    width_mm = float(page.mediabox.width) / 72.0 * 25.4
    height_mm = float(page.mediabox.height) / 72.0 * 25.4
    return {"available": True, "embedded": bool(fonts and embedded), "type3": bool(type3),
            "font_rows": fonts, "page_mm": [round(width_mm, 2), round(height_mm, 2)]}


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
        large = image.copy(); large.thumbnail((1034, 780))
        small = image.copy(); small.thumbnail((502, 380))
        thumbs.append((name, large, small))
    cell_w, cell_h = 1600, 850
    sheet = Image.new("RGB", (cell_w, cell_h * len(thumbs)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, large, small) in enumerate(thumbs):
        y = index * cell_h
        sheet.paste(large, (32, y + 48))
        sheet.paste(small, (1080, y + 48))
        draw.text((28, y + 16), name.replace(".png", "") + "  |  175 mm", fill="#1F2930")
        draw.text((1080, y + 16), "85 mm stress preview", fill="#626A70")
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
    for item in report["figures"]:
        if not item.get("dpi_ok", False):
            warnings += 1
        pdf = item.get("pdf_fonts", {})
        if not pdf.get("embedded", False) or pdf.get("type3", False):
            warnings += 1
    blanks = sum(1 for item in report["figures"] if item.get("blank"))
    print(json.dumps({"report": output, "contact_sheet": path, "warnings": warnings,
                      "blank_images": blanks}, ensure_ascii=False))
    if args.strict and (warnings or blanks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
