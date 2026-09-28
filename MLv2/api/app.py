import io
import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import uvicorn

app = FastAPI(
    title="DENTEX Multi-Stage Detection API",
    description="API for detecting dental abnormalities and mapping them to specific teeth using a 6-model YOLOv8 pipeline.",
    version="2.0.0",
)

# Base path for models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

# Load All 6 Models globally (loaded at startup)
try:
    coordinator = YOLO(os.path.join(MODELS_DIR, 'coordinator_quadrant', 'weights', 'best.pt'))
    enumerators = {
        1: YOLO(os.path.join(MODELS_DIR, 'enumerator_q1', 'weights', 'best.pt')),
        2: YOLO(os.path.join(MODELS_DIR, 'enumerator_q2', 'weights', 'best.pt')),
        3: YOLO(os.path.join(MODELS_DIR, 'enumerator_q3', 'weights', 'best.pt')),
        4: YOLO(os.path.join(MODELS_DIR, 'enumerator_q4', 'weights', 'best.pt'))
    }
    disease_detector = YOLO(os.path.join(MODELS_DIR, 'disease_detector', 'weights', 'best.pt'))
    models_loaded = True
except Exception as e:
    models_loaded = False
    print(f"Error loading models: {e}")

# Map YOLO classes back to DENTEX diagnoses 
DISEASE_MAP = {
    0: 'Impacted', 
    1: 'Caries', 
    2: 'Periapical Lesion', 
    3: 'Deep Caries'
}

def calculate_iou(boxA, boxB):
    # Calculate Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0: return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)

@app.get("/")
def health_check():
    if not models_loaded:
        return {"status": "error", "message": "Models failed to load."}
    return {"status": "ok", "message": "DENTEX Multi-Stage API is running."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not models_loaded:
        raise HTTPException(status_code=500, detail="Models not loaded correctly.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        image_bytes = await file.read()
        # Convert bytes to OpenCV format (BGR) since YOLO handles cv2 well
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        # A. Detect Diseases globally
        disease_results = disease_detector(img, verbose=False)[0].boxes
        diseases = []
        for d_box in disease_results:
            dx1, dy1, dx2, dy2 = map(int, d_box.xyxy[0].tolist())
            d_cls = int(d_box.cls[0].item())
            d_conf = float(d_box.conf[0].item())
            diseases.append({
                'box': [dx1, dy1, dx2, dy2], 
                'class': DISEASE_MAP.get(d_cls, f"Disease_{d_cls}"),
                'confidence': round(d_conf, 4)
            })
            
        # B. Detect Quadrants
        quadrant_results = coordinator(img, verbose=False)[0].boxes
        
        all_teeth = []
        
        # C. Detect Teeth per Quadrant
        for q_box in quadrant_results:
            q_cls = int(q_box.cls[0].item())
            q_num = q_cls + 1
            qx1, qy1, qx2, qy2 = map(int, q_box.xyxy[0].tolist())
            
            # Crop and run enumerator
            q_crop = img[qy1:qy2, qx1:qx2]
            if q_crop.shape[0] == 0 or q_crop.shape[1] == 0: continue
                
            tooth_results = enumerators[q_num](q_crop, verbose=False)[0].boxes
            
            for t_box in tooth_results:
                t_cls = int(t_box.cls[0].item())
                tooth_num = t_cls + 1 # YOLO classes 0-7 become Teeth 1-8
                
                # Shift local crop coordinates back to global full-image coordinates
                lx1, ly1, lx2, ly2 = map(int, t_box.xyxy[0].tolist())
                gx1, gy1, gx2, gy2 = lx1 + qx1, ly1 + qy1, lx2 + qx1, ly2 + qy1
                
                all_teeth.append({
                    'quadrant': q_num,
                    'tooth': tooth_num,
                    'box': [gx1, gy1, gx2, gy2]
                })
                
        # D. Match Diseases to Teeth via IoU
        final_diagnoses = []
        for disease in diseases:
            best_iou = 0
            assigned_tooth = None
            
            for tooth in all_teeth:
                iou = calculate_iou(disease['box'], tooth['box'])
                if iou > best_iou:
                    best_iou = iou
                    assigned_tooth = tooth
                    
            # Use a minimum overlap threshold to prevent false assignments (10% overlap minimum)
            if assigned_tooth and best_iou > 0.1: 
                final_diagnoses.append({
                    'quadrant': assigned_tooth['quadrant'],
                    'tooth': assigned_tooth['tooth'],
                    'disease': disease['class'],
                    'confidence': disease['confidence'],
                    'disease_bbox': {
                        "xmin": disease['box'][0],
                        "ymin": disease['box'][1],
                        "xmax": disease['box'][2],
                        "ymax": disease['box'][3]
                    },
                    'tooth_bbox': {
                        "xmin": assigned_tooth['box'][0],
                        "ymin": assigned_tooth['box'][1],
                        "xmax": assigned_tooth['box'][2],
                        "ymax": assigned_tooth['box'][3]
                    }
                })
                
        return JSONResponse(content={"predictions": final_diagnoses})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference pipeline failed: {e}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
