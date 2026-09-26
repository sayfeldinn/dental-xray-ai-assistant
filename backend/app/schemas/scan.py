"""
X-ray scan related schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ScanStatusEnum(str, Enum):
    """Status of scan analysis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverityEnum(str, Enum):
    """Severity level of detected findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingTypeEnum(str, Enum):
    """Types of dental findings."""
    CAVITY = "cavity"
    ROOT_CANAL = "root_canal"
    CROWN = "crown"
    EXTRACTION = "extraction"
    FILLING = "filling"
    IMPLANT = "implant"
    OTHER = "other"


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected findings."""
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)


class Finding(BaseModel):
    """Detected finding on X-ray."""
    id: Optional[str] = None
    type: FindingTypeEnum
    severity: FindingSeverityEnum
    confidence: float = Field(..., ge=0, le=1)
    bounding_box: BoundingBox
    tooth_number: Optional[str] = None
    description: Optional[str] = None
    ai_generated: bool = True
    confirmed: bool = False
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class ScanCreate(BaseModel):
    """Schema for creating a new scan."""
    patient_id: str
    scan_type: str = Field(default="panoramic", description="Type of X-ray scan")
    notes: Optional[str] = None


class ScanUpdate(BaseModel):
    """Schema for updating a scan."""
    status: Optional[ScanStatusEnum] = None
    notes: Optional[str] = None
    findings: Optional[List[Finding]] = None


class ScanResponse(BaseModel):
    """Schema for scan response."""
    id: str
    patient_id: str
    dentist_id: str
    scan_type: str
    image_url: str
    status: ScanStatusEnum
    findings: List[Finding] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """Schema for paginated scan list response."""
    scans: List[ScanResponse]
    total: int
    page: int
    page_size: int
