"""
DentalAI - API Dependencies
Shared FastAPI dependencies. Tests replace these via app.dependency_overrides.
"""

from functools import lru_cache

from app.core.auth import AuthenticatedDentist, get_current_dentist
from app.core.config import settings
from app.services.access import AccessService
from app.services.clinical_workflow import ClinicalWorkflowService
from app.services.ml_client import dentex_client
from app.services.scan_ingestion import ScanIngestionService
from app.services.supabase_client import (
    patient_service, scan_service, finding_service, treatment_service, prescription_service,
    feedback_service,
)

__all__ = ["AuthenticatedDentist", "get_current_dentist", "get_workflow", "get_access", "get_ingestion"]


@lru_cache
def get_workflow() -> ClinicalWorkflowService:
    """Workflow service wired to the real Supabase-backed services."""
    return ClinicalWorkflowService(
        patients=patient_service,
        scans=scan_service,
        findings=finding_service,
        treatments=treatment_service,
        prescriptions=prescription_service,
        feedback=feedback_service,
        ml_feedback=dentex_client.submit_feedback,
    )


@lru_cache
def get_access() -> AccessService:
    """Ownership checks: a dentist only reaches their own patients and what hangs off them."""
    return AccessService(patient_service, scan_service, finding_service, treatment_service, prescription_service)


@lru_cache
def get_ingestion() -> ScanIngestionService:
    return ScanIngestionService(scan_service, finding_service, dentex_client, settings.MAX_UPLOAD_MB)
