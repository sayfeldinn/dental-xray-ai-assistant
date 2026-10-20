"""
DentalAI - Feedback Service
Database operations for the append-only clinical_feedback_logs ledger (Step 6).
Rows are inserted and read, never updated or deleted by the application.
"""

from typing import List, Optional
from uuid import UUID
from app.core.supabase_client import supabase_admin
from app.domain.feedback import FeedbackLog, FeedbackLogCreate


class FeedbackService:
    """Service for feedback ledger persistence."""

    def __init__(self):
        self.client = supabase_admin
        self.table = "clinical_feedback_logs"

    async def create_log(self, data: FeedbackLogCreate) -> FeedbackLog:
        """Append one ledger row."""
        response = self.client.table(self.table).insert(data.model_dump(exclude_none=True, mode="json")).execute()
        if not response.data:
            raise ValueError("Failed to create feedback log")
        return FeedbackLog(**response.data[0])

    async def list_logs(
        self,
        scan_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        correction_type: Optional[str] = None,
    ) -> List[FeedbackLog]:
        """List ledger rows, newest first."""
        query = self.client.table(self.table).select("*")
        if scan_id:
            query = query.eq("scan_id", str(scan_id))
        if stage:
            query = query.eq("stage", stage)
        if correction_type:
            query = query.eq("correction_type", correction_type)
        response = query.order("created_at", desc=True).execute()
        return [FeedbackLog(**row) for row in response.data] if response.data else []


feedback_service = FeedbackService()
