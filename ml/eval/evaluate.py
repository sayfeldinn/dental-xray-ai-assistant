#!/usr/bin/env python3
"""Held-out evaluation of the shipped DENTEX pipeline on the official
DENTEX validation set (50 panoramas, 182 annotated lesions with the full
quadrant + tooth + disease ground-truth triple).

Why this exists
---------------
``eval/final_evaluation.json`` records disease 97.54% / tooth 76.23% /
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
  Lesion, Deep Caries) match ``pipeline/pipeline_config.json``.
"""

import argparse
import json
import os
import sys
import uuid
from collections import defaultdict

# The evaluator is run both as a script (`python ml/eval/evaluate.py`) and
# imported by ml/eval/significance.py, so make its own directory importable
# before pulling in the shared metrics module.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from metrics import (  # noqa: E402
    average_precision,
    fmt_pct,
    greedy_match,
    macro_mean,
    prf,
    wilson_ci,
)

# ------------------------------------------------------------------
# Ground truth
# ------------------------------------------------------------------

DISEASE_NAMES = ["Impacted", "Caries", "Periapical Lesion", "Deep Caries"]
IOU_MATCH = 0.5  # operating point for precision/recall + label metrics
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
        per_image[img["file_name"]].append(
            {
                "bbox": [x, y, x + w, y + h],
                "quadrant": ann["category_id_1"] + 1,
                "tooth": ann["category_id_2"] + 1,
                "disease_id": ann["category_id_3"],
                "disease": DISEASE_NAMES[ann["category_id_3"]],
            }
        )
    return dict(per_image)


# ------------------------------------------------------------------
# Inference backends
# ------------------------------------------------------------------


def make_http_backend(api_url, timeout=120):
    """POST each image to a running ML service (the shipped /predict route)."""
    import urllib.error
    import urllib.request

    def run(image_path):
        boundary = uuid.uuid4().hex
        with open(image_path, "rb") as fh:
            payload = fh.read()
        name = os.path.basename(image_path)
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + payload
            + f"\r\n--{boundary}--\r\n".encode()
        )

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
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "pipeline")
    )
    from inference import run_dentex_pipeline  # noqa: WPS433

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
# `iou` and `greedy_match` are imported from metrics.py; the duplicate copies
# that used to live here shadowed them and have been removed.


# ------------------------------------------------------------------
# Detection / label statistics
# ------------------------------------------------------------------
# wilson_ci, fmt_pct, average_precision, prf and macro_mean also live in
# metrics.py. They are re-exported from this module so
# `from evaluate import average_precision, greedy_match` keeps working for the
# significance and research scripts.


def detections_at(rec, conf):
    """Detections in a cached result at or above ``conf``.

    The pipeline bakes in conf=0.20, so raising the threshold is pure
    post-filtering and never re-runs the model.
    """
    return [
        d for d in rec["result"].get("detections", []) if d.get("disease_confidence", 0) >= conf
    ]


def collect_stats(cache, gt, sweep):
    """Single pass over the scored images, gathering every raw counter.

    Returns a dict of accumulators (counts, per-class flags, confusion
    matrices, per-quadrant tallies, sweep tallies) that the ``*_metrics``
    builders below turn into the report. One pass keeps the evaluator's
    runtime identical to the original implementation.
    """
    failed = sorted(name for name, rec in cache.items() if not rec["ok"])
    scored_images = sorted(name for name, rec in cache.items() if rec["ok"] and name in gt)

    per_class_flags = defaultdict(list)  # class -> [(conf, is_tp)]
    per_class_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    micro = {"tp": 0, "fp": 0, "fn": 0}

    # label + quadrant metrics use class-agnostic matching (any label)
    label_stats = {
        "disease": {"ok": 0, "n": 0},
        "tooth": {"ok": 0, "n": 0},
        "quadrant": {"ok": 0, "n": 0},
        "joint": {"ok": 0, "n": 0},
    }
    disease_confusion = defaultdict(lambda: defaultdict(int))
    quadrant_confusion = defaultdict(lambda: defaultdict(int))
    per_quadrant = defaultdict(lambda: {"tooth": [0, 0], "joint": [0, 0]})

    # AP across IoU thresholds for mAP50-95
    ap_flags = {t: defaultdict(list) for t in IOU_SWEEP}

    # threshold sweep (raise above the pipeline's conf=0.20)
    sweep_stats = {c: {"tp": 0, "fp": 0, "fn": 0, "disease_ok": 0, "disease_n": 0} for c in sweep}

    gt_per_class = defaultdict(int)
    for name in scored_images:
        for g in gt[name]:
            gt_per_class[DISEASE_NAMES[g["disease_id"]]] += 1

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
            matches = greedy_match(
                [gt_boxes[i] for i in g_idx], [pred_boxes[i] for i in p_idx], IOU_MATCH
            )
            tp, fp = len(matches), len(p_idx) - len(matches)
            fn = len(g_idx) - len(matches)
            per_class_counts[cname]["tp"] += tp
            per_class_counts[cname]["fp"] += fp
            per_class_counts[cname]["fn"] += fn
            for _, pi in matches:
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
                matches = greedy_match(
                    [gt_boxes[i] for i in g_idx], [pred_boxes[i] for i in p_idx], t
                )
                matched_p = {pi for _, pi in matches}
                for _, pi in matches:
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
            label_stats["joint"]["ok"] += d_ok and t_ok
            disease_confusion[g["disease"]][p["disease"]] += 1
            quadrant_confusion[g["quadrant"]][p["quadrant"]] += 1
            bucket = per_quadrant[g["quadrant"]]
            bucket["tooth"][1] += 1
            bucket["tooth"][0] += t_ok
            bucket["joint"][1] += 1
            bucket["joint"][0] += d_ok and t_ok

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
                m = greedy_match([gt_boxes[i] for i in g_idx], [kp[i] for i in p_idx], IOU_MATCH)
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

    return {
        "failed": failed,
        "scored_images": scored_images,
        "per_class_flags": per_class_flags,
        "per_class_counts": per_class_counts,
        "micro": micro,
        "label_stats": label_stats,
        "disease_confusion": disease_confusion,
        "quadrant_confusion": quadrant_confusion,
        "per_quadrant": per_quadrant,
        "ap_flags": ap_flags,
        "sweep_stats": sweep_stats,
        "gt_per_class": gt_per_class,
    }


