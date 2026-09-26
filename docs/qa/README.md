# QA Artifacts

Owner: Person D — Integration/QA Engineer. See [docs/Week1_Execution_Plan.md](../Week1_Execution_Plan.md) §4 for task context.

| File | Due | Status |
| --- | --- | --- |
| `synthetic-patient-profiles.md` | Day 2 (Tue) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `contraindication-test-cases.md` | Day 3 (Wed) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `demo-script-outline.md` | Day 4 (Thu) | done (DRAFT — inference blocked by #30) |
| `manual-test-log.md` | Day 4 (Thu) | done (**13 pass / 16 xfail** vs engine) |

**Executable suite:** [`backend/tests/test_contraindications.py`](../../backend/tests/test_contraindications.py)
executes every case in `contraindication-test-cases.md`. Run with `cd backend && pytest -q`.
It lights up the Backend CI job, which previously skipped with *"No tests yet"*.

**Dependency note:** `contraindication-test-cases.md` must be handed to the Backend Engineer by end of Day 3. If the dentist meeting has slipped, every case is marked `UNVALIDATED` rather than blocking delivery.

**Open QA findings:**

- **#33 — engine contract gaps (16 of 29 tests are `xfail`).** Ten gaps found by executing the
  cases: no age/weight/lifestyle parameter, two drugs missing from `DRUGS_DATABASE`,
  Paracetamol contradicting R-02, no substitution logic, exact-string condition matching,
  object-vs-string medications (would 500 the endpoint), no dose concept, four unrepresentable
  findings, and an unmapped finding returning HTTP 400. **Blocks #17.**
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
