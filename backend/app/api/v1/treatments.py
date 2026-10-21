"""
DentalAI - Treatment API Endpoints
Review and decide proposed treatments (Step 5).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist, get_workflow
from app.services.access import AccessService
from app.domain.treatment import (
    Treatment, TreatmentDecisionRequest, TreatmentListResponse, TreatmentManualCreate, TreatmentWithPrescriptions,
)
from app.services.clinical_workflow import ClinicalWorkflowService

router = APIRouter(prefix="/treatments", tags=["treatments"])


@router.post("", response_model=Treatment, status_code=201)
async def create_treatment(
    request: TreatmentManualCreate, workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Dentist-authored treatment for a scan (optionally linked to a finding).

    It is the dentist's own decision, so it is stored as `confirmed`. Use the engine's
    `POST /recommendations/scans/{scan_id}` for AI-assisted proposals instead.
    """
    await access.scan(request.scan_id, dentist)
    request.dentist_id = dentist.id
    return await workflow.create_treatment(request)


@router.get("", response_model=TreatmentListResponse)
async def list_treatments(
    scan_id: Optional[UUID] = Query(None, description="Filter by scan"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    status: Optional[str] = Query(
        None, pattern="^(proposed|confirmed|modified|in_progress|completed|cancelled)$"),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """List treatments with their candidate prescriptions."""
    if not scan_id and not patient_id:
        raise HTTPException(status_code=400, detail="Either patient_id or scan_id must be provided")
    if scan_id:
        await access.scan(scan_id, dentist)
    if patient_id:
        await access.patient(patient_id, dentist)

    treatments = await workflow.list_treatments(scan_id=scan_id, patient_id=patient_id, status=status)
    return TreatmentListResponse(treatments=treatments, total=len(treatments))


@router.get("/{treatment_id}", response_model=TreatmentWithPrescriptions)
async def get_treatment(
    treatment_id: UUID,
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Retrieve a treatment with its prescriptions."""
    await access.treatment(treatment_id, dentist)
    return await workflow.get_treatment(treatment_id)


@router.post("/{treatment_id}/decision", response_model=Treatment)
async def decide_treatment(
    treatment_id: UUID,
    request: TreatmentDecisionRequest,
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Dentist decision on a proposed treatment.

    **Step 5 in Clinical Loop**: confirm, modify (category/description), or cancel.
    Decisions are final: a decided treatment returns 409.
    """
    await access.treatment(treatment_id, dentist)
    request.dentist_id = dentist.id
    return await workflow.decide_treatment(treatment_id, request)
