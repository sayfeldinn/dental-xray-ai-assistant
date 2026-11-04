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

# Evaluation can point at candidate weights without touching the shipped ones:
#   DENTEX_MODEL_DIR=/tmp/v3_weights python ...
MODEL_DIR = os.environ.get("DENTEX_MODEL_DIR", PACKAGE_DIR)

with open(os.path.join(PACKAGE_DIR, "pipeline_config.json")) as fh:
    CONFIG = json.load(fh)

_MODELS = {}


def _model(key):
    """Load a detector on first use.

    Lazy so the service can start (and the tooth stage can be evaluated) while
    one of the two weight files is still being produced.
    """
    if key not in _MODELS:
        _MODELS[key] = YOLO(os.path.join(MODEL_DIR, CONFIG[f"{key}_model"]))
    return _MODELS[key]

DISEASE_MAP = {int(k): v for k, v in CONFIG["disease_map"].items()}

TOOTH_IMGSZ = CONFIG.get("tooth_imgsz", 1024)
DISEASE_IMGSZ = CONFIG.get("disease_imgsz", 1024)
TOOTH_CONF = CONFIG.get("tooth_conf", 0.25)
DISEASE_CONF = CONFIG.get("disease_conf", 0.25)
TOOTH_NMS_IOU = CONFIG.get("tooth_nms_iou", 0.6)

FINDINGS_IMGSZ = CONFIG.get("findings_imgsz", 640)
FINDINGS_CONF = CONFIG.get("findings_conf", 0.40)
FINDINGS_MAP = {int(k): v for k, v in CONFIG.get("findings_map", {}).items()}


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

def _dedup_teeth(teeth, iou_thresh=TOOTH_NMS_IOU):
    """Drop overlapping tooth boxes of different classes.

    YOLO's NMS is per-class, so the 32-class head can keep two class
    hypotheses for the same physical tooth. Without this, a lesion attaches
    to whichever duplicate happens to have the higher IoU — a common
    source of adjacent-tooth errors (e.g. 17 vs 18).
    """
    kept = []
    for t in sorted(teeth, key=lambda t: -t["tooth_confidence"]):
        if all(_iou(t["box"], k["box"]) < iou_thresh for k in kept):
            kept.append(t)
    return kept


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
    return _dedup_teeth(teeth)


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
# Optional stage — caries verifier (tooth-crop re-ranker)
# ----------------------------------------------------------------------

_VERIFIER = {}
CARIES_TARGETS = ("Caries", "Deep Caries")
VERIFIER_SIZE = 224
VERIFIER_PAD = 0.10


def _verifier_config():
    """Config block, overridable for experiments with
    DENTEX_CARIES_VERIFIER=/abs/path/verifier.pt[:alpha|gate:threshold]."""
    env = os.environ.get("DENTEX_CARIES_VERIFIER")
    if env:
        parts = env.split(":")
        cfg = {"enabled": True, "model": parts[0]}
        if len(parts) > 1 and parts[1] == "gate":
            cfg["mode"] = "gate"
            cfg["threshold"] = float(parts[2]) if len(parts) > 2 else 0.5
        elif len(parts) > 1:
            cfg["alpha"] = float(parts[1] or 1.0)
        return cfg
    return CONFIG.get("caries_verifier", {})


def _load_verifier(cfg):
    if "model" in _VERIFIER:
        return _VERIFIER["model"]
    import torch

    from torchvision import models

    path = cfg["model"]
    if not os.path.isabs(path):
        path = os.path.join(MODEL_DIR, path)
    ckpt = torch.load(path, map_location="cpu")
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    _VERIFIER["model"] = (model, ckpt)
    return _VERIFIER["model"]


def _crop_tooth(image, tb, size=VERIFIER_SIZE, pad=VERIFIER_PAD):
    from PIL import Image as _Image

    x1, y1, x2, y2 = tb
    w, h = x2 - x1, y2 - y1
    x1, x2 = x1 - pad * w, x2 + pad * w
    y1, y2 = y1 - pad * h, y2 + pad * h
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return None
    im = _Image.fromarray(image[int(y1):int(y2), int(x1):int(x2)])
    return im.resize((size, size), _Image.BILINEAR)


