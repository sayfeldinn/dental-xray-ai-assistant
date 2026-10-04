"""
X-ray scan management endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query, Form
from typing import Optional, List
from datetime import datetime
import uuid
from app.schemas.scan import (
    ScanCreate,
    ScanCreateByUrl,
    ScanUpdate,
    ScanResponse,
    ScanListResponse,
    ScanStatusEnum,
    Finding
)
from app.schemas.prediction import PredictionResponse, rows_to_predictions
from app.services.prediction_service import load_prediction_rows
from app.core.supabase import get_supabase_service
from app.utils.auth import get_current_user_id
from app.utils.records import require_scan, require_patient
from supabase import Client

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post("/upload", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def upload_scan(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    scan_type: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    patient_id_q: Optional[str] = Query(None, alias="patient_id"),
    scan_type_q: Optional[str] = Query(None, alias="scan_type"),
    notes_q: Optional[str] = Query(None, alias="notes"),
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Upload a new X-ray scan image.
    Uses service role client to bypass storage and database RLS.
    """
    effective_patient_id = patient_id or patient_id_q
    if not effective_patient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required"
        )
    effective_scan_type = scan_type or scan_type_q or "panoramic"
    effective_notes = notes or notes_q

    # Validate file type
    content_type = file.content_type or "image/jpeg"
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/dicom", "application/octet-stream"]
    if content_type not in allowed_types and not (file.filename and file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.dcm'))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type {content_type}. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if (file.filename and '.' in file.filename) else "jpg"
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        unique_id = str(uuid.uuid4())
        unique_filename = f"scans/{timestamp}_{unique_id}.{file_ext}"
        
        # Upload to Supabase Storage using service role (bypasses RLS)
        file_content = await file.read()
        storage_response = supabase.storage.from_("xray-scans").upload(
            unique_filename,
            file_content,
            {"content-type": content_type, "upsert": "true"}
        )
        
        # Get public URL
        image_url = supabase.storage.from_("xray-scans").get_public_url(unique_filename)
        
        # Create scan record in database using service role (bypasses RLS)
        scan_data = {
            "patient_id": effective_patient_id,
            "dentist_id": current_user_id,
            "scan_type": effective_scan_type,
            "image_url": image_url,
            "status": ScanStatusEnum.PENDING.value,
            "findings": [],
            "notes": effective_notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("scans").insert(scan_data).execute()
        
        if not result.data:
            raise ValueError("Failed to create scan record")
        
        return ScanResponse(**result.data[0])
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload scan: {str(e)}"
        )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan: ScanCreateByUrl,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Register a scan whose image the client already uploaded to storage.

    The upload flow in the web app stores the file itself and posts only the
    resulting URL, so this is the create path it uses (``/scans/upload`` takes
    multipart bytes instead).
    """
    # The patient must belong to the signed-in dentist.
    require_patient(supabase, scan.patient_id, current_user_id)

    scan_data = {
        "patient_id": scan.patient_id,
        "dentist_id": current_user_id,
        "scan_type": scan.scan_type,
        "image_url": scan.image_url,
        "status": scan.status.value,
        "findings": [],
        "notes": scan.notes,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        result = supabase.table("scans").insert(scan_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create scan: {str(e)}"
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create scan record"
        )

    return ScanResponse(**result.data[0])


@router.get("", response_model=ScanListResponse)
@router.get("/", response_model=ScanListResponse)
async def list_scans(
    patient_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """List all scans for the current dentist with optional patient filter."""
    skip = (page - 1) * page_size
    
    try:
        query = supabase.table("scans").select("*", count="exact").eq(
            "dentist_id", current_user_id
        )
        
        if patient_id:
            query = query.eq("patient_id", patient_id)
        
        query = query.range(skip, skip + page_size - 1).order("created_at", desc=True)
        
        result = query.execute()
        
        scans = [ScanResponse(**scan) for scan in result.data]
        total = result.count or 0
        
        return ScanListResponse(
            scans=scans,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list scans: {str(e)}"
        )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """Get a specific scan by ID."""
    return ScanResponse(**require_scan(supabase, scan_id, current_user_id))


@router.get("/{scan_id}/predictions", response_model=List[PredictionResponse])
async def get_scan_predictions(
    scan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    List the detections stored for a scan.

    The Review screen reads this endpoint directly, so it always returns a
    list -- falling back to ``scans.findings`` for scans analysed before the
    ``predictions`` table existed.
    """
    scan = require_scan(supabase, scan_id, current_user_id)
    rows = await load_prediction_rows(supabase, scan, current_user_id)
    return rows_to_predictions(rows)


@router.put("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: str,
    scan_data: ScanUpdate,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """Update a scan record (e.g., add findings, update status)."""
    try:
        update_data = {
            k: v for k, v in scan_data.model_dump(exclude_unset=True).items()
        }
        
        if not update_data:
            return await get_scan(scan_id, current_user_id, supabase)
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert findings to dict if present
        if "findings" in update_data:
            update_data["findings"] = [
                f.model_dump() if isinstance(f, Finding) else f
                for f in update_data["findings"]
            ]
        
        result = supabase.table("scans").update(update_data).eq(
            "id", scan_id
        ).eq(
            "dentist_id", current_user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found"
            )
        
        return ScanResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update scan: {str(e)}"
        )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """Delete a scan record and its associated image."""
    try:
        # Get scan to find image URL
        scan_result = supabase.table("scans").select("*").eq(
            "id", scan_id
        ).eq(
            "dentist_id", current_user_id
        ).single().execute()
        
        if not scan_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found"
            )
        
        # Extract file path from URL and delete from storage
        image_url = scan_result.data.get("image_url", "")
        if image_url:
            # Extract path from URL
            path_parts = image_url.split("/xray-scans/")
            if len(path_parts) > 1:
                file_path = path_parts[1]
                supabase.storage.from_("xray-scans").remove([file_path])
        
        # Delete scan record
        result = supabase.table("scans").delete().eq(
            "id", scan_id
        ).eq(
            "dentist_id", current_user_id
        ).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete scan: {str(e)}"
        )
