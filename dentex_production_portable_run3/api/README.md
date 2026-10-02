# DENTEX Production API (Run 3)

This is the FastAPI wrapper for the **Run 3 Production Configuration** of the DENTEX pipeline.

This updated architecture removes the local YOLO enumerator models and instead uses a highly accurate **Random Forest (RF)** model for tooth association, resolving previous edge cases with missing teeth numbering shifts by using engineered spatial features.

## Setup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

Test the API via the interactive swagger UI at `http://localhost:8000/docs`, or use `curl`:

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/panoramic.png"
```

The endpoint uses the `inference_pipeline.py` script to generate a highly detailed JSON response containing detected quadrants, disease boxes, and their mathematically associated tooth IDs based on the 75.4% benchmarked RF model.
