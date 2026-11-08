# Agent & Developer Onboarding (read this first, ~5 minutes)

## What this is
DentalAI: an **assistive** dental decision-support system (IEEE IC-FTAI). AI proposes, the dentist decides. Never write code or UI copy that implies autonomous diagnosis or prescribing.

## The loop and where each step lives
| Step | What | Status | Code |
| :--- | :--- | :--- | :--- |
| 1 Scan ingestion | upload X-ray to Storage | ✅ P2 | `api/v1/scans.py`, `scan_service.py` |
| 2 AI detection | call `dentex_week3` (:8001) | ✅ P2 | `services/ml_client/dentex_client.py` |
| 3 Finding validation | dentist confirms/rejects/modifies | ✅ P2 | `api/v1/findings.py` |
| 4 Recommendation | rules → treatments + drugs | ✅ P3 | `services/recommendation/`, `services/contraindication/` |
| 5 Prescription decision | accept/modify/reject with safety gates | ✅ P3 | `services/clinical_workflow.py` |
| 6 Feedback logging | audit ledger → active learning | ✅ P4 | `services/feedback/`, `api/v1/feedback.py` |
| Frontend | React + Vite + Tailwind | ✅ P5 | `frontend/` (see `docs/PHASE5_STATUS.md`) |
| Auth & access | Supabase Auth, per-dentist ownership | ✅ P6 | `app/core/auth.py`, `app/services/access.py` (see `docs/PHASE6_STATUS.md`) |

Status docs: `PHASE2_STATUS.md` … `PHASE5_STATUS.md`. Architecture: `ARCHITECTURE.md`. Rules: `CLINICAL_GUIDELINES.md` (**§4 rule register, §5 decisions**). DB: `DATABASE_SPEC.md` + `supabase/schema.sql`.

## Run it
```bash
cd backend && ./start.sh          # needs Python 3.11/3.12 and ../.env; API docs at :8000/docs
pytest -q                         # 171 tests, no network
cd ../dentex_week3/api && ./start.sh   # ML service on :8001 (only needed for scan upload)
cd ../../frontend && npm install && npm run dev   # UI on :5173; npm test = 14 tests
```

**Testing against the dev database:** use a throwaway patient and delete it afterwards. If the ML service is running, rejecting or relabelling a finding appends a row to `dentex_week3/feedback/*.csv` (Phase 4 forwarding); revert that file with `git checkout` after a test session.

## Architecture rules (do not break)
1. `api` is thin; logic lives in `services`; `domain` has no I/O.
2. `services/recommendation` and `services/contraindication` stay **pure** (no Supabase, no HTTP, no LLM): deterministic and unit-testable.
3. Clinical rules/doses live **only** in the backend. Never in the frontend (it renders the backend's status and calls `POST /prescriptions/check`; the one mirrored rule is documented in `frontend/src/lib/gate.ts`).
4. Only `DentexClient` talks to the ML service. Do not modify `dentex_week3/` pipeline code.
5. Expected failures are `DomainError` subclasses (`app/domain/errors.py`), mapped to 404/409/422/502 in `main.py`. Routers don't try/except them.
7. **Every `/api/v1` route is authenticated and ownership-checked.** New routes take `dentist = Depends(get_current_dentist)` and `access = Depends(get_access)`, check the resource with `access.*`, and stamp writes with `dentist.id` (never a body `dentist_id`). Tests use `tests/conftest.py:http_client`.
6. Every dose/limit/rule cites a published source (`catalog.py` source constants, `CLINICAL_GUIDELINES.md` §6) or is marked **PROJECT**. Never invent a dose; no clinician has reviewed the content yet.

## Recipes
- **New/changed clinical rule:** cite the guideline in `CLINICAL_GUIDELINES.md` (append a rule ID to §4, never renumber) → edit `catalog.py` / `checker.py` / `rules.py` → add tests → `pytest -q`.
- **New allergy/condition wording from real data:** add an alias in `catalog.py` (`ALLERGY_CLASSES` etc.).
- **New endpoint:** domain model → service method (persistence in `supabase_client/`, orchestration in `clinical_workflow.py`) → thin router in `api/v1/` → register in `api/v1/__init__.py` → test with `get_workflow` override (see `tests/test_api.py`).
- **Schema change:** SQL in `supabase/migrations/` + `schema.sql` + `DATABASE_SPEC.md` + Pydantic model, in one PR.

## Gotchas
- Python **3.14 breaks** pydantic-core/supabase: use 3.12 (`backend/venv` is 3.12).
- `requirements.txt` pins matter: `supabase==2.3.4` + `httpx<0.26` + `gotrue<2.9` (see comments there).
- Tests set dummy env vars first; the real `../.env` is never needed to run `pytest`.
- Regenerating recommendations changes proposal IDs; dentist-decided items are kept.
- Git: trunk-based, branch per ticket, PR + review (`CONTRIBUTING.md`).
