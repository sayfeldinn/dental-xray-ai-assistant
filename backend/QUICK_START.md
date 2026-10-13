# DentalAI Backend - Quick Start Guide

**Backend**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**Status**: ✅ Running with 15 test patients

---

## ✅ What's Working

- **Backend API** on port 8000
- **ML Service (dentex_week3)** on port 8001
- **Database** populated with 15 test patients
- **All CRUD operations** for patients, scans, and findings

---

## 🚀 Quick Commands

### 1. Start Backend
```bash
cd backend
./start.sh
```

### 2. Populate Database
```bash
cd backend
python3 seed_database.py
```

### 3. Run Tests
```bash
cd backend
python3 test_api.py
```

### 4. View API Docs
Open browser: http://localhost:8000/docs

---

## 📊 Test Patients Available

The database now has **15 patients** including:

### Competition Demo Profiles:

1. **Ahmed Hassan** (635e4e66-977f-4d7c-999b-9a9ae100c5ea)
   - Clean infection case → Amoxicillin

2. **Mona El-Sayed** (62777026-2162-46ae-b7ed-d199f2456cd5)
   - Penicillin allergy → Clindamycin

3. **Tarek Mahmoud** (c4421bed-735e-4619-87d9-7c1d665f4a5d)
   - Cardiac risk → AHA prophylaxis

4. **Nour Ibrahim** (1d8c62d2-0b85-4a35-ada3-934702c1aef8)
   - Superficial caries → Restorative only

5. **Omar Farouk** (1b3fcc15-fe0e-4c0b-aef1-ad29d9e4c775)
   - NSAID contraindication → Paracetamol

6. **Layla Mansour** (570a5ad5-11ff-498a-a486-2291934db75c)
   - Hepatic impairment → Dosage adjustment

7. **Youssef Abdel-Rahman** (16 years, 1f458aa0-57d6-48b3-b094-a0c76349d6ba)
   - Pediatric → Weight-based dosing

8. **Salma Kamal** (e709cc8a-a655-4a0a-bf8a-01e6ada248e5)
   - Multiple contraindications

9. **Khaled Naguib** (174f7bb8-f5ec-4e2d-a65b-8fa4312bd035)
   - Renal impairment

10. **Yasmine Fouad** (46161b5d-e04c-414d-b47f-e4ab4fc47752)
    - Healthy standard case

---

## 🔥 Common API Operations

### List All Patients
```bash
curl "http://localhost:8000/api/v1/patients?page=1&page_size=20"
```

### Get Specific Patient
```bash
curl "http://localhost:8000/api/v1/patients/635e4e66-977f-4d7c-999b-9a9ae100c5ea"
```

### Upload X-Ray & Analyze
```bash
# Replace PATIENT_ID and /path/to/xray.jpg
curl -X POST "http://localhost:8000/api/v1/scans/upload" \
  -F "file=@/path/to/xray.jpg" \
  -F "patient_id=635e4e66-977f-4d7c-999b-9a9ae100c5ea" \
  -F "auto_analyze=true" \
  -F "confidence_threshold=0.20"
```

### List Scans for Patient
```bash
curl "http://localhost:8000/api/v1/scans?patient_id=635e4e66-977f-4d7c-999b-9a9ae100c5ea"
```

### Get Findings for Scan
```bash
# Replace SCAN_ID with actual scan UUID
curl "http://localhost:8000/api/v1/scans/{SCAN_ID}/findings"
```

### Review a Finding (Dentist Confirmation)
```bash
curl -X POST "http://localhost:8000/api/v1/findings/review" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "FINDING_UUID",
    "review_status": "confirmed",
    "dentist_notes": "Confirmed - proceed with treatment"
  }'
```

---

## 🖼️ Testing with Real X-Rays

