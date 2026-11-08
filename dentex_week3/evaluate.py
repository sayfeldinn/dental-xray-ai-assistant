#!/usr/bin/env python3
"""Held-out evaluation of the shipped DENTEX pipeline on the official
DENTEX validation set (50 panoramas, 182 annotated lesions with the full
quadrant + tooth + disease ground-truth triple).

Why this exists
---------------
``production/final_evaluation.json`` records disease 97.54% / tooth 76.23% /
joint 75.41% on 23 held-out images, but ships without a script or a file
list, so those numbers cannot be reproduced. This script makes the benchmark
reproducible and adds the detection-level metrics (precision / recall /
mAP50 / mAP50-95) that were never measured, with 95% Wilson confidence
intervals on every proportion.

Validity
--------
The 50 images come from the official DENTEX *validation* split. The training
notebook (``MLv2/notebook93943e382e.ipynb``) trained every model exclusively
on ``training_data/``; ``validation_data/`` is only used for inference after
training, and the per-model ``provenance/*/args.yaml`` logs confirm the data
roots. The validation split is therefore untouched by training.

Usage
-----
Drive a running ML service (default; no torch needed locally)::

    python evaluate.py \
        --images-dir /path/to/dentex/validation_data/quadrant_enumeration_disease/xrays \
        --gt /path/to/validation_triple.json \
        --api http://localhost:8001/predict

Or run the frozen pipeline in-process (needs ultralytics + torch + sklearn)::

    python evaluate.py --images-dir ... --gt ... --local

Outputs (in --out-dir): ``evaluation_results.json`` (all numbers, machine
readable) and ``evaluation_report.md`` (human readable). Raw per-image model
outputs are cached in ``raw_predictions.jsonl`` so re-runs are instant.

Notes
-----
* The threshold sweep can only raise the disease confidence threshold above
  the pipeline's baked-in 0.20 (detections below 0.20 are never returned).
  Sweeps below 0.20 require --local mode.
* Ground-truth id mapping is 1:1 with the pipeline: quadrant ids 0-3 -> 1-4,
  tooth ids 0-7 -> 1-8, disease ids 0-3 (Impacted, Caries, Periapical
  Lesion, Deep Caries) match ``production/pipeline_config.json``.
"""

import argparse
import json
import math
import os
import sys
import uuid
from collections import defaultdict

# ------------------------------------------------------------------
# Ground truth
# ------------------------------------------------------------------

DISEASE_NAMES = ["Impacted", "Caries", "Periapical Lesion", "Deep Caries"]
IOU_MATCH = 0.5           # operating point for precision/recall + label metrics
IOU_SWEEP = [round(0.5 + 0.05 * i, 2) for i in range(10)]  # for mAP50-95
DEFAULT_SWEEP = [0.20, 0.25, 0.30, 0.40, 0.50]


def load_ground_truth(path):
    """Parse the DENTEX COCO-style triple annotation file.

    Returns {file_name: [lesion, ...]} where each lesion carries the pixel
    bbox and the (quadrant, tooth, disease) triple, ids already converted to
    the pipeline's 1-based convention.
    """
    with open(path) as f:
        data = json.load(f)

    images = {img["id"]: img for img in data["images"]}
    # keep every image, including the lesion-free ones: predictions on those
    # panoramas are pure false positives and must be counted.
    per_image = defaultdict(list)
    for img in images.values():
        per_image[img["file_name"]]

    for ann in data["annotations"]:
        img = images[ann["image_id"]]
        x, y, w, h = ann["bbox"]
        per_image[img["file_name"]].append({
            "bbox": [x, y, x + w, y + h],
            "quadrant": ann["category_id_1"] + 1,
            "tooth": ann["category_id_2"] + 1,
            "disease_id": ann["category_id_3"],
            "disease": DISEASE_NAMES[ann["category_id_3"]],
        })
    return dict(per_image)


# ------------------------------------------------------------------
# Inference backends
# ------------------------------------------------------------------

def make_http_backend(api_url, timeout=120):
    """POST each image to a running ML service (the shipped /predict route)."""
    import urllib.request
    import urllib.error

    def run(image_path):
        boundary = uuid.uuid4().hex
        with open(image_path, "rb") as fh:
            payload = fh.read()
        name = os.path.basename(image_path)
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            api_url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    return run


