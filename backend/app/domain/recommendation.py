"""
DentalAI - Recommendation Domain Models
Request/response shapes for Step 4 (condition-specific recommendation).
"""

from pydantic import Field
from typing import List
from uuid import UUID
from .base import BaseEntity
from .prescription import Prescription, PENDING_VALIDATION_NOTICE
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
    prescriptions: List[Prescription] = Field(default_factory=list)
    alerts: List[PlanAlert] = Field(default_factory=list)


class RecommendationResponse(BaseEntity):
    """Everything generated for a scan."""

    scan_id: UUID
    plans: List[TreatmentPlan]
    skipped_finding_ids: List[UUID] = Field(
        default_factory=list,
        description="Findings left untouched because the dentist already acted on their treatment",
    )
    disclaimer: str = PENDING_VALIDATION_NOTICE
