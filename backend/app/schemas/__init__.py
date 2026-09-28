"""Pydantic schemas for request/response validation."""
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
    MedicalHistoryItem,
    GenderEnum
)
from app.schemas.prediction import PredictionResponse
from app.schemas.scan import (
    ScanCreate,
    ScanCreateByUrl,
    ScanUpdate,
    ScanResponse,
    ScanListResponse,
    Finding,
    FindingTypeEnum,
    FindingSeverityEnum,
    ScanStatusEnum
)
from app.schemas.treatment import (
    TreatmentCreate,
    TreatmentUpdate,
    TreatmentResponse,
    TreatmentListResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    TreatmentStatusEnum
)

__all__ = [
    # Patient schemas
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "PatientListResponse",
    "MedicalHistoryItem",
    "GenderEnum",
    # Scan schemas
    "ScanCreate",
    "ScanCreateByUrl",
    "ScanUpdate",
    "ScanResponse",
    "ScanListResponse",
    "Finding",
    "FindingTypeEnum",
    "FindingSeverityEnum",
    "ScanStatusEnum",
    # Prediction schema
    "PredictionResponse",
    # Treatment schemas
    "TreatmentCreate",
    "TreatmentUpdate",
    "TreatmentResponse",
    "TreatmentListResponse",
    "PrescriptionCreate",
    "PrescriptionResponse",
    "TreatmentStatusEnum",
]
