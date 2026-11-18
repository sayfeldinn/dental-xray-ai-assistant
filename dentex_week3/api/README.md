# DENTEX v3 inference API

FastAPI wrapper for the production pipeline: 32-class FDI tooth detector +
4-class disease detector, joined by IoU/centre association, plus two advisory
layers. It generates the AI clinical report and forwards dentist feedback to the
offline learning queue. It never writes to the database and never prescribes.

## Endpoints

1. **`POST /predict`** — multipart `file`, optional `confidence_threshold`
   (default 0.20; the UI exposes 0.20 / 0.30 / 0.50).
   - Runs the v3 tooth + disease detectors and associates each lesion to an FDI tooth.
   - Returns the raw boxes and an **AI clinical report** built only from the core
     findings.
   - Appends advisory `findings` (`findings_advisory: true`) from the 11-class
     DentalOPG model when its weights are present.
   - Appends `missing_teeth` (`missing_teeth_advisory: true`) from the ResNet18
     classifier with a rule fallback (interior gaps only). Classifier: F1 **0.796**,
     P **0.896**, R **0.717**, validation AUC **0.931**; rule baseline F1 0.733.
   - Advisory layers are **not** part of the clinical report and must be shown as
     advisory in any UI.
   - Stores weights, thresholds and `pipeline_version` in `raw_ml_output.model`.

2. **`POST /findings`** — standalone run of the 11-class advisory findings detector
   (missing teeth, BDR, fillings, crowns, root canals, bridges, impactions,
   periapical abscess, periodontitis). Returns `"advisory": true`. Validated on
   DentalOPG only (in-hospital mAP@0.5 0.594; cross-hospital 0.118), so it stays
   advisory and out of the report.

3. **`POST /feedback/finding`** — dentist correction for a tooth/disease finding
   (e.g. `Caries` → `Deep Caries`, or false positive). Appends to
   `feedback/dentist_finding_feedback.csv` for the offline queue.

4. **`POST /feedback/report`** — accept/edit feedback on the generated report.
   Appends to `feedback/dentist_report_feedback.csv`.

## Setup

```bash
./start.sh          # creates/uses venv, checks weights, starts uvicorn on :8001
```

The script requires `../production/tooth_best.pt` and
`../production/disease_best.pt`; it warns (but still starts) if
`findings_best.pt` or `missing_teeth.pt` is absent. Fetch the public v3 release
from the repository root:

```bash
./notebooks/fetch_release_weights.sh
```

Then open `http://localhost:8001/docs`. The backend calls this service through
`ML_SERVICE_URL` (default `http://localhost:8001`).

## Notes

- The judge for model changes is `../evaluate.py` (repo root:
  `dentex_week3/evaluate.py`) on locked-50; this API wrapper is not a model.
- `findings` and `missing_teeth` are advisory only. Do not merge them into the
  report or the treatment engine.
- The service is stateless apart from the feedback CSV files; restarting it does not
  lose the database state.
