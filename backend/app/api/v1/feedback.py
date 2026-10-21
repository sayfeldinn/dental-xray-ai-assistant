"""
DentalAI - Feedback API Endpoints
Step 6: the append-only ledger of dentist corrections of the AI.
Rows are written automatically by finding reviews and treatment/prescription decisions;
the only direct write is reporting a lesion the AI missed.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist, get_workflow
from app.services.access import AccessService
from app.domain.feedback import (
    CorrectionType, FeedbackListResponse, FeedbackLog, FeedbackStage, FeedbackSummary, MissedFindingReport,
)
from app.services.clinical_workflow import ClinicalWorkflowService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    scan_id: UUID = Query(..., description="Scan whose ledger to read"),
    stage: Optional[FeedbackStage] = Query(None),
    correction_type: Optional[CorrectionType] = Query(None),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """One scan's corrections ledger, newest first."""
    await access.scan(scan_id, dentist)
    return await workflow.list_feedback(scan_id=scan_id, stage=stage, correction_type=correction_type)


@router.get("/summary", response_model=FeedbackSummary)
async def feedback_summary(
    scan_id: UUID = Query(..., description="Scan to summarise"),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Counts of one scan's corrections by stage and type."""
    await access.scan(scan_id, dentist)
    return await workflow.feedback_summary(scan_id=scan_id)


@router.post("/missed-findings", response_model=FeedbackLog, status_code=201)
async def report_missed_finding(
    report: MissedFindingReport, workflow: ClinicalWorkflowService = Depends(get_workflow),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Report a lesion the AI did not flag (false negative). Logged to the ledger and forwarded to the
    ML service's retraining queue. It does not create a finding: add a treatment for it with `POST /treatments`.
    """
    await access.scan(report.scan_id, dentist)
    report.dentist_id = dentist.id
    return await workflow.report_missed_finding(report)
