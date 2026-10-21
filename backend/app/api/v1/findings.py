"""
DentalAI - Finding API Endpoints
Tooth pathology findings review and validation (Step 3).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist, get_workflow
from app.domain.finding import Finding, FindingUpdate, FindingListResponse, FindingReviewRequest
from app.services.access import AccessService
from app.services.clinical_workflow import ClinicalWorkflowService
from app.services.supabase_client import finding_service

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/{finding_id}", response_model=Finding)
async def get_finding(
    finding_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Retrieve a finding by ID."""
    return await access.finding(finding_id, dentist)


@router.get("", response_model=FindingListResponse)
async def list_findings(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    scan_id: Optional[UUID] = Query(None, description="Filter by scan"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """List findings of one scan or one patient."""
    if scan_id:
        await access.scan(scan_id, dentist)
        findings = await finding_service.list_findings_by_scan(scan_id)
    elif patient_id:
        await access.patient(patient_id, dentist)
        findings = await finding_service.list_findings_by_patient(patient_id=patient_id, review_status=review_status)
    else:
        raise HTTPException(status_code=400, detail="Either patient_id or scan_id must be provided")
    return FindingListResponse(findings=findings, total=len(findings))


@router.put("/{finding_id}", response_model=Finding)
async def update_finding(
    finding_id: UUID,
    finding_data: FindingUpdate,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Update a finding's dentist notes.

    Review decisions (confirm / reject / modify) are intentionally **not** allowed here: they
    must go through `POST /findings/review`, which enforces the clinical gate and writes the
    feedback ledger (Step 6). This prevents unaudited review changes.
    """
    await access.finding(finding_id, dentist)
    finding = await finding_service.update_finding(finding_id, finding_data)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("/review", response_model=Finding)
async def review_finding(
    review_request: FindingReviewRequest,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """
    Dentist review of an AI-detected finding.

    **Step 3 in Clinical Loop**: Dentist Finding Validation

    The dentist can:
    - **Confirm**: Accept AI detection as-is
    - **Reject**: Mark as false positive (logged to the feedback ledger)
    - **Modify**: Change disease classification (logged as a misclassification)
    """
    await access.finding(review_request.finding_id, dentist)
    review_request.dentist_id = dentist.id
    return await workflow.review_finding(review_request)


@router.get("/scan/{scan_id}/confirmed", response_model=FindingListResponse)
async def get_confirmed_findings(
    scan_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Get dentist-validated (confirmed or modified) findings for a scan.

    **Step 3→4 Transition**: Retrieve validated findings for treatment recommendations.
    """
    await access.scan(scan_id, dentist)
    findings = await finding_service.get_confirmed_findings(scan_id)
    return FindingListResponse(findings=findings, total=len(findings))
