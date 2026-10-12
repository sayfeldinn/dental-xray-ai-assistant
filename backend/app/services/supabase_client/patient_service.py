"""
DentalAI - Patient Service
Database operations for patient records.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from app.core.supabase_client import supabase_admin
from app.domain.patient import Patient, PatientCreate, PatientUpdate


class PatientService:
    """Service for patient CRUD operations."""
    
    def __init__(self):
        self.client = supabase_admin
        self.table = "patients"
    
    async def create_patient(self, patient_data: PatientCreate) -> Patient:
        """
        Create a new patient record.
        
        Args:
            patient_data: Patient creation schema
        
        Returns:
            Created patient
        """
        data = patient_data.model_dump(exclude_unset=True)
        
        response = self.client.table(self.table).insert(data).execute()
        
        if not response.data:
            raise ValueError("Failed to create patient")
        
        return Patient(**response.data[0])
    
    async def get_patient(self, patient_id: UUID) -> Optional[Patient]:
        """
        Retrieve a patient by ID.
        
        Args:
            patient_id: Patient UUID
        
        Returns:
            Patient if found, None otherwise
        """
        response = self.client.table(self.table).select("*").eq("id", str(patient_id)).execute()
        
        if response.data:
            return Patient(**response.data[0])
        return None
    
    async def list_patients(
        self,
        dentist_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Patient], int]:
        """
        List patients with optional filtering and pagination.
        
        Args:
            dentist_id: Filter by dentist
            search: Search in name fields
            page: Page number (1-indexed)
            page_size: Results per page
        
        Returns:
            Tuple of (patients list, total count)
        """
        query = self.client.table(self.table).select("*", count="exact")
        
        # Apply filters
        if dentist_id:
            query = query.eq("dentist_id", str(dentist_id))
        
        if search:
            # Search in first_name or last_name
            query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        patients = [Patient(**p) for p in response.data] if response.data else []
        total = response.count or 0
        
        return patients, total
    
    async def update_patient(
        self,
        patient_id: UUID,
        patient_data: PatientUpdate
    ) -> Optional[Patient]:
        """
        Update patient record.
        
        Args:
            patient_id: Patient UUID
            patient_data: Fields to update
        
        Returns:
            Updated patient if found, None otherwise
        """
        data = patient_data.model_dump(exclude_unset=True)
        
        if not data:
            # No fields to update
            return await self.get_patient(patient_id)
        
        response = (
            self.client.table(self.table)
            .update(data)
            .eq("id", str(patient_id))
            .execute()
        )
        
        if response.data:
            return Patient(**response.data[0])
        return None
    
    async def delete_patient(self, patient_id: UUID) -> bool:
        """
        Delete a patient record (cascades to related scans/findings).
        
        Args:
            patient_id: Patient UUID
        
        Returns:
            True if deleted, False otherwise
        """
        response = (
            self.client.table(self.table)
            .delete()
            .eq("id", str(patient_id))
            .execute()
        )
        
        return len(response.data) > 0 if response.data else False


# Global service instance
patient_service = PatientService()
