# Storage Upload Fix Documentation

## Problem Overview

When trying to upload X-ray scans, users were encountering:
```
Status: 403 Forbidden
Error: "new row violates row-level security policy"
```

This was caused by the frontend attempting to upload directly to Supabase Storage using the anon key, which was blocked by Row Level Security (RLS) policies.

## Solution Summary

**Changed the upload flow from:**
```
Frontend → Supabase Storage (anon key) → ❌ RLS blocks
```

**To:**
```
Frontend → Backend API → Supabase Storage (service role) → ✅ Success
```

## Files Modified

### 1. Frontend: `frontend/src/pages/Scans.jsx`
- **Changed:** Upload now sends files to backend `/scans/upload` endpoint using `multipart/form-data`
- **Removed:** Direct Supabase Storage upload from frontend
- **Benefit:** All uploads go through authenticated backend with proper validation

### 2. Backend: `backend/app/api/scans.py`
- **Updated:** File path generation to use consistent `scans/{timestamp}_{uuid}.{ext}` format
- **Already using:** Service role client via `get_supabase_service()` which bypasses RLS

## Quick Fix Steps

### For Users Experiencing the Issue:

1. **Make storage bucket public** (required for viewing images):
   - Go to Supabase Dashboard → Storage → `xray-scans` bucket
   - Click Settings → Toggle "Public bucket" to ON
   - Save

2. **Verify backend environment**:
   ```bash
   cd backend
   cat .env | grep SUPABASE_SERVICE_KEY
   ```
   
   If missing, add to `backend/.env`:
   ```env
   SUPABASE_SERVICE_KEY=your_service_role_key_from_supabase_dashboard
   ```

3. **Restart backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

4. **Test upload** via frontend

### Verification Script

Run the diagnostic script to check your configuration:

```bash
cd backend
python3 verify_storage_config.py
```

This will check:
- ✅ Environment variables are set
- ✅ Supabase connection works
- ✅ Storage bucket exists and is accessible
- ✅ Upload permissions work correctly
- ✅ Database tables are accessible

## Documentation Files

| File | Purpose |
|------|---------|
| `QUICK_FIX_STORAGE.md` | 5-minute quick fix guide |
| `supabase_storage_setup.sql` | SQL scripts for storage policies |
| `README_STORAGE_FIX.md` | This file - overview and summary |
| `../backend/verify_storage_config.py` | Diagnostic verification script |

## Architecture

### Before (Broken)
```
┌─────────┐
│ Browser │
└────┬────┘
     │ 1. Upload file
     ▼
┌─────────────────┐
│ Frontend        │
│ (anon key)      │
└────┬────────────┘
     │ 2. Direct storage upload
     ▼
┌─────────────────┐
│ Supabase        │
│ Storage         │ ❌ RLS denies anon uploads
└─────────────────┘
```

### After (Fixed)
```
┌─────────┐
│ Browser │
└────┬────┘
     │ 1. Upload file (multipart/form-data)
     ▼
┌─────────────────┐
│ Frontend        │
│ (JWT auth)      │
└────┬────────────┘
     │ 2. POST /scans/upload
     ▼
┌─────────────────┐
│ Backend API     │
│ - Validates JWT │
│ - Checks patient│
│ - Uses service  │
│   role key      │
└────┬────────────┘
     │ 3. Upload with service role
     ▼
┌─────────────────┐
│ Supabase        │
│ Storage         │ ✅ Service role bypasses RLS
└─────────────────┘
```

## Security Considerations

### ✅ Secure Practices
- Frontend cannot directly access storage
- All uploads require valid JWT authentication
- Backend validates patient ownership before upload
- Service role key never exposed to frontend
- File names are UUID-based (unguessable)
- Storage bucket is public but URLs are unguessable

### ⚠️ Important Security Notes
- **NEVER** commit `SUPABASE_SERVICE_KEY` to git
- Keep service role key in `.env` (already in `.gitignore`)
- Only use service role key in backend (never frontend)
- Validate all inputs before using service role operations
- Current implementation correctly checks patient ownership

## RLS Policy Configuration

### Database Tables (Already Configured ✅)

All tables have RLS policies that allow service_role access:

```sql
-- scans table INSERT policy
WITH CHECK (
  (auth.uid() = dentist_id) OR 
  (auth.role() = 'service_role')
)
```

### Storage Bucket (Requires Manual Setup)

**Recommended Configuration:**

1. **Make bucket PUBLIC** (allows image viewing via URLs)
   - No upload policies needed (service role bypasses RLS)
   - Public read access for viewing images
   
2. **Alternative: Add RLS policies** (see `supabase_storage_setup.sql`)
   - Granular access control
   - Users can only access their own scans
   - More complex, but more secure for private images

## Testing

### Manual Test
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to `/scans` page
4. Click "Upload New Scan"
5. Select patient and image
6. Click "Upload Scan"
7. ✅ Should succeed and show scan in list

### Automated Verification
```bash
cd backend
python3 verify_storage_config.py
```

Should show all ✅ PASS checks.

## Troubleshooting

### Issue: Still getting 403 errors

**Check:**
1. `SUPABASE_SERVICE_KEY` is set in `backend/.env`
2. Backend was restarted after changing `.env`
3. Service key is the `service_role` key (not `anon` key)
4. User is logged in with valid JWT token

**Run diagnostic:**
```bash
cd backend
python3 verify_storage_config.py
```

### Issue: Images don't display

**Check:**
1. Storage bucket is set to PUBLIC
2. Image URLs are being generated correctly
3. Browser console for CORS errors

**Fix:**
- Supabase Dashboard → Storage → xray-scans → Settings → Public: ON

### Issue: "Patient not found"

**Check:**
1. Patient exists in database
2. Patient's `dentist_id` matches authenticated user ID
3. User is logged in

**Fix:**
- Create a patient from `/patients` page before uploading

## Migration Guide

If you have existing code using direct Supabase Storage uploads:

### Old Code
```javascript
const { error } = await supabase.storage
  .from('xray-scans')
  .upload(filePath, file);
```

### New Code
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('patient_id', patientId);
const response = await api.post('/scans/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

## Support

For more details:
- **Quick fix:** See `QUICK_FIX_STORAGE.md`
- **SQL policies:** See `supabase_storage_setup.sql`
- **Verification:** Run `backend/verify_storage_config.py`
- **Issues:** Check backend logs and browser console

## Changelog

### 2024-10-04
- ✅ Updated frontend to use backend upload endpoint
- ✅ Fixed backend file path generation
- ✅ Created comprehensive documentation
- ✅ Added verification script
- ✅ Added SQL policy templates

---

**Status:** ✅ Fixed and tested

**Impact:** All scan uploads now work correctly without RLS errors
