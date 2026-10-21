# DentalAI Setup Guide

The single entry point for running the complete system: Supabase (database, auth, storage),
the ML service (`dentex_week3`, port 8001), the backend API (port 8000) and the clinician UI
(port 5173 in development, 8080 with Docker).

## 1. Supabase project (once)

1. Create a project at supabase.com. From **Project Settings → API** copy the Project URL, the
   `anon`/publishable key and the `service_role` key.
2. **SQL Editor:** run `supabase/schema.sql` (tables, constraints, indexes, RLS, private `xray-scans` bucket).
   Optional demo data: `supabase/seed.sql`.
3. **Existing projects created before Phase 6:** also run `supabase/migrations/20261020_auth_lockdown.sql`.
   It removes the old development policies that let anyone holding the anon key read and change
   every clinical table, and makes the X-ray bucket private. **Do this before deploying the frontend**:
   the anon key is shipped to the browser for sign-in.
   Verify: `SELECT * FROM pg_policies WHERE schemaname = 'public';` returns no rows, and
   `SELECT public FROM storage.buckets WHERE id = 'xray-scans';` returns `false`.
4. **Authentication → URL Configuration:** set the Site URL to where the UI runs
   (`http://localhost:5173` in development) so confirmation and password-reset links come back to the app.

## 2. Configuration

```bash
cp .env.example .env      # repo root; never commit .env
```

Fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (and the other Supabase
values), plus `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` for the UI. The frontend reads the same
root `.env`; only `VITE_*` values reach the browser. **Never prefix the service-role key with `VITE_`.**

Access tokens are verified against the project's public signing keys (JWKS). Only projects still on
the legacy shared JWT secret need `SUPABASE_JWT_SECRET`.

## 3. Run it (development)

Python **3.11 or 3.12** (3.14 breaks `pydantic-core`), Node **20+**.

```bash
# ML service (needs the model weights in dentex_week3/production/, published as a GitHub Release)
cd dentex_week3/api && ./start.sh                 # http://localhost:8001

# Backend
cd backend && ./start.sh                          # http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev         # http://localhost:5173
```

## 4. First sign-in

- **Self sign-up** on the login page works; Supabase sends a confirmation email first.
- **Or create a ready-to-use account** (no email step):
  ```bash
  cd backend && source venv/bin/activate
  python -m scripts.create_dentist --email dr@clinic.eg --name "Dr Sara Adel"   # prompts for the password
  ```
- **Demo data:** patients created before authentication existed have no owner and are invisible to everyone.
  Give them to a dentist:
  ```bash
  python -m scripts.assign_unowned_patients --email dr@clinic.eg          # dry run
  python -m scripts.assign_unowned_patients --email dr@clinic.eg --apply
  ```

Each dentist sees only their own patients; another dentist's records answer 404.

## 5. Run it with Docker

```bash
docker compose up --build      # UI http://localhost:8080 · API http://localhost:8000 · ML http://localhost:8001
```

The weights must be in `dentex_week3/production/` before building. Add `http://localhost:8080` to the
Supabase Site URL / redirect URLs. Dentist feedback queued by the ML service is kept in the `ml-feedback` volume.

## 6. Checks

```bash
cd backend && pytest -q                          # 171 tests, no network
cd frontend && npm run typecheck && npm test     # 25 tests
curl http://localhost:8000/health                # public
curl -i http://localhost:8000/api/v1/patients    # 401 without a token (expected)
```

## 7. Troubleshooting

| Symptom | Cause / fix |
| :--- | :--- |
| Login page says Supabase Auth is not configured | `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` missing from the root `.env`; restart `npm run dev` |
| Every API call returns 401 "Session expired" | Token from another Supabase project, or clock skew; sign out and in again |
| Patient list is empty after signing in | Patients belong to their creator; run `scripts.assign_unowned_patients` for demo data |
| Upload returns 502 "AI analysis failed" | ML service not running on `ML_SERVICE_URL`; the scan is kept: start the service and use **Re-run AI analysis** |
| X-ray image does not load | Signed URLs expire after `SIGNED_URL_TTL_SECONDS` (default 1 h); reload the page |
| `Client.__init__() got an unexpected keyword argument 'proxy'` | Old venv: `pip install -r backend/requirements.txt` (pins `gotrue<2.9`) |
| Testing writes to `dentex_week3/feedback/*.csv` | Expected while the ML service runs (Phase 4 forwarding); `git checkout` that file after test sessions |
