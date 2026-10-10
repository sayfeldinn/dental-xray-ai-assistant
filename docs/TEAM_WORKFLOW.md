# DentalAI — Team Collaboration & Engineering Workflow

This guide establishes the rules of engagement for developers collaborating on the DentalAI codebase.

---

## 1. Golden Rules of Development

1. **Never commit `.env` files or secrets:** Always use `.env.example` as the clean template.
2. **Never hardcode clinical logic on the frontend:** All recommendation rules, dosages, and contraindications live in `backend/app/services/` to ensure auditability and consistent validation.
3. **Never bypass the dentist confirmation step:** In any UI or endpoint, ensure that AI predictions are flagged as `pending` until explicit user action confirms them.
4. **Keep `dentex_week3/` isolated:** The ML microservice runs as an autonomous inference service on port 8001. All communication with it must pass through `DentexClient` in the backend.

---

## 2. Local Environment Setup

### 2.1 Backend & ML Environment (Python 3.10+)
```bash
# In project root:
cp .env.example .env
# Edit .env with your assigned Supabase and local keys

# 1. AI Inference Microservice (dentex_week3)
cd dentex_week3/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py  # Runs on http://localhost:8001

# 2. Main Backend (Once scaffolded in Phase 2)
cd ../../backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2.2 Frontend Environment (Node 18+)
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

---

## 3. How to Make Changes (Multi-Developer Workflow)

### 3.1 Adding a New Clinical Rule or Dosing Logic
1. Open `docs/CLINICAL_GUIDELINES.md` and document the clinical guideline citation (ADA/AHA).
2. Modify `backend/app/services/recommendation/` or `backend/app/services/contraindication/`.
3. Add a corresponding test case in `backend/tests/test_recommendations.py`.
4. Run `pytest` to confirm all test branches pass.

### 3.2 Modifying the Database Schema
1. Create a timestamped SQL migration script in `supabase/migrations/` (e.g. `20261011_add_patient_field.sql`).
2. Run the SQL script in your Supabase project's SQL Editor.
3. Update `docs/DATABASE_SPEC.md` to reflect new tables or columns.
4. Update corresponding domain models in `backend/app/domain/`.

### 3.3 Adding a Frontend Component
1. Place atomic UI elements in `frontend/src/components/common/`.
2. Place clinical workflow views in `frontend/src/features/` (e.g., `scan-viewer`, `treatment-panel`).
3. Ensure every AI suggestion has a prominent `"Pending Dentist Validation"` badge.

---

## 4. Pre-Commit / Pre-Demo Checklist

Before presenting or merging code, verify:
- [ ] Backend runs without error: `curl http://localhost:8000/api/v1/health` returns `200 OK`.
- [ ] ML microservice is online: `curl http://localhost:8001/` returns `{"status":"ok","models_loaded":true}`.
- [ ] Database connection works: `python scripts/verify_supabase.py` passes.
- [ ] The 3 demo branches test successfully:
  - Branch 1: Caries with no infection -> Restorative referral, 0 drugs.
  - Branch 2: Periapical lesion with no allergy -> Amoxicillin 500mg q8h.
  - Branch 3: Periapical lesion with penicillin allergy -> Warning shown, Clindamycin suggested.

