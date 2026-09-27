"""Execution of ``docs/qa/contraindication-test-cases.md`` (v1) against the
recommendation engine.

Every case carries the ID it has in that document (TC-01 ... TC-17,
NC-01 ... NC-06) so the two stay traceable. Cases are split when only part of
the expected result is currently satisfiable -- for example TC-04a asserts the
warning that *does* fire while TC-04b asserts the substitution that does not
exist -- so a passing clause keeps guarding against regression instead of
hiding inside a whole-case xfail.

xfail policy (``xfail_strict = true`` in pytest.ini)
-----------------------------------------------------
Each gap test names issue #33 in its reason. Because the run is strict, a test
whose gap has been fixed starts passing and **turns CI red**, forcing the marker
to be deleted. Gaps therefore cannot be silently forgotten.

Status: ``UNVALIDATED`` -- the expected results derive from draft rules
(``synthetic-patient-profiles.md`` section 2) written without a dentist. Re-run
after issue #11 lands; do not treat a green run as clinical correctness.
"""
from __future__ import annotations

import pytest

from app.schemas.scan import (
    BoundingBox,
    Finding,
    FindingSeverityEnum,
    FindingTypeEnum,
)

GAP = "#33"  # engine contract gaps -- every xfail reason references it


def _finding(finding_type: FindingTypeEnum, severity: FindingSeverityEnum) -> Finding:
    return Finding(
        type=finding_type,
        severity=severity,
        confidence=0.9,
        bounding_box=BoundingBox(x=0.0, y=0.0, width=10.0, height=10.0),
    )


# --------------------------------------------------------------------------
# 1. Allergy  (R-01)
# --------------------------------------------------------------------------


def test_tc01_amoxicillin_warns_on_penicillin_allergy(engine_check):
    """TC-01 -- a penicillin-allergic patient must not get amoxicillin silently."""
    result = engine_check("P-003", "Amoxicillin")
    assert len(result.warnings) >= 1, result.warnings


def test_tc01_warning_names_the_allergen(engine_check):
    """TC-01 -- the reason for the warning must be legible to the dentist."""
    result = engine_check("P-003", "Amoxicillin")
    assert "penicillin" in result.warning_text.lower(), result.warning_text


def test_tc02_azithromycin_must_not_cross_react(engine_check):
    """TC-02 -- azithromycin is the penicillin-allergy alternative; it must pass."""
    result = engine_check("P-003", "Azithromycin")
    assert result.warnings == [], result.warnings


def test_tc03_metronidazole_must_not_cross_react(engine_check):
    """TC-03 -- penicillin allergy is unrelated to nitroimidazoles."""
    result = engine_check("P-003", "Metronidazole")
    assert result.warnings == [], result.warnings


# --------------------------------------------------------------------------
# 2. Drug-drug interaction  (R-02, R-08)
# --------------------------------------------------------------------------


def test_tc04_ibuprofen_warns_on_warfarin(engine_check):
    """TC-04 -- NSAID + warfarin must warn, and the detail must name warfarin."""
    result = engine_check("P-004", "Ibuprofen")
    assert len(result.warnings) >= 1, result.warnings
    assert "warfarin" in result.warning_text.lower(), result.warning_text


def test_tc04_offers_paracetamol_as_alternative(engine_check):
    """TC-04 -- flagging without an alternative leaves the dentist to solve it."""
    result = engine_check("P-004", "Ibuprofen")
    assert "paracetamol" in result.warning_text.lower(), result.warning_text


def test_tc05_paracetamol_cleared_after_substitution(engine_check):
    """TC-05 -- proves the engine is not just flagging P-004 forever."""
    result = engine_check("P-004", "Paracetamol")
    assert result.warnings == [], result.warnings


def test_tc06_azithromycin_cites_qt_co_medication(engine_check):
    """TC-06 -- R-08. Input is QA-supplied: no profile carries a QT drug (S6)."""
    result = engine_check(
        None,
        "Azithromycin",
        overrides={"current_medications": ["amiodarone"]},
    )
    assert len(result.warnings) >= 1, result.warnings
    assert "amiodarone" in result.warning_text.lower(), result.warning_text


# --------------------------------------------------------------------------
# 3. Age  (R-03)
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap A: check_prescription_safety() has no age parameter -- "
        "P-004 age_years=72 is dropped, so R-03 never fires. The only warning "
        "returned is R-02's warfarin interaction, which says nothing about age."
    ),
)
def test_tc07_age_factor_shown_in_warning(engine_check):
    """TC-07 -- the age factor (72 / >=65) must be visible in the warning."""
    result = engine_check("P-004", "Ibuprofen")
    text = result.warning_text.lower()
    assert "age" in text and ("72" in text or "65" in text), result.warnings


def test_tc08_paracetamol_clean_for_elderly(engine_check):
    """TC-08 -- R-03 is NSAID-specific."""
    result = engine_check("P-004", "Paracetamol")
    assert result.warnings == [], result.warnings


