"""
DentalAI - Patient API Endpoints
CRUD operations for patient records.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.domain.patient import (
    Patient,
    PatientCreate,
    PatientUpdate,
    PatientListResponse
)
from app.services.supabase_client import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=Patient, status_code=201)
async def create_patient(patient_data: PatientCreate):
    """
    Create a new patient record.
    
    **Step 1 in Clinical Loop**: Patient registration before scan ingestion.
    """
    try:
        patient = await patient_service.create_patient(patient_data)
        return patient
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: UUID):
    """
    Retrieve a patient by ID.
    """
    patient = await patient_service.get_patient(patient_id)
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient


@router.get("", response_model=PatientListResponse)
async def list_patients(
    dentist_id: Optional[UUID] = Query(None, description="Filter by dentist"),
    search: Optional[str] = Query(None, description="Search in patient names"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page")
):
    """
    List patients with optional filtering and pagination.
    """
    patients, total = await patient_service.list_patients(
        dentist_id=dentist_id,
        search=search,
        page=page,
        page_size=page_size
    )
    
    return PatientListResponse(
        patients=patients,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(patient_id: UUID, patient_data: PatientUpdate):
    """
    Update patient record.
    
    Critical for updating allergies, medications, and conditions that affect
    contraindication checking in Steps 4-5.
    """
    patient = await patient_service.update_patient(patient_id, patient_data)
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(patient_id: UUID):
    """
    Delete a patient record.
    
    **Warning**: This cascades to all related scans, findings, and treatments.
    """
    success = await patient_service.delete_patient(patient_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return None
