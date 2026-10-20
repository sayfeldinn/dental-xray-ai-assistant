"""
Shared fixtures. Env vars are set before any app import because Settings requires them;
the values are dummies (JWT-shaped, because supabase-py validates the key format) and win over
the real ../.env, so tests can never reach a real project.
"""

import os

for _key in (
    "SUPABASE_URL", "SUPABASE_PROJECT_REF", "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_ANON_KEY", "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY",
):
    os.environ.setdefault(_key, "https://test.supabase.co" if _key == "SUPABASE_URL" else "test.test.test")

from datetime import date, datetime, timezone
from itertools import count
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import pytest

from app.domain.feedback import FeedbackLog
from app.domain.finding import Finding
from app.domain.patient import Patient
from app.domain.prescription import Prescription
from app.domain.treatment import Treatment

TODAY = date(2026, 10, 20)   # fixed so ages never drift
NOW = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)


def make_patient(age: int = 35, weight_kg: Optional[float] = 78, allergies=(), medications=(), conditions=(),
                 patient_id: Optional[UUID] = None) -> Patient:
    return Patient(
        id=patient_id or uuid4(), first_name="Test", last_name="Patient", gender="male",
        date_of_birth=date(TODAY.year - age - 1, 1, 1),   # birthday already passed this year -> exact age
        weight_kg=weight_kg, allergies=list(allergies), current_medications=list(medications),
        medical_conditions=list(conditions), created_at=NOW, updated_at=NOW,
    )


_tooth = count(1)


def make_finding(disease: str = "Periapical Lesion", fdi: str = "36", review_status: str = "confirmed",
                 confirmed_disease: Optional[str] = None, scan_id: Optional[UUID] = None,
                 patient_id: Optional[UUID] = None) -> Finding:
    return Finding(
        id=uuid4(), scan_id=scan_id or uuid4(), patient_id=patient_id or uuid4(),
        quadrant=int(fdi[0]), tooth_id=int(fdi[1]), tooth_fdi=fdi, disease=disease,
        disease_confidence=0.9, box=[0, 0, 10, 10], review_status=review_status,
        confirmed_disease=confirmed_disease, created_at=NOW, updated_at=NOW,
    )


# --- In-memory stand-ins for the Supabase-backed services ----------------------

class FakePatients:
    def __init__(self, *patients: Patient):
        self.rows: Dict[UUID, Patient] = {p.id: p for p in patients}

    async def get_patient(self, patient_id):
        return self.rows.get(patient_id)


class FakeScans:
    def __init__(self):
        self.rows: Dict[UUID, object] = {}

    def add(self, patient_id: UUID) -> UUID:
        scan = type("Scan", (), {"id": uuid4(), "patient_id": patient_id})()
        self.rows[scan.id] = scan
        return scan.id

    async def get_scan(self, scan_id):
        return self.rows.get(scan_id)


class FakeFindings:
    def __init__(self):
        self.rows: List[Finding] = []

    async def get_finding(self, finding_id):
        return next((f for f in self.rows if f.id == finding_id), None)

    async def review_finding(self, finding_id, review_status, dentist_id=None, confirmed_disease=None,
                             dentist_notes=None):
        f = await self.get_finding(finding_id)
        if not f:
            return None
        changes = {"review_status": review_status, "reviewed_at": NOW}
        if confirmed_disease:
            changes["confirmed_disease"] = confirmed_disease
        if dentist_notes:
            changes["dentist_notes"] = dentist_notes
        updated = Finding(**{**f.model_dump(), **changes})
        self.rows[self.rows.index(f)] = updated
        return updated

    async def get_confirmed_findings(self, scan_id):
        return [f for f in self.rows if f.scan_id == scan_id and f.review_status in ("confirmed", "modified")]


class _Table:
    model = None

    def __init__(self):
        self.rows: Dict[UUID, object] = {}

    def _update(self, row_id, changes):
        if row_id not in self.rows:
            return None
        row = self.rows[row_id]
        self.rows[row_id] = type(row)(**{**row.model_dump(), **changes})   # re-validate like the DB round trip
        return self.rows[row_id]


