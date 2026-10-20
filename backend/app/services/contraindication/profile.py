"""
DentalAI - Patient Safety Profile
The slice of a patient record the safety rules need, with age/weight derived once.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple

from app.domain.patient import Patient
from .catalog import (
    ALLERGY_CLASSES, CONDITION_CLASSES, MEDICATION_CLASSES,
    PEDIATRIC_AGE_YEARS, ELDERLY_AGE_YEARS,
)
from .text_match import any_term_matches, matching_terms


def age_on(date_of_birth: date, on_date: date) -> int:
    """Whole years on a given date."""
    had_birthday = (on_date.month, on_date.day) >= (date_of_birth.month, date_of_birth.day)
    return on_date.year - date_of_birth.year - (0 if had_birthday else 1)


@dataclass(frozen=True)
class PatientSafetyProfile:
    age_years: int
    weight_kg: Optional[float]
    allergies: Tuple[str, ...] = ()
    medications: Tuple[str, ...] = ()
    conditions: Tuple[str, ...] = ()

    @classmethod
    def from_patient(cls, patient: Patient, on_date: Optional[date] = None) -> "PatientSafetyProfile":
        return cls(
            age_years=age_on(patient.date_of_birth, on_date or date.today()),
            weight_kg=patient.weight_kg,
            allergies=tuple(patient.allergies),
            medications=tuple(patient.current_medications),
            conditions=tuple(patient.medical_conditions),
        )

    @property
    def is_pediatric(self) -> bool:
        return self.age_years < PEDIATRIC_AGE_YEARS

    @property
    def is_elderly(self) -> bool:
        return self.age_years >= ELDERLY_AGE_YEARS

    def allergen_terms(self, allergy_class: str) -> Tuple[str, ...]:
        """Patient's own allergy entries that fall in the class (to name the allergen in warnings)."""
        return matching_terms(self.allergies, ALLERGY_CLASSES[allergy_class])

    def has_allergy(self, allergy_class: str) -> bool:
        return any_term_matches(self.allergies, ALLERGY_CLASSES[allergy_class])

    def has_condition(self, condition_class: str) -> bool:
        return any_term_matches(self.conditions, CONDITION_CLASSES[condition_class])

    def has_alcohol_use(self) -> bool:
        # Seed data records 'alcohol_chronic' under current_medications, so look in both lists.
        return any_term_matches(self.conditions + self.medications, CONDITION_CLASSES["alcohol_use"])

    def medication_terms(self, medication_class: str) -> Tuple[str, ...]:
        return matching_terms(self.medications, MEDICATION_CLASSES[medication_class])

    def condition_terms(self, condition_class: str) -> Tuple[str, ...]:
        return matching_terms(self.conditions, CONDITION_CLASSES[condition_class])

    @property
    def needs_cardiac_prophylaxis(self) -> bool:
        return self.has_condition("cardiac_prophylaxis_risk")
