"""
DentalAI - Recommendation API Endpoints
Step 4 of the clinical loop: condition-specific treatment and drug proposals.
"""

from fastapi import APIRouter, Depends
from uuid import UUID

from app.api.deps import get_workflow
from app.domain.recommendation import RecommendationRequest, RecommendationResponse
from app.services.clinical_workflow import ClinicalWorkflowService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/scans/{scan_id}", response_model=RecommendationResponse, status_code=201)
async def generate_recommendations(
    scan_id: UUID,
    request: RecommendationRequest = RecommendationRequest(),
    workflow: ClinicalWorkflowService = Depends(get_workflow),
):
    """
    Generate treatment and drug proposals for a scan's dentist-validated findings.

    **Step 4 in Clinical Loop**: the rule engine maps confirmed/modified findings to treatments;
    every candidate drug is checked against the patient's allergies, medications, conditions,
    age and weight. Antibiotics and analgesics are only proposed when `clinical_context` says
    they are indicated. Everything is a **proposal pending dentist validation**.

    Re-running replaces untouched proposals and keeps anything the dentist already acted on.
    """
    return await workflow.generate_for_scan(scan_id, request)
