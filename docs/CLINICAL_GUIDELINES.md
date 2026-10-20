# DentalAI — Clinical Guidelines & Recommendation Rules

> [!WARNING]
> **Pending Dentist Validation Disclosure:**
> All rules, dosages, and contraindications in this document are compiled from published dental-pharmacology and cardiology guidelines (ADA, AHA, AAPD; full citations in §6). Every UI screen and API payload must display a visible `"Pending Dentist Validation"` tag.
>
> **Evidence status:** no clinician has reviewed this content (no partner clinic is available yet). Every value is therefore either **SOURCED** (taken from a cited published guideline) or **PROJECT** (a conservative project decision, marked as such). A clinician sign-off remains a recommended step before any real-world use; the product stays assistive either way.

---

## 1. Finding-to-Treatment Mapping Logic

| Detected & Confirmed Pathology | Clinical Strategy | Requires Systemic Antibiotics? |
| :--- | :--- | :--- |
| **Caries (Enamel / Dentin)** | Restorative referral (filling/sealant) | **NO** (Strictly restorative) |
| **Deep Caries (Pulpal Proximity)**| Indirect pulp capping / pulpotomy / endodontic eval | Only if acute systemic swelling / severe symptoms |
| **Periapical Lesion** | Root canal treatment (RCT) or extraction referral | Only if active infection / abscess with systemic symptoms |
| **Impacted Tooth** | Oral surgery evaluation / extraction or monitoring | Prophylaxis only if surgery planned in at-risk cardiac patient |

---

## 2. Pharmacological Dosing Reference (ADA / AHA / AAPD)

Adult regimens follow the ADA 2019 guideline and its 2024 chairside guide; pediatric regimens and daily limits follow the AAPD Reference Manual (*Useful Medications*); prophylaxis follows AHA 2021. Pediatric = under 12 years (AAPD split); pediatric doses never exceed adult doses.

### 2.1 Active Dental Infection (Treatment — Multi-Day Regimen)

**When antibiotics are indicated (ADA 2019):** pulp necrosis with a localized acute apical abscess, or with systemic involvement. **Not indicated:** symptomatic irreversible pulpitis, or pulp necrosis with symptomatic apical periodontitis, when definitive treatment is available (pulpotomy, pulpectomy, root canal, incision for drainage). AAPD: not indicated for a localized pediatric infection without fever or facial swelling. Antibiotics never replace source control; re-evaluate within 3 days and stop 24 hours after symptoms resolve.

| Drug | Adult (ADA) | Pediatric (AAPD) | Notes |
| :--- | :--- | :--- | :--- |
| **Amoxicillin** | 500 mg 3×/day, 3–7 days | 20–40 mg/kg/day ÷ q8h, max 500 mg/dose (**project proposes 10 mg/kg/dose = 30 mg/kg/day**) | **First-line.** Penicillin V 500 mg 4×/day is the other ADA first-line option (not in the catalog). |
| **Clindamycin** | 300 mg 4×/day, 3–7 days (max 1800 mg/day) | 20–30 mg/kg/day ÷ q8h, max 450 mg/dose (**proposes 8 mg/kg/dose**) | ADA alternative for penicillin allergy with anaphylaxis, angioedema or hives. *C. difficile* risk. |
| **Azithromycin** | 500 mg day 1, then 250 mg daily × 4 more days | 10–12 mg/kg day 1 (max 500 mg), then 5–6 mg/kg daily (**proposes 10, then 5 mg/kg**) | Same ADA alternative group as clindamycin. QT caution (R-08). |
| **Cephalexin** | 500 mg 4×/day, 3–7 days (max 4000 mg/day) | 25–50 mg/kg/day ÷ q6–12h, max 2000 mg/day (**proposes 10 mg/kg q6h**) | ADA option for penicillin allergy **without** a history of anaphylaxis, angioedema or hives. **Never auto-proposed** (the record does not capture reaction severity); dentist choice only (R-26). |
| **Metronidazole** | 500 mg 3×/day, 7 days | *No AAPD recommendation for odontogenic infection* | **Add-on only if first-line therapy fails** (ADA). Strict alcohol avoidance during use and 48 h after. |

### 2.2 Pre-Procedure Prophylaxis (AHA 2021 — Single Dose, 30–60 min before)

Indicated **strictly for the highest-risk cardiac patients** (prosthetic valve or valve-repair material, previous infective endocarditis, certain congenital heart disease, cardiac transplant with valvulopathy) undergoing procedures that manipulate gingival tissue, the periapical region of teeth, or perforate oral mucosa.

