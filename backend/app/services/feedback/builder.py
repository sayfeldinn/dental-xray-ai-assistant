"""
Pure feedback builders: given the state before and after a dentist decision, return the ledger row to
write, or None when the dentist simply accepted what the AI proposed (nothing to learn from or audit).

Only departures are logged because the table's correction_type has no 'accepted' value and a confirmation
carries no correction. No database, HTTP or clock access here.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from app.domain.feedback import FeedbackLogCreate, MissedFindingReport
from app.domain.finding import Finding
from app.domain.prescription import Prescription
from app.domain.treatment import Treatment

NO_DETECTION = "None"   # original_disease sent to the ML service for a lesion the model missed


def finding_feedback(
    before: Finding,
    review_status: str,
    confirmed_disease: Optional[str],
    notes: Optional[str],
    dentist_id: Optional[UUID],
) -> Optional[FeedbackLogCreate]:
    """Step 3: rejecting a detection is a false positive; relabelling it is a misclassification."""
    if review_status == "rejected":
        correction, corrected = "false_positive", {"disease": None, "review_status": "rejected"}
    elif review_status == "modified" and confirmed_disease and confirmed_disease != before.disease:
        correction, corrected = "misclassification", {"disease": confirmed_disease, "review_status": "modified"}
    else:
        return None
    return FeedbackLogCreate(
        scan_id=before.scan_id,
        stage="finding_detection",
        correction_type=correction,
        ai_original_data={
            "finding_id": str(before.id),
            "tooth_fdi": before.tooth_fdi,
            "disease": before.disease,
            "disease_confidence": before.disease_confidence,
            "box": before.box,
        },
        dentist_corrected_data={"tooth_fdi": before.tooth_fdi, **corrected},
        notes=notes,
        dentist_id=dentist_id,
    )


def missed_finding_feedback(report: MissedFindingReport) -> FeedbackLogCreate:
    """Step 3: the dentist found a lesion the model never flagged (false negative)."""
    return FeedbackLogCreate(
        scan_id=report.scan_id,
        stage="finding_detection",
        correction_type="false_negative",
        ai_original_data={"tooth_fdi": report.tooth_fdi, "disease": None, "detected": False},
        dentist_corrected_data={"tooth_fdi": report.tooth_fdi, "disease": report.disease},
        notes=report.notes,
        dentist_id=report.dentist_id,
    )


def treatment_feedback(
    before: Treatment, after: Treatment, dentist_id: Optional[UUID]
) -> Optional[FeedbackLogCreate]:
    """Step 5: a cancelled treatment, or one whose category or description the dentist changed."""
    changed = (before.treatment_category, before.description) != (after.treatment_category, after.description)
    if after.status != "cancelled" and not changed:
        return None
    return FeedbackLogCreate(
        scan_id=before.scan_id,
        stage="treatment_recommendation",
        correction_type="custom_note",
        ai_original_data=_treatment_snapshot(before),
        dentist_corrected_data=_treatment_snapshot(after),
        notes=after.dentist_notes,
        dentist_id=dentist_id,
    )


def prescription_feedback(
    before: Prescription, after: Prescription, scan_id: UUID, dentist_id: Optional[UUID]
) -> Optional[FeedbackLogCreate]:
    """
    Step 5: rejecting a drug, swapping it, or accepting it over a contraindication is a drug_override;
    changing only dose, frequency or duration is dosage_adjusted. Accepting unchanged (even with warnings
    acknowledged) is not a correction.
    """
    drug_changed = after.drug_name != before.drug_name
    regimen_changed = (before.dosage, before.frequency, before.duration) != (after.dosage, after.frequency, after.duration)
    if after.dentist_status == "rejected" or drug_changed or after.dentist_override_reason:
        correction = "drug_override"
    elif regimen_changed:
        correction = "dosage_adjusted"
    else:
        return None
    return FeedbackLogCreate(
        scan_id=scan_id,
        stage="prescription_dosing",
        correction_type=correction,
        ai_original_data=_prescription_snapshot(before),
        dentist_corrected_data={**_prescription_snapshot(after), "decision": after.dentist_status,
                                "override_reason": after.dentist_override_reason},
        notes=after.dentist_override_reason,
        dentist_id=dentist_id,
    )


def ml_finding_feedback(log: FeedbackLogCreate) -> Optional[Dict[str, Any]]:
    """
    Arguments for DentexClient.submit_feedback, or None when the row is not a detection correction.
    The ML service's CSV queue is keyed by image_id, which the backend sends as the scan id.
    """
    if log.stage != "finding_detection":
        return None
    fdi = log.ai_original_data["tooth_fdi"]
    corrected = log.dentist_corrected_data.get("disease")
    return {
        "image_id": str(log.scan_id),
        "quadrant": int(fdi[0]),
        "tooth": int(fdi[1]),
        "original_disease": log.ai_original_data.get("disease") or NO_DETECTION,
        "is_correct": False,
        "corrected_disease": corrected,
        "notes": log.notes,
    }


def _treatment_snapshot(t: Treatment) -> Dict[str, Any]:
    return {"treatment_category": t.treatment_category, "description": t.description, "status": t.status}


def _prescription_snapshot(p: Prescription) -> Dict[str, Any]:
    return {
        "drug_name": p.drug_name, "dosage": p.dosage, "frequency": p.frequency, "duration": p.duration,
        "contraindication_status": p.contraindication_status,
        "rule_ids": [w.rule_id for w in p.contraindication_warnings],
    }
