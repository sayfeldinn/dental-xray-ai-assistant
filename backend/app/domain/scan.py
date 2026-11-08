"""
DentalAI - Scan Domain Models
Panoramic radiograph scans with AI inference results.
"""

from pydantic import Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from .base import BaseEntity, TimestampedEntity, IdentifiedEntity


class ScanBase(BaseEntity):
    """Core scan fields."""
    
    patient_id: UUID
    scan_type: str = Field(default="panoramic", max_length=50)
    image_url: str
    storage_path: Optional[str] = None
    status: str = Field(
        default="uploaded",
        pattern="^(uploaded|processing|analyzed|reviewed|failed)$"
    )
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    notes: Optional[str] = None


class ScanCreate(ScanBase):
    """Schema for creating a new scan record."""
    
    dentist_id: Optional[UUID] = None


class ScanUpdate(BaseEntity):
    """
    Schema for updating a scan record.

    Deliberately limited to `notes` and `status`. The AI outputs (`raw_ml_output`, `ai_report`)
    are excluded: they are written only by the ingestion service after a real model run, so a
    client cannot tamper with the stored model output.
    """

    status: Optional[str] = Field(None, pattern="^(uploaded|processing|analyzed|reviewed|failed)$")
    notes: Optional[str] = None


class Scan(ScanBase, IdentifiedEntity, TimestampedEntity):
    """Complete scan record from database."""
    
    dentist_id: Optional[UUID] = None
    raw_ml_output: Dict[str, Any] = Field(default_factory=dict)
    ai_report: Optional[str] = None


class ScanListResponse(BaseEntity):
    """Paginated scan list response."""
    
    scans: List[Scan]
    total: int
    page: int
    page_size: int


class ScanAnalysisResponse(BaseEntity):
    """Response after AI analysis of a scan."""
    
    scan_id: UUID
    status: str
    ai_report: Optional[str] = None
    findings_count: int
    raw_ml_output: Dict[str, Any]
