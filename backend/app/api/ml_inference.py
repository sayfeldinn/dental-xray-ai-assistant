"""
ML inference API endpoints.
Provides inference capabilities to the frontend.
"""
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from supabase import Client

from app.core.config import settings
from app.core.supabase import get_supabase_service
from app.schemas.prediction import PredictionResponse, findings_to_prediction_rows, rows_to_predictions
from app.schemas.scan import Finding, Quadrant
from app.services.ml_service import MLInferenceService, get_ml_service
from app.services.prediction_service import save_predictions, save_scan_findings
from app.utils.auth import get_current_user_id
from app.utils.records import require_scan

router = APIRouter(prefix="/ml", tags=["ML Inference"])


class InferenceRequest(BaseModel):
    """Request schema for ML inference."""
    image_url: str
    confidence_threshold: float = settings.ML_DEFAULT_CONFIDENCE


class InferenceResponse(BaseModel):
    """Response schema for ML inference."""
    model_config = {"protected_namespaces": ()}

    findings: List[Finding]
    model_version: str
    processing_time_ms: float = 0.0
    ai_report: Optional[str] = None
    quadrants: List[Quadrant] = Field(default_factory=list)


class InferScanResponse(BaseModel):
    """Response for the scan-scoped inference trigger used by the UI."""
    model_config = {"protected_namespaces": ()}

    scan_id: str
    status: str
    findings: List[Finding]
    predictions: List[PredictionResponse]
    model_version: str
    mode: str
    processing_time_ms: float
    ai_report: Optional[str] = None
    quadrants: List[Quadrant] = Field(default_factory=list)
    warning: Optional[str] = None


@router.post("/predict", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    current_user_id: str = Depends(get_current_user_id),
    ml_service: MLInferenceService = Depends(get_ml_service)
):
    """
    Run ML inference on an X-ray image.

    Takes an image URL from Supabase storage (or a local path) and returns
    findings with bounding boxes.
    """
    started = time.perf_counter()
    try:
        findings = await ml_service.predict(
            request.image_url,
            request.confidence_threshold
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Inference failed: {str(e)}"
        )

    model_info = ml_service.get_model_info()

    return InferenceResponse(
        findings=findings,
        model_version=model_info["model_version"],
        processing_time_ms=round((time.perf_counter() - started) * 1000, 1),
        ai_report=ml_service.ai_report,
        quadrants=ml_service.quadrants,
    )


@router.post("/infer/{scan_id}", response_model=InferScanResponse, status_code=status.HTTP_201_CREATED)
async def infer_scan(
    scan_id: str,
    confidence_threshold: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Defaults to ML_DEFAULT_CONFIDENCE"
    ),
    current_user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_service),
    ml_service: MLInferenceService = Depends(get_ml_service)
):
    """
    Run inference for a stored scan and persist the detections.

    This is what the Analyze button calls: it loads the scan, runs the model,
    replaces the scan's ``predictions`` rows and marks the scan completed.
    Failures to persist are reported as ``warning`` rather than failing the
    request, so the caller still gets the detections that were produced.
    """
    scan = require_scan(supabase, scan_id, current_user_id)
    threshold = (
        settings.ML_DEFAULT_CONFIDENCE
        if confidence_threshold is None
        else confidence_threshold
    )

    started = time.perf_counter()
    try:
        findings = await ml_service.predict(scan.get("image_url"), threshold)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Inference failed: {str(e)}"
        )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    # Read the extras off the service after predict(); they belong to the call
    # that just happened, not to the service's configuration.
    ai_report = ml_service.ai_report
    quadrants = ml_service.quadrants

    updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    warnings = [
        warning
        for warning in (
            await save_predictions(supabase, scan, current_user_id, findings),
            await save_scan_findings(
                supabase,
                scan_id,
                findings,
                "completed",
                updated_at,
                ai_report=ai_report,
                quadrants=quadrants,
            ),
        )
        if warning
    ]

    model_info = ml_service.get_model_info()
    rows = findings_to_prediction_rows(findings, scan_id=scan_id, dentist_id=current_user_id)

    return InferScanResponse(
        scan_id=scan_id,
        status="completed",
        findings=findings,
        predictions=rows_to_predictions(rows),
        model_version=model_info["model_version"],
        mode=model_info["mode"],
        processing_time_ms=elapsed_ms,
        ai_report=ai_report,
        quadrants=quadrants,
        warning="; ".join(warnings) if warnings else None,
    )


@router.get("/model-info")
async def get_model_info(
    ml_service: MLInferenceService = Depends(get_ml_service)
):
    """
    Get information about the loaded ML model.

    Returns the model version, supported findings, configured detector URL and
    whether that detector is currently answering.
    """
    return await ml_service.probe()
