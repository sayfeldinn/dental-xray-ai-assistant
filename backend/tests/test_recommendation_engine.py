"""Recommendation engine: the three demo branches plus the safety substitutions."""

from app.domain.recommendation import ClinicalContext
from app.services.contraindication import PatientSafetyProfile
from app.services.contraindication.catalog import WEIGHT_NEEDED_DOSAGE
from app.services.recommendation import RecommendationEngine
from tests.conftest import TODAY, make_finding, make_patient

engine = RecommendationEngine()
INFECTION = ClinicalContext(active_infection=True)
PAIN = ClinicalContext(pain=True)


def plan(findings, context=ClinicalContext(), **patient):
    profile = PatientSafetyProfile.from_patient(make_patient(**patient), TODAY)
    return engine.recommend_for_scan(findings, profile, context)


def drugs(proposal):
    return {rx.drug_name: rx for rx in proposal.prescriptions}


def alert_codes(proposal):
    return {a.code for a in proposal.alerts}


# --- The three demo branches (docs/TEAM_WORKFLOW.md §4) -------------------------------

def test_branch1_caries_gets_restorative_referral_and_no_drugs():
    (p,) = plan([make_finding("Caries", "16")])
    assert p.category == "restorative" and p.prescriptions == [] and p.alerts == []


def test_branch2_periapical_infection_gets_amoxicillin_500_q8h():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION)
    rx = drugs(p)["Amoxicillin"]
    assert (rx.dosage, rx.frequency, rx.status) == ("500 mg", "every 8 hours", "clear")
    assert p.category == "endodontic"


def test_branch3_penicillin_allergy_switches_to_clindamycin_with_visible_warning():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, allergies=["penicillin"])
    assert list(drugs(p)) == ["Clindamycin"]
    rx = p.prescriptions[0]
    assert rx.status == "warning" and rx.dosage == "300 mg"
    notice = next(w for w in rx.warnings if w.rule_id == "R-18")
    assert "Amoxicillin" in notice.message and "penicillin" in notice.message


# --- Stewardship and scope ------------------------------------------------------------

def test_no_antibiotic_is_proposed_unless_the_dentist_reports_infection():
    (p,) = plan([make_finding("Periapical Lesion")])
    assert p.prescriptions == []


def test_caries_never_gets_antibiotics_even_when_infection_is_reported():
    (p,) = plan([make_finding("Caries")], INFECTION)
    assert p.prescriptions == [] and "ANTIBIOTIC_NOT_INDICATED" in alert_codes(p)


def test_dentist_corrected_label_drives_the_recommendation():
    finding = make_finding("Caries", review_status="modified", confirmed_disease="Periapical Lesion")
    (p,) = plan([finding], INFECTION)
    assert p.category == "endodontic" and "Amoxicillin" in drugs(p)
    assert "corrected" in p.justification


def test_unmapped_finding_degrades_to_monitoring_with_an_alert():
    (p,) = plan([make_finding("Fracture")])
    assert p.category == "monitoring" and "UNMAPPED_FINDING" in alert_codes(p)


# --- Cardiac prophylaxis (AHA 2021) ------------------------------------------------------

def test_cardiac_patient_gets_single_dose_amoxicillin_before_impacted_extraction():
    (p,) = plan([make_finding("Impacted", "38")], conditions=["prosthetic_cardiac_valve"])
    rx = drugs(p)["Amoxicillin"]
    assert rx.indication_type == "pre_procedure_prophylaxis" and rx.dosage == "2 g"
    assert "30-60 min" in rx.frequency


def test_penicillin_allergic_cardiac_patient_gets_azithromycin_never_clindamycin():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION,
                allergies=["penicillin"], conditions=["cardiac_endocarditis_risk"])
    by_indication = {rx.indication_type: rx.drug_name for rx in p.prescriptions}
    assert by_indication == {"pre_procedure_prophylaxis": "Azithromycin", "active_infection": "Clindamycin"}
    assert "OVERLAPPING_ANTIBIOTICS" in alert_codes(p)


def test_no_prophylaxis_drug_when_penicillin_and_macrolide_allergic():
    (p,) = plan([make_finding("Impacted")], allergies=["penicillin", "azithromycin"],
                conditions=["infective_endocarditis_risk"])
    assert p.prescriptions == [] and "NO_SAFE_DRUG" in alert_codes(p)


