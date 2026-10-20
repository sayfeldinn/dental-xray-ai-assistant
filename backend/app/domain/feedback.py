"""
DentalAI - Feedback Domain Models (Step 6)
Append-only ledger of where the dentist departed from what the AI proposed.
"""

import re
from pydantic import Field, field_validator
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
from uuid import UUID
from .base import BaseEntity, IdentifiedEntity
from .finding import DISEASE_LABELS

# Mirror the CHECK constraints in supabase/schema.sql (clinical_feedback_logs).
FeedbackStage = Literal["finding_detection", "treatment_recommendation", "prescription_dosing"]
CorrectionType = Literal[
    "false_positive", "false_negative", "misclassification", "drug_override", "dosage_adjusted", "custom_note"
]

FDI_PATTERN = re.compile(r"^[1-4][1-8]$")


class FeedbackLogCreate(BaseEntity):
    """One ledger row, built by services/feedback/builder.py."""

    scan_id: UUID
    stage: FeedbackStage
    correction_type: CorrectionType
    ai_original_data: Dict[str, Any]
    dentist_corrected_data: Dict[str, Any]
    notes: Optional[str] = None
    dentist_id: Optional[UUID] = None


class FeedbackLog(FeedbackLogCreate, IdentifiedEntity):
    created_at: datetime


class MissedFindingReport(BaseEntity):
    """The dentist saw a lesion the model did not flag (a false negative)."""

    scan_id: UUID
    tooth_fdi: str = Field(..., description="FDI notation, e.g. '36'")
    disease: str
    notes: Optional[str] = None
    dentist_id: Optional[UUID] = None

    @field_validator("tooth_fdi")
    @classmethod
    def _valid_fdi(cls, value: str) -> str:
        if not FDI_PATTERN.match(value):
            raise ValueError("tooth_fdi must be a permanent-tooth FDI code: quadrant 1-4 then tooth 1-8")
        return value

    @field_validator("disease")
    @classmethod
    def _valid_disease(cls, value: str) -> str:
        if value not in DISEASE_LABELS:
            raise ValueError(f"disease must be one of {', '.join(DISEASE_LABELS)}")
        return value


class FeedbackListResponse(BaseEntity):
    logs: List[FeedbackLog]
    total: int


class FeedbackSummary(BaseEntity):
    """Counts the review UI and the retraining queue read; computed from the ledger, never stored."""

    total: int
    by_stage: Dict[str, int]
    by_correction_type: Dict[str, int]
