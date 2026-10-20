# QA Artifacts

Owner: Person D — Integration/QA Engineer. See [docs/Week1_Execution_Plan.md](../Week1_Execution_Plan.md) §4 for task context.

| File | Due | Status |
| --- | --- | --- |
| `synthetic-patient-profiles.md` | Day 2 (Tue) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `contraindication-test-cases.md` | Day 3 (Wed) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `demo-script-outline.md` | Day 4 (Thu) | done (DRAFT — inference blocked by #30) |
| `manual-test-log.md` | Day 4 (Thu) | done (run 2 after PR #35: **19 pass / 10 xfail**; run 1 was 13/16) |

> **Reconciliation note (Phase 3):** the backend was restarted in commit `6f7014b`; the old `test_contraindications.py`, the old engine, PR #33/#35 and issues #17/#28 no longer exist in this tree (they live in git history before `6f7014b`). The case IDs below are now covered by the new suite:
> `TC-01…TC-06` and profiles `P-001…P-006` → [`backend/tests/test_contraindication.py`](../../backend/tests/test_contraindication.py); the three demo branches → [`backend/tests/test_recommendation_engine.py`](../../backend/tests/test_recommendation_engine.py). Run with `cd backend && pytest -q` (the CI Backend job now runs it).
> Where these QA drafts disagree with [`docs/CLINICAL_GUIDELINES.md`](../CLINICAL_GUIDELINES.md), the guidelines win; the resolutions are in its §5 (penicillin alternative = Clindamycin for infection / Azithromycin for prophylaxis; paracetamol cap 3 g/day; Dexamethasone not in the catalog).

**Dependency note:** `contraindication-test-cases.md` must be handed to the Backend Engineer by end of Day 3. If the dentist meeting has slipped, every case is marked `UNVALIDATED` rather than blocking delivery.

**Open QA findings:**

- **#33 — engine contract gaps (10 of 29 tests are `xfail`; was 16).** Opened with ten gaps
  found by executing the cases. PR #35 closed six of them — `Azithromycin` added, Paracetamol's
  spurious warfarin interaction removed, allergy warnings now name the allergen, and a
  substitute is now offered. **Still open:** no age/weight/lifestyle parameter, Dexamethasone
  still missing, exact-string condition matching, object-vs-string medications (would 500 the
  endpoint), no dose concept, four unrepresentable findings, and an unmapped finding returning
  HTTP 400. **Blocks #17.**
- **R-06 / R-07 / R-08 have no covering profile** — no patient in `synthetic-patient-profiles.md`
  has liver disease, alcohol use, or a QT-prolonging co-medication, so TC-06, TC-16 and TC-17
  rely on QA-invented overrides. Needs either three appended profiles (P-007…P-009) or a scope
  decision from Team Lead — see §6 of that file.
- **#28 still blocks #17.** The test cases use QA free-text finding names so they stay usable
  independently of the taxonomy reconciliation, but Backend cannot map results into the API
  until `FindingTypeEnum` is settled. Four of six profiles' draft findings have no enum member.
- **#31 — rotate the Supabase service-role key** committed in `START_HERE.md` /
  `SETUP_INSTRUCTIONS.md` (removed from the tree by PR #29, still in git history).

No real patient data in this directory — synthetic/anonymized profiles only.
