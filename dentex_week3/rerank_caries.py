#!/usr/bin/env python3
"""Re-rank caries detections with the tooth-crop verifier, then score the
locked 50 with the unchanged ``evaluate.py`` judge.

The v3 detector localises caries well but ranks it poorly. For every Caries /
Deep Caries detection the verifier scores a tooth-sized crop; the detection
confidence becomes ``conf * p_verifier ** alpha`` before association, so false
positives can fall below the pipeline threshold without changing the detector.

Usage::

    python rerank_caries.py --verifier /path/to/caries_verifier.pt --alpha 1.0
    python rerank_caries.py --verifier ... --sweep          # alpha 0..2
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "production"))

import evaluate as judge          # noqa: E402
import inference_pipeline as pipe  # noqa: E402

SIZE = 224
PAD = 0.10
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
TARGET = ("Caries", "Deep Caries")


def load_verifier(path):
    ckpt = torch.load(path, map_location="cpu")
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    size = int(ckpt.get("size", SIZE))
    tf = transforms.Compose([
        transforms.Resize((size, size)) if size != 224 else transforms.Lambda(lambda im: im),
        transforms.ToTensor(),
        transforms.Normalize(ckpt.get("mean", MEAN), ckpt.get("std", STD)),
    ])
    return model, tf, ckpt


def crop_tooth(im, tb, size=SIZE, pad=PAD):
    x1, y1, x2, y2 = tb
    w, h = x2 - x1, y2 - y1
    x1, x2 = x1 - pad * w, x2 + pad * w
    y1, y2 = y1 - pad * h, y2 + pad * h
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(im.width, x2), min(im.height, y2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return None
    return im.crop((x1, y1, x2, y2)).resize((size, size), Image.BILINEAR)


def match_tooth(lesion, teeth):
    """Same priority as inference_pipeline.associate."""
    lbox = lesion["box"]
    center = ((lbox[0] + lbox[2]) / 2, (lbox[1] + lbox[3]) / 2)
    best = max(teeth, key=lambda t: pipe._iou(lbox, t["box"]))
    if pipe._iou(lbox, best["box"]) <= 0.0:
        containing = [t for t in teeth if pipe._contains(t["box"], center)]
        if containing:
            best = min(containing, key=lambda t: (t["box"][2] - t["box"][0]) *
                       (t["box"][3] - t["box"][1]))
        else:
            best = min(teeth, key=lambda t: (pipe._center(t["box"])[0] - center[0]) ** 2 +
                       (pipe._center(t["box"])[1] - center[1]) ** 2)
    return best


@torch.no_grad()
def score_crops(model, tf, crops):
    batch = torch.stack([tf(im) for im in crops])
    prob = torch.softmax(model(batch), 1)[:, 1]
    return prob.tolist()


def reranked_pipeline(image, verifier, alpha):
    model, tf, _ = verifier
    arr = pipe.load_image_array(image)
    teeth = pipe.detect_teeth(arr)
    lesions = pipe.detect_diseases(arr)
    if teeth and lesions:
        crops, refs = [], []
        for lesion in lesions:
            if lesion["disease"] not in TARGET:
                continue
            tb = match_tooth(lesion, teeth)["box"]
            im = Image.open(image).convert("RGB") if isinstance(image, str) else Image.fromarray(arr)
            crop = crop_tooth(im, tb)
            if crop is None:
                continue
            crops.append(crop)
            refs.append(lesion)
        if crops:
            probs = score_crops(model, tf, crops)
            for lesion, p in zip(refs, probs):
                lesion["disease_confidence"] = float(lesion["disease_confidence"] * p ** alpha)
    detections = pipe.associate(lesions, teeth)
    return {
        "image_width": 0, "image_height": 0,
        "quadrants": pipe.derive_quadrants(teeth),
        "detections": detections,
        "num_detections": len(detections),
        "model": {"tooth": pipe.CONFIG.get("tooth_model"),
                  "disease": pipe.CONFIG.get("disease_model")},
    }


def run_cache(images_dir, gt, verifier, alpha):
    cache = {}
    for i, name in enumerate(sorted(gt), 1):
        path = os.path.join(images_dir, name)
        try:
            cache[name] = {"image": name, "ok": True,
                           "result": reranked_pipeline(path, verifier, alpha)}
        except Exception as exc:  # noqa: BLE001
            cache[name] = {"image": name, "ok": False,
                           "error": f"{type(exc).__name__}: {exc}"}
        if i % 10 == 0:
            print(f"  {i}/{len(gt)}", flush=True)
    return cache


def summarize(results):
    per = results["ap_per_class"]
    return {
        "mAP50": results["mAP50"],
        "mAP50_95": results["mAP50_95"],
        "precision": results["detection_micro"]["precision"],
        "recall": results["detection_micro"]["recall"],
        "caries_ap50": per["Caries"]["AP50"],
        "tooth": results["label_accuracy"]["tooth"]["rate"],
        "joint": results["label_accuracy"]["joint"]["rate"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", default=str(
        Path("/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
             "validation_data/quadrant_enumeration_disease/xrays")))
    ap.add_argument("--gt", default=str(
        Path("/home/sayfeldin/Projects/dental-model-research/data/downloads/"
             "validation_triple.json")))
    ap.add_argument("--verifier", required=True)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="smoke test on N images")
    ap.add_argument("--out", default=os.path.join(HERE, "eval"))
    args = ap.parse_args()

    gt = judge.load_ground_truth(args.gt)
    if args.limit:
        gt = {k: gt[k] for k in sorted(gt)[:args.limit]}
    print(f"locked 50: {len(gt)} images | verifier {args.verifier}")
    verifier = load_verifier(args.verifier)
    print("verifier val:", verifier[2].get("val"))

    alphas = [0.0, 0.5, 1.0, 1.5, 2.0] if args.sweep else [args.alpha]
    cache = run_cache(args.images_dir, gt, verifier, alphas[0])

    table = []
    for a in alphas:
        if a != alphas[0]:
            cache = run_cache(args.images_dir, gt, verifier, a)
        results = judge.evaluate(cache, gt)
        s = summarize(results)
        s["alpha"] = a
        table.append(s)
        print(f"alpha {a:>4}  mAP {s['mAP50']:.4f}  mAP50-95 {s['mAP50_95']:.4f}  "
              f"P {s['precision']:.4f}  R {s['recall']:.4f}  "
              f"Caries {s['caries_ap50']:.4f}  tooth {s['tooth']:.4f}  joint {s['joint']:.4f}",
              flush=True)
        if not args.sweep:
            os.makedirs(args.out, exist_ok=True)
            (Path(args.out) / "rerank_caries_results.json").write_text(json.dumps(
                {"verifier": args.verifier, "summary": s,
                 "val": verifier[2].get("val")}, indent=2))
            with open(Path(args.out) / "rerank_caries_raw.jsonl", "w") as fh:
                for name, rec in cache.items():
                    fh.write(json.dumps(rec) + "\n")

    if args.sweep:
        print(json.dumps(table, indent=2))


if __name__ == "__main__":
    main()
