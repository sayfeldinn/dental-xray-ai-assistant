# DentalAI — Clean Architecture Specification

## 1. System Philosophy & Non-Negotiable Constraints

DentalAI is built for clinical decision support in dental clinics under the **IEEE IC-FTAI competition rules**. As the system is built and maintained by a team of engineers, every contributor must strictly observe the following foundational principles:

1. **Assistive, Never Autonomous ("The System Proposes, The Dentist Decides"):**
   - No finding, diagnosis, prescription, or dosage is committed to a patient's medical record without explicit confirmation by the treating dentist.
   - Every user interface screen and API response must visibly disclose that AI outputs are recommendations pending dentist validation.
2. **Deterministic & Auditable Recommendation Engine:**
   - Drug dosing and contraindication logic are **rule-based** and sourced from cited clinical dental guidelines (ADA, AHA, AAPD).
   - Generative LLM hallucination for drug dosages is strictly forbidden in production.
3. **Clean Architectural Boundaries:**
   - **Data Layer:** Supabase PostgreSQL + Supabase Storage (`xray-scans`).
   - **Inference Layer:** Standalone Python microservice (`dentex_week3` on port 8001).
   - **Backend Service Layer:** FastAPI (`backend/` on port 8000) housing domain models, recommendation rules, contraindication checks, and database adapters.
   - **Clinician Frontend Layer:** React + Vite + Tailwind CSS (`frontend/` on port 5173).

---

## 2. The 6-Step Clinical Loop (Data Flow)

```
[ Step 1: Scan Ingestion ]
      │ (Panoramic radiograph uploaded to Supabase Storage)
      ▼
[ Step 2: AI-Assisted Detection ]
      │ (dentex_week3 model detects Quadrants, Teeth FDI, Pathology Bounding Boxes)
      ▼
[ Step 3: Dentist Finding Validation ]
      │ (Dentist reviews findings: Confirms, Rejects, or Modifies)
      ▼
[ Step 4: Condition-Specific Recommendation ]
      │ (Rule engine maps confirmed findings to treatments & candidate drugs)
      │ (Contraindication validator scans patient allergies, meds, conditions)
      ▼
[ Step 5: Dentist Prescription Confirmation ]
      │ (Dentist approves, adjusts dosage, or overrides with clinical justification)
      ▼
[ Step 6: Active Feedback & Logging ]
        (Audit ledger logs discrepancies between original AI output and dentist decisions)
```

---

## 3. Directory Structure & Modular Layout

```
dental-xray-ai-assistant/
├── .env                          # Central active environment variables
├── .env.example                  # Sanitized template for team members
├── dentex_week3/                 # STANDALONE AI MODEL MICROSERVICE (DO NOT MODIFY PIPELINE)
│   ├── api/app.py                # FastAPI microservice running on port 8001
│   └── production/               # Pretrained weights (.pt, .joblib) and inference pipeline
├── supabase/
│   ├── schema.sql                # Complete Supabase DDL schema, RLS, indexes, and storage
│   └── seed.sql                  # Synthetic demo patient records for competition branches
├── backend/                      # TO BE BUILT IN PHASE 2 (Clean FastAPI backend)
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── core/                 # Config, security, logging
│   │   ├── domain/               # Core clinical entities and validation models
│   │   ├── services/
│   │   │   ├── recommendation/   # Deterministic ADA/AHA clinical recommendation rules
│   │   │   ├── contraindication/ # Allergy, medication, and clinical condition safety checker
│   │   │   ├── ml_client/        # HTTP client communicating with dentex_week3
│   │   │   └── supabase_client/  # Typed data access layer
│   │   └── api/v1/               # Clean REST routers (/scans, /findings, /recommendations, /feedback)
│   ├── tests/                    # Unit & integration test suite
│   └── requirements.txt
├── frontend/                     # TO BE BUILT IN PHASE 5 (React + Vite + Tailwind)
│   ├── src/
│   │   ├── components/           # Reusable UI widgets (Viewer, Alerts, Badges)
│   │   ├── features/             # Feature slices (scan-review, treatment-plan, feedback-log)
│   │   └── lib/                  # Supabase client and API clients
│   └── package.json
├── docs/                         # Team specifications and guides
│   ├── ARCHITECTURE.md           # This document
│   ├── DATABASE_SPEC.md          # Database dictionary, relations, and altering rules
│   ├── CLINICAL_GUIDELINES.md    # ADA/AHA/AAPD pharmacology and contraindication rules
│   └── TEAM_WORKFLOW.md          # Multi-developer collaboration and PR workflow
└── scripts/                      # Utility and verification scripts
```

---

## 4. Layer Responsibilities & Boundaries

### 4.1 AI Model Microservice (`dentex_week3`)
- **Port:** 8001
- **Role:** Pure computer vision inference engine.
- **Inputs:** Raw image bytes (JPEG / PNG / WebP panoramic dental radiograph).
- **Outputs:** Standard JSON containing image dimensions, quadrant coordinates, detection bounding boxes, FDI tooth numbers, disease labels (`Caries`, `Deep Caries`, `Periapical Lesion`, `Impacted`), confidence scores, and raw radiographic summary text.
- **Rule:** The AI microservice does **not** connect to the database directly and does **not** generate prescriptions.

### 4.2 Backend Service (`backend/`)
- **Port:** 8000
- **Role:** Business logic, clinical safety verification, data persistence, and orchestration.
- **Rule Engine:**
  - Caries with no signs of infection: Generates **restorative treatment referral only** (No systemic antibiotics).
  - Active infection / abscess: Recommends first-line antibiotic (**Amoxicillin**), but cross-checks patient allergies. If allergic to penicillins, switches to **Clindamycin** or **Azithromycin**.
  - Cardiac risk patients: Flags need for **pre-procedure prophylaxis** (single dose 30–60m before procedure). Note: Clindamycin is strictly forbidden for cardiac prophylaxis per AHA 2021 guidelines.
  - Pain management: Recommends **Ibuprofen**, unless patient has active GI ulcers, renal impairment, asthma, or anticoagulant therapy, falling back to **Paracetamol**.

### 4.3 Clinician Workstation (`frontend/`)
- **Port:** 5173
- **Role:** Clear, responsive interface for the dentist during consultation and live competition demonstration.
- **Key UI Sections:**
  1. **Radiograph Canvas:** Interactive image viewer displaying detections as color-coded bounding boxes labeled with FDI tooth notation and confidence badges.
  2. **Review Checklist:** Dentist can quickly click "Confirm", "Reject", or "Edit" on each finding.
  3. **Decision Drawer:** Shows condition-specific treatment paths and drug recommendations. Critical contraindication alerts are rendered in bold amber/red banners that cannot be silently skipped.
  4. **Feedback Table:** A live-updating corrections ledger demonstrating Step 6 audit logging.
