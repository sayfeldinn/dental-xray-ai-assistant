"""
Patient service for business logic related to patient management.
"""
from typing import List, Optional
from datetime import datetime
from supabase import Client
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.core.supabase import get_supabase_service


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
        
        return PatientResponse(**result.data[0])
    
    async def get_patient(self, patient_id: str, dentist_id: str) -> Optional[PatientResponse]:
        """Get a patient by ID (with access control)."""
        result = self.supabase.table(self.table).select("*").eq(
            "id", patient_id
        ).eq(
            "dentist_id", dentist_id
        ).single().execute()
        
        if not result.data:
            return None
        
        return PatientResponse(**result.data)
    
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
        
        patients = [PatientResponse(**patient) for patient in result.data]
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
        
        return PatientResponse(**result.data[0])
    
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
