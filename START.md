# 🚀 Quick Start Guide

## Run Everything in 3 Steps

### Step 1: Terminal 1 - Start Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Terminal 2 - Start Frontend  
```bash
cd frontend
npm run dev
```

**Expected output:**
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

### Step 3: Open Browser
```
http://localhost:5173
```

---

## If Backend Won't Start

### Check Python and Dependencies
```bash
cd backend

# Check Python version
/opt/homebrew/bin/python3.11 --version
# Should show: Python 3.11.x

# Recreate virtual environment if needed
rm -rf .venv
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --reload
```

### Check Environment Variables
```bash
cd backend
cat .env

# Should show:
# SUPABASE_URL=https://dnsitfbvxubrjqcjkqot.supabase.co
# SUPABASE_KEY=your_key_here
# ... etc
```

---

## If Frontend Won't Start

### Reinstall Dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Check Environment Variables
```bash
cd frontend
cat .env.local

# Should show:
# VITE_SUPABASE_URL=https://dnsitfbvxubrjqcjkqot.supabase.co
# VITE_SUPABASE_ANON_KEY=your_key_here
```

---

## First Time Setup Checklist

Before running, make sure:

1. ✅ **Database Schema Applied**
   - Go to Supabase SQL Editor
   - Run `backend/database_schema.sql`

2. ✅ **Storage Bucket Created**
   - Go to Supabase Storage
   - Create bucket: `xray-scans`
   - Make it **public**

3. ✅ **Environment Files Configured**
   - `backend/.env` has Supabase credentials
   - `frontend/.env.local` has Supabase credentials

4. ✅ **Dependencies Installed**
   - Backend: Python packages installed
   - Frontend: npm packages installed

---

## Quick Test

Once both servers are running:

1. Open http://localhost:5173
2. Sign up with email: `test@example.com`, password: `password123`
3. You should see the Dashboard with 4 cards:
   - 📋 Patients
   - 🩻 X-Ray Scans
   - 🔍 Review Findings
   - 💊 Treatments

If you see the dashboard, **everything is working!** 🎉

---

## Ports Used

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **Supabase:** https://dnsitfbvxubrjqcjkqot.supabase.co

Make sure these ports are not in use by other applications.

---

## Stop Servers

- Press `Ctrl+C` in each terminal to stop the servers

---

## Need Help?

1. Check `WEEK2_COMPLETE.md` for detailed documentation
2. Check `TROUBLESHOOTING.md` (if available)
3. Review error messages in terminal/browser console
