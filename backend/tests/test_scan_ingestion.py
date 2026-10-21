"""Steps 1-2: upload validation, AI failure handling, re-analysis rules; patient ownership on create/list."""

from datetime import date
from uuid import uuid4

import pytest

from app.domain.errors import ConflictError, RuleViolationError, UpstreamError
from app.domain.scan import Scan
from app.services.scan_ingestion import ScanIngestionService
from tests.conftest import DENTIST_ID, NOW, http_client, make_finding, make_patient


class FakeScanStore:
    def __init__(self):
        self.rows, self.uploads, self.updates = {}, [], []

    async def upload_image(self, file_bytes, patient_id, filename):
        self.uploads.append(filename)
        return f"https://storage/{filename}", f"patients/{patient_id}/{filename}"

    async def create_scan(self, data):
        scan = Scan(**data.model_dump(), id=uuid4(), created_at=NOW, updated_at=NOW)
        self.rows[scan.id] = scan
        return scan

    async def update_scan(self, scan_id, data):
        self.updates.append(data.model_dump(exclude_none=True))

    async def update_ml_results(self, **kw):
        self.updates.append({"status": "analyzed"})

    async def download_image(self, path):
        return b"stored-bytes"


class FakeFindingStore:
    def __init__(self, existing=()):
        self.existing, self.created, self.deleted = list(existing), [], False

    async def list_findings_by_scan(self, scan_id):
        return self.existing

    async def delete_findings_by_scan(self, scan_id):
        self.deleted = True

    async def bulk_create_findings(self, rows):
        self.created = rows
        return rows


class FakeML:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    async def analyze_scan(self, image_bytes, filename, confidence_threshold):
        self.calls.append(image_bytes)
        if self.fail:
            raise RuntimeError("connection refused")
        return {"image_width": 100, "image_height": 50, "report": "AI report", "detections": [{}, {}]}

    def parse_detections_to_findings(self, ml_output, scan_id, patient_id):
        return [{"scan_id": scan_id}] * len(ml_output["detections"])


def service(ml=None, findings=None, max_mb=1):
    return ScanIngestionService(FakeScanStore(), findings or FakeFindingStore(), ml or FakeML(), max_mb)


async def upload(svc, data=b"png-bytes", content_type="image/png", analyze=True, filename="../../etc/x.png"):
    return await svc.upload(patient_id=uuid4(), dentist_id=DENTIST_ID, file_bytes=data, filename=filename,
                            content_type=content_type, scan_type="panoramic", notes=None, auto_analyze=analyze, confidence=0.2)


async def test_upload_analyses_and_creates_pending_findings():
    svc = service()
    res = await upload(svc)
    assert res.status == "analyzed" and res.findings_count == 2 and res.ai_report == "AI report"
    assert svc.scans.uploads == ["scan.png"]          # the client's filename never reaches storage
    scan = next(iter(svc.scans.rows.values()))
    assert scan.dentist_id == DENTIST_ID


async def test_upload_without_analysis_stops_after_storage():
    svc = service()
    res = await upload(svc, analyze=False)
    assert res.status == "uploaded" and svc.ml.calls == []


@pytest.mark.parametrize("data,ctype", [(b"x", "application/pdf"), (b"x", None), (b"", "image/png"),
                                        (b"x" * (1024 * 1024 + 1), "image/jpeg")])
async def test_upload_rejects_bad_files(data, ctype):
    svc = service()
    with pytest.raises(RuleViolationError):
        await upload(svc, data=data, content_type=ctype)
    assert svc.scans.uploads == []


async def test_ml_failure_keeps_the_scan_marked_failed():
    svc = service(ml=FakeML(fail=True))
    with pytest.raises(UpstreamError):
        await upload(svc)
    assert svc.scans.updates[-1]["status"] == "failed" and "connection refused" in svc.scans.updates[-1]["notes"]


def _stored_scan(path="patients/p/scan.png"):
    return Scan(id=uuid4(), patient_id=uuid4(), image_url="u", storage_path=path, status="failed", created_at=NOW, updated_at=NOW)


async def test_reanalyse_replaces_pending_findings_from_the_stored_image():
    findings = FakeFindingStore([make_finding(review_status="pending")])
    svc = service(findings=findings)
    res = await svc.reanalyze(_stored_scan(), 0.3)
    assert findings.deleted and res.findings_count == 2 and svc.ml.calls == [b"stored-bytes"]


async def test_reanalyse_refused_after_any_review_or_without_an_image():
    with pytest.raises(ConflictError):
        await service(findings=FakeFindingStore([make_finding(review_status="confirmed")])).reanalyze(_stored_scan(), 0.2)
    with pytest.raises(RuleViolationError):
        await service().reanalyze(_stored_scan(path=None), 0.2)


# --- patients: ownership on create and list -----------------------------------------------

async def test_patient_create_and_list_are_scoped_to_the_signed_in_dentist(world, monkeypatch):
    from app.api.v1 import patients as router
    seen = {}

    async def create_patient(data):
        seen["owner"] = data.dentist_id
        return make_patient(dentist_id=data.dentist_id)

    async def list_patients(dentist_id, search, page, page_size):
        seen["filter"] = dentist_id
        return [], 0

    monkeypatch.setattr(router.patient_service, "create_patient", create_patient)
    monkeypatch.setattr(router.patient_service, "list_patients", list_patients)
    client = http_client(world())
    body = {"first_name": "A", "last_name": "B", "date_of_birth": str(date(1990, 1, 1)), "gender": "female",
            "dentist_id": str(uuid4())}
    assert (await client.post("/api/v1/patients", json=body)).status_code == 201
    assert (await client.get("/api/v1/patients")).status_code == 200
    assert seen == {"owner": DENTIST_ID, "filter": DENTIST_ID}