def detection_metrics(stats):
    """Per-class / micro P-R-F1 plus mAP@0.5, mAP@0.5:0.95, mAP@0.75 and AR."""
    per_class_counts = stats["per_class_counts"]
    ap_flags = stats["ap_flags"]

    ap50 = {c: average_precision(ap_flags[IOU_MATCH][c]) for c in DISEASE_NAMES}
    ap_per_class = {c: {"AP50": ap50[c]} for c in DISEASE_NAMES}
    mAP50 = macro_mean(ap50.values())

    per_threshold = []
    for t in IOU_SWEEP:
        per = [average_precision(ap_flags[t][c]) for c in DISEASE_NAMES]
        mean = macro_mean(per)
        if mean is not None:
            per_threshold.append(mean)
    mAP50_95 = macro_mean(per_threshold)

    per_class_ap75 = {c: average_precision(ap_flags[0.75][c]) for c in DISEASE_NAMES}
    for c in DISEASE_NAMES:
        ap_per_class[c]["AP75"] = per_class_ap75[c]
    mAP75 = macro_mean(per_class_ap75.values())

    # AR@0.5:0.95 = mean per-class recall across the ten IoU thresholds
    ar_per_class = {}
    for c in DISEASE_NAMES:
        n_gt = stats["gt_per_class"][c]
        recalls = [
            sum(1 for _, is_tp in ap_flags[t][c] if is_tp) / n_gt for t in IOU_SWEEP if n_gt
        ]
        ar_per_class[c] = macro_mean(recalls) if n_gt else None
    AR50_95 = macro_mean(ar_per_class.values())

    return {
        "per_class": {c: prf(per_class_counts[c]) for c in DISEASE_NAMES},
        "micro": prf(stats["micro"]),
        "mAP50": mAP50,
        "mAP50_95": mAP50_95,
        "ap_per_class": ap_per_class,
        "mAP75": mAP75,
        "ar_per_class": ar_per_class,
        "AR50_95": AR50_95,
    }


def label_metrics(stats):
    """Disease / tooth / quadrant / joint accuracy and the confusion matrices."""
    accuracy = {}
    for key, st in stats["label_stats"].items():
        accuracy[key] = dict(
            zip(
                ("rate", "ci_low", "ci_high", "correct", "total"),
                (*wilson_ci(st["ok"], st["n"]), st["ok"], st["n"]),
                strict=True,
            )
        )

    return {
        "accuracy": accuracy,
        "disease_confusion": {g: dict(v) for g, v in stats["disease_confusion"].items()},
        "quadrant_confusion": {
            str(g): {str(k): v for k, v in r.items()}
            for g, r in stats["quadrant_confusion"].items()
        },
        "per_quadrant": {
            str(q): {k: (*wilson_ci(v[0], v[1]), v[1]) for k, v in r.items()}
            for q, r in stats["per_quadrant"].items()
        },
    }


