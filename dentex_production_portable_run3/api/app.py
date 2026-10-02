import os
import sys
import io
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Add parent directory to sys.path to import the inference pipeline
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PARENT_DIR)

try:
    from inference_pipeline import run_dentex_pipeline
    models_loaded = True
except Exception as e:
    models_loaded = False
    print(f"Error loading models or pipeline: {e}")

app = FastAPI(
    title="DENTEX Production API (Run 3)",
    description="API for detecting dental abnormalities using the Coordinator + Disease YOLO models and RF Tooth Association.",
    version="3.0.0",
)

@app.get("/")
def health_check():
    if not models_loaded:
        return {"status": "error", "message": "Models failed to load. Check pipeline_config.json paths."}
    return {"status": "ok", "message": "DENTEX Run 3 API is up and running."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not models_loaded:
        raise HTTPException(status_code=500, detail="Models not loaded correctly.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        # Run the untouched benchmark pipeline
        results = run_dentex_pipeline(image_np)
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference pipeline failed: {e}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
