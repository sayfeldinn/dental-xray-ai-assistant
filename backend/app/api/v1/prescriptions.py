"""
DentalAI - Prescription API Endpoints
Safety checks and the dentist's prescription decision (Step 5).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist, get_workflow
from app.services.access import AccessService
from app.domain.prescription import (
    Prescription, PrescriptionCheckRequest, PrescriptionDecisionRequest,
    PrescriptionListResponse, PrescriptionManualCreate, SafetyCheckResult,
)
from app.services.clinical_workflow import ClinicalWorkflowService

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("", response_model=Prescription, status_code=201)
async def create_prescription(
    request: PrescriptionManualCreate, workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Dentist-authored prescription on a treatment that has already been confirmed or modified.

    The drug is safety-checked and saved as `proposed`: it still needs `POST /{id}/decision`
    (with `acknowledge_warnings` / `override_reason` when flagged) before it counts as prescribed.
    """
    await access.treatment(request.treatment_id, dentist)
    request.dentist_id = dentist.id
    return await workflow.create_prescription(request)


@router.get("", response_model=PrescriptionListResponse)
async def list_prescriptions(
    treatment_id: Optional[UUID] = Query(None, description="Filter by treatment"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """List prescriptions for a treatment or a patient."""
    if not treatment_id and not patient_id:
        raise HTTPException(status_code=400, detail="Either patient_id or treatment_id must be provided")
    if treatment_id:
        await access.treatment(treatment_id, dentist)
    if patient_id:
        await access.patient(patient_id, dentist)

    prescriptions = await workflow.list_prescriptions(treatment_id=treatment_id, patient_id=patient_id)
    return PrescriptionListResponse(prescriptions=prescriptions, total=len(prescriptions))


@router.post("/check", response_model=SafetyCheckResult)
async def check_prescription(
    request: PrescriptionCheckRequest,
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Stateless contraindication check of any drug/dose for a patient (nothing is saved).
    Use it while the dentist edits a proposal.
    """
    await access.patient(request.patient_id, dentist)
    return await workflow.check_prescription(request)


@router.get("/{prescription_id}", response_model=Prescription)
async def get_prescription(
    prescription_id: UUID,
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Retrieve a prescription by ID."""
    await access.prescription(prescription_id, dentist)
    return await workflow.get_prescription(prescription_id)


@router.post("/{prescription_id}/decision", response_model=Prescription)
async def decide_prescription(
    prescription_id: UUID,
    request: PrescriptionDecisionRequest,
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Dentist decision on a proposed prescription.

    **Step 5 in Clinical Loop**: accept, modify, or reject. The drug is re-checked against the
    patient's current record, and flagged drugs cannot be silently accepted:
    - status `warning` needs `acknowledge_warnings: true`
    - status `contraindicated` needs a written `override_reason`

    Decisions are final: a decided prescription returns 409.
    """
    await access.prescription(prescription_id, dentist)
    request.dentist_id = dentist.id
    return await workflow.decide_prescription(prescription_id, request)
