# DentalAI Setup Guide

Complete setup instructions for Week 1 implementation.

## 📋 Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- Supabase account (free tier)
- Git

## 🔧 Supabase Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in project details:
   - Name: `dentalai` (or your preferred name)
   - Database Password: (save this!)
   - Region: Choose closest to you
4. Wait for project to be created (~2 minutes)

### 2. Get API Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following:
   - `Project URL` (looks like: `https://xxxxx.supabase.co`)
   - `anon public` key (under Project API keys)
   - `service_role` key (under Project API keys - keep this secret!)

### 3. Create Storage Bucket

1. In Supabase dashboard, go to **Storage**
2. Click "New bucket"
3. Name: `xray-scans`
4. Set to **Public** bucket (for now - will add RLS policies later)
5. Click "Create bucket"

### 4. Set Up Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy the entire content from `backend/database_schema.sql`
4. Paste into SQL editor
5. Click "Run" to execute
6. Verify tables were created: Go to **Table Editor** and you should see:
   - patients
   - scans
   - treatments
   - prescriptions
   - feedback

## 🐍 Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

1. Copy the example env file:
```bash
cp .env.example .env
```

2. Edit `.env` file and fill in your Supabase credentials:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

SECRET_KEY=generate_a_random_secret_key_here
```

**To generate a SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend should now be running at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## ⚛️ Frontend Setup

### 1. Navigate to Frontend Directory

Open a **new terminal** and:

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

1. Copy the example env file:
```bash
cp .env.example .env.local
```

2. Edit `.env.local` file:
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_API_URL=http://localhost:8000
VITE_API_V1_PREFIX=/api/v1
```

**Important:** Use the same `SUPABASE_URL` and `SUPABASE_KEY` (anon key) from backend setup.

### 4. Run the Frontend Development Server

```bash
npm run dev
```

Frontend should now be running at: http://localhost:5173

## ✅ Verify Installation

### 1. Test Backend

Open http://localhost:8000/docs in your browser. You should see the FastAPI interactive documentation.

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "DentalAI",
  "version": "1.0.0"
}
```

### 2. Test Frontend

1. Open http://localhost:5173 in your browser
2. You should be redirected to the login page
3. Click "Sign Up" and create a test account:
   - Full Name: Test Dentist
   - Email: test@example.com
   - Password: password123
4. After signup, you should be redirected to the Dashboard

### 3. Test Full Stack Integration

1. On the Dashboard, you should see your email in the top right
2. Try clicking on different cards (they will show "Coming soon" pages)
3. Try signing out and signing back in

## 🔍 Troubleshooting

### Backend Issues

**Error: "Missing Supabase environment variables"**
- Make sure `.env` file exists in `backend/` directory
- Verify all required variables are set

**Error: "Failed to create scan record"**
- Check that database schema was run successfully
- Verify Supabase connection by checking `/health` endpoint

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**Error: "Missing Supabase environment variables"**
- Make sure `.env.local` file exists in `frontend/` directory
- Variables must start with `VITE_` prefix in Vite

**Error: "Network Error" or "CORS Error"**
- Make sure backend is running on port 8000
- Check `VITE_API_URL` in `.env.local`

**Port 5173 already in use:**
```bash
# Find and kill the process
lsof -ti:5173 | xargs kill -9
```

### Supabase Issues

**Storage bucket not working:**
1. Go to Supabase dashboard → Storage
2. Click on `xray-scans` bucket
3. Go to "Policies" tab
4. Add policy for public access:
   - Policy name: "Public Access"
   - Target roles: `public`
   - Policy command: `SELECT`
   - Policy definition: `true`

## 📚 API Documentation

Once backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Available Endpoints

#### Authentication
- `POST /api/v1/auth/signup` - Create new account
- `POST /api/v1/auth/signin` - Sign in
- `POST /api/v1/auth/signout` - Sign out
- `GET /api/v1/auth/me` - Get current user

#### Patients
- `GET /api/v1/patients` - List patients
- `POST /api/v1/patients` - Create patient
- `GET /api/v1/patients/{id}` - Get patient
- `PUT /api/v1/patients/{id}` - Update patient
- `DELETE /api/v1/patients/{id}` - Delete patient

#### Scans
- `GET /api/v1/scans` - List scans
- `POST /api/v1/scans/upload` - Upload X-ray
- `GET /api/v1/scans/{id}` - Get scan
- `PUT /api/v1/scans/{id}` - Update scan
- `DELETE /api/v1/scans/{id}` - Delete scan

#### Recommendations
- `POST /api/v1/recommendations/treatment` - Get treatment recommendation
- `POST /api/v1/recommendations/check-contraindication` - Check drug safety
- `GET /api/v1/recommendations/drugs` - List available drugs
- `GET /api/v1/recommendations/finding-mappings` - Get finding mappings

## 🎯 Next Steps

After successful setup:

1. **Test API endpoints** using the Swagger UI at http://localhost:8000/docs
2. **Create test patients** through the frontend (once implemented)
3. **Review recommendation engine** logic in `backend/app/services/recommendation_engine.py`
4. **Prepare for Week 2** - ML model integration

## 🆘 Need Help?

- Check backend logs in the terminal where you ran `uvicorn`
- Check frontend logs in the browser console (F12)
- Review Supabase logs in dashboard → Logs section
- Make sure both backend and frontend are running simultaneously

## 📝 Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- **Backend:** Any changes to Python files will auto-reload
- **Frontend:** Any changes to React files will auto-reload in browser

### Stopping Servers

- Press `Ctrl+C` in the terminal to stop either server

### Running Tests (Future)

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

**Week 1 Setup Complete! 🎉**

You now have a working full-stack application with:
- ✅ Authentication system
- ✅ Database with proper schema
- ✅ Backend API with FastAPI
- ✅ Frontend with React
- ✅ Supabase integration
- ✅ Recommendation engine skeleton
