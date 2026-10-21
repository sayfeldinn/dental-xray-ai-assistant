import io
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import uvicorn

app = FastAPI(
    title="Dental Abnormality Detection API",
    description="API for detecting dental abnormalities in panoramic X-rays using YOLOv8",
    version="1.0.0",
)

# Load the best frozen checkpoint.
# Resolved from this file rather than the working directory, so the service
# behaves the same whether it is started from ml/api, the repo root or a
# process manager.
_ML_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = _ML_DIR.parent
_CANDIDATES = (
    _ML_DIR / "best.pt",
    _ROOT_DIR / "best.pt",
)
MODEL_PATH = next((path for path in _CANDIDATES if path.is_file()), _CANDIDATES[0])

try:
    model = YOLO(str(MODEL_PATH))
    print(f"Loaded detector weights from {MODEL_PATH}")
except Exception as e:
    model = None
    print(f"Failed to load model from {MODEL_PATH}: {e}")

# Inference defaults. The checkpoint was trained at imgsz=1024 on full-size
# radiographs; upscaling a small web-sized image past its native width only
# blurs it, so the working size is derived from the input and capped at the
# training resolution.
DEFAULT_CONF = 0.2
MIN_IMGSZ = 640
MAX_IMGSZ = 1024


def resolve_imgsz(image: Image.Image, requested: Optional[int]) -> int:
    """Pick an inference size: native width (rounded to 32) within bounds."""
    if requested:
        return requested
    native = -(-image.width // 32) * 32
    return max(MIN_IMGSZ, min(MAX_IMGSZ, native))


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Dental Abnormality Detection API is running.",
        "model_loaded": model is not None,
        "weights": str(MODEL_PATH),
        "classes": getattr(model, "names", None),
        "defaults": {"conf": DEFAULT_CONF, "imgsz": [MIN_IMGSZ, MAX_IMGSZ]},
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    conf: float = Query(DEFAULT_CONF, ge=0.0, le=1.0, description="Confidence floor"),
    imgsz: Optional[int] = Query(None, ge=320, le=2048, description="Inference size"),
):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded correctly.")

    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        size = resolve_imgsz(image, imgsz)
        results = model.predict(image, imgsz=size, conf=conf, verbose=False)

        predictions = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # bounding box coordinates in (x1, y1, x2, y2) format
                b = box.xyxy[0].tolist()
                c = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                class_name = model.names[c] if hasattr(model, "names") else str(c)

                predictions.append({
                    "class_id": c,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "xmin": round(b[0], 2),
                        "ymin": round(b[1], 2),
                        "xmax": round(b[2], 2),
                        "ymax": round(b[3], 2),
                    },
                })

        return JSONResponse(content={
            "predictions": predictions,
            "model_version": f"yolov8s-dental-1.0@{MODEL_PATH.name}",
            "params": {"conf": conf, "imgsz": size},
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

if __name__ == "__main__":
    # Port 8001 keeps the detector alongside the backend (8000) and the
    # frontend dev server (5173) instead of competing with them.
    uvicorn.run("app:app", host="0.0.0.0", port=8001)
