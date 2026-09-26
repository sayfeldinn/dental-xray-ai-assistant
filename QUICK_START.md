# DentalAI - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Supabase Setup (2 minutes)

1. Go to [supabase.com](https://supabase.com) → Create new project
2. Copy from dashboard:
   - Project URL
   - `anon public` key  
   - `service_role` key
3. Run SQL in SQL Editor: Copy content from `backend/database_schema.sql`
4. Create Storage bucket: Name it `xray-scans`, set to Public

### 2. Backend Setup (1 minute)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup (1 minute)

```bash
# In a new terminal
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your Supabase credentials
npm run dev
```

### 4. Test It (1 minute)

- Open http://localhost:5173
- Click "Sign Up"
- Create account → You're in! 🎉

## 📝 Environment Variables Cheatsheet

### Backend `.env`
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SECRET_KEY=generate_with_python_secrets
```

### Frontend `.env.local`
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
VITE_API_V1_PREFIX=/api/v1
```

## 🔗 Important URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Supabase Dashboard: https://app.supabase.com

## 🆘 Quick Troubleshooting

**Backend won't start:**
```bash
# Check if .env exists
ls -la backend/.env
# Check if port 8000 is free
lsof -ti:8000
```

**Frontend won't start:**
```bash
# Check if .env.local exists
ls -la frontend/.env.local
# Check if port 5173 is free
lsof -ti:5173
```

**Can't login:**
- Make sure backend is running on port 8000
- Check browser console for errors (F12)
- Verify Supabase credentials in both .env files

## 📚 Full Documentation

- Complete Setup: `docs/SETUP_GUIDE.md`
- Project Context: `docs/Project_Context.md`
- Week 1 Plan: `docs/Week1_Execution_Plan.md`
- Status: `docs/WEEK1_STATUS.md`

## ⌨️ Useful Commands

```bash
# Start both servers (macOS/Linux)
./start-dev.sh

# Backend only
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Run tests (future)
cd backend && pytest
cd frontend && npm test
```

## 🎯 Week 1 Checklist

- [ ] Supabase project created
- [ ] Database schema executed
- [ ] Storage bucket created
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can create account and login
- [ ] Dashboard loads successfully

**All checked? You're ready for Week 2! 🚀**
