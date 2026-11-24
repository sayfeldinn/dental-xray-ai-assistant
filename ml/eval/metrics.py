"""Detection metrics shared by the evaluator and the research scripts.

Pure functions only — no I/O, no torch, no project imports — so this module can
be unit-tested in isolation and reused from any of the ``ml/eval`` and
``ml/research`` entry points.

The shipped inference pipeline (``ml/pipeline/inference.py``) deliberately keeps
its own private ``_iou``: the Docker image copies only ``pipeline/`` and
``weights/``, so the frozen pipeline must not depend on anything under ``eval/``.
The box maths here and there are the same formula; the duplication is a
deployment-boundary decision, not an oversight.
"""

import math


def iou(a, b):
    """Intersection-over-union of two ``(x1, y1, x2, y2)`` boxes."""
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
    """One-to-one match by descending IoU. Returns a list of ``(gt_idx, pred_idx)``.

    ``pred_scores`` is accepted for interface compatibility with callers that
    rank by confidence; the current matching is IoU-only and ties break
    deterministically on the box indices.
    """
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


def wilson_ci(successes, total, z=1.96):
    """95% Wilson score interval for a proportion. Returns ``(p, low, high)``."""
    if total == 0:
        return (None, None, None)
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def fmt_pct(x):
    """Format a 0..1 rate as ``"54.2%"``; ``None`` renders as ``"-"``."""
    return "-" if x is None else f"{100 * x:.1f}%"


def average_precision(scored_flags):
    """All-point interpolated AP (VOC 2010+ / COCO style).

    ``scored_flags`` is a list of ``(confidence, is_true_positive)`` across the
    dataset; it is sorted by confidence descending internally.
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


def prf(counts):
    """Precision / recall / F1 with Wilson CIs from a ``{"tp", "fp", "fn"}`` dict."""
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    p, pl, ph = wilson_ci(tp, tp + fp)
    r, rl, rh = wilson_ci(tp, tp + fn)
    f1 = (2 * p * r / (p + r)) if (p and r) else (0.0 if (tp + fp + fn) else None)
    return {
        "precision": p,
        "precision_ci": [pl, ph],
        "recall": r,
        "recall_ci": [rl, rh],
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def macro_mean(values):
    """Mean of the non-``None`` values, or ``None`` when nothing scored."""
    scored = [v for v in values if v is not None]
    return sum(scored) / len(scored) if scored else None


__all__ = [
    "iou",
    "greedy_match",
    "wilson_ci",
    "fmt_pct",
    "average_precision",
    "prf",
    "macro_mean",
]
