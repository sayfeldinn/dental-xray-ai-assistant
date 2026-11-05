"""Render ground truth vs model detections side by side for the locked-50 DENTEX set.

Reads the official DENTEX validation triple annotations and the live ML service,
then writes one PNG per image with two panels:

    left  = DENTEX ground truth (green)
    right = production v3 detections (amber)

This is a visual QA aid only: it never writes to the database and does not
change the locked-50 benchmark.

    python scripts/render_gt_vs_pred.py --names val_28.png val_31.png val_2.png

Environment overrides: ML_URL, DENTEX_GT, DENTEX_XRAYS, OUT_DIR.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ML_URL = os.environ.get("ML_URL", "http://127.0.0.1:8001")
GT_PATH = Path(os.environ.get(
    "DENTEX_GT",
    "/home/sayfeldin/Projects/dental-model-research/data/downloads/validation_triple.json"))
XRAY_DIR = Path(os.environ.get(
    "DENTEX_XRAYS",
    "/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
    "validation_data/quadrant_enumeration_disease/xrays"))
OUT_DIR = Path(os.environ.get("OUT_DIR", "submission/assets"))

GT_COLOR = (34, 197, 94)
PRED_COLOR = (245, 158, 11)
TEXT_COLOR = (15, 23, 42)
PANEL_W = 1400
GAP = 24
MARGIN = 24
HEADER_H = 56


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/usr/share/fonts/Adwaita/AdwaitaMono-Bold.ttf",
        "/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_box(draw: ImageDraw.ImageDraw, box, scale: float, color, label: str, font):
    x1, y1, x2, y2 = (v * scale for v in box)
    draw.rectangle([x1, y1, x2, y2], outline=color, width=max(2, int(scale * 4)))
    if not label:
        return
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ty = max(0, y1 - th - 6)
    draw.rectangle([x1, ty, x1 + tw + 8, ty + th + 6], fill=color)
    draw.text((x1 + 4, ty + 2), label, fill=TEXT_COLOR, font=font)


def predict(image_path: Path, threshold: float) -> dict:
    with image_path.open("rb") as fh:
        response = requests.post(
            f"{ML_URL}/predict",
            params={"confidence_threshold": threshold},
            files={"file": (image_path.name, fh, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()


def render(name: str, gt: dict, threshold: float, out_dir: Path) -> Path:
    image_path = XRAY_DIR / name
    image = Image.open(image_path).convert("RGB")
    scale = PANEL_W / image.width
    panel_h = int(image.height * scale)
    panel = image.resize((PANEL_W, panel_h), Image.LANCZOS)

    file_id = next(i["id"] for i in gt["images"] if i["file_name"] == name)
    anns = [a for a in gt["annotations"] if a["image_id"] == file_id]
    disease_names = {c["id"]: c["name"] for c in gt["categories_3"]}

    pred = predict(image_path, threshold)
    detections = pred.get("detections", [])

    font = load_font(max(14, int(panel_h * 0.024)))
    title_font = load_font(max(18, int(panel_h * 0.030)))

    canvas = Image.new(
        "RGB",
        (2 * PANEL_W + GAP + 2 * MARGIN, HEADER_H + panel_h + 2 * MARGIN),
        (248, 250, 252),
    )
    draw = ImageDraw.Draw(canvas)

    left = panel.copy()
    right = panel.copy()
    draw_left = ImageDraw.Draw(left)
    draw_right = ImageDraw.Draw(right)

    for a in anns:
        x, y, w, h = a["bbox"]
        fdi = f"{a['category_id_1'] + 1}{a['category_id_2'] + 1}"
        draw_box(draw_left, (x, y, x + w, y + h), scale, GT_COLOR,
                 f"{fdi} {disease_names.get(a['category_id_3'], '?')}", font)

    for d in detections:
        draw_box(draw_right, d["box"], scale, PRED_COLOR,
                 f"{d.get('tooth_fdi', '?')} {d.get('disease', '?')} {d.get('disease_confidence', 0):.2f}",
                 font)

    x0, y0 = MARGIN, HEADER_H + MARGIN
    canvas.paste(left, (x0, y0))
    canvas.paste(right, (x0 + PANEL_W + GAP, y0))

    draw.text((x0, MARGIN), f"{name} — ground truth ({len(anns)})", fill=TEXT_COLOR, font=title_font)
    draw.text((x0 + PANEL_W + GAP, MARGIN),
              f"v3 detections ({len(detections)} @ {threshold:.2f})", fill=TEXT_COLOR, font=title_font)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"gt_vs_pred_{Path(name).stem}.png"
    canvas.save(out_path, optimize=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names", nargs="+", default=["val_28.png", "val_31.png", "val_2.png"])
    parser.add_argument("--threshold", type=float, default=0.20)
    parser.add_argument("--gt", type=Path, default=GT_PATH)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    gt = json.loads(args.gt.read_text())
    for name in args.names:
        out = render(name, gt, args.threshold, args.out_dir)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
