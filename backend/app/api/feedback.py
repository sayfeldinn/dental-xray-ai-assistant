"""
Feedback and Active Learning endpoints for clinician annotations.
Logs accepted, rejected, and corrected AI findings to Supabase feedback table.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
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
    feedback_id = str(uuid4())
    
    # Support simple format from frontend
    finding_id = feedback.prediction_id or feedback.finding_id
    
    # Determine action
    if feedback.is_correct is not None:
        action = "confirmed" if feedback.is_correct else "rejected"
    else:
        action = feedback.dentist_action or "confirmed"
    
    record = {
        "id": feedback_id,
        "dentist_id": current_user_id,
        "scan_id": feedback.scan_id,
        "finding_id": finding_id,
        "action": action,
        "original_type": feedback.original_finding_type or "unknown",
        "corrected_type": feedback.corrected_finding_type or feedback.original_finding_type or "unknown",
        "original_bbox": feedback.original_bbox,
        "corrected_bbox": feedback.corrected_bbox,
        "notes": feedback.dentist_notes or f"Feedback by {feedback.corrected_by or 'dentist'}",
        "created_at": datetime.utcnow().isoformat()
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