| Drug | Adult | Pediatric (AAPD, citing AHA) | Note |
| :--- | :--- | :--- | :--- |
| **Amoxicillin** | 2 g | 50 mg/kg (max 2 g) | First choice. |
| **Cephalexin** | 2 g | 50 mg/kg (max 2 g) | Penicillin-allergic **without** anaphylaxis/angioedema/hives. Never auto-proposed. |
| **Azithromycin** | 500 mg | 15 mg/kg (max 500 mg) | Penicillin-allergic fallback (also clarithromycin; doxycycline for patients over 8 years: not in the catalog). |
| ~~**Clindamycin**~~ | **EXCLUDED** | **EXCLUDED** | **AHA 2021:** removed from prophylaxis because of severe/fatal adverse reactions (*C. difficile*). |

### 2.3 Pain Management (Analgesics)

| Drug | Adult | Pediatric (AAPD, under 12) | Contraindications & warnings |
| :--- | :--- | :--- | :--- |
| **Ibuprofen** | 200–400 mg q4–6h, or 600–800 mg q6–8h; **max 3200 mg/day**. Project proposes 400 mg q4–6h. ADA: 400–600 mg ibuprofen **plus** 1000 mg acetaminophen may be most effective for dental pain. | 4–10 mg/kg/dose q6–8h, max single dose 600 mg; 40 mg/kg/day (**proposes 10 mg/kg, capped at 400 mg**) | First-line analgesic. Contraindicated: active peptic ulcer/GI bleeding, renal impairment, asthma (project: any asthma), NSAID/aspirin allergy, anticoagulants. Caution: age ≥ 65 (Beers 2023), NSAID + ACE inhibitor/ARB + diuretic. |
| **Paracetamol** | 325–650 mg q4–6h or 1000 mg 3–4×/day; **label max 4000 mg/day**. Project proposes 500 mg q4–6h with a **project limit of 3000 mg/day** (above it = warning; above 4000 = contraindicated). | 10–15 mg/kg/dose q4–6h; max 75 mg/kg/day, never above 4000 mg/day (**proposes 10 mg/kg**) | Alternative when NSAIDs are contraindicated. Contraindicated: severe hepatic impairment, chronic alcohol abuse. |

---

## 3. FDI Two-Digit Tooth Notation System

