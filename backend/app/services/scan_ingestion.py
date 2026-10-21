"""
DentalAI - Scan ingestion (Steps 1-2)
Upload a radiograph to private storage, run the dentex_week3 pipeline through DentexClient, and
store each detection as a *pending* finding. Also re-runs analysis on a stored scan.
"""

import logging
from typing import Optional
from uuid import UUID

from app.domain.errors import ConflictError, RuleViolationError, UpstreamError
from app.domain.scan import Scan, ScanAnalysisResponse, ScanCreate, ScanUpdate

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class ScanIngestionService:
    def __init__(self, scans, findings, ml, max_upload_mb: int = 20):
        self.scans = scans
        self.findings = findings
        self.ml = ml
        self.max_bytes = max_upload_mb * 1024 * 1024

    async def upload(
        self, *, patient_id: UUID, dentist_id: UUID, file_bytes: bytes, filename: Optional[str],
        content_type: Optional[str], scan_type: str, notes: Optional[str], auto_analyze: bool, confidence: float,
    ) -> ScanAnalysisResponse:
        self._validate(file_bytes, content_type)
        # Name the object after the validated type, never after the client's filename.
        name = f"scan.{ALLOWED_TYPES[content_type]}"
        image_url, storage_path = await self.scans.upload_image(file_bytes=file_bytes, patient_id=patient_id, filename=name)
        scan = await self.scans.create_scan(ScanCreate(
            patient_id=patient_id, dentist_id=dentist_id, scan_type=scan_type, image_url=image_url,
            storage_path=storage_path, notes=notes, status="uploaded"))
        if not auto_analyze:
            return ScanAnalysisResponse(scan_id=scan.id, status=scan.status, findings_count=0, raw_ml_output={})
        return await self._analyze(scan, file_bytes, filename or name, confidence)

    async def reanalyze(self, scan: Scan, confidence: float) -> ScanAnalysisResponse:
        """
        Run the model again on a stored scan. Refused once the dentist has reviewed any finding:
        replacing them would silently discard clinical decisions.
        """
        if not scan.storage_path:
            raise RuleViolationError("This scan has no stored image to re-analyse")
        existing = await self.findings.list_findings_by_scan(scan.id)
        if any(f.review_status != "pending" for f in existing):
            raise ConflictError("Findings on this scan were already reviewed; upload a new scan instead")
        try:
            image = await self.scans.download_image(scan.storage_path)
        except Exception as exc:
            raise UpstreamError(f"Could not read the stored image: {exc}") from exc
        await self.findings.delete_findings_by_scan(scan.id)
        return await self._analyze(scan, image, scan.storage_path.rsplit("/", 1)[-1], confidence)

    def _validate(self, file_bytes: bytes, content_type: Optional[str]) -> None:
        if content_type not in ALLOWED_TYPES:
            raise RuleViolationError("Upload a JPEG, PNG or WebP image")
        if not file_bytes:
            raise RuleViolationError("The uploaded file is empty")
        if len(file_bytes) > self.max_bytes:
            raise RuleViolationError(f"The image is larger than {self.max_bytes // (1024 * 1024)} MB")

    async def _analyze(self, scan: Scan, image: bytes, filename: str, confidence: float) -> ScanAnalysisResponse:
        await self.scans.update_scan(scan.id, ScanUpdate(status="processing"))
        try:
            output = await self.ml.analyze_scan(image_bytes=image, filename=filename, confidence_threshold=confidence)
        except Exception as exc:
            logger.exception("ML analysis failed for scan %s", scan.id)
            await self.scans.update_scan(scan.id, ScanUpdate(status="failed", notes=f"AI analysis failed: {exc}"))
            raise UpstreamError("The scan was saved but the AI analysis failed. Check the ML service and re-analyse.") from exc

        report = output.get("report")
        await self.scans.update_ml_results(
            scan_id=scan.id, ml_output=output, ai_report=report,
            image_width=output.get("image_width", 0), image_height=output.get("image_height", 0))
        rows = self.ml.parse_detections_to_findings(ml_output=output, scan_id=str(scan.id), patient_id=str(scan.patient_id))
        created = await self.findings.bulk_create_findings(rows) if rows else []
        return ScanAnalysisResponse(scan_id=scan.id, status="analyzed", ai_report=report,
                                    findings_count=len(created), raw_ml_output=output)
