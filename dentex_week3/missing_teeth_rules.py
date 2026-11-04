"""Compare missing-teeth derivation rules on the tooth detector's held-out 94.

Caches one low-confidence tooth-detection pass, then scores rule variants:
  neighbour  : any present tooth on each side (baseline)
  adjacent   : both direct neighbours (t-1, t+1) present
  maxgap1/2  : nearest present lower/higher within 2 / 3 FDI
  include8   : extend to third molars
  nbrconf    : neighbour detections must exceed a confidence floor
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "production"))

import inference_pipeline as pipe  # noqa: E402

QE = Path("/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
          "training_data/quadrant_enumeration/train_quadrant_enumeration.json")
QE_IMG = QE.parent / "xrays"
CACHE = Path("/tmp/opencode/tooth_raw94.json")


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
        m = sorted(groups[key]); rng.shuffle(m)
        k = max(1, round(len(m) * 0.15)) if len(m) > 1 else 0
        val.extend(m[:k]); train.extend(m[k:])
    return sorted(train), sorted(val)


def detect_raw(name, conf=0.01):
    arr = pipe.load_image_array(str(QE_IMG / name))
    res = pipe._model("tooth").predict(source=arr, imgsz=pipe.TOOTH_IMGSZ, conf=conf, verbose=False)[0]
    out = []
    if res.boxes is not None:
        for box in res.boxes:
            idx = int(box.cls[0].item())
            out.append({"q": idx // 8 + 1, "t": idx % 8 + 1,
                        "c": float(box.conf[0].item()),
                        "box": [float(v) for v in box.xyxy[0].cpu().numpy()]})
    return [{"q": d["quadrant"], "t": d["tooth_id"], "c": d["tooth_confidence"],
             "box": d["box"]} for d in pipe._dedup_teeth(
        [{"quadrant": o["q"], "tooth_id": o["t"], "box": o["box"],
          "tooth_confidence": o["c"]} for o in out])]


def present_map(raw, conf):
    pt = defaultdict(dict)
    for o in raw:
        if o["c"] >= conf:
            pt[o["q"]][o["t"]] = o["c"]
    return pt


def derive(pt, rule, max8, nbrconf):
    out = set()
    top = 8 if max8 else 7
    for q in (1, 2, 3, 4):
        teeth = pt.get(q, {})
        for t in range(2, top + 1):
            if t in teeth:
                continue
            lo = [x for x in teeth if x < t]
            hi = [x for x in teeth if x > t]
            if not lo or not hi:
                continue
            if nbrconf > 0:
                nl = max(lo, default=None); nh = min(hi, default=None)
                if nl is None or nh is None or teeth[nl] < nbrconf or teeth[nh] < nbrconf:
                    continue
            if rule == "adjacent":
                if (t - 1) not in teeth or (t + 1) not in teeth:
                    continue
            if rule == "maxgap1" and (min(hi) - max(lo)) > 3:
                continue
            if rule == "maxgap2" and (min(hi) - max(lo)) > 4:
                continue
            out.add((q, t))
    return out


def score(gt, pred):
    tp = sum(len(gt[k] & pred.get(k, set())) for k in gt)
    fp = sum(len(pred.get(k, set()) - gt[k]) for k in gt)
    fn = sum(len(gt[k] - pred.get(k, set())) for k in gt)
    p = tp / max(1, tp + fp); r = tp / max(1, tp + fn)
    return tp, fp, fn, p, r, 2 * p * r / max(1e-9, p + r)


def main():
    _, val94 = tooth_split()
    qe = json.load(open(QE))
    present = present_from_coco(qe)

    if CACHE.exists():
        raw = json.load(open(CACHE))
    else:
        raw = {}
        for i, n in enumerate(val94, 1):
            raw[n] = detect_raw(n)
            if i % 20 == 0:
                print(f"  detect {i}/{len(val94)}", flush=True)
        CACHE.write_text(json.dumps(raw))

    def gt_missing(name, max8):
        pt = defaultdict(dict)
        for (q, t) in present[name]:
            pt[q][t] = 1.0
        return derive(pt, "neighbour", max8, 0)

    best = None
    for max8 in (False, True):
        gt = {n: gt_missing(n, max8) for n in val94}
        for rule in ("neighbour", "adjacent", "maxgap1", "maxgap2"):
            for conf in (0.15, 0.20, 0.25, 0.30, 0.40):
                for nbrconf in (0.0, 0.30):
                    pred = {n: derive(present_map(raw[n], conf), rule, max8, nbrconf) for n in val94}
                    tp, fp, fn, p, r, f1 = score(gt, pred)
                    tag = f"max8={max8} rule={rule:9s} conf={conf:.2f} nbr={nbrconf:.2f}"
                    if best is None or f1 > best[0]:
                        best = (f1, tag, {"tp": tp, "fp": fp, "fn": fn, "p": p, "r": r,
                                          "gt_total": sum(len(v) for v in gt.values())})
    print("best by F1:")
    print(f"  {best[1]} -> F1 {best[0]:.3f} P {best[2]['p']:.3f} R {best[2]['r']:.3f} "
          f"(tp {best[2]['tp']} fp {best[2]['fp']} fn {best[2]['fn']}, gt {best[2]['gt_total']})")

    gt = {n: gt_missing(n, False) for n in val94}
    table = []
    for rule in ("neighbour", "adjacent", "maxgap1", "maxgap2"):
        for conf in (0.15, 0.20, 0.25, 0.30, 0.40):
            pred = {n: derive(present_map(raw[n], conf), rule, False, 0.0) for n in val94}
            tp, fp, fn, p, r, f1 = score(gt, pred)
            table.append({"rule": rule, "conf": conf, "precision": p, "recall": r,
                          "f1": f1, "tp": tp, "fp": fp, "fn": fn})
            print(f"  {rule:9s} conf {conf:.2f}: P {p:.3f} R {r:.3f} F1 {f1:.3f} (tp {tp} fp {fp} fn {fn})")

    out = HERE / "eval" / "missing_teeth_rules.json"
    out.write_text(json.dumps({"best": best[1], "best_f1": best[0], "table": table}, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
