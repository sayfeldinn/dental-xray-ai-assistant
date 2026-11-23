"""
DentalAI - Treatment Domain Models
Condition-specific management paths generated from dentist-validated findings.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from .base import BaseEntity, IdentifiedEntity, TimestampedEntity
from .prescription import PENDING_VALIDATION_NOTICE, Prescription

TreatmentCategory = Literal[
    "restorative", "endodontic", "surgical_extraction", "periodontal", "preventive", "monitoring"
]
TreatmentStatus = Literal[
    "proposed", "confirmed", "modified", "in_progress", "completed", "cancelled"
]


class TreatmentBase(BaseEntity):
    """Core treatment fields."""

    patient_id: UUID
    scan_id: UUID
    finding_id: UUID | None = None
    treatment_category: TreatmentCategory
    description: str
    requires_prescription: bool = False
    clinical_justification: str | None = None


class TreatmentCreate(TreatmentBase):
    """Schema for persisting an engine proposal or a dentist-authored treatment."""

    dentist_id: UUID | None = None
    status: TreatmentStatus | None = None  # DB default 'proposed' when omitted
    confirmed_at: datetime | None = None
    dentist_notes: str | None = None


class Treatment(TreatmentBase, IdentifiedEntity, TimestampedEntity):
    """Complete treatment record from database."""

    dentist_id: UUID | None = None
    status: TreatmentStatus = "proposed"
    dentist_notes: str | None = None
    confirmed_at: datetime | None = None


class TreatmentWithPrescriptions(Treatment):
    """Treatment plus its candidate prescriptions (what the review UI renders)."""

    prescriptions: list[Prescription] = Field(default_factory=list)


class TreatmentListResponse(BaseEntity):
    """List of treatments with their prescriptions."""

    treatments: list[TreatmentWithPrescriptions]
    total: int
    disclaimer: str = PENDING_VALIDATION_NOTICE


class TreatmentManualCreate(BaseEntity):
    """A dentist-authored treatment: already the dentist's decision, so it is stored as confirmed."""

    scan_id: UUID
    finding_id: UUID | None = None
    treatment_category: TreatmentCategory
    description: str = Field(..., min_length=1)
    clinical_justification: str | None = None
    dentist_notes: str | None = None
    dentist_id: UUID | None = None


class TreatmentDecisionRequest(BaseEntity):
    """Step 5: the dentist confirms, modifies, or cancels a proposed treatment."""

    decision: Literal["confirmed", "modified", "cancelled"]
    treatment_category: TreatmentCategory | None = None
    description: str | None = None
    dentist_notes: str | None = None
    dentist_id: UUID | None = None

    @model_validator(mode="after")
    def _check_modification(self) -> "TreatmentDecisionRequest":
        edited = self.treatment_category is not None or self.description is not None
        if self.decision == "modified" and not edited:
            raise ValueError("decision 'modified' needs treatment_category or description")
        if self.decision != "modified" and edited:
            raise ValueError(
                "treatment_category/description are only allowed with decision 'modified'"
            )
        return self
