# Demo Script Outline — three required branches (Day 4 draft)

**Owner:** Person D — Integration/QA · **Issue:** #19 · **Consumer:** whole team,
issue #21 (*End-of-week checkpoint demo*)
**Status:** ⚠️ **DRAFT — blocked where marked.** Every clinical claim below is
**UNVALIDATED** (dentist meeting, issues #1/#6 → table in #11 not held).

Friday's checkpoint per `docs/Week1_Execution_Plan.md` §4 needs *"the model running
inference on one sample scan, the backend rules running against one synthetic profile,
and the UI shells, even unpolished."* This outline covers the middle of those three plus
the branch structure the profiles were built for.

---

## 0. Time budget and shape

| Segment | Min | Owner on the day |
| --- | --- | --- |
| Preconditions check (§1) | 3 | Integration/QA |
| Branch A — no-drug | 2 | Backend |
| Branch B — drug, no conflict | 2 | Backend |
| Branch C — drug, conflict | 4 | Backend + Frontend |
| Honest gaps rundown (§5) | 3 | Integration/QA |

**Target ≤ 15 minutes.** The gaps rundown is not padding — it is the part that makes the
rest credible. Do not cut it.

---

## 1. Preconditions — verify before anyone joins

| # | Need | State | If missing |
| --- | --- | --- | --- |
| 1 | `backend` running (`scripts/start-dev.sh`) | | fall back to the pytest suite, §4 |
| 2 | `frontend` running | | demo the two UI shells against mock data |
| 3 | Auth token (`POST` login) — every recommendation route has `Depends(get_current_user_id)` | | blocks *all* API branches |
| 4 | Six profiles seeded into `patients`, with `dentist_id` matching the logged-in user | | branches return **404 Patient not found** |
| 5 | `backend/tests/test_contraindications.py` green | 19 passed / 10 xfailed | stop — see §4 |
| 6 | Model weights available (`v0.1-dental-yolov8s` Release asset) | | inference segment cannot run — #30 |

**Known seeding problem (gap A, #33):** `age_years` and `weight_kg` are **not columns in the
patients schema**, so P-004's age 72 and P-005's 18 kg **cannot be stored at all**. Branch C
can therefore only demo the *interaction* and *allergy* flavours of conflict, not the
age/weight one. Say so rather than letting it fail on stage.

---

## 2. The three branches

Profiles verbatim from [`synthetic-patient-profiles.md`](synthetic-patient-profiles.md) §4.
Contract IDs are stable — do not renumber.

### Branch A — no drug needed

| | |
| --- | --- |
| **Profile** | **P-001** — 28/F, 62 kg, no allergies, no meds, no conditions |
| **Finding** | *Generalized mild gingivitis, calculus deposits* |
| **Treatment** | Scaling + oral hygiene instruction |
| **Expected** | 0 warnings · 0 prescriptions · branch = no-drug · dentist confirmation field empty |

**Steps**
1. Load the scan → review screen shows the finding (⚠️ see §3 — this finding has no enum member).
2. Confirm treatment → the confirmation screen renders **no proposed drug** and no warning.
3. Show that `Finding.confirmed` is still `false` — the dentist has not signed off.

**Talking points**
- The system can correctly say *"nothing to prescribe"*. Silence is a clinical output.
- This is the branch that keeps the engine from over-prescribing.

**Known caveats — state these out loud**
- ⚠️ **Blocked by #28:** `FindingTypeEnum` has no gingivitis/periodontal member.
  `recommendation_engine.recommend_treatment()` returns `None` for an unmapped finding and the
  endpoint turns that into **HTTP 400**, not a clean empty recommendation (gap J).
- **Working fallback:** a `CAVITY` + `low` finding carries `drugs: []` and produces a genuine
  0-prescription result. This is what test `test_nc02_no_drug_branch_yields_no_prescriptions`
  exercises. Use it to demonstrate the *mechanism*, and say the real finding is pending #28.

### Branch B — drug proposed, no conflict

| | |
| --- | --- |
| **Profile** | **P-006** — 45/F, 90 kg, sulfa allergy, metformin, well-controlled T2D |
| **Finding** | *Tooth 47 → root canal treatment* |
| **Treatment** | Endodontics + analgesia → Paracetamol 500 mg q6h PRN |
| **Expected** | **0 warnings** — sulfa allergy must not fire (R-09), metformin + paracetamol clean, obesity alone must not warn |

**Steps**
1. Open the scan → finding = `root_canal`, severity `medium`.
2. Confirm → confirmation screen shows **Paracetamol 500 mg / every 4-6 hours as needed / 5 days**
   with **no warning banner**.
3. Point at the allergy field and say: *"sulfa is recorded, and we deliberately do not warn."*

**Talking points**
- A safety tool that cries wolf is as useless as one that is blind — this branch is the proof
  we are not warning on everything.
- **Verified:** `test_nc01_paracetamol_clean_for_p006` and `test_nc04_...` both pass.

**Alternate for this branch:** **P-002** (healthy adult, Amoxicillin + Paracetamol) if you want
two proposed drugs on screen instead of one.

**Known caveats**
- ⚠️ **Dosage will not match the profile.** P-002 specifies *Amoxicillin 500 mg q8h × 5 days*;
  the engine emits `DRUGS_DATABASE` defaults — **7 days**, frequency *"3 times daily"*. This is
  gap H (`test_nc03_dosages_match_draft_table` is xfail). Either avoid quoting durations, or
  name the gap.
- P-006's diabetes is stored as free text and would not match a condition token (gap F) —
  harmless here because R-05 is not the rule under test.

### Branch C — drug proposed, with conflict

Two flavours are demoable; a third is not.

#### C1 — allergy (fully demoable today)

| | |
| --- | --- |
| **Profile** | **P-003** — 19/F, 55 kg, **penicillin allergy**, atopic eczema |
| **Finding** | *Tooth 38 pericoronitis* |
| **Expected** | Blocking warning (R-01); Amoxicillin **not** silently kept; alternative surfaced; warning names the allergen |

**Steps**
1. Load scan → confirm → confirmation screen shows Amoxicillin **with a warning banner**.
2. Read the warning aloud.

**Talking points + honest narration**
- ✅ The warning *fires*. `test_tc01_amoxicillin_warns_on_penicillin_allergy` passes.
- ✅ The text now names the allergen — **"Allergy alert: Amoxicillin contraindicated due to
  penicillin allergy. Consider Azithromycin."** (`test_tc01b` passes since PR #35; gap E closed).
- ✅ **An alternative is offered**, and Azithromycin is now in `DRUGS_DATABASE`, so it can be
  checked in its own right (gap B closed for Azithromycin).
- ⚠️ Still open: Dexamethasone is missing from `DRUGS_DATABASE`, so the R-05 diabetes branch
  (TC-14) remains xfail.
- **Line to use:** *"Six of the sixteen gaps the test suite found were closed this afternoon by
  the backend engineer — the remaining ten are listed in issue #33."*

#### C2 — drug interaction (fully demoable today)

| | |
| --- | --- |
| **Profile** | **P-004** — 72/M, warfarin + amlodipine + atorvastatin |
| **Finding** | *Tooth 26, hopeless prognosis → extraction* |
| **Expected** | ≥2 warnings — R-02 (warfarin × NSAID, Paracetamol offered) **and** R-03 (age ≥ 65) |

**Steps**
1. Confirm with Ibuprofen proposed → warning shows **"Drug interaction: Ibuprofen co-administered with Warfarin increases bleed risk. Substitute Paracetamol."**
2. Swap to Paracetamol → it now comes back **clean**.

**Talking points + honest narration**
- ✅ `test_tc04_ibuprofen_warns_on_warfarin` passes and names the interacting drug.
- ✅ **The substitute is named in the warning** — gap D closed.
- ✅ **Paracetamol now clears.** It no longer declares `warfarin` as an interaction, so R-02's
  own recommended substitute is clean (gap C closed; `test_tc05` and `test_tc08` pass).
  *The suite caught this and the backend engineer fixed it the same day.*
- ⚠️ **Only one warning appears, not two.** R-03 (age 72) never fires: there is no age input
  (gap **A**), and `age_years` is not even a column. `test_tc07` and `test_nc06b` are xfail.
- **Line to use:** *"We flagged the interaction, named the substitute, and proved the substitute
  is clean. What we still cannot do is warn on age — that field does not exist yet."*

#### C3 — age / weight (⛔ not demoable)

**P-005** (6 y/o, 18 kg, adult Ibuprofen dose) was built for this. **It cannot run:**
`weight_kg` does not exist in the schema and the engine takes neither age nor weight
(gap **A**). Tests TC-10 and TC-13 are xfail; TC-13 is the highest-value case in the whole
QA document. Show the xfailed test rather than pretending to demo it.

---

## 3. Inference segment (Friday checkpoint)

**Blocked by #30** — there is no inference path: no `predict.py`, no prediction endpoint.
Week 1 checkpoint expects *"the model running inference on one sample scan."*

- **Weights exist:** Release `v0.1-dental-yolov8s`, 22,601,514 bytes, sha256
  `df4455861a67fd683a0ab44b0f461b889624b513738b7cbb6c0ea3adc033a2ed`.
- **Taxonomy mismatch:** the model predicts 5 classes
  (`0 Inter-Radicular / 1 Non-Odontogenic / 2 Periapical / 3 Pericoronal / 4 Caries`) against
  `FindingTypeEnum`'s 7 unrelated values. Also tracked in **#28**.
- **Fallback for Friday:** show the notebook (`ml/train_dental_yolov8s.ipynb`) and the model
  card (`ml/README.md`) instead of a live run, and name #30 + #28 as the blockers.

---

## 4. Fallback if the backend will not start

Run the suite — it needs no server, no Supabase and no `.env`:

```bash
cd backend && pytest -q -rx
```

`19 passed, 10 xfailed` proves the engine matches our contract on everything the contract
currently supports, and each xfail reason names the blocking gap. Read the reasons aloud;
they *are* the gap report (#33).

---

## 5. What must be said — claims we cannot make

Do not present any of the following as done:

| Claim | Why we can't | Issue |
| --- | --- | --- |
| "Rules are dentist-validated" | meeting never held; all expectations DRAFT | #1, #6, #11 |
| "The model runs on X-rays" | no inference path | #30 |
| "Findings map to the API" | taxonomy unreconciled | #28 |
| "Contraindications are covered" | 10 of 29 assertions blocked | #33 |
| "Age and weight are checked" | fields don't exist | #33 gap A |
| "We cover the draft six drugs" | Dexamethasone still missing from `DRUGS_DATABASE` | #33 gap B |
| "Patient data is protected" | leaked service-role key not yet rotated | #31 |

**What we can honestly claim:** the repo has CI that enforces hygiene and runs tests; six
synthetic profiles cover all three branches; 23 written test cases with 5 negative controls;
a 29-test suite that passes 19 and documents 10 real gaps (6 of the original 16 were closed
within hours of the suite landing); and every open blocker is on the board.

---

## 6. Go / no-go

**Go** if §1 rows 1–5 hold and Branches B + C1 + C2 can be walked.

**No-go** if auth or seeding fails — in that case run §4 (the pytest suite) and do the gaps
rundown. A demo that shows *exactly* what works and what does not scores better than one
that fails on stage.

**Never:** improvise clinical claims, quote draft doses as validated, or skip §5.
