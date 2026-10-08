"""
Persistence for the ``predictions`` rows the Review screen renders.

Reads prefer the ``predictions`` table and fall back to the ``scans.findings``
JSONB column, so scans analysed before the table existed still show boxes
instead of an empty canvas.
"""
from typing import Any, Dict, List, Optional

from supabase import Client

from app.schemas.prediction import findings_to_prediction_rows, prediction_to_finding
from app.schemas.scan import Finding

TABLE = "predictions"


def as_findings(raw: Any) -> List[Finding]:
    """Coerce stored ``scans.findings`` entries into ``Finding`` objects.

    Accepts both the nested ``bounding_box`` shape this API writes and the
    flat ``bbox_*`` shape a prediction row uses, tolerating one bad entry.
    """
    findings: List[Finding] = []
    for item in raw or []:
        if isinstance(item, Finding):
            findings.append(item)
            continue
        if not isinstance(item, dict):
            continue
        try:
            if "bounding_box" in item or "type" in item:
                findings.append(Finding(**item))
            else:
                findings.append(prediction_to_finding(item))
        except Exception:
            continue
    return findings


async def load_prediction_rows(
    supabase: Client,
    scan: Dict[str, Any],
    dentist_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return raw prediction rows for a scan (table first, JSONB fallback)."""
    rows: List[Dict[str, Any]] = []
    try:
        result = (
            supabase.table(TABLE)
            .select("*")
            .eq("scan_id", scan.get("id"))
            .execute()
        )
        rows = result.data or []
    except Exception:
        rows = []

    if not rows:
        rows = findings_to_prediction_rows(
            as_findings(scan.get("findings")),
            scan_id=str(scan.get("id") or ""),
            dentist_id=dentist_id or scan.get("dentist_id"),
        )
    return rows


async def save_predictions(
    supabase: Client,
    scan: Dict[str, Any],
    dentist_id: Optional[str],
    findings: List[Finding],
) -> Optional[str]:
    """Replace a scan's predictions with fresh model output.

    Returns a warning string when the write could not be completed (for
    example the ``predictions`` table has not been migrated yet); ``None``
    means the rows were stored. Callers surface the warning rather than
    failing the request -- the response still carries the detections.
    """
    scan_id = str(scan.get("id") or "")
    if not scan_id:
        return "scan has no id"

    rows = findings_to_prediction_rows(findings, scan_id=scan_id, dentist_id=dentist_id)
    try:
        # Delete ALL existing predictions for this scan first to ensure clean slate.
        # This is critical when switching models or when the new model detects
        # fewer findings than the old one - we don't want stale detections from
        # a previous model (e.g., caries from old model) to persist when the
        # current model (dentex_week3) only detects impacted teeth.
        supabase.table(TABLE).delete().eq("scan_id", scan_id).execute()
        
        # Now insert the fresh predictions
        if rows:
            supabase.table(TABLE).insert(rows).execute()
    except Exception as exc:
        return str(exc)
    return None


async def save_scan_findings(
    supabase: Client,
    scan_id: str,
    findings: List[Finding],
    status: str = "completed",
    updated_at: Optional[str] = None,
    ai_report: Optional[str] = None,
    quadrants: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """Mirror detections onto the scan row (``scans.findings`` + status).

    The detector's clinical report and quadrant boxes ride along here because
    neither has a column in ``predictions``; they describe the scan as a whole.
    """
    payload: Dict[str, Any] = {"findings": [f.model_dump(mode="json") for f in findings]}
    if status:
        payload["status"] = status
    if updated_at:
        payload["updated_at"] = updated_at

    extras: Dict[str, Any] = {}
    if ai_report is not None:
        extras["ai_report"] = ai_report
    if quadrants is not None:
        extras["quadrants"] = quadrants

    try:
        supabase.table("scans").update({**payload, **extras}).eq("id", scan_id).execute()
        return None
    except Exception as exc:
        if not extras:
            return str(exc)
        # `ai_report` / `quadrants` need PART 5 of
        # docs/supabase_predictions_migration.sql. Losing the report is
        # acceptable; losing the findings and the status is not, so retry
        # without them and report what happened.
        try:
            supabase.table("scans").update(payload).eq("id", scan_id).execute()
        except Exception as retry_exc:
            return str(retry_exc)
        return (
            "findings stored, but the clinical report could not be saved "
            f"({exc}). Apply PART 5 of docs/supabase_predictions_migration.sql."
        )
