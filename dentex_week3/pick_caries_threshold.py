"""Pick the caries-verifier gate threshold on the held-out 107-image DENTEX
split (never used to train the detector or the verifier), then report the
locked-50 result once.

The gate drops Caries / Deep Caries detections whose tooth-crop verifier
probability is below the threshold. Threshold is chosen to maximize F1 on the
detector's own caries detections in the held-out split.
"""
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "production"))

import rerank_caries as rc  # noqa: E402
import inference_pipeline as pipe  # noqa: E402

QED = Path("/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
           "training_data/quadrant-enumeration-disease/train_quadrant_enumeration_disease.json")
VAL_IMG = QED.parent / "xrays"

TARGET_IDS = (1,)  # Caries GT


def v3_split():
    qed = json.load(open(QED))
    imgs = {i["id"]: i for i in qed["images"]}
    ids = defaultdict(set)
    for ann in qed["annotations"]:
        ids[ann["image_id"]].add(ann["category_id_3"])
    name_to_ids = {i["file_name"]: tuple(sorted(ids.get(i["id"], ()))) for i in qed["images"]}
    groups = defaultdict(list)
    for n in name_to_ids:
        groups[name_to_ids[n]].append(n)
    rng = random.Random(42)
    train, val = [], []
    for key in sorted(groups):
        items = sorted(groups[key])
        rng.shuffle(items)
        n_val = max(1, int(round(len(items) * 0.15))) if len(items) > 1 else 0
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    return sorted(train), sorted(val), qed


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    if i <= 0:
        return 0.0
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i)


def collect(images, gt_boxes, verifier):
    model, tf, _ = verifier
    pairs = []  # (p, conf, is_tp)
    for name in images:
        path = VAL_IMG / name
        arr = pipe.load_image_array(str(path))
        teeth = pipe.detect_teeth(arr)
        les = pipe.detect_diseases(arr)
        im = Image.open(path).convert("RGB")
        gts = gt_boxes.get(name, [])
        for l in les:
            if l["disease"] != "Caries":
                continue
            p = 1.0
            if teeth:
                c = rc.crop_tooth(im, rc.match_tooth(l, teeth)["box"])
                if c is not None:
                    p = rc.score_crops(model, tf, [c])[0]
            tp = int(any(iou(l["box"], b) >= 0.5 for b in gts))
            pairs.append((p, l["disease_confidence"], tp))
    return pairs


def best_threshold(pairs):
    P = np.array([t[0] for t in pairs])
    T = np.array([t[2] for t in pairs])
    pos = T.sum()
    best = (0.0, -1.0)
    for thr in np.arange(0.05, 1.0, 0.05):
        m = P >= thr
        if not m.any():
            continue
        tp = T[m].sum()
        fp = m.sum() - tp
        fn = pos - tp
        f1 = 2 * tp / max(1, 2 * tp + fp + fn)
        if f1 > best[1]:
            best = (round(float(thr), 2), float(f1))
    return best


def main():
    verifier = rc.load_verifier(sys.argv[1])
    train, val, qed = v3_split()
    assert len(train) == 598 and len(val) == 107
    boxes = defaultdict(list)
    img_by_id = {i["id"]: i for i in qed["images"]}
    for ann in qed["annotations"]:
        if ann["category_id_3"] in TARGET_IDS:
            x, y, w, h = ann["bbox"]
            img = img_by_id[ann["image_id"]]
            boxes[img["file_name"]].append([x, y, x + w, y + h])

    print(f"held-out val images: {len(val)}")
    pairs = collect(val, boxes, verifier)
    pos = sum(t[2] for t in pairs)
    print(f"caries detections {len(pairs)} | TP {pos} | FP {len(pairs) - pos}")
    thr, f1 = best_threshold(pairs)
    print(f"F1-optimal threshold on held-out val: {thr} (F1 {f1:.3f})")
    for t in (0.5, 0.7, 0.8, 0.9):
        P = np.array([x[0] for x in pairs])
        T = np.array([x[2] for x in pairs])
        m = P >= t
        if m.any():
            print(f"  thr {t}: kept {m.sum()} prec {T[m].mean():.3f} rec {T[m].sum()/max(1,pos):.3f}")

    # AP on the held-out val: baseline (rank by conf) vs gate (drop p<thr, rank by conf)
    def ap(conf, tp):
        conf = np.asarray(conf, float)
        tp = np.asarray(tp, float)
        o = np.argsort(-conf)
        tp = tp[o]
        npos = tp.sum()
        if npos == 0:
            return float("nan")
        tpc = np.cumsum(tp)
        fpc = np.cumsum(1 - tp)
        prec = tpc / np.maximum(tpc + fpc, 1)
        rec = tpc / npos
        a, prev = 0.0, 0.0
        for i in range(len(tp) - 1, -1, -1):
            if rec[i] > prev:
                a += (rec[i] - prev) * prec[i]
                prev = rec[i]
        return a

    C = [x[1] for x in pairs]
    T = [x[2] for x in pairs]
    Pb = np.array([x[0] for x in pairs])
    print(f"\nheld-out val Caries AP baseline (rank by conf): {ap(C, T):.4f}")
    for t in (0.5, 0.7, 0.8, 0.9):
        m = Pb >= t
        print(f"  gate {t}: Caries AP {ap([C[i] for i in range(len(C)) if m[i]], [T[i] for i in range(len(T)) if m[i]]):.4f} "
              f"(kept {int(m.sum())}/{len(C)})")
    json.dump({"threshold": thr, "f1": f1, "n": len(pairs), "pos": int(pos)},
              open(HERE / "eval" / "caries_verifier_threshold.json", "w"), indent=2)


if __name__ == "__main__":
    main()
