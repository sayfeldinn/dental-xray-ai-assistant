"""
DentalAI - Scan Domain Models
Panoramic radiograph scans with AI inference results.
"""

from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntity, IdentifiedEntity, TimestampedEntity


class ScanBase(BaseEntity):
    """Core scan fields."""

    patient_id: UUID
    scan_type: str = Field(default="panoramic", max_length=50)
    image_url: str
    storage_path: str | None = None
    status: str = Field(
        default="uploaded", pattern="^(uploaded|processing|analyzed|reviewed|failed)$"
    )
    image_width: int | None = None
    image_height: int | None = None
    notes: str | None = None


class ScanCreate(ScanBase):
    """Schema for creating a new scan record."""

    dentist_id: UUID | None = None


class ScanUpdate(BaseEntity):
    """
    Schema for updating a scan record.

    Deliberately limited to `notes` and `status`. The AI outputs (`raw_ml_output`, `ai_report`)
    are excluded: they are written only by the ingestion service after a real model run, so a
    client cannot tamper with the stored model output.
    """

    status: str | None = Field(None, pattern="^(uploaded|processing|analyzed|reviewed|failed)$")
    notes: str | None = None


class Scan(ScanBase, IdentifiedEntity, TimestampedEntity):
    """Complete scan record from database."""

    dentist_id: UUID | None = None
    raw_ml_output: dict[str, Any] = Field(default_factory=dict)
    ai_report: str | None = None


class ScanListResponse(BaseEntity):
    """Paginated scan list response."""

    scans: list[Scan]
    total: int
    page: int
    page_size: int


class ScanAnalysisResponse(BaseEntity):
    """Response after AI analysis of a scan."""

    scan_id: UUID
    status: str
    ai_report: str | None = None
    findings_count: int
    raw_ml_output: dict[str, Any]
