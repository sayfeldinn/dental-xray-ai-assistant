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


@router.get("/{scan_id}")
async def get_scan_recommendations(
    scan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Get treatment recommendations for a scan based on ML predictions.
    
    This endpoint reads the predictions from the database for a specific scan,
    then generates treatment recommendations for each finding.
    """
    try:
        # Get scan details
        scan_result = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
        if not scan_result.data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan = scan_result.data
        
        # Get patient details for contraindication checking
        patient_result = supabase.table("patients").select("*").eq(
            "id", scan["patient_id"]
        ).single().execute()
        
        if not patient_result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient = patient_result.data
        
        # Get predictions for this scan
        predictions_result = supabase.table("predictions").select("*").eq(
            "scan_id", scan_id
        ).execute()
        
        predictions = predictions_result.data or []
        
        # Generate recommendations for each prediction
        recommendations = []
        for pred in predictions:
            # Create Finding object from prediction
            finding = Finding(
                type=pred.get("finding_type", "caries"),
                severity=pred.get("severity", "moderate"),
                confidence=pred.get("confidence", 0.8),
                bbox_x=pred.get("bbox_x", 0),
                bbox_y=pred.get("bbox_y", 0),
                bbox_width=pred.get("bbox_width", 100),
                bbox_height=pred.get("bbox_height", 100),
                tooth_number=pred.get("tooth_number"),
                notes=pred.get("notes", "")
            )
            
            # Generate treatment recommendation
            rec = recommendation_engine.recommend_treatment(
                finding=finding,
                patient_allergies=patient.get("allergies", []),
                patient_medications=patient.get("current_medications", []),
                patient_conditions=patient.get("medical_conditions", [])
            )
            
            if rec:
                # Convert to dict and add finding info
                rec_dict = rec.model_dump()
                rec_dict["finding_type"] = pred.get("finding_type")
                rec_dict["severity"] = pred.get("severity")
                rec_dict["tooth_number"] = pred.get("tooth_number")
                rec_dict["confidence"] = pred.get("confidence")
                
                # Format medications for frontend
                medications_formatted = []
                for prescription in rec_dict.get("prescriptions", []):
                    medications_formatted.append({
                        "name": prescription.get("drug_name"),
                        "dosage": f"{prescription.get('dosage')} {prescription.get('frequency')}",
                        "duration": prescription.get("duration"),
                        "instructions": prescription.get("instructions")
                    })
                
                rec_dict["medications"] = medications_formatted
                rec_dict["treatment"] = rec_dict.get("description", "")
                
                recommendations.append(rec_dict)
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )
