"""
DentalAI - Recommendation Engine (Step 4)
Maps dentist-validated findings to treatments and candidate drugs. Deterministic and pure:
no database, no network, no LLM. Every drug goes through ContraindicationChecker, and the
first non-contraindicated option in catalog.PREFERENCE wins (with a visible substitution warning).
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.domain.finding import Finding
from app.domain.prescription import SafetyWarning
from app.domain.recommendation import ClinicalContext, PlanAlert
from app.services.contraindication import ContraindicationChecker, PatientSafetyProfile
from app.services.contraindication.catalog import (
    CATALOG, DENTIST_DOSE_DOSAGE, PREFERENCE, WEIGHT_NEEDED_DOSAGE,
)
from .rules import INFECTION_ELIGIBLE, PROPHYLAXIS_ELIGIBLE, TREATMENT_RULES

GUIDE = "docs/CLINICAL_GUIDELINES.md"


@dataclass
class PrescriptionProposal:
    drug_name: str
    dosage: str
    frequency: str
    duration: str
    indication_type: str
    instructions: str
    status: str
    warnings: List[SafetyWarning]


@dataclass
class TreatmentProposal:
    finding: Finding
    category: str
    description: str
    justification: str
    prescriptions: List[PrescriptionProposal] = field(default_factory=list)
    alerts: List[PlanAlert] = field(default_factory=list)


class RecommendationEngine:
    def __init__(self, checker: Optional[ContraindicationChecker] = None):
        self.checker = checker or ContraindicationChecker()

    def recommend_for_scan(
        self,
        findings: List[Finding],
        patient: PatientSafetyProfile,
        context: ClinicalContext,
    ) -> List[TreatmentProposal]:
        """One proposal per finding. Each systemic drug is proposed once per scan (first tooth wins)."""
        proposed_under: Dict[str, str] = {}   # indication -> FDI of the tooth that already carries it
        return [self._recommend(f, patient, context, proposed_under) for f in findings]

    # --- per finding ---------------------------------------------------------

    def _recommend(self, finding, patient, context, proposed_under) -> TreatmentProposal:
        disease = finding.effective_disease
        rule = TREATMENT_RULES.get(disease)
        if rule is None:
            return TreatmentProposal(
                finding, "monitoring",
                f"No automated rule for '{disease}': dentist to decide the management.",
                self._justification(finding),
                alerts=[PlanAlert(code="UNMAPPED_FINDING",
                                  message=f"'{disease}' has no recommendation rule; no drugs were proposed.")],
            )

        proposal = TreatmentProposal(finding, rule.category, rule.description, self._justification(finding))

        indications: List[str] = []
        if context.active_infection:
            if disease in INFECTION_ELIGIBLE:
                indications.append("active_infection")
            else:
                proposal.alerts.append(PlanAlert(
                    code="ANTIBIOTIC_NOT_INDICATED",
                    message=f"Active infection reported but '{disease}' is managed restoratively without systemic "
                            "antibiotics. Reconsider the finding (e.g. Deep Caries / Periapical Lesion)."))
        if patient.needs_cardiac_prophylaxis and disease in PROPHYLAXIS_ELIGIBLE:
            indications.append("pre_procedure_prophylaxis")
        if context.pain:
            indications.append("pain_management")

        for indication in indications:
            if indication in proposed_under:
                proposal.alerts.append(PlanAlert(
                    code="DUPLICATE_DRUG_SKIPPED",
                    message=f"{indication} medication is already proposed under tooth {proposed_under[indication]}; "
                            "not repeated."))
                continue
            proposed_under[indication] = finding.tooth_fdi
            prescription, exclusions = self._select_drug(indication, patient)
            if prescription:
                proposal.prescriptions.append(prescription)
            else:
                proposal.alerts.append(PlanAlert(
                    code="NO_SAFE_DRUG",
                    message=f"No safe {indication} drug could be proposed ({exclusions}). Dentist decision required."))

        if {rx.indication_type for rx in proposal.prescriptions} >= {"active_infection", "pre_procedure_prophylaxis"}:
            proposal.alerts.append(PlanAlert(
                code="OVERLAPPING_ANTIBIOTICS",
                message="Both an infection course and procedural prophylaxis are proposed: "
                        "dentist to reconcile the overlapping antibiotics."))
        return proposal

    # --- drug selection ------------------------------------------------------

    def _select_drug(self, indication: str, patient: PatientSafetyProfile
                     ) -> Tuple[Optional[PrescriptionProposal], str]:
        excluded: List[Tuple[str, str]] = []   # (drug, reasons)
        for name in PREFERENCE[indication]:
            dosage, frequency, duration, instructions = self._regimen(name, indication, patient)
            result = self.checker.check(name, indication, patient, dosage, frequency)
            if result.status == "contraindicated":
                reasons = " ".join(w.message for w in result.warnings if w.severity == "contraindicated")
                excluded.append((name, reasons))
                continue
            warnings = [
                SafetyWarning(code="FIRST_LINE_EXCLUDED", rule_id="R-18", severity="warning", drug=ex_name,
                              message=f"{ex_name} not proposed: {reasons} Substituted {name}.", source=GUIDE)
                for ex_name, reasons in excluded
            ] + result.warnings
            return PrescriptionProposal(
                name, dosage, frequency, duration, indication, instructions,
                self.checker.status_of(warnings), warnings,
            ), ""
        return None, "; ".join(f"{n}: {r}" for n, r in excluded)

    @staticmethod
    def _regimen(drug_name: str, indication: str, patient: PatientSafetyProfile) -> Tuple[str, str, str, str]:
        regimen = CATALOG[drug_name].regimens[indication]
        if not patient.is_pediatric:
            return regimen.dosage, regimen.frequency, regimen.duration, regimen.instructions
        peds = regimen.pediatric
        if peds is None:
            return DENTIST_DOSE_DOSAGE, regimen.frequency, regimen.duration, regimen.instructions
        if patient.weight_kg is None:
            return WEIGHT_NEEDED_DOSAGE, peds.frequency, peds.duration, regimen.instructions

        def mg(per_kg: float) -> float:
            # Floor to 5 mg so rounding can never push a dose over the limit the checker enforces.
            return math.floor(min(per_kg * patient.weight_kg, peds.max_single_mg) / 5) * 5

        dosage = f"{mg(peds.mg_per_kg):g} mg"
        if peds.follow_on_mg_per_kg:
            dosage += f" day 1, then {mg(peds.follow_on_mg_per_kg):g} mg daily"
        return dosage, peds.frequency, peds.duration, regimen.instructions

    @staticmethod
    def _justification(finding: Finding) -> str:
        text = (f"{finding.effective_disease} at tooth {finding.tooth_fdi} "
                f"(AI confidence {finding.disease_confidence:.0%}), validated by the dentist")
        if finding.confirmed_disease and finding.confirmed_disease != finding.disease:
            text += f"; dentist corrected the AI label '{finding.disease}'"
        return f"{text}. Rules: {GUIDE} §1-2."
