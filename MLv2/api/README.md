# DENTEX Multi-Stage Detection API

This is a FastAPI wrapper for the multi-stage DENTEX pipeline. It coordinates 6 separate YOLOv8 models (Coordinator, 4 Enumerators, Global Disease Detector) to map detected diseases precisely to quadrant and tooth numbers.

## Architecture
1. **Coordinator:** Detects 4 anatomical quadrants.
2. **Enumerators:** 4 independent models to crop quadrants and enumerate teeth (1-8).
3. **Disease Detector:** Global detector for Caries, Deep Caries, Periapical Lesions, and Impacted Teeth.
4. **Integration (this API):** Uses Intersection over Union (IoU) to associate the disease box with the local tooth box mathematically.

## Setup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   cd api
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

The API exposes a `/predict` endpoint that accepts image files via `multipart/form-data`.

You can test the API using your browser at `http://localhost:8000/docs`, or using curl:

```bash
curl -X POST "http://localhost:8000/predict" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@path/to/your/panoramic_xray.jpg"
```

The response will be a JSON array containing the detected abnormalities mapped directly to a quadrant and tooth number:

```json
{
  "predictions": [
    {
      "quadrant": 4,
      "tooth": 7,
      "disease": "Deep Caries",
      "confidence": 0.892,
      "disease_bbox": { "xmin": 100, "ymin": 200, "xmax": 150, "ymax": 250 },
      "tooth_bbox": { "xmin": 90, "ymin": 190, "xmax": 160, "ymax": 260 }
    }
  ]
}
```
