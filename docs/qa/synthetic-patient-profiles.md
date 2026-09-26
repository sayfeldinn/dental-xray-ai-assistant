# Synthetic Patient Profiles — v1 (UNVALIDATED)

**Owner:** Person D — Integration/QA · **Issue:** #10 · **Due:** Day 2
**Status:** ⚠️ **UNVALIDATED — pending dentist meeting.** The dentist meeting (issues #1/#6) has not happened. The six-drug list and finding-to-treatment mapping below are DRAFT assumptions built only to unblock Day 2–4 work. Every profile, drug, dose, and expected result must be re-checked against the dentist-validated table (issue #11) before Week 2.

**Covers:** 6 profiles (min required: 5) · all three demo branches · ages 6–72 · weights 18–90 kg · allergies (penicillin, sulfa, none) · current medications (warfarin stack, metformin, none)

---

## 1. DRAFT Six-Drug List (UNVALIDATED)

| # | Drug | Class | Draft dose (adult) | Notes |
| --- | --- | --- | --- | --- |
| 1 | Amoxicillin | Antibiotic | 500 mg q8h, 5–7 days | Draft first-line post-extraction prophylaxis |
| 2 | Azithromycin | Antibiotic | 500 mg day 1, then 250 mg daily | Draft penicillin-allergy alternative |
| 3 | Metronidazole | Antibiotic | 500 mg q8h, 5–7 days | Draft anaerobic cover |
| 4 | Paracetamol | Analgesic | 500 mg q6h (max 4 g/day) | Draft first-line analgesic |
| 5 | Ibuprofen | NSAID | 400 mg q8h with food | Draft anti-inflammatory |
| 6 | Dexamethasone | Corticosteroid | 4 mg daily, 3 days | Draft post-op inflammation control |

## 2. DRAFT Interaction/Contraindication Seeds (UNVALIDATED)

Hand-curated draft — replaces the retired RxNav DDI API. Dentist to confirm/correct (issue #11).

| ID | Rule | Type |
| --- | --- | --- |
| R-01 | Beta-lactam allergy → do not recommend Amoxicillin | Allergy |
| R-02 | NSAID + Warfarin → bleeding risk; recommend Paracetamol instead | Drug–drug |
| R-03 | Ibuprofen + age ≥ 65 → dose/renal/GI caution | Age |
| R-04 | Ibuprofen + age < 12 → weight-based dosing only; adult 400 mg dose forbidden | Age/weight |
| R-05 | Dexamethasone + Diabetes mellitus → glycemic-control warning | Condition |
| R-06 | Paracetamol + liver disease → daily-dose cap warning | Condition |
| R-07 | Metronidazole + alcohol → avoid-alcohol warning | Lifestyle |
| R-08 | Azithromycin + QT-prolonging drug → cardiology warning | Drug–drug |
| R-09 | Sulfa allergy → unrelated to this drug list → **must NOT warn** | Negative control |

---

## 3. Demo-Branch Coverage Matrix

| Profile | Branch | Trigger | Age | Weight | Allergies | Current meds |
| --- | --- | --- | --- | --- | --- | --- |
| P-001 | **No-drug** | Scaling only, no systemic drug needed | 28 | 62 kg | none | none |
| P-002 | **Drug, no conflict** | Clean proposal, healthy adult | 35 | 78 kg | none | none |
| P-003 | **Drug, conflict** | Penicillin allergy vs. draft Amoxicillin | 19 | 55 kg | penicillin (rash) | none |
| P-004 | **Drug, conflict** | Warfarin × Ibuprofen, age 72 (R-02, R-03) | 72 | 70 kg | none | warfarin, amlodipine, atorvastatin |
| P-005 | **Drug, conflict** | Child 18 kg given adult Ibuprofen dose (R-04) | 6 | 18 kg | none | none |
| P-006 | **Drug, no conflict** | Sulfa allergy + metformin — must NOT warn (R-09) | 45 | 90 kg | sulfa (rash) | metformin |

---

## 4. Profiles

### P-001 — Sara M. (no-drug branch)

| Field | Value |
| --- | --- |
| Age / Sex | 28 / F |
| Weight | 62 kg (BMI 23) |
| Allergies | none recorded |
| Current medications | none |
| Conditions | none |
| Lifestyle | non-smoker, no alcohol |
| Draft scan finding | Generalized mild gingivitis, calculus deposits |
| Draft treatment (table) | Scaling + oral hygiene instruction |
| Draft drug recommendation | **none** |
| Expected engine output | No proposed drug; no warnings; branch = no-drug |
| Assertions | 0 warnings · 0 prescriptions · finding stored with dentist confirmation field empty |

### P-002 — Omar H. (drug, no conflict)

| Field | Value |
| --- | --- |
| Age / Sex | 35 / M |
| Weight | 78 kg |
| Allergies | none recorded |
| Current medications | none |
| Conditions | none |
| Lifestyle | non-smoker |
| Draft scan finding | Tooth 36 deep caries, periapical radiolucency |
| Draft treatment (table) | Extraction + antibiotic cover, analgesia |
| Draft drug recommendation | Amoxicillin 500 mg q8h × 5 days + Paracetamol 500 mg q6h PRN |
| Expected engine output | Both drugs proposed; **branch = drug-no-conflict** |
| Assertions | 0 warnings · dosages match draft table exactly · both proposals present |

### P-003 — Nour A. (drug, conflict — allergy)

| Field | Value |
| --- | --- |
| Age / Sex | 19 / F |
| Weight | 55 kg |
| Allergies | **Penicillin** — childhood rash (non-anaphylactic, recorded as `penicillin`) |
| Current medications | none |
| Conditions | atopic eczema |
| Lifestyle | non-smoker |
| Draft scan finding | Tooth 38 pericoronitis |
| Draft treatment (table) | Antibiotic cover + analgesia |
| Draft drug recommendation (pre-conflict) | Amoxicillin 500 mg q8h |
| Expected engine output | **Blocking warning (R-01): penicillin allergy → Amoxicillin contraindicated.** Alternative proposed: Azithromycin per draft list. Branch = drug-with-conflict |
| Assertions | ≥1 blocking warning citing allergy · Amoxicillin not silently kept · alternative or "pharmacist/dentist choice" surfaced · warning text names the allergen |

### P-004 — Mahmoud S. (drug, conflict — interaction + age)

| Field | Value |
| --- | --- |
| Age / Sex | **72** / M |
| Weight | 70 kg |
| Allergies | none recorded |
| Current medications | Warfarin 5 mg daily (atrial fibrillation), Amlodipine 5 mg daily, Atorvastatin 20 mg nightly |
| Conditions | atrial fibrillation, hypertension, hyperlipidemia |
| Lifestyle | ex-smoker |
| Draft scan finding | Tooth 26, hopeless prognosis → extraction |
| Draft treatment (table) | Extraction + anti-inflammatory + analgesia |
| Draft drug recommendation (pre-conflict) | Ibuprofen 400 mg q8h |
| Expected engine output | **Warning (R-02): NSAID + warfarin → bleeding risk; Paracetamol offered instead.** **Warning (R-03): age ≥ 65 → NSAID renal/GI caution.** Branch = drug-with-conflict |
| Assertions | ≥2 warnings · warfarin listed as interacting drug in warning detail · age factor shown · Paracetamol alternative present |

### P-005 — Youssef A. (drug, conflict — age/weight extremes)

| Field | Value |
| --- | --- |
| Age / Sex | **6** / M |
| Weight | **18 kg** |
| Allergies | none recorded |
| Current medications | none |
| Conditions | none |
| Lifestyle | n/a (pediatric) |
| Draft scan finding | Tooth 55 extensive caries, non-restorable |
| Draft treatment (table) | Extraction + analgesia |
| Draft drug recommendation (pre-conflict) | Ibuprofen 400 mg (adult dose) — *dose produced by draft logic* |
| Expected engine output | **Blocking warning (R-04): age < 12 + weight 18 kg → adult 400 mg dose forbidden.** Weight-based dose shown instead (draft: 10 mg/kg/dose q6–8h → 180 mg, max 40 mg/kg/day). Branch = drug-with-conflict |
| Assertions | adult dose not accepted as-is · kg-based calculation displayed · age floor enforced (years AND kg both checked) |

### P-006 — Fatma Z. (drug, no conflict — negative control)

| Field | Value |
| --- | --- |
| Age / Sex | 45 / F |
| Weight | 90 kg (obese) |
| Allergies | **Sulfa** — skin rash (irrelevant to draft six-drug list) |
| Current medications | Metformin 1000 mg daily |
| Conditions | Type 2 diabetes, well controlled (HbA1c 6.4%) |
| Lifestyle | non-smoker |
| Draft scan finding | Tooth 47 → root canal treatment |
| Draft treatment (table) | Endodontics + analgesia |
| Draft drug recommendation | Paracetamol 500 mg q6h PRN |
| Expected engine output | Proposal passes clean; **branch = drug-no-conflict** |
| Assertions | **0 warnings** — sulfa allergy recorded but must NOT trigger (R-09); Paracetamol safe with metformin (draft); obesity does not by itself warn |

---

## 5. Handoff Notes

- **Backend (issue #8):** every profile field above maps to a patient-record column — `age_years`, `weight_kg`, `allergies[]`, `current_medications[]` (name + dose + frequency + indication), `conditions[]`. Missing any of these = test cases can't run Day 4.
- **Backend (issue #13/#17):** assertions in §4 are the contract for the Day 3 contraindication test cases (issue #15); keep rule IDs (R-01…R-09) stable across both documents.
- **Team Lead (issue #11):** when the dentist meeting happens, re-validate §1, §2, and the `Draft treatment` column of every profile. Do not renumber profiles — only correct values, so downstream test cases keep their IDs.
- **Allergies encoding:** lowercase generic drug/class names (`penicillin`, `sulfa`) — no free text.
- **Demo note:** P-003, P-004, P-005 give three *flavors* of conflict (allergy, interaction, age/weight); P-006 is the deliberate negative control proving the engine does not over-warn.
