# DentalAI - IEEE FCTAI Competition Project

AI-Assisted Diagnostic & Patient History System for Dental Clinics

> **Positioning:** DentalAI is an **assistive, second-opinion tool**. It surfaces findings
> and flags drug-safety concerns for a licensed dentist to review. It does **not**
> diagnose, prescribe, or make treatment decisions autonomously.

## Locked stack

Do not swap these without Team Lead sign-off.

| Layer | Choice | Notes |
| --- | --- | --- |
| Backend | **FastAPI** (Python) | Already scaffolded |
| Database / Auth / Storage | **Supabase** | Postgres + RLS + Storage |
| Frontend | **React** (Vite) | Already scaffolded |
| Detection model | **Ultralytics YOLOv8s** | Weights published as a [Release](https://github.com/sayfeldinn/dental-xray-ai-assistant/releases) |

**No drug-interaction API.** The RxNav DDI endpoint returns 404 — it has been retired.
Contraindications come from a **hand-curated table** maintained with the dentist, not a
live API. See `docs/qa/synthetic-patient-profiles.md`.

## Project Structure

```
dental-xray-ai-assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # REST routers
│   │   ├── core/           # Config, Supabase client
│   │   ├── domain/         # Pydantic entities + errors
│   │   └── services/       # contraindication/, recommendation/, ml_client/, supabase_client/, clinical_workflow.py
│   ├── tests/              # pytest suite (121 tests)
│   └── requirements.txt
├── frontend/               # React frontend - NOT IN TREE YET (rebuilt in Phase 5)
├── ml/                     # Training notebook + model card
│   ├── README.md           # Class taxonomy, metrics, Release link
│   └── train_dental_yolov8s.ipynb
├── scripts/                # Dev tooling
│   ├── setup-week1-board.ps1
│   ├── start-dev.sh
│   └── test_supabase_connection.py
├── docs/                   # Documentation
│   ├── SETUP_GUIDE.md      # Single setup entry point
│   ├── qa/                 # QA artifacts (synthetic profiles, test cases)
│   └── ...
└── .gitignore
```

**Model weights are not in git** (22.6 MB). Download them from the
[Releases page](https://github.com/sayfeldinn/dental-xray-ai-assistant/releases).

## Quick Start

### Prerequisites

- Python **3.11 or 3.12** (3.14 breaks `pydantic-core`; `backend/start.sh` enforces it)
- Supabase account (free tier) - Phase 1 complete
- Database schema deployed (run `supabase/schema.sql` in Supabase dashboard)

### Backend Setup (Phases 2-3 ✅)

1. Navigate to backend directory and start server:
```bash
cd backend
./start.sh
```

This will:
- Create virtual environment if needed
- Install dependencies
- Start FastAPI on http://localhost:8000

**API Documentation:** http://localhost:8000/docs

### ML Service (dentex_week3)

Start the AI inference microservice:
```bash
cd dentex_week3/api
./start.sh
```

Runs on http://localhost:8001

### Frontend Setup (Phase 5 - Not Yet Built)

The frontend was removed in the restart (`6f7014b`) and will be rebuilt in Phase 5 using React + Vite + Tailwind CSS.

### Testing the Backend

Run the API test script:
```bash
cd backend
python3 test_api.py
```

Run the automated suite (no network needed): `cd backend && pytest -q`.

Or test individual endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Create a patient
curl -X POST "http://localhost:8000/api/v1/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ahmed",
    "last_name": "Hassan",
    "date_of_birth": "1985-03-15",
    "gender": "male",
    "weight_kg": 75.0,
    "allergies": []
  }'
```

Full instructions, troubleshooting and the Week 1 checklist:
**[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)**.

## Project Status

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Supabase schema, storage, seed data | ✅ |
| 2 | Backend: scan ingestion, AI detection, finding review (loop steps 1-3) | ✅ |
| 3 | Recommendation + contraindication engine, treatment/prescription endpoints (steps 4-5) | ✅ [`docs/PHASE3_STATUS.md`](docs/PHASE3_STATUS.md) |
| 4 | Feedback logging / active learning (step 6) | ⬜ |
| 5 | React frontend (review UI, decision drawer) | ⬜ |

The active ML service is `dentex_week3/`. `ml/`, `MLv2/` and `dentex_production_portable_run3/` are earlier/alternative models kept for reference. **New here? Read [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md).**

## Environment Variables

### Backend (.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### Frontend (.env.local)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

Never commit `.env` files, and never prefix the service-role key with `VITE_`.

## Documentation

See the `/docs` folder for detailed project documentation:

- `docs/SETUP_GUIDE.md` - Setup, troubleshooting, checklist
- `docs/Project_Context.md` - Full project context and scope
- `docs/AGENT_ONBOARDING.md` - 5-minute orientation (start here)
- `docs/ARCHITECTURE.md` - System design and layer rules
- `docs/PHASE2_STATUS.md`, `docs/PHASE3_STATUS.md` - What each phase delivered
- `docs/CLINICAL_GUIDELINES.md` - Clinical rules, rule register, resolved conflicts
- `docs/DATABASE_SPEC.md` - Schema guide
- `docs/Week1_Execution_Plan.md` - Week 1 plan (historical)
- `docs/qa/README.md` - QA artifacts and their status
- `ml/README.md` - Model card, class taxonomy, metrics

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
Phase 5 (no `frontend/` yet).

### Connection check
```bash
python scripts/test_supabase_connection.py
```

## Team Roles

- ML Engineer - Dataset preparation & model training
- Backend Engineer - API & business logic
- Frontend Engineer - UI/UX implementation
- Integration/QA Engineer - Testing & synthetic data
- Team Lead - Coordination & clinical liaison

## License

IEEE FCTAI Competition Project
