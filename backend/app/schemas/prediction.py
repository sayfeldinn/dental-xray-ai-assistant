"""
Flat prediction rows: what the ``predictions`` table stores and what the
Review / Treatment screens read.

``Finding`` (``app.schemas.scan``) nests its geometry in a ``bounding_box``
object; the frontend canvas draws from flat ``bbox_*`` columns. Both are
legit representations of the same detection, so every conversion between them
lives here -- including the tolerant coercion that keeps a single odd row from
500-ing an entire endpoint.
"""
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, Field, field_validator

from app.schemas.scan import (
    BoundingBox,
    Finding,
    FindingSeverityEnum,
    FindingTypeEnum,
)

FALLBACK_TYPE = FindingTypeEnum.OTHER
FALLBACK_SEVERITY = FindingSeverityEnum.MODERATE
FALLBACK_CONFIDENCE = 0.5

# Model class label -> (finding type, clinical severity proxy).
# The detector has no severity head, so severity is derived from the class:
# a periapical lesion drives endodontics, a pericoronal/impacted tooth drives
# surgical referral, plain caries is moderate.
CLASS_MAP: Dict[str, FindingTypeEnum] = {
    "caries": FindingTypeEnum.CARIES,
    "deep caries": FindingTypeEnum.CARIES,
    "cavity": FindingTypeEnum.CAVITY,
    "periapical": FindingTypeEnum.PERIAPICAL,
    "periapical lesion": FindingTypeEnum.PERIAPICAL,
    "pericoronal": FindingTypeEnum.PERICORONAL,
    "impacted": FindingTypeEnum.PERICORONAL,
    "inter-radicular": FindingTypeEnum.INTER_RADICULAR,
    "inter radicular": FindingTypeEnum.INTER_RADICULAR,
    "inter_radicular": FindingTypeEnum.INTER_RADICULAR,
    "non-odontogenic": FindingTypeEnum.NON_ODONTOGENIC,
    "non odontogenic": FindingTypeEnum.NON_ODONTOGENIC,
    "non_odontogenic": FindingTypeEnum.NON_ODONTOGENIC,
}

SEVERITY_BY_TYPE: Dict[FindingTypeEnum, FindingSeverityEnum] = {
    FindingTypeEnum.PERIAPICAL: FindingSeverityEnum.HIGH,
    FindingTypeEnum.CAVITY: FindingSeverityEnum.MEDIUM,
    FindingTypeEnum.CARIES: FindingSeverityEnum.MEDIUM,
    FindingTypeEnum.PERICORONAL: FindingSeverityEnum.MEDIUM,
    FindingTypeEnum.INTER_RADICULAR: FindingSeverityEnum.MEDIUM,
    FindingTypeEnum.NON_ODONTOGENIC: FindingSeverityEnum.LOW,
    FindingTypeEnum.ROOT_CANAL: FindingSeverityEnum.HIGH,
    FindingTypeEnum.EXTRACTION: FindingSeverityEnum.HIGH,
    FindingTypeEnum.OTHER: FindingSeverityEnum.LOW,
}


class PredictionResponse(BaseModel):
    """One detection, in the flat shape the frontend draws and patches."""

    id: str
    scan_id: str
    dentist_id: Optional[str] = None
    finding_type: str
    severity: str
    confidence: float = Field(..., ge=0, le=1)
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    tooth_number: Optional[str] = None
    notes: Optional[str] = None
    confirmed: bool = False
    confirmed_by: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, value: Any) -> Any:
        return coerce_confidence(value)

    @field_validator("bbox_width", "bbox_height", mode="before")
    @classmethod
    def _positive_size(cls, value: Any) -> Any:
        return coerce_positive(value)

    @field_validator("bbox_x", "bbox_y", mode="before")
    @classmethod
    def _non_negative(cls, value: Any) -> Any:
        return coerce_non_negative(value)


def coerce_confidence(value: Any, default: float = FALLBACK_CONFIDENCE) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return default
    if conf != conf:  # NaN
        return default
    return min(max(conf, 0.0), 1.0)


