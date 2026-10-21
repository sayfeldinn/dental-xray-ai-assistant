"""
DentalAI - Access control
A dentist may only touch patients they own (patients.dentist_id) and everything hanging off them:
scans, findings, treatments, prescriptions and feedback. Every resource is resolved back to its
patient and checked here.

Someone else's record answers 404, exactly like a missing one, so record ids cannot be probed.
"""

from uuid import UUID

from app.core.auth import AuthenticatedDentist
from app.domain.errors import NotFoundError


class AccessService:
    def __init__(self, patients, scans, findings, treatments, prescriptions):
        self.patients = patients
        self.scans = scans
        self.findings = findings
        self.treatments = treatments
        self.prescriptions = prescriptions

    async def patient(self, patient_id: UUID, dentist: AuthenticatedDentist):
        patient = await self.patients.get_patient(patient_id)
        if not patient or patient.dentist_id != dentist.id:
            raise NotFoundError("Patient not found")
        return patient

    async def scan(self, scan_id: UUID, dentist: AuthenticatedDentist):
        scan = await self.scans.get_scan(scan_id)
        if not scan:
            raise NotFoundError("Scan not found")
        await self._owns(scan.patient_id, dentist, "Scan not found")
        return scan

    async def finding(self, finding_id: UUID, dentist: AuthenticatedDentist):
        finding = await self.findings.get_finding(finding_id)
        if not finding:
            raise NotFoundError("Finding not found")
        await self._owns(finding.patient_id, dentist, "Finding not found")
        return finding

    async def treatment(self, treatment_id: UUID, dentist: AuthenticatedDentist):
        treatment = await self.treatments.get_treatment(treatment_id)
        if not treatment:
            raise NotFoundError("Treatment not found")
        await self._owns(treatment.patient_id, dentist, "Treatment not found")
        return treatment

    async def prescription(self, prescription_id: UUID, dentist: AuthenticatedDentist):
        rx = await self.prescriptions.get_prescription(prescription_id)
        if not rx:
            raise NotFoundError("Prescription not found")
        await self._owns(rx.patient_id, dentist, "Prescription not found")
        return rx

    async def _owns(self, patient_id: UUID, dentist: AuthenticatedDentist, message: str) -> None:
        patient = await self.patients.get_patient(patient_id)
        if not patient or patient.dentist_id != dentist.id:
            raise NotFoundError(message)
