"""
Treatment and prescription related schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TreatmentStatusEnum(str, Enum):
    """Status of treatment."""
    RECOMMENDED = "recommended"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PrescriptionCreate(BaseModel):
    """Schema for creating a prescription."""
    drug_name: str = Field(..., min_length=1)
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None


class PrescriptionResponse(BaseModel):
    """Schema for prescription response."""
    id: str
    treatment_id: str
    drug_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None
    contraindication_checked: bool = False
    contraindication_warnings: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        from_attributes = True


class TreatmentCreate(BaseModel):
    """Schema for creating a treatment plan."""
    patient_id: str
    scan_id: Optional[str] = None
    finding_id: Optional[str] = None
    treatment_type: str
    description: str
    estimated_cost: Optional[float] = None
    prescriptions: Optional[List[PrescriptionCreate]] = Field(default_factory=list)
    notes: Optional[str] = None


class TreatmentUpdate(BaseModel):
    """Schema for updating a treatment."""
    status: Optional[TreatmentStatusEnum] = None
    description: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class TreatmentResponse(BaseModel):
    """Schema for treatment response."""
    id: str
    patient_id: str
    dentist_id: str
    scan_id: Optional[str] = None
    finding_id: Optional[str] = None
    treatment_type: str
    description: str
    status: TreatmentStatusEnum
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    prescriptions: List[PrescriptionResponse] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TreatmentListResponse(BaseModel):
    """Schema for paginated treatment list response."""
    treatments: List[TreatmentResponse]
    total: int
    page: int
    page_size: int
