"""Unit tests for the shared detection metrics (ml/eval/metrics.py).

Pure-Python and dependency-free, so they run in CI without torch/ultralytics.
"""

import os
import sys

import pytest

EVAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
sys.path.insert(0, EVAL_DIR)

from metrics import (  # noqa: E402
    average_precision,
    fmt_pct,
    greedy_match,
    iou,
    macro_mean,
    prf,
    wilson_ci,
)


def test_iou_identical_boxes():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == pytest.approx(1.0)


def test_iou_disjoint_boxes():
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_iou_half_overlap():
    # Two 10x10 boxes overlapping in a 5x10 strip: inter=50, union=150.
    assert iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(50 / 150)


def test_greedy_match_is_one_to_one_and_iou_ordered():
    gt = [(0, 0, 10, 10), (100, 100, 110, 110)]
    pred = [(100, 100, 110, 110), (1, 0, 11, 10)]  # best match for gt0 is pred1
    matches = greedy_match(gt, pred, 0.5)
    assert sorted(matches) == [(0, 1), (1, 0)]


def test_greedy_match_respects_threshold():
    assert greedy_match([(0, 0, 10, 10)], [(50, 50, 60, 60)], 0.5) == []


def test_wilson_ci_bounds_and_center():
    p, lo, hi = wilson_ci(7, 10)
    assert p == pytest.approx(0.7)
    assert lo < p < hi
    assert lo >= 0.0 and hi <= 1.0


def test_wilson_ci_empty():
    assert wilson_ci(0, 0) == (None, None, None)


def test_average_precision_known_defect_is_precision():
    """KNOWN DEFECT (behaviour preserved by this refactor).

    ``average_precision`` divides the running recall by the number of *matched*
    positives rather than the number of ground-truth instances, so recall always
    reaches 1.0 and the integral collapses to the precision at the lowest
    confidence -- i.e. the class's overall precision. This test pins the current
    behaviour so the refactor stays byte-identical; see the xfail below for what
    the function should return.
    """
    flags = [(0.9, True), (0.8, True), (0.2, False), (0.1, False)]
    assert average_precision(flags) == pytest.approx(0.5)  # = precision, not AP


@pytest.mark.xfail(
    strict=True,
    reason="average_precision uses matched positives as the "
    "recall denominator instead of the GT count",
)
def test_average_precision_perfect_ranking():
    # Two positives ranked above two negatives -> AP must be 1.0.
    flags = [(0.9, True), (0.8, True), (0.2, False), (0.1, False)]
    assert average_precision(flags) == pytest.approx(1.0)


def test_average_precision_all_negatives_is_none():
    assert average_precision([(0.9, False)]) is None


def test_prf_counts_and_f1():
    out = prf({"tp": 3, "fp": 1, "fn": 1})
    assert out["tp"] == 3 and out["fp"] == 1 and out["fn"] == 1
    assert out["precision"] == pytest.approx(0.75)
    assert out["recall"] == pytest.approx(0.75)
    assert out["f1"] == pytest.approx(0.75)


def test_prf_no_predictions_has_no_f1():
    out = prf({"tp": 0, "fp": 0, "fn": 2})
    assert out["precision"] is None
    assert out["recall"] == 0.0
    assert out["f1"] == 0.0


def test_macro_mean_ignores_none():
    assert macro_mean([1.0, None, 0.0]) == pytest.approx(0.5)
    assert macro_mean([None, None]) is None


def test_fmt_pct():
    assert fmt_pct(0.542) == "54.2%"
    assert fmt_pct(None) == "-"
