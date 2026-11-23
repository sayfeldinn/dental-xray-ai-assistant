# DentalAI — IEEE IC-FTAI 2026

**AI-assisted dental radiography and patient-history system.** DentalAI surfaces
findings on a panoramic X-ray, ties each one to an FDI tooth, and carries it through
the dentist's review into a rule-based treatment and drug-safety check.

> **Positioning:** DentalAI is an **assistive second-opinion tool**. It does not
> diagnose, prescribe, or make treatment decisions autonomously. Every AI finding is
> pending until a licensed dentist confirms, corrects, or rejects it.

## Current model: v3

The shipped pipeline is **two YOLOv8s detectors joined by geometric association**,
plus two clearly-labelled advisory layers:

```
panoramic X-ray (1024 px)
  ├─ tooth detector    32 FDI classes      → tooth boxes + tooth numbers
  ├─ disease detector  4 classes           → Caries, Deep Caries, Periapical Lesion, Impacted
  │     └─ association: IoU → containment → nearest centre
  ├─ missing-teeth classifier (advisory)   → interior FDI gaps; never enters the report
  └─ 11-class findings detector (advisory) → fillings, crowns, root canals, …; never enters the report
```

**Locked-50 evaluation** — the official DENTEX validation split (50 images, 182
lesions), never used for training or model selection; confidence threshold 0.20:

| Metric | v3 |
| --- | ---: |
| mAP@0.5 | **54.2** |
| mAP@0.5:0.95 | **38.2** |
| Precision | **44.6** (95% CI 39.1–50.2) |
| Recall | **74.2** (95% CI 67.4–80.0) |
| AP@0.5 — Impacted | 75.0 |
| AP@0.5 — Caries | 35.3 |
| AP@0.5 — Periapical Lesion | 55.6 |
| AP@0.5 — Deep Caries | 51.1 |

On the 145 lesions the model matched, label accuracy is **91.7% tooth**, **89.0%
disease**, **100% quadrant**, **82.8% joint**. Counting missed lesions end-to-end,
tooth accuracy is **73.1%** and joint accuracy **65.9%**. On an external Romanian
hospital set (175 images) mAP@0.5 is **43.3** and Caries AP **17.7** — a real
domain-shift drop that we report rather than hide.

v3 improves on v2 on recall (+9.9 pp), end-to-end tooth (+7.7 pp) and joint (+8.8 pp),
all statistically significant. A v4 candidate was **rejected** because it lost 5.5 pp
of end-to-end joint accuracy (p = 0.029). Full report:
[`ml/eval/evaluation_report_v3.md`](ml/eval/evaluation_report_v3.md).

## Locked stack

Do not swap these without team sign-off.

| Layer | Choice | Notes |
| --- | --- | --- |
| Backend | **FastAPI** (Python 3.11/3.12) | `backend/`, port 8000 |
| Database / Auth / Storage | **Supabase** | Postgres + RLS + private `xray-scans` bucket |
| Frontend | **React + Vite + Tailwind** | `frontend/`, port 5173 (8080 in Docker) |
| Detection | **Ultralytics YOLOv8s** | tooth + disease + advisory findings |
| Missing teeth | **ResNet18 classifier + rule fallback** | advisory only |
| Model service | **FastAPI** (`ml/service`) | port 8001 |

**No drug-interaction API.** The RxNav DDI endpoint returns 404 and has been retired.
Contraindications come from a hand-curated, cited table maintained with the dentist,
not a live API. See [`docs/CLINICAL_GUIDELINES.md`](docs/CLINICAL_GUIDELINES.md).

## Repository layout

```
dental-xray-ai-assistant/
├── backend/                    # FastAPI API, clinical rules, Supabase adapters
│   ├── app/api/v1/             # REST routers
│   ├── app/services/           # recommendation/, contraindication/, ml_client/, clinical_workflow.py
│   └── tests/                  # 176 pytest tests (no network)
├── frontend/                   # React clinician UI (review, treatment, feedback)
│   └── src/features/           # patients, scan-review, treatment-plan, feedback-log
├── ml/                         # ACTIVE model service
│   ├── pipeline/               # frozen v3 inference pipeline + config
│   ├── weights/                # v3 *.pt checkpoints (not in git)
│   ├── service/                # FastAPI inference API (:8001) + start.sh
│   ├── eval/                   # locked-50 reports, CIs, significance, external validation
│   │   └── evaluate.py         # the judge — do not replace with ad-hoc scripts
│   ├── research/               # one-off studies (caries, missing teeth)
│   └── tests/                  # model/pipeline tests
├── notebooks/                  # training/eval notebooks + weight fetch scripts
├── supabase/                   # migrations, schema, seed
├── deploy/                     # Cloud Run / Cloudflare scripts
├── submission/                 # IC-FTAI 2026 deck, summary, facts, Q&A
├── docs/                       # setup, architecture, clinical rules, QA
└── docker-compose.yml
```