def test_tc09_ibuprofen_clean_below_age_threshold(engine_check):
    """TC-09 -- age 35 is under the >=65 threshold; keys on age, not the drug."""
    result = engine_check("P-002", "Ibuprofen")
    assert result.warnings == [], result.warnings


# --------------------------------------------------------------------------
# 4. Weight / pediatric dose  (R-04)
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap A: weight_kg does not exist in the patient schema and the "
        "engine takes neither age nor weight, so R-04 cannot fire for P-005 "
        "(18 kg). Dropped: age_years=6, weight_kg=18."
    ),
)
def test_tc10_adult_dose_blocked_for_pediatric_patient(engine_check):
    """TC-10 -- an adult 400 mg dose must not be accepted as-is for 18 kg."""
    result = engine_check("P-005", "Ibuprofen")
    assert len(result.warnings) >= 1, result.warnings


def test_tc11_weight_based_dose_accepted(engine_check):
    """TC-11 -- the corrected dose must pass.

    Passes only because the engine has no dose concept at all (gap H), so this
    guards nothing about dosing -- see TC-13 for the case that would.
    """
    result = engine_check("P-005", "Ibuprofen")
    assert result.warnings == [], result.warnings


def test_tc12_age_and_weight_both_out_of_range_clears(engine_check):
    """TC-12 -- flipping both age and weight out of paediatric range must clear.

    Also vacuous today: with no age/weight input there is nothing left to warn
    about once the profile is otherwise clean.
    """
    result = engine_check(
        "P-005",
        "Ibuprofen",
        overrides={"age_years": 14, "weight_kg": 60},
    )
    assert result.warnings == [], result.warnings


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap A: weight_kg has no parameter. P-005 stays 18 kg after the "
        "age override, but R-04 cannot see it. This is the case that separates "
        "an engine evaluating age and weight independently from one that "
        "short-circuits after the first match."
    ),
)
def test_tc13_weight_check_independent_of_age(engine_check):
    """TC-13 -- highest-value case in the QA document (see S4)."""
    result = engine_check("P-005", "Ibuprofen", overrides={"age_years": 14})
    assert len(result.warnings) >= 1, result.warnings


# --------------------------------------------------------------------------
# 5. Condition & lifestyle  (R-05, R-06, R-07)
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap B: Dexamethasone is missing from DRUGS_DATABASE, so R-05 has "
        "no entry. Gap F would bite next: P-006's condition is free text "
        "('Type 2 diabetes, well controlled...') and would not match a token."
    ),
)
def test_tc14_dexamethasone_glycemic_warning(engine_check):
    """TC-14 -- R-05. The warning must name the diabetes context."""
    result = engine_check("P-006", "Dexamethasone")
    text = result.warning_text.lower()
    assert result.warnings, result.warnings
    assert "glycemic" in text or "diabetes" in text, result.warnings


def test_tc15_paracetamol_clean_for_diabetic(engine_check):
    """TC-15 -- paracetamol does not affect glycaemic control."""
    result = engine_check("P-006", "Paracetamol")
    assert result.warnings == [], result.warnings


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap F: conditions are matched by exact list membership against "
        "the token 'severe_liver_disease', so the profile-style value "
        "'liver disease' never matches. Gap H compounds it -- no dose-cap logic "
        "exists to state a numeric ceiling."
    ),
)
def test_tc16_liver_disease_states_numeric_dose_cap(engine_check):
    """TC-16 -- R-06. Override input: no profile carries a hepatic condition (S6)."""
    result = engine_check(
        None,
        "Paracetamol",
        overrides={"conditions": ["liver disease"]},
    )
    assert len(result.warnings) >= 1, result.warnings
    assert any(ch.isdigit() for ch in result.warning_text), result.warning_text


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap A: profiles S5 handoff defines no lifestyle column and "
        "check_prescription_safety() has no lifestyle parameter -- R-07 has no "
        "data path anywhere in the stack. Dropped: lifestyle='alcohol use'."
    ),
)
def test_tc17_avoids_alcohol_with_metronidazole(engine_check):
    """TC-17 -- R-07. Override input: every profile is a non-drinker (S6)."""
    result = engine_check(
        None,
        "Metronidazole",
        overrides={"lifestyle": "alcohol use"},
    )
    assert len(result.warnings) >= 1, result.warnings


# --------------------------------------------------------------------------
# 7. Negative controls  -- zero-warning cases, catch an over-warn engine
# --------------------------------------------------------------------------


def test_nc01_paracetamol_clean_for_p006(engine_check):
    """NC-01 -- sulfa allergy irrelevant, metformin clean, obesity alone silent.

    Counted toward the >=3 strict zero-warning minimum.
    """
    result = engine_check("P-006", "Paracetamol")
    assert result.warnings == [], result.warnings


