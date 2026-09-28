"""
Ownership-checked record lookups shared by the API routes.

Every patient/scan read goes through here so a record that does not exist and
a record that belongs to another dentist are indistinguishable to the caller.
"""
from typing import Any, Dict

from fastapi import HTTPException, status
from supabase import Client


def require_record(
    supabase: Client,
    table: str,
    record_id: str,
    dentist_id: str,
    label: str,
) -> Dict[str, Any]:
    """Fetch a row scoped to the signed-in dentist or raise 404."""
    try:
        result = (
            supabase.table(table)
            .select("*")
            .eq("id", record_id)
            .eq("dentist_id", dentist_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} not found",
        ) from exc

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} not found",
        )
    return result.data


def require_scan(supabase: Client, scan_id: str, dentist_id: str) -> Dict[str, Any]:
    """Fetch a scan owned by the signed-in dentist."""
    return require_record(supabase, "scans", scan_id, dentist_id, "Scan")


def require_patient(supabase: Client, patient_id: str, dentist_id: str) -> Dict[str, Any]:
    """Fetch a patient owned by the signed-in dentist."""
    return require_record(supabase, "patients", patient_id, dentist_id, "Patient")
