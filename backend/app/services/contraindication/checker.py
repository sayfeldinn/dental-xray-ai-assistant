"""
DentalAI - Contraindication Checker
Deterministic safety rules (Step 4/5): one drug + one patient -> structured warnings.
Rule IDs (R-xx) are a stable register documented in docs/CLINICAL_GUIDELINES.md §4;
never renumber them, only append. Every warning carries the citation of its rule.
"""

import re
from typing import Callable, List, Optional

from app.domain.prescription import SafetyCheckResult, SafetyWarning, Severity
from .catalog import (
    AAPD, ADA_2019, AHA_2021, CATALOG, DENTIST_DOSE_DOSAGE, PROJECT, DrugProfile, find_drug,
)
from .profile import PatientSafetyProfile

GUIDE = "docs/CLINICAL_GUIDELINES.md"
FDA_AZITHROMYCIN = "FDA Drug Safety Communication on azithromycin and fatal heart rhythms (2013)"
BEERS_2023 = "AGS Beers Criteria 2023 (NSAIDs in adults 65+)"
WARFARIN_DENTAL = "Hersh & Moore, Compendium of Continuing Education in Dentistry; NPS MedicineWise; Dental Update"
TRIPLE_WHAMMY = "bpac NZ 'triple whammy' (NSAID + ACE inhibitor/ARB + diuretic) and Pharmacy Times"

_DOSE = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|g)\b", re.IGNORECASE)
_EVERY_HOURS = re.compile(r"every\s+(\d+(?:\.\d+)?)(?:\s*-\s*\d+(?:\.\d+)?)?\s*hours?")
_TIMES_DAILY = re.compile(r"(\d+)\s*(?:times|x)\s*(?:per\s+|a\s+)?(?:day|daily)")
_WORD_COUNTS = (("four times", 4), ("three times", 3), ("twice", 2), ("once", 1), ("single dose", 1))


def parse_dose_mg(dosage: Optional[str]) -> Optional[float]:
    """First dose in a free-text dosage, in mg ('2 g' -> 2000, '500-1000 mg' -> 1000). None if absent."""
    match = _DOSE.search(dosage or "")
    if not match:
        return None
    value = float(match.group(1))
    return value * 1000 if match.group(2).lower() == "g" else value


def doses_per_day(frequency: Optional[str]) -> Optional[float]:
    """
    Maximum doses in 24 h implied by a frequency text ('every 4-6 hours' -> 6, 'twice daily' -> 2).
    The most frequent reading is used so daily-limit checks err on the safe side. None if unparseable.
    """
    text = (frequency or "").lower()
    match = _EVERY_HOURS.search(text)
    if match and float(match.group(1)) > 0:
        return 24 / float(match.group(1))
    match = _TIMES_DAILY.search(text)
    if match:
        return float(match.group(1))
    return next((n for word, n in _WORD_COUNTS if word in text), None)


def _warn(drug: str, rule_id: str, code: str, severity: Severity, message: str, source: str) -> SafetyWarning:
    return SafetyWarning(code=code, rule_id=rule_id, severity=severity, drug=drug, message=message, source=source)


Rule = Callable[[DrugProfile, str, PatientSafetyProfile, Optional[float], Optional[float]], List[SafetyWarning]]


# --- Generic rules (apply to every drug) -------------------------------------
# Signature: (drug, indication, patient, dose_mg, per_day)

def _indication_rule(drug, indication, patient, dose_mg, per_day):
    # Clindamycin + prophylaxis is reported as the stronger R-14 instead.
    if indication in drug.regimens or (drug.name == "Clindamycin" and indication == "pre_procedure_prophylaxis"):
        return []
    allowed = ", ".join(drug.regimens)
    return [_warn(drug.name, "R-21", "INDICATION_MISMATCH", "warning",
                  f"{drug.name} is not a guideline option for {indication} (guideline indications: {allowed}).", GUIDE)]


def _allergy_rule(drug, indication, patient, dose_mg, per_day):
    if not drug.allergy_class or not patient.has_allergy(drug.allergy_class):
        return []
    allergen = ", ".join(patient.allergen_terms(drug.allergy_class))
    rule_id = "R-01" if drug.allergy_class == "penicillin" else "R-13"
    return [_warn(drug.name, rule_id, f"ALLERGY_{drug.allergy_class.upper()}", "contraindicated",
                  f"Patient allergy '{allergen}' contraindicates {drug.name} ({drug.allergy_class} class).", GUIDE)]


