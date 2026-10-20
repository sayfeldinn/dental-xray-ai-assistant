"""
Contraindication rules. Cases TC-xx / P-00x come from docs/qa/ (early drafts);
expected values follow the cited sources in docs/CLINICAL_GUIDELINES.md.
"""

from datetime import date

import pytest

from app.services.contraindication import (
    ContraindicationChecker, PatientSafetyProfile, age_on, doses_per_day, parse_dose_mg,
)
from app.services.recommendation import RecommendationEngine
from app.services.contraindication.catalog import ALLERGY_CLASSES, CATALOG, DENTIST_DOSE_DOSAGE
from tests.conftest import TODAY, make_patient

checker = ContraindicationChecker()


def profile(**kwargs) -> PatientSafetyProfile:
    return PatientSafetyProfile.from_patient(make_patient(**kwargs), TODAY)


def rules(result):
    return {w.rule_id for w in result.warnings}


# --- Allergy -------------------------------------------------------------------

def test_tc01_penicillin_allergy_blocks_amoxicillin_and_names_allergen():
    result = checker.check("Amoxicillin", "active_infection", profile(age=19, allergies=["penicillin"]), "500 mg")
    assert result.status == "contraindicated"
    assert "R-01" in rules(result)
    assert "penicillin" in next(w for w in result.warnings if w.rule_id == "R-01").message


def test_tc02_penicillin_allergy_does_not_block_azithromycin():
    result = checker.check("Azithromycin", "pre_procedure_prophylaxis", profile(age=19, allergies=["penicillin"]), "500 mg")
    assert result.status == "clear"


def test_tc03_penicillin_allergy_does_not_block_metronidazole():
    result = checker.check("Metronidazole", "active_infection", profile(allergies=["penicillin"]), "500 mg")
    assert result.status == "clear"   # only the R-20 counselling note (info)


def test_r09_sulfa_allergy_triggers_nothing_across_the_catalog():
    patient = profile(age=45, weight_kg=90, allergies=["sulfa"], medications=["metformin"])
    for name, drug in CATALOG.items():
        for indication in drug.regimens:
            result = checker.check(name, indication, patient, drug.regimens[indication].dosage)
            assert result.status == "clear", (name, indication, result.warnings)


def test_aspirin_allergy_blocks_ibuprofen_via_nsaid_class():
    result = checker.check("Ibuprofen", "pain_management", profile(allergies=["aspirin"]), "400 mg")
    assert result.status == "contraindicated" and "R-13" in rules(result)


def test_every_allergy_class_used_by_the_catalog_is_defined():
    assert {d.allergy_class for d in CATALOG.values()} <= set(ALLERGY_CLASSES)


# --- Drug-drug / condition -------------------------------------------------------

def test_tc04_ibuprofen_with_warfarin_is_contraindicated_and_names_warfarin():
    result = checker.check("Ibuprofen", "pain_management",
                           profile(age=72, medications=["Warfarin 5 mg daily"]), "400 mg")
    assert result.status == "contraindicated"
    assert {"R-02", "R-03"} <= rules(result)
    assert "Warfarin" in next(w for w in result.warnings if w.rule_id == "R-02").message


def test_tc05_paracetamol_is_clear_for_the_warfarin_patient():
    assert checker.check("Paracetamol", "pain_management",
                         profile(age=72, medications=["warfarin"]), "500 mg").status == "clear"


def test_tc06_azithromycin_with_qt_drug_warns():
    result = checker.check("Azithromycin", "pre_procedure_prophylaxis", profile(medications=["amiodarone"]), "500 mg")
    assert result.status == "warning" and "R-08" in rules(result)


@pytest.mark.parametrize("condition,rule", [("gi_ulcer", "R-10"), ("renal_impairment", "R-11"), ("asthma", "R-12")])
def test_ibuprofen_condition_contraindications(condition, rule):
    result = checker.check("Ibuprofen", "pain_management", profile(conditions=[condition]), "400 mg")
    assert result.status == "contraindicated" and rule in rules(result)


def test_adrenal_condition_is_not_mistaken_for_renal_impairment():
    assert checker.check("Ibuprofen", "pain_management", profile(conditions=["adrenal_insufficiency"]), "400 mg").status == "clear"


