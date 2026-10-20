"""
DentalAI - Feedback API Endpoints
Step 6: the append-only ledger of dentist corrections of the AI.
Rows are written automatically by finding reviews and treatment/prescription decisions;
the only direct write is reporting a lesion the AI missed.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

from app.api.deps import get_workflow
from app.domain.feedback import (
    CorrectionType, FeedbackListResponse, FeedbackLog, FeedbackStage, FeedbackSummary, MissedFindingReport,
)
from app.services.clinical_workflow import ClinicalWorkflowService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    scan_id: Optional[UUID] = Query(None, description="Filter by scan"),
    stage: Optional[FeedbackStage] = Query(None),
    correction_type: Optional[CorrectionType] = Query(None),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """The corrections ledger, newest first."""
    return await workflow.list_feedback(scan_id=scan_id, stage=stage, correction_type=correction_type)


@router.get("/summary", response_model=FeedbackSummary)
async def feedback_summary(
    scan_id: Optional[UUID] = Query(None, description="Limit to one scan"),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """Counts of corrections by stage and type."""
    return await workflow.feedback_summary(scan_id=scan_id)


@router.post("/missed-findings", response_model=FeedbackLog, status_code=201)
async def report_missed_finding(
    report: MissedFindingReport, workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """
    Report a lesion the AI did not flag (false negative). Logged to the ledger and forwarded to the
    ML service's retraining queue. It does not create a finding: add a treatment for it with `POST /treatments`.
    """
    return await workflow.report_missed_finding(report)