### Option 1: Use Swagger UI (Easiest)
1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/scans/upload`
3. Click "Try it out"
4. Upload an X-ray image file
5. Fill in patient_id from list above
6. Set auto_analyze=true
7. Click "Execute"

### Option 2: Use cURL
```bash
# Example: Upload for Ahmed Hassan
curl -X POST "http://localhost:8000/api/v1/scans/upload" \
  -F "file=@./test_xray.jpg" \
  -F "patient_id=635e4e66-977f-4d7c-999b-9a9ae100c5ea" \
  -F "auto_analyze=true"
```

### Option 3: Use Python Script
```python
import httpx
import asyncio

async def upload_scan():
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open('/path/to/xray.jpg', 'rb') as f:
            files = {'file': ('xray.jpg', f, 'image/jpeg')}
            data = {
                'patient_id': '635e4e66-977f-4d7c-999b-9a9ae100c5ea',
                'auto_analyze': 'true'
            }
            
            response = await client.post(
                'http://localhost:8000/api/v1/scans/upload',
                files=files,
                data=data
            )
            
            print(response.json())

asyncio.run(upload_scan())
```

---

## 📋 Complete Workflow Example

### Step-by-Step: Patient → Scan → Findings → Review

```bash
# 1. List patients to get UUID
curl "http://localhost:8000/api/v1/patients?page=1&page_size=5"

# 2. Upload X-ray for patient
curl -X POST "http://localhost:8000/api/v1/scans/upload" \
  -F "file=@xray.jpg" \
  -F "patient_id=635e4e66-977f-4d7c-999b-9a9ae100c5ea" \
  -F "auto_analyze=true"

# Response will include scan_id and findings_count

# 3. Get findings for the scan
curl "http://localhost:8000/api/v1/scans/{SCAN_ID}/findings"

# 4. Review a finding
curl -X POST "http://localhost:8000/api/v1/findings/review" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "FINDING_UUID",
    "review_status": "confirmed"
  }'

# 5. Get confirmed findings only
curl "http://localhost:8000/api/v1/findings/scan/{SCAN_ID}/confirmed"
```

---

## 🎯 Patient UUID Quick Reference

Copy-paste ready UUIDs for testing:

```bash
# Ahmed Hassan (clean infection)
PATIENT_ID="635e4e66-977f-4d7c-999b-9a9ae100c5ea"

# Mona El-Sayed (penicillin allergy)
PATIENT_ID="62777026-2162-46ae-b7ed-d199f2456cd5"

# Tarek Mahmoud (cardiac risk)
PATIENT_ID="c4421bed-735e-4619-87d9-7c1d665f4a5d"

# Nour Ibrahim (restorative only)
PATIENT_ID="1d8c62d2-0b85-4a35-ada3-934702c1aef8"
```

---

## 📈 Statistics

```bash
# Patient count
curl "http://localhost:8000/api/v1/patients?page=1&page_size=1" | jq '.total'

# Scan count
curl "http://localhost:8000/api/v1/scans?page=1&page_size=1" | jq '.total'
```

---

## 🔍 Troubleshooting

### Backend not running?
```bash
cd backend
./start.sh
```

### ML service not running?
```bash
cd dentex_week3/api
./start.sh
```

### Need to reset database?
Delete patients one by one via Swagger UI or recreate from `supabase/seed.sql`

### Want more test patients?
```bash
cd backend
python3 seed_database.py
```

---

## ✅ Phase 2 Status

**Complete and Working:**
- ✅ Patient CRUD operations
- ✅ Scan upload to Supabase Storage
- ✅ AI analysis via dentex_week3
- ✅ Finding extraction and storage
- ✅ Dentist review workflow
- ✅ 15 test patients with diverse medical profiles

**Next: Phase 3**
- ⬜ Recommendation engine (ADA/AHA rules)
- ⬜ Contraindication checker
- ⬜ Treatment & prescription endpoints

---

## 🎓 Learn More

- **API Docs**: http://localhost:8000/docs
- **Backend README**: `backend/README.md`
- **Phase 2 Status**: `docs/PHASE2_STATUS.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Clinical Guidelines**: `docs/CLINICAL_GUIDELINES.md`

---

**Ready to build Phase 3! 🚀**
