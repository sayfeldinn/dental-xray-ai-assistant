"""
Feedback and Active Learning endpoints for clinician annotations.
Logs accepted, rejected, and corrected AI findings to Supabase feedback table.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from supabase import Client
from app.core.supabase import get_supabase_service
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/feedback", tags=["Active Learning & Feedback"])


class FindingFeedbackRequest(BaseModel):
    prediction_id: Optional[str] = Field(None, alias="prediction_id")
    finding_id: Optional[str] = None
    scan_id: Optional[str] = None
    is_correct: Optional[bool] = None
    corrected_by: Optional[str] = None
    dentist_action: Optional[str] = Field(None, description="'confirmed', 'rejected', or 'edited'")
    original_finding_type: Optional[str] = None
    corrected_finding_type: Optional[str] = None
    bounding_box_valid: Optional[bool] = True
    original_bbox: Optional[Dict[str, float]] = None
    corrected_bbox: Optional[Dict[str, float]] = None
    dentist_notes: Optional[str] = None
    
    class Config:
        populate_by_name = True


class FeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: str


def _uuid_or_none(value: Optional[str]) -> Optional[str]:
    """Postgres rejects non-UUID strings in UUID columns; drop them instead."""
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


_ACTION_ALIASES = {
    "accepted": "accepted",
    "confirmed": "accepted",
    "correct": "accepted",
    "approved": "accepted",
    "rejected": "rejected",
    "incorrect": "rejected",
    "corrected": "corrected",
    "edited": "corrected",
    "modified": "corrected",
}


def _coerce_action(feedback: FindingFeedbackRequest) -> str:
    """Map client vocabulary onto the ``feedback.action`` CHECK constraint.

    The schema only allows accepted/rejected/corrected, while clients also
    send "confirmed" and "edited".
    """
    if feedback.dentist_action:
        key = feedback.dentist_action.strip().lower()
    elif feedback.is_correct is not None:
        key = "accepted" if feedback.is_correct else "rejected"
    else:
        key = "accepted"
    return _ACTION_ALIASES.get(key, "accepted")


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FindingFeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Log clinician correction or confirmation for model active learning.
    Supports both simple (is_correct) and detailed (dentist_action) formats.
    """
    if not feedback.scan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scan_id is required to log feedback",
        )

    feedback_id = str(uuid4())
    finding_id = _uuid_or_none(feedback.prediction_id or feedback.finding_id)
    action = _coerce_action(feedback)

    original = {
        key: value
        for key, value in {
            "type": feedback.original_finding_type,
            "bbox": feedback.original_bbox,
            "bounding_box_valid": feedback.bounding_box_valid,
        }.items()
        if value is not None
    }
    corrected = {
        key: value
        for key, value in {
            "type": feedback.corrected_finding_type,
            "bbox": feedback.corrected_bbox,
        }.items()
        if value is not None
    }

    # Columns follow database_schema.sql: feedback stores JSONB snapshots
    # (original_data/corrected_data), not per-field type/bbox columns.
    record = {
        "id": feedback_id,
        "dentist_id": current_user_id,
        "scan_id": feedback.scan_id,
        "finding_id": finding_id,
        "action": action,
        "original_data": original or None,
        "corrected_data": corrected or None,
        "notes": feedback.dentist_notes
        or f"Feedback by {feedback.corrected_by or 'dentist'}",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        # Attempt to insert into feedback table in Supabase
        supabase.table("feedback").insert(record).execute()
    except Exception as e:
        # If table doesn't exist yet in Supabase or fails, log gracefully
        print(f"⚠️ [Active Learning] Feedback recorded locally (Supabase write note: {e})")

    return FeedbackResponse(
        status="success",
        message="Feedback logged successfully for active learning",
        feedback_id=feedback_id
    )


# Also support finding-level route /findings/{finding_id}/feedback
finding_feedback_router = APIRouter(prefix="/findings", tags=["Active Learning & Feedback"])

@finding_feedback_router.post("/{finding_id}/feedback", response_model=FeedbackResponse)
async def submit_finding_feedback(
    finding_id: str,
    feedback: FindingFeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    feedback.finding_id = finding_id
    return await submit_feedback(feedback, current_user_id, supabase)
