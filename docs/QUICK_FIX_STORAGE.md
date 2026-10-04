# Quick Fix: Storage Upload Error (403/RLS)

## The Problem
You're getting:
```
"statusCode": "403",
"error": "Unauthorized", 
"message": "new row violates row-level security policy"
```

When uploading X-ray scans.

## The Solution (5 minutes)

### Step 1: Configure Supabase Storage Bucket

1. Open [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Storage** in the left sidebar
4. Click on the `xray-scans` bucket (create it if it doesn't exist)
5. Click the **⚙️ Settings** icon
6. **Toggle "Public bucket" to ON** ✅
7. Click **Save**

### Step 2: Verify Backend Environment

Check `backend/.env` has both keys:

```bash
cd backend
cat .env | grep SUPABASE
```

Should show:
```env
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role key
```

If `SUPABASE_SERVICE_KEY` is missing:
1. Go to Supabase Dashboard → **Settings** → **API**
2. Copy the `service_role` key (⚠️ secret - keep it safe!)
3. Add to `backend/.env`:
   ```env
   SUPABASE_SERVICE_KEY=your_service_role_key_here
   ```

### Step 3: Restart Backend

```bash
cd backend
# If running, stop it (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload --port 8000
```

### Step 4: Test Upload

1. Open frontend: http://localhost:5173 (or your frontend URL)
2. Navigate to **Scans** page
3. Click **"+ Upload New Scan"**
4. Select a patient
5. Choose an X-ray image
6. Click **"Upload Scan"**

✅ **Expected result:** Upload succeeds, scan appears in the list

---

## Why This Works

### Before (❌ Broken):
```
Frontend → Supabase Storage (anon key) → RLS blocks upload → 403 Error
```

### After (✅ Fixed):
```
Frontend → Backend API (JWT) → Supabase Storage (service_role key) → Bypasses RLS → Success
```

**Key changes made:**
1. ✅ Frontend now sends files to backend `/scans/upload` endpoint
2. ✅ Backend uses service role key (bypasses RLS)
3. ✅ Storage bucket is public (images viewable via URL)

---

## Troubleshooting

### Still getting 403?

**Check service role key:**
```bash
cd backend
python3 -c "from app.core.config import settings; print('Service key set:', bool(settings.SUPABASE_SERVICE_KEY))"
```

Should print: `Service key set: True`

If `False`, add `SUPABASE_SERVICE_KEY` to `.env`

### Images not displaying?

**Make bucket public:**
- Supabase Dashboard → Storage → xray-scans → Settings → Public bucket: ON

### "Patient not found"?

**Create a patient first:**
1. Go to **Patients** page
2. Click **"+ Add Patient"**
3. Fill in details and save
4. Then try uploading scan

---

## What Changed in the Code

### `frontend/src/pages/Scans.jsx`
**Before:**
```javascript
// Direct upload to Supabase Storage (RLS blocked this)
await supabase.storage.from('xray-scans').upload(filePath, selectedFile);
```

**After:**
```javascript
// Upload via backend API (service role bypasses RLS)
const formData = new FormData();
formData.append('file', selectedFile);
formData.append('patient_id', selectedPatient);
await api.post('/scans/upload', formData);
```

### `backend/app/api/scans.py`
Already uses `get_supabase_service()` which provides service role client that bypasses RLS.

---

## Security Notes

✅ **This is secure because:**
- Frontend cannot directly upload to storage
- Backend validates JWT token (user must be logged in)
- Backend checks patient ownership before upload
- Service role key is never exposed to frontend
- Storage URLs are unguessable (UUID-based filenames)

⚠️ **Important:**
- **NEVER** commit `SUPABASE_SERVICE_KEY` to git
- Keep it in `.env` (already in `.gitignore`)
- Only use service role key in backend (never in frontend)

---

## Need More Help?

See detailed documentation:
- `docs/supabase_storage_setup.sql` - SQL policies and configurations
- `docs/Supabase_Storage_RLS_Fix_Guide.md` - Complete architecture explanation

## Quick Checklist

- [ ] Supabase bucket `xray-scans` exists
- [ ] Bucket is set to **Public**
- [ ] `backend/.env` has `SUPABASE_SERVICE_KEY`
- [ ] Backend is restarted after `.env` changes
- [ ] Frontend code uses `/scans/upload` endpoint (✅ already fixed)
- [ ] At least one patient exists in the database
- [ ] User is logged in with valid JWT token

All checked? Try uploading a scan! 🚀
