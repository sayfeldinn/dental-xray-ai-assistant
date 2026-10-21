# Dental Abnormality Detection API

This is a FastAPI wrapper for the YOLOv8 dental abnormality detection model.

## Setup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Fetch the model weights. They are **not** tracked in git (22.6 MB; the repo
   guard fails CI on any committed `.pt` file — weights live on the Release so
   clones stay small):
   ```bash
   # run from the repo root
   gh release download v0.1-dental-yolov8s --pattern best.pt --dir ml
   ```
   Expected: `ml/best.pt`, 22,601,514 bytes, SHA-256
   `df4455861a67fd683a0ab44b0f461b889624b513738b7cbb6c0ea3adc033a2ed`.
   Paths are resolved relative to `ml/api/app.py` (not the working directory),
   in this order: `ml/best.pt`, `best.pt`.
   The server still starts without them, but `/predict` returns HTTP 500.

3. Run the server:
   ```bash
   cd api
   uvicorn app:app --host 0.0.0.0 --port 8001 --reload
   ```

   Port **8001** is deliberate: 8000 is the FastAPI backend and 5173 is the
   Vite dev server. The backend reaches this service via `ML_API_URL`
   (default `http://localhost:8001`).

## Usage

The API exposes a `/predict` endpoint that accepts image files via `multipart/form-data`.

Optional query parameters:

| param  | default | meaning                                                        |
| ------ | ------- | -------------------------------------------------------------- |
| `conf` | `0.2`   | Confidence floor. The backend forwards its own threshold here. |
| `imgsz`| native  | Inference size. Defaults to the image width (rounded to 32), clamped to 640–1024; the checkpoint was trained at 1024, but upscaling a small image past its native width only blurs it. |

You can test the API using curl:

```bash
curl -X POST "http://localhost:8001/predict?conf=0.2" \
  -H "accept: application/json" \
  -F "file=@path/to/your/panoramic_xray.jpg"
```

The response will be a JSON object containing the detected bounding boxes, their classes, and confidence scores:

```json
{
  "predictions": [
    {
      "class_id": 4,
      "class_name": "Caries",
      "confidence": 0.2446,
      "bbox": {
        "xmin": 330.71,
        "ymin": 187.76,
        "xmax": 343.17,
        "ymax": 207.79
      }
    }
  ],
  "model_version": "yolov8s-dental-1.0@best.pt",
  "params": { "conf": 0.2, "imgsz": 640 }
}
```

Classes: `Inter-Radicular`, `Non-Odontogenic`, `Periapical`, `Pericoronal`, `Caries`.
Bounding boxes are in absolute pixels of the uploaded image, which is what the
Review screen expects.

## Notes on thresholds

The reference checkpoint scores mAP50 = 0.379 on its validation split. On the
bundled sample image (`frontend/public/demo/panorama-xray.jpg`, 640x336) the
best detection is ~0.24, so a floor above ~0.25 returns nothing. The backend's
`ML_DEFAULT_CONFIDENCE` is 0.2 to match, and every detection is shown to the
dentist with its confidence for accept/reject before it is used.