def test_nc02_no_drug_branch_yields_no_prescriptions(engine):
    """NC-02 -- the no-drug demo branch: a finding needing no systemic drug.

    Uses the lowest-severity cavity mapping, which carries ``drugs: []`` and so
    is the one path in FINDING_TO_TREATMENT_MAP that legitimately yields zero
    prescriptions. P-001's own draft finding is covered by NC-02b.
    """
    finding = _finding(FindingTypeEnum.CAVITY, FindingSeverityEnum.LOW)
    recommendation = engine.recommend_treatment(finding)

    assert recommendation is not None
    assert recommendation.prescriptions == [], recommendation.prescriptions
    # dentist confirmation field must start empty
    assert finding.confirmed is False


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap I (overlaps #28): FindingTypeEnum has no gingivitis or "
        "periodontal member, so P-001's draft finding 'Generalized mild "
        "gingivitis, calculus deposits' cannot be represented at all."
    ),
)
def test_nc02_p001_finding_is_representable():
    """NC-02 -- P-001's draft finding must map to a FindingTypeEnum member."""
    draft_finding = "generalized mild gingivitis, calculus deposits"
    enum_values = {member.value for member in FindingTypeEnum}
    assert any(
        token in enum_values
        for token in ("gingivitis", "periodontal", "gingival")
    ), f"no enum member covers {draft_finding!r}; have {sorted(enum_values)}"


def test_nc03_proposed_drugs_are_clean_for_p002(engine_check):
    """NC-03a -- both draft proposals for P-002 must pass with zero warnings."""
    for drug in ("Amoxicillin", "Paracetamol"):
        result = engine_check("P-002", drug)
        assert result.warnings == [], (drug, result.warnings)


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap H: prescriptions come from DRUGS_DATABASE defaults only -- "
        "Amoxicillin defaults to '7 days' while P-002 specifies 'x 5 days', and "
        "there is no dose/duration contract to compare against. Frequency "
        "wording ('3 times daily' vs 'q8h') is likewise unchecked."
    ),
)
def test_nc03_dosages_match_draft_table(engine):
    """NC-03b -- dosages must match profiles S4 exactly (500 mg q8h x 5 days)."""
    amoxicillin = engine.DRUGS_DATABASE["Amoxicillin"]
    assert amoxicillin["default_duration"] == "5 days", amoxicillin


def test_nc04_sulfa_allergy_does_not_cross_react(engine_check):
    """NC-04 -- sulfa allergy must not be inferred as penicillin allergy (R-09)."""
    result = engine_check("P-006", "Amoxicillin")
    assert result.warnings == [], result.warnings


def test_nc05_clean_patient_has_no_warnings(engine_check):
    """NC-05 -- no allergies, no meds, no conditions: nothing to warn about."""
    result = engine_check("P-001", "Amoxicillin")
    assert result.warnings == [], result.warnings


def test_nc06_no_warfarin_means_no_interaction_warning(engine_check):
    """NC-06a -- R-02 must key on warfarin, not on the identity of P-004.

    Only the non-firing half of the split expectation is assertable: R-03 would
    supply the required warning but has no age input (see NC-06b).
    """
    result = engine_check(
        "P-004",
        "Ibuprofen",
        overrides={
            "current_medications": [
                "Amlodipine 5 mg daily",
                "Atorvastatin 20 mg nightly",
            ]
        },
    )
    assert result.warnings == [], result.warnings


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap A: check_prescription_safety() has no age parameter, so "
        "R-03 cannot fire on P-004's age_years=72 once warfarin is removed. "
        "The expected >=1 warning has no source."
    ),
)
def test_nc06_age_still_fires_without_warfarin(engine_check):
    """NC-06b -- isolating R-02 must leave R-03 firing."""
    result = engine_check(
        "P-004",
        "Ibuprofen",
        overrides={
            "current_medications": [
                "Amlodipine 5 mg daily",
                "Atorvastatin 20 mg nightly",
            ]
        },
    )
    assert len(result.warnings) >= 1, result.warnings


# --------------------------------------------------------------------------
# Gap probes -- not QA cases, but the failure mode that breaks every case
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{GAP} gap G: _check_contraindications() calls med.lower(), so the "
        "object shape profiles S5 specifies raises AttributeError. The API "
        "forwards Supabase JSONB through unchanged, so this would 500 "
        "POST /recommendations/treatment rather than warn."
    ),
)
def test_gap_structured_medication_from_handoff_contract(engine):
    """profiles S5 defines current_medications as name + dose + frequency."""
    structured = [
        {
            "name": "Warfarin",
            "dose": "5 mg",
            "frequency": "daily",
            "indication": "atrial fibrillation",
        }
    ]
    result = engine.check_prescription_safety(
        drug_name="Ibuprofen",
        patient_allergies=[],
        patient_medications=structured,
        patient_conditions=[],
    )
    assert result["warnings"] == [], result["warnings"]
