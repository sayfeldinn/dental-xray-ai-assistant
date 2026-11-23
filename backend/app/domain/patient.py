"""
DentalAI - Patient Domain Models
Clinical patient records with medical history for contraindication checking.
"""

from datetime import date
from uuid import UUID

from pydantic import EmailStr, Field

from .base import BaseEntity, IdentifiedEntity, TimestampedEntity


class PatientBase(BaseEntity):
    """Core patient fields."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other)$")
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    address: str | None = None

    # Clinical context for safety checks
    weight_kg: float | None = Field(None, gt=0, description="Required for pediatric dosing")
    allergies: list[str] = Field(default_factory=list, description="Known drug allergies")
    current_medications: list[str] = Field(default_factory=list, description="Active medications")
    medical_conditions: list[str] = Field(
        default_factory=list, description="Pre-existing conditions"
    )
    notes: str | None = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""

    dentist_id: UUID | None = None


class PatientUpdate(BaseEntity):
    """Schema for updating patient (all fields optional)."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(None, pattern="^(male|female|other)$")
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    address: str | None = None
    weight_kg: float | None = Field(None, gt=0)
    allergies: list[str] | None = None
    current_medications: list[str] | None = None
    medical_conditions: list[str] | None = None
    notes: str | None = None


class Patient(PatientBase, IdentifiedEntity, TimestampedEntity):
    """Complete patient record from database."""

    dentist_id: UUID | None = None


class PatientListResponse(BaseEntity):
    """Paginated patient list response."""

    patients: list[Patient]
    total: int
    page: int
    page_size: int
