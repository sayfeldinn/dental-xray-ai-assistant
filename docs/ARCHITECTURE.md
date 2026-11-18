# DentalAI — Architecture Specification

## 1. System philosophy and non-negotiable constraints

DentalAI is a clinical decision-support system built for the **IEEE IC-FTAI 2026
Student Project Track**. Every contributor must observe these principles:

1. **Assistive, never autonomous ("the system proposes, the dentist decides").**
   - No finding, diagnosis, prescription, or dosage is committed to a patient record
     without explicit confirmation by the treating dentist.
   - Every UI screen and API response that shows AI output must disclose that it is a
     recommendation pending dentist validation.
2. **Deterministic and auditable clinical logic.**
   - Treatment and contraindication rules are rule-based and sourced from cited
     guidelines (ADA, AHA, AAPD).
   - Generative-LLM output is never used for drug selection or dosing.
3. **Clean boundaries.**
   - **Data layer:** Supabase PostgreSQL + private Supabase Storage (`xray-scans`).
   - **Inference layer:** standalone FastAPI service (`dentex_week3/api`, port 8001).
   - **Backend layer:** FastAPI (`backend/`, port 8000) — domain models, clinical rules,
     data adapters, orchestration.
   - **Clinician UI:** React + Vite + Tailwind (`frontend/`, port 5173; 8080 in Docker).
   - **Identity:** Supabase Auth issues the dentist token; the backend verifies it and
     scopes every request to that dentist's patients. Clients have no direct table or
     storage access (RLS with no client policies, private bucket, signed URLs).

---

## 2. The six-step clinical loop

```
[ 1. Scan ingestion ]
      │  panoramic radiograph → Supabase Storage (private bucket)
      ▼
[ 2. AI-assisted detection ]
      │  dentex_week3 v3: tooth detector + disease detector + association
      │  advisory layers: missing teeth, 11-class findings (never in the report)
      ▼
[ 3. Dentist finding validation ]
      │  confirm / modify / reject every finding; corrections are logged
      ▼
[ 4. Condition-specific recommendation ]
      │  confirmed findings → rule engine → treatment + candidate drugs
      │  contraindication validator checks allergies, medications, conditions
      ▼
[ 5. Dentist prescription confirmation ]
      │  approve / adjust / reject with clinical justification; safety gates block silently
      ▼
[ 6. Feedback and audit ]
         every AI-vs-dentist discrepancy is written to the feedback ledger
```

The loop is deliberately bidirectional: a scan cannot be re-analysed after any finding
has been reviewed, so the audit trail always refers to the AI output the dentist saw.

---

## 3. Directory structure

```
dental-xray-ai-assistant/
├── .env                          # local environment (never committed)
├── .env.example                  # sanitized template
├── dentex_week3/                 # ACTIVE model microservice
│   ├── api/                      # FastAPI app, start.sh (:8001)
│   ├── production/               # v3 weights + pipeline_config.json (weights not in git)
│   ├── eval/                     # locked-50 reports, CIs, significance, external validation
│   ├── tests/                    # model/pipeline tests
│   └── evaluate.py               # the judge for every model candidate
├── supabase/
│   ├── migrations/               # base schema + auth lockdown (applied by `supabase start`)
│   ├── schema.sql                # full DDL for hosted projects
│   └── seed.sql                  # synthetic demo patients
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py               # entry point, domain-error → HTTP mapping
│   │   ├── core/                 # config, Supabase client factory
│   │   ├── domain/               # Pydantic entities + errors (no I/O)
│   │   ├── services/
│   │   │   ├── contraindication/ # pure safety rules R-01..R-26
│   │   │   ├── recommendation/   # pure finding → treatment + candidate drugs
│   │   │   ├── clinical_workflow.py
│   │   │   ├── ml_client/        # HTTP client for dentex_week3
│   │   │   └── supabase_client/  # typed data access
│   │   └── api/v1/               # patients, scans, findings, recommendations,
│   │                             #   treatments, prescriptions, feedback
│   ├── tests/                    # 176 pytest tests (no network)
│   └── requirements.txt
├── frontend/                     # React + Vite + Tailwind clinician UI
│   ├── src/
│   │   ├── components/           # viewer, alerts, badges
│   │   ├── features/             # patients, scan-review, treatment-plan, feedback-log
│   │   └── lib/                  # Supabase client, typed API client
│   └── package.json
├── notebooks/                    # training/eval notebooks + weight fetch scripts
├── deploy/                       # Cloud Run / Cloudflare scripts
├── submission/                   # IC-FTAI deck, summary, facts, Q&A
├── docs/                         # specifications and guides
├── archive/                      # ml-v1, ml-v2 (historical)
└── scripts/                      # dev/verification tooling
```

---

## 4. Layer responsibilities

### 4.1 Inference service (`dentex_week3`, port 8001)

- **Role:** pure computer-vision inference. No database access, no prescriptions.
- **Input:** JPEG / PNG / WebP panoramic radiograph.
- **Core output:** image dimensions, tooth boxes with FDI numbers, disease boxes with
  `Caries` / `Deep Caries` / `Periapical Lesion` / `Impacted`, confidences, and the
  associated `(tooth, disease)` findings.
