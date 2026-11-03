"""Paired significance analysis: v1 vs v2 on the locked DENTEX benchmark.

The harness reports point estimates. With 50 images / 182 lesions those
estimates carry real uncertainty, so this script asks a stricter question:
*is the improvement distinguishable from noise?*

Both prediction files come from the same harness and the same ground truth, so
every lesion is a paired observation:

  * McNemar exact test on per-lesion correctness (detection, tooth, joint)
  * image-level paired bootstrap CI for mAP@0.5, recall and per-class AP

The bootstrap resamples the 50 panoramas (the unit that was actually sampled),
not individual lesions, so it respects within-image correlation.

Usage:
    python dentex_week3/paired_significance.py
    python dentex_week3/paired_significance.py --markdown > out.md
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from evaluate import (  # noqa: E402
    DISEASE_NAMES, IOU_MATCH, average_precision, greedy_match, load_ground_truth,
)

DEFAULT_GT = Path("/home/sayfeldin/Projects/dental-model-research"
                  "/data/downloads/validation_triple.json")


def load_cache(path):
    return {rec["image"]: rec
            for rec in map(json.loads, Path(path).read_text().splitlines())}


def per_image_stats(gt, cache):
    """Per-image structures needed for every metric."""
    stats = {}
    for name, gts in gt.items():
        rec = cache.get(name)
        preds = rec["result"].get("detections", []) if rec and rec["ok"] else []
        gt_boxes = [g["bbox"] for g in gts]
        pred_boxes = [p["box"] for p in preds]

        cls_flags = {}
        for cid, cname in enumerate(DISEASE_NAMES):
            g_idx = [i for i, g in enumerate(gts) if g["disease_id"] == cid]
            p_idx = [i for i, p in enumerate(preds) if p["disease_id"] == cid]
            matches = greedy_match([gt_boxes[i] for i in g_idx],
                                   [pred_boxes[i] for i in p_idx], IOU_MATCH)
            matched = {pi for _, pi in matches}
            flags = [(preds[p_idx[pi]]["disease_confidence"], True) for _, pi in matches]
            flags += [(preds[p_idx[pi]]["disease_confidence"], False)
                      for pi in range(len(p_idx)) if pi not in matched]
            cls_flags[cname] = flags

        matches = greedy_match(gt_boxes, pred_boxes, IOU_MATCH)
        det_ok = [False] * len(gts)
        tooth_ok = [False] * len(gts)
        joint_ok = [False] * len(gts)
        for gi, pi in matches:
            g, p = gts[gi], preds[pi]
            det_ok[gi] = True
            tooth_ok[gi] = g["tooth"] == p["tooth_id"]
            joint_ok[gi] = tooth_ok[gi] and g["disease_id"] == p["disease_id"]

        stats[name] = {"cls_flags": cls_flags, "n_gt": len(gts),
                       "det_ok": det_ok, "tooth_ok": tooth_ok, "joint_ok": joint_ok}
    return stats


def aggregate(stats, subset):
    """Headline metrics over a set of image names.

    tooth/joint here are *end-to-end*: every ground-truth lesion counts in the
    denominator, so an undetected lesion is a failure. The harness instead
    conditions on detected lesions; both are reported.
    """
    flags = {c: [] for c in DISEASE_NAMES}
    tp = fn = 0
    tooth = [0, 0]
    joint = [0, 0]
    for name in subset:
        st = stats[name]
        for c in DISEASE_NAMES:
            flags[c].extend(st["cls_flags"][c])
        tp += sum(st["det_ok"])
        fn += st["n_gt"] - sum(st["det_ok"])
        tooth[0] += sum(st["tooth_ok"])
        tooth[1] += st["n_gt"]
        joint[0] += sum(st["joint_ok"])
        joint[1] += st["n_gt"]

    aps = [a for a in (average_precision(flags[c]) for c in DISEASE_NAMES) if a is not None]
    return {
        "mAP50": sum(aps) / len(aps) if aps else None,
        "recall": tp / (tp + fn) if (tp + fn) else None,
        "tooth_e2e": tooth[0] / tooth[1] if tooth[1] else None,
        "joint_e2e": joint[0] / joint[1] if joint[1] else None,
    }


def mcnemar(a, b):
    """Exact McNemar. a, b are aligned correctness lists. Returns (b01, b10, p)."""
    b01 = sum(1 for x, y in zip(a, b) if not x and y)
    b10 = sum(1 for x, y in zip(a, b) if x and not y)
    n = b01 + b10
    if n == 0:
        return b01, b10, 1.0
    k = min(b01, b10)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return b01, b10, min(1.0, p)


def bootstrap(s1, s2, names, n_boot=2000, seed=42):
    rng = random.Random(seed)
    deltas = defaultdict(list)
    for _ in range(n_boot):
        sample = [rng.choice(names) for _ in names]
        a, b = aggregate(s1, sample), aggregate(s2, sample)
        for k in a:
            if a[k] is not None and b[k] is not None:
                deltas[k].append(b[k] - a[k])
    out = {}
    for k, vals in deltas.items():
        vals.sort()
        out[k] = (vals[int(0.025 * len(vals))],
                  vals[int(0.975 * len(vals)) - 1],
                  sum(1 for v in vals if v > 0) / len(vals))
    return out


def per_class_bootstrap(f1, f2, names, n_boot=2000, seed=42):
    rng = random.Random(seed)

    def ap(stats, subset, c):
        return average_precision([x for n in subset for x in stats[n][c]])

    out = {}
    for c in DISEASE_NAMES:
        base1, base2 = ap(f1, names, c), ap(f2, names, c)
        d = []
        for _ in range(n_boot):
            s = [rng.choice(names) for _ in names]
            a, b = ap(f1, s, c), ap(f2, s, c)
            if a is not None and b is not None:
                d.append(b - a)
        d.sort()
        out[c] = (base1, base2, d[int(0.025 * len(d))],
                  d[int(0.975 * len(d)) - 1],
                  sum(1 for v in d if v > 0) / len(d))
    return out


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--gt", default=str(DEFAULT_GT))
    ap_.add_argument("--v1", default=str(HERE / "eval/raw_predictions.jsonl"))
    ap_.add_argument("--v2", default=str(HERE / "eval/raw_predictions_v2.jsonl"))
    ap_.add_argument("--markdown", action="store_true")
    ap_.add_argument("--boot", type=int, default=2000)
    args = ap_.parse_args()

    gt = load_ground_truth(args.gt)
    names = sorted(gt)
    s1 = per_image_stats(gt, load_cache(args.v1))
    s2 = per_image_stats(gt, load_cache(args.v2))

    a1, a2 = aggregate(s1, names), aggregate(s2, names)
    boot = bootstrap(s1, s2, names, args.boot)
    per_class = per_class_bootstrap(
        {n: s1[n]["cls_flags"] for n in names},
        {n: s2[n]["cls_flags"] for n in names},
        names, args.boot)

    labels = {
        "mAP50": "mAP@0.5",
        "recall": "recall",
        "tooth_e2e": "tooth (end-to-end)",
        "joint_e2e": "joint (end-to-end)",
    }
    tests = []
    for key, label in (("det_ok", "detection"), ("tooth_ok", "tooth"), ("joint_ok", "joint")):
        a = [x for n in names for x in s1[n][key]]
        b = [x for n in names for x in s2[n][key]]
        b01, b10, p = mcnemar(a, b)
        tests.append((label, b01, b10, p))

    if args.markdown:
        print("## Paired significance: v1 vs v2\n")
        print("| metric | v1 | v2 | delta | 95% CI (paired bootstrap) | P(v2 > v1) |")
        print("|---|---|---|---|---|---|")
        for k, label in labels.items():
            lo, hi, share = boot[k]
            print(f"| {label} | {a1[k]:.1%} | {a2[k]:.1%} | {a2[k] - a1[k]:+.1%} "
                  f"| [{lo:+.1%}, {hi:+.1%}] | {share:.3f} |")
        print("\n### McNemar exact test (per-lesion, paired)\n")
        print("| metric | v2-only correct | v1-only correct | p (two-sided) |")
        print("|---|---|---|---|")
        for label, b01, b10, p in tests:
            print(f"| {label} | {b01} | {b10} | {p:.2e} |")
        print("\n### Per-class AP@0.5\n")
        print("| class | v1 | v2 | delta | 95% CI | P(v2 > v1) |")
        print("|---|---|---|---|---|---|")
        for c, (b1, b2, lo, hi, share) in per_class.items():
            print(f"| {c} | {b1:.1%} | {b2:.1%} | {b2 - b1:+.1%} "
                  f"| [{lo:+.1%}, {hi:+.1%}] | {share:.3f} |")
        print(f"\nBootstrap: {args.boot} replicates, images resampled with replacement.")
        return

    print(f"images: {len(names)}  lesions: {sum(s['n_gt'] for s in s1.values())}")
    for k, label in labels.items():
        lo, hi, share = boot[k]
        print(f"{label:20s} {a1[k]:6.1%} -> {a2[k]:6.1%}  "
              f"delta {a2[k] - a1[k]:+6.1%}  95% CI [{lo:+.1%}, {hi:+.1%}]  P={share:.3f}")
    for label, b01, b10, p in tests:
        print(f"McNemar {label:10s} v2-only {b01:3d}  v1-only {b10:3d}  p={p:.2e}")
    for c, (b1, b2, lo, hi, share) in per_class.items():
        print(f"{c:20s} {b1:6.1%} -> {b2:6.1%}  "
              f"delta {b2 - b1:+6.1%}  95% CI [{lo:+.1%}, {hi:+.1%}]  P={share:.3f}")


if __name__ == "__main__":
    main()
