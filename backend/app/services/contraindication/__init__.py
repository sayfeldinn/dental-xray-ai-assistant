"""Contraindication checking (pure: no database or network access)."""

from .checker import ContraindicationChecker, doses_per_day, parse_dose_mg
from .profile import PatientSafetyProfile, age_on

__all__ = ["ContraindicationChecker", "PatientSafetyProfile", "age_on", "parse_dose_mg", "doses_per_day"]