def _pediatric_rule(drug, indication, patient, dose_mg, per_day):
    regimen = drug.regimens.get(indication)
    if not patient.is_pediatric or regimen is None:
        return []
    peds = regimen.pediatric
    if peds is None:
        return [_warn(drug.name, "R-16", "PEDIATRIC_DOSE_NOT_VALIDATED", "warning",
                      f"No published pediatric regimen for {drug.name} in this indication; patient is "
                      f"{patient.age_years}. Dentist must set a weight-based dose.", AAPD)]
    if patient.weight_kg is None:
        return [_warn(drug.name, "R-17", "WEIGHT_REQUIRED", "warning",
                      f"Patient is {patient.age_years}: weight is required to dose {drug.name}.", AAPD)]
    if dose_mg is None:
        return []

    weight = patient.weight_kg
    single_limit = min((peds.limit_mg_per_kg or peds.mg_per_kg) * weight, peds.limit_single_mg or peds.max_single_mg)
    if dose_mg > single_limit + 1e-6:
        return [_warn(drug.name, "R-04", "DOSE_EXCEEDS_WEIGHT_LIMIT", "contraindicated",
                      f"{dose_mg:g} mg exceeds the weight-based limit of {single_limit:g} mg per dose "
                      f"(patient {weight:g} kg, age {patient.age_years}).", peds.source)]

    daily_caps = []
    if peds.daily_limit_mg_per_kg:
        daily_caps.append(peds.daily_limit_mg_per_kg * weight)
    if peds.daily_limit_mg:
        daily_caps.append(peds.daily_limit_mg)
    if per_day and daily_caps and dose_mg * per_day > min(daily_caps) + 1e-6:
        return [_warn(drug.name, "R-23", "DAILY_DOSE_EXCEEDED", "contraindicated",
                      f"{dose_mg * per_day:g} mg/day exceeds the pediatric daily limit of {min(daily_caps):g} mg "
                      f"(patient {weight:g} kg).", peds.source)]
    return []


def _adult_daily_rule(drug, indication, patient, dose_mg, per_day):
    regimen = drug.regimens.get(indication)
    if patient.is_pediatric or regimen is None or dose_mg is None or per_day is None:
        return []
    daily = dose_mg * per_day
    if regimen.max_daily_mg and daily > regimen.max_daily_mg + 1e-6:
        return [_warn(drug.name, "R-23", "DAILY_DOSE_EXCEEDED", "contraindicated",
                      f"{daily:g} mg/day exceeds the maximum daily dose of {regimen.max_daily_mg:g} mg.", regimen.source)]
    if regimen.advised_daily_mg and daily > regimen.advised_daily_mg + 1e-6:
        return [_warn(drug.name, "R-23", "DAILY_DOSE_ABOVE_PROJECT_LIMIT", "warning",
                      f"{daily:g} mg/day is above the project limit of {regimen.advised_daily_mg:g} mg/day "
                      f"(label maximum {regimen.max_daily_mg:g} mg).", PROJECT)]
    return []


# --- Drug-specific rules -----------------------------------------------------

def _clindamycin_rules(drug, indication, patient, dose_mg, per_day):
    warnings = [_warn(drug.name, "R-19", "CDIFF_RISK", "info",
                      "Risk of C. difficile colitis: stop and contact the clinic if watery diarrhea occurs.", AAPD)]
    if indication == "pre_procedure_prophylaxis":
        warnings.append(_warn(drug.name, "R-14", "CLINDAMYCIN_EXCLUDED_PROPHYLAXIS", "contraindicated",
                              "Clindamycin is no longer recommended for endocarditis prophylaxis.", AHA_2021))
    return warnings


def _azithromycin_rules(drug, indication, patient, dose_mg, per_day):
    qt_drugs = patient.medication_terms("qt_prolonging")
    qt_conditions = patient.condition_terms("qt_risk")
    if not (qt_drugs or qt_conditions):
        return []
    reasons = ", ".join(qt_drugs + qt_conditions)
    return [_warn(drug.name, "R-08", "QT_RISK", "warning",
                  f"Azithromycin can prolong the QT interval; patient has QT risk factors ({reasons}). "
                  "Consider the risk of arrhythmia or consult the patient's cardiologist.", FDA_AZITHROMYCIN)]


def _metronidazole_rules(drug, indication, patient, dose_mg, per_day):
    warnings = []
    if patient.has_alcohol_use():
        warnings.append(_warn(drug.name, "R-07", "ALCOHOL_INTERACTION", "warning",
                              "Patient has alcohol use recorded: strict alcohol avoidance during and 48 hours after metronidazole.",
                              AAPD))
    else:
        warnings.append(_warn(drug.name, "R-20", "ALCOHOL_COUNSELLING", "info",
                              "Counsel the patient: no alcohol during use and for 48 hours afterwards.", AAPD))
    warfarin = patient.medication_terms("warfarin")
    if warfarin:
        warnings.append(_warn(drug.name, "R-24", "METRONIDAZOLE_WARFARIN", "warning",
                              f"Metronidazole can greatly raise the INR in patients on warfarin ({', '.join(warfarin)}): "
                              "consult the physician managing anticoagulation and monitor INR.", WARFARIN_DENTAL))
    return warnings


