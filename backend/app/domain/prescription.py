"""
DentalAI - Prescription Domain Models
Candidate drugs, safety-check results, and the dentist's Step 5 decision.
"""

from pydantic import Field, model_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from .base import BaseEntity, TimestampedEntity, IdentifiedEntity

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
    rule_id: str = Field(..., description="Rule register ID from docs/CLINICAL_GUIDELINES.md, e.g. R-01")
    severity: Severity
    drug: str
    message: str
    source: str = Field(..., description="Published source behind the rule, or the project-decision marker")


class SafetyCheckResult(BaseEntity):
    """Outcome of checking one drug against one patient."""

    drug_name: str
    indication_type: IndicationType
    status: ContraindicationStatus
    warnings: List[SafetyWarning] = Field(default_factory=list)
    disclaimer: str = PENDING_VALIDATION_NOTICE


class PrescriptionBase(BaseEntity):
    """Core prescription fields."""

    treatment_id: UUID
    patient_id: UUID
    finding_id: Optional[UUID] = None
    drug_name: str = Field(..., max_length=100)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration: str = Field(..., max_length=100)
    indication_type: IndicationType
    instructions: Optional[str] = None


class PrescriptionCreate(PrescriptionBase):
    """Schema for persisting an engine proposal."""

    dentist_id: Optional[UUID] = None
    contraindication_status: ContraindicationStatus = "clear"
    contraindication_warnings: List[SafetyWarning] = Field(default_factory=list)


class Prescription(PrescriptionBase, IdentifiedEntity, TimestampedEntity):
    """Complete prescription record from database."""

    dentist_id: Optional[UUID] = None
    contraindication_status: ContraindicationStatus = "clear"
    contraindication_warnings: List[SafetyWarning] = Field(default_factory=list)
    dentist_status: DentistStatus = "proposed"
    dentist_override_reason: Optional[str] = None
    prescribed_at: Optional[datetime] = None


class PrescriptionListResponse(BaseEntity):
    """List of prescriptions."""

    prescriptions: List[Prescription]
    total: int
    disclaimer: str = PENDING_VALIDATION_NOTICE


class PrescriptionCheckRequest(BaseEntity):
    """Stateless safety check, e.g. while the dentist edits a drug or dose."""

    patient_id: UUID
    drug_name: str
    indication_type: IndicationType
    dosage: Optional[str] = None
    frequency: Optional[str] = Field(None, description="Enables the daily-dose check, e.g. 'every 6 hours'")


class PrescriptionManualCreate(BaseEntity):
    """A dentist-authored prescription added to an already-decided treatment (still safety-checked)."""

    treatment_id: UUID
    drug_name: str = Field(..., max_length=100)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration: str = Field(..., max_length=100)
    indication_type: IndicationType
    instructions: Optional[str] = None
    dentist_id: Optional[UUID] = None


class PrescriptionDecisionRequest(BaseEntity):
    """Step 5: the dentist accepts, modifies, or rejects a proposed prescription."""

    decision: Literal["accepted", "modified", "rejected"]
    drug_name: Optional[str] = Field(None, max_length=100)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    instructions: Optional[str] = None
    acknowledge_warnings: bool = Field(
        False, description="Required to accept a prescription whose status is 'warning'"
    )
    override_reason: Optional[str] = Field(
        None, description="Required to accept a prescription whose status is 'contraindicated'"
    )
    dentist_id: Optional[UUID] = None

    @model_validator(mode="after")
    def _check_modification(self) -> "PrescriptionDecisionRequest":
        edits = (self.drug_name, self.dosage, self.frequency, self.duration, self.instructions)
        if self.decision == "modified" and not any(e is not None for e in edits):
            raise ValueError("decision 'modified' needs at least one edited field")
        if self.decision != "modified" and any(e is not None for e in edits):
            raise ValueError("edited fields are only allowed with decision 'modified'")
        return self
