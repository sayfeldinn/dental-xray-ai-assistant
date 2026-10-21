# Phase 6 Status: Authentication, Authorization, Security & Deployment

**Verified:** backend 171 tests (24 new) pass, also from a clean install of `requirements.txt` on Python 3.12;
frontend 25 tests, typecheck and build pass. Live run against the dev Supabase with two throwaway dentist
accounts (deleted afterwards, with their patients and files): sign-in, patient creation, real X-ray upload with
live AI analysis (9 findings), signed image URL, re-analysis, cross-dentist isolation, tamper rejection, sign-out.
**Not verified:** the Docker images were not built (Docker daemon not running); `docker compose config` validates.

## 1. Authentication
- **Frontend:** Supabase Auth (email + password): sign in, self sign-up (email confirmation), password reset,
  sign-out. Session persisted and refreshed by supabase-js; every API call sends `Authorization: Bearer <access token>`.
  A 401 signs the user out; signing out clears all cached data.
- **Backend:** `app/core/auth.py` verifies the token locally (signature against the project's JWKS, ES256, cached;
  expiry; audience `authenticated`; issuer; role). Legacy HS256 projects use `SUPABASE_JWT_SECRET`. The whole
  `/api/v1` router requires it; `/` and `/health` stay public.

## 2. Authorization (per-dentist ownership)
- `app/services/access.py`: every resource (scan, finding, treatment, prescription, feedback) is resolved to its
  patient and the patient's `dentist_id` must be the caller. Otherwise **404** (same as missing, so ids cannot be probed).
- Patient list is filtered to the caller; creates are stamped with the caller. `dentist_id` in a request body is
  **ignored** (overwritten), so it cannot be spoofed. Reviews, decisions, treatments, prescriptions and feedback rows
  now record the real dentist.
- Breaking API changes: `GET /scans` requires `patient_id`; `GET /feedback` and `/feedback/summary` require `scan_id`.

## 3. Security fixes found during this phase
| Issue | Fix |
| :--- | :--- |
| RLS policies granted `anon` full read/write on all clinical tables; the anon key is now in the browser | `supabase/migrations/20261020_auth_lockdown.sql` drops them; `schema.sql` updated. Clients get no table access; only the backend (service role) does |
| X-ray bucket public | Bucket private (same migration); backend returns 1-hour signed URLs |
| Deleting a patient left their X-rays in storage | Images removed with the patient |
| Uploads accepted any file type/size; client filename used in storage path | JPEG/PNG/WebP only, `MAX_UPLOAD_MB` (20), object named from the validated type |
| Shared default request object mutated per request (recommendations) | Fresh copy per call (tested) |
| Field hints inside `<label>` polluted accessible names | Hint moved outside the label |

> **Action required on the existing dev project:** run the migration in the Supabase SQL editor. Until then the
> old policies are still live.

## 4. Completeness work
- Scan ingestion moved out of the router into `services/scan_ingestion.py` (testable); AI failure keeps the scan
  as `failed` and returns **502** (`UpstreamError`).
- `POST /scans/{id}/reanalyze` implemented (was 501): re-reads the stored image and re-runs the model; refused (409)
  once any finding is reviewed.
- UI: edit and delete patient, re-run analysis, delete scan, failed-analysis banner.
- Admin scripts (`backend/scripts/`): `create_dentist` (confirmed account, password prompted) and
  `assign_unowned_patients` (gives pre-auth demo patients to a dentist; dry run by default).
- Deployment: `backend/Dockerfile` (non-root), `frontend/Dockerfile` + `nginx.conf` (SPA fallback, security headers),
  `deploy/ml.Dockerfile` (copies `dentex_week3` unmodified), `docker-compose.yml`.
- `docs/SETUP_GUIDE.md` rewritten (it described a public bucket and auth endpoints that never existed).

## 5. Known limitations
1. **No clinician review** of the rule content (unchanged; see `CLINICAL_GUIDELINES.md`).
2. **No clinic/team sharing:** a patient belongs to one dentist. Sharing needs a clinic table and membership.
3. **No rate limiting or audit of reads**; sign-in protection is Supabase's.
4. **Docker images untested** (see above). The ML image is large (ultralytics/torch).
5. The local dev venv had `gotrue 2.9.1` although `requirements.txt` pins `<2.9`; the auth-admin calls in that
   combination fail, so the scripts use plain HTTP. Re-sync with `pip install -r requirements.txt`.
6. After sign-in the app opens the patient list, not the deep link that was requested.