class FakeTreatments(_Table):
    async def create_treatment(self, data):
        t = Treatment(**data.model_dump(exclude_none=True), id=uuid4(), created_at=NOW, updated_at=NOW)
        self.rows[t.id] = t
        return t

    async def get_treatment(self, treatment_id):
        return self.rows.get(treatment_id)

    async def list_treatments(self, scan_id=None, patient_id=None, status=None):
        return [t for t in self.rows.values()
                if (not scan_id or t.scan_id == scan_id) and (not patient_id or t.patient_id == patient_id)
                and (not status or t.status == status)]

    async def update_treatment(self, treatment_id, changes):
        return self._update(treatment_id, changes)

    async def delete_treatments(self, treatment_ids):
        for tid in treatment_ids:
            self.rows.pop(tid, None)
        if getattr(self, "cascade", None):
            self.cascade()   # ON DELETE CASCADE


class FakePrescriptions(_Table):
    def __init__(self, treatments: FakeTreatments):
        super().__init__()
        self.treatments = treatments
        treatments.cascade = self._cascade   # emulate ON DELETE CASCADE

    async def create_prescription(self, data):
        p = Prescription(**data.model_dump(exclude_none=True), id=uuid4(), created_at=NOW, updated_at=NOW)
        self.rows[p.id] = p
        return p

    async def get_prescription(self, prescription_id):
        return self.rows.get(prescription_id)

    async def list_prescriptions(self, treatment_ids=None, patient_id=None):
        self._cascade()
        return [p for p in self.rows.values()
                if (treatment_ids is None or p.treatment_id in treatment_ids)
                and (not patient_id or p.patient_id == patient_id)]

    async def update_prescription(self, prescription_id, changes):
        return self._update(prescription_id, changes)

    def _cascade(self):
        self.rows = {k: p for k, p in self.rows.items() if p.treatment_id in self.treatments.rows}


class FakeFeedback:
    """Stand-in for the clinical_feedback_logs service; can be told to fail."""

    def __init__(self):
        self.rows: List[FeedbackLog] = []
        self.fail = False

    async def create_log(self, data):
        if self.fail:
            raise RuntimeError("ledger down")
        log = FeedbackLog(**data.model_dump(), id=uuid4(), created_at=NOW)
        self.rows.append(log)
        return log

    async def list_logs(self, scan_id=None, stage=None, correction_type=None):
        return [l for l in reversed(self.rows) if (not scan_id or l.scan_id == scan_id)
                and (not stage or l.stage == stage) and (not correction_type or l.correction_type == correction_type)]


class World:
    """A patient with one scan, wired into a ClinicalWorkflowService on fakes."""

    def __init__(self, patient: Patient):
        from app.services.clinical_workflow import ClinicalWorkflowService
        self.patient = patient
        self.patients = FakePatients(patient)
        self.scans = FakeScans()
        self.findings = FakeFindings()
        self.treatments = FakeTreatments()
        self.prescriptions = FakePrescriptions(self.treatments)
        self.scan_id = self.scans.add(patient.id)
        self.feedback = FakeFeedback()
        self.ml_calls: List[dict] = []
        self.ml_fail = False

        async def ml_feedback(**payload):
            if self.ml_fail:
                raise RuntimeError("ml down")
            self.ml_calls.append(payload)

        self.workflow = ClinicalWorkflowService(
            self.patients, self.scans, self.findings, self.treatments, self.prescriptions, today=lambda: TODAY,
            feedback=self.feedback, ml_feedback=ml_feedback)

    def add_finding(self, **kwargs) -> Finding:
        f = make_finding(scan_id=self.scan_id, patient_id=self.patient.id, **kwargs)
        self.findings.rows.append(f)
        return f


@pytest.fixture
def world():
    return lambda patient=None: World(patient or make_patient())
