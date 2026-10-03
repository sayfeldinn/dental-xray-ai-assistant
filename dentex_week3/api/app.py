import os
import sys
import io
import csv
import json
from datetime import datetime
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

# Setup paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROD_DIR = os.path.join(BASE_DIR, "production")
FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")
sys.path.append(PROD_DIR)

try:
    from inference_pipeline import run_dentex_pipeline
    models_loaded = True
except Exception as e:
    models_loaded = False
    print(f"Error loading production pipeline: {e}")

app = FastAPI(
    title="DENTEX Week 3 API (AI Report & Feedback)",
    description="API for running the dental model, generating clinical reports, and collecting dentist feedback.",
    version="4.0.0",
)

# --- Models for Feedback API ---
class FindingFeedback(BaseModel):
    image_id: str
    quadrant: int
    tooth: int
    original_disease: str
    is_correct: bool
    corrected_disease: Optional[str] = None
    notes: Optional[str] = None

class ReportFeedback(BaseModel):
    image_id: str
    report_accepted: bool
    edited_report_text: Optional[str] = None
    dentist_comments: Optional[str] = None

# --- Report Generator ---
def generate_clinical_report(detections):
    if not detections:
        return "Clinical Findings: No abnormalities detected in the provided panoramic radiograph. Routine monitoring recommended."
    
    report = "Clinical Radiographic Findings:\n\n"
    for d in detections:
        quad = d.get('quadrant', 'Unknown')
        tooth = d.get('tooth', 'Unknown')
        disease = d.get('disease', 'Unknown')
        
        if disease.lower() == 'impacted':
            report += f"- Tooth {tooth} (Quadrant {quad}) appears to be impacted.\n"
        elif disease.lower() == 'caries':
            report += f"- Carious lesion detected on Tooth {tooth} (Quadrant {quad}).\n"
        elif disease.lower() == 'deep caries':
            report += f"- Deep carious lesion observed on Tooth {tooth} (Quadrant {quad}), potential pulpal involvement.\n"
        elif disease.lower() == 'periapical lesion':
            report += f"- Periapical radiolucency / lesion associated with Tooth {tooth} (Quadrant {quad}).\n"
        else:
            report += f"- {disease} identified on Tooth {tooth} (Quadrant {quad}).\n"
    
    report += "\nRecommendation: Clinical correlation and vitality testing advised for the noted areas."
    return report

@app.get("/")
def health_check():
    return {"status": "ok", "models_loaded": models_loaded}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not models_loaded:
        raise HTTPException(status_code=500, detail="Models not loaded.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # Run inference
    results = run_dentex_pipeline(image_np)
    
    # Generate structured report based on findings
    generated_report = generate_clinical_report(results.get("detections", []))
    
    # Attach report to the response
    results["ai_generated_report"] = generated_report
    
    return JSONResponse(content=results)

@app.post("/feedback/finding")
async def submit_finding_feedback(feedback: FindingFeedback):
    csv_path = os.path.join(FEEDBACK_DIR, "dentist_finding_feedback.csv")
    file_exists = os.path.isfile(csv_path)
    
    try:
        with open(csv_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "image_id", "quadrant", "tooth", "original_disease", "is_correct", "corrected_disease", "notes"])
            
            writer.writerow([
                datetime.now().isoformat(),
                feedback.image_id,
                feedback.quadrant,
                feedback.tooth,
                feedback.original_disease,
                feedback.is_correct,
                feedback.corrected_disease or "",
                feedback.notes or ""
            ])
        return {"status": "success", "message": "Finding feedback saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback/report")
async def submit_report_feedback(feedback: ReportFeedback):
    csv_path = os.path.join(FEEDBACK_DIR, "dentist_report_feedback.csv")
    file_exists = os.path.isfile(csv_path)
    
    try:
        with open(csv_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "image_id", "report_accepted", "edited_report_text", "dentist_comments"])
            
            writer.writerow([
                datetime.now().isoformat(),
                feedback.image_id,
                feedback.report_accepted,
                feedback.edited_report_text or "",
                feedback.dentist_comments or ""
            ])
        return {"status": "success", "message": "Report feedback saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
