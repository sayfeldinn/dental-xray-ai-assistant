"""Supabase client services."""

from .patient_service import PatientService, patient_service
from .scan_service import ScanService, scan_service
from .finding_service import FindingService, finding_service
from .treatment_service import TreatmentService, treatment_service
from .prescription_service import PrescriptionService, prescription_service
from .feedback_service import FeedbackService, feedback_service

__all__ = [
    'FeedbackService', 'feedback_service',
    'PatientService', 'patient_service',
    'ScanService', 'scan_service',
    'FindingService', 'finding_service',
    'TreatmentService', 'treatment_service',
    'PrescriptionService', 'prescription_service'
]
