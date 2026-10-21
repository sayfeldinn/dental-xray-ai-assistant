"""
DentalAI - Finding Domain Models
Individual tooth pathology detections with dentist validation.
"""

from pydantic import Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from .base import BaseEntity, TimestampedEntity, IdentifiedEntity

# Pathology classes emitted by dentex_week3 (see docs/CLINICAL_GUIDELINES.md §1).
DISEASE_LABELS = ("Caries", "Deep Caries", "Periapical Lesion", "Impacted")


class FindingBase(BaseEntity):
    """Core finding fields."""
    
    scan_id: UUID
    patient_id: UUID
    quadrant: int = Field(..., ge=1, le=4, description="Quadrant 1-4")
    tooth_id: int = Field(..., ge=1, le=8, description="Tooth position 1-8")
    tooth_fdi: str = Field(..., max_length=10, description="FDI notation e.g. '18', '27'")
    disease: str = Field(..., max_length=50, description="Caries, Deep Caries, Periapical Lesion, Impacted")
    disease_confidence: float = Field(..., ge=0.0, le=1.0)
    tooth_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    association_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    box: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")


class FindingCreate(FindingBase):
    """Schema for creating a new finding."""
    
    dentist_id: Optional[UUID] = None


class FindingUpdate(BaseEntity):
    """
    Schema for a client-side finding update.

    Deliberately limited to `dentist_notes`. A review decision (review_status /
    confirmed_disease) must go through `POST /findings/review`, which enforces the clinical
    gate and writes the audit ledger row — letting clients set those fields here would allow a
    review to be changed without any audit trail.
    """

    dentist_notes: Optional[str] = None


class Finding(FindingBase, IdentifiedEntity, TimestampedEntity):
    """Complete finding record from database."""
    
    dentist_id: Optional[UUID] = None
    review_status: str = Field(default="pending")
    confirmed_disease: Optional[str] = None
    dentist_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None

    @property
    def effective_disease(self) -> str:
        """Disease label to act on: the dentist's correction wins over the AI's."""
        return self.confirmed_disease or self.disease


class FindingListResponse(BaseEntity):
    """List of findings for a scan."""
    
    findings: List[Finding]
    total: int


class FindingReviewRequest(BaseEntity):
    """Request to review a finding."""
    
    finding_id: UUID
    review_status: str = Field(..., pattern="^(confirmed|rejected|modified)$")
    confirmed_disease: Optional[str] = None
    dentist_notes: Optional[str] = None
    dentist_id: Optional[UUID] = None

    @model_validator(mode="after")
    def _check_disease_labels(self) -> "FindingReviewRequest":
        if self.review_status == "modified" and not self.confirmed_disease:
            raise ValueError("confirmed_disease is required when review_status is 'modified'")
        if self.confirmed_disease and self.confirmed_disease not in DISEASE_LABELS:
            raise ValueError(f"confirmed_disease must be one of {DISEASE_LABELS}")
        return self
