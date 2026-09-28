"""
Patient-related Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class GenderEnum(str, Enum):
    """Patient gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class PatientBase(BaseModel):
    """Base patient schema with common attributes."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: datetime
    gender: GenderEnum
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    
    # Medical information
    allergies: Optional[List[str]] = Field(default_factory=list)
    current_medications: Optional[List[str]] = Field(default_factory=list)
    medical_conditions: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating a patient (all fields optional)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[GenderEnum] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    notes: Optional[str] = None


class MedicalHistoryItem(BaseModel):
    """A condition the patient has, plus the drugs to avoid because of it.

    The Treatment Confirmation screen renders this list and highlights any
    medication appearing in ``contraindications``.
    """
    condition: str
    contraindications: List[str] = Field(default_factory=list)


class PatientResponse(PatientBase):
    """Schema for patient response."""
    id: str
    dentist_id: str
    created_at: datetime
    updated_at: datetime

    # Derived views of PatientBase, consumed by the Scans and Treatment
    # screens (age, contact number, per-condition drug avoidance).
    age: Optional[int] = None
    contact_number: Optional[str] = None
    medical_history: Optional[List[MedicalHistoryItem]] = None

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Schema for paginated patient list response."""
    patients: List[PatientResponse]
    total: int
    page: int
    page_size: int
