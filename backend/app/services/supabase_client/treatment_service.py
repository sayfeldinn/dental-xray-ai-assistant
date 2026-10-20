"""
DentalAI - Treatment Service
Database operations for treatments (Step 4/5).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.supabase_client import supabase_admin
from app.domain.treatment import Treatment, TreatmentCreate


class TreatmentService:
    """Service for treatment persistence."""

    def __init__(self):
        self.client = supabase_admin
        self.table = "treatments"

    async def create_treatment(self, treatment_data: TreatmentCreate) -> Treatment:
        """Insert a treatment proposal."""
        data = treatment_data.model_dump(exclude_none=True, mode='json')
        response = self.client.table(self.table).insert(data).execute()

        if not response.data:
            raise ValueError("Failed to create treatment")

        return Treatment(**response.data[0])

    async def get_treatment(self, treatment_id: UUID) -> Optional[Treatment]:
        """Retrieve a treatment by ID."""
        response = self.client.table(self.table).select("*").eq("id", str(treatment_id)).execute()
        return Treatment(**response.data[0]) if response.data else None

    async def list_treatments(
        self,
        scan_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[Treatment]:
        """List treatments filtered by scan and/or patient and/or status, oldest first."""
        query = self.client.table(self.table).select("*")
        if scan_id:
            query = query.eq("scan_id", str(scan_id))
        if patient_id:
            query = query.eq("patient_id", str(patient_id))
        if status:
            query = query.eq("status", status)

        response = query.order("created_at").execute()
        return [Treatment(**t) for t in response.data] if response.data else []

    async def update_treatment(self, treatment_id: UUID, changes: Dict[str, Any]) -> Optional[Treatment]:
        """Apply a partial update (JSON-safe values only)."""
        response = (
            self.client.table(self.table)
            .update(changes)
            .eq("id", str(treatment_id))
            .execute()
        )
        return Treatment(**response.data[0]) if response.data else None

    async def delete_treatments(self, treatment_ids: List[UUID]) -> None:
        """Delete treatments; their prescriptions go with them (ON DELETE CASCADE)."""
        if treatment_ids:
            self.client.table(self.table).delete().in_("id", [str(t) for t in treatment_ids]).execute()


# Global service instance
treatment_service = TreatmentService()
