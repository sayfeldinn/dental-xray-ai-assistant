# Phase 3: Recommendation & Contraindication Engine — COMPLETED ✅

**Scope:** Steps 4 and 5 of the clinical loop (condition-specific recommendation, dentist prescription confirmation).
**Verified:** 121 automated tests pass on Python 3.12 from a clean `pip install -r requirements.txt`; end-to-end run against the dev Supabase project (throwaway patient, auto-deleted).
**Clinical content status:** every dose, limit and rule cites a published source (ADA 2019, AAPD Reference Manual, AHA 2021, FDA, AGS Beers 2023, dental interaction literature; full list in `CLINICAL_GUIDELINES.md` §6) or is marked **PROJECT**. No clinician has reviewed it (no clinic partner yet): it is source-backed, not clinician-validated, and the product stays assistive.

---

## 1. What was built

```
backend/app/
├── domain/                      # Pydantic models, no I/O
│   ├── treatment.py             # Treatment*, TreatmentDecisionRequest
│   ├── prescription.py          # Prescription*, SafetyWarning, SafetyCheckResult, PrescriptionDecisionRequest
│   ├── recommendation.py        # ClinicalContext, RecommendationRequest/Response, TreatmentPlan, PlanAlert
│   └── errors.py                # NotFoundError / ConflictError / RuleViolationError  -> 404 / 409 / 422
├── services/
│   ├── contraindication/        # PURE. Safety rules R-01..R-26
│   │   ├── catalog.py           #   drug data, regimens, alias vocabularies, preference order
│   │   ├── text_match.py        #   whole-token matching of free-text patient terms
│   │   ├── profile.py           #   PatientSafetyProfile (age/weight/allergies/meds/conditions)
│   │   └── checker.py           #   ContraindicationChecker.check(drug, indication, patient, dosage)
│   ├── recommendation/          # PURE. finding -> treatment + candidate drugs
│   │   ├── rules.py             #   finding-to-treatment table (mirrors CLINICAL_GUIDELINES §1)
│   │   └── engine.py            #   RecommendationEngine.recommend_for_scan(...)
│   ├── supabase_client/         # treatment_service.py, prescription_service.py (persistence only)
│   └── clinical_workflow.py     # loads data, runs engines, applies decision policy, saves
└── api/
    ├── deps.py                  # get_workflow() — override in tests
    └── v1/                      # recommendations.py, treatments.py, prescriptions.py
```

Dependency direction: `api → clinical_workflow → (recommendation → contraindication) + supabase_client → domain`. The two engine packages import nothing from Supabase/FastAPI, so they are fast to test and safe to reason about.

## 2. Endpoints (`/api/v1`)

| Method & path | Purpose |
| :--- | :--- |
| `POST /recommendations/scans/{scan_id}` | Generate proposals for the scan's confirmed/modified findings. Body (optional): `{"clinical_context": {"active_infection": bool, "pain": bool}, "dentist_id": uuid}` → 201 |
| `POST /treatments` | Dentist-authored treatment for a scan (stored `confirmed`; optional `finding_id` must belong to the scan) → 201 |
| `GET /treatments?scan_id=\|patient_id=[&status=]` | Treatments with their prescriptions |
| `GET /treatments/{id}` | One treatment with prescriptions |
| `POST /treatments/{id}/decision` | `confirmed` / `modified` (+`treatment_category`/`description`) / `cancelled` |
| `POST /prescriptions` | Dentist-authored prescription on a confirmed/modified treatment; safety-checked, saved `proposed`, still needs a decision → 201 |
| `GET /prescriptions?treatment_id=\|patient_id=` | List prescriptions |
| `GET /prescriptions/{id}` | One prescription |
| `POST /prescriptions/check` | Stateless safety check of any drug/dose/frequency for a patient (saves nothing) |
| `POST /prescriptions/{id}/decision` | `accepted` / `modified` (+ edited fields) / `rejected`; `acknowledge_warnings`, `override_reason` |

Naming note: Phase 2 planned `PUT /prescriptions/{id}/confirm`. It became `POST …/decision` because the dentist can also modify or reject, and a decision is a non-idempotent action.

## 3. Behaviour worth knowing

- **Assistive only:** every response carries the *Pending Dentist Validation* disclaimer; proposals start `proposed`; nothing is `accepted` without an explicit decision.
- **Re-run is safe:** regenerating replaces untouched proposals and keeps anything the dentist acted on (those findings come back in `skipped_finding_ids`). Regeneration changes proposal IDs.
- **Flagged drugs cannot be silently accepted:** `warning` needs `acknowledge_warnings: true`; `contraindicated` needs a written `override_reason`; both are enforced server-side after re-checking against the *current* patient record.
- **Decisions are final:** a second decision returns 409. Accepting a prescription under a cancelled treatment returns 409.
- **Persistence is not transactional** (Supabase REST): a failure while saving a plan deletes the treatments created in that call.
- The three demo branches (`TEAM_WORKFLOW.md` §4) are covered by `tests/test_recommendation_engine.py`.

## 4. Phase 2 problems fixed on the way