- **Advisory output:** `missing_teeth` (ResNet18 classifier with a rule fallback;
  interior gaps only) and `findings` (11-class DentalOPG model). Both carry explicit
  `*_advisory: true` flags and are excluded from the clinical report.
- **Provenance:** every response stores the weights, thresholds and
  `pipeline_version` in `raw_ml_output.model`.
- **Threshold:** `/predict` honours `confidence_threshold` (UI exposes 0.20 / 0.30 /
  0.50; default 0.20). Re-analysis is allowed only before any finding is reviewed.
- **Startup:** `api/start.sh` checks the two required v3 weights, starts uvicorn on
  `:8001`, and warns (does not fail) when the optional advisory weights are absent.

### 4.2 Model pipeline (v3)

```
panoramic
  ├─ tooth detector   YOLOv8s, 32 FDI classes, 1024 px
  ├─ disease detector YOLOv8s, 4 classes, 1024 px
  │     └─ association: IoU → containment → nearest centre
  ├─ missing teeth    ResNet18 classifier (advisory) + rule fallback
  └─ findings         YOLOv8s, 11 classes, 640 px (advisory)
```

- Training data: DENTEX 2023 (tooth: 540 train / 94 val) and DENTEX + OralXrays
  (disease: 10,120 train / 9,848 unique / 107 val; 4 classes).
- The **locked-50** official DENTEX validation split is the judge. It is never used
  for training or model selection. A candidate is promoted only if it beats the
  incumbent on mAP@0.5, Caries AP, tooth accuracy and joint accuracy.
- v3 is the production model. v4 was rejected after losing end-to-end joint accuracy
  (p = 0.029). Full numbers: `dentex_week3/eval/evaluation_report_v3.md`.

### 4.3 Backend (`backend/`, port 8000)

- **Role:** business logic, clinical safety, persistence, orchestration.
- **Rule engine** (authoritative detail: `docs/CLINICAL_GUIDELINES.md`; the dentist
  supplies `active_infection` / `pain` because an X-ray cannot show them):
  - Caries without infection → restorative referral only; no systemic antibiotics.
  - Active infection / abscess → first-line amoxicillin after allergy check; penicillin
    allergy → clindamycin (infection) or azithromycin (cardiac prophylaxis only).
  - Cardiac-risk patients → pre-procedure prophylaxis flag; clindamycin is forbidden
    for cardiac prophylaxis per AHA 2021.
  - Pain → ibuprofen unless GI ulcer, renal impairment, asthma or anticoagulant
    therapy; fallback paracetamol.
- **26 rules** (R-01..R-26) are pure functions with unit tests. Warnings must be
  acknowledged; a contraindicated drug requires a written justification.
- **Persistence:** every state change goes through the typed Supabase adapter. The
  service-role key stays server-side.

### 4.4 Clinician UI (`frontend/`, port 5173 / 8080)

1. **Radiograph viewer** — colour-coded disease boxes, FDI labels, dashed missing-tooth
   boxes, wheel zoom, drag pan and reset.
2. **Review checklist** — confirm / modify / reject per finding; a sticky summary shows
   progress; the confirmed-findings gate blocks treatment until review is complete.
3. **Advisory panel** — missing teeth and 11-class findings are visually separated and
   labelled "advisory"; they never appear in the clinical report.
4. **Re-analysis controls** — confidence threshold (0.20 / 0.30 / 0.50), disabled after
   the first review; the run is stored with its provenance.
5. **Model provenance** — a collapsed card shows the pipeline version, tooth/disease/
   findings weights and missing-teeth gate stored with the run.
6. **Decision drawer** — treatment paths, candidate drugs, contraindication banners that
   cannot be silently skipped.
7. **Feedback tab** — the corrections ledger (Step 6), with no automatic retraining.

### 4.5 Data and security

- Supabase Auth; backend verifies the JWT and scopes every query to the dentist.
- RLS enabled on all clinical tables with **no client policies**; the backend uses the
  service role. The `xray-scans` bucket is private; images are served through
  short-lived signed URLs.
- Cross-dentist access returns 404, not 403, to avoid leaking record existence.
- Local development uses the Supabase CLI stack (`127.0.0.1:54321`). Production deploy
  scripts live in `deploy/`; they require cloud credentials that are not in the repo.

---

## 5. Testing and quality gates

| Gate | Command | Current |
| --- | --- | --- |
| Backend | `cd backend && pytest -q` | **176 passed** |
| Frontend | `cd frontend && npm run typecheck && npm test` | **29 passed** |
| Model | `python dentex_week3/evaluate.py` on locked-50 | v3 frozen |
| E2E | local Supabase + host-network backend | recorded in `docs/qa/e2e-clinician-flow.md` |
| CI | GitHub Actions: guard, backend, frontend | green on `main` |

The model judge is `dentex_week3/evaluate.py`; ad-hoc scripts are not accepted as
promotion evidence. Detection CIs use image-level bootstrap; label accuracy uses Wilson
CIs; paired comparisons use bootstrap and McNemar.

---

## 6. Historical layers

`archive/ml-v1/` (coordinator + random forest) and `archive/ml-v2/` are kept for
reference and reproducibility. They are not deployed. `ml/` and `MLv2/` contain the
earlier training assets. The active pipeline and all current metrics are v3.
