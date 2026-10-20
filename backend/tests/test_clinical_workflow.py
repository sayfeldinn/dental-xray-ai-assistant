"""Workflow service on in-memory fakes: persistence rules and the Step 5 decision policy."""

import pytest

from app.domain.errors import ConflictError, NotFoundError, RuleViolationError
from app.domain.prescription import PrescriptionCheckRequest, PrescriptionDecisionRequest
from app.domain.recommendation import ClinicalContext, RecommendationRequest
from app.domain.treatment import TreatmentDecisionRequest
from tests.conftest import make_patient

INFECTION = RecommendationRequest(clinical_context=ClinicalContext(active_infection=True))


async def generated(world, request=INFECTION, disease="Periapical Lesion"):
    world.add_finding(disease=disease)
    return await world.workflow.generate_for_scan(world.scan_id, request)


# --- generation ----------------------------------------------------------------------------

async def test_generate_persists_proposed_treatment_and_prescription(world):
    w = world()
    response = await generated(w)
    (plan,) = response.plans
    assert plan.treatment.status == "proposed" and plan.treatment.requires_prescription
    (rx,) = plan.prescriptions
    assert rx.drug_name == "Amoxicillin" and rx.dentist_status == "proposed"
    assert "Pending Dentist Validation" in response.disclaimer


async def test_generate_is_idempotent_for_untouched_proposals(world):
    w = world()
    await generated(w)
    second = await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    assert len(w.treatments.rows) == 1 and len(w.prescriptions.rows) == 1
    assert second.skipped_finding_ids == []


async def test_regenerate_drops_proposals_for_findings_no_longer_valid(world):
    w = world()
    w.add_finding(disease="Caries", fdi="16")
    stale = w.add_finding(disease="Periapical Lesion", fdi="36")
    await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    stale.review_status = "rejected"
    await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    assert [t.finding_id for t in w.treatments.rows.values() if t.finding_id == stale.id] == []
    assert len(w.treatments.rows) == 1


async def test_dentist_decisions_survive_regeneration(world):
    w = world()
    (plan,) = (await generated(w)).plans
    await w.workflow.decide_prescription(plan.prescriptions[0].id, PrescriptionDecisionRequest(decision="accepted"))
    again = await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    assert again.plans == [] and again.skipped_finding_ids == [plan.treatment.finding_id]
    assert next(iter(w.prescriptions.rows.values())).dentist_status == "accepted"


async def test_confirmed_treatment_is_not_overwritten(world):
    w = world()
    (plan,) = (await generated(w)).plans
    await w.workflow.decide_treatment(plan.treatment.id, TreatmentDecisionRequest(decision="confirmed"))
    again = await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    assert again.plans == [] and len(again.skipped_finding_ids) == 1


async def test_generate_requires_validated_findings(world):
    w = world()
    w.add_finding(review_status="pending")
    with pytest.raises(ConflictError):
        await w.workflow.generate_for_scan(w.scan_id, INFECTION)


async def test_modified_findings_feed_the_engine(world):
    w = world()
    w.add_finding(disease="Caries", review_status="modified", confirmed_disease="Periapical Lesion")
    (plan,) = (await w.workflow.generate_for_scan(w.scan_id, INFECTION)).plans
    assert plan.treatment.treatment_category == "endodontic"


async def test_generate_unknown_scan(world):
    from uuid import uuid4
    with pytest.raises(NotFoundError):
        await world().workflow.generate_for_scan(uuid4(), INFECTION)


async def test_partial_failure_leaves_no_half_written_plan(world):
    w = world()
    w.add_finding()
    async def boom(data):
        raise RuntimeError("db down")
    w.prescriptions.create_prescription = boom
    with pytest.raises(RuntimeError):
        await w.workflow.generate_for_scan(w.scan_id, INFECTION)
    assert w.treatments.rows == {}


# --- prescription decisions ---------------------------------------------------------------------

async def test_clear_prescription_can_be_accepted_and_is_timestamped(world):
    w = world()
    (plan,) = (await generated(w)).plans
    rx = await w.workflow.decide_prescription(
        plan.prescriptions[0].id, PrescriptionDecisionRequest(decision="accepted"))
    assert rx.dentist_status == "accepted" and rx.prescribed_at is not None


