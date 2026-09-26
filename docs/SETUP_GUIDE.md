# DentalAI Setup Guide

Single entry point for getting the project running. Everything the old
`QUICK_START.md`, `START_HERE.md` and `SETUP_INSTRUCTIONS.md` covered is merged here.

## Table of contents

- [Prerequisites](#prerequisites)
- [5-minute quick start](#5-minute-quick-start)
- [Supabase setup](#supabase-setup)
- [Backend setup](#backend-setup)
- [Frontend setup](#frontend-setup)
- [Environment variables](#environment-variables)
- [Python version notes](#python-version-notes)
- [Verify the install](#verify-the-install)
- [Useful commands](#useful-commands)
- [Troubleshooting](#troubleshooting)
- [Week 1 checklist](#week-1-checklist)
- [API reference](#api-reference)

## Prerequisites

- **Python 3.11 or 3.12** (3.14 is broken — see [Python version notes](#python-version-notes))
- Node.js 18+
- Supabase account (free tier)
- Git

## 5-minute quick start

**1. Supabase (2 min)** — create a project, copy the Project URL, `anon public` key and
`service_role` key, run `backend/database_schema.sql` in the SQL Editor, and create a
Storage bucket named `xray-scans` (public for now).

**2. Backend (1 min)**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your Supabase credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. Frontend (1 min)** — in a new terminal:

```bash
cd frontend
npm install
cp .env.example .env.local    # then fill in your Supabase credentials
npm run dev
```

**4. Test it** — open http://localhost:5173, click **Sign Up**, create an account.

## Supabase setup

### 1. Create a project

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Name: `dentalai`, pick a region, save the database password

### 2. Get API credentials

**Settings → API**, copy:

- `Project URL` (`https://xxxxx.supabase.co`)
- `anon public` key
- `service_role` key — **keep this secret, never commit it**

### 3. Create the storage bucket

**Storage → New bucket** → name `xray-scans` → Public → Create.

### 4. Apply the schema

1. **SQL Editor → New query**
2. Paste the entire contents of `backend/database_schema.sql`
3. Run it. You should see "Success. No rows returned"
4. **Table Editor** should now show: `patients`, `scans`, `treatments`, `prescriptions`, `feedback`

## Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in Supabase credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Generate a `SECRET_KEY` for `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Running at:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local    # fill in Supabase credentials
npm run dev
```

Running at http://localhost:5173.

Use the **same** `SUPABASE_URL` and anon key in both `.env` and `.env.local`.

## Environment variables

### Backend (`backend/.env`)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SECRET_KEY=generate_with_python_secrets
```

### Frontend (`frontend/.env.local`)

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
VITE_API_V1_PREFIX=/api/v1
```

Variables exposed to the browser **must** start with `VITE_`. Never put the
`service_role` key in a `VITE_` variable.

## Python version notes

**Python 3.14 does not work** — `pydantic-core` (pulled in by `pydantic==2.5.3`) has no
3.14 wheels yet, so `pip install -r requirements.txt` fails. Use 3.11 or 3.12.

Check what you have:

```bash
python --version
```

**Option 1 — Homebrew:**

```bash
brew install python@3.12
cd backend && rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option 2 — pyenv:**

```bash
pyenv install 3.12
pyenv local 3.12
cd backend && rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option 3 — no admin rights?** Install just the runtime deps from PyPI wheels:

```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn supabase-py python-dotenv \
  "python-jose[cryptography]" "passlib[bcrypt]" python-multipart \
  email-validator pydantic-settings
uvicorn app.main:app --reload
```

## Verify the install

**Backend:**

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "healthy", "app": "DentalAI", "version": "1.0.0" }
```

**Connection test:**

```bash
python scripts/test_supabase_connection.py
```

Loads `backend/.env` and confirms the Supabase client connects. If it reports missing
tables, re-run the schema SQL.

**Frontend:** open http://localhost:5173, sign up with a test account
(`test@example.com` / `password123`), and confirm you land on the Dashboard.

## Useful commands

```bash
# Start both servers (macOS/Linux)
./scripts/start-dev.sh

# Backend only
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Supabase connection check
python scripts/test_supabase_connection.py

# Tests (when they land)
cd backend && pytest
cd frontend && npm run lint
```

**URLs**

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Supabase dashboard | https://app.supabase.com |

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`** — you are not in the virtual
environment: `cd backend && source venv/bin/activate`

**`Connection refused` / `ECONNREFUSED`** — the backend is not running:
`cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

**`Missing Supabase environment variables`** — `backend/.env` or `frontend/.env.local`
is missing or incomplete. Frontend vars must start with `VITE_`.

**`Invalid credentials` on login** — the schema SQL was never applied; re-run it in the
SQL Editor.

**`pydantic-core` / Python 3.14 build failure** — see [Python version notes](#python-version-notes).

**Port already in use:**

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

**`Network Error` / CORS error** — the backend is down, or `VITE_API_URL` does not point
at http://localhost:8000.

**Storage bucket not working** — Supabase dashboard → Storage → `xray-scans` → Policies
→ add a `SELECT` policy for role `public` with definition `true`.

## Week 1 checklist

- [ ] Supabase project created
- [ ] Database schema executed
- [ ] `xray-scans` storage bucket created
- [ ] Backend running on port 8000 (`/health` returns healthy)
- [ ] Frontend running on port 5173
- [ ] `scripts/test_supabase_connection.py` passes
- [ ] Can create an account and log in
- [ ] Dashboard loads

All checked → you're ready for Week 2.

## API reference

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

| Group | Endpoints |
| --- | --- |
| Auth | `POST /api/v1/auth/signup`, `/signin`, `/signout`, `GET /api/v1/auth/me` |
| Patients | `GET/POST /api/v1/patients`, `GET/PUT/DELETE /api/v1/patients/{id}` |
| Scans | `GET/POST /api/v1/scans`, `POST /api/v1/scans/upload`, `GET/PUT/DELETE /api/v1/scans/{id}` |
| Recommendations | `POST /api/v1/recommendations/treatment`, `POST /api/v1/recommendations/check-contraindication`, `GET /api/v1/recommendations/drugs`, `GET /api/v1/recommendations/finding-mappings` |

## Next steps

- Test endpoints in Swagger
- Review `backend/app/services/recommendation_engine.py`
- Week 1 QA artifacts live in [`docs/qa/`](qa/README.md)
- ML weights and the model card live in [`ml/`](../ml/README.md)
