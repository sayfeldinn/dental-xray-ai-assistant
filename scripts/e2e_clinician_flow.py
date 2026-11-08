"""End-to-end clinician flow against a LOCAL stack (local Supabase + backend + ML).

sign up -> create/reuse a throwaway patient -> upload a panoramic -> analyze ->
list findings -> confirm one -> confirmed-findings gate -> re-analyze refusal.

Local only: it signs up a user with a known password and expects the local
Supabase env printed by `supabase start -o env` (default
/tmp/opencode/supabase_local.env). Do not point it at production.

    python scripts/e2e_clinician_flow.py

Environment overrides: BACKEND_URL, SUPABASE_LOCAL_ENV, E2E_EMAIL, E2E_PASSWORD,
E2E_IMAGE, E2E_OUT.
"""
import json
import os
import sys
from pathlib import Path

import requests

BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
ENV = Path(os.environ.get("SUPABASE_LOCAL_ENV", "/tmp/opencode/supabase_local.env"))
IMG = Path(os.environ.get(
    "E2E_IMAGE",
    "/home/sayfeldin/Projects/dental-model-research/data/raw/dentex/"
    "training_data/quadrant_enumeration/xrays/train_12.png"))
EMAIL = os.environ.get("E2E_EMAIL", "qa.e2e@dentalai.local")
PASSWORD = os.environ.get("E2E_PASSWORD", "Qa-e2e-local-2026!")
OUT = Path(os.environ.get("E2E_OUT", "/tmp/opencode/e2e_result.json"))


def load_local():
    if not ENV.exists():
        sys.exit(f"missing {ENV}; run `supabase start -o env` and save its output there")
    out = {}
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main():
    cfg = load_local()
    api = cfg.get("API_URL", "http://127.0.0.1:54321").rstrip("/")
    hdr = {"apikey": cfg["ANON_KEY"], "Content-Type": "application/json"}

    # 1) sign up (local confirmations are off) or sign in if the user exists
    r = requests.post(f"{api}/auth/v1/signup", headers=hdr,
                      json={"email": EMAIL, "password": PASSWORD,
                            "data": {"full_name": "QA E2E"}}, timeout=30)
    if r.status_code >= 400:
        r = requests.post(f"{api}/auth/v1/token?grant_type=password", headers=hdr,
                          json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    auth = r.json()
    token = auth["access_token"]
    dentist_id = auth["user"]["id"]
    print(f"auth ok: dentist {dentist_id} ({EMAIL})")
    auth_hdr = {"Authorization": f"Bearer {token}"}

    # 2) create (or reuse) a throwaway patient
    existing = requests.get(f"{BACKEND}/api/v1/patients", headers=auth_hdr,
                            params={"search": "Throwaway"}, timeout=30)
    patient = existing.json()["patients"][0] if existing.ok and existing.json()["patients"] else None
    if patient is None:
        pr = requests.post(f"{BACKEND}/api/v1/patients", headers=auth_hdr,
                           json={"first_name": "QA", "last_name": "Throwaway",
                                 "date_of_birth": "1990-01-01", "gender": "other",
                                 "phone": "+20 100 000 0000",
                                 "allergies": ["penicillin"],
                                 "notes": "Throwaway QA patient for the end-to-end flow."},
                           timeout=30)
        pr.raise_for_status()
        patient = pr.json()
    print(f"patient ok: {patient['id']} ({patient['first_name']} {patient['last_name']})")

    # 3) upload + analyze
    with IMG.open("rb") as fh:
        up = requests.post(f"{BACKEND}/api/v1/scans/upload", headers=auth_hdr,
                           files={"file": (IMG.name, fh, "image/png")},
                           data={"patient_id": patient["id"], "scan_type": "panoramic",
                                 "auto_analyze": "true", "confidence_threshold": "0.20"},
                           timeout=180)
    up.raise_for_status()
    scan = up.json()
    scan_id = scan["scan_id"]
    print(f"upload ok: scan {scan_id} status={scan['status']} findings={scan['findings_count']}")

    # 4) read the stored scan (signed URL + raw ML output)
    gs = requests.get(f"{BACKEND}/api/v1/scans/{scan_id}", headers=auth_hdr, timeout=30)
    gs.raise_for_status()
    stored = gs.json()
    raw = stored.get("raw_ml_output") or {}
    print(f"scan stored: status={stored['status']} "
          f"image_url={'signed' if 'token=' in (stored.get('image_url') or '') else 'missing'} "
          f"missing_teeth={len(raw.get('missing_teeth') or [])} "
          f"findings_advisory={len(raw.get('findings') or [])} "
          f"report={bool(stored.get('ai_report'))}")

    # 5) list findings
    fl = requests.get(f"{BACKEND}/api/v1/scans/{scan_id}/findings", headers=auth_hdr, timeout=30)
    fl.raise_for_status()
    findings = fl.json()["findings"]
    print(f"findings: {len(findings)}")
    for f in sorted(findings, key=lambda x: -x["disease_confidence"])[:8]:
        print(f"  - {f['tooth_fdi']:>3} {f['disease']:<20} "
              f"conf {f['disease_confidence']:.3f} status={f['review_status']}")
    if not findings:
        print("NO FINDINGS: cannot test the review gate on this image")
        return 1

    # 6) confirm the top finding
    top = max(findings, key=lambda f: f["disease_confidence"])
    rv = requests.post(f"{BACKEND}/api/v1/findings/review", headers=auth_hdr,
                       json={"finding_id": top["id"], "review_status": "confirmed",
                             "dentist_notes": "E2E check: confirmed by QA."}, timeout=30)
    rv.raise_for_status()
    reviewed = rv.json()
    print(f"review ok: {reviewed['tooth_fdi']} {reviewed['disease']} -> "
          f"{reviewed['review_status']} by {reviewed['reviewed_by']}")

    # 7) the clinical gate: confirmed findings are now available
    cf = requests.get(f"{BACKEND}/api/v1/findings/scan/{scan_id}/confirmed",
                      headers=auth_hdr, timeout=30)
    cf.raise_for_status()
    confirmed = cf.json()["findings"]
    print(f"confirmed gate: {len(confirmed)} finding(s) available for treatment planning")

    # 8) re-analyze must now be refused (409) because a finding was reviewed
    ra = requests.post(f"{BACKEND}/api/v1/scans/{scan_id}/reanalyze", headers=auth_hdr, timeout=30)
    print(f"reanalyze after review: HTTP {ra.status_code} "
          f"({'correctly refused' if ra.status_code == 409 else 'UNEXPECTED'})")

    out = {"dentist_id": dentist_id, "patient_id": patient["id"], "scan_id": scan_id,
           "findings": len(findings), "confirmed": len(confirmed),
           "reviewed_finding": reviewed["id"],
           "image_url_signed": "token=" in stored["image_url"],
           "missing_teeth": len(raw.get("missing_teeth") or []),
           "findings_advisory": len(raw.get("findings") or []),
           "ai_report_stored": bool(stored.get("ai_report"))}
    OUT.write_text(json.dumps(out, indent=2))
    print("\nE2E OK", json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
