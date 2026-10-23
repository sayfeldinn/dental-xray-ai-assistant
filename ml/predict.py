#!/usr/bin/env python3
"""Run Phase 1 YOLOv8s inference on a panoramic dental X-ray.

Usage:
    python ml/predict.py                                  # default test image
    python ml/predict.py ml/panorama-xray-example.jpeg
    python ml/predict.py img.jpg --conf 0.10 --imgsz 1024
    python ml/predict.py img.jpg --save                   # also write annotated JPG

Weights and the default image are resolved relative to this file, so the
script works from any working directory.
"""

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = HERE / "best.pt"
DEFAULT_IMAGE = HERE / "panorama-xray-example.jpeg"

# ml/README.md, "Class taxonomy (authoritative)"
EXPECTED_CLASSES = ["Inter-Radicular", "Non-Odontogenic", "Periapical", "Pericoronal", "Caries"]

RULE = "-" * 74


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Run the DentalAI YOLOv8s detector on a panoramic X-ray.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "image",
        nargs="?",
        default=str(DEFAULT_IMAGE),
        help="path to the X-ray image",
    )
    p.add_argument(
        "--weights",
        default=str(DEFAULT_WEIGHTS),
        help="path to the YOLO checkpoint (.pt)",
    )
    p.add_argument("--conf", type=float, default=0.25, help="minimum confidence threshold")
    p.add_argument("--imgsz", type=int, default=1024, help="inference image size")
    p.add_argument(
        "--save",
        action="store_true",
        help="also write an annotated JPG under runs/detect/predict/",
    )
    return p.parse_args(argv)


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def saved_annotation(result):
    """Ultralytics normalises the extension (.jpeg -> .jpg), so list the dir."""
    save_dir = getattr(result, "save_dir", None)
    if not save_dir:
        return None
    files = [p for p in Path(save_dir).iterdir() if p.is_file()]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def main(argv=None):
    args = parse_args(argv)

    weights = Path(args.weights).expanduser().resolve()
    image = Path(args.image).expanduser().resolve()

    if not weights.is_file():
        die(
            f"weights not found: {weights}\n"
            f"  fetch them with:\n"
            f"    gh release download v0.1-dental-yolov8s --pattern best.pt --dir ml"
        )
    if not image.is_file():
        die(f"image not found: {image}")

    try:
        from ultralytics import YOLO
    except ImportError:
        die("ultralytics is not installed: pip install ultralytics", code=3)

    try:
        model = YOLO(str(weights))
    except Exception as exc:
        die(f"failed to load {weights.name}: {exc}", code=3)

    started = time.perf_counter()
    try:
        results = model.predict(
            source=str(image),
            conf=args.conf,
            imgsz=args.imgsz,
            save=args.save,
            verbose=False,
        )
    except Exception as exc:
        die(f"inference failed: {exc}", code=4)
    elapsed = time.perf_counter() - started

    if not results:
        die("model returned no result object", code=4)

    result = results[0]
    names = result.names if isinstance(result.names, dict) else model.names
    height, width = result.orig_shape

    print(RULE)
    print(f"weights  : {weights}")
    print(f"classes  : {', '.join(f'{k}={v}' for k, v in sorted(names.items()))}")
    print(f"image    : {image}")
    print(f"size     : {width} x {height} px")
    print(f"params   : conf >= {args.conf}  imgsz={args.imgsz}")
    print(f"elapsed  : {elapsed:.2f} s")
    print(RULE)

    boxes = getattr(result, "boxes", None)
    rows = []
    if boxes is not None and len(boxes) > 0:
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf = float(boxes.conf[i].item())
            x1, y1, x2, y2 = (float(v) for v in boxes.xyxy[i].tolist())
            rows.append((conf, names.get(cls_id, str(cls_id)), cls_id, x1, y1, x2, y2))
        rows.sort(reverse=True, key=lambda r: r[0])

    if not rows:
        print(f"0 detections at conf >= {args.conf}.")
        print()
        print("This is a legitimate outcome, not a failure. On the held-out set this")
        print("checkpoint scores overall mAP@0.5 = 38.0% and Caries recall = 66.7%")
        print("(ml/README.md, 'Reported results'). Try lowering the threshold:")
        print(f"    python ml/predict.py {image.name} --conf 0.10")
        print(RULE)
        if args.save:
            path = saved_annotation(result)
            if path:
                print(f"annotated copy: {path}")
        return 0

    print(f"{'#':>2}  {'class':<18} {'conf':>6}  bbox (x1, y1, x2, y2)")
    print(RULE)
    for n, (conf, label, _cls, x1, y1, x2, y2) in enumerate(rows, 1):
        print(f"{n:>2}  {label:<18} {conf:>6.3f}  ({x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f})")
    print(RULE)
    print(f"{len(rows)} detection(s)")

    counts = {}
    for _conf, label, _cls, *_rest in rows:
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {label:<20} {count}")

    missing = [c for c in EXPECTED_CLASSES if c not in set(names.values())]
    if missing:
        print()
        print(f"warning: checkpoint is missing expected class(es): {', '.join(missing)}")
        print("  this may not be the Phase 1 5-class model - check ml/README.md")

    if args.save:
        print()
        path = saved_annotation(result)
        if path:
            print(f"annotated copy: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
