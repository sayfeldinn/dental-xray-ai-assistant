"""
DentalAI - Finding Service
Database operations for tooth pathology findings.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from app.core.supabase_client import supabase_admin
from app.domain.finding import Finding, FindingCreate, FindingUpdate


class FindingService:
    """Service for finding CRUD operations."""
    
    def __init__(self):
        self.client = supabase_admin
        self.table = "findings"
    
    async def create_finding(self, finding_data: FindingCreate) -> Finding:
        """
        Create a new finding record.
        
        Args:
            finding_data: Finding creation schema
        
        Returns:
            Created finding
        """
        data = finding_data.model_dump(exclude_unset=True, mode='json')
        
        response = self.client.table(self.table).insert(data).execute()
        
        if not response.data:
            raise ValueError("Failed to create finding")
        
        return Finding(**response.data[0])
    
    async def bulk_create_findings(self, findings_data: List[Dict[str, Any]]) -> List[Finding]:
        """
        Create multiple findings at once.
        
        Args:
            findings_data: List of finding dictionaries
        
        Returns:
            List of created findings
        """
        if not findings_data:
            return []
        
        response = self.client.table(self.table).insert(findings_data).execute()
        
        if not response.data:
            raise ValueError("Failed to create findings")
        
        return [Finding(**f) for f in response.data]
    
    async def get_finding(self, finding_id: UUID) -> Optional[Finding]:
        """
        Retrieve a finding by ID.
        
        Args:
            finding_id: Finding UUID
        
        Returns:
            Finding if found, None otherwise
        """
        response = self.client.table(self.table).select("*").eq("id", str(finding_id)).execute()
        
        if response.data:
            return Finding(**response.data[0])
        return None
    
    async def list_findings_by_scan(self, scan_id: UUID) -> List[Finding]:
        """
        List all findings for a specific scan.
        
        Args:
            scan_id: Scan UUID
        
        Returns:
            List of findings
        """
        response = (
            self.client.table(self.table)
            .select("*")
            .eq("scan_id", str(scan_id))
            .order("quadrant")
            .order("tooth_id")
            .execute()
        )
        
        return [Finding(**f) for f in response.data] if response.data else []
    
    async def list_findings_by_patient(
        self,
        patient_id: UUID,
        review_status: Optional[str] = None
    ) -> List[Finding]:
        """
        List all findings for a specific patient.
        
        Args:
            patient_id: Patient UUID
            review_status: Filter by review status
        
        Returns:
            List of findings
        """
        query = self.client.table(self.table).select("*").eq("patient_id", str(patient_id))
        
        if review_status:
            query = query.eq("review_status", review_status)
        
        query = query.order("created_at", desc=True)
        
        response = query.execute()
        
        return [Finding(**f) for f in response.data] if response.data else []
    
    async def update_finding(
        self,
        finding_id: UUID,
        finding_data: FindingUpdate
    ) -> Optional[Finding]:
        """
        Update finding record (typically for dentist review).
        
        Args:
            finding_id: Finding UUID
            finding_data: Fields to update
        
        Returns:
            Updated finding if found, None otherwise
        """
        data = finding_data.model_dump(exclude_unset=True, mode='json')
        
        if not data:
            return await self.get_finding(finding_id)
        
        response = (
            self.client.table(self.table)
            .update(data)
            .eq("id", str(finding_id))
            .execute()
        )
        
        if response.data:
            return Finding(**response.data[0])
        return None
    
    async def review_finding(
        self,
        finding_id: UUID,
        review_status: str,
        dentist_id: Optional[UUID] = None,
        confirmed_disease: Optional[str] = None,
        dentist_notes: Optional[str] = None
    ) -> Optional[Finding]:
        """
        Update finding with dentist review decision.
        
        Args:
            finding_id: Finding UUID
            review_status: 'confirmed', 'rejected', or 'modified'
            dentist_id: Reviewing dentist UUID (stamped from the verified JWT; reviewed_by
                        references auth.users, so it is only set when authenticated)
            confirmed_disease: Corrected disease if modified
            dentist_notes: Dentist's notes
        
        Returns:
            Updated finding
        """
        data = {
            'review_status': review_status,
            'reviewed_at': datetime.now(timezone.utc).isoformat()
        }

        if dentist_id:
            data['reviewed_by'] = str(dentist_id)
        
        if confirmed_disease:
            data['confirmed_disease'] = confirmed_disease
        
        if dentist_notes:
            data['dentist_notes'] = dentist_notes
        
        response = (
            self.client.table(self.table)
            .update(data)
            .eq("id", str(finding_id))
            .execute()
        )
        
        if response.data:
            return Finding(**response.data[0])
        return None
    
    async def delete_findings_by_scan(self, scan_id: UUID) -> None:
        """Remove a scan's findings before re-analysis (treatments keep running: finding_id is SET NULL)."""
        self.client.table(self.table).delete().eq("scan_id", str(scan_id)).execute()

    async def get_confirmed_findings(self, scan_id: UUID) -> List[Finding]:
        """
        Get dentist-validated findings for a scan (for treatment recommendations).

        Includes 'modified' findings: the dentist accepted the detection but
        corrected the disease label (see Finding.effective_disease).
        Rejected and pending findings never feed the recommendation engine.

        Args:
            scan_id: Scan UUID

        Returns:
            List of confirmed or modified findings
        """
        response = (
            self.client.table(self.table)
            .select("*")
            .eq("scan_id", str(scan_id))
            .in_("review_status", ["confirmed", "modified"])
            .order("quadrant")
            .order("tooth_id")
            .execute()
        )
        
        return [Finding(**f) for f in response.data] if response.data else []


# Global service instance
finding_service = FindingService()