async def test_warning_needs_acknowledgement(world):
    w = world(make_patient(allergies=["penicillin"]))
    (plan,) = (await generated(w)).plans
    rx_id = plan.prescriptions[0].id   # Clindamycin with substitution notice
    with pytest.raises(RuleViolationError, match="acknowledge_warnings"):
        await w.workflow.decide_prescription(rx_id, PrescriptionDecisionRequest(decision="accepted"))
    rx = await w.workflow.decide_prescription(
        rx_id, PrescriptionDecisionRequest(decision="accepted", acknowledge_warnings=True))
    assert rx.dentist_status == "accepted"


async def test_stale_proposal_is_rechecked_against_the_current_patient_record(world):
    w = world()
    (plan,) = (await generated(w)).plans   # Amoxicillin, clear at generation time
    w.patient.allergies.append("penicillin")   # allergy recorded afterwards
    rx_id = plan.prescriptions[0].id
    with pytest.raises(RuleViolationError, match="override_reason"):
        await w.workflow.decide_prescription(rx_id, PrescriptionDecisionRequest(decision="accepted"))
    with pytest.raises(RuleViolationError):   # whitespace is not a reason
        await w.workflow.decide_prescription(
            rx_id, PrescriptionDecisionRequest(decision="accepted", override_reason="   "))
    rx = await w.workflow.decide_prescription(
        rx_id, PrescriptionDecisionRequest(decision="accepted", override_reason="Tolerated before, allergist cleared"))
    assert rx.contraindication_status == "contraindicated"
    assert rx.dentist_override_reason == "Tolerated before, allergist cleared"


async def test_modifying_to_a_safe_drug_needs_no_override(world):
    w = world(make_patient(allergies=["penicillin"], conditions=[]))
    (plan,) = (await generated(w)).plans
    rx = await w.workflow.decide_prescription(
        plan.prescriptions[0].id,
        PrescriptionDecisionRequest(decision="modified", drug_name="metronidazole", dosage="500 mg",
                                    frequency="every 8 hours", duration="7 days", acknowledge_warnings=True))
    assert rx.dentist_status == "modified" and rx.drug_name == "Metronidazole"
    assert rx.contraindication_status == "clear"


async def test_modified_dose_is_checked_for_children(world):
    w = world(make_patient(age=6, weight_kg=18))
    w.add_finding(disease="Caries")
    (plan,) = (await w.workflow.generate_for_scan(
        w.scan_id, RecommendationRequest(clinical_context=ClinicalContext(pain=True)))).plans
    rx_id = plan.prescriptions[0].id
    with pytest.raises(RuleViolationError, match="override_reason"):
        await w.workflow.decide_prescription(rx_id, PrescriptionDecisionRequest(decision="modified", dosage="400 mg"))


async def test_rejection_needs_no_justification_and_decisions_are_final(world):
    w = world()
    (plan,) = (await generated(w)).plans
    rx_id = plan.prescriptions[0].id
    rx = await w.workflow.decide_prescription(rx_id, PrescriptionDecisionRequest(decision="rejected"))
    assert rx.dentist_status == "rejected" and rx.prescribed_at is None
    with pytest.raises(ConflictError):
        await w.workflow.decide_prescription(rx_id, PrescriptionDecisionRequest(decision="accepted"))


async def test_cancelled_treatment_blocks_prescription_decisions(world):
    w = world()
    (plan,) = (await generated(w)).plans
    await w.workflow.decide_treatment(plan.treatment.id, TreatmentDecisionRequest(decision="cancelled"))
    with pytest.raises(ConflictError):
        await w.workflow.decide_prescription(plan.prescriptions[0].id, PrescriptionDecisionRequest(decision="accepted"))


def test_decision_request_validation():
    with pytest.raises(ValueError):
        PrescriptionDecisionRequest(decision="modified")                     # nothing edited
    with pytest.raises(ValueError):
        PrescriptionDecisionRequest(decision="accepted", dosage="500 mg")    # edits without 'modified'
    with pytest.raises(ValueError):
        TreatmentDecisionRequest(decision="modified")


# --- treatment decisions / reads ---------------------------------------------------------------------

