# DentalAI Backend Service

Clean FastAPI backend for IEEE IC-FTAI dental decision-support system.

## Architecture

This backend implements the 6-step clinical loop:

1. **Scan Ingestion** → Upload panoramic X-ray to Supabase Storage
2. **AI Detection** → Call dentex_week3 microservice for analysis
3. **Dentist Validation** → Review and confirm/reject/modify findings
4. **Recommendation Engine** → Rule-based treatment + drug proposals (Phase 3 ✅)
5. **Dentist Confirmation** → Accept/modify/reject prescriptions behind contraindication gates (Phase 3 ✅)
6. **Feedback Logging** → Audit trail for active learning (Phase 4 ✅)

## Directory Structure

```
backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── patients.py      # Patient CRUD
│   │   ├── scans.py         # Scan upload & analysis
│   │   ├── findings.py      # Finding review
│   │   ├── recommendations.py  # Step 4: generate proposals
│   │   ├── treatments.py    # Step 5: review/decide treatments
│   │   └── prescriptions.py # Step 5: safety check + decide prescriptions
│   ├── api/deps.py          # get_workflow() dependency
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   └── supabase_client.py  # Supabase client factory
│   ├── domain/              # Pydantic domain models
│   │   ├── patient.py, scan.py, finding.py
│   │   ├── treatment.py, prescription.py, recommendation.py
│   │   └── errors.py        # NotFound/Conflict/RuleViolation -> 404/409/422
│   ├── services/            # Business logic layer
│   │   ├── ml_client/       # Dentex ML service client
│   │   ├── supabase_client/ # Database services
│   │   ├── contraindication/  # PURE safety rules (catalog, matcher, checker)
│   │   ├── recommendation/    # PURE finding -> treatment + drugs
│   │   └── clinical_workflow.py  # orchestration + dentist-decision policy
│   └── main.py              # FastAPI application
├── tests/                   # pytest suite (171 tests, no network)
└── requirements.txt         # Python dependencies
```

## Quick Start

### 1. Prerequisites

- Python 3.11 or 3.12 (**not 3.14**; `start.sh` enforces this)
- Virtual environment tool (venv, conda, etc.)
- Supabase project configured (Phase 1 complete)
- dentex_week3 ML service running on port 8001

### 2. Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Environment variables are loaded from the root `.env` file (already configured in Phase 1).

Required variables:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ML_SERVICE_URL` (default: http://localhost:8001)

### 4. Run Development Server

```bash
# From backend directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Detailed health status

### Patients (`/api/v1/patients`)
- `POST /api/v1/patients` - Create patient
- `GET /api/v1/patients` - List patients (with search & pagination)
- `GET /api/v1/patients/{id}` - Get patient details
- `PUT /api/v1/patients/{id}` - Update patient
- `DELETE /api/v1/patients/{id}` - Delete patient

### Scans (`/api/v1/scans`)
- `POST /api/v1/scans/upload` - Upload & analyze X-ray (JPEG/PNG/WebP, max 20 MB; AI failure = 502, scan kept)
- `POST /api/v1/scans/{id}/reanalyze` - Re-run AI on the stored image (409 once any finding is reviewed)
- `GET /api/v1/scans?patient_id=` - List a patient's scans (image URLs are signed, 1 h)
- `GET /api/v1/scans/{id}` - Get scan details
- `GET /api/v1/scans/{id}/findings` - Get findings for scan
- `PUT /api/v1/scans/{id}` - Update scan
- `DELETE /api/v1/scans/{id}` - Delete scan

### Findings (`/api/v1/findings`)
- `GET /api/v1/findings` - List findings (by patient or scan)
- `GET /api/v1/findings/{id}` - Get finding details
- `POST /api/v1/findings/review` - Dentist review finding
- `GET /api/v1/findings/scan/{scan_id}/confirmed` - Get dentist-validated (confirmed + modified) findings
- `PUT /api/v1/findings/{id}` - Update finding

### Recommendations (`/api/v1/recommendations`) — Phase 3
- `POST /api/v1/recommendations/scans/{scan_id}` - Generate treatment + drug proposals (body optional: `clinical_context.active_infection` / `pain`)

