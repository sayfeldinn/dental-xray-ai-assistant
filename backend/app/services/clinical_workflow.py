"""
DentalAI - Clinical Workflow Service (Steps 4-5)
Orchestrates the pure engines with persistence. The rules live in services/recommendation and
services/contraindication; this module only loads data, applies the dentist-decision policy,
and saves. Dependencies are injected so tests can run it against in-memory fakes.
"""

import logging
from datetime import date, datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional
from uuid import UUID

from app.domain.errors import ConflictError, NotFoundError, RuleViolationError
from app.domain.feedback import FeedbackListResponse, FeedbackLog, FeedbackLogCreate, FeedbackSummary, MissedFindingReport
from app.domain.finding import Finding, FindingReviewRequest
from app.domain.prescription import (
    Prescription, PrescriptionCheckRequest, PrescriptionCreate,
    PrescriptionDecisionRequest, PrescriptionManualCreate, SafetyCheckResult,
)
from app.domain.recommendation import RecommendationRequest, RecommendationResponse, TreatmentPlan
from app.domain.treatment import (
    Treatment, TreatmentCreate, TreatmentDecisionRequest, TreatmentManualCreate, TreatmentWithPrescriptions,
)
from app.services.contraindication import ContraindicationChecker, PatientSafetyProfile
from app.services.feedback import (
    finding_feedback, missed_finding_feedback, ml_finding_feedback, prescription_feedback, summarize,
    treatment_feedback,
)
from app.services.recommendation import RecommendationEngine

logger = logging.getLogger(__name__)