def test_paracetamol_hepatic_and_alcohol_seed_vocabulary():
    # Seed data stores 'alcohol_chronic' under medications and 'hepatic_impairment' under conditions.
    patient = profile(medications=["alcohol_chronic"], conditions=["hepatic_impairment"])
    result = checker.check("Paracetamol", "pain_management", patient, "500 mg")
    assert result.status == "contraindicated" and {"R-06", "R-15"} <= rules(result)


def test_metronidazole_alcohol_warns_otherwise_only_counsels():
    assert rules(checker.check("Metronidazole", "active_infection", profile(medications=["chronic_alcohol"]), "500 mg")) == {"R-07"}
    clean = checker.check("Metronidazole", "active_infection", profile(), "500 mg")
    assert clean.status == "clear" and rules(clean) == {"R-20"}


def test_clindamycin_is_always_excluded_from_cardiac_prophylaxis():
    result = checker.check("Clindamycin", "pre_procedure_prophylaxis", profile(), "600 mg")
    assert result.status == "contraindicated" and "R-14" in rules(result)
    assert "R-21" not in rules(result)   # reported once, as the stronger R-14


# --- Age / weight / dose --------------------------------------------------------

def test_p005_adult_ibuprofen_dose_is_forbidden_for_a_child_and_weight_based_dose_passes():
    child = profile(age=6, weight_kg=18)
    forbidden = checker.check("Ibuprofen", "pain_management", child, "400 mg")
    assert forbidden.status == "contraindicated" and "R-04" in rules(forbidden)
    assert "180 mg" in forbidden.warnings[0].message
    assert checker.check("Ibuprofen", "pain_management", child, "180 mg").status == "clear"


def test_child_without_weight_needs_weight():
    assert "R-17" in rules(checker.check("Ibuprofen", "pain_management", profile(age=6, weight_kg=None), "180 mg"))


def test_pediatric_drug_without_published_regimen_requires_dentist_dose():
    # AAPD gives no pediatric metronidazole recommendation for odontogenic infections.
    result = checker.check("Metronidazole", "active_infection", profile(age=8, weight_kg=25), DENTIST_DOSE_DOSAGE)
    assert result.status == "warning" and "R-16" in rules(result)


def test_pediatric_prophylaxis_dose_cap():
    child = profile(age=10, weight_kg=60)   # 50 mg/kg = 3 g, capped at 2 g
    assert checker.check("Amoxicillin", "pre_procedure_prophylaxis", child, "2 g").status == "clear"
    assert checker.check("Amoxicillin", "pre_procedure_prophylaxis", child, "2.5 g").status == "contraindicated"


def test_elderly_nsaid_caution_cites_beers():
    result = checker.check("Ibuprofen", "pain_management", profile(age=65), "400 mg")
    assert rules(result) == {"R-03"} and "Beers" in result.warnings[0].source


# --- Catalog / indication --------------------------------------------------------

def test_unknown_drug_is_flagged_not_silently_passed():
    result = checker.check("Dexamethasone", "pain_management", profile(), "4 mg")
    assert result.status == "warning" and "R-22" in rules(result)


def test_indication_mismatch_warns():
    result = checker.check("Amoxicillin", "pain_management", profile(), "500 mg")
    assert result.status == "warning" and "R-21" in rules(result)


def test_drug_lookup_is_case_insensitive_and_canonicalises_name():
    assert checker.check("  ibuprofen ", "pain_management", profile(), "400 mg").drug_name == "Ibuprofen"


# --- Helpers ---------------------------------------------------------------------

@pytest.mark.parametrize("text,mg", [("500 mg", 500), ("2 g", 2000), ("500-1000 mg", 1000), ("2.5g", 2500),
                                     ("Weight-based - dentist to specify", None), (None, None)])
def test_parse_dose_mg(text, mg):
    assert parse_dose_mg(text) == mg


def test_age_respects_birthday():
    assert age_on(date(2000, 12, 31), date(2026, 10, 20)) == 25
    assert age_on(date(2000, 10, 20), date(2026, 10, 20)) == 26


# --- Daily limits (AAPD / ADA) -----------------------------------------------------------

@pytest.mark.parametrize("text,per_day", [
    ("every 4-6 hours as needed", 6), ("every 8 hours", 3), ("every 6 hours", 4), ("twice daily", 2),
    ("3 times daily", 3), ("once daily", 1), ("single dose 30-60 min pre-procedure", 1), ("sometimes", None), (None, None),
])
def test_doses_per_day(text, per_day):
    assert doses_per_day(text) == per_day


