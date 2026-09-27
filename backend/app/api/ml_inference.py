"""
ML inference API endpoints.
Week 2: Provides inference capabilities to the frontend.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from pydantic import BaseModel
from app.schemas.scan import Finding
from app.services.ml_service import MLInferenceService, get_ml_service
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/ml", tags=["ML Inference"])


class InferenceRequest(BaseModel):
    """Request schema for ML inference."""
    image_url: str
    confidence_threshold: float = 0.5


class InferenceResponse(BaseModel):
    """Response schema for ML inference."""
    findings: List[Finding]
    model_version: str
    processing_time_ms: float = 0.0


@router.post("/predict", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    current_user_id: str = Depends(get_current_user_id),
    ml_service: MLInferenceService = Depends(get_ml_service)
):
    """
    Run ML inference on an X-ray image.
    
    This endpoint:
    1. Takes an image URL from Supabase storage
    2. Runs the detection model
    3. Returns findings with bounding boxes
    
    Week 2: Returns mock predictions for demonstration.
    """
    try:
        findings = await ml_service.predict(
            request.image_url,
            request.confidence_threshold
        )
        
        model_info = ml_service.get_model_info()
        
        return InferenceResponse(
            findings=findings,
            model_version=model_info["model_version"],
            processing_time_ms=125.0  # Mock processing time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )


@router.get("/model-info")
async def get_model_info(
    ml_service: MLInferenceService = Depends(get_ml_service)
):
    """
    Get information about the loaded ML model.
    
    Returns model version, supported findings, and status.
    """
    return ml_service.get_model_info()
