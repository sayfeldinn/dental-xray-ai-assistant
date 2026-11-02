"""DENTEX v2 inference pipeline — tooth detector + disease detector.

Replaces the v1 design (quadrant coordinator -> disease detector -> random
forest on lesion-box geometry). Here every tooth is localised and classified
with its FDI number, and each lesion is assigned to the tooth it overlaps.

Output contract is unchanged, so the FastAPI service and the backend keep
working without modification:

    {
      "image_width", "image_height",
      "quadrants": [{"quadrant", "confidence", "box"}],   # derived, for overlays
      "detections": [{quadrant, tooth_id, tooth, tooth_confidence,
                      disease, disease_id, disease_confidence,
                      association_confidence, box}],
      "num_detections", "model"
    }
"""

import json
import os

import numpy as np
from PIL import Image
from ultralytics import YOLO

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(PACKAGE_DIR, "pipeline_config.json")) as fh:
    CONFIG = json.load(fh)

_MODELS = {}


def _model(key):
    """Load a detector on first use.

    Lazy so the service can start (and the tooth stage can be evaluated) while
    one of the two weight files is still being produced.
    """
    if key not in _MODELS:
        _MODELS[key] = YOLO(os.path.join(PACKAGE_DIR, CONFIG[f"{key}_model"]))
    return _MODELS[key]

DISEASE_MAP = {int(k): v for k, v in CONFIG["disease_map"].items()}

TOOTH_IMGSZ = CONFIG.get("tooth_imgsz", 1024)
DISEASE_IMGSZ = CONFIG.get("disease_imgsz", 1024)
TOOTH_CONF = CONFIG.get("tooth_conf", 0.25)
DISEASE_CONF = CONFIG.get("disease_conf", 0.25)


# ----------------------------------------------------------------------
# Image handling
# ----------------------------------------------------------------------

def load_image_array(image):
    if isinstance(image, str):
        return np.array(Image.open(image).convert("RGB"))
    if isinstance(image, Image.Image):
        return np.array(image.convert("RGB"))
    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)
        if image.shape[-1] == 4:
            image = image[..., :3]
        return image
    raise TypeError("image must be a filepath, PIL Image, or numpy array")


# ----------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------

def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter)


def _center(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def _contains(box, point):
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


# ----------------------------------------------------------------------
# Stage 1 — teeth
# ----------------------------------------------------------------------

def detect_teeth(image):
    """Return tooth boxes with FDI numbers.

    Model class index -> FDI: index = (quadrant - 1) * 8 + (tooth - 1).
    """
    result = _model("tooth").predict(source=image, imgsz=TOOTH_IMGSZ,
                                 conf=TOOTH_CONF, verbose=False)[0]
    if result.boxes is None:
        return []

    teeth = []
    for box in result.boxes:
        idx = int(box.cls[0].item())
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].cpu().numpy())
        quadrant, tooth = idx // 8 + 1, idx % 8 + 1
        teeth.append({
            "quadrant": quadrant,
            "tooth_id": tooth,
            "tooth": f"Tooth_{tooth}",
            "tooth_fdi": f"{quadrant}{tooth}",
            "tooth_confidence": float(box.conf[0].item()),
            "box": [x1, y1, x2, y2],
        })
    return teeth


# ----------------------------------------------------------------------
# Stage 2 — lesions
# ----------------------------------------------------------------------

def detect_diseases(image):
    result = _model("disease").predict(source=image, imgsz=DISEASE_IMGSZ,
                                   conf=DISEASE_CONF, verbose=False)[0]
    if result.boxes is None:
        return []

    lesions = []
    for box in result.boxes:
        disease_id = int(box.cls[0].item())
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].cpu().numpy())
        lesions.append({
            "disease_id": disease_id,
            "disease": DISEASE_MAP.get(disease_id, f"Unknown_{disease_id}"),
            "disease_confidence": float(box.conf[0].item()),
            "box": [x1, y1, x2, y2],
        })
    return lesions


# ----------------------------------------------------------------------
# Stage 3 — association
# ----------------------------------------------------------------------

def associate(lesions, teeth):
    """Assign every lesion to a tooth.

    Priority: highest IoU with a tooth box; else the tooth whose box contains
    the lesion centre; else the nearest tooth centre. A lesion with no teeth
    to attach to is dropped rather than mislabelled.
    """
    if not lesions or not teeth:
        return []

    output = []
    for lesion in lesions:
        lbox = lesion["box"]
        center = _center(lbox)

        best = max(teeth, key=lambda t: _iou(lbox, t["box"]))
        if _iou(lbox, best["box"]) <= 0.0:
            containing = [t for t in teeth if _contains(t["box"], center)]
            if containing:
                best = min(containing, key=lambda t: (t["box"][2] - t["box"][0]) *
                                                      (t["box"][3] - t["box"][1]))
            else:
                best = min(teeth, key=lambda t: (_center(t["box"])[0] - center[0]) ** 2 +
                                                 (_center(t["box"])[1] - center[1]) ** 2)

        output.append({
            "quadrant": best["quadrant"],
            "tooth_id": best["tooth_id"],
            "tooth": best["tooth"],
            "tooth_fdi": best["tooth_fdi"],
            "tooth_confidence": best["tooth_confidence"],
            "disease": lesion["disease"],
            "disease_id": lesion["disease_id"],
            "disease_confidence": lesion["disease_confidence"],
            "association_confidence": lesion["disease_confidence"] * best["tooth_confidence"],
            "box": lbox,
        })
    return output


def derive_quadrants(teeth):
    """Union of tooth boxes per FDI quadrant, for UI overlays."""
    by_q = {}
    for tooth in teeth:
        q = tooth["quadrant"]
        if q not in by_q:
            by_q[q] = {"quadrant": q, "confidence": 0.0,
                       "box": list(tooth["box"])}
            by_q[q]["confidence"] = tooth["tooth_confidence"]
        else:
            b = by_q[q]["box"]
            t = tooth["box"]
            by_q[q]["box"] = [min(b[0], t[0]), min(b[1], t[1]),
                              max(b[2], t[2]), max(b[3], t[3])]
            by_q[q]["confidence"] = min(by_q[q]["confidence"], tooth["tooth_confidence"])
    return [by_q[q] for q in sorted(by_q)]


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------

def run_dentex_pipeline(image, save_json=None):
    image = load_image_array(image)
    height, width = image.shape[:2]

    teeth = detect_teeth(image)
    lesions = detect_diseases(image)
    detections = associate(lesions, teeth)

    output = {
        "image_width": int(width),
        "image_height": int(height),
        "quadrants": derive_quadrants(teeth),
        "detections": detections,
        "num_detections": len(detections),
        "model": {
            "tooth": CONFIG.get("tooth_model"),
            "disease": CONFIG.get("disease_model"),
            "architecture": "tooth_detector+disease_detector",
        },
    }

    if save_json is not None:
        with open(save_json, "w") as fh:
            json.dump(output, fh, indent=2)
    return output
