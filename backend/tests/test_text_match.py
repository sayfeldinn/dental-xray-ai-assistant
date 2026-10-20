import pytest

from app.services.contraindication.text_match import any_term_matches, term_matches, tokenize


def test_tokenize_normalises_case_and_punctuation():
    assert tokenize("Penicillin (rash)") == ("penicillin", "rash")
    assert tokenize("beta-lactam") == ("beta", "lactam")


@pytest.mark.parametrize("term,alias", [
    ("alcohol_chronic", "alcohol"),
    ("chronic_alcohol", "alcohol"),
    ("Penicillin (rash)", "penicillin"),
    ("beta-lactam allergy", "beta lactam"),
    ("prosthetic_cardiac_valve", "prosthetic cardiac valve"),
])
def test_matches(term, alias):
    assert term_matches(term, alias)


@pytest.mark.parametrize("term,alias", [
    ("adrenal_insufficiency", "renal"),     # substring but not a whole token
    ("sulfa", "penicillin"),
    ("renal", "renal impairment"),          # alias longer than term
    ("anything", ""),
])
def test_does_not_match(term, alias):
    assert not term_matches(term, alias)


def test_any_term_matches_checks_all_pairs():
    assert any_term_matches(["sulfa", "aspirin"], ["nsaid", "aspirin"])
    assert not any_term_matches([], ["nsaid"])
