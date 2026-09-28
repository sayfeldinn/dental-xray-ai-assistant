"""
Integration contract tests: the routes and payloads the React client actually
uses, plus the conversion helpers that sit between the ML service, the
database rows and the API responses.

These run without a database: route existence is checked against the FastAPI
route table, and everything else is a pure helper.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys
from datetime import datetime
from uuid import UUID

import pytest

# Settings() is constructed at import time by app.core.config and requires
# SUPABASE_URL before any application module can be imported. Test-only
# values; nothing here talks to a real database.
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.api.feedback import FindingFeedbackRequest, _coerce_action, _uuid_or_none  # noqa: E402
from app.api.treatments import map_treatment_status  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.prediction import (  # noqa: E402
    findings_to_prediction_rows,
    prediction_to_finding,
    rows_to_predictions,
)
from app.schemas.patient import GenderEnum  # noqa: E402
from app.schemas.scan import BoundingBox, Finding, FindingSeverityEnum, FindingTypeEnum  # noqa: E402
from app.services.ml_service import MLInferenceService, _to_finding  # noqa: E402
from app.services.patient_service import build_patient_response  # noqa: E402

API_PREFIX = "/api/v1"

# Every (method, path) the frontend calls, taken from frontend/src/services/api.js
# and the pages (Scans, Review, Treatments, Patients).
FRONTEND_CONTRACT = [
    ("POST", f"{API_PREFIX}/auth/signup"),
    ("POST", f"{API_PREFIX}/auth/signin"),
    ("POST", f"{API_PREFIX}/auth/signout"),
    ("GET", f"{API_PREFIX}/auth/me"),
    ("GET", f"{API_PREFIX}/patients"),
    ("POST", f"{API_PREFIX}/patients"),
    ("GET", f"{API_PREFIX}/patients/{{patient_id}}"),
    ("PUT", f"{API_PREFIX}/patients/{{patient_id}}"),
    ("DELETE", f"{API_PREFIX}/patients/{{patient_id}}"),
    ("GET", f"{API_PREFIX}/scans/"),
    ("POST", f"{API_PREFIX}/scans/"),
    ("POST", f"{API_PREFIX}/scans/upload"),
    ("GET", f"{API_PREFIX}/scans/{{scan_id}}"),
    ("PUT", f"{API_PREFIX}/scans/{{scan_id}}"),
    ("DELETE", f"{API_PREFIX}/scans/{{scan_id}}"),
    ("GET", f"{API_PREFIX}/scans/{{scan_id}}/predictions"),
    ("POST", f"{API_PREFIX}/ml/infer/{{scan_id}}"),
    ("POST", f"{API_PREFIX}/ml/predict"),
    ("POST", f"{API_PREFIX}/feedback/"),
    ("GET", f"{API_PREFIX}/recommendations/{{scan_id}}"),
    ("POST", f"{API_PREFIX}/recommendations/treatment"),
    ("POST", f"{API_PREFIX}/recommendations/check-contraindication"),
    ("GET", f"{API_PREFIX}/recommendations/drugs"),
    ("GET", f"{API_PREFIX}/recommendations/finding-mappings"),
    ("POST", f"{API_PREFIX}/treatments/"),
]


def _route_table() -> set:
    table = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            if method == "HEAD":
                continue
            table.add((method, route.path))
    return table


@pytest.mark.parametrize("method,path", FRONTEND_CONTRACT)
def test_frontend_route_is_registered(method, path):
    assert (method, path) in _route_table(), (
        f"{method} {path} is called by the frontend but is not served by the "
        f"backend. Registered routes: {sorted(_route_table())}"
    )


def test_scan_predictions_route_is_declared_before_scan_detail():
    """A greedy /{scan_id} must not swallow /{scan_id}/predictions."""
    paths = [route.path for route in app.routes if hasattr(route, "path")]
    detail = f"{API_PREFIX}/scans/{{scan_id}}"
    predictions = f"{API_PREFIX}/scans/{{scan_id}}/predictions"
    assert predictions in paths
    # Starlette matches in declaration order; the exact route only wins if it
    # exists at all, and path params never span a '/'.
    assert paths.index(predictions) > paths.index(detail)


# --------------------------------------------------------------------------- #
# prediction <-> finding conversions
# --------------------------------------------------------------------------- #
def test_prediction_to_finding_builds_nested_bbox():
    finding = prediction_to_finding(
        {
            "id": "abc",
            "finding_type": "periapical",
            "severity": "high",
            "confidence": 0.77,
            "bbox_x": 12,
            "bbox_y": 34,
            "bbox_width": 56,
            "bbox_height": 78,
            "notes": "lesion",
        }
    )

    assert finding.type == FindingTypeEnum.PERIAPICAL
    assert finding.severity == FindingSeverityEnum.HIGH
    assert finding.confidence == 0.77
    assert finding.bounding_box == BoundingBox(x=12, y=34, width=56, height=78)
    assert finding.description == "lesion"


def test_prediction_to_finding_repairs_bad_rows():
    """One malformed row must degrade, not 500 the recommendations endpoint."""
    finding = prediction_to_finding(
        {
            "finding_type": "not_a_real_class",
            "severity": "catastrophic",
            "confidence": 3.4,
            "bbox_x": -10,
            "bbox_y": -20,
            "bbox_width": 0,
            "bbox_height": -5,
        }
    )

    assert finding.type == FindingTypeEnum.OTHER
    assert finding.severity == FindingSeverityEnum.LOW
    assert finding.confidence == 1.0
    assert finding.bounding_box.x == 0
    assert finding.bounding_box.y == 0
    assert finding.bounding_box.width > 0
    assert finding.bounding_box.height > 0


def test_findings_round_trip_through_prediction_rows():
    finding = Finding(
        type=FindingTypeEnum.CARIES,
        severity=FindingSeverityEnum.MEDIUM,
        confidence=0.84,
        bounding_box=BoundingBox(x=1, y=2, width=30, height=40),
        tooth_number="26",
        description="caries",
    )

    rows = findings_to_prediction_rows([finding], scan_id="scan-1", dentist_id="dent-1")

    assert len(rows) == 1
    # feedback.finding_id is a UUID column, so derived ids must be valid UUIDs.
    UUID(rows[0]["id"])
    assert rows[0]["scan_id"] == "scan-1"
    assert rows[0]["finding_type"] == "caries"
    assert rows[0]["bbox_width"] == 30

    restored = rows_to_predictions(rows)
    assert restored[0].finding_type == "caries"
    assert restored[0].confidence == 0.84
    assert restored[0].bbox_height == 40


# --------------------------------------------------------------------------- #
# detector response parsing
# --------------------------------------------------------------------------- #
def test_detector_v1_response_maps_to_finding():
    finding = _to_finding(
        {
            "class_id": 0,
            "class_name": "Caries",
            "confidence": 0.81,
            "bbox": {"xmin": 10, "ymin": 20, "xmax": 60, "ymax": 90},
        }
    )

    assert finding.type == FindingTypeEnum.CARIES
    assert finding.bounding_box.x == 10
    assert finding.bounding_box.y == 20
    assert finding.bounding_box.width == 50
    assert finding.bounding_box.height == 70


def test_multimodel_response_maps_to_finding_with_tooth_number():
    finding = _to_finding(
        {
            "disease": "Periapical Lesion",
            "confidence": 0.9,
            "quadrant": 2,
            "tooth": 6,
            "disease_bbox": {"x": 5, "y": 6, "width": 20, "height": 30},
        }
    )

    assert finding.type == FindingTypeEnum.PERIAPICAL
    assert finding.severity == FindingSeverityEnum.HIGH
    assert finding.tooth_number == "26"
    assert finding.bounding_box.width == 20


def test_detector_unreachable_falls_back_to_labelled_mock():
    service = MLInferenceService(
        api_url="http://127.0.0.1:9", timeout=2.0, allow_mock_fallback=True
    )

    # Empty source fails before any socket is opened, so this stays offline.
    findings = asyncio.run(service.predict("", 0.5))

    assert findings, "mock fallback should still return detections"
    info = service.get_model_info()
    assert info["mode"] == "mock"
    assert info["model_version"] == "mock-v1.0"
    assert info["last_error"]


def test_mock_fallback_can_be_disabled(tmp_path):
    service = MLInferenceService(
        api_url="http://127.0.0.1:9", timeout=2.0, allow_mock_fallback=False
    )
    with pytest.raises(Exception):
        asyncio.run(service.predict("", 0.5))


def test_load_image_reads_local_file(tmp_path):
    image = tmp_path / "xray.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n fake")

    service = MLInferenceService(api_url="")
    data, content_type = asyncio.run(service._load_image(str(image)))

    assert data.startswith(b"\x89PNG")
    assert content_type == "image/png"


# --------------------------------------------------------------------------- #
# treatment + feedback vocabulary
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("planned", "confirmed"),
        ("confirmed", "confirmed"),
        ("recommended", "recommended"),
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("nonsense", "recommended"),
        (None, "recommended"),
    ],
)
def test_map_treatment_status_only_emits_schema_values(raw, expected):
    from app.schemas.treatment import TreatmentStatusEnum

    allowed = {member.value for member in TreatmentStatusEnum}
    mapped = map_treatment_status(raw)
    assert mapped == expected
    assert mapped in allowed


@pytest.mark.parametrize(
    "payload,expected",
    [
        (FindingFeedbackRequest(is_correct=True), "accepted"),
        (FindingFeedbackRequest(is_correct=False), "rejected"),
        (FindingFeedbackRequest(dentist_action="confirmed"), "accepted"),
        (FindingFeedbackRequest(dentist_action="edited"), "corrected"),
        (FindingFeedbackRequest(dentist_action="rejected"), "rejected"),
    ],
)
def test_feedback_action_satisfies_check_constraint(payload, expected):
    assert _coerce_action(payload) == expected
    assert expected in {"accepted", "rejected", "corrected"}


def test_feedback_finding_id_drops_non_uuid_values():
    assert _uuid_or_none("5f0c9c3e-8f1a-4c2d-9b7e-1a2b3c4d5e6f") is not None
    assert _uuid_or_none("p-12") is None
    assert _uuid_or_none(None) is None


# --------------------------------------------------------------------------- #
# patient fields the Scans/Treatment screens read
# --------------------------------------------------------------------------- #
def _patient_row(**overrides):
    today = datetime.utcnow()
    dob = datetime(today.year - 30, today.month, min(today.day, 28))
    row = {
        "id": "p-1",
        "dentist_id": "d-1",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "date_of_birth": dob.isoformat(),
        "gender": GenderEnum.FEMALE.value,
        "phone": "+44 20 7946 0000",
        "medical_conditions": ["Active Ulcer"],
        "allergies": ["Penicillin"],
        "current_medications": ["Warfarin"],
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }
    row.update(overrides)
    return row


def test_patient_response_exposes_age_contact_and_history():
    patient = build_patient_response(_patient_row())

    assert patient.age == 30
    assert patient.contact_number == "+44 20 7946 0000"
    assert [item.condition for item in patient.medical_history] == ["Active Ulcer"]
    # The Treatment screen highlights medication listed here.
    assert "Ibuprofen" in patient.medical_history[0].contraindications


def test_patient_response_falls_back_to_phone_without_conditions():
    patient = build_patient_response(_patient_row(medical_conditions=[]))

    assert patient.medical_history == []
    assert patient.contact_number == patient.phone


def test_age_helper_returns_none_for_unusable_dates():
    from app.services.patient_service import _age_from_dob

    assert _age_from_dob("not-a-date") is None
    assert _age_from_dob(None) is None
    assert _age_from_dob(object()) is None
