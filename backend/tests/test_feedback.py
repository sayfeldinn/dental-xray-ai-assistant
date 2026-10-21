"""Step 6: the feedback ledger. Only departures from the AI are logged; ML forwarding is best effort."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.errors import NotFoundError
from app.domain.feedback import MissedFindingReport
from app.domain.finding import FindingReviewRequest
from app.domain.prescription import PrescriptionDecisionRequest
from app.domain.recommendation import RecommendationRequest
from app.domain.treatment import TreatmentDecisionRequest
from app.services.feedback import ml_finding_feedback, missed_finding_feedback, summarize
from tests.conftest import http_client, make_finding, make_patient

INFECTION = RecommendationRequest(clinical_context={"active_infection": True})


def review(finding, status, **kw):
    return FindingReviewRequest(finding_id=finding.id, review_status=status, **kw)


# --- Step 3: finding review ------------------------------------------------------

async def test_confirming_a_finding_logs_nothing(world):
    w = world()
    f = w.add_finding(review_status="pending")
    await w.workflow.review_finding(review(f, "confirmed"))
    assert w.feedback.rows == [] and w.ml_calls == []


async def test_rejecting_a_finding_is_a_false_positive_and_is_forwarded_to_ml(world):
    w = world()
    f = w.add_finding(disease="Caries", fdi="36", review_status="pending")
    await w.workflow.review_finding(review(f, "rejected", dentist_notes="artefact"))
    [log] = w.feedback.rows
    assert (log.stage, log.correction_type) == ("finding_detection", "false_positive")
    assert log.ai_original_data["disease"] == "Caries" and log.ai_original_data["tooth_fdi"] == "36"
    assert log.dentist_corrected_data["disease"] is None and log.notes == "artefact"
    assert w.ml_calls == [{"image_id": str(w.scan_id), "quadrant": 3, "tooth": 6, "original_disease": "Caries",
                           "is_correct": False, "corrected_disease": None, "notes": "artefact"}]


async def test_relabelling_a_finding_is_a_misclassification(world):
    w = world()
    f = w.add_finding(disease="Caries", review_status="pending")
    updated = await w.workflow.review_finding(review(f, "modified", confirmed_disease="Deep Caries"))
    assert updated.effective_disease == "Deep Caries"
    [log] = w.feedback.rows
    assert log.correction_type == "misclassification" and log.dentist_corrected_data["disease"] == "Deep Caries"
    assert w.ml_calls[0]["corrected_disease"] == "Deep Caries"


async def test_modifying_to_the_same_label_is_not_a_correction(world):
    w = world()
    f = w.add_finding(disease="Caries", review_status="pending")
    await w.workflow.review_finding(review(f, "modified", confirmed_disease="Caries"))
    assert w.feedback.rows == []


async def test_review_of_unknown_finding_is_not_found(world):
    w = world()
    with pytest.raises(NotFoundError):
        await w.workflow.review_finding(review(make_finding(), "rejected"))


async def test_ledger_or_ml_outage_never_blocks_the_dentists_decision(world):
    w = world()
    f = w.add_finding(review_status="pending")
    w.feedback.fail = True
    assert (await w.workflow.review_finding(review(f, "rejected"))).review_status == "rejected"
    g = w.add_finding(fdi="46", review_status="pending")
    w.feedback.fail, w.ml_fail = False, True
    assert (await w.workflow.review_finding(review(g, "rejected"))).review_status == "rejected"
    assert len(w.feedback.rows) == 1          # the ledger row survives an ML outage


# --- missed findings (false negatives) -------------------------------------------

async def test_missed_finding_is_logged_and_forwarded(world):
    w = world()
    report = MissedFindingReport(scan_id=w.scan_id, tooth_fdi="47", disease="Periapical Lesion", notes="missed")
    log = await w.workflow.report_missed_finding(report)
    assert log.correction_type == "false_negative" and log.ai_original_data["detected"] is False
    assert w.ml_calls[0]["original_disease"] == "None" and w.ml_calls[0]["corrected_disease"] == "Periapical Lesion"
    assert (w.ml_calls[0]["quadrant"], w.ml_calls[0]["tooth"]) == (4, 7)


async def test_missed_finding_on_unknown_scan_and_ledger_failure_surface(world):
    w = world()
    with pytest.raises(NotFoundError):
        await w.workflow.report_missed_finding(MissedFindingReport(scan_id=uuid4(), tooth_fdi="11", disease="Caries"))
    w.feedback.fail = True
    with pytest.raises(RuntimeError):        # the write IS the request, so it must not be swallowed
        await w.workflow.report_missed_finding(
            MissedFindingReport(scan_id=w.scan_id, tooth_fdi="11", disease="Caries"))


@pytest.mark.parametrize("fdi", ["19", "50", "5", "abc", "08"])
def test_missed_finding_rejects_invalid_fdi(fdi):
    with pytest.raises(ValidationError):
        MissedFindingReport(scan_id=uuid4(), tooth_fdi=fdi, disease="Caries")


def test_missed_finding_rejects_unknown_disease():
    with pytest.raises(ValidationError):
        MissedFindingReport(scan_id=uuid4(), tooth_fdi="11", disease="Gingivitis")


# --- Step 5: prescriptions and treatments ------------------------------------------

async def _proposal(w, **ctx):
    res = await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    plan = res.plans[0]
    return plan.treatment, plan.prescriptions[0]


async def test_accepting_a_clear_prescription_unchanged_logs_nothing(world):
    w = world()
    w.add_finding(disease="Periapical Lesion")
    _, rx = await _proposal(w)
    await w.workflow.decide_prescription(rx.id, PrescriptionDecisionRequest(decision="accepted"))
    assert w.feedback.rows == []


async def test_changing_the_dose_logs_dosage_adjusted(world):
    w = world()
    w.add_finding(disease="Periapical Lesion")
    t, rx = await _proposal(w)
    await w.workflow.decide_prescription(
        rx.id, PrescriptionDecisionRequest(decision="modified", dosage="875 mg", frequency="every 12 hours"))
    [log] = w.feedback.rows
    assert (log.stage, log.correction_type) == ("prescription_dosing", "dosage_adjusted")
    assert log.scan_id == w.scan_id
    assert log.ai_original_data["dosage"] == rx.dosage and log.dentist_corrected_data["dosage"] == "875 mg"
    assert w.ml_calls == []                  # drug feedback is audit-only; the ML queue is for detections


async def test_swapping_the_drug_or_rejecting_logs_drug_override(world):
    w = world()
    w.add_finding(disease="Periapical Lesion")
    _, rx = await _proposal(w)
    await w.workflow.decide_prescription(rx.id, PrescriptionDecisionRequest(decision="rejected"))
    assert w.feedback.rows[-1].correction_type == "drug_override"
    assert w.feedback.rows[-1].dentist_corrected_data["decision"] == "rejected"


async def test_override_of_a_contraindication_is_logged_with_the_reason(world):
    w = world(make_patient(allergies=["penicillin"]))
    w.add_finding(disease="Periapical Lesion")
    _, rx = await _proposal(w)               # clindamycin, warning R-18
    await w.workflow.decide_prescription(
        rx.id, PrescriptionDecisionRequest(decision="modified", drug_name="Amoxicillin", dosage="500 mg",
                                           override_reason="Allergy was a childhood rash; tolerated since"))
    [log] = w.feedback.rows
    assert log.correction_type == "drug_override"
    assert log.dentist_corrected_data["override_reason"].startswith("Allergy was")
    assert "R-01" in log.dentist_corrected_data["rule_ids"]
    assert log.notes == log.dentist_corrected_data["override_reason"]


async def test_acknowledging_warnings_without_changes_is_not_a_correction(world):
    w = world(make_patient(allergies=["penicillin"]))
    w.add_finding(disease="Periapical Lesion")
    _, rx = await _proposal(w)
    await w.workflow.decide_prescription(
        rx.id, PrescriptionDecisionRequest(decision="accepted", acknowledge_warnings=True))
    assert w.feedback.rows == []


async def test_cancelling_or_rewriting_a_treatment_is_logged(world):
    w = world()
    w.add_finding(disease="Caries")
    res = await w.workflow.generate_for_scan(w.scan_id, RecommendationRequest())
    t = res.plans[0].treatment
    await w.workflow.decide_treatment(t.id, TreatmentDecisionRequest(decision="cancelled", dentist_notes="patient declined"))
    [log] = w.feedback.rows
    assert (log.stage, log.correction_type) == ("treatment_recommendation", "custom_note")
    assert log.ai_original_data["status"] == "proposed" and log.dentist_corrected_data["status"] == "cancelled"
    assert log.notes == "patient declined"


async def test_confirming_a_treatment_unchanged_logs_nothing(world):
    w = world()
    w.add_finding(disease="Caries")
    t = (await w.workflow.generate_for_scan(w.scan_id, RecommendationRequest())).plans[0].treatment
    await w.workflow.decide_treatment(t.id, TreatmentDecisionRequest(decision="confirmed"))
    assert w.feedback.rows == []


# --- ledger reads -------------------------------------------------------------------

async def test_list_and_summary_reflect_the_ledger(world):
    w = world()
    a = w.add_finding(disease="Caries", review_status="pending")
    b = w.add_finding(fdi="46", disease="Caries", review_status="pending")
    await w.workflow.review_finding(review(a, "rejected"))
    await w.workflow.review_finding(review(b, "modified", confirmed_disease="Deep Caries"))
    assert (await w.workflow.list_feedback(correction_type="false_positive")).total == 1
    summary = await w.workflow.feedback_summary(scan_id=w.scan_id)
    assert summary.total == 2 and summary.by_stage == {"finding_detection": 2}
    assert summary.by_correction_type == {"false_positive": 1, "misclassification": 1}
    assert summarize([]).total == 0


def test_only_detection_rows_are_forwarded_to_ml():
    report = MissedFindingReport(scan_id=uuid4(), tooth_fdi="11", disease="Caries")
    assert ml_finding_feedback(missed_finding_feedback(report))["tooth"] == 1


async def test_without_a_configured_ledger_reads_are_refused_and_decisions_still_work(world):
    w = world()
    w.workflow.feedback = None
    f = w.add_finding(review_status="pending")
    assert (await w.workflow.review_finding(review(f, "rejected"))).review_status == "rejected"
    from app.domain.errors import RuleViolationError
    with pytest.raises(RuleViolationError):
        await w.workflow.list_feedback()


# --- HTTP -----------------------------------------------------------------------------

@pytest.fixture
def api(world):
    w = world()
    yield w, http_client(w)


async def test_feedback_over_http(api):
    w, client = api
    f = w.add_finding(disease="Caries", review_status="pending")
    res = await client.post("/api/v1/findings/review", json={"finding_id": str(f.id), "review_status": "rejected"})
    assert res.status_code == 200
    miss = await client.post("/api/v1/feedback/missed-findings",
                             json={"scan_id": str(w.scan_id), "tooth_fdi": "28", "disease": "Impacted"})
    assert miss.status_code == 201 and miss.json()["correction_type"] == "false_negative"

    listing = (await client.get("/api/v1/feedback", params={"scan_id": str(w.scan_id)})).json()
    assert listing["total"] == 2
    assert (await client.get("/api/v1/feedback", params={"scan_id": str(w.scan_id), "stage": "prescription_dosing"})).json()["total"] == 0
    assert (await client.get("/api/v1/feedback")).status_code == 422          # the ledger is read per scan
    summary = (await client.get("/api/v1/feedback/summary", params={"scan_id": str(w.scan_id)})).json()
    assert summary["by_correction_type"] == {"false_positive": 1, "false_negative": 1}


async def test_http_validation_and_not_found(api):
    w, client = api
    assert (await client.post("/api/v1/findings/review",
                              json={"finding_id": str(uuid4()), "review_status": "rejected"})).status_code == 404
    assert (await client.post("/api/v1/feedback/missed-findings",
                              json={"scan_id": str(w.scan_id), "tooth_fdi": "99", "disease": "Caries"})).status_code == 422
    assert (await client.post("/api/v1/feedback/missed-findings",
                              json={"scan_id": str(uuid4()), "tooth_fdi": "11", "disease": "Caries"})).status_code == 404
    assert (await client.get("/api/v1/feedback", params={"scan_id": str(w.scan_id), "stage": "bogus"})).status_code == 422
