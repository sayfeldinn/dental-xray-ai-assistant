"""
Patient management endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse
)
from app.services.patient_service import PatientService, get_patient_service
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    current_user_id: str = Depends(get_current_user_id),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Create a new patient record."""
    try:
        return await patient_service.create_patient(patient, current_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create patient: {str(e)}"
        )


@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id),
    patient_service: PatientService = Depends(get_patient_service)
):
    """List all patients for the current dentist with pagination and search."""
    skip = (page - 1) * page_size
    
    try:
        patients, total = await patient_service.list_patients(
            dentist_id=current_user_id,
            skip=skip,
            limit=page_size,
            search=search
        )
        
        return PatientListResponse(
            patients=patients,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list patients: {str(e)}"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user_id: str = Depends(get_current_user_id),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Get a specific patient by ID."""
    patient = await patient_service.get_patient(patient_id, current_user_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    current_user_id: str = Depends(get_current_user_id),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Update a patient record."""
    patient = await patient_service.update_patient(
        patient_id, current_user_id, patient_data
    )
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    current_user_id: str = Depends(get_current_user_id),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Delete a patient record."""
    success = await patient_service.delete_patient(patient_id, current_user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return None