def sweep_metrics(stats, sweep):
    """Precision / recall / F1 and disease accuracy at each threshold in ``sweep``."""
    out = {}
    for c in sweep:
        st = stats["sweep_stats"][c]
        p, _, _ = wilson_ci(st["tp"], st["tp"] + st["fp"])
        r, _, _ = wilson_ci(st["tp"], st["tp"] + st["fn"])
        d, dl, dh = wilson_ci(st["disease_ok"], st["disease_n"])
        out[str(c)] = {
            "precision": p,
            "recall": r,
            "f1": (2 * p * r / (p + r)) if (p and r) else None,
            "disease_acc": d,
            "disease_acc_ci": [dl, dh],
            "disease_n": st["disease_n"],
        }
    return out


# ------------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------------


def evaluate(cache, gt, sweep=DEFAULT_SWEEP):
    """Compute detection, label and quadrant metrics from cached predictions.

    Three stages, each independently testable:
      1. ``collect_stats``   -- one pass over the scored images
      2. ``*_metrics``       -- turn the accumulators into the report sections
      3. assemble            -- emit the dict the report renderer expects
    """
    stats = collect_stats(cache, gt, sweep)
    detection = detection_metrics(stats)
    labels = label_metrics(stats)
    sweep_results = sweep_metrics(stats, sweep)

    scored_images = stats["scored_images"]
    return {
        "dataset": {
            "images_total": len(gt),
            "images_scored": len(scored_images),
            "images_failed": len(stats["failed"]),
            "failed_images": stats["failed"],
            "gt_lesions": sum(len(gt[n]) for n in scored_images),
            "predictions": sum(len(detections_at(cache[n], 0.0)) for n in scored_images),
            "protocol": {
                "iou_match": IOU_MATCH,
                "disease_conf": 0.20,
                "matching": "greedy one-to-one by descending IoU",
                "ap": "all-point interpolated (COCO-style)",
            },
        },
        "detection_per_class": detection["per_class"],
        "detection_micro": detection["micro"],
        "mAP50": detection["mAP50"],
        "mAP50_95": detection["mAP50_95"],
        "ap_per_class": detection["ap_per_class"],
        "label_accuracy": labels["accuracy"],
        "disease_confusion": labels["disease_confusion"],
        "quadrant_confusion": labels["quadrant_confusion"],
        "per_quadrant": labels["per_quadrant"],
        "threshold_sweep": sweep_results,
        "mAP75": detection["mAP75"],
        "ar_per_class": detection["ar_per_class"],
        "AR50_95": detection["AR50_95"],
    }


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
        "only; see `docs/evidence/mlv2/provenance/*/args.yaml`). Ground truth is the full "
        "quadrant + tooth + disease triple from `validation_triple.json`. "
        "Predictions are the frozen production pipeline "
        "(`pipeline/inference.py`, conf=0.20) served by the ML service.",
        "",
        f"- images scored: **{ds['images_scored']}/{ds['images_total']}**"
        + (f" (failed: {', '.join(ds['failed_images'])})" if ds["failed_images"] else ""),
        f"- ground-truth lesions: **{ds['gt_lesions']}** · model predictions: **{ds['predictions']}**",
        f"- matching: {ds['protocol']['matching']} at IoU ≥ {ds['protocol']['iou_match']}",
        "",
        "## 1. Detection quality (per disease class, IoU ≥ 0.5)",
        "",
        "| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 | AP@0.75 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cname in DISEASE_NAMES:
        d = results["detection_per_class"][cname]
        gt_n, pred_n = d["tp"] + d["fn"], d["tp"] + d["fp"]
        p_ci = f"{fmt_pct(d['precision'])} [{fmt_pct(d['precision_ci'][0])}, {fmt_pct(d['precision_ci'][1])}]"
        r_ci = (
            f"{fmt_pct(d['recall'])} [{fmt_pct(d['recall_ci'][0])}, {fmt_pct(d['recall_ci'][1])}]"
        )
        ap = results["ap_per_class"][cname]["AP50"]
        ap75 = results["ap_per_class"][cname]["AP75"]
        out.append(
            f"| {cname} | {gt_n} | {pred_n} | {p_ci} | {r_ci} | "
            f"{fmt_pct(d['f1'])} | {fmt_pct(ap)} | {fmt_pct(ap75)} |"
        )
    m = results["detection_micro"]
    out += [
        f"| **micro avg** | {m['tp'] + m['fn']} | {m['tp'] + m['fp']} | "
        f"{fmt_pct(m['precision'])} [{fmt_pct(m['precision_ci'][0])}, {fmt_pct(m['precision_ci'][1])}] | "
        f"{fmt_pct(m['recall'])} [{fmt_pct(m['recall_ci'][0])}, {fmt_pct(m['recall_ci'][1])}] | "
        f"{fmt_pct(m['f1'])} | {fmt_pct(results['mAP50'])} | {fmt_pct(results['mAP75'])} |",
        "",
        f"**mAP@0.5 = {fmt_pct(results['mAP50'])} · mAP@0.5:0.95 = {fmt_pct(results['mAP50_95'])} · "
        f"mAP@0.75 = {fmt_pct(results['mAP75'])} · AR@0.5:0.95 = {fmt_pct(results['AR50_95'])}**",
        "",
        "`AP@0.75` and `AR@0.5:0.95` are macro averages over the four disease classes; "
        "AR is the mean per-class recall across the ten IoU thresholds (COCO-style), "
        "computed on the detections the pipeline returns at conf ≥ 0.20.",
        "",
        "## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)",
        "",
        "This is the metric family of the original `final_evaluation.json` "
        "(disease / tooth / joint), now on a reproducible 182-lesion set with CIs.",
        "",
        "| metric | rate (95% CI) | correct / total |",
        "|---|---|---|",
    ]
    for key, title in (
        ("disease", "disease label"),
        ("tooth", "tooth number"),
        ("quadrant", "quadrant"),
        ("joint", "disease **and** tooth"),
    ):
        la = results["label_accuracy"][key]
        out.append(
            f"| {title} | **{fmt_pct(la['rate'])}** "
            f"[{fmt_pct(la['ci_low'])}, {fmt_pct(la['ci_high'])}] | "
            f"{la['correct']} / {la['total']} |"
        )

    out += [
        "",
        "### Disease confusion matrix (rows = ground truth, cols = prediction)",
        "",
        "| GT \\ pred | " + " | ".join(DISEASE_NAMES) + " |",
        "|---|" + "---|" * len(DISEASE_NAMES),
    ]
    for g in DISEASE_NAMES:
        row = results["disease_confusion"].get(g, {})
        out.append(f"| **{g}** | " + " | ".join(str(row.get(p, 0)) for p in DISEASE_NAMES) + " |")

    out += [
        "",
        "## 3. Tooth accuracy per quadrant",
        "",
        "| quadrant | tooth acc (95% CI) | joint (95% CI) | n |",
        "|---|---|---|---|",
    ]
    for q in ("1", "2", "3", "4"):
        r = results["per_quadrant"].get(q, {})
        if not r:
            continue
        t, j = r["tooth"], r["joint"]
        out.append(
            f"| Q{q} | {fmt_pct(t[0])} [{fmt_pct(t[1])}, {fmt_pct(t[2])}] | "
            f"{fmt_pct(j[0])} [{fmt_pct(j[1])}, {fmt_pct(j[2])}] | {t[3]} |"
        )

    out += [
        "",
        "## 4. Confidence-threshold sweep (disease detector)",
        "",
        "The pipeline bakes in conf=0.20; higher thresholds can be applied by "
        "filtering returned detections (identical to raising the threshold). "
        "Values below 0.20 are unreachable without re-running the model.",
        "",
        "| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |",
        "|---|---|---|---|---|---|",
    ]
    for c in DEFAULT_SWEEP:
        s = results["threshold_sweep"].get(str(c))
        if not s:
            continue
        ci = s["disease_acc_ci"]
        out.append(
            f"| {c:.2f} | {fmt_pct(s['precision'])} | {fmt_pct(s['recall'])} | "
            f"{fmt_pct(s['f1'])} | {fmt_pct(s['disease_acc'])} [{fmt_pct(ci[0])}, {fmt_pct(ci[1])}] | "
            f"{s['disease_n']} |"
        )

    out += [
        "",
        "---",
        "",
        "Regenerate with `python ml/eval/evaluate.py` (see its docstring). "
        "Confidence intervals are 95% Wilson score intervals.",
    ]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--images-dir",
        required=True,
        help="Directory with the DENTEX validation panoramas (val_*.png)",
    )
    ap.add_argument(
        "--gt", required=True, help="validation_triple.json (COCO-style quadrant+tooth+disease GT)"
    )
    ap.add_argument(
        "--api",
        default="http://localhost:8001/predict",
        help="Running ML service /predict endpoint (default: %(default)s)",
    )
    ap.add_argument(
        "--local",
        action="store_true",
        help="Run the frozen pipeline in-process instead of via the ML service",
    )
    ap.add_argument(
        "--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval")
    )
    ap.add_argument(
        "--limit", type=int, default=None, help="Only evaluate the first N images (smoke test)"
    )
    ap.add_argument(
        "--fresh", action="store_true", help="Ignore the prediction cache and re-run inference"
    )
    args = ap.parse_args()

    gt = load_ground_truth(args.gt)
    if not gt:
        sys.exit(f"No ground-truth lesions found in {args.gt}")

    os.makedirs(args.out_dir, exist_ok=True)
    cache_path = os.path.join(args.out_dir, "raw_predictions.jsonl")
    if args.fresh and os.path.exists(cache_path):
        os.remove(cache_path)

    print(
        f"Evaluating on {len(gt)} images ({sum(len(v) for v in gt.values())} lesions) "
        f"via {'local pipeline' if args.local else args.api}"
    )
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
