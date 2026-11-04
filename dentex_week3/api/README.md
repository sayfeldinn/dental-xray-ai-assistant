# DENTEX Week 3 API

This is the API wrapper for the Week 3 production pipeline, which includes the AI Clinical Report Generator and the Dentist Feedback Learning Pipeline.

## Endpoints

1. **`POST /predict`**
   - Upload a panoramic X-ray image.
   - Runs the v3 pipeline (32-class FDI tooth detector + 4-class disease detector, joined by IoU / centre association).
   - Generates and returns an **AI Clinical Report** in plain text based on the detected clinical facts.
   - Returns the raw bounding box data alongside the report.
   - Also appends an advisory `findings` list (`findings_advisory: true`) from the DentalOPG model.
   - Also appends `missing_teeth` (`missing_teeth_advisory: true`), derived from the FDI teeth (interior gaps only; F1 0.74 on the DENTEX held-out 94).

2. **`POST /findings`**
   - Upload a panoramic X-ray image.
   - Runs the advisory 11-class findings detector (missing teeth, BDR, fillings, crowns, root canals, bridges, impactions, periapical abscess, periodontitis).
   - Returns `"advisory": true`. The model is validated on DentalOPG only and has no DENTEX ground truth, so it is kept out of `/predict`.

3. **`POST /feedback/finding`**
   - Submit feedback on a specific tooth/disease finding (e.g., Dentist corrects "Caries" to "Deep Caries" or marks a false positive).
   - Automatically appends to `feedback/dentist_finding_feedback.csv` for the offline learning queue.

4. **`POST /feedback/report`**
   - Submit feedback on the generated AI report (e.g., Dentist accepts the report, or provides an edited version).
   - Automatically appends to `feedback/dentist_report_feedback.csv`.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Test using the interactive Swagger UI at `http://localhost:8000/docs`.
