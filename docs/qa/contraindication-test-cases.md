# Contraindication Test Cases — v1 (UNVALIDATED)

**Owner:** Person D — Integration/QA · **Issue:** #15 · **Due:** Day 3 (Wed)
**Status:** ⚠️ **UNVALIDATED — pending dentist meeting.** Every `Expected result` below
derives from the DRAFT rules in [`synthetic-patient-profiles.md`](synthetic-patient-profiles.md)
§2, which were written without a dentist. Re-validate against issue #11 before these
become acceptance criteria.

**Consumer:** Backend Engineer, issue #17 (*"run QA test cases and fix failures"*).

---

## 0. How to use this document

Each row is one invocation of the contraindication check:

```
check_contraindication(patient_fields, candidate_drug) -> warnings[]
```

- **Profile ref** points at a profile in `synthetic-patient-profiles.md`. Take its fields
  verbatim unless the **Input** column adds or overrides something.
- **Input → add/override** lists only the deltas. `∅` means "use the profile exactly as written".
- **Expected result** is the assertion. A case passes only if every clause holds.
- **Rule ID** is the rule the expected result comes from. IDs `R-01`…`R-09` are a stable
  contract — do not renumber them (profiles §5).
- **Source** is where the expectation originated. `profiles §4` = asserted in a profile;
  `profiles §2` = asserted only by the rule table; `TEST-ONLY` = QA-invented, no upstream
  statement — treat as the weakest evidence.