class ClinicalWorkflowService:
    def __init__(
        self,
        patients,
        scans,
        findings,
        treatments,
        prescriptions,
        engine: Optional[RecommendationEngine] = None,
        checker: Optional[ContraindicationChecker] = None,
        today: Callable[[], date] = date.today,
        feedback=None,
        ml_feedback: Optional[Callable[..., Awaitable]] = None,
    ):
        self.patients = patients
        self.scans = scans
        self.findings = findings
        self.treatments = treatments
        self.prescriptions = prescriptions
        self.checker = checker or ContraindicationChecker()
        self.engine = engine or RecommendationEngine(self.checker)
        self._today = today
        self.feedback = feedback          # clinical_feedback_logs service; None disables the ledger
        self.ml_feedback = ml_feedback    # DentexClient.submit_feedback; None disables forwarding

    # --- Step 4: recommendation ----------------------------------------------

    async def generate_for_scan(self, scan_id: UUID, request: RecommendationRequest) -> RecommendationResponse:
        """
        Propose treatments and drugs for every dentist-validated finding of a scan.
        Re-running replaces untouched proposals; anything the dentist already acted on is kept.
        """
        scan = await self.scans.get_scan(scan_id)
        if not scan:
            raise NotFoundError("Scan not found")
        patient = await self.patients.get_patient(scan.patient_id)
        if not patient:
            raise NotFoundError("Patient not found")

        findings = await self.findings.get_confirmed_findings(scan_id)
        if not findings:
            raise ConflictError("No dentist-validated findings for this scan: review its findings first (Step 3)")

        existing = await self.treatments.list_treatments(scan_id=scan_id)
        existing_rx = await self.prescriptions.list_prescriptions(treatment_ids=[t.id for t in existing])
        acted_on = {rx.treatment_id for rx in existing_rx if rx.dentist_status != "proposed"}
        locked = [t for t in existing if t.status != "proposed" or t.id in acted_on]
        stale_ids = [t.id for t in existing if t not in locked]
        locked_finding_ids = {t.finding_id for t in locked}

        to_plan = [f for f in findings if f.id not in locked_finding_ids]
        skipped = [f.id for f in findings if f.id in locked_finding_ids]

        profile = PatientSafetyProfile.from_patient(patient, self._today())
        proposals = self.engine.recommend_for_scan(to_plan, profile, request.clinical_context)

        await self.treatments.delete_treatments(stale_ids)
        created_ids: List[UUID] = []
        plans: List[TreatmentPlan] = []
        try:
            for proposal in proposals:
                treatment = await self.treatments.create_treatment(TreatmentCreate(
                    patient_id=patient.id,
                    scan_id=scan_id,
                    finding_id=proposal.finding.id,
                    dentist_id=request.dentist_id,
                    treatment_category=proposal.category,
                    description=proposal.description,
                    requires_prescription=bool(proposal.prescriptions),
                    clinical_justification=proposal.justification,
                ))
                created_ids.append(treatment.id)
                saved = [
                    await self.prescriptions.create_prescription(PrescriptionCreate(
                        treatment_id=treatment.id,
                        patient_id=patient.id,
                        finding_id=proposal.finding.id,
                        dentist_id=request.dentist_id,
                        drug_name=rx.drug_name,
                        dosage=rx.dosage,
                        frequency=rx.frequency,
                        duration=rx.duration,
                        indication_type=rx.indication_type,
                        instructions=rx.instructions,
                        contraindication_status=rx.status,
                        contraindication_warnings=rx.warnings,
                    ))
                    for rx in proposal.prescriptions
                ]
                plans.append(TreatmentPlan(treatment=treatment, prescriptions=saved, alerts=proposal.alerts))
        except Exception:
            await self.treatments.delete_treatments(created_ids)   # no half-written plans
            raise

        return RecommendationResponse(scan_id=scan_id, plans=plans, skipped_finding_ids=skipped)

    async def check_prescription(self, request: PrescriptionCheckRequest) -> SafetyCheckResult:
        """Stateless safety check for a dentist-chosen drug/dose."""
        profile = await self._profile(request.patient_id)
        return self.checker.check(
            request.drug_name, request.indication_type, profile, request.dosage, request.frequency)

    # --- dentist-authored additions -------------------------------------------

    async def create_treatment(self, request: TreatmentManualCreate) -> Treatment:
        """A dentist adds their own treatment to a scan. It is their decision, so it is stored confirmed."""
        scan = await self.scans.get_scan(request.scan_id)
        if not scan:
            raise NotFoundError("Scan not found")
        if request.finding_id:
            finding = await self.findings.get_finding(request.finding_id)
            if not finding:
                raise NotFoundError("Finding not found")
            if finding.scan_id != request.scan_id:
                raise RuleViolationError("The finding does not belong to this scan")
        return await self.treatments.create_treatment(TreatmentCreate(
            patient_id=scan.patient_id,
            scan_id=request.scan_id,
            finding_id=request.finding_id,
            dentist_id=request.dentist_id,
            treatment_category=request.treatment_category,
            description=request.description,
            clinical_justification=request.clinical_justification,
            dentist_notes=request.dentist_notes,
            status="confirmed",
            confirmed_at=datetime.now(timezone.utc),
        ))

    async def create_prescription(self, request: PrescriptionManualCreate) -> Prescription:
        """
        A dentist adds a prescription to a treatment they already decided. The drug is safety-checked and
        stored as 'proposed', so it still passes the same Step 5 gates (acknowledge / override) before use.
        """
        treatment = await self.treatments.get_treatment(request.treatment_id)
        if not treatment:
            raise NotFoundError("Treatment not found")
        if treatment.status in ("proposed", "cancelled"):
            raise ConflictError(
                f"Treatment is {treatment.status}: confirm or modify it before adding prescriptions "
                "(proposals are replaced when recommendations are regenerated)")

        result = self.checker.check(
            request.drug_name, request.indication_type, await self._profile(treatment.patient_id),
            request.dosage, request.frequency)
        prescription = await self.prescriptions.create_prescription(PrescriptionCreate(
            treatment_id=treatment.id,
            patient_id=treatment.patient_id,
            finding_id=treatment.finding_id,
            dentist_id=request.dentist_id,
            drug_name=result.drug_name,
            dosage=request.dosage,
            frequency=request.frequency,
            duration=request.duration,
            indication_type=request.indication_type,
            instructions=request.instructions,
            contraindication_status=result.status,
            contraindication_warnings=result.warnings,
        ))
        if not treatment.requires_prescription:
            await self.treatments.update_treatment(treatment.id, {"requires_prescription": True})
        return prescription

    # --- Step 5: dentist decisions -------------------------------------------

    async def decide_prescription(self, prescription_id: UUID, request: PrescriptionDecisionRequest) -> Prescription:
        """
        Apply the dentist's decision. For accept/modify the drug is re-checked against the
        patient's CURRENT record (it may have changed since the proposal) and flagged drugs
        cannot be silently accepted:
          warning          -> acknowledge_warnings must be true
          contraindicated  -> override_reason must be given
        """
        rx = await self.prescriptions.get_prescription(prescription_id)
        if not rx:
            raise NotFoundError("Prescription not found")
        if rx.dentist_status != "proposed":
            raise ConflictError(f"Prescription already {rx.dentist_status}; decisions are final")
        treatment = await self.treatments.get_treatment(rx.treatment_id)
        if treatment and treatment.status == "cancelled":
            raise ConflictError("The parent treatment was cancelled")

        changes: Dict = {"dentist_status": request.decision}
        if request.decision != "rejected":
            drug_name = request.drug_name or rx.drug_name
            dosage = request.dosage or rx.dosage
            frequency = request.frequency or rx.frequency
            result = self.checker.check(
                drug_name, rx.indication_type, await self._profile(rx.patient_id), dosage, frequency)
            warnings = result.warnings
            if result.drug_name == rx.drug_name:
                # Keep the engine's substitution notice (R-18): the dentist must still see why this drug was chosen.
                warnings = [w for w in rx.contraindication_warnings if w.rule_id == "R-18"] + warnings
            status = self.checker.status_of(warnings)

            if status == "contraindicated" and not (request.override_reason or "").strip():
                raise RuleViolationError(
                    f"{result.drug_name} is contraindicated for this patient: an override_reason is required to accept it")
            if status == "warning" and not request.acknowledge_warnings:
                raise RuleViolationError(
                    f"{result.drug_name} has safety warnings: set acknowledge_warnings to accept it")

            changes.update(
                contraindication_status=status,
                contraindication_warnings=[w.model_dump(mode="json") for w in warnings],
                prescribed_at=datetime.now(timezone.utc).isoformat(),
            )
            if status != "clear" and request.override_reason:
                changes["dentist_override_reason"] = request.override_reason.strip()
            if request.decision == "modified":
                changes.update(drug_name=result.drug_name, dosage=dosage)
                for field in ("frequency", "duration", "instructions"):
                    if getattr(request, field) is not None:
                        changes[field] = getattr(request, field)
        if request.dentist_id:
            changes["dentist_id"] = str(request.dentist_id)

        updated = await self.prescriptions.update_prescription(prescription_id, changes)
        if treatment and updated:
            await self._record(prescription_feedback(rx, updated, treatment.scan_id, request.dentist_id))
        return updated

    async def decide_treatment(self, treatment_id: UUID, request: TreatmentDecisionRequest) -> Treatment:
        """Confirm, modify, or cancel a proposed treatment."""
        treatment = await self.treatments.get_treatment(treatment_id)
        if not treatment:
            raise NotFoundError("Treatment not found")
        if treatment.status != "proposed":
            raise ConflictError(f"Treatment already {treatment.status}; decisions are final")

        changes: Dict = {"status": request.decision}
        if request.decision != "cancelled":
            changes["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        for field in ("treatment_category", "description", "dentist_notes"):
            if getattr(request, field) is not None:
                changes[field] = getattr(request, field)
        if request.dentist_id:
            changes["dentist_id"] = str(request.dentist_id)

        updated = await self.treatments.update_treatment(treatment_id, changes)
        if updated:
            await self._record(treatment_feedback(treatment, updated, request.dentist_id))
        return updated

    # --- Step 3 (with Step 6 logging): finding review -------------------------

    async def review_finding(self, request: FindingReviewRequest) -> Finding:
        """Apply the dentist's review of an AI detection and log any correction of the AI."""
        before = await self.findings.get_finding(request.finding_id)
        if not before:
            raise NotFoundError("Finding not found")
        updated = await self.findings.review_finding(
            finding_id=request.finding_id,
            review_status=request.review_status,
            dentist_id=request.dentist_id,
            confirmed_disease=request.confirmed_disease,
            dentist_notes=request.dentist_notes,
        )
        if not updated:
            raise NotFoundError("Finding not found")
        await self._record(finding_feedback(
            before, request.review_status, request.confirmed_disease, request.dentist_notes, request.dentist_id))
        return updated

    async def report_missed_finding(self, report: MissedFindingReport) -> FeedbackLog:
        """The dentist saw a lesion the AI did not flag. Logged as a false negative."""
        if not await self.scans.get_scan(report.scan_id):
            raise NotFoundError("Scan not found")
        entry = missed_finding_feedback(report)
        log = await self._ledger().create_log(entry)   # this IS the request, so a failed write must surface
        await self._forward(entry, log)
        return log

    # --- Step 6: feedback ledger ----------------------------------------------

    async def list_feedback(self, scan_id=None, stage=None, correction_type=None) -> FeedbackListResponse:
        logs = await self._ledger().list_logs(scan_id=scan_id, stage=stage, correction_type=correction_type)
        return FeedbackListResponse(logs=logs, total=len(logs))

    async def feedback_summary(self, scan_id=None) -> FeedbackSummary:
        return summarize(await self._ledger().list_logs(scan_id=scan_id))

    async def _record(self, entry: Optional[FeedbackLogCreate]) -> Optional[FeedbackLog]:
        """
        Append a ledger row, then forward detection corrections to the ML service's retraining queue.
        Best effort by design: the dentist's decision is already saved, so a ledger or ML outage is logged
        for follow-up instead of failing the request or undoing a clinical decision.
        """
        if entry is None or self.feedback is None:
            return None
        try:
            log = await self.feedback.create_log(entry)
        except Exception:
            logger.exception("Feedback ledger write failed; decision was saved: %s/%s", entry.stage, entry.correction_type)
            return None
        await self._forward(entry, log)
        return log

    async def _forward(self, entry: FeedbackLogCreate, log: FeedbackLog) -> None:
        payload = ml_finding_feedback(entry)
        if payload and self.ml_feedback:
            try:
                await self.ml_feedback(**payload)
            except Exception:
                logger.exception("Forwarding feedback to the ML service failed; ledger row %s kept", log.id)

    def _ledger(self):
        if self.feedback is None:
            raise RuleViolationError("The feedback ledger is not configured")
        return self.feedback

    # --- reads ---------------------------------------------------------------

    async def get_treatment(self, treatment_id: UUID) -> TreatmentWithPrescriptions:
        treatment = await self.treatments.get_treatment(treatment_id)
        if not treatment:
            raise NotFoundError("Treatment not found")
        return (await self._attach_prescriptions([treatment]))[0]

    async def list_treatments(
        self, scan_id: Optional[UUID] = None, patient_id: Optional[UUID] = None, status: Optional[str] = None,
    ) -> List[TreatmentWithPrescriptions]:
        treatments = await self.treatments.list_treatments(scan_id=scan_id, patient_id=patient_id, status=status)
        return await self._attach_prescriptions(treatments)

    async def get_prescription(self, prescription_id: UUID) -> Prescription:
        prescription = await self.prescriptions.get_prescription(prescription_id)
        if not prescription:
            raise NotFoundError("Prescription not found")
        return prescription

    async def list_prescriptions(
        self, treatment_id: Optional[UUID] = None, patient_id: Optional[UUID] = None,
    ) -> List[Prescription]:
        return await self.prescriptions.list_prescriptions(
            treatment_ids=[treatment_id] if treatment_id else None, patient_id=patient_id)

    # --- helpers -------------------------------------------------------------

    async def _profile(self, patient_id: UUID) -> PatientSafetyProfile:
        patient = await self.patients.get_patient(patient_id)
        if not patient:
            raise NotFoundError("Patient not found")
        return PatientSafetyProfile.from_patient(patient, self._today())

    async def _attach_prescriptions(self, treatments: List[Treatment]) -> List[TreatmentWithPrescriptions]:
        rx = await self.prescriptions.list_prescriptions(treatment_ids=[t.id for t in treatments])
        by_treatment: Dict[UUID, List[Prescription]] = {}
        for p in rx:
            by_treatment.setdefault(p.treatment_id, []).append(p)
        return [TreatmentWithPrescriptions(**t.model_dump(), prescriptions=by_treatment.get(t.id, [])) for t in treatments]