### Treatments (`/api/v1/treatments`) — Phase 3
- `POST /api/v1/treatments` - Dentist-authored treatment (stored confirmed)
- `GET /api/v1/treatments?scan_id=|patient_id=` - List with prescriptions
- `GET /api/v1/treatments/{id}` - Get one
- `POST /api/v1/treatments/{id}/decision` - Confirm / modify / cancel

### Prescriptions (`/api/v1/prescriptions`) — Phase 3
- `POST /api/v1/prescriptions` - Dentist-authored prescription on a decided treatment (safety-checked, still needs a decision)
- `GET /api/v1/prescriptions?treatment_id=|patient_id=` - List
- `GET /api/v1/prescriptions/{id}` - Get one
- `POST /api/v1/prescriptions/check` - Stateless contraindication check
- `POST /api/v1/prescriptions/{id}/decision` - Accept / modify / reject (`acknowledge_warnings`, `override_reason`)

### Feedback (`/api/v1/feedback`) — Phase 4
- `GET /api/v1/feedback?scan_id=&stage=&correction_type=` - Corrections ledger, newest first
- `GET /api/v1/feedback/summary?scan_id=` - Counts by stage and correction type
- `POST /api/v1/feedback/missed-findings` - Report a lesion the AI missed (false negative)

`POST /api/v1/findings/review` now also writes the ledger (false positive / misclassification) and forwards it to the ML service. Behaviour: `docs/PHASE4_STATUS.md`.

Full behaviour: `docs/PHASE3_STATUS.md`. Rules: `docs/CLINICAL_GUIDELINES.md` §4-5.

## Testing the API

### 1. Check Health
```bash
curl http://localhost:8000/health
```

### 2. Create a Patient
```bash
curl -X POST "http://localhost:8000/api/v1/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Patient",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "allergies": ["penicillin"],
    "weight_kg": 70.0
  }'
```

### 3. Upload & Analyze Scan
```bash
curl -X POST "http://localhost:8000/api/v1/scans/upload" \
  -F "file=@/path/to/xray.jpg" \
  -F "patient_id=<patient_uuid>" \
  -F "auto_analyze=true"
```

## Testing

```bash
source venv/bin/activate
pytest -q        # 171 tests, <1 s, no network, no .env needed
```

## Phase 2 Status

✅ **Completed:**
- Clean backend directory structure
- Core configuration management
- Supabase client integration
- Patient, Scan, and Finding domain models
- DentexClient for ML service communication
- Patient, Scan, and Finding CRUD services
- API endpoints for Steps 1-3 of clinical loop
- Automatic scan upload and AI analysis
- Finding review workflow

✅ **Phase 3 (see `docs/PHASE3_STATUS.md`):** recommendation engine, contraindication checker, treatment/prescription endpoints, tests.

⬜ **Not Yet Implemented:**

## Development Notes

### Async/Await
All service methods are `async` for non-blocking I/O, even though Supabase client is synchronous. This prepares for future async optimizations.

### Error Handling
- HTTPException for API-level errors
- Service-level exceptions wrapped in try/except blocks
- Global exception handler for uncaught errors

### Database Access
- Uses the service-role key (bypasses RLS); clients have no table access (no client RLS policies)
- Every `/api/v1` call needs `Authorization: Bearer <Supabase access token>`; data is scoped to the signed-in dentist (`app/services/access.py`)

### ML Service Communication
- `DentexClient` wraps all HTTP communication with dentex_week3
- Timeout configured via settings (default: 60s)
- Automatic parsing of ML output to Finding records

## Next Steps (Phase 5)

All six loop steps, the UI and authentication are built. Remaining: clinician review of the rule content, clinic-level sharing. See `docs/PHASE6_STATUS.md`.

## Troubleshooting

### "Connection refused" on ML service
- Ensure dentex_week3 is running: `cd dentex_week3/api && ./start.sh`
- Check ML_SERVICE_URL in `.env`

### "Table not found" errors
- Run `supabase/schema.sql` in Supabase Dashboard SQL Editor
- Verify with: `python3 ../scripts/verify_supabase.py` (from `backend/`)

### Import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

---

**Backend Port**: 8000  
**ML Service Port**: 8001 (dentex_week3)  
**Database**: Supabase PostgreSQL  
**Storage**: Supabase Storage (xray-scans bucket)
