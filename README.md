# DentalAI

AI-Assisted Diagnostic & Patient History System for Dental Clinics

Clinical decision-support tool for dentists: analyzes panoramic X-rays, flags possible findings for dentist review, and keeps a longitudinal patient history (scans, findings, prescriptions, treatments). Sold per-seat/per-scan to clinics.

> **Positioning:** assistive second-opinion tool. A licensed dentist confirms or dismisses every flag. Nothing here is an autonomous diagnostic device.

## Stack (locked Day 1 — do not revisit mid-week)

| Layer | Choice |
| --- | --- |
| Backend API | FastAPI (Python) |
| Data + Auth + Storage | Supabase (managed Postgres) |
| Frontend | React |
| Detection model | Ultralytics YOLOv8/v9/v11, fine-tuned |
| Training data | DENTEX + Tufts + Roboflow dental datasets (merged via Roboflow) |
| Drug name standardization | RxNorm / RxNav lookup API (name/ingredient lookup **only**) |

> **No drug-interaction API.** The RxNav DDI endpoint was retired by the NLM (HTTP 404). Contraindications come from a dentist-validated, hand-curated table.

## Repository Layout (proposed — Backend owns final structure)

```
dental-xray-ai-assistant/
├── docs/                  # Project documentation (source of truth for plans)
│   ├── Project_Context.md
│   ├── Week1_Execution_Plan.md
│   └── qa/                # QA artifacts: synthetic profiles, test cases, demo script
├── backend/               # FastAPI app
├── frontend/              # React app
├── ml/                    # Training notebooks, dataset conversion, inference scripts
└── CONTRIBUTING.md        # Branching strategy & workflow
```

## Working Agreement

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first commit. In short: branch off `main`, name branches `<type>/<ticket>`, open a PR, get one teammate review, never push straight to `main`.

## Current Status

Week 1 of 4 — see [docs/Week1_Execution_Plan.md](docs/Week1_Execution_Plan.md) for the day-by-day plan and Friday deliverables checklist.
