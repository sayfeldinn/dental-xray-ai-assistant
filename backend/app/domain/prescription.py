"""
DentalAI - Prescription Domain Models
Candidate drugs, safety-check results, and the dentist's Step 5 decision.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from .base import BaseEntity, IdentifiedEntity, TimestampedEntity

Severity = Literal["info", "warning", "contraindicated"]
ContraindicationStatus = Literal["clear", "warning", "contraindicated"]
IndicationType = Literal["active_infection", "pre_procedure_prophylaxis", "pain_management"]
DentistStatus = Literal["proposed", "accepted", "modified", "rejected"]

PENDING_VALIDATION_NOTICE = (
    "Pending Dentist Validation: AI-assisted suggestions only. "
    "Nothing here is a diagnosis or prescription until the treating dentist confirms it."
)


class SafetyWarning(BaseEntity):
    """One structured finding from the contraindication checker (stored as JSONB)."""

    code: str = Field(..., description="Stable machine-readable code, e.g. ALLERGY_PENICILLIN")
    rule_id: str = Field(
        ..., description="Rule register ID from docs/CLINICAL_GUIDELINES.md, e.g. R-01"
    )
    severity: Severity
    drug: str
    message: str
    source: str = Field(
        ..., description="Published source behind the rule, or the project-decision marker"
    )


class SafetyCheckResult(BaseEntity):
    """Outcome of checking one drug against one patient."""

    drug_name: str
    indication_type: IndicationType
    status: ContraindicationStatus
    warnings: list[SafetyWarning] = Field(default_factory=list)
    disclaimer: str = PENDING_VALIDATION_NOTICE


class PrescriptionBase(BaseEntity):
    """Core prescription fields."""

    treatment_id: UUID
    patient_id: UUID
    finding_id: UUID | None = None
    drug_name: str = Field(..., max_length=100)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration: str = Field(..., max_length=100)
    indication_type: IndicationType
    instructions: str | None = None


class PrescriptionCreate(PrescriptionBase):
    """Schema for persisting an engine proposal."""

    dentist_id: UUID | None = None
    contraindication_status: ContraindicationStatus = "clear"
    contraindication_warnings: list[SafetyWarning] = Field(default_factory=list)


class Prescription(PrescriptionBase, IdentifiedEntity, TimestampedEntity):
    """Complete prescription record from database."""

    dentist_id: UUID | None = None
    contraindication_status: ContraindicationStatus = "clear"
    contraindication_warnings: list[SafetyWarning] = Field(default_factory=list)
    dentist_status: DentistStatus = "proposed"
    dentist_override_reason: str | None = None
    prescribed_at: datetime | None = None


class PrescriptionListResponse(BaseEntity):
    """List of prescriptions."""

    prescriptions: list[Prescription]
    total: int
    disclaimer: str = PENDING_VALIDATION_NOTICE


class PrescriptionCheckRequest(BaseEntity):
    """Stateless safety check, e.g. while the dentist edits a drug or dose."""

    patient_id: UUID
    drug_name: str
    indication_type: IndicationType
    dosage: str | None = None
    frequency: str | None = Field(
        None, description="Enables the daily-dose check, e.g. 'every 6 hours'"
    )


class PrescriptionManualCreate(BaseEntity):
    """A dentist-authored prescription added to an already-decided treatment (still safety-checked)."""

    treatment_id: UUID
    drug_name: str = Field(..., max_length=100)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration: str = Field(..., max_length=100)
    indication_type: IndicationType
    instructions: str | None = None
    dentist_id: UUID | None = None


class PrescriptionDecisionRequest(BaseEntity):
    """Step 5: the dentist accepts, modifies, or rejects a proposed prescription."""

    decision: Literal["accepted", "modified", "rejected"]
    drug_name: str | None = Field(None, max_length=100)
    dosage: str | None = Field(None, max_length=100)
    frequency: str | None = Field(None, max_length=100)
    duration: str | None = Field(None, max_length=100)
    instructions: str | None = None
    acknowledge_warnings: bool = Field(
        False, description="Required to accept a prescription whose status is 'warning'"
    )
    override_reason: str | None = Field(
        None, description="Required to accept a prescription whose status is 'contraindicated'"
    )
    dentist_id: UUID | None = None

    @model_validator(mode="after")
    def _check_modification(self) -> "PrescriptionDecisionRequest":
        edits = (self.drug_name, self.dosage, self.frequency, self.duration, self.instructions)
        if self.decision == "modified" and not any(e is not None for e in edits):
            raise ValueError("decision 'modified' needs at least one edited field")
        if self.decision != "modified" and any(e is not None for e in edits):
            raise ValueError("edited fields are only allowed with decision 'modified'")
        return self
