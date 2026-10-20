"""
DentalAI - Prescription Service
Database operations for prescriptions (Step 4/5).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from app.core.supabase_client import supabase_admin
from app.domain.prescription import Prescription, PrescriptionCreate


class PrescriptionService:
    """Service for prescription persistence."""

    def __init__(self):
        self.client = supabase_admin
        self.table = "prescriptions"

    async def create_prescription(self, prescription_data: PrescriptionCreate) -> Prescription:
        """Insert a prescription proposal."""
        data = prescription_data.model_dump(exclude_none=True, mode='json')
        response = self.client.table(self.table).insert(data).execute()

        if not response.data:
            raise ValueError("Failed to create prescription")

        return Prescription(**response.data[0])

    async def get_prescription(self, prescription_id: UUID) -> Optional[Prescription]:
        """Retrieve a prescription by ID."""
        response = self.client.table(self.table).select("*").eq("id", str(prescription_id)).execute()
        return Prescription(**response.data[0]) if response.data else None

    async def list_prescriptions(
        self,
        treatment_ids: Optional[List[UUID]] = None,
        patient_id: Optional[UUID] = None,
    ) -> List[Prescription]:
        """List prescriptions for treatments and/or a patient, oldest first."""
        query = self.client.table(self.table).select("*")
        if treatment_ids is not None:
            if not treatment_ids:
                return []
            query = query.in_("treatment_id", [str(t) for t in treatment_ids])
        if patient_id:
            query = query.eq("patient_id", str(patient_id))

        response = query.order("created_at").execute()
        return [Prescription(**p) for p in response.data] if response.data else []

    async def update_prescription(self, prescription_id: UUID, changes: Dict[str, Any]) -> Optional[Prescription]:
        """Apply a partial update (JSON-safe values only)."""
        response = (
            self.client.table(self.table)
            .update(changes)
            .eq("id", str(prescription_id))
            .execute()
        )
        return Prescription(**response.data[0]) if response.data else None


# Global service instance
prescription_service = PrescriptionService()
