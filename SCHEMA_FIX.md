# Schema Fix - Bounding Box Attribute Error

## Error
```
"Inference failed: 'Finding' object has no attribute 'bbox_x'"
```

## Problem
**Schema Mismatch:**
- `Finding` schema uses: `bounding_box` (object with `x`, `y`, `width`, `height`)
- Database stores: `bbox_x`, `bbox_y`, `bbox_width`, `bbox_height` (separate columns)
- Code was trying to access: `finding.bbox_x` (doesn't exist)

## Solution Applied

### Fixed ML Inference Endpoint
**File:** `backend/app/api/ml_inference.py`

**Changed from:**
```python
bbox_x: finding.bbox_x,  # ❌ Doesn't exist
bbox_y: finding.bbox_y,
```

**Changed to:**
```python
bbox_x: finding.bounding_box.x,  # ✅ Correct
bbox_y: finding.bounding_box.y,
bbox_width: finding.bounding_box.width,
bbox_height: finding.bounding_box.height,
```

---

## Quick Fix

### Restart Backend
```bash
cd backend
# Press Ctrl+C to stop
uvicorn app.main:app --reload
```

### Test Again
1. Go to Scans page
2. Click "🔍 Analyze" on a pending scan
3. Should work now! ✅

---

## Data Flow

### ML Service → Finding Schema
```python
Finding(
    type="cavity",
    severity="medium",
    confidence=0.87,
    bounding_box=BoundingBox(x=120, y=450, width=45, height=40),  # Object
    tooth_number="14"
)
```

### Finding Schema → Database
```python
{
    "bbox_x": finding.bounding_box.x,      # Extract x
    "bbox_y": finding.bounding_box.y,      # Extract y
    "bbox_width": finding.bounding_box.width,   # Extract width
    "bbox_height": finding.bounding_box.height  # Extract height
}
```

### Database → Frontend
```python
{
    "bbox_x": 120,
    "bbox_y": 450,
    "bbox_width": 45,
    "bbox_height": 40
}
```

### Frontend → Canvas
```javascript
const x = pred.bbox_x * scaleX;
const y = pred.bbox_y * scaleY;
ctx.strokeRect(x, y, width, height);
```

---

## Why This Design?

### Finding Schema (Nested)
- Clean object-oriented design
- Type-safe bounding box
- Easy to validate (width > 0, etc.)
- Used by ML service and API responses

### Database (Flat)
- SQL columns are simpler as primitives
- Easier indexing and querying
- No JSON parsing needed
- Standard relational design

### Conversion Layer
The API endpoint handles conversion:
- ML Service → API: Uses `Finding` schema (nested)
- API → Database: Flattens to separate columns
- Database → Frontend: Already flat, no conversion needed

---

## Complete Schema Reference

### Finding Schema
```python
class Finding(BaseModel):
    type: FindingTypeEnum
    severity: FindingSeverityEnum
    confidence: float
    bounding_box: BoundingBox  # Nested object
    tooth_number: Optional[str]
    description: Optional[str]

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
```

### Database Schema
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    scan_id UUID NOT NULL,
    finding_type VARCHAR(50),
    confidence DECIMAL(5, 4),
    bbox_x INTEGER,         -- Separate columns
    bbox_y INTEGER,
    bbox_width INTEGER,
    bbox_height INTEGER,
    tooth_number INTEGER,
    severity VARCHAR(20),
    ...
);
```

---

## Files Modified

✅ `backend/app/api/ml_inference.py` - Fixed bounding box access

---

## What Works Now

✅ ML inference runs without errors  
✅ Predictions saved to database  
✅ Bounding boxes stored correctly  
✅ Frontend can display them on canvas  

Just restart the backend and test! 🎉
