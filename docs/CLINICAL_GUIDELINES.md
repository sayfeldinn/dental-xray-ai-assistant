# DentalAI — Clinical Guidelines & Recommendation Rules

> [!WARNING]
> **Pending Dentist Validation Disclosure:**
> All rules, dosages, and contraindications in this document are compiled from published dental-pharmacology and cardiology guidelines (ADA, AHA, AAPD). Every UI screen and API payload must display a visible `"Pending Dentist Validation"` tag.

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

### 2.1 Active Dental Infection (Treatment — Multi-Day Regimen)

Antibiotics are indicated only when acute infection presents with systemic symptoms, diffuse intraoral swelling, or when definitive operative care (pulpotomy, drainage, extraction) must be delayed.

| Drug | Standard Adult Dosing | First-Line Alternative / Notes |
| :--- | :--- | :--- |
| **Amoxicillin** | 500 mg orally every 8 hours for 3–7 days | **First-line choice**. Contraindicated in Penicillin allergy. |
| **Clindamycin** | 300 mg orally every 6 hours (four times daily) for 3–7 days | **First-line alternative if Penicillin allergic**. *Warning:* Risk of *C. difficile* colitis; instruct patient to stop if watery diarrhea occurs. |
| **Metronidazole**| 500 mg orally every 8 hours for 7 days | **Adjunctive only** (added to Amoxicillin if refractory to first-line). *Contraindication:* Strict alcohol avoidance during use and for 48 hours post-treatment. |

---

### 2.2 Pre-Procedure Prophylaxis (AHA Guideline — Single-Dose)

Indicated **strictly for specific at-risk cardiac patients** (e.g., prosthetic heart valves, previous infective endocarditis, unrepaired cyanotic congenital heart disease) undergoing procedures that involve manipulation of gingival tissue or periapical region of teeth.

| Drug | Adult Prophylaxis Dosing | Pediatric Prophylaxis Dosing | Critical Clinical Note |
| :--- | :--- | :--- | :--- |
| **Amoxicillin** | 2 g orally as a single dose 30–60 min before procedure | 50 mg/kg orally single dose (max 2 g) | Standard first-line regimen for cardiac prophylaxis. |
| **Azithromycin** (or Doxycycline)| 500 mg orally single dose 30–60 min before procedure | 15 mg/kg orally single dose | Used **only if penicillin-allergic**. |
| ~~**Clindamycin**~~ | **STRICTLY EXCLUDED** | **STRICTLY EXCLUDED** | **AHA 2021 Update:** Clindamycin was explicitly removed from endocarditis prophylaxis recommendations due to severe/fatal adverse reactions (*C. diff*). |

---

### 2.3 Pain Management (Analgesics)

| Drug | Adult Dosing | Contraindications & Warnings |
| :--- | :--- | :--- |
| **Ibuprofen** | 400 mg orally every 4–6 hours as needed | **First-line analgesic**. Contraindicated in: Active peptic ulcer/GI bleeding, severe renal impairment, concurrent anticoagulants (e.g. Warfarin), aspirin-sensitive asthma. |
| **Paracetamol** | 500–1000 mg orally every 4–6 hours (max 3000 mg/day) | **Alternative when NSAIDs contraindicated**. Contraindicated in: Severe hepatic impairment, chronic alcohol abuse. |

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

