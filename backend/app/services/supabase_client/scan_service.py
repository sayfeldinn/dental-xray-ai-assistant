"""
DentalAI - Scan Service
Database and storage operations for X-ray scans.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from app.core.supabase_client import supabase_admin
from app.core.config import settings
from app.domain.scan import Scan, ScanCreate, ScanUpdate


class ScanService:
    """Service for scan CRUD and storage operations."""
    
    def __init__(self):
        self.client = supabase_admin
        self.table = "scans"
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
    
    async def upload_image(
        self,
        file_bytes: bytes,
        patient_id: UUID,
        filename: str = None
    ) -> tuple[str, str]:
        """
        Upload X-ray image to Supabase Storage.
        
        Args:
            file_bytes: Image file bytes
            patient_id: Patient UUID for organization
            filename: Original filename
        
        Returns:
            Tuple of (public_url, storage_path)
        """
        # Generate unique storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1] if filename and '.' in filename else 'jpg'
        storage_path = f"patients/{patient_id}/{timestamp}_{uuid4().hex[:8]}.{file_ext}"
        
        # Upload to storage
        response = self.client.storage.from_(self.bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": f"image/{file_ext}"}
        )
        
        # Get public URL
        public_url = self.client.storage.from_(self.bucket).get_public_url(storage_path)
        
        return public_url, storage_path
    
    async def create_scan(self, scan_data: ScanCreate) -> Scan:
        """
        Create a new scan record.
        
        Args:
            scan_data: Scan creation schema
        
        Returns:
            Created scan
        """
        data = scan_data.model_dump(exclude_unset=True)
        
        response = self.client.table(self.table).insert(data).execute()
        
        if not response.data:
            raise ValueError("Failed to create scan")
        
        return Scan(**response.data[0])
    
    async def get_scan(self, scan_id: UUID) -> Optional[Scan]:
        """
        Retrieve a scan by ID.
        
        Args:
            scan_id: Scan UUID
        
        Returns:
            Scan if found, None otherwise
        """
        response = self.client.table(self.table).select("*").eq("id", str(scan_id)).execute()
        
        if response.data:
            return Scan(**response.data[0])
        return None
    
    async def list_scans(
        self,
        patient_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Scan], int]:
        """
        List scans with optional filtering and pagination.
        
        Args:
            patient_id: Filter by patient
            status: Filter by status
            page: Page number (1-indexed)
            page_size: Results per page
        
        Returns:
            Tuple of (scans list, total count)
        """
        query = self.client.table(self.table).select("*", count="exact")
        
        # Apply filters
        if patient_id:
            query = query.eq("patient_id", str(patient_id))
        
        if status:
            query = query.eq("status", status)
        
        # Order by creation date (newest first)
        query = query.order("created_at", desc=True)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        scans = [Scan(**s) for s in response.data] if response.data else []
        total = response.count or 0
        
        return scans, total
    
    async def update_scan(
        self,
        scan_id: UUID,
        scan_data: ScanUpdate
    ) -> Optional[Scan]:
        """
        Update scan record.
        
        Args:
            scan_id: Scan UUID
            scan_data: Fields to update
        
        Returns:
            Updated scan if found, None otherwise
        """
        data = scan_data.model_dump(exclude_unset=True)
        
        if not data:
            return await self.get_scan(scan_id)
        
        response = (
            self.client.table(self.table)
            .update(data)
            .eq("id", str(scan_id))
            .execute()
        )
        
        if response.data:
            return Scan(**response.data[0])
        return None
    
    async def update_ml_results(
        self,
        scan_id: UUID,
        ml_output: Dict[str, Any],
        ai_report: str,
        image_width: int,
        image_height: int
    ) -> Optional[Scan]:
        """
        Update scan with ML analysis results.
        
        Args:
            scan_id: Scan UUID
            ml_output: Raw ML service response
            ai_report: Generated clinical report
            image_width: Image width in pixels
            image_height: Image height in pixels
        
        Returns:
            Updated scan
        """
        data = {
            'raw_ml_output': ml_output,
            'ai_report': ai_report,
            'image_width': image_width,
            'image_height': image_height,
            'status': 'analyzed'
        }
        
        response = (
            self.client.table(self.table)
            .update(data)
            .eq("id", str(scan_id))
            .execute()
        )
        
        if response.data:
            return Scan(**response.data[0])
        return None
    
    async def delete_scan(self, scan_id: UUID) -> bool:
        """
        Delete a scan record and its storage file.
        
        Args:
            scan_id: Scan UUID
        
        Returns:
            True if deleted, False otherwise
        """
        # Get scan to find storage path
        scan = await self.get_scan(scan_id)
        
        if not scan:
            return False
        
        # Delete from storage if path exists
        if scan.storage_path:
            try:
                self.client.storage.from_(self.bucket).remove([scan.storage_path])
            except Exception as e:
                print(f"Warning: Could not delete storage file: {e}")
        
        # Delete database record
        response = (
            self.client.table(self.table)
            .delete()
            .eq("id", str(scan_id))
            .execute()
        )
        
        return len(response.data) > 0 if response.data else False


# Global service instance
scan_service = ScanService()
