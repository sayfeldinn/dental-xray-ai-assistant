"""Geometry and contract tests for the v3 inference pipeline (no real weights)."""

import inference_pipeline as ip
from conftest import tooth


# --- stage 1: teeth ---------------------------------------------------------

def test_class_index_maps_to_fdi(models, image):
    models(teeth=[(0, 0.9, [0, 0, 10, 10]), (13, 0.9, [100, 0, 110, 10]),
                  (31, 0.9, [200, 0, 210, 10])])
    fdis = sorted(t["tooth_fdi"] for t in ip.detect_teeth(image))
    assert fdis == ["11", "26", "48"]


def test_dedup_keeps_the_most_confident_of_overlapping_classes(models, image):
    # The same physical tooth predicted as 17 (0.6) and 18 (0.9).
    models(teeth=[tooth(17, 0.6, [0, 0, 100, 100]), tooth(18, 0.9, [2, 2, 100, 100]),
                  tooth(16, 0.8, [300, 0, 400, 100])])
    fdis = sorted(t["tooth_fdi"] for t in ip.detect_teeth(image))
    assert fdis == ["16", "18"]


# --- stage 3: association ---------------------------------------------------

def _teeth(*specs):
    return [{"quadrant": int(f[0]), "tooth_id": int(f[1]), "tooth": f"Tooth_{f[1]}",
             "tooth_fdi": f, "tooth_confidence": c, "box": b} for f, c, b in specs]


def _lesion(box, conf=0.8, disease="Caries", disease_id=1):
    return {"disease": disease, "disease_id": disease_id, "disease_confidence": conf, "box": box}


def test_lesion_goes_to_the_tooth_it_overlaps_most():
    teeth = _teeth(("36", 0.9, [0, 0, 100, 100]), ("37", 0.8, [100, 0, 200, 100]))
    [d] = ip.associate([_lesion([80, 10, 190, 90])], teeth)
    assert d["tooth_fdi"] == "37"
    assert d["box"] == [80, 10, 190, 90]          # the lesion box, not the tooth box


def test_lesion_without_overlap_falls_back_to_the_nearest_tooth():
    teeth = _teeth(("11", 0.9, [0, 0, 100, 100]), ("21", 0.9, [500, 0, 600, 100]))
    [d] = ip.associate([_lesion([620, 0, 640, 20])], teeth)
    assert d["tooth_fdi"] == "21"


def test_association_confidence_is_disease_times_tooth():
    teeth = _teeth(("46", 0.5, [0, 0, 100, 100]))
    [d] = ip.associate([_lesion([10, 10, 50, 50], conf=0.8)], teeth)
    assert d["association_confidence"] == 0.8 * 0.5


def test_lesions_are_dropped_when_no_teeth_are_found():
    assert ip.associate([_lesion([0, 0, 10, 10])], []) == []


# --- advisory: missing teeth and quadrants ----------------------------------

def test_interior_gap_is_reported_with_its_neighbours():
    teeth = _teeth(("14", 0.9, [0, 0, 100, 100]), ("16", 0.7, [200, 0, 300, 100]))
    [gap] = ip.derive_missing_teeth(teeth)
    assert gap["tooth_fdi"] == "15"
    assert gap["bounded_by"] == ["14", "16"]
    assert gap["confidence"] == 0.7                # the weaker neighbour
    assert gap["box"] == [100.0, 0.0, 200.0, 100.0]


def test_arch_edges_and_low_confidence_teeth_do_not_create_gaps():
    # 1 and 8 are never "missing" (edge of the arch / third molar); a gap needs teeth
    # on both sides, and a low-confidence tooth does not count as present.
    teeth = _teeth(("12", 0.9, [0, 0, 10, 10]), ("17", 0.9, [500, 0, 510, 10]),
                   ("14", 0.1, [200, 0, 210, 10]))
    fdis = [g["tooth_fdi"] for g in ip.derive_missing_teeth(teeth)]
    assert fdis == ["13", "14", "15", "16"]


def test_quadrant_box_is_the_union_of_its_teeth():
    teeth = _teeth(("11", 0.9, [10, 20, 50, 60]), ("12", 0.6, [0, 25, 40, 70]))
    [q] = ip.derive_quadrants(teeth)
    assert q["quadrant"] == 1
    assert q["box"] == [0, 20, 50, 70]
    assert q["confidence"] == 0.6


# --- full pipeline contract -------------------------------------------------

def test_pipeline_returns_the_backend_contract(models, image):
    models(teeth=[tooth(36, 0.9, [0, 0, 100, 100])],
           lesions=[(3, 0.85, [10, 10, 60, 60])])
    out = ip.run_dentex_pipeline(image)
    assert (out["image_width"], out["image_height"]) == (2000, 1000)
    [d] = out["detections"]
    assert (d["tooth_fdi"], d["quadrant"], d["tooth_id"], d["disease"]) == ("36", 3, 6, "Deep Caries")
    assert out["num_detections"] == 1
    for key in ("quadrants", "missing_teeth", "model", "confidence_threshold"):
        assert key in out


def test_threshold_filters_detections_and_is_echoed(models, image):
    models(teeth=[tooth(11, 0.9, [0, 0, 100, 100])],
           lesions=[(1, 0.30, [0, 0, 50, 50]), (1, 0.60, [50, 50, 100, 100])])
    out = ip.run_dentex_pipeline(image, confidence_threshold=0.5)
    assert [d["disease_confidence"] for d in out["detections"]] == [0.60]
    assert out["confidence_threshold"] == 0.5


def test_threshold_below_the_floor_asks_the_detector_for_more(models, image):
    installed = models(teeth=[tooth(11, 0.9, [0, 0, 100, 100])],
                       lesions=[(1, 0.12, [0, 0, 50, 50])])
    out = ip.run_dentex_pipeline(image, confidence_threshold=0.10)
    assert installed["disease"].calls[0]["conf"] == 0.10
    assert out["num_detections"] == 1


def test_out_of_range_threshold_is_clamped(models, image):
    models(teeth=[tooth(11, 0.9, [0, 0, 100, 100])])
    assert ip.run_dentex_pipeline(image, confidence_threshold=1.5)["confidence_threshold"] == 1.0


def test_a_broken_findings_model_does_not_break_predict(models, image, monkeypatch):
    monkeypatch.setitem(ip.CONFIG, "findings_in_predict", True)
    models(teeth=[tooth(11, 0.9, [0, 0, 100, 100])], lesions=[(1, 0.9, [0, 0, 50, 50])],
           findings_error=RuntimeError("weights missing"))
    out = ip.run_dentex_pipeline(image)
    assert out["num_detections"] == 1
    assert out["findings"] == [] and "weights missing" in out["findings_error"]