def make_local_backend():
    """Import and call the frozen pipeline directly (needs torch et al.)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "production"))
    from inference_pipeline import run_dentex_pipeline  # noqa: WPS433

    def run(image_path):
        return run_dentex_pipeline(image_path)

    return run


def get_predictions(images_dir, gt, api_url, local, cache_path, limit=None):
    """Run the pipeline over every image, caching raw outputs to disk."""
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path) as fh:
            for line in fh:
                rec = json.loads(line)
                cache[rec["image"]] = rec

    run = make_local_backend() if local else make_http_backend(api_url)
    file_names = sorted(gt)
    if limit:
        file_names = file_names[:limit]

    with open(cache_path, "a") as cache_fh:
        for i, name in enumerate(file_names, 1):
            if name in cache:
                continue
            print(f"  [{i}/{len(file_names)}] {name}", flush=True)
            try:
                out = run(os.path.join(images_dir, name))
                rec = {"image": name, "ok": True, "result": out}
            except Exception as exc:  # noqa: BLE001 - report per-image failures
                rec = {"image": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            cache[name] = rec
            cache_fh.write(json.dumps(rec) + "\n")
            cache_fh.flush()
    return cache


# ------------------------------------------------------------------
# Geometry + matching
# ------------------------------------------------------------------

def iou(a, b):
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


def greedy_match(gt_boxes, pred_boxes, iou_thresh, pred_scores=None):
    """One-to-one match by descending IoU. Returns list of (gt_idx, pred_idx)."""
    pairs = []
    for gi, gb in enumerate(gt_boxes):
        for pi, pb in enumerate(pred_boxes):
            score = iou(gb, pb)
            if score >= iou_thresh:
                pairs.append((score, gi, pi))
    # highest IoU first; break ties deterministically by score then indices
    pairs.sort(key=lambda t: (-t[0], t[1], t[2]))

    used_g, used_p, matches = set(), set(), []
    for _, gi, pi in pairs:
        if gi in used_g or pi in used_p:
            continue
        used_g.add(gi)
        used_p.add(pi)
        matches.append((gi, pi))
    return matches


# ------------------------------------------------------------------
# Statistics
# ------------------------------------------------------------------

def wilson_ci(successes, total, z=1.96):
    """95% Wilson score interval for a proportion."""
    if total == 0:
        return (None, None, None)
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def fmt_pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def average_precision(scored_flags):
    """All-point interpolated AP (VOC 2010+ / COCO style).

    scored_flags: list of (confidence, is_true_positive) across the dataset,
    to be sorted by confidence descending.
    """
    if not scored_flags:
        return None
    ranked = sorted(scored_flags, key=lambda t: -t[0])
    n_pos = sum(1 for _, tp in ranked if tp)
    if n_pos == 0:
        return None

    tp_cum = fp_cum = 0
    precisions, recalls = [], []
    for _, tp in ranked:
        if tp:
            tp_cum += 1
        else:
            fp_cum += 1
        precisions.append(tp_cum / (tp_cum + fp_cum))
        recalls.append(tp_cum / n_pos)

    # monotone precision envelope, integrated over recall
    ap = 0.0
    prev_r = 0.0
    for i in range(len(ranked) - 1, -1, -1):
        r, p = recalls[i], precisions[i]
        if r > prev_r:
            ap += (r - prev_r) * p
            prev_r = r
    return ap


# ------------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------------

def evaluate(cache, gt, thresholds=(IOU_MATCH,), sweep=DEFAULT_SWEEP):
    """Compute detection, label and quadrant metrics from cached outputs."""
    # --- raw prediction filtering helpers -------------------------------
    def detections_at(rec, conf):
        return [d for d in rec["result"].get("detections", [])
                if d.get("disease_confidence", 0) >= conf]

    failed = sorted(name for name, rec in cache.items() if not rec["ok"])
    scored_images = sorted(name for name, rec in cache.items()
                           if rec["ok"] and name in gt)

    # ---------------------------------------------------------------
    # 1. Detection metrics at the primary operating point (IoU 0.5,
    #    pipeline's baked-in conf=0.20), per disease class + micro.
    # ---------------------------------------------------------------
    per_class_flags = defaultdict(list)     # class -> [(conf, is_tp)]
    per_class_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    micro = {"tp": 0, "fp": 0, "fn": 0}

    # label + quadrant metrics use class-agnostic matching (any label)
    label_stats = {"disease": {"ok": 0, "n": 0}, "tooth": {"ok": 0, "n": 0},
                   "quadrant": {"ok": 0, "n": 0}, "joint": {"ok": 0, "n": 0}}
    disease_confusion = defaultdict(lambda: defaultdict(int))
    quadrant_confusion = defaultdict(lambda: defaultdict(int))
    per_quadrant = defaultdict(lambda: {"tooth": [0, 0], "joint": [0, 0]})

    # AP across IoU thresholds for mAP50-95
    ap_flags = {t: defaultdict(list) for t in IOU_SWEEP}

    # threshold sweep (raise above the pipeline's conf=0.20)
    sweep_stats = {c: {"tp": 0, "fp": 0, "fn": 0, "disease_ok": 0, "disease_n": 0}
                   for c in sweep}

    for name in scored_images:
        rec = cache[name]
        gts = gt[name]
        preds = detections_at(rec, 0.0)  # all detections (conf >= 0.20)
        gt_boxes = [g["bbox"] for g in gts]
        pred_boxes = [p["box"] for p in preds]

        # --- class-aware matching per disease class (detection quality) --
        for cid, cname in enumerate(DISEASE_NAMES):
            g_idx = [i for i, g in enumerate(gts) if g["disease_id"] == cid]
            p_idx = [i for i, p in enumerate(preds) if p["disease_id"] == cid]
            matches = greedy_match([gt_boxes[i] for i in g_idx],
                                   [pred_boxes[i] for i in p_idx], IOU_MATCH)
            tp, fp = len(matches), len(p_idx) - len(matches)
            fn = len(g_idx) - len(matches)
            per_class_counts[cname]["tp"] += tp
            per_class_counts[cname]["fp"] += fp
            per_class_counts[cname]["fn"] += fn
            for gi, pi in matches:
                per_class_flags[cname].append((preds[pi]["disease_confidence"], True))
            for pi in range(len(p_idx)):
                if not any(pi == m[1] for m in matches):
                    per_class_flags[cname].append((preds[p_idx[pi]]["disease_confidence"], False))
            micro["tp"] += tp
            micro["fp"] += fp
            micro["fn"] += fn

        # --- mAP across IoU sweep ---------------------------------------
        for t in IOU_SWEEP:
            for cid, cname in enumerate(DISEASE_NAMES):
                g_idx = [i for i, g in enumerate(gts) if g["disease_id"] == cid]
                p_idx = [i for i, p in enumerate(preds) if p["disease_id"] == cid]
                matches = greedy_match([gt_boxes[i] for i in g_idx],
                                       [pred_boxes[i] for i in p_idx], t)
                matched_p = {pi for _, pi in matches}
                for gi, pi in matches:
                    ap_flags[t][cname].append((preds[p_idx[pi]]["disease_confidence"], True))
                for pi in range(len(p_idx)):
                    if pi not in matched_p:
                        ap_flags[t][cname].append((preds[p_idx[pi]]["disease_confidence"], False))

        # --- class-agnostic matching (label / quadrant correctness) -----
        matches = greedy_match(gt_boxes, pred_boxes, IOU_MATCH)
        for gi, pi in matches:
            g, p = gts[gi], preds[pi]
            label_stats["disease"]["n"] += 1
            label_stats["tooth"]["n"] += 1
            label_stats["quadrant"]["n"] += 1
            label_stats["joint"]["n"] += 1
            d_ok = g["disease_id"] == p["disease_id"]
            t_ok = g["tooth"] == p["tooth_id"]
            q_ok = g["quadrant"] == p["quadrant"]
            label_stats["disease"]["ok"] += d_ok
            label_stats["tooth"]["ok"] += t_ok
            label_stats["quadrant"]["ok"] += q_ok
            label_stats["joint"]["ok"] += (d_ok and t_ok)
            disease_confusion[g["disease"]][p["disease"]] += 1
            quadrant_confusion[g["quadrant"]][p["quadrant"]] += 1
            bucket = per_quadrant[g["quadrant"]]
            bucket["tooth"][1] += 1
            bucket["tooth"][0] += t_ok
            bucket["joint"][1] += 1
            bucket["joint"][0] += (d_ok and t_ok)

        # --- threshold sweep (conf above 0.20 = pure filtering) ---------
        for c in sweep:
            kept = detections_at(rec, c)
            kp = [d["box"] for d in kept]
            # class-aware detection counts
            tp = fp = 0
            matched_g = set()
            for cid in range(len(DISEASE_NAMES)):
                g_idx = [i for i, g in enumerate(gts) if g["disease_id"] == cid]
                p_idx = [i for i, d in enumerate(kept) if d["disease_id"] == cid]
                m = greedy_match([gt_boxes[i] for i in g_idx],
                                 [kp[i] for i in p_idx], IOU_MATCH)
                tp += len(m)
                fp += len(p_idx) - len(m)
                matched_g |= {g_idx[gi] for gi, _ in m}
            sweep_stats[c]["tp"] += tp
            sweep_stats[c]["fp"] += fp
            sweep_stats[c]["fn"] += len(gts) - len(matched_g)
            # disease accuracy on class-agnostic matches
            for gi, pi in greedy_match(gt_boxes, kp, IOU_MATCH):
                sweep_stats[c]["disease_n"] += 1
                sweep_stats[c]["disease_ok"] += gts[gi]["disease_id"] == kept[pi]["disease_id"]

    # ---------------------------------------------------------------
    # 2. Assemble the report
    # ---------------------------------------------------------------
    def prf(counts):
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        p, pl, ph = wilson_ci(tp, tp + fp)
        r, rl, rh = wilson_ci(tp, tp + fn)
        f1 = (2 * p * r / (p + r)) if (p and r) else (0.0 if (tp + fp + fn) else None)
        return {"precision": p, "precision_ci": [pl, ph],
                "recall": r, "recall_ci": [rl, rh], "f1": f1,
                "tp": tp, "fp": fp, "fn": fn}

    results = {
        "dataset": {
            "images_total": len(gt),
            "images_scored": len(scored_images),
            "images_failed": len(failed),
            "failed_images": failed,
            "gt_lesions": sum(len(gt[n]) for n in scored_images),
            "predictions": sum(len(detections_at(cache[n], 0.0)) for n in scored_images),
            "protocol": {
                "iou_match": IOU_MATCH,
                "disease_conf": 0.20,
                "matching": "greedy one-to-one by descending IoU",
                "ap": "all-point interpolated (COCO-style)",
            },
        },
        "detection_per_class": {c: prf(per_class_counts[c]) for c in DISEASE_NAMES},
        "detection_micro": prf(micro),
        "mAP50": None,
        "mAP50_95": None,
        "ap_per_class": {},
        "label_accuracy": {},
        "disease_confusion": {g: dict(v) for g, v in disease_confusion.items()},
        "quadrant_confusion": {str(g): {str(k): v for k, v in r.items()}
                               for g, r in quadrant_confusion.items()},
        "per_quadrant": {str(q): {k: (*wilson_ci(v[0], v[1]), v[1])
                                  for k, v in r.items()}
                         for q, r in per_quadrant.items()},
        "threshold_sweep": {},
    }

    ap50 = {}
    for cname in DISEASE_NAMES:
        ap50[cname] = average_precision(ap_flags[IOU_MATCH][cname])
    results["ap_per_class"] = {c: {"AP50": ap50[c]} for c in DISEASE_NAMES}
    scored = [v for v in ap50.values() if v is not None]
    results["mAP50"] = sum(scored) / len(scored) if scored else None

    aps = []
    for t in IOU_SWEEP:
        per = [average_precision(ap_flags[t][c]) for c in DISEASE_NAMES]
        per = [v for v in per if v is not None]
        if per:
            aps.append(sum(per) / len(per))
    results["mAP50_95"] = sum(aps) / len(aps) if aps else None

    for key, st in label_stats.items():
        results["label_accuracy"][key] = dict(zip(
            ("rate", "ci_low", "ci_high", "correct", "total"),
            (*wilson_ci(st["ok"], st["n"]), st["ok"], st["n"])))

    for c in sweep:
        st = sweep_stats[c]
        p, _, _ = wilson_ci(st["tp"], st["tp"] + st["fp"])
        r, _, _ = wilson_ci(st["tp"], st["tp"] + st["fn"])
        d, dl, dh = wilson_ci(st["disease_ok"], st["disease_n"])
        results["threshold_sweep"][str(c)] = {
            "precision": p, "recall": r, "f1": (2 * p * r / (p + r)) if (p and r) else None,
            "disease_acc": d, "disease_acc_ci": [dl, dh],
            "disease_n": st["disease_n"],
        }
    return results


# ------------------------------------------------------------------
# Report rendering
# ------------------------------------------------------------------

def render_report(results):
    ds = results["dataset"]
    out = [
        "# Shipped DENTEX pipeline — held-out evaluation",
        "",
        "Official DENTEX **validation** split (50 panoramas / 182 lesions), which the "
        "models never saw in training (all `model.train()` runs used `training_data/` "
        "only; see `MLv2/provenance/*/args.yaml`). Ground truth is the full "
        "quadrant + tooth + disease triple from `validation_triple.json`. "
        "Predictions are the frozen production pipeline "
        "(`production/inference_pipeline.py`, conf=0.20) served by the ML service.",
        "",
        f"- images scored: **{ds['images_scored']}/{ds['images_total']}**"
        + (f" (failed: {', '.join(ds['failed_images'])})" if ds["failed_images"] else ""),
        f"- ground-truth lesions: **{ds['gt_lesions']}** · model predictions: **{ds['predictions']}**",
        f"- matching: {ds['protocol']['matching']} at IoU ≥ {ds['protocol']['iou_match']}",
        "",
        "## 1. Detection quality (per disease class, IoU ≥ 0.5)",
        "",
        "| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 |",
        "|---|---|---|---|---|---|---|",
    ]
    for cname in DISEASE_NAMES:
        d = results["detection_per_class"][cname]
        gt_n, pred_n = d["tp"] + d["fn"], d["tp"] + d["fp"]
        p_ci = f"{fmt_pct(d['precision'])} [{fmt_pct(d['precision_ci'][0])}, {fmt_pct(d['precision_ci'][1])}]"
        r_ci = f"{fmt_pct(d['recall'])} [{fmt_pct(d['recall_ci'][0])}, {fmt_pct(d['recall_ci'][1])}]"
        ap = results["ap_per_class"][cname]["AP50"]
        out.append(f"| {cname} | {gt_n} | {pred_n} | {p_ci} | {r_ci} | "
                   f"{fmt_pct(d['f1'])} | {fmt_pct(ap)} |")
    m = results["detection_micro"]
    out += [
        f"| **micro avg** | {m['tp'] + m['fn']} | {m['tp'] + m['fp']} | "
        f"{fmt_pct(m['precision'])} [{fmt_pct(m['precision_ci'][0])}, {fmt_pct(m['precision_ci'][1])}] | "
        f"{fmt_pct(m['recall'])} [{fmt_pct(m['recall_ci'][0])}, {fmt_pct(m['recall_ci'][1])}] | "
        f"{fmt_pct(m['f1'])} | {fmt_pct(results['mAP50'])} |",
        "",
        f"**mAP@0.5 = {fmt_pct(results['mAP50'])} · mAP@0.5:0.95 = {fmt_pct(results['mAP50_95'])}**",
        "",
        "## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)",
        "",
        "This is the metric family of the original `final_evaluation.json` "
        "(disease / tooth / joint), now on a reproducible 182-lesion set with CIs.",
        "",
        "| metric | rate (95% CI) | correct / total |",
        "|---|---|---|",
    ]
    for key, title in (("disease", "disease label"),
                       ("tooth", "tooth number"),
                       ("quadrant", "quadrant"),
                       ("joint", "disease **and** tooth")):
        la = results["label_accuracy"][key]
        out.append(f"| {title} | **{fmt_pct(la['rate'])}** "
                   f"[{fmt_pct(la['ci_low'])}, {fmt_pct(la['ci_high'])}] | "
                   f"{la['correct']} / {la['total']} |")

    out += ["", "### Disease confusion matrix (rows = ground truth, cols = prediction)", "",
            "| GT \\ pred | " + " | ".join(DISEASE_NAMES) + " |", "|---|" + "---|" * len(DISEASE_NAMES)]
    for g in DISEASE_NAMES:
        row = results["disease_confusion"].get(g, {})
        out.append(f"| **{g}** | " + " | ".join(str(row.get(p, 0)) for p in DISEASE_NAMES) + " |")

    out += ["", "## 3. Tooth accuracy per quadrant", "",
            "| quadrant | tooth acc (95% CI) | joint (95% CI) | n |", "|---|---|---|---|"]
    for q in ("1", "2", "3", "4"):
        r = results["per_quadrant"].get(q, {})
        if not r:
            continue
        t, j = r["tooth"], r["joint"]
        out.append(f"| Q{q} | {fmt_pct(t[0])} [{fmt_pct(t[1])}, {fmt_pct(t[2])}] | "
                   f"{fmt_pct(j[0])} [{fmt_pct(j[1])}, {fmt_pct(j[2])}] | {t[3]} |")

    out += ["", "## 4. Confidence-threshold sweep (disease detector)", "",
            "The pipeline bakes in conf=0.20; higher thresholds can be applied by "
            "filtering returned detections (identical to raising the threshold). "
            "Values below 0.20 are unreachable without re-running the model.",
            "",
            "| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |",
            "|---|---|---|---|---|---|"]
    for c in DEFAULT_SWEEP:
        s = results["threshold_sweep"].get(str(c))
        if not s:
            continue
        ci = s["disease_acc_ci"]
        out.append(f"| {c:.2f} | {fmt_pct(s['precision'])} | {fmt_pct(s['recall'])} | "
                   f"{fmt_pct(s['f1'])} | {fmt_pct(s['disease_acc'])} [{fmt_pct(ci[0])}, {fmt_pct(ci[1])}] | "
                   f"{s['disease_n']} |")

    out += ["", "---", "",
            "Regenerate with `python dentex_week3/evaluate.py` (see its docstring). "
            "Confidence intervals are 95% Wilson score intervals."]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images-dir", required=True,
                    help="Directory with the DENTEX validation panoramas (val_*.png)")
    ap.add_argument("--gt", required=True,
                    help="validation_triple.json (COCO-style quadrant+tooth+disease GT)")
    ap.add_argument("--api", default="http://localhost:8001/predict",
                    help="Running ML service /predict endpoint (default: %(default)s)")
    ap.add_argument("--local", action="store_true",
                    help="Run the frozen pipeline in-process instead of via the ML service")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval"))
    ap.add_argument("--limit", type=int, default=None, help="Only evaluate the first N images (smoke test)")
    ap.add_argument("--fresh", action="store_true", help="Ignore the prediction cache and re-run inference")
    args = ap.parse_args()

    gt = load_ground_truth(args.gt)
    if not gt:
        sys.exit(f"No ground-truth lesions found in {args.gt}")

    os.makedirs(args.out_dir, exist_ok=True)
    cache_path = os.path.join(args.out_dir, "raw_predictions.jsonl")
    if args.fresh and os.path.exists(cache_path):
        os.remove(cache_path)

    print(f"Evaluating on {len(gt)} images ({sum(len(v) for v in gt.values())} lesions) "
          f"via {'local pipeline' if args.local else args.api}")
    cache = get_predictions(args.images_dir, gt, args.api, args.local, cache_path, args.limit)

    results = evaluate(cache, gt)

    stem = "evaluation_results"
    with open(os.path.join(args.out_dir, f"{stem}.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    with open(os.path.join(args.out_dir, "evaluation_report.md"), "w") as fh:
        fh.write(render_report(results))

    print()
    print(render_report(results))
    print(f"Written: {args.out_dir}/{stem}.json, {args.out_dir}/evaluation_report.md")


if __name__ == "__main__":
    main()