async def test_treatment_confirm_modify_and_finality(world):
    w = world()
    (plan,) = (await generated(w)).plans
    t = await w.workflow.decide_treatment(
        plan.treatment.id,
        TreatmentDecisionRequest(decision="modified", treatment_category="surgical_extraction", dentist_notes="Extract"))
    assert t.status == "modified" and t.treatment_category == "surgical_extraction" and t.confirmed_at
    with pytest.raises(ConflictError):
        await w.workflow.decide_treatment(plan.treatment.id, TreatmentDecisionRequest(decision="confirmed"))


async def test_list_and_get_attach_prescriptions(world):
    w = world()
    (plan,) = (await generated(w)).plans
    (listed,) = await w.workflow.list_treatments(scan_id=w.scan_id)
    assert [p.id for p in listed.prescriptions] == [plan.prescriptions[0].id]
    assert (await w.workflow.get_treatment(plan.treatment.id)).prescriptions


async def test_check_prescription_is_stateless(world):
    w = world(make_patient(medications=["warfarin"]))
    result = await w.workflow.check_prescription(PrescriptionCheckRequest(
        patient_id=w.patient.id, drug_name="Ibuprofen", indication_type="pain_management", dosage="400 mg"))
    assert result.status == "contraindicated" and w.prescriptions.rows == {}


# --- dentist-authored treatments and prescriptions ----------------------------------------------------

async def test_manual_treatment_is_stored_confirmed_and_linked_to_the_patient(world):
    from app.domain.treatment import TreatmentManualCreate
    w = world()
    finding = w.add_finding(disease="Caries", fdi="16")
    t = await w.workflow.create_treatment(TreatmentManualCreate(
        scan_id=w.scan_id, finding_id=finding.id, treatment_category="restorative", description="Composite filling"))
    assert t.status == "confirmed" and t.confirmed_at and t.patient_id == w.patient.id


async def test_manual_treatment_rejects_a_finding_from_another_scan(world):
    from app.domain.treatment import TreatmentManualCreate
    from tests.conftest import make_finding
    w = world()
    other = make_finding()
    w.findings.rows.append(other)
    with pytest.raises(RuleViolationError):
        await w.workflow.create_treatment(TreatmentManualCreate(
            scan_id=w.scan_id, finding_id=other.id, treatment_category="restorative", description="x"))


async def test_manual_prescription_is_checked_and_still_needs_a_decision(world):
    from app.domain.prescription import PrescriptionManualCreate
    from app.domain.treatment import TreatmentManualCreate
    w = world(make_patient(medications=["warfarin"]))
    t = await w.workflow.create_treatment(TreatmentManualCreate(
        scan_id=w.scan_id, treatment_category="surgical_extraction", description="Extraction"))
    rx = await w.workflow.create_prescription(PrescriptionManualCreate(
        treatment_id=t.id, drug_name="ibuprofen", dosage="400 mg", frequency="every 6 hours",
        duration="3 days", indication_type="pain_management"))
    assert rx.drug_name == "Ibuprofen" and rx.dentist_status == "proposed"
    assert rx.contraindication_status == "contraindicated"
    assert w.treatments.rows[t.id].requires_prescription
    with pytest.raises(RuleViolationError):   # same gate as engine proposals
        await w.workflow.decide_prescription(rx.id, PrescriptionDecisionRequest(decision="accepted"))


async def test_manual_prescription_needs_a_decided_treatment(world):
    from app.domain.prescription import PrescriptionManualCreate
    w = world()
    (plan,) = (await generated(w)).plans   # still 'proposed': regeneration would erase a manual prescription
    with pytest.raises(ConflictError):
        await w.workflow.create_prescription(PrescriptionManualCreate(
            treatment_id=plan.treatment.id, drug_name="Paracetamol", dosage="500 mg", frequency="every 6 hours",
            duration="3 days", indication_type="pain_management"))


async def test_modified_dose_is_checked_against_the_daily_limit(world):
    w = world()
    w.add_finding(disease="Caries")
    (plan,) = (await w.workflow.generate_for_scan(
        w.scan_id, RecommendationRequest(clinical_context=ClinicalContext(pain=True)))).plans
    with pytest.raises(RuleViolationError, match="override_reason"):
        await w.workflow.decide_prescription(plan.prescriptions[0].id, PrescriptionDecisionRequest(
            decision="modified", dosage="800 mg", frequency="every 4 hours"))
