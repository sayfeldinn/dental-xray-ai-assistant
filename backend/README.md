# DentalAI Backend Service

Clean FastAPI backend for IEEE IC-FTAI dental decision-support system.

## Architecture

This backend implements the 6-step clinical loop:

1. **Scan Ingestion** → Upload panoramic X-ray to Supabase Storage
2. **AI Detection** → Call dentex_week3 microservice for analysis
3. **Dentist Validation** → Review and confirm/reject/modify findings
4. **Recommendation Engine** → Generate treatment recommendations (Phase 3)
5. **Dentist Confirmation** → Approve prescriptions with contraindication checks (Phase 3)
6. **Feedback Logging** → Audit trail for active learning (Phase 4)

## Directory Structure

```
backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── patients.py      # Patient CRUD
│   │   ├── scans.py         # Scan upload & analysis
│   │   └── findings.py      # Finding review
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   └── supabase_client.py  # Supabase client factory
│   ├── domain/              # Pydantic domain models
│   │   ├── patient.py
│   │   ├── scan.py
│   │   └── finding.py
│   ├── services/            # Business logic layer
│   │   ├── ml_client/       # Dentex ML service client
│   │   ├── supabase_client/ # Database services
│   │   ├── recommendation/  # (Phase 3)
│   │   └── contraindication/  # (Phase 3)
│   └── main.py              # FastAPI application
└── requirements.txt         # Python dependencies
```

## Quick Start

### 1. Prerequisites

- Python 3.11 or 3.12
- Virtual environment tool (venv, conda, etc.)
- Supabase project configured (Phase 1 complete)
- dentex_week3 ML service running on port 8001

### 2. Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

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
- `POST /api/v1/scans/upload` - Upload & analyze X-ray
- `GET /api/v1/scans` - List scans (with filters)
- `GET /api/v1/scans/{id}` - Get scan details
- `GET /api/v1/scans/{id}/findings` - Get findings for scan
- `PUT /api/v1/scans/{id}` - Update scan
- `DELETE /api/v1/scans/{id}` - Delete scan

### Findings (`/api/v1/findings`)
- `GET /api/v1/findings` - List findings (by patient or scan)
- `GET /api/v1/findings/{id}` - Get finding details
- `POST /api/v1/findings/review` - Dentist review finding
- `GET /api/v1/findings/scan/{scan_id}/confirmed` - Get confirmed findings
- `PUT /api/v1/findings/{id}` - Update finding

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

⬜ **Not Yet Implemented (Future Phases):**
- Recommendation engine (Phase 3)
- Contraindication checking (Phase 3)
- Treatment and Prescription endpoints (Phase 3-4)
- Feedback logging to clinical_feedback_logs (Phase 4)

## Development Notes

### Async/Await
All service methods are `async` for non-blocking I/O, even though Supabase client is synchronous. This prepares for future async optimizations.

### Error Handling
- HTTPException for API-level errors
- Service-level exceptions wrapped in try/except blocks
- Global exception handler for uncaught errors

### Database Access
- Uses service_role key to bypass RLS (for backend operations)
- RLS policies still enforced for future direct frontend access

### ML Service Communication
- `DentexClient` wraps all HTTP communication with dentex_week3
- Timeout configured via settings (default: 60s)
- Automatic parsing of ML output to Finding records

## Next Steps (Phase 3)

1. Implement recommendation engine with ADA/AHA clinical rules
2. Build contraindication checker
3. Add treatment and prescription endpoints
4. Create unit tests for business logic

## Troubleshooting

### "Connection refused" on ML service
- Ensure dentex_week3 is running: `cd dentex_week3/api && ./start.sh`
- Check ML_SERVICE_URL in `.env`

### "Table not found" errors
- Run `supabase/schema.sql` in Supabase Dashboard SQL Editor
- Verify with: `python3 scripts/verify_supabase.py`

### Import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

---

**Backend Port**: 8000  
**ML Service Port**: 8001 (dentex_week3)  
**Database**: Supabase PostgreSQL  
**Storage**: Supabase Storage (xray-scans bucket)