| Problem | Fix |
| :--- | :--- |
| `requirements.txt` (the "Python 3.14 attempt") failed on a clean install: `Client.__init__() got an unexpected keyword argument 'proxy'` | Pinned `gotrue>=2.0,<2.9` (with `httpx<0.26` as supabase 2.3.4 requires). Verified clean install on 3.12. |
| `start.sh` created the venv with whatever `python3` is (3.14 here) | Prefers `python3.12` / `3.11`, errors otherwise. |
| `GET /findings/scan/{id}/confirmed` ignored `modified` findings, so dentist-corrected labels never reached treatment planning | Returns `confirmed` + `modified`; `Finding.effective_disease` picks the corrected label. |
| `POST /findings/review` wrote a placeholder all-zero UUID into `reviewed_by` (FK to `auth.users` → would fail) | `reviewed_by` only written when a real `dentist_id` is given. |
| Review accepted any `confirmed_disease` and `modified` without one | Validated against the four model labels; `modified` requires `confirmed_disease`. |
| CI frontend job failed on every PR (no `frontend/` since the restart) | Steps are skipped until `frontend/package.json` exists. |
| Docs referenced deleted files/PRs, disagreed with each other and with `schema.sql` | Reconciled: `CLINICAL_GUIDELINES.md` §4-5, `DATABASE_SPEC.md`, `ARCHITECTURE.md`, `qa/README.md`, READMEs. |

## 5. Testing

```bash
cd backend
source venv/bin/activate          # Python 3.12
pytest -q                         # 121 tests, <1 s, no network, no .env needed
```

| File | Covers |
| :--- | :--- |
| `test_contraindication.py` | Every rule R-xx, daily-dose limits, QA profiles P-001…P-006, seed-data vocabulary, catalog self-consistency (every default regimen passes its own safety check, adult and child) |
| `test_recommendation_engine.py` | Demo branches, substitution, stewardship, prophylaxis, pediatrics, dedupe |
| `test_clinical_workflow.py` | Idempotent regeneration, locking, decision policy, stale-record re-check, dentist-authored treatments/prescriptions (in-memory fakes) |
| `test_api.py` | Routing, status-code mapping, disclaimer |
| `test_findings_phase2_fixes.py` | Regressions for the Phase 2 bugs above |
| `test_text_match.py` | Whole-token vocabulary matching |

Tests set dummy Supabase env vars *before* importing the app, so they can never reach a real project.

## 6. Research pass (no clinic available)

With no dentist meeting possible, the provisional values were replaced by researched ones; details and citations are in `CLINICAL_GUIDELINES.md` §2, §4, §6.

| Changed | From → To | Source |
| :--- | :--- | :--- |
| Infection alternatives | Clindamycin only → Clindamycin, then Azithromycin (500 mg day 1, 250 mg ×4); Cephalexin added as dentist-only option with R-26 | ADA 2019 chairside guide |
| Antibiotic indication | "infection" → abscess or systemic involvement, not pain alone; follow-up text (3-day re-evaluation, stop 24 h after resolution) | ADA 2019, AAPD |
| Pediatric dosing | "dentist to specify" for most drugs → AAPD weight-based regimens for amoxicillin, clindamycin, azithromycin, cephalexin, ibuprofen, paracetamol (metronidazole stays "dentist to specify": AAPD has no recommendation) | AAPD *Useful Medications* |
| Daily-dose limits (new R-23) | none → ibuprofen 3200, paracetamol 4000 (project 3000), clindamycin 1800, cephalexin 4000 mg/day; pediatric mg/kg/day caps | AAPD, ADA |
| Paracetamol default | "500-1000 mg" → 500 mg q4-6h (passes its own daily check); 3 g project limit kept as a warning tier | AAPD |
| Elderly NSAID (R-03), QT (R-08) | UNVALIDATED drafts → cited (Beers 2023; FDA 2013 + AAPD), QT conditions added | see §6 of guidelines |
| New interaction rules | R-24 metronidazole + warfarin; R-25 NSAID + ACE/ARB + diuretic; R-26 cephalexin + penicillin allergy | dental literature, bpac, ADA |
| Phase 3 spec gaps | no manual creation → `POST /treatments`, `POST /prescriptions` | Phase 2 plan |

## 7. Known limitations / for later phases

1. **Not clinician-reviewed.** Values are source-backed (and AHA/Beers/FDA/interaction items were confirmed from search summaries, not full text, see guidelines §6). Recommended before any real use: a clinician pass over `CLINICAL_GUIDELINES.md` §2 and §4.
2. **Not modelled:** pregnancy/lactation, renal dose adjustment, severity grades of liver/kidney disease, penicillin-reaction severity (the schema has no fields for them). Documented in guidelines §5.14.
3. **No auth yet:** `dentist_id` is optional everywhere and stays NULL (Phase 5 wires Supabase Auth).
4. **Step 6:** built in Phase 4 (`docs/PHASE4_STATUS.md`); this note describes the state at the end of Phase 3.
5. **Vocabulary-based matching:** unknown free-text terms are ignored by design (extend `catalog.py` aliases).
6. A prescription's frequency is parsed from free text for the daily-limit check; an unparseable frequency skips only that check.

## 8. Next: Phase 4 — delivered

See `docs/PHASE4_STATUS.md`. (Test count there: 147, including the 121 from this phase.)
