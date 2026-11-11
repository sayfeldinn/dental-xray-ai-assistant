# E2E clinician flow — local run (2026-11-05)

**Scope:** auth → patient → panoramic upload → AI analysis → findings review →
confirmed-findings gate → re-analysis refusal → treatment proposal.

**Why local:** the cloud Supabase project in `.env` (`vudxogycxfaarnirtxhf`)
returns **NXDOMAIN** (Cloudflare DoH `Status: 3`) from the host and from the
backend container. `/health` only reports that env vars are set, so it stayed green.
**Correction (2026-11-09):** the project had only been paused for inactivity; it was
restored from the dashboard with its data intact. A paused free-plan project can stop
resolving, so NXDOMAIN does not prove deletion. `.github/workflows/supabase-keepalive.yml`
now pings it daily.
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

## Follow-up round: re-analyze threshold, provenance, zoom, migrations

- **Re-analyze with a threshold** — the scan page's re-run control now carries a
  0.20 / 0.30 / 0.50 select; `api.reanalyzeScan(id, threshold)` sends
  `?confidence_threshold=`. Verified against the backend: upload `train_12.png`
  at 0.20 -> 9 findings, then re-analyze at 0.50 -> 8, stored
  `confidence_threshold` 0.5.
- **Selecting a box scrolls to its finding card** — the card list is keyed by
  `finding-<id>`; the X-ray `onSelect` sets the selection and calls
  `scrollIntoView` (guarded for jsdom).
- **Model provenance** — `raw_ml_output.model` now records `missing_teeth`,
  `missing_teeth_gap_threshold` and `pipeline_version` (from
  `pipeline_config.json`) alongside the tooth/disease/findings weights.
- **Zoom / pan** — the viewer zooms around the cursor, pans on drag (a drag no
  longer selects a box), double-click / Reset returns to fit, with `+`/`−`/Reset
  buttons and a hint line.
- **`supabase start` from scratch** — `supabase/schema.sql` is now the first
  migration (`20261019_base_schema.sql`, idempotent), so a clean
  `supabase start` applies the base schema, the auth lockdown and `seed.sql`
  with no manual `psql`. Verified in an isolated project (ports 5xxxx): all 6
  tables present, 4 seeded patients, 0 public policies, `xray-scans` private.
- **Docs** — README and `docs/SETUP_GUIDE.md` now document the migration flow
  and the `backend-e2e` vs compose `backend` `:8000` conflict.

Frontend 16 tests pass; ML `/predict` rebuild returns the provenance block and
6 missing-tooth boxes.

## Bug found and fixed

The ML service returns the clinical text as **`ai_generated_report`**, but
`scan_ingestion.py` read `report`, so `ai_report` was stored empty and the UI
never showed it. Fixed in `backend/app/services/scan_ingestion.py` (accepts both
keys) with a regression test in `backend/tests/test_scan_ingestion.py`.
Backend suite: **172 passed**.

## Reproduce

```bash
# 1) local Supabase: base schema, auth lockdown and seed are migrations now
npx supabase start -o env > /tmp/opencode/supabase_local.env

# 2) backend that can reach 127.0.0.1:54321 + the ML container
docker compose stop backend
docker run -d --name backend-e2e --network host --env-file .env \
  -e ML_SERVICE_URL=http://127.0.0.1:8001 \
  -e CORS_ORIGINS='["http://localhost:8080","http://127.0.0.1:8080"]' \
  dental-xray-ai-assistant-backend:latest

# 3) drive the flow
python scripts/e2e_clinician_flow.py
```

**Local stack order:** `supabase start` now applies
`20261019_base_schema.sql`, `20261020_auth_lockdown.sql` and `seed.sql`, so no
manual `psql` step is needed. Then run the host-network `backend-e2e` and start
`ml` + `frontend` with `docker compose up -d --no-deps ml frontend` (the compose
`backend` must stay stopped: it also binds `:8000`). An existing local database
that was created with the old manual steps keeps working; the new migration only
matters for a fresh volume. `.env` points at local Supabase; the cloud config is
in `.env.cloud.bak` (gitignored) and needs a recreated project to work again.

## Cloud run against the live project (2026-11-11)

Full stack from `docker compose up --build` (ML image with CPU torch, ultralytics
pinned to 8.4.174) against the restored cloud Supabase project, scripted as
`scripts/e2e_cloud_flow.py` on the held-out DENTEX image `val_28.png`.
**28/28 checks passed**; the script deletes its dentist, patient and scan, and the
six table row counts matched before and after.

| Area | Observed |
| --- | --- |
| Access | unauthenticated 401; a new dentist sees 0 of the existing patients, another dentist's patient is 404, a direct PostgREST read with the user token returns `[]` |
| Upload + analyze | 201, 9 findings, AI report and `pipeline_version: v3` stored; X-ray readable only via the signed URL |
| Review | 36 Periapical confirmed, 27 Caries rejected, 46 Caries -> Periapical; planning sees exactly the 2 validated findings; re-analyze 409 |
| Plan | penicillin allergy: Clindamycin + Ibuprofen, no Amoxicillin, `FIRST_LINE_EXCLUDED`; accepting without acknowledging is 422 |
| Feedback | ledger rows `false_positive` + `misclassification`; both also reached the ML retraining CSV |

Upload + analysis took ~21 s, of which ML inference is ~1.5 s. The rest is the
5.4 MB PNG upload to Supabase eu-west-1 over a ~2 Mbit/s uplink; venue Wi-Fi decides
this number on demo day.

Locked-50 benchmark through the same container's HTTP API: all 101 metrics identical
to the local run (tooth 91.7%, disease 89.0%, joint 82.8%, mAP@0.5 54.9%).
