"""
ML inference API endpoints.
Week 2: Provides inference capabilities to the frontend.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from pydantic import BaseModel
from app.schemas.scan import Finding
from app.services.ml_service import MLInferenceService, get_ml_service
from app.core.supabase import get_supabase_service
from app.utils.auth import get_current_user_id
from supabase import Client

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


@router.post("/infer/{scan_id}")
async def infer_scan(
    scan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    ml_service: MLInferenceService = Depends(get_ml_service),
    supabase: Client = Depends(get_supabase_service)
):
    """
    Run ML inference on a specific scan and save predictions to database.
    
    Steps:
    1. Get scan details from database
    2. Run ML inference on the image
    3. Save predictions to predictions table
    4. Update scan status to 'completed'
    """
    try:
        # Get scan details
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
        
        scan = scan_result.data
        image_url = scan.get("image_url")
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan has no image URL"
            )
        
        # Update scan status to processing
        supabase.table("scans").update({
            "status": "processing"
        }).eq("id", scan_id).execute()
        
        # Run ML inference
        try:
            findings = await ml_service.predict(image_url, confidence_threshold=0.5)
        except Exception as e:
            print(f"ML prediction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML prediction failed: {str(e)}"
            )
        
        # Save predictions to database
        predictions_data = []
        for finding in findings:
            try:
                prediction = {
                    "scan_id": scan_id,
                    "finding_type": str(finding.type.value if hasattr(finding.type, 'value') else finding.type),
                    "confidence": float(finding.confidence),
                    "bbox_x": int(finding.bounding_box.x),
                    "bbox_y": int(finding.bounding_box.y),
                    "bbox_width": int(finding.bounding_box.width),
                    "bbox_height": int(finding.bounding_box.height),
                    "tooth_number": str(finding.tooth_number) if finding.tooth_number else None,
                    "severity": str(finding.severity.value if hasattr(finding.severity, 'value') else finding.severity),
                    "notes": finding.description or ""
                }
                predictions_data.append(prediction)
            except Exception as e:
                print(f"Error processing finding: {str(e)}")
                print(f"Finding data: {finding}")
                raise
        
        # Insert predictions if any found
        if predictions_data:
            try:
                supabase.table("predictions").insert(predictions_data).execute()
            except Exception as e:
                print(f"Database insert error: {str(e)}")
                print(f"Predictions data: {predictions_data}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save predictions: {str(e)}"
                )
        
        # Update scan status to completed
        supabase.table("scans").update({
            "status": "completed",
            "findings": [f.model_dump() for f in findings]
        }).eq("id", scan_id).execute()
        
        return {
            "status": "success",
            "scan_id": scan_id,
            "findings_count": len(findings),
            "predictions": predictions_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Update scan status to failed
        print(f"Inference failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            supabase.table("scans").update({
                "status": "failed"
            }).eq("id", scan_id).execute()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )
