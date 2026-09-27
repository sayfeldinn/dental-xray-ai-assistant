"""Shared fixtures for the QA recommendation-engine suite.

Profile values are copied verbatim from ``docs/qa/synthetic-patient-profiles.md``
section 4. The contract IDs (P-001 ... P-006, R-01 ... R-09) are stable --
section 5 of that document permits correcting values but forbids renumbering.
"""
from __future__ import annotations

import pathlib
import sys
import types
from typing import Any, Dict, List, NamedTuple, Optional

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Importing the engine through ``app.services`` also executes
# ``app/services/__init__`` (patient_service -> supabase -> app.core.config),
# which calls Settings() at module level and therefore requires SUPABASE_URL,
# SUPABASE_KEY, SUPABASE_SERVICE_KEY and SECRET_KEY before any contraindication
# logic can be reached. ``app/schemas/__init__`` likewise pulls in patient.py
# and its EmailStr fields.
#
# None of that is what these tests are testing, and demanding env vars (or fake
# secrets) just to unit-test a pure function would make the suite unrunnable on
# a bare interpreter. So both *package* objects are substituted instead.
# __path__ still points at the real directories, so every submodule -- the
# engine itself and the two schema modules it depends on -- is loaded from disk
# unchanged. Nothing under test is stubbed; only the eager imports sitting
# beside it are skipped.
#
# Consequence: this suite covers recommendation_engine.py only. The config,
# supabase and API layers are exercised by no test today (worth raising).
for _pkg_name, _pkg_path in (
    ("app.services", _BACKEND / "app" / "services"),
    ("app.schemas", _BACKEND / "app" / "schemas"),
):
    _pkg = types.ModuleType(_pkg_name)
    _pkg.__path__ = [str(_pkg_path)]
    sys.modules[_pkg_name] = _pkg

from app.services.recommendation_engine import (  # noqa: E402
    recommendation_engine,
)

# Fields required by profiles section 5 that check_prescription_safety() has
# no parameter for. ``check()`` reports which of these were silently dropped,
# so each xfail reason can name exactly what the engine never saw.
UNMAPPED_FIELDS = ("age_years", "weight_kg", "lifestyle")

PROFILES: Dict[str, Dict[str, Any]] = {
    "P-001": {
        "age_years": 28,
        "weight_kg": 62,
        "lifestyle": "non-smoker, no alcohol",
        "allergies": [],
        "current_medications": [],
        "conditions": [],
    },
    "P-002": {
        "age_years": 35,
        "weight_kg": 78,
        "lifestyle": "non-smoker",
        "allergies": [],
        "current_medications": [],
        "conditions": [],
    },
    "P-003": {
        "age_years": 19,
        "weight_kg": 55,
        "lifestyle": "non-smoker",
        "allergies": ["penicillin"],
        "current_medications": [],
        "conditions": ["atopic eczema"],
    },
    "P-004": {
        "age_years": 72,
        "weight_kg": 70,
        "lifestyle": "ex-smoker",
        "allergies": [],
        "current_medications": [
            "Warfarin 5 mg daily",
            "Amlodipine 5 mg daily",
            "Atorvastatin 20 mg nightly",
        ],
        "conditions": [
            "atrial fibrillation",
            "hypertension",
            "hyperlipidemia",
        ],
    },
    "P-005": {
        "age_years": 6,
        "weight_kg": 18,
        "lifestyle": "n/a (pediatric)",
        "allergies": [],
        "current_medications": [],
        "conditions": [],
    },
    "P-006": {
        "age_years": 45,
        "weight_kg": 90,
        "lifestyle": "non-smoker",
        "allergies": ["sulfa"],
        "current_medications": ["Metformin 1000 mg daily"],
        "conditions": ["Type 2 diabetes, well controlled (HbA1c 6.4%)"],
    },
}

# Base context for the three cases the QA document marks "(no profile)" --
# TC-06, TC-16 and TC-17. Not a profile: no ID is invented, section 5 forbids
# renumbering P-001 ... P-006.
EMPTY_CONTEXT: Dict[str, Any] = {
    "age_years": None,
    "weight_kg": None,
    "lifestyle": None,
    "allergies": [],
    "current_medications": [],
    "conditions": [],
}


class SafetyCheck(NamedTuple):
    """Outcome of one ``check_prescription_safety()`` call."""

    safe: bool
    warnings: List[str]
    dropped: tuple

    @property
    def warning_text(self) -> str:
        """All warnings joined, for substring assertions."""
        return " | ".join(self.warnings)


def check(
    profile: Optional[str],
    drug: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> SafetyCheck:
    """Run the engine's standalone check for *drug* against *profile*.

    ``profile`` is a P-00x key, or ``None`` for the three cases the QA document
    marks ``(no profile)``. ``overrides`` applies the ``Input -> add/override``
    column. Fields the engine has no parameter for are reported in ``dropped``
    rather than silently vanishing -- an xfail reason should always name them.
    """
    source = (PROFILES.get(profile) if profile else None) or EMPTY_CONTEXT
    context = dict(source)
    context.update(overrides or {})
    dropped = tuple(
        f"{field}={context[field]}"
        for field in UNMAPPED_FIELDS
        if context.get(field) is not None
    )
    result = recommendation_engine.check_prescription_safety(
        drug_name=drug,
        patient_allergies=context["allergies"],
        patient_medications=context["current_medications"],
        patient_conditions=context["conditions"],
    )
    return SafetyCheck(
        safe=result["safe"],
        warnings=result["warnings"],
        dropped=dropped,
    )


@pytest.fixture
def engine():
    """The recommendation engine singleton."""
    return recommendation_engine


@pytest.fixture
def engine_check():
    """Standalone contraindication harness (see :func:`check`)."""
    return check
