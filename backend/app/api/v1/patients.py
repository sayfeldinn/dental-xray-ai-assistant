"""
DentalAI - Patient API Endpoints
CRUD for the signed-in dentist's patients. Other dentists' patients answer 404.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.api.deps import AuthenticatedDentist, get_access, get_current_dentist
from app.domain.patient import Patient, PatientCreate, PatientUpdate, PatientListResponse
from app.services.access import AccessService
from app.services.supabase_client import patient_service, scan_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=Patient, status_code=201)
async def create_patient(patient_data: PatientCreate, dentist: AuthenticatedDentist = Depends(get_current_dentist)):
    """
    Create a new patient record owned by the signed-in dentist.

    **Step 1 in Clinical Loop**: Patient registration before scan ingestion.
    """
    patient_data.dentist_id = dentist.id   # never trust an owner sent by the client
    try:
        return await patient_service.create_patient(patient_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """Retrieve one of your patients."""
    return await access.patient(patient_id, dentist)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    search: Optional[str] = Query(None, description="Search in patient names"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
):
    """List your patients, with optional name search and pagination."""
    patients, total = await patient_service.list_patients(
        dentist_id=dentist.id, search=search, page=page, page_size=page_size)
    return PatientListResponse(patients=patients, total=total, page=page, page_size=page_size)


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Update a patient record.

    Critical for updating allergies, medications, and conditions that affect
    contraindication checking in Steps 4-5.
    """
    await access.patient(patient_id, dentist)
    patient = await patient_service.update_patient(patient_id, patient_data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: UUID,
    dentist: AuthenticatedDentist = Depends(get_current_dentist),
    access: AccessService = Depends(get_access),
):
    """
    Delete a patient record and their X-ray images.

    **Warning**: This cascades to all related scans, findings, treatments, prescriptions and feedback.
    """
    await access.patient(patient_id, dentist)
    scans, _ = await scan_service.list_scans(patient_id=patient_id, page=1, page_size=1000)
    await scan_service.remove_images([s.storage_path for s in scans if s.storage_path])
    if not await patient_service.delete_patient(patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    return None
