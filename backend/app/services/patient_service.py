"""
Patient service for business logic related to patient management.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from supabase import Client
from app.schemas.patient import (
    MedicalHistoryItem,
    PatientCreate,
    PatientUpdate,
    PatientResponse,
)
from app.core.supabase import get_supabase_service
from app.services.recommendation_engine import recommendation_engine


def _age_from_dob(value: Any) -> Optional[int]:
    """Whole years between a date of birth and today."""
    if isinstance(value, datetime):
        dob = value
    elif isinstance(value, str):
        try:
            dob = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    today = datetime.utcnow()
    before_birthday = (today.month, today.day) < (dob.month, dob.day)
    return today.year - dob.year - (1 if before_birthday else 0)


def _avoided_drugs(condition: str) -> List[str]:
    """Drugs the recommendation engine refuses for this single condition.

    Allergies are checked separately by the UI, so only condition-driven
    contraindications are reported here.
    """
    avoided: List[str] = []
    for drug_name in recommendation_engine.DRUGS_DATABASE:
        safety = recommendation_engine.check_prescription_safety(
            drug_name=drug_name,
            patient_allergies=[],
            patient_medications=[],
            patient_conditions=[condition],
        )
        if not safety.get("safe"):
            avoided.append(drug_name)
    return avoided


def _needs_derived_history(value: Any) -> bool:
    if not value:
        return True
    return any(isinstance(item, str) for item in value)


def build_patient_response(row: Dict[str, Any]) -> PatientResponse:
    """Attach the fields the Scans and Treatment screens read.

    ``age``, ``contact_number`` and ``medical_history`` are derived from the
    columns the schema actually stores (``date_of_birth``, ``phone``,
    ``medical_conditions``) rather than requiring extra tables.
    """
    payload = dict(row)

    if payload.get("age") is None:
        payload["age"] = _age_from_dob(payload.get("date_of_birth"))

    if not payload.get("contact_number"):
        payload["contact_number"] = payload.get("phone")

    if _needs_derived_history(payload.get("medical_history")):
        payload["medical_history"] = [
            MedicalHistoryItem(
                condition=condition,
                contraindications=_avoided_drugs(condition),
            )
            for condition in (payload.get("medical_conditions") or [])
        ]

    return PatientResponse(**payload)


class PatientService:
    """Service for managing patient records."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = "patients"
    
    async def create_patient(
        self, 
        patient_data: PatientCreate, 
        dentist_id: str
    ) -> PatientResponse:
        """Create a new patient record."""
        data = {
            **patient_data.model_dump(),
            "dentist_id": dentist_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Convert datetime to ISO string
        if isinstance(data.get("date_of_birth"), datetime):
            data["date_of_birth"] = data["date_of_birth"].isoformat()
        
        result = self.supabase.table(self.table).insert(data).execute()
        
        if not result.data:
            raise ValueError("Failed to create patient")
        
        return build_patient_response(result.data[0])
    
    async def get_patient(self, patient_id: str, dentist_id: str) -> Optional[PatientResponse]:
        """Get a patient by ID (with access control)."""
        result = self.supabase.table(self.table).select("*").eq(
            "id", patient_id
        ).eq(
            "dentist_id", dentist_id
        ).single().execute()
        
        if not result.data:
            return None
        
        return build_patient_response(result.data)
    
    async def list_patients(
        self, 
        dentist_id: str,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None
    ) -> tuple[List[PatientResponse], int]:
        """List patients for a dentist with pagination."""
        query = self.supabase.table(self.table).select(
            "*", count="exact"
        ).eq("dentist_id", dentist_id)
        
        # Add search filter if provided
        if search:
            query = query.or_(
                f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%"
            )
        
        # Add pagination
        query = query.range(skip, skip + limit - 1).order("created_at", desc=True)
        
        result = query.execute()
        
        patients = [build_patient_response(patient) for patient in result.data]
        total = result.count or 0
        
        return patients, total
    
    async def update_patient(
        self,
        patient_id: str,
        dentist_id: str,
        patient_data: PatientUpdate
    ) -> Optional[PatientResponse]:
        """Update a patient record."""
        # Only update fields that are provided
        update_data = {
            k: v for k, v in patient_data.model_dump(exclude_unset=True).items()
        }
        
        if not update_data:
            return await self.get_patient(patient_id, dentist_id)
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert datetime to ISO string if present
        if "date_of_birth" in update_data and isinstance(update_data["date_of_birth"], datetime):
            update_data["date_of_birth"] = update_data["date_of_birth"].isoformat()
        
        result = self.supabase.table(self.table).update(update_data).eq(
            "id", patient_id
        ).eq(
            "dentist_id", dentist_id
        ).execute()
        
        if not result.data:
            return None
        
        return build_patient_response(result.data[0])
    
    async def delete_patient(self, patient_id: str, dentist_id: str) -> bool:
        """Delete a patient record (soft delete recommended in production)."""
        result = self.supabase.table(self.table).delete().eq(
            "id", patient_id
        ).eq(
            "dentist_id", dentist_id
        ).execute()
        
        return bool(result.data)


def get_patient_service() -> PatientService:
    """Dependency to get patient service instance."""
    return PatientService(get_supabase_service())
