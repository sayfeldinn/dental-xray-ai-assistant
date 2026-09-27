# Dental Abnormality Detection API

This is a FastAPI wrapper for the YOLOv8 dental abnormality detection model.

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

You can test the API using curl:

```bash
curl -X POST "http://localhost:8000/predict" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@path/to/your/panoramic_xray.jpg"
```

The response will be a JSON object containing the detected bounding boxes, their classes, and confidence scores:

```json
{
  "predictions": [
    {
      "class_id": 4,
      "class_name": "Caries",
      "confidence": 0.8523,
      "bbox": {
        "xmin": 120.5,
        "ymin": 230.1,
        "xmax": 145.2,
        "ymax": 255.8
      }
    }
  ]
}
```
