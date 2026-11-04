"""Evaluate the missing-teeth classifier against the derivation baseline.

Uses the cached tooth detections for the held-out 94 images (no detector
re-run) and the trained ResNet18 gap-vs-tooth model.

Baseline: interior FDI gaps at presence conf 0.30 (the F1 0.742 rule).
Classifier: same candidate slots, but each crop is scored; a detected tooth
that looks like a gap is demoted (recall) and a candidate gap is kept only if
it looks like a gap (precision).
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from torchvision import models

HERE = Path(__file__).resolve().parent

QE = Path("/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
          "training_data/quadrant_enumeration/train_quadrant_enumeration.json")
IMG = QE.parent / "xrays"
CACHE = Path("/tmp/opencode/tooth_raw94.json")
INTERIOR = range(2, 8)
SIZE, PAD = 224, 0.10


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
        m = sorted(groups[key]); rng.shuffle(m)
        k = max(1, round(len(m) * 0.15)) if len(m) > 1 else 0
        val.extend(m[:k]); train.extend(m[k:])
    return sorted(train), sorted(val)


def crop_pil(im, box):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    x1, x2 = x1 - PAD * w, x2 + PAD * w
    y1, y2 = y1 - PAD * h, y2 + PAD * h
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(im.width, x2), min(im.height, y2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return None
    return im.crop((x1, y1, x2, y2)).resize((SIZE, SIZE), Image.BILINEAR)


def interp_box(te, t):
    """te: {tooth_id: [x1,y1,x2,y2]} for detected teeth in one quadrant."""
    lo = [x for x in te if x < t]
    hi = [x for x in te if x > t]
    if not lo or not hi:
        return None
    L, H = max(lo), min(hi)
    bl, bh = te[L], te[H]
    a = (t - L) / (H - L)
    x = (bl[0] + bl[2]) / 2 * (1 - a) + (bh[0] + bh[2]) / 2 * a
    y = (bl[1] + bl[3]) / 2 * (1 - a) + (bh[1] + bh[3]) / 2 * a
    w = ((bl[2] - bl[0]) + (bh[2] - bh[0])) / 2
    h = ((bl[3] - bl[1]) + (bh[3] - bh[1])) / 2
    return [x - w / 2, y - h / 2, x + w / 2, y + h / 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/kaggle_out_mt/missing_teeth.pt")
    ap.add_argument("--out", default=str(HERE / "eval" / "missing_teeth_model_results.json"))
    args = ap.parse_args()

    _, val94 = tooth_split()
    qe = json.load(open(QE))
    imgs = {i["id"]: i for i in qe["images"]}
    gt = defaultdict(set)
    for a in qe["annotations"]:
        gt[imgs[a["image_id"]]["file_name"]].add((a["category_id_1"] + 1, a["category_id_2"] + 1))
    raw = json.load(open(CACHE))

    ckpt = torch.load(args.model, map_location="cpu")
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    tf = T.Compose([T.ToTensor(), T.Normalize(ckpt["mean"], ckpt["std"])])

    @torch.no_grad()
    def gap_prob(crop):
        return float(torch.softmax(model(tf(crop).unsqueeze(0)), 1)[0, 1])

    def det_by_quad(n, conf):
        out = defaultdict(dict)
        for o in raw[n]:
            if o["c"] >= conf and o["t"] in INTERIOR:
                out[o["q"]][o["t"]] = o["box"]
        return out

    def gt_missing(n):
        out = set()
        for q in (1, 2, 3, 4):
            teeth = sorted(t for (qq, t) in gt[n] if qq == q)
            for t in INTERIOR:
                if t not in teeth and any(x < t for x in teeth) and any(x > t for x in teeth):
                    out.add((q, t))
        return out

    def derive(n, conf):
        out = set()
        for q, te in det_by_quad(n, conf).items():
            for t in INTERIOR:
                if t not in te and any(x < t for x in te) and any(x > t for x in te):
                    out.add((q, t))
        return out

    def score(pred_fn):
        tp = fp = fn = 0
        for n in val94:
            g, p = gt_missing(n), pred_fn(n)
            tp += len(g & p); fp += len(p - g); fn += len(g - p)
        pr = tp / max(1, tp + fp); rc = tp / max(1, tp + fn)
        return {"tp": tp, "fp": fp, "fn": fn, "precision": pr, "recall": rc,
                "f1": 2 * pr * rc / max(1e-9, pr + rc)}

    results = {"model_val_auc": ckpt.get("val_auc"), "baselines": {}, "classifier": []}
    for conf in (0.20, 0.25, 0.30, 0.40):
        s = score(lambda n, c=conf: derive(n, c))
        results["baselines"][f"derivation_conf_{conf}"] = s
        print(f"derivation conf {conf}: P {s['precision']:.3f} R {s['recall']:.3f} "
              f"F1 {s['f1']:.3f} (tp {s['tp']} fp {s['fp']} fn {s['fn']})")

    pre_by_conf = {}
    for conf in (0.30,):
        pre = {}
        for n in val94:
            im = Image.open(IMG / n).convert("RGB")
            det, gaps = {}, {}
            for q, te in det_by_quad(n, conf).items():
                for t, b in te.items():
                    c = crop_pil(im, b)
                    det[(q, t)] = gap_prob(c) if c is not None else 0.0
                for t in INTERIOR:
                    if t in te:
                        continue
                    b = interp_box(te, t)
                    if b is None:
                        continue
                    c = crop_pil(im, b)
                    gaps[(q, t)] = gap_prob(c) if c is not None else 0.0
            pre[n] = (det, gaps)
            if len(pre) % 20 == 0:
                print(f"  probs conf {conf} {len(pre)}/{len(val94)}", flush=True)
        pre_by_conf[conf] = pre

        for t_gap in (0.3, 0.4, 0.5, 0.6, 0.7):
            for t_tooth in (1.1, 0.9, 0.8, 0.7):
                def pred(n, tg=t_gap, tt=t_tooth):
                    det, gaps = pre[n]
                    return ({k for k, p in gaps.items() if p >= tg} |
                            {k for k, p in det.items() if p >= tt})
                s = score(pred)
                s.update({"conf": conf, "t_gap": t_gap, "t_tooth": t_tooth})
                results["classifier"].append(s)

    best = max(results["classifier"], key=lambda s: s["f1"])
    results["best"] = best
    print("\nBEST classifier:", {k: best[k] for k in
          ("conf", "t_gap", "t_tooth", "precision", "recall", "f1", "tp", "fp", "fn")})

    # split-half threshold selection: pick t_gap on one half, score the other
    pre = pre_by_conf[0.30]
    idx = sorted(val94)
    random.Random(0).shuffle(idx)
    A, B = idx[:47], idx[47:]

    def score_on(names, t_gap):
        tp = fp = fn = 0
        for n in names:
            det, gaps = pre[n]
            p = {k for k, v in gaps.items() if v >= t_gap}
            g = gt_missing(n)
            tp += len(g & p); fp += len(p - g); fn += len(g - p)
        pr = tp / max(1, tp + fp); rc = tp / max(1, tp + fn)
        return 2 * pr * rc / max(1e-9, pr + rc)

    grid = (0.3, 0.4, 0.5, 0.6, 0.7)
    tg_a = max(grid, key=lambda t: score_on(A, t))
    tg_b = max(grid, key=lambda t: score_on(B, t))
    cross = {"A->B": score_on(B, tg_a), "B->A": score_on(A, tg_b),
             "tg_selected_on_A": tg_a, "tg_selected_on_B": tg_b,
             "mean": (score_on(B, tg_a) + score_on(A, tg_b)) / 2}
    results["split_half"] = cross
    print("split-half threshold check:", cross)

    Path(args.out).write_text(json.dumps(results, indent=2))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
