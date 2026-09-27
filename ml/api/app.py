import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import uvicorn

app = FastAPI(
    title="Dental Abnormality Detection API",
    description="API for detecting dental abnormalities in panoramic X-rays using YOLOv8",
    version="1.0.0",
)

# Load the best frozen checkpoint
# Adjust the path if the app is run from a different working directory
MODEL_PATH = "../best.pt"
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    model = None
    print(f"Failed to load model from {MODEL_PATH}: {e}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Dental Abnormality Detection API is running."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded correctly.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        # Run inference
        results = model(image, imgsz=1024, conf=0.25)
        
        predictions = []
        # Parse results
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # get bounding box coordinates in (x1, y1, x2, y2) format
                b = box.xyxy[0].tolist() 
                c = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                
                # Fetch class name if available, else use class ID
                class_name = model.names[c] if hasattr(model, 'names') else str(c)

                predictions.append({
                    "class_id": c,
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "bbox": {
                        "xmin": round(b[0], 2),
                        "ymin": round(b[1], 2),
                        "xmax": round(b[2], 2),
                        "ymax": round(b[3], 2)
                    }
                })

        return JSONResponse(content={"predictions": predictions})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
