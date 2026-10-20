"""
DentalAI - Finding-to-Treatment Rules
Mirrors docs/CLINICAL_GUIDELINES.md §1. Change both together.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet


@dataclass(frozen=True)
class TreatmentRule:
    category: str       # must match the treatments.treatment_category CHECK constraint
    description: str


TREATMENT_RULES: Dict[str, TreatmentRule] = {
    "Caries": TreatmentRule(
        "restorative",
        "Restorative referral (filling or sealant). Systemic antibiotics are not indicated.",
    ),
    "Deep Caries": TreatmentRule(
        "endodontic",
        "Indirect pulp capping, pulpotomy, or endodontic evaluation. "
        "Systemic antibiotics only for acute systemic swelling or severe symptoms.",
    ),
    "Periapical Lesion": TreatmentRule(
        "endodontic",
        "Root canal treatment (RCT) or extraction referral. "
        "Systemic antibiotics only with active infection or abscess.",
    ),
    "Impacted": TreatmentRule(
        "surgical_extraction",
        "Oral surgery evaluation: extraction or monitoring. "
        "Prophylaxis only for at-risk cardiac patients when surgery is planned.",
    ),
}

# Findings for which a treatment antibiotic course can be proposed when the dentist reports
# active infection. Plain Caries is "strictly restorative": never antibiotics.
INFECTION_ELIGIBLE: FrozenSet[str] = frozenset({"Deep Caries", "Periapical Lesion", "Impacted"})

# Procedures that manipulate gingival tissue or the periapical region (AHA prophylaxis scope).
PROPHYLAXIS_ELIGIBLE: FrozenSet[str] = frozenset({"Periapical Lesion", "Impacted"})
