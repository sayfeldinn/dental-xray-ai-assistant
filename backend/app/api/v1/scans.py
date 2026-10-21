"""
DentalAI - Scan API Endpoints
Panoramic X-ray upload, AI analysis, and management. Images live in a private bucket and are
returned as short-lived signed URLs.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist, get_ingestion
from app.domain.scan import Scan, ScanUpdate, ScanListResponse, ScanAnalysisResponse
from app.domain.finding import FindingListResponse
from app.services.access import AccessService
from app.services.scan_ingestion import ScanIngestionService
from app.services.supabase_client import scan_service, finding_service

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("/upload", response_model=ScanAnalysisResponse, status_code=201)
async def upload_and_analyze_scan(
    file: UploadFile = File(..., description="Panoramic X-ray image (JPEG/PNG/WebP)"),
    patient_id: UUID = Form(..., description="Patient UUID"),
    scan_type: str = Form("panoramic", description="Type of scan"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    auto_analyze: bool = Form(True, description="Automatically run AI analysis"),
    confidence_threshold: float = Form(0.20, ge=0.0, le=1.0, description="Detection confidence threshold"),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
    ingestion: ScanIngestionService = Depends(get_ingestion),
):
    """
    Upload a panoramic X-ray and optionally analyze it with AI.

    **Steps 1-2 in Clinical Loop**: store the image, run dentex_week3, save every detection as a
    *pending* finding. If the AI fails the scan is kept (status `failed`) and the call returns 502.
    """
    await access.patient(patient_id, dentist)
    return await ingestion.upload(
        patient_id=patient_id, dentist_id=dentist.id, file_bytes=await file.read(), filename=file.filename,
        content_type=file.content_type, scan_type=scan_type, notes=notes, auto_analyze=auto_analyze,
        confidence=confidence_threshold)


@router.get("/{scan_id}", response_model=Scan)
async def get_scan(
    scan_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Retrieve a scan with its full ML output."""
    return scan_service.signed_url(await access.scan(scan_id, dentist))


@router.get("", response_model=ScanListResponse)
async def list_scans(
    patient_id: UUID = Query(..., description="Patient whose scans to list"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """List one patient's scans, newest first."""
    await access.patient(patient_id, dentist)
    scans, total = await scan_service.list_scans(patient_id=patient_id, status=status, page=page, page_size=page_size)
    return ScanListResponse(scans=[scan_service.signed_url(s) for s in scans], total=total, page=page, page_size=page_size)


@router.put("/{scan_id}", response_model=Scan)
async def update_scan(
    scan_id: UUID,
    scan_data: ScanUpdate,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Update a scan record (status, notes)."""
    await access.scan(scan_id, dentist)
    scan = await scan_service.update_scan(scan_id, scan_data)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_service.signed_url(scan)


@router.get("/{scan_id}/findings", response_model=FindingListResponse)
async def get_scan_findings(
    scan_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Get all findings for a specific scan.

    **Step 3 Preparation**: Retrieve findings for dentist review.
    """
    await access.scan(scan_id, dentist)
    findings = await finding_service.list_findings_by_scan(scan_id)
    return FindingListResponse(findings=findings, total=len(findings))


@router.post("/{scan_id}/reanalyze", response_model=ScanAnalysisResponse)
async def reanalyze_scan(
    scan_id: UUID,
    confidence_threshold: float = Query(0.20, ge=0.0, le=1.0, description="Detection confidence threshold"),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
    ingestion: ScanIngestionService = Depends(get_ingestion),
):
    """
    Re-run AI analysis on a stored scan (e.g. after a failed analysis or a model update).
    Refused with 409 once any finding has been reviewed.
    """
    return await ingestion.reanalyze(await access.scan(scan_id, dentist), confidence_threshold)


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Delete a scan record and its storage file.

    **Warning**: This cascades to all related findings, treatments and feedback.
    """
    await access.scan(scan_id, dentist)
    if not await scan_service.delete_scan(scan_id):
        raise HTTPException(status_code=404, detail="Scan not found")
    return None