def test_adult_ibuprofen_over_3200_mg_a_day_is_contraindicated():
    result = checker.check("Ibuprofen", "pain_management", profile(), "800 mg", "every 4 hours")
    assert result.status == "contraindicated" and "R-23" in rules(result)
    assert checker.check("Ibuprofen", "pain_management", profile(), "800 mg", "every 6 hours").status == "clear"


def test_paracetamol_has_a_project_limit_below_the_label_maximum():
    adult = profile()
    assert checker.check("Paracetamol", "pain_management", adult, "500 mg", "every 4-6 hours as needed").status == "clear"
    soft = checker.check("Paracetamol", "pain_management", adult, "650 mg", "every 4-6 hours as needed")
    assert soft.status == "warning" and soft.warnings[0].code == "DAILY_DOSE_ABOVE_PROJECT_LIMIT"
    hard = checker.check("Paracetamol", "pain_management", adult, "1000 mg", "every 4 hours")
    assert hard.status == "contraindicated"


def test_clindamycin_over_1800_mg_a_day_is_contraindicated():
    assert checker.check("Clindamycin", "active_infection", profile(), "450 mg", "every 6 hours").status == "clear"
    assert checker.check("Clindamycin", "active_infection", profile(), "600 mg", "every 6 hours").status == "contraindicated"


def test_pediatric_daily_limit_uses_weight():
    child = profile(age=6, weight_kg=18)   # ibuprofen 40 mg/kg/day = 720 mg
    assert checker.check("Ibuprofen", "pain_management", child, "180 mg", "every 6 hours").status == "clear"
    over = checker.check("Ibuprofen", "pain_management", child, "180 mg", "every 4 hours")
    assert over.status == "contraindicated" and "R-23" in rules(over)


# --- Interactions added from the published literature ----------------------------------------

def test_r24_metronidazole_with_warfarin_warns_to_monitor_inr():
    result = checker.check("Metronidazole", "active_infection", profile(medications=["Warfarin"]), "500 mg", "every 8 hours")
    assert result.status == "warning" and "R-24" in rules(result)


def test_r25_nsaid_triple_whammy_needs_ace_arb_and_diuretic():
    both = profile(medications=["lisinopril", "furosemide"])
    assert "R-25" in rules(checker.check("Ibuprofen", "pain_management", both, "400 mg"))
    one = profile(medications=["lisinopril"])
    assert "R-25" not in rules(checker.check("Ibuprofen", "pain_management", one, "400 mg"))


def test_r26_cephalexin_with_penicillin_allergy_asks_about_reaction_history():
    result = checker.check("Cephalexin", "active_infection", profile(allergies=["penicillin"]), "500 mg", "every 6 hours")
    assert result.status == "warning" and "R-26" in rules(result)
    assert checker.check("Cephalexin", "active_infection", profile(), "500 mg", "every 6 hours").status == "clear"


@pytest.mark.parametrize("kwargs", [{"conditions": ["long_qt_syndrome"]}, {"conditions": ["Cardiac conduction defect"]}])
def test_r08_azithromycin_with_qt_risk_condition_warns(kwargs):
    assert "R-08" in rules(checker.check("Azithromycin", "pre_procedure_prophylaxis", profile(**kwargs), "500 mg"))


# --- Catalog self-consistency ---------------------------------------------------------------------

def test_every_catalog_regimen_cites_a_source():
    for drug in CATALOG.values():
        for indication, regimen in drug.regimens.items():
            assert regimen.source, (drug.name, indication)
            if regimen.pediatric:
                assert regimen.pediatric.source, (drug.name, indication)


def test_default_regimens_never_trip_the_checker_for_a_healthy_patient():
    """What the engine would propose must itself pass the safety rules (adult and 25 kg child)."""
    for patient in (profile(age=35, weight_kg=78), profile(age=8, weight_kg=25)):
        for name, drug in CATALOG.items():
            for indication, regimen in drug.regimens.items():
                if patient.is_pediatric and regimen.pediatric is None:
                    continue
                dosage, frequency, _, _ = RecommendationEngine._regimen(name, indication, patient)
                result = checker.check(name, indication, patient, dosage, frequency)
                assert result.status != "contraindicated", (name, indication, patient.age_years, dosage, result.warnings)
