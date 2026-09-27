# Manual Test Log — recommendation engine (Day 4)

**Owner:** Person D — Integration/QA · **Issue:** #19 · **Date:** 2026-09-27
**Branch:** `test/19-engine-test-suite` · **Suite:** `backend/tests/test_contraindications.py`
**Consumer:** Backend Engineer, issue #17 · **Gap report:** issue #33

**Status:** ⚠️ **UNVALIDATED** — every expected result derives from the DRAFT rules in
[`synthetic-patient-profiles.md`](synthetic-patient-profiles.md) §2, written without a dentist.
A green run proves the engine matches our draft assumptions. It does **not** prove the
assumptions are clinically correct. Re-run after the dentist meeting (issues #1/#6 → table in #11).

---

## 1. How to reproduce

```bash
cd backend
pytest -q            # 19 passed, 10 xfailed   (run 2 — current)
pytest -q -rx        # list each xfail reason
pytest -q --runxfail # show the real assertion behind each xfail
```

No Supabase, no `.env` and no network are required — the suite unit-tests
`recommendation_engine.py` in isolation. See §5 for the import caveat.

| | Run 1 (Day 4) | Run 2 (after PR #35) | CI (`backend` job) |
| --- | --- | --- | --- |
| Date | 2026-09-27 | 2026-09-27 | 2026-09-27 |
| Python | 3.12.10 | 3.12.10 | 3.12 |
| pytest | 8.3.2 | 8.3.2 | 7.4.4 |
| pydantic | 2.13.4 | 2.13.4 | 2.5.3 |
| Result | 13 passed, 16 xfailed | **19 passed, 10 xfailed** | 19 passed, 10 xfailed |

CI picks the suite up automatically: the workflow already contains
`if [ -d tests ] && ls tests/test_*.py ... then pytest -q`, which previously printed
*"No tests yet — skipping"*.

### Run 2 — 2026-09-27, after PR #35 rewrote the engine

Six gaps closed by that PR; their `xfail` markers were deleted because
`xfail_strict = true` turns a passing xfail into a **CI failure** — which is
exactly what happened on PR #36 and is how these were found.

| Case | Gap | What changed in `recommendation_engine.py` |
| --- | --- | --- |
| TC-01b | **E** | warning now reads `… contraindicated due to {allergy} allergy` — names the allergen |
| TC-02 | **B** | `Azithromycin` added to `DRUGS_DATABASE` (no beta-lactam contraindication) |
| TC-04b | **D** | Ibuprofen + warfarin warning now ends `Substitute Paracetamol.` |
| TC-05 | **C** | `Paracetamol.interactions` changed `["warfarin"]` → `[]` |
| TC-06 | **B** | Azithromycin carries `interactions: ["amiodarone", "pimozide"]` |
| TC-08 | **C** | same root cause as TC-05 |

**Still xfail (10):** TC-07, TC-10, TC-13, TC-14, TC-16, TC-17, NC-02b, NC-03b, NC-06b,
gap probe — gaps **A, F, G, H, I** plus the *Dexamethasone half* of **B**.

Each of the 10 was re-confirmed with `--runxfail` to fail on its intended assertion.

---

## 2. Run 1 result summary (Day 4 — superseded by run 2 above)

```
13 passed · 16 xfailed · 0 failures
```

Every one of the 16 xfails was individually confirmed to fail on its **intended assertion**,
not on a harness or import error, by re-running with `--runxfail` and inspecting the traceback.

### 2.1 Passing (13)

| Case | Assertion | Note |
| --- | --- | --- |
| TC-01a | Amoxicillin + penicillin allergy → ≥1 warning | warning fires |
| TC-03 | Metronidazole + penicillin allergy → 0 warnings | R-01 correctly silent |
| TC-04a | Ibuprofen + warfarin → ≥1 warning naming `warfarin` | R-02 fires |
| TC-09 | Ibuprofen, age 35 → 0 warnings | R-03 correctly silent |
| TC-11 | weight-based dose → 0 warnings | ⚠️ **vacuous** — see §3 |
| TC-12 | override age+weight → 0 warnings | ⚠️ **vacuous** — see §3 |
| TC-15 | Paracetamol + diabetes → 0 warnings | R-05 correctly silent |
| NC-01 | P-006 → 0 warnings | zero-warning control |
| NC-02a | no-drug branch → 0 prescriptions | zero-warning control |
| NC-03a | P-002 both drugs → 0 warnings | zero-warning control |
| NC-04 | sulfa allergy + Amoxicillin → 0 warnings | R-09 / R-01 silent |
| NC-05 | clean patient + Amoxicillin → 0 warnings | zero-warning control |
| NC-06a | P-004 minus warfarin → 0 warnings | R-02 keyed on warfarin |

**Strict zero-warning controls passing: 4** (NC-01, NC-02a, NC-03a, NC-04, NC-05 → 5 rows,
NC-06a is a split case). Requirement was ≥3 — **met**.

### 2.2 xfail (16) — each names a gap in #33

| Case | Assertion that fails | Gap |
| --- | --- | --- |
| TC-01b | warning must name `penicillin` | **E** wording |
| TC-02 | Azithromycin → 0 warnings | **B** drug missing |
| TC-04b | Paracetamol offered as alternative | **D** no substitution |
| TC-05 | Paracetamol → 0 warnings | **C** self-contradiction |
| TC-06 | QT warning naming amiodarone | **B** drug + R-08 missing |
| TC-07 | age factor shown in warning | **A** no age input |
| TC-08 | Paracetamol, elderly → 0 warnings | **C** self-contradiction |
| TC-10 | adult dose blocked for 18 kg | **A** no weight input |
| TC-13 | weight check independent of age | **A** no weight input |
| TC-14 | Dexamethasone glycemic warning | **B** drug + R-05 missing |
| TC-16 | liver disease → numeric dose cap | **F** token mismatch + **H** |
| TC-17 | alcohol → avoid-alcohol warning | **A** no lifestyle field |
| NC-02b | P-001 finding representable | **I** (overlaps #28) |
| NC-03b | dosages match draft table | **H** no dose input |
| NC-06b | R-03 fires without warfarin | **A** no age input |
| gap probe | object-shaped medications | **G** `AttributeError` → 500 |

`xfail_strict = true` (in `backend/pytest.ini`): when a gap closes the test starts passing,
**CI turns red**, and the marker must be deleted. Gaps cannot rot silently.

---

## 3. Honest caveats

- **TC-11 and TC-12 pass vacuously.** They assert *0 warnings*, and the engine has **no dose,
  age or weight concept at all** — so they would pass even if it were broken differently.
  They guard nothing about dosing today. TC-13 is the case that would, and it is xfail.
- **NC-02a does not test P-001.** P-001's draft finding (*"Generalized mild gingivitis"*)
  has no member in `FindingTypeEnum`, so the no-drug branch is exercised via the only path in
  `FINDING_TO_TREATMENT_MAP` that legitimately carries `drugs: []` — `CAVITY` + `low`.
  P-001 itself is NC-02b (xfail, gap I / #28).
- **4 of 6 profiles' findings are not representable** in `FindingTypeEnum` (P-001, P-003, and
  P-002/P-005 only after normalization). Tracked in #28.
- **Medications are stored as strings**, not the object shape profiles §5 specifies — a
  deliberate workaround for gap G. The dedicated gap probe reproduces the `AttributeError`.

---

## 4. Rule coverage against the run

| Rule | Positive case | Outcome | Negative case | Outcome |
| --- | --- | --- | --- | --- |
| R-01 Allergy | TC-01a, TC-01b | ✅ / ✅ (run 2) | TC-02, TC-03, NC-04 | ✅ / ✅ / ✅ |
| R-02 Drug–drug | TC-04a, TC-04b | ✅ / ✅ (run 2) | TC-05, NC-06a | ✅ / ✅ |
| R-03 Age | TC-07 | xfail | TC-08, TC-09, NC-06a | ✅ / ✅ / ✅ |
| R-04 Age/weight | TC-10, TC-13 | xfail, xfail | TC-11, TC-12 | ✅ (vacuous) |
| R-05 Condition | TC-14 | xfail (Dexamethasone missing) | TC-15 | ✅ |
| R-06 Condition | TC-16 | xfail | — | — |
| R-07 Lifestyle | TC-17 | xfail | — | — |
| R-08 Drug–drug | TC-06 | ✅ (run 2) | — | — |
| R-09 Negative control | — | — | NC-01, NC-04 | ✅, ✅ |

**All 9 draft rules are exercised.** Run 1 could not fire 6 of 9 for structural reasons.
Run 2 closed three of them: R-01 wording, R-02's substitute, and R-08. **R-03, R-04, R-06
and R-07 still cannot fire at all**, and R-05 still cannot fire for Dexamethasone — all
captured in #33.

---

## 5. Not covered by this run

- **The API layer.** `POST /recommendations/treatment` and `/check-contraindication` are not
  called — no HTTP, no auth, no Supabase. Gap **G** (object-shaped medications) would 500 the
  endpoint in production; the suite only reproduces it at the function level.
- **The config / supabase / schema-persistence layers** are exercised by no test in this repo.
  `app/core/config.py` calls `Settings()` at module level with required fields, so importing
  through the normal package chain requires `.env` — the suite therefore bypasses the two
  package `__init__` files (see the comment in `tests/conftest.py`). Worth raising as a gap.
- **Any finding-name validation** (see `contraindication-test-cases.md` §9).
- **Anything clinically validated** — see the status banner.

---

## 6. Blockers carried forward

| Blocker | Issue | Effect |
| --- | --- | --- |
| Six engine contract gaps remain (A, F, G, H, I + half of B) | **#33** | 10 assertions cannot be made |
| Model/enum/QA taxonomy mismatch | **#28** | NC-02b; blocks mapping results into the API for #17 |
| Dentist meeting not held | **#1**, #6, #11 | all expectations DRAFT |
| No inference path | **#30** | demo cannot run on real X-rays |

---

## 7. Sign-off

| Step | Owner | Status |
| --- | --- | --- |
| Cases written | Integration/QA | ✅ v1 (`contraindication-test-cases.md`) |
| Cases executed against engine | Integration/QA | ✅ run 1: **13 pass / 16 xfail** · run 2: **19 pass / 10 xfail** |
| Failures triaged | Integration/QA | ✅ #33 (10 gaps at open → **6 remaining**) |
| Handed to Backend | Integration/QA | ✅ issue #17 + PR review request |
| Gaps fixed | Backend | 🟡 **partial** — 6 of 16 closed by PR #35, 10 remain |
| Rules re-validated against dentist table | Team Lead (#11) | ⛔ **not done — blocks sign-off** |
| Re-run after #11 and #33 | Integration/QA | pending |

**No real patient data in this document — synthetic/anonymized inputs only.**