def test_caries_does_not_trigger_prophylaxis():
    (p,) = plan([make_finding("Caries")], conditions=["cardiac_risk"])
    assert p.prescriptions == []


# --- Analgesia ----------------------------------------------------------------------------

def test_ibuprofen_is_first_line_for_a_healthy_adult():
    (p,) = plan([make_finding("Caries")], PAIN)
    assert drugs(p)["Ibuprofen"].dosage == "400 mg"


def test_warfarin_patient_is_switched_to_paracetamol_with_notice():
    (p,) = plan([make_finding("Impacted")], PAIN, age=72, medications=["warfarin"])
    assert list(drugs(p)) == ["Paracetamol"]
    assert "Ibuprofen" in next(w for w in p.prescriptions[0].warnings if w.rule_id == "R-18").message


def test_no_analgesic_when_both_are_contraindicated():
    (p,) = plan([make_finding("Caries")], PAIN, medications=["warfarin"], conditions=["hepatic_impairment"])
    assert p.prescriptions == [] and "NO_SAFE_DRUG" in alert_codes(p)


# --- Pediatric ----------------------------------------------------------------------------

def test_child_gets_weight_based_ibuprofen_floored_to_5_mg():
    (p,) = plan([make_finding("Caries")], PAIN, age=6, weight_kg=18.3)
    rx = drugs(p)["Ibuprofen"]
    assert rx.dosage == "180 mg" and rx.status == "clear"


def test_child_amoxicillin_uses_the_aapd_weight_based_dose():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, age=8, weight_kg=25)
    rx = drugs(p)["Amoxicillin"]   # 10 mg/kg/dose = 30 mg/kg/day, within AAPD 20-40
    assert (rx.dosage, rx.frequency, rx.status) == ("250 mg", "every 8 hours", "clear")


def test_child_without_weight_gets_no_invented_dose():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, age=8, weight_kg=None)
    rx = drugs(p)["Amoxicillin"]
    assert rx.dosage == WEIGHT_NEEDED_DOSAGE and rx.status == "warning"


def test_child_azithromycin_course_has_loading_and_maintenance_doses():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, age=8, weight_kg=25,
                allergies=["penicillin", "clindamycin"])
    rx = drugs(p)["Azithromycin"]   # 10 mg/kg day 1 then 5 mg/kg (AAPD)
    assert rx.dosage == "250 mg day 1, then 125 mg daily" and rx.indication_type == "active_infection"


# --- Scan level -----------------------------------------------------------------------------

def test_systemic_drug_is_proposed_once_per_scan():
    first, second = plan([make_finding("Periapical Lesion", "36"), make_finding("Periapical Lesion", "46")], INFECTION)
    assert "Amoxicillin" in drugs(first)
    assert second.prescriptions == [] and "DUPLICATE_DRUG_SKIPPED" in alert_codes(second)
    assert "36" in second.alerts[0].message


def test_engine_is_deterministic():
    findings = [make_finding("Impacted", "38"), make_finding("Deep Caries", "26")]
    first = plan(findings, INFECTION, allergies=["penicillin"])
    second = plan(findings, INFECTION, allergies=["penicillin"])
    assert first == second


def test_overlap_alert_only_where_both_antibiotics_are_actually_proposed():
    first, second = plan([make_finding("Periapical Lesion", "36"), make_finding("Impacted", "38")], INFECTION,
                         conditions=["cardiac_risk"])
    assert "OVERLAPPING_ANTIBIOTICS" in alert_codes(first)
    assert "OVERLAPPING_ANTIBIOTICS" not in alert_codes(second)


def test_azithromycin_is_the_third_infection_option_when_clindamycin_is_also_excluded():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, allergies=["penicillin", "lincosamide"])
    rx = drugs(p)["Azithromycin"]
    assert rx.dosage == "500 mg day 1, then 250 mg daily" and rx.status == "warning"


def test_cephalexin_is_never_auto_proposed():
    # Penicillin-allergy reaction severity is not in the record, so cephalexin stays a dentist choice (R-26).
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION, allergies=["penicillin"])
    assert "Cephalexin" not in drugs(p)


def test_infection_course_carries_reevaluation_guidance():
    (p,) = plan([make_finding("Periapical Lesion")], INFECTION)
    text = drugs(p)["Amoxicillin"].instructions
    assert "3 days" in text and "24 hours" in text
