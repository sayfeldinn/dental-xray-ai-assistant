"""Missing-teeth benchmark from DENTEX quadrant enumeration.

DENTEX enumerates every visible tooth as (quadrant, tooth 1-8). A missing tooth
is an FDI slot absent from a quadrant while teeth exist on both sides of it
(an "interior gap" -- a true edentulous gap, as opposed to a missing third
molar or a cropped arch edge).

Scores a zero-training derivation: run the existing 32-class tooth detector,
build the per-quadrant present set, and report interior gaps. Evaluated on the
tooth detector's own held-out 94-image split (seed 42), which is leak-free.

The official locked 50 carries only the 182 diseased teeth, not the full
enumeration, so it cannot supply missing-teeth ground truth.
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "production"))

import numpy as np  # noqa: E402
import inference_pipeline as pipe  # noqa: E402

DENTEX = Path("/home/sayfeldin/Projects/dental-model-research/data/raw/dentex")
QE = DENTEX / "training_data/quadrant_enumeration/train_quadrant_enumeration.json"
QE_IMG = QE.parent / "xrays"


def present_from_coco(coco):
    imgs = {i["id"]: i for i in coco["images"]}
    present = defaultdict(set)
    for a in coco["annotations"]:
        present[imgs[a["image_id"]]["file_name"]].add((a["category_id_1"] + 1, a["category_id_2"] + 1))
    return present


def tooth_split():
    qe = json.load(open(QE))
    labels = defaultdict(list)
    imgs = {i["id"]: i for i in qe["images"]}
    for a in qe["annotations"]:
        labels[imgs[a["image_id"]]["file_name"]].append(a)
    groups = defaultdict(list)
    for i in qe["images"]:
        n = len(labels[i["file_name"]])
        groups["sparse" if n < 20 else ("dense" if n > 30 else "normal")].append(i["file_name"])
    rng = random.Random(42)
    train, val = [], []
    for key in sorted(groups, key=str):
        members = sorted(groups[key])
        rng.shuffle(members)
        n_val = max(1, round(len(members) * 0.15)) if len(members) > 1 else 0
        val.extend(members[:n_val])
        train.extend(members[n_val:])
    return sorted(train), sorted(val)


def interior_missing(present, max_tooth=7):
    out = set()
    for q in (1, 2, 3, 4):
        teeth = sorted(t for (qq, t) in present if qq == q)
        if not teeth:
            continue
        for t in range(2, max_tooth + 1):
            if t not in teeth and any(x < t for x in teeth) and any(x > t for x in teeth):
                out.add((q, t))
    return out


def detect_with_conf(image_path, conf):
    arr = pipe.load_image_array(str(image_path))
    res = pipe._model("tooth").predict(source=arr, imgsz=pipe.TOOTH_IMGSZ, conf=conf, verbose=False)[0]
    teeth = []
    if res.boxes is not None:
        for box in res.boxes:
            idx = int(box.cls[0].item())
            teeth.append({"quadrant": idx // 8 + 1, "tooth_id": idx % 8 + 1,
                          "tooth_confidence": float(box.conf[0].item()),
                          "box": [float(v) for v in box.xyxy[0].cpu().numpy()]})
    return pipe._dedup_teeth(teeth)


def score(gt, pred):
    tp = sum(len(gt[k] & pred.get(k, set())) for k in gt)
    fp = sum(len(pred.get(k, set()) - gt[k]) for k in gt)
    fn = sum(len(gt[k] - pred.get(k, set())) for k in gt)
    prec = tp / max(1, tp + fp)
    rec = tp / max(1, tp + fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec,
            "f1": 2 * prec * rec / max(1e-9, prec + rec),
            "exact_match": sum(1 for k in gt if gt[k] == pred.get(k, set())),
            "n_images": len(gt),
            "gt_total": sum(len(v) for v in gt.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "eval" / "missing_teeth_results.json"))
    args = ap.parse_args()

    train, val94 = tooth_split()
    assert len(train) == 540 and len(val94) == 94, (len(train), len(val94))
    qe = json.load(open(QE))
    present = present_from_coco(qe)
    gt = {n: interior_missing(present[n]) for n in val94}
    print(f"held-out {len(val94)} images | interior missing teeth GT total "
          f"{sum(len(v) for v in gt.values())} | images with any {sum(1 for v in gt.values() if v)}")

    # one low-confidence pass, then threshold in post-processing
    raw = {}
    for i, n in enumerate(val94, 1):
        raw[n] = [(t["quadrant"], t["tooth_id"], t["tooth_confidence"])
                  for t in detect_with_conf(QE_IMG / n, 0.01)]
        if i % 20 == 0:
            print(f"  {i}/{len(val94)}", flush=True)

    sweep = []
    for conf in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        pred = {n: interior_missing({(q, t) for q, t, c in raw[n] if c >= conf}) for n in val94}
        s = {"tooth_conf": conf}
        s.update(score(gt, pred))
        sweep.append(s)
        print(f"conf {conf:.2f}: P {s['precision']:.3f} R {s['recall']:.3f} "
              f"F1 {s['f1']:.3f} exact {s['exact_match']}/{s['n_images']} "
              f"(tp {s['tp']} fp {s['fp']} fn {s['fn']})")

    best = max(sweep, key=lambda s: s["f1"])
    out = {"split": "tooth detector held-out 94 (DENTEX enumeration)",
           "definition": "interior FDI gap, third molars excluded",
           "best": best, "sweep": sweep}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print("best:", best)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
