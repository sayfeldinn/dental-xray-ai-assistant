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
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, dependencies
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   ├── public/
│   └── package.json
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

- Python **3.11 or 3.12** (3.14 breaks `pydantic-core` — see `docs/SETUP_GUIDE.md`)
- Node.js 18+
- Supabase account (free tier)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example` and fill in your Supabase credentials

5. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file from `.env.example` and fill in your Supabase credentials

4. Run the development server:
```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Or start both at once

```bash
./scripts/start-dev.sh
```

Full instructions, troubleshooting and the Week 1 checklist:
**[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)**.

## Week 1 Features

### Backend
- ✅ Patient record management (CRUD)
- ✅ X-ray upload and storage
- ✅ Recommendation engine skeleton
- ✅ Contraindication checking logic
- ✅ Supabase integration

### Frontend
- ✅ Authentication (login/signup)
- ✅ X-ray review screen
- ✅ Treatment confirmation screen
- ✅ Patient history viewer

### ML
- ✅ YOLOv8s detector trained (5 classes) — see [`ml/README.md`](ml/README.md)
- ⬜ Inference path (`predict.py` / ONNX / API endpoint) — issue #12

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
- `docs/Week1_Execution_Plan.md` - Week 1 detailed execution plan
- `docs/ARCHITECTURE.md` - System design and diagrams
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
npm run lint
```

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
