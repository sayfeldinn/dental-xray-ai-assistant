# QA Artifacts

Owner: Person D — Integration/QA Engineer. See [docs/Week1_Execution_Plan.md](../Week1_Execution_Plan.md) §4 for task context.

| File | Due | Status |
| --- | --- | --- |
| `synthetic-patient-profiles.md` | Day 2 (Tue) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `contraindication-test-cases.md` | Day 3 (Wed) | done (v1, **UNVALIDATED** — dentist meeting not held) |
| `demo-script-outline.md` | Day 4 (Thu) | pending |
| `manual-test-log.md` | Day 4 (Thu) | pending |

**Dependency note:** `contraindication-test-cases.md` must be handed to the Backend Engineer by end of Day 3. If the dentist meeting has slipped, every case is marked `UNVALIDATED` rather than blocking delivery.

**Open QA findings (raised while writing `contraindication-test-cases.md`):**

- **R-06 / R-07 / R-08 have no covering profile** — no patient in `synthetic-patient-profiles.md`
  has liver disease, alcohol use, or a QT-prolonging co-medication, so TC-06, TC-16 and TC-17
  rely on QA-invented overrides. Needs either three appended profiles (P-007…P-009) or a scope
  decision from Team Lead — see §6 of that file.
- **#28 still blocks #17.** The test cases use QA free-text finding names so they stay usable
  independently of the taxonomy reconciliation, but Backend cannot map results into the API
  until `FindingTypeEnum` is settled.
- **#31 — rotate the Supabase service-role key** committed in `START_HERE.md` /
  `SETUP_INSTRUCTIONS.md` (removed from the tree by PR #29, still in git history).

No real patient data in this directory — synthetic/anonymized profiles only.