The active ML service is `ml/`. Earlier models are kept for reference
only: `docs/evidence/mlv2/` (v2 training logs) and `docs/history/` (v1 assets,
phase notes). Their weights are not in git.

## Quick start

Full instructions: [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md).

```bash
# 1. Model weights (public release, tensor-identical to the validated v3 weights)
./notebooks/fetch_release_weights.sh

# 2. Database (local Supabase; applies migrations + seed automatically)
npx supabase start

# 3. Configuration
cp .env.example .env    # fill in Supabase URL/keys; never commit .env

# 4. Services (run each in its own terminal)
cd ml/service && ./start.sh            # ML   :8001
cd backend && ./start.sh                     # API  :8000  (docs at /docs)
cd frontend && npm install && npm run dev    # UI   :5173
```

Or `docker compose up --build` (UI on :8080). **Local e2e note:** if a host-network
`backend-e2e` container already owns `:8000`, start only `docker compose up -d ml frontend`;
the compose `backend` binds the same port. See
[`docs/qa/e2e-clinician-flow.md`](docs/qa/e2e-clinician-flow.md).

## Testing

```bash
cd backend && pytest -q                          # 176 tests, no network
cd frontend && npm run typecheck && npm test     # 29 tests (vitest)
```

CI runs three jobs (guard, backend, frontend) on pushes to `main`/`develop` and on
pull requests, plus a Supabase keep-alive workflow. The clinician loop is also exercised
end-to-end against a local Supabase stack; the run record is in
[`docs/qa/e2e-clinician-flow.md`](docs/qa/e2e-clinician-flow.md).

## What is and is not validated

**Validated**

- Detection and end-to-end tooth/joint accuracy on the locked DENTEX validation split,
  with 95% CIs and paired significance tests.
- External detection on 175 Romanian hospital panoramas (reported with the drop).
- The clinician loop (auth → upload → review → gate → treatment → feedback) on a local
  Supabase stack.
- 176 backend + 29 frontend automated tests.

**Not validated**

- No clinician reader study, no prospective clinic pilot, no regulatory clearance.
- Caries detection is the weakest class (AP 35.3; external AP 17.7).
- Confidence scores are not calibrated; the threshold is an operating-point choice.
- DICOM/PACS ingestion is not implemented (JPEG/PNG/WebP only).
- The missing-teeth and 11-class findings layers are **advisory** and are excluded
  from the clinical report.
- No model retraining from dentist feedback has been performed yet; feedback is logged.

DentalAI is a research prototype, **not a medical device**. Do not use it for patient
care outside a supervised research setting.

## Documentation

- [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) — 5-minute orientation
- [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) — setup and troubleshooting
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layers, data flow, model pipeline
- [`docs/CLINICAL_GUIDELINES.md`](docs/CLINICAL_GUIDELINES.md) — 26 rules and sources
- [`docs/qa/README.md`](docs/qa/README.md) — QA artifacts and demo run records
- [`docs/qa/conference-demo-script.md`](docs/qa/conference-demo-script.md) — 2–3 minute local demo runbook
- [`ml/eval/evaluation_report_v3.md`](ml/eval/evaluation_report_v3.md) — authoritative v3 metrics
- [`MODEL_CARD.md`](MODEL_CARD.md) — intended use, limitations, ethics
- [`submission/FACTS.md`](submission/FACTS.md) — conference source of truth
- [`submission/QA_Prep.md`](submission/QA_Prep.md) — judge Q&A
- [`submission/DECK_V3_REWRITE.md`](submission/DECK_V3_REWRITE.md) — slide-by-slide v3 rewrite
- [`submission/VERIFICATION.md`](submission/VERIFICATION.md) — claim→source check
- [`submission/CONFERENCE_CHECKLIST.md`](submission/CONFERENCE_CHECKLIST.md) — 5-day readiness plan

## Team

Two members:

- **sayfeldinn** — ML Engineer (research & evaluation lead): dataset preparation,
  model training and evaluation, the locked-50 judge, and the conference numbers.
- **Seif-shawky** — Full-stack / Platform Engineer (backend + frontend + DevOps):
  API, clinical rules, data access, clinician UI, deployment and CI.

Both are listed in [`CITATION.cff`](CITATION.cff); the same two-person roster appears
on the submission title slide.

## License and citation

- **Code:** MIT — see [`LICENSE`](LICENSE).
- **Model weights and data:** research/non-commercial only; DENTEX is CC BY-NC-SA 4.0.
  See [`NOTICE`](NOTICE) and [`MODEL_CARD.md`](MODEL_CARD.md).
- **Citation:** [`CITATION.cff`](CITATION.cff).

## Conference materials

IC-FTAI 2026, Alexandria, 23–26 November 2026. The submission folder contains the
deck, one-page summary, fact sheet, verification table and Q&A. The v3 rewrite is the
authoritative content; the binary deck must be updated from it before submission.
