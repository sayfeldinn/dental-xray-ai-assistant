"""Shared DENTEX data utilities for the ML rebuild.

Pure Python (json + pathlib + shutil); no numpy/pandas/torch so the exact same
code runs in a local notebook and in a Kaggle notebook. Same seed -> identical
splits everywhere.

Conventions
-----------
* DENTEX COCO files use ``category_id_*`` fields:
    category_id_1: quadrant 0-3  -> FDI quadrant 1-4
    category_id_2: tooth    0-7  -> FDI tooth    1-8
    category_id_3: disease  0-3  -> Impacted, Caries, Periapical Lesion, Deep Caries
* YOLO labels are ``class cx cy w h`` normalised to the image size.
* Tooth detector classes are the 32 FDI positions, index = (q-1)*8 + (t-1).
"""

from __future__ import annotations

import json
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

DISEASE_NAMES = ["Impacted", "Caries", "Periapical Lesion", "Deep Caries"]


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

def load_coco(path):
    with open(path) as fh:
        return json.load(fh)


def image_map(coco):
    return {img["id"]: img for img in coco["images"]}


def image_names(coco):
    return sorted(img["file_name"] for img in coco["images"])


# ----------------------------------------------------------------------
# Class mapping
# ----------------------------------------------------------------------

def tooth_class_names():
    """32 FDI classes in model-index order."""
    return [f"FDI_{q}{t}" for q in range(1, 5) for t in range(1, 9)]


def tooth_class_index(quadrant, tooth):
    """FDI quadrant 1-4 / tooth 1-8 -> class index 0-31."""
    return (quadrant - 1) * 8 + (tooth - 1)


def disease_class(ann):
    return ann["category_id_3"]


def tooth_class(ann):
    return tooth_class_index(ann["category_id_1"] + 1, ann["category_id_2"] + 1)


# ----------------------------------------------------------------------
# COCO -> YOLO
# ----------------------------------------------------------------------

def yolo_labels(coco, class_fn):
    """Return {file_name: ["cls cx cy w h", ...]} in YOLO normalised form."""
    imgs = image_map(coco)
    out = defaultdict(list)
    for ann in coco["annotations"]:
        img = imgs[ann["image_id"]]
        width, height = img["width"], img["height"]
        x, y, w, h = ann["bbox"]
        # clamp: DENTEX boxes occasionally poke a pixel outside the frame
        x1, y1 = max(0.0, x), max(0.0, y)
        x2, y2 = min(width, x + w), min(height, y + h)
        w, h = x2 - x1, y2 - y1
        if w <= 1 or h <= 1:
            continue
        out[img["file_name"]].append(
            f"{class_fn(ann)} "
            f"{(x1 + w / 2) / width:.6f} {(y1 + h / 2) / height:.6f} "
            f"{w / width:.6f} {h / height:.6f}"
        )
    return dict(out)


# ----------------------------------------------------------------------
# Splitting
# ----------------------------------------------------------------------

def stratified_split(names, signature_fn, val_frac=0.15, seed=42):
    """Deterministic stratified split.

    ``signature_fn(name)`` returns a hashable group key (e.g. the set of
    disease classes present in the image). Groups are shuffled with ``seed``
    and ~``val_frac`` of each group goes to validation, so rare classes are
    represented on both sides.
    """
    groups = defaultdict(list)
    for name in names:
        groups[signature_fn(name)].append(name)

    rng = random.Random(seed)
    train, val = [], []
    for key in sorted(groups, key=str):
        members = sorted(groups[key])
        rng.shuffle(members)
        n_val = max(1, round(len(members) * val_frac)) if len(members) > 1 else 0
        val.extend(members[:n_val])
        train.extend(members[n_val:])
    return sorted(train), sorted(val)


# ----------------------------------------------------------------------
# Writing a YOLO dataset
# ----------------------------------------------------------------------

def _yaml(names):
    lines = ["names:"]
    lines += [f"  {i}: {n}" for i, n in enumerate(names)]
    return "\n".join(lines) + "\n"


def build_yolo_dataset(out_root, name, image_src_dir, labels_by_name,
                       train_names, val_names, class_names, hardlink=True):
    """Materialise a YOLO dataset (images + labels + data.yaml).

    Images are hardlinked when possible (same filesystem) so the source data
    is not duplicated; falls back to copying.
    """
    root = Path(out_root) / name
    for split in ("train", "val"):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)

    stats = {"train_images": 0, "val_images": 0,
             "train_boxes": 0, "val_boxes": 0, "missing_images": []}

    for split, names in (("train", train_names), ("val", val_names)):
        for fname in names:
            src = Path(image_src_dir) / fname
            dst = root / "images" / split / fname
            if not dst.exists():
                if not src.exists():
                    stats["missing_images"].append(str(src))
                    continue
                try:
                    if hardlink:
                        os.link(src, dst)
                    else:
                        shutil.copy2(src, dst)
                except OSError:
                    shutil.copy2(src, dst)
            lines = labels_by_name.get(fname, [])
            label_path = root / "labels" / split / (Path(fname).stem + ".txt")
            label_path.write_text("\n".join(lines) + ("\n" if lines else ""))
            stats[f"{split}_images"] += 1
            stats[f"{split}_boxes"] += len(lines)

    (root / "data.yaml").write_text(
        f"path: {root.resolve()}\ntrain: images/train\nval: images/val\n"
        + _yaml(class_names)
    )
    return stats


def write_splits(path, payload):
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
