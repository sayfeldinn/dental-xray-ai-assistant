"""
Treatment recommendation endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.scan import Finding
from app.schemas.treatment import TreatmentCreate
from app.services.recommendation_engine import recommendation_engine
from app.core.supabase import get_supabase_service
from app.utils.auth import get_current_user_id
from supabase import Client

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationRequest(BaseModel):
    """Request schema for treatment recommendation."""
    finding: Finding
    patient_id: str


class ContraindicationCheckRequest(BaseModel):
    """Request schema for contraindication check."""
    drug_name: str
    patient_id: str


class ContraindicationCheckResponse(BaseModel):
    """Response schema for contraindication check."""
    safe: bool
    warnings: List[str]


@router.post("/treatment", response_model=TreatmentCreate)
async def recommend_treatment(
    request: RecommendationRequest = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Generate treatment recommendation based on a detected finding.
    
    This endpoint takes a finding (from AI detection) and patient context,
    then returns a recommended treatment plan with prescriptions and
    contraindication checks.
    """
    try:
        # Get patient data for contraindication checking
        patient_result = supabase.table("patients").select("*").eq(
            "id", request.patient_id
        ).eq(
            "dentist_id", current_user_id
        ).single().execute()
        
        if not patient_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        patient = patient_result.data
        
        # Generate recommendation
        recommendation = recommendation_engine.recommend_treatment(
            finding=request.finding,
            patient_allergies=patient.get("allergies", []),
            patient_medications=patient.get("current_medications", []),
            patient_conditions=patient.get("medical_conditions", [])
        )
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate recommendation for this finding type"
            )
        
        # Set patient_id
        recommendation.patient_id = request.patient_id
        
        return recommendation
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate recommendation: {str(e)}"
        )


@router.post("/check-contraindication", response_model=ContraindicationCheckResponse)
async def check_contraindication(
    request: ContraindicationCheckRequest = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Check for contraindications and drug interactions for a specific drug.
    
    This endpoint is used when a dentist wants to prescribe a drug
    and needs to verify it's safe for the patient.
    """
    try:
        # Get patient data
        patient_result = supabase.table("patients").select("*").eq(
            "id", request.patient_id
        ).eq(
            "dentist_id", current_user_id
        ).single().execute()
        
        if not patient_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        patient = patient_result.data
        
        # Check contraindications
        result = recommendation_engine.check_prescription_safety(
            drug_name=request.drug_name,
            patient_allergies=patient.get("allergies", []),
            patient_medications=patient.get("current_medications", []),
            patient_conditions=patient.get("medical_conditions", [])
        )
        
        return ContraindicationCheckResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to check contraindication: {str(e)}"
        )


@router.get("/drugs")
async def list_available_drugs():
    """
    List all drugs available in the recommendation system.
    
    Returns drug database with dosage information and contraindications.
    """
    return {
        "drugs": recommendation_engine.DRUGS_DATABASE
    }


@router.get("/finding-mappings")
async def list_finding_mappings():
    """
    List all finding-to-treatment mappings.
    
    Returns the current finding-to-treatment mapping table.
    Week 1: Returns placeholder data.
    Week 2+: Returns dentist-validated mappings.
    """
    return {
        "mappings": recommendation_engine.FINDING_TO_TREATMENT_MAP,
        "note": "Week 1 placeholder data - to be validated by partner dentist"
    }