def apply_caries_verifier(lesions, teeth, image):
    """Down-weight caries detections whose tooth crop looks caries-free.

    confidence *= p_verifier ** alpha. This only re-ranks: the detector and
    the association logic are untouched. No-op when disabled or no teeth.
    """
    cfg = _verifier_config()
    if not cfg.get("enabled") or not cfg.get("model") or not teeth or not lesions:
        return lesions
    targets = [l for l in lesions if l["disease"] in CARIES_TARGETS]
    if not targets:
        return lesions

    crops = []
    for lesion in targets:
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
        crops.append(_crop_tooth(image, best["box"]))

    valid = [(l, c) for l, c in zip(targets, crops) if c is not None]
    if not valid:
        return lesions

    import torch
    from torchvision import transforms

    model, ckpt = _load_verifier(cfg)
    mean = ckpt.get("mean", (0.485, 0.456, 0.406))
    std = ckpt.get("std", (0.229, 0.224, 0.225))
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean, std)])
    batch = torch.stack([tf(c) for _, c in valid])
    with torch.no_grad():
        probs = torch.softmax(model(batch), 1)[:, 1].tolist()

    mode = cfg.get("mode", "scale")
    alpha = float(cfg.get("alpha", 1.0))
    threshold = float(cfg.get("threshold", 0.0))

    if mode == "gate":
        # drop caries detections the verifier thinks are caries-free
        drop = {id(l) for (l, _), p in zip(valid, probs)
                if p < threshold and l["disease"] in CARIES_TARGETS}
        kept = [l for l in lesions if id(l) not in drop]
        for (l, _), p in zip(valid, probs):
            l["caries_verifier_p"] = float(p)
        return kept

    for (lesion, _), p in zip(valid, probs):
        lesion["disease_confidence"] = float(lesion["disease_confidence"] * p ** alpha)
        lesion["caries_verifier_p"] = float(p)
    return lesions



# ----------------------------------------------------------------------
# Optional stage — restorations / missing teeth (advisory)
# ----------------------------------------------------------------------

def detect_findings(image):
    """Return restoration and dentition findings from the DentalOPG model.

    The model is trained and validated on DentalOPG only, and there is no
    DENTEX ground truth for missing teeth, BDR, fillings or crowns. Its output
    is advisory, is flagged with ``findings_advisory`` in ``/predict``, and
    never feeds the clinical report.
    """
    if not CONFIG.get("findings_model"):
        return []
    result = _model("findings").predict(source=image, imgsz=FINDINGS_IMGSZ,
                                        conf=FINDINGS_CONF, verbose=False)[0]
    if result.boxes is None:
        return []

    findings = []
    for box in result.boxes:
        idx = int(box.cls[0].item())
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].cpu().numpy())
        findings.append({
            "finding_id": idx,
            "finding": FINDINGS_MAP.get(idx, f"Unknown_{idx}"),
            "confidence": float(box.conf[0].item()),
            "box": [x1, y1, x2, y2],
        })
    return findings


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
    # Optional caries re-ranker; never let a missing verifier break /predict.
    try:
        lesions = apply_caries_verifier(lesions, teeth, image)
    except Exception:
        pass
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

    # Advisory layer: never let a missing findings weight break /predict.
    if CONFIG.get("findings_in_predict", False):
        try:
            output["findings"] = detect_findings(image)
        except Exception as exc:
            output["findings"] = []
            output["findings_error"] = str(exc)
        output["findings_advisory"] = True
        output["model"]["findings"] = CONFIG.get("findings_model")

    if save_json is not None:
        with open(save_json, "w") as fh:
            json.dump(output, fh, indent=2)
    return output


def run_findings(image):
    """Run the advisory findings model only (no tooth/disease detectors).

    The same boxes are appended to ``/predict`` when ``findings_in_predict`` is
    enabled; this entry point exists for clients that want findings alone and
    for isolating the model during validation.
    """
    image = load_image_array(image)
    height, width = image.shape[:2]
    findings = detect_findings(image)
    return {
        "image_width": int(width),
        "image_height": int(height),
        "findings": findings,
        "num_findings": len(findings),
        "model": {"findings": CONFIG.get("findings_model")},
        "advisory": True,
    }
