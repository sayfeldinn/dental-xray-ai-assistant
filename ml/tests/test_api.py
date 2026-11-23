"""HTTP tests for the ML service (fake detectors, no real weights)."""

import csv
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app as ml_app
from conftest import tooth


@pytest.fixture
def client():
    return TestClient(ml_app.app)


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (200, 100)).save(buf, format="PNG")
    return buf.getvalue()


def _post(client, data=None, params=None):
    return client.post("/predict", files={"file": ("x.png", data or _png(), "image/png")}, params=params)


# --- health -----------------------------------------------------------------

def _weights_dir(tmp_path, monkeypatch, names):
    for name in names:
        (tmp_path / name).write_bytes(b"x")
    monkeypatch.setattr(ml_app, "MODEL_DIR", str(tmp_path))


def test_health_is_ok_when_the_required_weights_exist(client, tmp_path, monkeypatch):
    _weights_dir(tmp_path, monkeypatch, ["tooth_best.pt", "disease_best.pt"])
    body = client.get("/").json()
    assert body["status"] == "ok" and body["models_loaded"] is True
    assert body["weights"]["tooth"] and body["weights"]["disease"]
    assert body["weights"]["findings"] is False          # optional: reported, not required


def test_health_is_degraded_when_a_required_weight_is_missing(client, tmp_path, monkeypatch):
    _weights_dir(tmp_path, monkeypatch, ["tooth_best.pt"])
    body = client.get("/").json()
    assert body["status"] == "degraded" and body["models_loaded"] is False
    assert body["weights"]["disease"] is False


# --- /predict -----------------------------------------------------------------

def test_predict_returns_detections_and_a_report(client, models):
    models(teeth=[tooth(46, 0.9, [0, 0, 100, 100])], lesions=[(2, 0.8, [10, 10, 50, 50])])
    body = _post(client).json()
    assert body["detections"][0]["tooth_fdi"] == "46"
    assert "Tooth 46" in body["ai_generated_report"]
    assert "Periapical" in body["ai_generated_report"]


def test_predict_passes_the_threshold_through(client, models):
    models(teeth=[tooth(11, 0.9, [0, 0, 100, 100])], lesions=[(1, 0.4, [0, 0, 50, 50])])
    body = _post(client, params={"confidence_threshold": 0.5}).json()
    assert body["confidence_threshold"] == 0.5 and body["detections"] == []


def test_predict_rejects_an_out_of_range_threshold(client, models):
    models()
    assert _post(client, params={"confidence_threshold": 2}).status_code == 422


def test_predict_rejects_a_non_image(client, models):
    models()
    assert _post(client, data=b"not an image").status_code == 400


def test_predict_returns_503_when_inference_fails(client, monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("tooth_best.pt")

    monkeypatch.setattr(ml_app, "run_dentex_pipeline", boom)
    resp = _post(client)
    assert resp.status_code == 503 and "tooth_best.pt" in resp.json()["detail"]


# --- report text ----------------------------------------------------------------

def test_report_uses_fdi_numbers():
    report = ml_app.generate_clinical_report(
        [{"quadrant": 4, "tooth_id": 8, "tooth": "Tooth_8", "disease": "Impacted"}])
    assert "Tooth 48 (Quadrant 4) appears to be impacted" in report


def test_report_for_a_clean_scan():
    assert "No abnormalities" in ml_app.generate_clinical_report([])


# --- feedback -----------------------------------------------------------------

def test_finding_feedback_is_appended_to_the_csv(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ml_app, "FEEDBACK_DIR", str(tmp_path))
    entry = {"image_id": "scan-1", "quadrant": 3, "tooth": 6, "original_disease": "Caries",
             "is_correct": False, "corrected_disease": "Deep Caries"}
    for _ in range(2):
        assert client.post("/feedback/finding", json=entry).status_code == 200
    rows = list(csv.reader(open(tmp_path / "dentist_finding_feedback.csv")))
    assert rows[0][0] == "timestamp" and len(rows) == 3          # one header, two rows
    assert rows[1][5:7] == ["False", "Deep Caries"]
