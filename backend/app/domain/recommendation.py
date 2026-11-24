"""
DentalAI - Recommendation Domain Models
Request/response shapes for Step 4 (condition-specific recommendation).
"""

from uuid import UUID

from pydantic import Field

from .base import BaseEntity
from .prescription import PENDING_VALIDATION_NOTICE, Prescription
from .treatment import Treatment


class ClinicalContext(BaseEntity):
    """
    Facts the X-ray cannot show, supplied by the dentist after examining the patient.
    The engine never assumes an infection or pain: antibiotics and analgesics are only
    proposed when the dentist says they are indicated (antibiotic stewardship).
    """

    active_infection: bool = Field(
        False,
        description="Pulp necrosis with a localized acute apical abscess (swelling/pus) or systemic involvement "
        "(fever, spreading swelling). Pain alone is NOT an indication for antibiotics (ADA 2019).",
    )
    pain: bool = Field(False, description="Patient reports pain needing analgesia")


class RecommendationRequest(BaseEntity):
    """Body of POST /recommendations/scans/{scan_id}."""

    clinical_context: ClinicalContext = Field(default_factory=ClinicalContext)
    dentist_id: UUID | None = None


class PlanAlert(BaseEntity):
    """Plan-level message the dentist must see (not tied to a single prescription)."""

    code: str
    message: str


class TreatmentPlan(BaseEntity):
    """One finding's persisted treatment proposal with its candidate prescriptions."""

    treatment: Treatment
    prescriptions: list[Prescription] = Field(default_factory=list)
    alerts: list[PlanAlert] = Field(default_factory=list)


class RecommendationResponse(BaseEntity):
    """Everything generated for a scan."""

    scan_id: UUID
    plans: list[TreatmentPlan]
    skipped_finding_ids: list[UUID] = Field(
        default_factory=list,
        description="Findings left untouched because the dentist already acted on their treatment",
    )
    disclaimer: str = PENDING_VALIDATION_NOTICE