**Rule IDs and expected results are DRAFT.** The dentist meeting (#1/#6) has not happened.

---

## 1. Allergy

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| TC-01 | P-003 | ∅; candidate = Amoxicillin 500 mg q8h | ≥1 **blocking** warning; warning text names `penicillin` as the allergen; Amoxicillin **not** left in the proposal unchanged | R-01 | profiles §4 |
| TC-02 | P-003 | ∅; candidate = Azithromycin 500 mg → 250 mg daily | **0 warnings.** Azithromycin is not a beta-lactam, so R-01 must not fire on class similarity | R-01 (must not fire) | profiles §4 |
| TC-03 | P-003 | ∅; candidate = Metronidazole 500 mg q8h | **0 warnings.** Penicillin allergy is unrelated to nitroimidazoles | R-01 (must not fire) | TEST-ONLY |

**TC-01 additional assertion:** if an alternative is auto-substituted it must be Azithromycin
per the draft list; if no substitution logic exists yet, the warning alone satisfies this case —
but "silently keep Amoxicillin" does **not**.

## 2. Drug–drug interaction

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| TC-04 | P-004 | ∅; candidate = Ibuprofen 400 mg q8h | ≥1 warning; warning detail **lists `warfarin` as the interacting drug**; Paracetamol offered as the alternative | R-02 | profiles §4 |
| TC-05 | P-004 | ∅; candidate = Paracetamol 500 mg q6h | **0 warnings.** Substituting the recommended alternative must clear the warning — proves the engine is not just flagging P-004 forever | R-02 (must not fire) | TEST-ONLY |
| TC-06 | *(no profile)* | **override** `current_medications[] += amiodarone` (any profile); candidate = Azithromycin | ≥1 warning citing cardiology/QT prolongation risk **and** naming the QT-prolonging co-medication | R-08 | profiles §2 |

> ⚠️ **TC-06 has no covering profile.** No profile carries a QT-prolonging drug — see
> [§6 Coverage gaps](#6-coverage-gaps-found-while-writing-this). The `override` is QA-supplied
> input, not a validated patient.

## 3. Age

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| TC-07 | P-004 | ∅; candidate = Ibuprofen 400 mg q8h | ≥1 warning; **age factor (72 / ≥65) shown** in the warning; Paracetamol offered | R-03 | profiles §4 |
| TC-08 | P-004 | ∅; candidate = Paracetamol 500 mg q6h | **0 warnings.** R-03 is NSAID-specific — an elderly patient must not trigger it on a non-NSAID | R-03 (must not fire) | TEST-ONLY |
| TC-09 | P-002 | ∅; candidate = Ibuprofen 400 mg q8h | **0 warnings** from R-03. Age 35 is below the ≥65 threshold; proves the rule keys on age and not merely on "Ibuprofen present" | R-03 (must not fire) | TEST-ONLY |

## 4. Weight / pediatric dose

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| TC-10 | P-005 | ∅; candidate = Ibuprofen **400 mg** (adult dose) | ≥1 **blocking** warning; adult 400 mg **not accepted as-is**; weight-based alternative displayed | R-04 | profiles §4 |
| TC-11 | P-005 | ∅; candidate = Ibuprofen **10 mg/kg/dose** → 180 mg, max 40 mg/kg/day | **0 warnings.** The corrected dose must pass — otherwise the engine blocks without offering a way forward | R-04 (satisfied) | profiles §4 |
| TC-12 | P-005 | **override** `weight_kg = 18` → `60`, `age_years = 6` → `14`; candidate = Ibuprofen 400 mg q8h | **0 warnings.** Both the age floor (<12) and the pediatric weight must be evaluated; flipping **both** out of range must clear it | R-04 (must not fire) | TEST-ONLY |
| TC-13 | P-005 | **override** `age_years = 6` → `14` only, weight stays **18 kg**; candidate = Ibuprofen 400 mg q8h | **≥1 warning.** Age is now out of range but the patient is still 18 kg — an adult dose remains unsafe, so a weight-based check must still fire | R-04 | TEST-ONLY |

**TC-13 is the highest-value case in this document.** It distinguishes an engine that checks
*age and weight independently* from one that short-circuits after the first match. Profiles §4
explicitly asks for "age floor enforced (years AND kg both checked)".

## 5. Condition & lifestyle

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| TC-14 | P-006 | ∅; candidate = Dexamethasone 4 mg daily × 3 days | ≥1 warning about **glycemic control**; the warning names the diabetes context | R-05 | profiles §2 |
| TC-15 | P-006 | ∅; candidate = Paracetamol 500 mg q6h | **0 warnings** from R-05 — Paracetamol does not affect glycemic control | R-05 (must not fire) | TEST-ONLY |
| TC-16 | *(no profile)* | **override** `conditions[] += liver disease`; candidate = Paracetamol 500 mg q6h (or any dose > 2 g/day) | ≥1 warning with a **daily-dose cap**; cap stated numerically | R-06 | profiles §2 |
| TC-17 | *(no profile)* | **override** `lifestyle = alcohol use`; candidate = Metronidazole 500 mg q8h | ≥1 **avoid-alcohol** warning | R-07 | profiles §2 |

> ⚠️ **TC-16 and TC-17 have no covering profiles.** See [§6](#6-coverage-gaps-found-while-writing-this).

## 6. Coverage gaps found while writing this

Three of the nine draft rules have **no patient profile that exercises them**. Rather than hide
that, it is recorded here so the gap is visible to Backend and to the dentist meeting.

| Rule | Needs | Present in any profile? |
| --- | --- | --- |
| R-06 | `conditions[]` contains liver disease | ❌ No — P-001/002/003/005 have no hepatic condition; P-004 has cardiac, P-006 has diabetes |
| R-07 | `lifestyle` = alcohol use | ❌ No — every profile is explicitly non-drinker or silent |
| R-08 | `current_medications[]` contains a QT-prolonging drug | ❌ No — P-004's meds are warfarin/amlodipine/atorvastatin; P-006's is metformin |

**Consequence:** TC-16, TC-17, TC-06 currently depend on QA-invented `override` inputs. They
are marked `TEST-ONLY` / `(no profile)` accordingly.

**Recommendation for Team Lead (#11):** ask the dentist to add three profiles —
`P-007` (liver disease), `P-008` (alcohol use), `P-009` (QT-prolonging co-medication) —
or confirm that R-06/R-07/R-08 should be dropped from scope. Per profiles §5, **append new
IDs, never renumber the existing six**; downstream artifacts already reference P-001…P-006.

## 7. Negative controls (zero-warning cases)

Minimum required: **3**. Supplied: **6**. These are the tests that catch an engine which
over-warns — a false-positive-prone safety tool is as unusable as a blind one.

| ID | Profile ref | Input → add/override | Expected result | Rule ID | Source |
| --- | --- | --- | --- | --- | --- |
| NC-01 | P-006 | ∅; candidate = Paracetamol 500 mg q6h PRN | **0 warnings.** Sulfa allergy recorded but irrelevant to the six-drug list; metformin + paracetamol is clean; obesity alone must not warn | R-09 | profiles §4 |
| NC-02 | P-001 | ∅; no candidate drug (no-drug branch) | **0 warnings · 0 prescriptions · 0 proposed drugs**; branch = no-drug; finding stored with dentist confirmation field empty | — | profiles §4 |
| NC-03 | P-002 | ∅; candidates = Amoxicillin + Paracetamol | **0 warnings**; both dosages match the draft table **exactly** (500 mg q8h × 5 days; 500 mg q6h PRN) | — | profiles §4 |
| NC-04 | P-006 | ∅; candidate = Amoxicillin 500 mg q8h | **0 warnings.** Sulfa allergy ≠ penicillin allergy — cross-reactivity must not be inferred | R-09, R-01 (must not fire) | TEST-ONLY |
| NC-05 | P-001 | ∅; candidate = Amoxicillin 500 mg q8h | **0 warnings.** No allergies, no meds, no conditions, age 28 — nothing to warn about | — | TEST-ONLY |
| NC-06 | P-004 | **override** `current_medications[]` → remove `warfarin` only; candidate = Ibuprofen 400 mg q8h | **≥1 warning from R-03 (age), 0 warnings from R-02.** Isolates the two rules that normally co-fire on P-004 — proves R-02 keys on warfarin and not on "P-004" | R-02 must not fire; R-03 must fire | TEST-ONLY |

**NC-06 is deliberately a split outcome, not a zero-warning case.** It sits here because it
tests non-firing behaviour, but do not count it toward the ≥3 zero-warning minimum on its own.

### Zero-warning count

NC-01, NC-02, NC-03, NC-04, NC-05 = **5 zero-warning cases** → requirement (≥3) met.

---

## 8. Coverage matrix

| Rule | Type | Positive cases | Negative cases | Profile-backed |
| --- | --- | --- | --- | --- |
| R-01 | Allergy | TC-01 | TC-02, TC-03, NC-04 | ✅ P-003 |
| R-02 | Drug–drug | TC-04 | TC-05, NC-06 | ✅ P-004 |
| R-03 | Age | TC-07 | TC-08, TC-09, NC-06 | ✅ P-004, P-002 |
| R-04 | Age/weight | TC-10, TC-13 | TC-11, TC-12 | ✅ P-005 |
| R-05 | Condition | TC-14 | TC-15 | ✅ P-006 |
| R-06 | Condition | TC-16 | — | ❌ override only |
| R-07 | Lifestyle | TC-17 | — | ❌ override only |
| R-08 | Drug–drug | TC-06 | — | ❌ override only |
| R-09 | Negative control | — | NC-01, NC-04 | ✅ P-006 |

**Totals:** 17 positive/exercising cases (TC-01…TC-17) · 6 negative-control rows (NC-01…NC-06)
· 5 strict zero-warning · all 9 draft rules exercised at least once.

## 9. What is *not* covered here

- **Finding names.** Inputs use the free-text finding wording from the QA profiles
  (e.g. *"Tooth 36 deep caries, periapical radiolucency"*). This is deliberately independent of
  `FindingTypeEnum` so these cases stay usable while issue **#28** (model classes vs.
  `FindingTypeEnum` vs. QA profiles) is reconciled. **#28 still has to land before #17 can map
  results into the API** — this document does not unblock #17 on its own.
- **Dose arithmetic beyond R-04.** Only P-005's 10 mg/kg → 180 mg is asserted numerically.
- **Combination multi-drug interactions.** Each case proposes one candidate drug (P-002/NC-03
  proposes two, both inert).
- **Severity ordering / display.** Only presence, wording content, and firing-vs-not.
- **Anything clinically validated.** See status banner.

## 10. Sign-off

| Step | Owner | Status |
| --- | --- | --- |
| Cases written | Integration/QA (Person D) | ✅ v1 |
| Handed to Backend by end of Day 3 | Integration/QA | pending issue #17 |
| Rules re-validated against dentist table | Team Lead (#11) | ⛔ **not done — blocks** |
| Cases executed against engine | Backend (#17) | pending |
| Failures triaged | Integration/QA + Backend | pending |

**No real patient data in this document — synthetic/anonymized inputs only.**
