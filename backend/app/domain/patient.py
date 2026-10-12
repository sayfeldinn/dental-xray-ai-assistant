"""
DentalAI - Patient Domain Models
Clinical patient records with medical history for contraindication checking.
"""

from pydantic import EmailStr, Field
from typing import Optional, List
from datetime import date
from uuid import UUID
from .base import BaseEntity, TimestampedEntity, IdentifiedEntity


class PatientBase(BaseEntity):
    """Core patient fields."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other)$")
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    
    # Clinical context for safety checks
    weight_kg: Optional[float] = Field(None, gt=0, description="Required for pediatric dosing")
    allergies: List[str] = Field(default_factory=list, description="Known drug allergies")
    current_medications: List[str] = Field(default_factory=list, description="Active medications")
    medical_conditions: List[str] = Field(default_factory=list, description="Pre-existing conditions")
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    
    dentist_id: Optional[UUID] = None


class PatientUpdate(BaseEntity):
    """Schema for updating patient (all fields optional)."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    notes: Optional[str] = None


class Patient(PatientBase, IdentifiedEntity, TimestampedEntity):
    """Complete patient record from database."""
    
    dentist_id: Optional[UUID] = None


class PatientListResponse(BaseEntity):
    """Paginated patient list response."""
    
    patients: List[Patient]
    total: int
    page: int
    page_size: int
