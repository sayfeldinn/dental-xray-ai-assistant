"""
DentalAI - Scan API Endpoints
Panoramic X-ray scan upload, AI analysis, and management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional
from uuid import UUID

from app.domain.scan import (
    Scan,
    ScanCreate,
    ScanUpdate,
    ScanListResponse,
    ScanAnalysisResponse
)
from app.domain.finding import FindingListResponse
from app.services.supabase_client import scan_service, finding_service
from app.services.ml_client import dentex_client

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("/upload", response_model=ScanAnalysisResponse, status_code=201)
async def upload_and_analyze_scan(
    file: UploadFile = File(..., description="Panoramic X-ray image (JPEG/PNG/WebP)"),
    patient_id: UUID = Form(..., description="Patient UUID"),
    scan_type: str = Form("panoramic", description="Type of scan"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    auto_analyze: bool = Form(True, description="Automatically run AI analysis"),
    confidence_threshold: float = Form(0.20, ge=0.0, le=1.0, description="Detection confidence threshold")
):
    """
    Upload a panoramic X-ray and optionally analyze with AI.
    
    **Steps 1-2 in Clinical Loop**:
    1. Scan Ingestion: Upload to Supabase Storage
    2. AI-Assisted Detection: Run dentex_week3 inference
    
    Returns scan record with AI detections and generated findings.
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # Step 1: Upload to Supabase Storage
        image_url, storage_path = await scan_service.upload_image(
            file_bytes=file_bytes,
            patient_id=patient_id,
            filename=file.filename
        )
        
        # Create scan record
        scan_data = ScanCreate(
            patient_id=patient_id,
            scan_type=scan_type,
            image_url=image_url,
            storage_path=storage_path,
            notes=notes,
            status="uploaded"
        )
        
        scan = await scan_service.create_scan(scan_data)
        
        findings_count = 0
        ml_output = {}
        ai_report = None
        
        # Step 2: AI Analysis (if requested)
        if auto_analyze:
            try:
                # Update status to processing
                await scan_service.update_scan(
                    scan.id,
                    ScanUpdate(status="processing")
                )
                
                # Call dentex_week3 ML service
                ml_output = await dentex_client.analyze_scan(
                    image_bytes=file_bytes,
                    filename=file.filename,
                    confidence_threshold=confidence_threshold
                )
                
                # Extract report and metadata
                ai_report = ml_output.get('report', 'No report generated')
                image_width = ml_output.get('image_width', 0)
                image_height = ml_output.get('image_height', 0)
                
                # Update scan with ML results
                scan = await scan_service.update_ml_results(
                    scan_id=scan.id,
                    ml_output=ml_output,
                    ai_report=ai_report,
                    image_width=image_width,
                    image_height=image_height
                )
                
                # Parse detections into findings
                findings_data = dentex_client.parse_detections_to_findings(
                    ml_output=ml_output,
                    scan_id=str(scan.id),
                    patient_id=str(patient_id)
                )
                
                # Create findings in database
                if findings_data:
                    findings = await finding_service.bulk_create_findings(findings_data)
                    findings_count = len(findings)
                
            except Exception as ml_error:
                # Mark scan as failed but don't fail the entire request
                await scan_service.update_scan(
                    scan.id,
                    ScanUpdate(
                        status="failed",
                        notes=f"AI analysis failed: {str(ml_error)}"
                    )
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Scan uploaded but AI analysis failed: {str(ml_error)}"
                )
        
        return ScanAnalysisResponse(
            scan_id=scan.id,
            status=scan.status,
            ai_report=ai_report,
            findings_count=findings_count,
            raw_ml_output=ml_output
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload scan: {str(e)}")


@router.get("/{scan_id}", response_model=Scan)
async def get_scan(scan_id: UUID):
    """
    Retrieve a scan by ID with full ML output.
    """
    scan = await scan_service.get_scan(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan


@router.get("", response_model=ScanListResponse)
async def list_scans(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page")
):
    """
    List scans with optional filtering and pagination.
    """
    scans, total = await scan_service.list_scans(
        patient_id=patient_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return ScanListResponse(
        scans=scans,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/{scan_id}", response_model=Scan)
async def update_scan(scan_id: UUID, scan_data: ScanUpdate):
    """
    Update scan record.
    """
    scan = await scan_service.update_scan(scan_id, scan_data)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan


@router.get("/{scan_id}/findings", response_model=FindingListResponse)
async def get_scan_findings(scan_id: UUID):
    """
    Get all findings for a specific scan.
    
    **Step 3 Preparation**: Retrieve findings for dentist review.
    """
    # Verify scan exists
    scan = await scan_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    findings = await finding_service.list_findings_by_scan(scan_id)
    
    return FindingListResponse(
        findings=findings,
        total=len(findings)
    )


@router.post("/{scan_id}/reanalyze", response_model=ScanAnalysisResponse)
async def reanalyze_scan(
    scan_id: UUID,
    confidence_threshold: float = Query(0.20, ge=0.0, le=1.0, description="Detection confidence threshold")
):
    """
    Rerun AI analysis on an existing scan.
    
    Useful if ML service was updated or different confidence threshold needed.
    """
    # Get existing scan
    scan = await scan_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # TODO: Download image from storage and reanalyze
    # This requires implementing storage download, which we'll add in refinement
    
    raise HTTPException(
        status_code=501,
        detail="Reanalysis not yet implemented. Upload a new scan instead."
    )


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: UUID):
    """
    Delete a scan record and its storage file.
    
    **Warning**: This cascades to all related findings.
    """
    success = await scan_service.delete_scan(scan_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return None
