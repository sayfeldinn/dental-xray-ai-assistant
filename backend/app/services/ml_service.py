"""
ML inference service for X-ray analysis.

The detector lives in a separate process (``ml/api``) so the web process never
imports torch -- that matters on machines where the CUDA build cannot load.
This module is the HTTP client for that service, plus a clearly-labelled mock
fallback so the API stays usable when the detector is not running.
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
from app.schemas.scan import BoundingBox, Finding, FindingSeverityEnum, FindingTypeEnum

# Classes the deployed detector can emit, in API-facing order.
SUPPORTED_FINDINGS: List[str] = [
    FindingTypeEnum.CARIES.value,
    FindingTypeEnum.PERIAPICAL.value,
    FindingTypeEnum.PERICORONAL.value,
    FindingTypeEnum.INTER_RADICULAR.value,
    FindingTypeEnum.NON_ODONTOGENIC.value,
]

_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".dcm": "application/dicom",
}


class MLInferenceService:
    """Client for the YOLO detection API, with a mock fallback."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: Optional[float] = None,
        allow_mock_fallback: Optional[bool] = None,
    ):
        url = settings.ML_API_URL if api_url is None else api_url
        self.api_url = (url or "").strip().rstrip("/")
        self.timeout = timeout if timeout is not None else settings.ML_TIMEOUT_SECONDS
        self.allow_mock_fallback = (
            settings.ML_ALLOW_MOCK_FALLBACK
            if allow_mock_fallback is None
            else allow_mock_fallback
        )
        self.model_version = "unconfigured" if not self.api_url else "unknown"
        self.last_error: Optional[str] = None
        self.last_latency_ms: Optional[float] = None

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    async def predict(
        self,
        image_source: str,
        confidence_threshold: float = 0.5,
    ) -> List[Finding]:
        """Run detection on an image given as a URL or a local path."""
        if not self.api_url:
            self.last_error = "ML_API_URL is not configured"
            self.model_version = "mock-v1.0"
            return self._mock_predict(confidence_threshold)

        started = time.perf_counter()
        try:
            image_bytes, content_type = await self._load_image(image_source)
            detections = await self._call_api(
                image_bytes, content_type, confidence_threshold
            )
            self.last_error = None
            self.last_latency_ms = round((time.perf_counter() - started) * 1000, 1)
        except Exception as exc:  # noqa: BLE001 - one place decides the fallback
            self.last_error = str(exc)
            self.last_latency_ms = round((time.perf_counter() - started) * 1000, 1)
            if not self.allow_mock_fallback:
                raise
            self.model_version = "mock-v1.0"
            return self._mock_predict(confidence_threshold)

        self.model_version = "yolov8s-dental-1.0"
        findings = [f for f in (_to_finding(d) for d in detections) if f is not None]
        return [f for f in findings if f.confidence >= confidence_threshold]

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
        """Model metadata for ``GET /ml/model-info``."""
        if not self.api_url:
            mode = "mock"
        elif self.model_version.startswith("mock"):
            mode = "mock"
        else:
            mode = "live"
        return {
            "model_version": self.model_version,
            "model_loaded": bool(self.api_url),
            "mode": mode,
            "ml_api_url": self.api_url or None,
            "reachable": None if self.api_url else False,
            "supported_findings": SUPPORTED_FINDINGS,
            "confidence_threshold": settings.ML_DEFAULT_CONFIDENCE,
            "last_error": self.last_error,
            "last_latency_ms": self.last_latency_ms,
            "mock_fallback_enabled": self.allow_mock_fallback,
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
    ) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/predict",
                # The detector applies the same floor server-side, so the
                # threshold the caller asked for is the one that takes effect.
                params={"conf": confidence_threshold},
                files={"file": ("xray", image_bytes, content_type)},
            )
            response.raise_for_status()
            payload = response.json()

        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("predictions", "detections", "results"):
                if key in payload and isinstance(payload[key], list):
                    return payload[key]
        raise ValueError(f"unexpected detector response: {type(payload).__name__}")

    # ------------------------------------------------------------------ #
    # fallback
    # ------------------------------------------------------------------ #
    @staticmethod
    def _mock_predict(confidence_threshold: float) -> List[Finding]:
        mock_findings = [
            Finding(
                type=FindingTypeEnum.CAVITY,
                severity=FindingSeverityEnum.MEDIUM,
                confidence=0.87,
                bounding_box=BoundingBox(x=120, y=450, width=45, height=40),
                tooth_number="14",
                description="Cavity detected on upper right first molar",
                ai_generated=True,
                confirmed=False,
            ),
            Finding(
                type=FindingTypeEnum.CAVITY,
                severity=FindingSeverityEnum.LOW,
                confidence=0.72,
                bounding_box=BoundingBox(x=520, y=380, width=35, height=38),
                tooth_number="26",
                description="Small cavity detected on upper left first molar",
                ai_generated=True,
                confirmed=False,
            ),
            Finding(
                type=FindingTypeEnum.ROOT_CANAL,
                severity=FindingSeverityEnum.HIGH,
                confidence=0.91,
                bounding_box=BoundingBox(x=280, y=520, width=50, height=55),
                tooth_number="36",
                description="Periapical lesion detected, root canal may be required",
                ai_generated=True,
                confirmed=False,
            ),
        ]
        return [f for f in mock_findings if f.confidence >= confidence_threshold]


def _to_finding(detection: Dict[str, Any]) -> Optional[Finding]:
    """Map one detector response onto a ``Finding``.

    Understands the v1 contract (``class_name`` + ``bbox.xmin/ymin/xmax/ymax``)
    and the multi-model contract (``disease`` + ``quadrant``/``tooth`` +
    ``disease_bbox``), so either deployment can back this API.
    """
    if not isinstance(detection, dict):
        return None

    label = detection.get("class_name") or detection.get("disease") or detection.get("type")
    if label is None:
        return None

    finding_type = coerce_finding_type(label)
    severity = coerce_severity(detection.get("severity"), finding_type)
    confidence = coerce_confidence(detection.get("confidence"))

    bbox = detection.get("bbox") or detection.get("disease_bbox") or detection
    if all(key in bbox for key in ("xmin", "ymin", "xmax", "ymax")):
        x = coerce_non_negative(bbox.get("xmin"))
        y = coerce_non_negative(bbox.get("ymin"))
        width = coerce_positive(float(bbox.get("xmax", 0)) - float(bbox.get("xmin", 0)))
        height = coerce_positive(float(bbox.get("ymax", 0)) - float(bbox.get("ymin", 0)))
    else:
        x = coerce_non_negative(bbox.get("x", bbox.get("xmin")))
        y = coerce_non_negative(bbox.get("y", bbox.get("ymin")))
        width = coerce_positive(bbox.get("width", bbox.get("w")))
        height = coerce_positive(bbox.get("height", bbox.get("h")))

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


def _tooth_number(detection: Dict[str, Any]) -> Optional[str]:
    """FDI notation from a quadrant/tooth pair, when the model reports one."""
    explicit = detection.get("tooth_number") or detection.get("fdi")
    if explicit:
        return str(explicit)
    quadrant = detection.get("quadrant")
    tooth = detection.get("tooth")
    if quadrant is None or tooth is None:
        return None
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