The AI model output utilizes the international FDI World Dental Federation notation:
- **Quadrant Digit (Tens place):**
  - `1`: Upper Right (Patient's Maxillary Right)
  - `2`: Upper Left (Patient's Maxillary Left)
  - `3`: Lower Left (Patient's Mandibular Left)
  - `4`: Lower Right (Patient's Mandibular Right)
- **Tooth Digit (Units place, 1 to 8 from midline):**
  - `1`: Central incisor
  - `2`: Lateral incisor
  - `3`: Canine
  - `4`: First premolar
  - `5`: Second premolar
  - `6`: First molar
  - `7`: Second molar
  - `8`: Third molar (Wisdom tooth)

**Examples:**
- `Tooth_8` in Quadrant 4 = FDI **48** (Lower Right Wisdom Tooth).
- `Tooth_7` in Quadrant 2 = FDI **27** (Upper Left Second Molar).
- `Tooth_6` in Quadrant 3 = FDI **36** (Lower Left First Molar).


---

## 4. Rule Register (implemented in `backend/app/services/contraindication/`)

Rule IDs are a **stable contract**: tests, API warnings (`rule_id`), and the QA docs reference them. Never renumber; only append. Severity maps to the prescription's `contraindication_status` (worst wins; `info` never changes it). Every API warning also carries its `source` citation.

| ID | Trigger | Severity | Evidence |
| :--- | :--- | :--- | :--- |
| R-01 | Penicillin-class allergy → Amoxicillin | contraindicated | SOURCED (ADA 2019 pathway) |
| R-02 | Ibuprofen + anticoagulant (warfarin, DOACs, heparin) | contraindicated | SOURCED (Beers 2023: avoid NSAID + anticoagulant) |
| R-03 | Ibuprofen + age ≥ 65 | warning | SOURCED (Beers 2023) |
| R-04 | Single pediatric dose above the weight limit (AAPD per-dose mg/kg and absolute caps) | contraindicated | SOURCED (AAPD; AHA prophylaxis doses) |
| R-05 | *Reserved* (Dexamethasone + diabetes): Dexamethasone is not in the catalog | — | — |
| R-06 | Paracetamol + hepatic impairment | contraindicated | SOURCED (AAPD hepatotoxicity caution) |
| R-07 | Metronidazole + alcohol use | warning | SOURCED (AAPD) |
| R-08 | Azithromycin + QT-prolonging drug or QT-risk condition (long QT, arrhythmia, bradycardia, heart block, conduction defect, heart failure) | warning | SOURCED (FDA 2013 safety communication; AAPD conduction-defect caution). Antiarrhythmics are FDA-named; haloperidol/citalopram/methadone are label-based. |
| R-09 | Sulfa allergy: **must not warn** (negative control, unit-tested) | — | QA profile P-006 |
| R-10 | Ibuprofen + active GI ulcer / bleeding | contraindicated | SOURCED (NSAID labelling) |
| R-11 | Ibuprofen + renal impairment | contraindicated | SOURCED (NSAID labelling) |
| R-12 | Ibuprofen + asthma (any asthma: the record cannot show aspirin sensitivity) | contraindicated | PROJECT (conservative; paracetamol is the fallback) |
| R-13 | Allergy to the class of any other catalog drug | contraindicated | general |
| R-14 | Clindamycin for cardiac prophylaxis | contraindicated | SOURCED (AHA 2021) |
| R-15 | Paracetamol + chronic alcohol use | contraindicated | SOURCED (AAPD) |
| R-16 | Pediatric patient and no published pediatric regimen → dentist must set a weight-based dose | warning | SOURCED (AAPD has none, e.g. metronidazole) |
| R-17 | Pediatric patient with no recorded weight | warning | general |
| R-18 | First-line drug excluded for this patient; a substitute was proposed | warning | `ARCHITECTURE.md` §4.2 |
| R-19 | Clindamycin: *C. difficile* counselling | info | SOURCED (AAPD) |
| R-20 | Metronidazole: alcohol-avoidance counselling | info | SOURCED (AAPD) |
| R-21 | Drug not a guideline option for this indication | warning | general |
| R-22 | Drug not in the catalog: no automated check ran | warning | general |
| R-23 | Daily dose (dose × doses/day) above a published maximum (contraindicated) or the project limit (warning). Maxima: ibuprofen 3200 mg, paracetamol 4000 mg (project 3000), clindamycin 1800 mg, cephalexin 4000 mg, azithromycin course 500 mg/day; pediatric mg/kg/day limits | contraindicated / warning | SOURCED (AAPD, ADA); 3000 mg paracetamol = PROJECT |
| R-24 | Metronidazole + warfarin (can sharply raise INR) | warning | SOURCED (Hersh & Moore; NPS; Dental Update) |
| R-25 | Ibuprofen + ACE inhibitor/ARB **and** diuretic ("triple whammy", acute kidney injury) | warning | SOURCED (bpac NZ; Pharmacy Times) |
| R-26 | Cephalexin with a penicillin allergy on record: unsafe if the reaction was anaphylaxis, angioedema or hives | warning | SOURCED (ADA 2019; AAPD) |

## 5. Engine Behaviour & Decisions

1. **Source of truth:** this document wins over `docs/qa/*` (early drafts written before any research). Where a QA draft value survived it is cited above; where it did not, the change is listed here.
2. **Penicillin-allergic patients (ADA 2019):** active infection → **Clindamycin**, then **Azithromycin** if clindamycin is also excluded (ADA lists both for patients with anaphylaxis/angioedema/hives). Cardiac prophylaxis → **Azithromycin** (never clindamycin, R-14). **Cephalexin** is ADA's choice for penicillin allergy *without* those reactions; the patient record doesn't capture reaction severity, so the engine treats every penicillin allergy as potentially severe and leaves cephalexin to the dentist, with R-26.
3. **Paracetamol:** proposed at 500 mg q4–6h; **3000 mg/day** is the project limit (warning above), 4000 mg/day the published maximum (contraindicated above).
4. **Antibiotic stewardship (ADA/AAPD):** the X-ray cannot show infection or pain, so the dentist supplies a `clinical_context` (`active_infection`, `pain`). `active_infection` means a localized acute apical abscess or systemic involvement, **not pain alone**. Without it: no antibiotics and no analgesics (except cardiac prophylaxis, which depends on the patient record). Plain **Caries never gets antibiotics**, even if infection is reported (alert `ANTIBIOTIC_NOT_INDICATED`). Infection courses carry the ADA follow-up instructions (re-evaluate within 3 days, stop 24 h after resolution, definitive treatment not delayed).
   - Demo branches 2 and 3 (`TEAM_WORKFLOW.md` §4) are run with `active_infection: true`.
5. **Cardiac prophylaxis** is proposed for `Periapical Lesion` and `Impacted` findings when the patient has an at-risk cardiac condition (procedures that manipulate periapical tissue). `Caries` / `Deep Caries` do not trigger it.
6. **Substitution:** for each indication the first non-contraindicated drug in `catalog.PREFERENCE` is proposed (infection: Amoxicillin → Clindamycin → Azithromycin; prophylaxis: Amoxicillin → Azithromycin; pain: Ibuprofen → Paracetamol). A substitute always carries an R-18 warning. If none is safe, no drug is proposed and a `NO_SAFE_DRUG` alert tells the dentist.
7. **One systemic drug per indication per scan:** later teeth get a `DUPLICATE_DRUG_SKIPPED` alert instead of a repeat prescription.
8. **Metronidazole** is an add-on after first-line failure (ADA): never auto-proposed, but checked when the dentist selects it. **Cephalexin** likewise.
9. **Pediatric (< 12 years):** adult doses are never used. Where AAPD/AHA give a weight-based regimen it is computed (floored to 5 mg, capped per dose) and single-dose and daily limits are enforced; otherwise the dosage reads *"Weight-based - dentist to specify"* (R-16). A missing weight gives R-17.
10. **Daily limits** need the frequency text (`every 6 hours`, `twice daily`, …); the most frequent reading is used, so the check errs on the safe side. Unparseable frequencies skip only the daily check.
11. **Dexamethasone** appears in the QA drafts but not in the cited guidelines, so it is not in the catalog (R-22 if a dentist selects it).
12. **Free-text matching:** patient allergies/medications/conditions are matched against alias tables by whole tokens (`'alcohol_chronic'`, `'Penicillin (rash)'`, `'prosthetic_cardiac_valve'` all work). A term outside `catalog.py`'s alias tables is **not understood**: add an alias, never loosen the matcher.
13. **Dentist decisions are re-checked** against the *current* patient record at decision time. `warning` needs `acknowledge_warnings`; `contraindicated` needs a written `override_reason`. Decisions are final (409 afterwards). Dentist-authored treatments are stored `confirmed`; dentist-authored prescriptions are safety-checked and still need a decision.
14. **Not modelled:** pregnancy/lactation, renal dose adjustment, drug allergies other than the listed classes, liver/renal severity grades (the record has no such fields). These are documented gaps, not silent passes.

## 6. Sources & Verification Notes

Read in full (primary text extracted and checked against the catalog):
- **ADA** — Lockhart PB et al., *Evidence-based clinical practice guideline on antibiotic use for the urgent management of pulpal- and periapical-related dental pain and intraoral swelling*, JADA 2019;150(11):906–921; chairside guide (ADA, updated 2024): https://www.ferris.edu/pharmacy/michigan-antibiotic-resistance-reduction-coalition/Documents/ADA_Chairside_Guide_Antibiotics_TNA.pdf
- **AAPD** — *Useful Medications for Oral Conditions*, Reference Manual of Pediatric Dentistry (pp. 644–648): https://www.aapd.org/globalassets/media/policies_guidelines/r_usefulmeds.pdf ; and *Use of Antibiotic Therapy for Pediatric Dental Patients*: https://www.aapd.org/globalassets/media/policies_guidelines/bp_antibiotictherapy26.pdf

Confirmed from search summaries only (primary full text was not retrievable; re-check when a clinician reviews):
- **AHA 2021** — Wilson WR et al., *Prevention of viridans group streptococcal infective endocarditis*, Circulation 2021;143(20):e963–e978 (https://pubmed.ncbi.nlm.nih.gov/33853363/). Clindamycin exclusion confirmed; prophylaxis doses (2 g / 500 mg / 50 and 15 mg/kg) are cross-checked through the AAPD table that cites it.
- **FDA** Drug Safety Communication on azithromycin and fatal heart rhythms (2013): https://www.fda.gov/drugs/drug-safety-and-availability/fda-drug-safety-communication-azithromycin-zithromax-or-zmax-and-risk-potentially-fatal-heart
- **AGS Beers Criteria 2023** (NSAIDs in adults 65+, especially with anticoagulants/steroids).
- Metronidazole–warfarin: Hersh & Moore, *Compendium of Continuing Education in Dentistry*; NPS MedicineWise; *Dental Update* ("Warfarin and drug interactions: prescribing vigilance"). NSAID triple whammy: bpac NZ (https://bpac.org.nz/2018/docs/triple-whammy.pdf); Pharmacy Times (2013).

Project decisions (not from a guideline): 3000 mg/day paracetamol limit, "any asthma contraindicates ibuprofen", proposing the middle of AAPD dose ranges, floor-to-5 mg rounding.

