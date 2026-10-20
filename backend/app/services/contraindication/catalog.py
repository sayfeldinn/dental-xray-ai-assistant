"""
DentalAI - Drug Safety Knowledge Base
Hand-curated, deterministic data (no LLM, no external DDI API: RxNav is retired).
Every regimen and limit cites a published source (constants below); where the project chose
a more conservative value than the source, the entry says so. Keep docs/CLINICAL_GUIDELINES.md
in sync with any change here.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

PEDIATRIC_AGE_YEARS = 12   # AAPD tables split "children < 12" from "> 12 / adolescents"
ELDERLY_AGE_YEARS = 65     # AGS Beers Criteria

# --- Sources ------------------------------------------------------------------
AHA_2021 = "AHA 2021 scientific statement, Circulation 143:e963"
ADA_2019 = "ADA 2019 antibiotic guideline (JADA 150:906) and 2024 chairside guide"
AAPD = "AAPD Reference Manual, Useful Medications"
PROJECT = "Project conservative limit (docs/CLINICAL_GUIDELINES.md)"

# --- Vocabulary: canonical key -> aliases found in patient records -----------

ALLERGY_CLASSES: Dict[str, Tuple[str, ...]] = {
    "penicillin": ("penicillin", "amoxicillin", "ampicillin", "beta lactam", "betalactam"),
    "cephalosporin": ("cephalosporin", "cephalexin", "cefazolin", "ceftriaxone", "cefuroxime"),
    "nsaid": ("nsaid", "ibuprofen", "aspirin", "naproxen", "diclofenac"),
    "paracetamol": ("paracetamol", "acetaminophen"),
    "macrolide": ("macrolide", "azithromycin", "erythromycin", "clarithromycin"),
    "lincosamide": ("lincosamide", "clindamycin", "lincomycin"),
    "nitroimidazole": ("nitroimidazole", "metronidazole"),
}

CONDITION_CLASSES: Dict[str, Tuple[str, ...]] = {
    "cardiac_prophylaxis_risk": (
        "cardiac risk", "cardiac endocarditis risk", "endocarditis", "prosthetic cardiac valve",
        "prosthetic heart valve", "prosthetic valve", "cyanotic congenital heart disease",
    ),
    "gi_ulcer": ("gi ulcer", "peptic ulcer", "gastric ulcer", "gi bleeding"),
    "renal_impairment": ("renal impairment", "renal failure", "kidney disease", "ckd"),
    "hepatic_impairment": ("hepatic impairment", "liver disease", "liver failure", "cirrhosis"),
    "asthma": ("asthma",),
    "alcohol_use": ("alcohol",),   # 'alcohol_chronic' and 'chronic_alcohol' both appear in seed data
    "qt_risk": (   # FDA azithromycin safety communication (2013) + AAPD caution on conduction defects
        "long qt", "qt prolongation", "torsades", "arrhythmia", "bradycardia", "heart block",
        "cardiac conduction", "conduction defect", "heart failure",
    ),
}

MEDICATION_CLASSES: Dict[str, Tuple[str, ...]] = {
    "anticoagulant": (
        "warfarin", "coumadin", "heparin", "apixaban", "rivaroxaban",
        "dabigatran", "edoxaban", "anticoagulant",
    ),
    "qt_prolonging": (   # FDA names class IA/III antiarrhythmics; the others are label-based
        "amiodarone", "sotalol", "quinidine", "procainamide", "dofetilide",
        "haloperidol", "citalopram", "methadone",
    ),
    "warfarin": ("warfarin", "coumadin"),
    "ace_arb": (   # "triple whammy" components
        "lisinopril", "enalapril", "ramipril", "captopril", "perindopril", "benazepril", "ace inhibitor",
        "losartan", "valsartan", "candesartan", "irbesartan", "telmisartan", "olmesartan", "arb",
    ),
    "diuretic": (
        "furosemide", "hydrochlorothiazide", "hctz", "indapamide", "chlorthalidone",
        "spironolactone", "bumetanide", "diuretic",
    ),
}

# --- Drugs -------------------------------------------------------------------


@dataclass(frozen=True)
class WeightBasedDose:
    """Pediatric regimen computed from weight (patients under PEDIATRIC_AGE_YEARS)."""

    mg_per_kg: float                      # per-dose amount the engine proposes
    max_single_mg: float                  # cap on a proposed single dose
    frequency: str
    duration: str
    source: str
    limit_mg_per_kg: Optional[float] = None    # highest acceptable per-dose mg/kg (default: mg_per_kg)
    limit_single_mg: Optional[float] = None    # highest acceptable single dose (default: max_single_mg)
    daily_limit_mg_per_kg: Optional[float] = None
    daily_limit_mg: Optional[float] = None     # absolute daily cap regardless of weight
    follow_on_mg_per_kg: Optional[float] = None  # azithromycin: day 1 loading, then this daily


@dataclass(frozen=True)
class Regimen:
    """Adult regimen for one indication, plus limits and the optional pediatric rule."""

    dosage: str
    frequency: str
    duration: str
    instructions: str
    source: str
    max_daily_mg: Optional[float] = None       # published ceiling: above it is contraindicated
    advised_daily_mg: Optional[float] = None   # project ceiling: above it is a warning
    pediatric: Optional[WeightBasedDose] = None


@dataclass(frozen=True)
class DrugProfile:
    name: str
    allergy_class: Optional[str]        # allergy class that blocks this drug
    regimens: Dict[str, Regimen]        # indication_type -> regimen; keys = allowed indications


_REEVALUATE = " Re-evaluate within 3 days; stop 24 hours after symptoms resolve. Definitive dental treatment must not be delayed."
_PROPHYLAXIS_TIMING = "single dose 30-60 min pre-procedure"

CATALOG: Dict[str, DrugProfile] = {
    "Amoxicillin": DrugProfile("Amoxicillin", "penicillin", {
        "active_infection": Regimen(
            "500 mg", "every 8 hours", "3-7 days",
            "First-line antibiotic for pulp necrosis with abscess or systemic involvement." + _REEVALUATE, ADA_2019,
            pediatric=WeightBasedDose(
                10, 500, "every 8 hours", "3-7 days", AAPD,
                limit_mg_per_kg=40 / 3, daily_limit_mg_per_kg=40),   # AAPD 20-40 mg/kg/day, max 500 mg/dose; 30 proposed
        ),
        "pre_procedure_prophylaxis": Regimen(
            "2 g", _PROPHYLAXIS_TIMING, "single dose",
            "Single oral dose 30-60 minutes before the procedure.", AHA_2021,
            pediatric=WeightBasedDose(50, 2000, _PROPHYLAXIS_TIMING, "single dose", AAPD),
        ),
    }),
    "Cephalexin": DrugProfile("Cephalexin", "cephalosporin", {
        # Not auto-proposed: only suitable without a history of anaphylaxis, angioedema or hives
        # with penicillin, which patient records do not capture (see rule R-26).
        "active_infection": Regimen(
            "500 mg", "every 6 hours", "3-7 days",
            "Penicillin-allergic patients WITHOUT a history of anaphylaxis, angioedema or hives." + _REEVALUATE,
            ADA_2019, max_daily_mg=4000,
            pediatric=WeightBasedDose(
                10, 500, "every 6 hours", "3-7 days", AAPD,
                limit_mg_per_kg=12.5, daily_limit_mg_per_kg=50, daily_limit_mg=2000),
        ),
        "pre_procedure_prophylaxis": Regimen(
            "2 g", _PROPHYLAXIS_TIMING, "single dose",
            "Only without a history of anaphylaxis, angioedema or hives with penicillin.", AHA_2021,
            pediatric=WeightBasedDose(50, 2000, _PROPHYLAXIS_TIMING, "single dose", AAPD),
        ),
    }),
    "Clindamycin": DrugProfile("Clindamycin", "lincosamide", {
        "active_infection": Regimen(
            "300 mg", "every 6 hours", "3-7 days",
            "Alternative for penicillin allergy. Stop and call the clinic on watery diarrhea." + _REEVALUATE,
            ADA_2019, max_daily_mg=1800,
            pediatric=WeightBasedDose(
                8, 450, "every 8 hours", "3-7 days", AAPD,
                limit_mg_per_kg=10, daily_limit_mg_per_kg=30),   # AAPD 20-30 mg/kg/day q8h, max 450 mg/dose
        ),
    }),
    "Azithromycin": DrugProfile("Azithromycin", "macrolide", {
        "active_infection": Regimen(
            "500 mg day 1, then 250 mg daily", "once daily", "5 days",
            "Alternative for penicillin allergy (500 mg loading dose, then 250 mg for 4 more days)." + _REEVALUATE,
            ADA_2019, max_daily_mg=500,
            pediatric=WeightBasedDose(
                10, 500, "once daily", "5 days", AAPD,
                limit_mg_per_kg=12, daily_limit_mg=500, follow_on_mg_per_kg=5),   # AAPD 10-12 then 5-6 mg/kg
        ),
        "pre_procedure_prophylaxis": Regimen(
            "500 mg", _PROPHYLAXIS_TIMING, "single dose",
            "Penicillin-allergic cardiac prophylaxis.", AHA_2021,
            pediatric=WeightBasedDose(15, 500, _PROPHYLAXIS_TIMING, "single dose", AAPD),
        ),
    }),
    "Metronidazole": DrugProfile("Metronidazole", "nitroimidazole", {
        # AAPD gives no pediatric recommendation for odontogenic infections.
        "active_infection": Regimen(
            "500 mg", "every 8 hours", "7 days",
            "Adjunct to first-line therapy only if it fails. No alcohol during use and for 48 hours after.",
            ADA_2019),
    }),
    "Ibuprofen": DrugProfile("Ibuprofen", "nsaid", {
        "pain_management": Regimen(
            "400 mg", "every 4-6 hours as needed", "as needed (short course)",
            "First-line analgesic. Take with food. Do not exceed 3200 mg/24 hours.", AAPD,
            max_daily_mg=3200,
            pediatric=WeightBasedDose(
                10, 400, "every 6-8 hours as needed", "as needed (short course)", AAPD,
                limit_single_mg=600, daily_limit_mg_per_kg=40),   # AAPD 4-10 mg/kg/dose, max single 600 mg
        ),
    }),
    "Paracetamol": DrugProfile("Paracetamol", "paracetamol", {
        "pain_management": Regimen(
            "500 mg", "every 4-6 hours as needed", "as needed; max 3000 mg/day",
            "Alternative when NSAIDs are contraindicated. Up to 1000 mg per dose; "
            "project limit 3000 mg/24 hours (label maximum 4000 mg).", AAPD,
            max_daily_mg=4000, advised_daily_mg=3000,
            pediatric=WeightBasedDose(
                10, 500, "every 4-6 hours as needed", "as needed", AAPD,
                limit_mg_per_kg=15, limit_single_mg=1000, daily_limit_mg_per_kg=75, daily_limit_mg=4000),
        ),
    }),
}

# Order of preference per indication; the first non-contraindicated drug is proposed.
# Clindamycin is deliberately absent from prophylaxis (R-14). Cephalexin is never auto-proposed.
PREFERENCE: Dict[str, Tuple[str, ...]] = {
    "active_infection": ("Amoxicillin", "Clindamycin", "Azithromycin"),
    "pre_procedure_prophylaxis": ("Amoxicillin", "Azithromycin"),
    "pain_management": ("Ibuprofen", "Paracetamol"),
}

WEIGHT_NEEDED_DOSAGE = "Weight-based - weight required"
DENTIST_DOSE_DOSAGE = "Weight-based - dentist to specify"


def find_drug(name: str) -> Optional[DrugProfile]:
    """Case-insensitive lookup."""
    return next((d for d in CATALOG.values() if d.name.lower() == name.strip().lower()), None)
