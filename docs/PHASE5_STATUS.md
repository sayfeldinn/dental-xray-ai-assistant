# Phase 5 Status: Clinician Frontend

**Verified:** 21 frontend tests (vitest), typecheck and production build pass; backend still 147 tests.
The full loop was driven in a real browser (Playwright) against the dev Supabase with a throwaway patient, then deleted (0 rows left).

## What was built (`frontend/`, see `frontend/README.md`)

| Screen | Loop step | What the dentist does |
| :--- | :--- | :--- |
| Patients | - | Search, create a patient (allergies, medications, conditions, weight feed the safety checker) |
| Patient | 1 | See safety-relevant history, list scans, upload an X-ray (optionally run AI analysis) |
| Scan → Review findings | 2-3 | Radiograph with colour-coded FDI boxes (pending/confirmed/modified/rejected); confirm, reject, relabel; report a missed lesion; read the AI report (marked pending) |
| Scan → Treatment plan | 4-5 | Set clinical context (active infection, pain), generate/regenerate; confirm/modify/cancel treatments; review each prescription in the decision panel; add own treatment or prescription |
| Scan → Feedback log | 6 | Ledger of every correction (AI → dentist), with counts by type |

### Decision panel (Step 5)
- Accept / Modify / Reject. Modify edits drug, dose, frequency, duration and runs the live safety check (debounced `POST /prescriptions/check`).
- `warning` → "I have reviewed the warnings" checkbox required. `contraindicated` → written clinical justification required.
- Only edited fields are sent. The backend re-checks and its 422/409 message is displayed.

## Browser walkthrough (what was observed)
Patient with penicillin allergy and warfarin; 9 AI findings from a seed scan.
1. Confirmed 37 (Deep Caries) and 48 (Impacted), rejected one 27 Caries → dashed box, ledger `false_positive`.
2. Generated with infection + pain → Clindamycin (R-18: amoxicillin excluded by allergy; R-19 info) and Paracetamol (R-18: ibuprofen excluded by warfarin); surgical-extraction plan for 48.
3. Clindamycin: Accept disabled until acknowledged, then accepted.
4. Paracetamol modified to 1000 mg every 4 h → live check **contraindicated (R-23, 6000 mg/day > 4000)** and justification required; changed to every 8 h → warning (R-18 kept) → acknowledged and saved → ledger `dosage_adjusted`.
5. Cancelled the 48 treatment → ledger `custom_note`.

Bugs found and fixed during the walkthrough: duplicate React keys for repeated plan alerts; stale acknowledge box while a check was in flight; finding list re-ordering after each review (now sorted by tooth); "Decision: — → modified" noise in the ledger view; missing favicon.

## Known limitations
1. **No authentication** (`dentist_id` stays NULL). Supabase Auth is the next step; until then anyone who can reach the UI can act.
2. **Plan alerts** (e.g. duplicate drug skipped) are shown only right after generation; they are not stored, so a reload hides them.
3. **Mobile width not verified** in the browser (layout uses responsive grids and scrollable tables).
4. **Patient editing** (PUT) and scan deletion are not in the UI; use the API.
5. **Test pollution:** with the ML service running, finding corrections are forwarded to `dentex_week3/feedback/*.csv`. One test row was appended during the walkthrough and reverted.
