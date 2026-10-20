"""
DentalAI - Finding API Endpoints
Tooth pathology findings review and validation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.domain.finding import (
    Finding,
    FindingUpdate,
    FindingListResponse,
    FindingReviewRequest
)
from app.api.deps import get_workflow
from app.services.clinical_workflow import ClinicalWorkflowService
from app.services.supabase_client import finding_service

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/{finding_id}", response_model=Finding)
async def get_finding(finding_id: UUID):
    """
    Retrieve a finding by ID.
    """
    finding = await finding_service.get_finding(finding_id)
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return finding


@router.get("", response_model=FindingListResponse)
async def list_findings(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    scan_id: Optional[UUID] = Query(None, description="Filter by scan"),
    review_status: Optional[str] = Query(None, description="Filter by review status")
):
    """
    List findings with optional filtering.
    """
    if scan_id:
        findings = await finding_service.list_findings_by_scan(scan_id)
    elif patient_id:
        findings = await finding_service.list_findings_by_patient(
            patient_id=patient_id,
            review_status=review_status
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either patient_id or scan_id must be provided"
        )
    
    return FindingListResponse(
        findings=findings,
        total=len(findings)
    )


@router.put("/{finding_id}", response_model=Finding)
async def update_finding(finding_id: UUID, finding_data: FindingUpdate):
    """
    Update finding record.
    """
    finding = await finding_service.update_finding(finding_id, finding_data)
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return finding


@router.post("/review", response_model=Finding)
async def review_finding(
    review_request: FindingReviewRequest, workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """
    Dentist review of an AI-detected finding.

    **Step 3 in Clinical Loop**: Dentist Finding Validation

    The dentist can:
    - **Confirm**: Accept AI detection as-is
    - **Reject**: Mark as false positive (logged to the feedback ledger)
    - **Modify**: Change disease classification (logged as a misclassification)
    """
    return await workflow.review_finding(review_request)


@router.get("/scan/{scan_id}/confirmed", response_model=FindingListResponse)
async def get_confirmed_findings(scan_id: UUID):
    """
    Get dentist-validated (confirmed or modified) findings for a scan.
    
    **Step 3→4 Transition**: Retrieve validated findings for treatment recommendations.
    """
    findings = await finding_service.get_confirmed_findings(scan_id)
    
    return FindingListResponse(
        findings=findings,
        total=len(findings)
    )
