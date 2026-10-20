"""HTTP layer: routing, error mapping, and the always-visible validation disclaimer."""

from uuid import uuid4

import httpx
import pytest

from app.api.deps import get_workflow
from app.main import app
from tests.conftest import make_patient


@pytest.fixture
def api(world):
    w = world(make_patient(allergies=["penicillin"]))
    w.add_finding(disease="Periapical Lesion")
    app.dependency_overrides[get_workflow] = lambda: w.workflow
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    yield w, client
    app.dependency_overrides.clear()


GENERATE = {"clinical_context": {"active_infection": True}}


async def test_recommendation_flow_over_http(api):
    w, client = api
    res = await client.post(f"/api/v1/recommendations/scans/{w.scan_id}", json=GENERATE)
    assert res.status_code == 201
    body = res.json()
    assert "Pending Dentist Validation" in body["disclaimer"]
    rx = body["plans"][0]["prescriptions"][0]
    assert rx["drug_name"] == "Clindamycin" and rx["contraindication_status"] == "warning"
    assert rx["contraindication_warnings"][0]["rule_id"] == "R-18"

    # warning accepted only with acknowledgement -> 422 then 200
    url = f"/api/v1/prescriptions/{rx['id']}/decision"
    assert (await client.post(url, json={"decision": "accepted"})).status_code == 422
    ok = await client.post(url, json={"decision": "accepted", "acknowledge_warnings": True})
    assert ok.status_code == 200 and ok.json()["dentist_status"] == "accepted"
    assert (await client.post(url, json={"decision": "rejected"})).status_code == 409   # final


async def test_recommendation_body_is_optional_and_defaults_to_no_drugs(api):
    w, client = api
    res = await client.post(f"/api/v1/recommendations/scans/{w.scan_id}")
    assert res.status_code == 201 and res.json()["plans"][0]["prescriptions"] == []


async def test_not_found_and_conflict_mapping(api):
    _, client = api
    assert (await client.post(f"/api/v1/recommendations/scans/{uuid4()}", json=GENERATE)).status_code == 404
    assert (await client.get(f"/api/v1/prescriptions/{uuid4()}")).status_code == 404
    assert (await client.get(f"/api/v1/treatments/{uuid4()}")).status_code == 404


async def test_list_endpoints_require_a_filter(api):
    w, client = api
    assert (await client.get("/api/v1/treatments")).status_code == 400
    assert (await client.get("/api/v1/prescriptions")).status_code == 400
    await client.post(f"/api/v1/recommendations/scans/{w.scan_id}", json=GENERATE)
    listed = (await client.get("/api/v1/treatments", params={"scan_id": str(w.scan_id)})).json()
    assert listed["total"] == 1 and listed["treatments"][0]["prescriptions"]


async def test_check_endpoint_and_validation_errors(api):
    w, client = api
    res = await client.post("/api/v1/prescriptions/check", json={
        "patient_id": str(w.patient.id), "drug_name": "Amoxicillin",
        "indication_type": "active_infection", "dosage": "500 mg"})
    assert res.status_code == 200 and res.json()["status"] == "contraindicated"
    bad = await client.post("/api/v1/prescriptions/check", json={
        "patient_id": str(w.patient.id), "drug_name": "Amoxicillin", "indication_type": "nonsense"})
    assert bad.status_code == 422


async def test_dentist_authored_treatment_and_prescription_over_http(api):
    w, client = api
    t = await client.post("/api/v1/treatments", json={
        "scan_id": str(w.scan_id), "treatment_category": "surgical_extraction", "description": "Extraction"})
    assert t.status_code == 201 and t.json()["status"] == "confirmed"
    rx = await client.post("/api/v1/prescriptions", json={
        "treatment_id": t.json()["id"], "drug_name": "Amoxicillin", "dosage": "500 mg",
        "frequency": "every 8 hours", "duration": "5 days", "indication_type": "active_infection"})
    assert rx.status_code == 201 and rx.json()["contraindication_status"] == "contraindicated"   # penicillin allergy
    assert (await client.post("/api/v1/treatments", json={"scan_id": str(uuid4()), "treatment_category": "restorative",
                                                          "description": "x"})).status_code == 404