def _cephalexin_rules(drug, indication, patient, dose_mg, per_day):
    if not patient.has_allergy("penicillin"):
        return []
    allergen = ", ".join(patient.allergen_terms("penicillin"))
    return [_warn(drug.name, "R-26", "CEPHALOSPORIN_PENICILLIN_ALLERGY", "warning",
                  f"Patient is allergic to '{allergen}': cephalexin must NOT be used if the reaction was anaphylaxis, "
                  "angioedema or hives. Confirm the reaction history first.", f"{ADA_2019}; {AAPD}")]


def _ibuprofen_rules(drug, indication, patient, dose_mg, per_day):
    warnings = []
    anticoagulants = patient.medication_terms("anticoagulant")
    if anticoagulants:
        warnings.append(_warn(drug.name, "R-02", "NSAID_ANTICOAGULANT", "contraindicated",
                              f"Ibuprofen with anticoagulant therapy ({', '.join(anticoagulants)}) raises bleeding risk. "
                              "Paracetamol is the usual alternative.", BEERS_2023))
    for condition, rule_id, text in (
        ("gi_ulcer", "R-10", "active peptic ulcer / GI bleeding"),
        ("renal_impairment", "R-11", "renal impairment"),
        ("asthma", "R-12", "asthma (aspirin-sensitive asthma is a labelled contraindication; any asthma is excluded here "
                           "because the record does not capture aspirin sensitivity)"),
    ):
        if patient.has_condition(condition):
            warnings.append(_warn(drug.name, rule_id, f"NSAID_{condition.upper()}", "contraindicated",
                                  f"Ibuprofen is contraindicated with {text}.", GUIDE if rule_id != "R-12" else PROJECT))
    if patient.is_elderly:
        warnings.append(_warn(drug.name, "R-03", "NSAID_ELDERLY", "warning",
                              f"Age {patient.age_years}: NSAIDs carry GI, renal and bleeding risk in older adults; "
                              "use the lowest effective dose for the shortest time.", BEERS_2023))
    if patient.medication_terms("ace_arb") and patient.medication_terms("diuretic"):
        names = ", ".join(patient.medication_terms("ace_arb") + patient.medication_terms("diuretic"))
        warnings.append(_warn(drug.name, "R-25", "NSAID_TRIPLE_WHAMMY", "warning",
                              f"NSAID with an ACE inhibitor/ARB plus a diuretic ({names}) raises the risk of acute kidney "
                              "injury; avoid if possible.", TRIPLE_WHAMMY))
    return warnings


def _paracetamol_rules(drug, indication, patient, dose_mg, per_day):
    warnings = []
    if patient.has_condition("hepatic_impairment"):
        warnings.append(_warn(drug.name, "R-06", "PARACETAMOL_HEPATIC", "contraindicated",
                              "Paracetamol is contraindicated with severe hepatic impairment.", AAPD))
    if patient.has_alcohol_use():
        warnings.append(_warn(drug.name, "R-15", "PARACETAMOL_ALCOHOL", "contraindicated",
                              "Paracetamol is contraindicated with chronic alcohol abuse.", AAPD))
    return warnings


_GENERIC_RULES: List[Rule] = [_indication_rule, _allergy_rule, _pediatric_rule, _adult_daily_rule]
_DRUG_RULES = {
    "Cephalexin": _cephalexin_rules,
    "Clindamycin": _clindamycin_rules,
    "Azithromycin": _azithromycin_rules,
    "Metronidazole": _metronidazole_rules,
    "Ibuprofen": _ibuprofen_rules,
    "Paracetamol": _paracetamol_rules,
}
assert set(_DRUG_RULES) <= set(CATALOG), "drug rule registered for a drug missing from the catalog"


class ContraindicationChecker:
    """Stateless; safe to share across requests."""

    def check(
        self,
        drug_name: str,
        indication_type: str,
        patient: PatientSafetyProfile,
        dosage: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> SafetyCheckResult:
        drug = find_drug(drug_name)
        if drug is None:
            warnings = [_warn(drug_name, "R-22", "UNKNOWN_DRUG", "warning",
                              f"'{drug_name}' is not in the drug catalog: no automated safety check was performed.",
                              GUIDE)]
        else:
            dose_mg = None if dosage == DENTIST_DOSE_DOSAGE else parse_dose_mg(dosage)
            per_day = doses_per_day(frequency)
            rules = _GENERIC_RULES + ([_DRUG_RULES[drug.name]] if drug.name in _DRUG_RULES else [])
            warnings = [w for rule in rules for w in rule(drug, indication_type, patient, dose_mg, per_day)]

        return SafetyCheckResult(
            drug_name=drug.name if drug else drug_name,
            indication_type=indication_type,
            status=self.status_of(warnings),
            warnings=warnings,
        )

    @staticmethod
    def status_of(warnings: List[SafetyWarning]) -> str:
        """Worst severity wins; 'info' notes never change the status."""
        severities = {w.severity for w in warnings}
        if "contraindicated" in severities:
            return "contraindicated"
        return "warning" if "warning" in severities else "clear"
