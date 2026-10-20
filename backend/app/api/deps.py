"""
DentalAI - API Dependencies
Shared FastAPI dependencies. Tests replace get_workflow via app.dependency_overrides.
"""

from functools import lru_cache

from app.services.clinical_workflow import ClinicalWorkflowService
from app.services.supabase_client import (
    patient_service, scan_service, finding_service, treatment_service, prescription_service,
)


@lru_cache
def get_workflow() -> ClinicalWorkflowService:
    """Workflow service wired to the real Supabase-backed services."""
    return ClinicalWorkflowService(
        patients=patient_service,
        scans=scan_service,
        findings=finding_service,
        treatments=treatment_service,
        prescriptions=prescription_service,
    )
