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
| Frontend | **React** (Vite + Tailwind) | Built in Phase 5 |
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
│   ├── scripts/            # create_dentist, assign_unowned_patients
│   ├── tests/              # pytest suite (171 tests)
│   └── requirements.txt
├── frontend/               # React + Vite + Tailwind clinician UI (Phase 5)
├── ml/                     # Training notebook + model card
│   ├── README.md           # Class taxonomy, metrics, Release link
│   └── train_dental_yolov8s.ipynb
├── scripts/                # Dev tooling
│   ├── setup-week1-board.ps1
│   └── verify_supabase.py
├── docs/                   # Documentation
│   ├── SETUP_GUIDE.md      # Single setup entry point
│   ├── qa/                 # QA artifacts (synthetic profiles, test cases)
│   └── ...
└── .gitignore
```

**Model weights are not in git** (22.6 MB). Download them from the
[Releases page](https://github.com/sayfeldinn/dental-xray-ai-assistant/releases).

## Quick Start

Full instructions: **[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)**. In short:

1. Run `supabase/schema.sql` in the Supabase SQL editor (existing projects: also `supabase/migrations/20261020_auth_lockdown.sql`).
2. `cp .env.example .env` and fill in the Supabase values.
3. Start the three services (Python 3.11/3.12, Node 20+):
   ```bash
   cd dentex_week3/api && ./start.sh        # ML service   :8001
   cd backend && ./start.sh                 # API          :8000 (docs at /docs)
   cd frontend && npm install && npm run dev  # UI         :5173
   ```
   Or everything at once: `docker compose up --build` (UI on :8080).
4. Sign up on the login page, or `cd backend && python -m scripts.create_dentist --email you@clinic.eg --name "Dr You"`.

Tests: `cd backend && pytest -q` (171) · `cd frontend && npm test` (14).

## Project Status

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Supabase schema, storage, seed data | ✅ |
| 2 | Backend: scan ingestion, AI detection, finding review (loop steps 1-3) | ✅ |
| 3 | Recommendation + contraindication engine, treatment/prescription endpoints (steps 4-5) | ✅ [`docs/PHASE3_STATUS.md`](docs/PHASE3_STATUS.md) |
| 4 | Feedback logging / active learning (step 6) | ✅ [`docs/PHASE4_STATUS.md`](docs/PHASE4_STATUS.md) |
| 5 | React frontend (review UI, decision drawer) | ✅ [`docs/PHASE5_STATUS.md`](docs/PHASE5_STATUS.md) |
| 6 | Login (Supabase Auth), per-dentist access, security lockdown, Docker | ✅ [`docs/PHASE6_STATUS.md`](docs/PHASE6_STATUS.md) |

The active ML service is `dentex_week3/`. `ml/` and `MLv2/` are earlier/alternative models kept for reference (their heavy weights are not in git). **New here? Read [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md).**

## Environment Variables

One `.env` at the repo root, copied from [`.env.example`](.env.example), serves the backend and the frontend
(Vite exposes only `VITE_*` values to the browser). Never commit `.env`, and never prefix the service-role
key with `VITE_`.

## Documentation

See the `/docs` folder for detailed project documentation:

- `docs/SETUP_GUIDE.md` - Setup, troubleshooting, checklist
- `docs/Project_Context.md` - Full project context and scope
- `docs/AGENT_ONBOARDING.md` - 5-minute orientation (start here)
- `docs/ARCHITECTURE.md` - System design and layer rules
- `docs/PHASE2_STATUS.md` … `docs/PHASE6_STATUS.md` - What each phase delivered
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
```bash
cd frontend
npm run typecheck && npm test   # 14 tests (vitest)
```

### Connection check
```bash
python scripts/verify_supabase.py
```

## Team Roles

- ML Engineer - Dataset preparation & model training
- Backend Engineer - API & business logic
- Frontend Engineer - UI/UX implementation
- Integration/QA Engineer - Testing & synthetic data
- Team Lead - Coordination & clinical liaison

## License

IEEE FCTAI Competition Project
