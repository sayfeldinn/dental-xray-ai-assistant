"""
Treatment plan endpoints.

The Treatment Confirmation screen posts the plan the dentist just approved:
one treatment row plus a prescription row per medication, with a
contraindication check recorded for each drug.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from supabase import Client

from app.core.supabase import get_supabase_service
from app.schemas.treatment import (
    PrescriptionResponse,
    TreatmentResponse,
    TreatmentStatusEnum,
)
from app.services.recommendation_engine import recommendation_engine
from app.utils.auth import get_current_user_id
from app.utils.records import require_patient, require_scan

router = APIRouter(prefix="/treatments", tags=["Treatments"])

# The web client labels its confirmation button "planned"; the schema only
# accepts the lifecycle states below, so aliases are normalised here rather
# than letting the insert violate its CHECK constraint.
_STATUS_ALIASES = {
    "planned": "confirmed",
    "accepted": "confirmed",
    "reviewed": "confirmed",
    "pending": "recommended",
    "proposed": "recommended",
}
_VALID_STATUSES = {status_enum.value for status_enum in TreatmentStatusEnum}


def map_treatment_status(raw: Optional[str]) -> str:
    """Normalise a client-supplied status onto a value the DB accepts."""
    if not raw:
        return TreatmentStatusEnum.RECOMMENDED.value
    key = str(raw).strip().lower()
    if key in _STATUS_ALIASES:
        return _STATUS_ALIASES[key]
    if key in _VALID_STATUSES:
        return key
    return TreatmentStatusEnum.RECOMMENDED.value


class MedicationItem(BaseModel):
    """One medication as sent by the Treatment Confirmation screen."""
    name: str = Field(..., min_length=1)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class TreatmentPlanRequest(BaseModel):
    """Payload the frontend posts for a confirmed treatment plan."""
    patient_id: str
    scan_id: Optional[str] = None
    finding_type: Optional[str] = None
    treatment_type: Optional[str] = None
    treatment_plan: str = Field(..., min_length=1)
    medications: List[MedicationItem] = Field(default_factory=list)
    status: Optional[str] = None
    notes: Optional[str] = None


class TreatmentCreatedResponse(TreatmentResponse):
    """Treatment response plus a non-fatal persistence warning."""
    warning: Optional[str] = None


def _iso_now() -> str:
    return datetime.utcnow().isoformat()


@router.post(
    "",
    response_model=TreatmentCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=TreatmentCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_treatment(
    payload: TreatmentPlanRequest,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service),
):
    """Create a confirmed treatment plan with its prescriptions."""
    patient = require_patient(supabase, payload.patient_id, current_user_id)
    if payload.scan_id:
        require_scan(supabase, payload.scan_id, current_user_id)

    now = _iso_now()
    treatment_row = {
        "patient_id": payload.patient_id,
        "dentist_id": current_user_id,
        "scan_id": payload.scan_id,
        "treatment_type": (payload.treatment_type or payload.finding_type or "other")[:255],
        "description": payload.treatment_plan,
        "status": map_treatment_status(payload.status),
        "notes": payload.notes,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = supabase.table("treatments").insert(treatment_row).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create treatment: {str(e)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create treatment record",
        )

    treatment = result.data[0]
    treatment_id = treatment["id"]
    warning = None

    if payload.medications:
        prescription_rows = _build_prescriptions(
            payload.medications, treatment_id, patient, now
        )
        try:
            inserted = (
                supabase.table("prescriptions").insert(prescription_rows).execute().data or []
            )
        except Exception as e:
            # The plan itself is saved; report the prescriptions failure instead
            # of failing a request the clinician is watching.
            inserted = []
            warning = f"prescriptions were not saved: {e}"
    else:
        inserted = []

    return TreatmentCreatedResponse(
        **treatment,
        prescriptions=[PrescriptionResponse(**row) for row in inserted],
        warning=warning,
    )


def _build_prescriptions(
    medications: List[MedicationItem],
    treatment_id: str,
    patient: dict,
    created_at: str,
) -> List[dict]:
    """Map medications onto ``prescriptions`` rows, checking each drug."""
    allergies = patient.get("allergies") or []
    current_medications = patient.get("current_medications") or []
    conditions = patient.get("medical_conditions") or []

    rows: List[dict] = []
    for med in medications:
        safety = recommendation_engine.check_prescription_safety(
            drug_name=med.name,
            patient_allergies=allergies,
            patient_medications=current_medications,
            patient_conditions=conditions,
        )
        rows.append(
            {
                "treatment_id": treatment_id,
                "drug_name": med.name,
                # The recommendation payload folds the frequency into
                # "dosage", so an unspecified frequency is defaulted rather
                # than left NULL (the column is NOT NULL).
                "dosage": (med.dosage or "as directed")[:100],
                "frequency": (med.frequency or "as directed")[:100],
                "duration": (med.duration or "as directed")[:100],
                "instructions": med.instructions,
                "contraindication_checked": True,
                "contraindication_warnings": safety.get("warnings") or [],
                "created_at": created_at,
            }
        )
    return rows
