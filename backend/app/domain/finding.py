"""
DentalAI - Finding Domain Models
Individual tooth pathology detections with dentist validation.
"""

from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from .base import BaseEntity, TimestampedEntity, IdentifiedEntity


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
    """Schema for updating finding (dentist review)."""
    
    review_status: Optional[str] = Field(None, pattern="^(pending|confirmed|rejected|modified)$")
    confirmed_disease: Optional[str] = Field(None, max_length=50)
    dentist_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None


class Finding(FindingBase, IdentifiedEntity, TimestampedEntity):
    """Complete finding record from database."""
    
    dentist_id: Optional[UUID] = None
    review_status: str = Field(default="pending")
    confirmed_disease: Optional[str] = None
    dentist_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None


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
