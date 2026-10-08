"""
ML inference service for X-ray analysis.

The detector (``dentex_week3``) lives in a separate process so the web process
never imports torch -- that matters on machines where the CUDA build cannot
load. This module is the HTTP client for that service.

There is deliberately no mock fallback: when the detector cannot be reached
this raises, and the caller returns an error. Substituting invented findings
would put fabricated boxes and tooth numbers in front of a dentist and, because
they are persisted, would outlive the request that created them.
"""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.schemas.prediction import (
    coerce_confidence,
    coerce_finding_type,
    coerce_non_negative,
    coerce_positive,
    coerce_severity,
)
from app.schemas.scan import BoundingBox, Finding, FindingTypeEnum

# Finding types the deployed detector can emit, in API-facing order.
# dentex_week3 predicts four disease classes -- Impacted, Caries, Deep Caries
# and Periapical Lesion -- which map onto three finding types (Deep Caries
# shares the CARIES type with Caries, and Impacted maps to PERICORONAL).
SUPPORTED_FINDINGS: List[str] = [
    FindingTypeEnum.CARIES.value,
    FindingTypeEnum.PERIAPICAL.value,
    FindingTypeEnum.PERICORONAL.value,
]

_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".dcm": "application/dicom",
}


class MLInferenceService:
    """Client for the dentex_week3 detection API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        url = settings.ML_API_URL if api_url is None else api_url
        self.api_url = (url or "").strip().rstrip("/")
        self.timeout = timeout if timeout is not None else settings.ML_TIMEOUT_SECONDS
        self.model_version = "unconfigured" if not self.api_url else "unknown"
        self.last_error: Optional[str] = None
        self.last_latency_ms: Optional[float] = None
        # Whole detector payload from the last successful call, so callers can
        # persist what does not fit in a Finding (report, quadrant boxes).
        self.last_result: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    async def predict(
        self,
        image_source: str,
        confidence_threshold: float = 0.5,
    ) -> List[Finding]:
        """Run detection on an image given as a URL or a local path.

        Raises if the detector is unreachable or answers with something
        unusable -- there is no fallback to invented findings. On success the
        raw payload is kept on :attr:`last_result`.
        """
        if not self.api_url:
            self.last_error = "ML_API_URL is not configured"
            raise RuntimeError(self.last_error)

        started = time.perf_counter()
        try:
            image_bytes, content_type = await self._load_image(image_source)
            payload = await self._call_api(
                image_bytes, content_type, confidence_threshold
            )
        except Exception as exc:  # noqa: BLE001 - record, then let it propagate
            self.last_error = str(exc)
            self.last_latency_ms = round((time.perf_counter() - started) * 1000, 1)
            raise

        self.last_error = None
        self.last_latency_ms = round((time.perf_counter() - started) * 1000, 1)
        self.last_result = payload if isinstance(payload, dict) else {}
        self.model_version = self._detector_model_version()

        detections = _extract_detections(payload)
        findings = [f for f in (_to_finding(d) for d in detections) if f is not None]
        return [f for f in findings if f.confidence >= confidence_threshold]

    # ------------------------------------------------------------------ #
    # what the detector returned beyond the findings
    # ------------------------------------------------------------------ #
    def _detector_model_version(self) -> str:
        """Name the pipeline that actually answered, from its own payload.

        The tooth-association variant is the useful discriminator -- it is what
        changes between training runs, and the two ``best.pt`` files are named
        identically so they identify nothing.
        """
        model = self.last_result.get("model")
        if isinstance(model, dict):
            variant = model.get("tooth")
            if variant:
                return f"dentex_week3/{variant}"
        return "dentex_week3"

    @property
    def ai_report(self) -> Optional[str]:
        """The detector's AI-generated clinical report, when it sent one."""
        report = self.last_result.get("ai_generated_report")
        return report if isinstance(report, str) and report.strip() else None

    @property
    def quadrants(self) -> List[Dict[str, Any]]:
        """Quadrant boxes the detector found, in original-image coordinates."""
        quadrants = self.last_result.get("quadrants")
        return quadrants if isinstance(quadrants, list) else []

    async def batch_predict(
        self,
        image_paths: List[str],
        confidence_threshold: float = 0.5,
    ) -> Dict[str, List[Finding]]:
        results: Dict[str, List[Finding]] = {}
        for image_path in image_paths:
            results[image_path] = await self.predict(image_path, confidence_threshold)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Model metadata for ``GET /ml/model-info``.

        ``mode`` is ``live`` whenever a detector URL is configured; an
        unconfigured service is reported as such rather than pretending to be
        a working model.
        """
        return {
            "model_version": self.model_version,
            "model_loaded": bool(self.api_url),
            "mode": "live" if self.api_url else "unconfigured",
            "detector": "dentex_week3",
            "ml_api_url": self.api_url or None,
            "reachable": None if self.api_url else False,
            "supported_findings": SUPPORTED_FINDINGS,
            "confidence_threshold": settings.ML_DEFAULT_CONFIDENCE,
            "last_error": self.last_error,
            "last_latency_ms": self.last_latency_ms,
        }

    async def probe(self) -> Dict[str, Any]:
        """Check whether the detector is answering, without running inference."""
        info = self.get_model_info()
        if not self.api_url:
            info["reachable"] = False
            info["detail"] = "ML_API_URL is not configured"
            return info
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 5.0)) as client:
                response = await client.get(f"{self.api_url}/")
                response.raise_for_status()
            info["reachable"] = True
            info["detail"] = "detector is answering"
        except Exception as exc:  # noqa: BLE001
            info["reachable"] = False
            info["detail"] = str(exc)
            info["last_error"] = str(exc)
        info["probe_latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        return info

    # ------------------------------------------------------------------ #
    # transport
    # ------------------------------------------------------------------ #
    async def _load_image(self, image_source: str) -> Tuple[bytes, str]:
        """Return (bytes, content_type) for a URL or filesystem path."""
        if not image_source:
            raise ValueError("no image source supplied")

        parsed = urlparse(image_source)
        if parsed.scheme in ("http", "https"):
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                response = await client.get(image_source)
                response.raise_for_status()
                content_type = (response.headers.get("content-type") or "").split(";")[0]
                if not content_type.startswith("image/"):
                    content_type = "image/jpeg"
                return response.content, content_type

        path = Path(image_source)
        if path.is_file():
            suffix = path.suffix.lower()
            return path.read_bytes(), _CONTENT_TYPES.get(suffix, "image/jpeg")

        raise ValueError(f"could not resolve image source: {image_source!r}")

    async def _call_api(
        self,
        image_bytes: bytes,
        content_type: str,
        confidence_threshold: float,
    ) -> Any:
        """POST the image and return the detector's payload unreshaped.

        The whole payload is returned rather than just the detections, because
        dentex_week3 also sends the clinical report and quadrant boxes and
        those are worth persisting.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/predict",
                # The detector applies the same floor server-side, so the
                # threshold the caller asked for is the one that takes effect.
                params={"conf": confidence_threshold},
                files={"file": ("xray", image_bytes, content_type)},
            )
            response.raise_for_status()
            return response.json()


