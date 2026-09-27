# Debug 500 Internal Server Error

## Error
HTTP 500 when calling `POST /api/v1/ml/infer/{scan_id}`

## Fixes Applied

### 1. Better Error Handling
Added detailed error messages and logging to identify the exact issue.

### 2. Type Conversion
Made sure enum values are converted to strings properly:
- `finding.type.value` instead of `finding.type`
- `finding.severity.value` instead of `finding.severity`

### 3. Integer Conversion
Bounding box coordinates must be integers for the database:
- `int(finding.bounding_box.x)`

---

## To Debug

### Step 1: Restart Backend
```bash
cd backend
# Press Ctrl+C
uvicorn app.main:app --reload
```

### Step 2: Check Backend Terminal
When you click "Analyze", watch the backend terminal for errors.

It will now print:
- "ML prediction error: ..." if ML fails
- "Error processing finding: ..." if data conversion fails
- "Database insert error: ..." if Supabase insert fails
- Full stack trace for debugging

### Step 3: Test Analyze Again
1. Go to Scans page
2. Click "🔍 Analyze"
3. Watch backend terminal
4. Tell me what error shows up

---

## Most Likely Issues

### Issue 1: Predictions Table Doesn't Exist
**Error:** `relation "predictions" does not exist`

**Fix:** Run `ADD_PREDICTIONS_TABLE.sql` in Supabase SQL Editor

### Issue 2: RLS Policy Blocking
**Error:** `new row violates row-level security policy`

**Fix:** Predictions table needs proper RLS policies (included in ADD_PREDICTIONS_TABLE.sql)

### Issue 3: Data Type Mismatch
**Error:** `invalid input syntax for type integer`

**Fix:** Already handled with `int()` conversions in latest code

### Issue 4: Enum Serialization
**Error:** `Object of type FindingTypeEnum is not JSON serializable`

**Fix:** Already handled with `.value` attribute in latest code

---

## Quick Checklist

Before testing:
- ✅ Run ADD_PREDICTIONS_TABLE.sql in Supabase
- ✅ Restart backend
- ✅ Backend terminal is visible
- ✅ Try analyze and watch terminal

---

## If Error Persists

Copy the EXACT error message from backend terminal and share it.

Look for lines like:
```
ML prediction error: ...
Error processing finding: ...
Database insert error: ...
Traceback (most recent call last):
  ...
```

This will tell us exactly what's failing!
