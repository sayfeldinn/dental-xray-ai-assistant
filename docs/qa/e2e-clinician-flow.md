# E2E clinician flow — local run (2026-11-05)

**Scope:** auth → patient → panoramic upload → AI analysis → findings review →
confirmed-findings gate → re-analysis refusal → treatment proposal.

**Why local:** the cloud Supabase project in `.env` (`vudxogycxfaarnirtxhf`)
returns **NXDOMAIN** (Cloudflare DoH `Status: 3`) from the host and from the
backend container. A paused project still resolves; NXDOMAIN means the project
was deleted. `/health` only reports that env vars are set, so it stayed green.
The run therefore used a local Supabase stack.

## Environment

| Piece | Value |
| --- | --- |
| Supabase | local CLI 3.0, API `http://127.0.0.1:54321`, Studio `:54323` |
| Backend | image run with `--network host` (compose `backend` stopped) |
| ML | `http://127.0.0.1:8001` |
| UI | `http://localhost:8080` (rebuilt with the local `VITE_*` keys) |
| QA user | `qa.e2e@dentalai.local` (local only) |
| Image | DENTEX `train_12.png` |

## Result

| Step | Observed |
| --- | --- |
| Sign-up / sign-in | 200, dentist `846e3899-…` |
| Patient | created (penicillin allergy on file) |
| Upload + analyze | 200, scan `e130cb90-…`, status `analyzed` |
| Findings | **9** pending (Periapical 0.952, Impacted 0.881, Deep Caries 0.855, …) |
| Stored scan | signed image URL, `missing_teeth` 6, advisory `findings` 19, `ai_report` present |
| Review | tooth 46 Periapical Lesion → `confirmed`, `reviewed_by` = dentist |
| Confirmed gate | 1 finding available for treatment planning |
| Re-analyze after review | **409** (correctly refused) |
| Treatment proposal | endodontic RCT/extraction; **Clindamycin** 300 mg q6h 3–7 d + Ibuprofen; `FIRST_LINE_EXCLUDED` (penicillin allergy) and `CDIFF_RISK` warnings |
| Delete | 204, cascades |

## UI advisory layers and threshold (follow-up)

The scan page now renders the two advisory layers from `raw_ml_output`:

- **Missing teeth** — dashed sky-blue boxes on the radiograph plus a collapsed
  "Advisory AI signals" panel with the gap probability and bracketing teeth.
- **Findings model** — listed in the same panel, never drawn on the radiograph.

Both are labelled "not in the clinical report"; the disease findings remain the
only reviewable boxes. `derive_missing_teeth` now keeps the interpolated `box`
(additive), so the overlay works without a second model call.

The upload form exposes **Detection confidence** (0.20 / 0.30 / 0.50) and the
backend forwards `confidence_threshold` to `/predict`, which filters after tooth
association. On `train_12.png`: 9 detections at 0.20, 8 at 0.50.

Verification: scan `e6b213ba-f1ca-4b60-87de-a127e7c14507` (9 findings, 6 missing
teeth with boxes, 19 advisory findings); 0.50 upload
`5f25a5ba-542e-4910-bf5b-7c88b7c824b2` (8 findings). Frontend 15 tests pass,
backend 172 tests pass.

`scripts/render_gt_vs_pred.py` writes side-by-side GT/model images to
`submission/assets/gt_vs_pred_val_{28,31,2}.png`.

## Bug found and fixed

The ML service returns the clinical text as **`ai_generated_report`**, but
`scan_ingestion.py` read `report`, so `ai_report` was stored empty and the UI
never showed it. Fixed in `backend/app/services/scan_ingestion.py` (accepts both
keys) with a regression test in `backend/tests/test_scan_ingestion.py`.
Backend suite: **172 passed**.

## Reproduce

```bash
# 1) local Supabase (schema.sql + lockdown migration, then save the env)
npx supabase start -o env > /tmp/opencode/supabase_local.env
docker exec -i supabase_db_dental-xray-ai-assistant psql -U postgres -d postgres < supabase/schema.sql
docker exec -i supabase_db_dental-xray-ai-assistant psql -U postgres -d postgres < supabase/migrations/20261020_auth_lockdown.sql

# 2) backend that can reach 127.0.0.1:54321 + the ML container
docker compose stop backend
docker run -d --name backend-e2e --network host --env-file .env \
  -e ML_SERVICE_URL=http://127.0.0.1:8001 \
  -e CORS_ORIGINS='["http://localhost:8080","http://127.0.0.1:8080"]' \
  dental-xray-ai-assistant-backend:latest

# 3) drive the flow
python scripts/e2e_clinician_flow.py
```

**Caveats:** `supabase start` replays `supabase/migrations/` and `seed.sql`
before any manual schema apply; this repo's base schema lives in `schema.sql`,
not in a migration, so the first `start` fails on the lockdown migration. The
run above started with migrations/seed temporarily moved aside, applied
`schema.sql`, then the lockdown. A future fix is to add the base schema as the
first migration. `.env` now points at local Supabase; the cloud config is in
`.env.cloud.bak` (gitignored) and needs a recreated project to work again.
