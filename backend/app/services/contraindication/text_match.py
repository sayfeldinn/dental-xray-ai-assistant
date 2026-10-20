"""
DentalAI - Vocabulary Matching
Patient allergy/medication/condition lists are free text (seed data mixes
'alcohol_chronic', 'Penicillin (rash)', 'cardiac_endocarditis_risk'...). Terms are
normalised to lowercase tokens and matched against alias tables as whole-token
sequences, so 'renal' never matches 'adrenal_insufficiency'.
Anything outside the alias tables is NOT understood: extend the tables, don't loosen the matcher.
"""

import re
from typing import Iterable, Tuple

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def tokenize(term: str) -> Tuple[str, ...]:
    """'Penicillin (rash)' -> ('penicillin', 'rash')."""
    return tuple(t for t in _NON_ALNUM.split(term.lower()) if t)


def term_matches(term: str, alias: str) -> bool:
    """True if the alias's tokens appear contiguously inside the term's tokens."""
    haystack, needle = tokenize(term), tokenize(alias)
    if not needle or len(needle) > len(haystack):
        return False
    return any(
        haystack[i : i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    )


def any_term_matches(terms: Iterable[str], aliases: Iterable[str]) -> bool:
    """True if any patient term matches any alias."""
    aliases = tuple(aliases)
    return any(term_matches(t, a) for t in terms for a in aliases)


def matching_terms(terms: Iterable[str], aliases: Iterable[str]) -> Tuple[str, ...]:
    """The original patient terms that matched (for naming the allergen/drug in warnings)."""
    aliases = tuple(aliases)
    return tuple(t for t in terms if any(term_matches(t, a) for a in aliases))