def coerce_non_negative(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number != number or number < 0:
        number = 0.0
    return number


def coerce_positive(value: Any) -> float:
    try:
        number = abs(float(value))
    except (TypeError, ValueError):
        number = 0.0
    if number != number or number == 0.0:
        number = 1.0
    return number


def coerce_finding_type(value: Any) -> FindingTypeEnum:
    if isinstance(value, FindingTypeEnum):
        return value
    if isinstance(value, Finding):
        return value.type
    label = str(value or "").strip().lower()
    if label in CLASS_MAP:
        return CLASS_MAP[label]
    try:
        return FindingTypeEnum(label)
    except ValueError:
        return FALLBACK_TYPE


def coerce_severity(value: Any, finding_type: Optional[FindingTypeEnum] = None) -> FindingSeverityEnum:
    if isinstance(value, FindingSeverityEnum):
        return value
    if value is not None:
        try:
            return FindingSeverityEnum(str(value).strip().lower())
        except ValueError:
            pass
    if finding_type is not None:
        return SEVERITY_BY_TYPE.get(finding_type, FALLBACK_SEVERITY)
    return FALLBACK_SEVERITY


def prediction_to_finding(row: Dict[str, Any]) -> Finding:
    """Convert a flat ``predictions`` row into a nested ``Finding``.

    Every field is coerced rather than trusted: a row with a unknown class
    label, a negative box or an out-of-range confidence degrades to a
    well-formed ``Finding`` instead of raising (which used to 500
    ``GET /recommendations/{scan_id}``).
    """
    finding_type = coerce_finding_type(row.get("finding_type"))
    bbox = BoundingBox(
        x=coerce_non_negative(row.get("bbox_x")),
        y=coerce_non_negative(row.get("bbox_y")),
        width=coerce_positive(row.get("bbox_width")),
        height=coerce_positive(row.get("bbox_height")),
    )
    return Finding(
        id=str(row["id"]) if row.get("id") is not None else None,
        type=finding_type,
        severity=coerce_severity(row.get("severity"), finding_type),
        confidence=coerce_confidence(row.get("confidence")),
        bounding_box=bbox,
        tooth_number=row.get("tooth_number") or None,
        description=row.get("notes") or row.get("description") or None,
        confirmed=bool(row.get("confirmed", False)),
        confirmed_by=row.get("confirmed_by") or None,
    )


def stable_prediction_id(scan_id: str, index: int) -> str:
    """Deterministic UUID5 for a derived prediction.

    ``feedback.finding_id`` is a UUID column, so ids we mint for findings that
    were never written to the ``predictions`` table must still be valid UUIDs.
    """
    return str(uuid5(NAMESPACE_URL, f"dentalai:prediction:{scan_id}:{index}"))


def findings_to_prediction_rows(
    findings: Iterable[Finding],
    scan_id: str,
    dentist_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Turn model ``Finding`` objects into insert-ready ``predictions`` rows."""
    rows: List[Dict[str, Any]] = []
    for index, finding in enumerate(findings):
        bbox = finding.bounding_box
        rows.append(
            {
                "id": finding.id or stable_prediction_id(scan_id, index),
                "scan_id": scan_id,
                "dentist_id": dentist_id,
                "finding_type": finding.type.value,
                "severity": finding.severity.value,
                "confidence": coerce_confidence(finding.confidence),
                "bbox_x": bbox.x,
                "bbox_y": bbox.y,
                "bbox_width": bbox.width,
                "bbox_height": bbox.height,
                "tooth_number": finding.tooth_number,
                "notes": finding.description,
                "confirmed": bool(finding.confirmed),
                "confirmed_by": finding.confirmed_by,
            }
        )
    return rows


def rows_to_predictions(rows: Iterable[Dict[str, Any]]) -> List[PredictionResponse]:
    """Validate DB rows into responses, dropping anything unusable."""
    predictions: List[PredictionResponse] = []
    for index, row in enumerate(rows):
        payload = dict(row)
        payload.setdefault("id", None)
        if not payload.get("id"):
            payload["id"] = stable_prediction_id(str(payload.get("scan_id") or "unknown"), index)
        try:
            predictions.append(PredictionResponse(**payload))
        except Exception:
            continue
    return predictions
