# ML Model Switch Guide: dentex_week3

## Overview

This guide documents switching from the `dentex_production_portable_run3` model to the **`dentex_week3`** model for dental X-ray analysis.

## What Changed

### Model Location
- **Old:** `dentex_production_portable_run3/` (if it existed)
- **New:** `dentex_week3/`

### Model Architecture

The **dentex_week3** pipeline uses a **3-stage approach**:

1. **Coordinator Model** (`coordinator_best.pt`)
   - Detects and localizes 4 anatomical quadrants
   - YOLOv8 model trained on quadrant detection

2. **Disease Detector** (`disease_detector_best.pt`)
   - Runs on the full panoramic image
   - Detects 4 disease types:
     - Impacted teeth
     - Caries
     - Periapical Lesion
     - Deep Caries

3. **Tooth Association RF** (`tooth_association_rf_300.joblib`)
   - Random Forest classifier (300 estimators)
   - Associates detected diseases with specific tooth numbers (1-8)
   - Uses spatial features and disease-tooth relationships

### Model Performance (Validation Metrics)

From the frozen evaluation:
- **Tooth Accuracy:** 76.23%
- **Disease Accuracy:** 97.54%
- **Full Match Accuracy:** 75.41%
- Evaluated on 23 held-out images with 122 detections

## Files Modified

### 1. Pipeline Configuration ✅
**File:** `dentex_week3/production/pipeline_config.json`

**Changed:**
```json
// OLD (Windows absolute paths)
"coordinator_model": "D:/pes/dentex_week3_FINAL/dentex_week3/production/coordinator_best.pt",
"disease_model": "D:/pes/dentex_week3_FINAL/dentex_week3/production/disease_detector_best.pt"

// NEW (Relative paths)
"coordinator_model": "coordinator_best.pt",
"disease_model": "disease_detector_best.pt"
```

### 2. Inference Pipeline ✅
**File:** `dentex_week3/production/inference_pipeline.py`

**Changed:**
```python
# OLD
COORDINATOR_PATH = CONFIG["coordinator_model"]
DISEASE_PATH = CONFIG["disease_model"]

# NEW (Resolves relative to production directory)
COORDINATOR_PATH = os.path.join(PACKAGE_DIR, CONFIG["coordinator_model"])
DISEASE_PATH = os.path.join(PACKAGE_DIR, CONFIG["disease_model"])
```

## Directory Structure

```
dentex_week3/
├── api/
│   ├── app.py                    # FastAPI server
│   ├── requirements.txt
│   └── README.md
├── production/
│   ├── coordinator_best.pt       # Quadrant detection model
│   ├── disease_detector_best.pt  # Disease detection model
│   ├── tooth_association_rf_300.joblib  # Tooth association RF
│   ├── inference_pipeline.py     # Main pipeline logic
│   ├── pipeline_config.json      # Configuration ✅ UPDATED
│   └── final_evaluation.json     # Performance metrics
└── feedback/
    ├── dentist_finding_feedback.csv
    └── dentist_report_feedback.csv
```

## Configuration

### Backend Environment Variables

Update `backend/.env`:

```env
# ML detector (points to dentex_week3 API)
ML_API_URL=http://localhost:8001
ML_TIMEOUT_SECONDS=60
ML_ALLOW_MOCK_FALLBACK=true
ML_DEFAULT_CONFIDENCE=0.2
```

**Note:** The dentex_week3 API runs on port 8000 by default (in the README), but we're using port 8001 to avoid conflicts with the backend. Update the app.py startup port if needed.

### dentex_week3 API Port

The API README shows port 8000, but to avoid conflict with the backend:

**Option 1: Run on port 8001 (recommended)**
```bash
cd dentex_week3/api
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

**Option 2: Update app.py**
```python
# In dentex_week3/api/app.py, change:
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
```

## API Endpoints

The dentex_week3 API provides:

### `GET /`
Health check - returns model loading status

### `POST /predict`
Main inference endpoint:
- **Input:** X-ray image (multipart/form-data)
- **Output:**
  ```json
  {
    "image_width": 2976,
    "image_height": 1536,
    "quadrants": [...],
    "detections": [
      {
        "quadrant": 1,
        "tooth": "Tooth_4",
        "disease": "Caries",
        "disease_confidence": 0.85,
        "tooth_confidence": 0.92,
        "association_confidence": 0.782,
        "box": [x1, y1, x2, y2]
      }
    ],
    "num_detections": 3,
    "ai_generated_report": "Clinical Radiographic Findings:..."
  }
  ```

### `POST /feedback/finding`
Submit dentist corrections on individual findings

### `POST /feedback/report`
Submit dentist feedback on AI-generated reports

## Setup and Testing

### 1. Install Dependencies

```bash
cd dentex_week3/api
pip install -r requirements.txt
```

### 2. Verify Model Files Exist

```bash
ls -lh dentex_week3/production/*.pt
ls -lh dentex_week3/production/*.joblib
```

Should show:
- `coordinator_best.pt` (~6MB)
- `disease_detector_best.pt` (~6MB)
- `tooth_association_rf_300.joblib` (~1MB)

### 3. Start the API

```bash
cd dentex_week3/api
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Test the API

**Health Check:**
```bash
curl http://localhost:8001/
```

Expected:
```json
{"status": "ok", "models_loaded": true}
```

**Inference Test:**
```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/xray.jpg"
```

### 5. Update Backend Configuration

Make sure `backend/.env` has:
```env
ML_API_URL=http://localhost:8001
```

Then restart the backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 6. Test Full Integration

1. Start dentex_week3 API: `cd dentex_week3/api && uvicorn app:app --port 8001 --reload`
2. Start backend: `cd backend && uvicorn app.main:app --port 8000 --reload`
3. Start frontend: `cd frontend && npm run dev`
4. Upload an X-ray scan
5. Click "Analyze"
6. Verify results appear

## Verification Script

Create a test script to verify the models load correctly:

```bash
cd dentex_week3/api
python3 -c "
import sys
sys.path.append('../production')
from inference_pipeline import run_dentex_pipeline
print('✅ Models loaded successfully')
"
```

## Disease Mapping

The model detects 4 disease types:

| Disease ID | Disease Name | Description |
|------------|-------------|-------------|
| 0 | Impacted | Impacted teeth |
| 1 | Caries | Carious lesion (cavity) |
| 2 | Periapical Lesion | Infection at tooth root |
| 3 | Deep Caries | Deep cavity (near pulp) |

## Tooth Numbering

Each quadrant has 8 teeth (Tooth_1 to Tooth_8):

| Quadrant | Location | Teeth |
|----------|----------|-------|
| 1 | Upper Right | 11-18 (FDI notation) |
| 2 | Upper Left | 21-28 (FDI notation) |
| 3 | Lower Left | 31-38 (FDI notation) |
| 4 | Lower Right | 41-48 (FDI notation) |

The output format is: `Quadrant X, Tooth Y` → FDI notation: `XY`

Example: Quadrant 1, Tooth 4 → FDI 14 (Upper right first premolar)

## Differences from Other Models

### vs. MLv2 (6-model pipeline)
- **MLv2:** Uses 6 separate models (1 coordinator + 4 quadrant enumerators + 1 global disease)
- **dentex_week3:** Uses 3 models (1 coordinator + 1 global disease + 1 RF classifier)
- **Benefit:** Faster inference, simpler deployment, comparable accuracy

### vs. ml/api (single model)
- **ml/api:** Single YOLOv8 model for all detections
- **dentex_week3:** Multi-stage pipeline with spatial reasoning
- **Benefit:** Better tooth localization accuracy (76% vs lower)

## Performance Considerations

### Inference Time
- Coordinator: ~50-100ms
- Disease Detector: ~100-200ms
- Tooth Association: ~5-10ms
- **Total:** ~200-300ms per image (depending on hardware)

### Memory Usage
- Models: ~15MB total on disk
- Runtime: ~500MB-1GB GPU memory (if available)
- CPU fallback: Supported (slower, ~1-2s per image)

### Confidence Thresholds
- **Coordinator:** 0.25 (fixed in code)
- **Disease Detector:** 0.20 (fixed in code)
- **Backend filter:** 0.20 (configurable via `ML_DEFAULT_CONFIDENCE`)

Lower the backend threshold to see more detections (may include false positives).

## Troubleshooting

### "Models not loaded" Error

**Check:**
```bash
cd dentex_week3/production
ls -lh *.pt *.joblib
```

If files are missing, download/copy the model weights.

### "No module named 'ultralytics'" Error

**Fix:**
```bash
cd dentex_week3/api
pip install -r requirements.txt
```

### Port Already in Use

**Check what's using port 8001:**
```bash
lsof -i :8001
```

**Kill the process or use a different port:**
```bash
uvicorn app:app --port 8002 --reload
# Then update ML_API_URL=http://localhost:8002
```

### Slow Inference

**Solutions:**
1. Install GPU-enabled PyTorch (if you have a GPU)
2. Reduce image size before upload
3. Run on dedicated GPU server
4. Use the mock fallback for UI testing (`ML_ALLOW_MOCK_FALLBACK=true`)

### Path Errors (Windows/Mac/Linux)

The code now uses `os.path.join()` which is cross-platform compatible. If you still have issues:

```python
# In inference_pipeline.py, verify:
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDINATOR_PATH = os.path.join(PACKAGE_DIR, CONFIG["coordinator_model"])
```

## Migration Checklist

- [x] Updated `pipeline_config.json` with relative paths
- [x] Updated `inference_pipeline.py` to resolve paths correctly
- [ ] Install dependencies: `pip install -r dentex_week3/api/requirements.txt`
- [ ] Verify model files exist in `dentex_week3/production/`
- [ ] Start dentex_week3 API on port 8001
- [ ] Update `backend/.env` with `ML_API_URL=http://localhost:8001`
- [ ] Restart backend server
- [ ] Test health check: `curl http://localhost:8001/`
- [ ] Test full workflow: Upload → Analyze → Review results

## Summary

✅ **Files Updated:**
- `dentex_week3/production/pipeline_config.json` - Relative paths
- `dentex_week3/production/inference_pipeline.py` - Path resolution

🔲 **Required Actions:**
1. Start dentex_week3 API on port 8001
2. Update backend `.env` to point to dentex_week3
3. Test the full upload → analyze workflow

📊 **Benefits:**
- ✅ Better tooth localization (76% accuracy)
- ✅ High disease classification (97% accuracy)
- ✅ AI-generated clinical reports
- ✅ Feedback collection for continuous improvement
- ✅ Cross-platform compatible paths

---

**Last Updated:** 2024-10-04
**Model Version:** dentex_week3 (Run 3, Step 51 RF_300)