def _extract_detections(payload: Any) -> List[Dict[str, Any]]:
    """Pull the detection list out of whichever payload shape arrived.

    dentex_week3 answers with ``{"detections": [...]}``; the v1 contract used a
    bare list. Anything else is an error rather than an empty result -- a
    silently empty detection list is indistinguishable from a clean X-ray.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("detections", "predictions", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError(f"unexpected detector response: {type(payload).__name__}")


def _to_finding(detection: Dict[str, Any]) -> Optional[Finding]:
    """Map one detector response onto a ``Finding``.

    Understands the v1 contract (``class_name`` + ``bbox.xmin/ymin/xmax/ymax``)
    and the dentex_week3 contract (``disease`` + ``disease_confidence`` +
    ``quadrant``/``tooth_id`` + ``box`` list), so either deployment can back
    this API.
    """
    if not isinstance(detection, dict):
        return None

    label = detection.get("class_name") or detection.get("disease") or detection.get("type")
    if label is None:
        return None

    finding_type = coerce_finding_type(label)
    severity = coerce_severity(detection.get("severity"), finding_type)

    confidence_value = detection.get("confidence")
    if confidence_value is None:
        # dentex_week3 names the detector score ``disease_confidence``.
        confidence_value = detection.get("disease_confidence")
    confidence = coerce_confidence(confidence_value)

    bbox = detection.get("bbox") or detection.get("disease_bbox") or detection
    x, y, width, height = _box_coordinates(bbox)

    tooth_number = _tooth_number(detection)
    description = detection.get("description") or detection.get("notes")
    if not description and label:
        description = f"{str(label)} detected"

    return Finding(
        type=finding_type,
        severity=severity,
        confidence=confidence,
        bounding_box=BoundingBox(x=x, y=y, width=width, height=height),
        tooth_number=tooth_number,
        description=description,
        ai_generated=True,
        confirmed=False,
    )


def _box_coordinates(source: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Return ``(x, y, width, height)`` from whichever bbox shape is present.

    Accepts the v1 ``xmin/ymin/xmax/ymax`` dict, an ``x/y/width/height`` dict,
    and dentex_week3's ``box`` list in ``[x1, y1, x2, y2]`` order.
    """
    box = source.get("box")
    if isinstance(box, (list, tuple)) and len(box) == 4:
        x1, y1, x2, y2 = (float(value) for value in box)
        return (
            coerce_non_negative(x1),
            coerce_non_negative(y1),
            coerce_positive(x2 - x1),
            coerce_positive(y2 - y1),
        )

    if all(key in source for key in ("xmin", "ymin", "xmax", "ymax")):
        xmin = coerce_non_negative(source.get("xmin"))
        ymin = coerce_non_negative(source.get("ymin"))
        return (
            xmin,
            ymin,
            coerce_positive(float(source.get("xmax", 0)) - float(source.get("xmin", 0))),
            coerce_positive(float(source.get("ymax", 0)) - float(source.get("ymin", 0))),
        )

    return (
        coerce_non_negative(source.get("x", source.get("xmin"))),
        coerce_non_negative(source.get("y", source.get("ymin"))),
        coerce_positive(source.get("width", source.get("w"))),
        coerce_positive(source.get("height", source.get("h"))),
    )


def _tooth_number(detection: Dict[str, Any]) -> Optional[str]:
    """FDI notation from a quadrant/tooth pair, when the model reports one."""
    explicit = detection.get("tooth_number") or detection.get("fdi")
    if explicit:
        return str(explicit)
    quadrant = detection.get("quadrant")
    # dentex_week3 reports the numeric tooth as ``tooth_id`` and the label as
    # ``tooth`` ("Tooth_8"); prefer the numeric one.
    tooth = detection.get("tooth_id")
    if tooth is None:
        tooth = detection.get("tooth")
    if quadrant is None or tooth is None:
        return None
    if isinstance(tooth, str):
        tooth = tooth.rsplit("_", 1)[-1]
    try:
        q, t = int(quadrant), int(tooth)
    except (TypeError, ValueError):
        return None
    # FDI notation: one quadrant digit (1-4) + one tooth digit (1-8).
    if 1 <= q <= 4 and 1 <= t <= 8:
        return f"{q}{t}"
    return None


# Singleton instance
ml_service = MLInferenceService()


def get_ml_service() -> MLInferenceService:
    """Dependency to get ML service instance."""
    return ml_service
