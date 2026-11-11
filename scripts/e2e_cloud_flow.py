"""Pre-demo check: the full clinician flow against the live Supabase project.

Runs every step of the 6-step loop through the running backend (default
http://127.0.0.1:8000, e.g. `docker compose up`): sign-in, access isolation, upload +
AI analysis, review gate, treatment plan with drug-safety checks, dentist decisions and
the feedback ledger. It creates a throwaway dentist with a random password, deletes
everything it created at the end (even on failure), and checks the table row counts
are back where they started. Exit code 0 means every check passed.

    backend/venv/bin/python scripts/e2e_cloud_flow.py .env /path/to/val_28.png

The expectations (tooth 36 periapical lesion, 27 and 46 caries) are specific to the
DENTEX validation image val_28.png, which the model never trained on.
"""
import json
import os
import secrets
import sys
import time

import httpx

ENV_PATH, IMAGE = sys.argv[1], sys.argv[2]
BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/") + "/api/v1"

env = {}
for line in open(ENV_PATH):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SB = env["SUPABASE_URL"].rstrip("/")
SERVICE, ANON = env["SUPABASE_SERVICE_ROLE_KEY"], env["SUPABASE_ANON_KEY"]
admin = {"apikey": SERVICE, "Authorization": f"Bearer {SERVICE}"}
TABLES = ["patients", "scans", "findings", "treatments", "prescriptions", "clinical_feedback_logs"]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def counts():
    out = {}
    for t in TABLES:
        r = httpx.get(f"{SB}/rest/v1/{t}?select=id", headers={**admin, "Prefer": "count=exact", "Range": "0-0"})
        out[t] = int(r.headers["content-range"].split("/")[-1])
    return out


before = counts()
print("row counts before:", before)

email = f"qa-e2e-{secrets.token_hex(4)}@dentalai.test"
password = secrets.token_urlsafe(24)
user_id = scan_id = patient_id = None
c = httpx.Client(timeout=180)
try:
    r = c.post(f"{SB}/auth/v1/admin/users", headers=admin,
               json={"email": email, "password": password, "email_confirm": True,
                     "user_metadata": {"full_name": "QA E2E (temporary)"}})
    r.raise_for_status()
    user_id = r.json()["id"]
    r = c.post(f"{SB}/auth/v1/token?grant_type=password", headers={"apikey": ANON},
               json={"email": email, "password": password})
    r.raise_for_status()
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}
    check("sign in with Supabase Auth", True, email)

    # --- security -------------------------------------------------------------
    check("unauthenticated request is refused", c.get(f"{BACKEND}/patients").status_code == 401)
    mine = c.get(f"{BACKEND}/patients", headers=H).json()
    check("new dentist sees none of the existing patients", mine["total"] == 0, f"total={mine['total']}")
    other = httpx.get(f"{SB}/rest/v1/patients?select=id&limit=1", headers=admin).json()
    if other:
        code = c.get(f"{BACKEND}/patients/{other[0]['id']}", headers=H).status_code
        check("another dentist's patient cannot be opened", code in (403, 404), f"HTTP {code}")
    direct = httpx.get(f"{SB}/rest/v1/patients?select=id", headers={"apikey": ANON, "Authorization": f"Bearer {token}"})
    check("direct database read with the user's token returns nothing (RLS)", direct.json() == [], direct.text[:60])

    # --- step 1-2: upload + AI analysis ----------------------------------------
    r = c.post(f"{BACKEND}/patients", headers=H, json={
        "first_name": "QA", "last_name": "Temporary", "date_of_birth": "1985-03-02", "gender": "other",
        "allergies": ["penicillin"], "medical_conditions": [], "current_medications": [],
        "notes": "Temporary E2E patient; deleted by the test."})
    r.raise_for_status()
    patient_id = r.json()["id"]
    check("create patient (penicillin allergy)", True)

    t0 = time.time()
    with open(IMAGE, "rb") as fh:
        r = c.post(f"{BACKEND}/scans/upload", headers=H,
                   files={"file": ("val_28.png", fh, "image/png")},
                   data={"patient_id": patient_id, "confidence_threshold": "0.20"})
    up = r.json()
    scan_id = up.get("scan_id")
    check("upload + AI analysis", r.status_code == 201 and up["status"] == "analyzed",
          f"{up.get('findings_count')} findings in {time.time() - t0:.1f}s")

    scan = c.get(f"{BACKEND}/scans/{scan_id}", headers=H).json()
    raw = scan["raw_ml_output"]
    check("AI report stored", bool(scan.get("ai_report")))
    check("model provenance stored", raw["model"]["pipeline_version"] == "v3")
    img = httpx.get(scan["image_url"], timeout=60)
    check("X-ray served through a signed URL", img.status_code == 200 and img.content[:4] == b"\x89PNG",
          f"{len(img.content)} bytes")
    unsigned = scan["image_url"].split("?")[0].replace("/object/sign/", "/object/public/")
    check("X-ray is not publicly readable", httpx.get(unsigned, timeout=30).status_code >= 400)

    findings = c.get(f"{BACKEND}/scans/{scan_id}/findings", headers=H).json()["findings"]
    by = {(f["tooth_fdi"], f["disease"]): f for f in findings}
    check("findings carry FDI tooth + box", all(f["tooth_fdi"] and len(f["box"]) == 4 for f in findings),
          ", ".join(sorted(f"{k[0]} {k[1]}" for k in by)))

    # --- step 3: dentist review -------------------------------------------------
    gate = c.get(f"{BACKEND}/findings/scan/{scan_id}/confirmed", headers=H).json()
    check("nothing reaches planning before review", gate["total"] == 0)
    pa = by.get(("36", "Periapical Lesion"))
    fp = by.get(("27", "Caries"))
    wrong = by.get(("46", "Caries"))
    r1 = c.post(f"{BACKEND}/findings/review", headers=H, json={"finding_id": pa["id"], "review_status": "confirmed"})
    r2 = c.post(f"{BACKEND}/findings/review", headers=H, json={"finding_id": fp["id"], "review_status": "rejected",
                                                                "dentist_notes": "No lesion visible."})
    r3 = c.post(f"{BACKEND}/findings/review", headers=H, json={"finding_id": wrong["id"], "review_status": "modified",
                                                                "confirmed_disease": "Periapical Lesion"})
    check("confirm / reject / correct findings", [r.status_code for r in (r1, r2, r3)] == [200, 200, 200],
          f"36 PA confirmed, 27 caries rejected, 46 caries -> periapical")
    check("review is stamped with the dentist", r1.json()["reviewed_by"] == user_id)
    gate = c.get(f"{BACKEND}/findings/scan/{scan_id}/confirmed", headers=H).json()
    check("only confirmed/corrected findings reach planning", gate["total"] == 2, f"total={gate['total']}")
    re = c.post(f"{BACKEND}/scans/{scan_id}/reanalyze", headers=H)
    check("re-analysis refused once reviewed", re.status_code == 409)

    # --- step 4: recommendations -----------------------------------------------
    r = c.post(f"{BACKEND}/recommendations/scans/{scan_id}", headers=H,
               json={"clinical_context": {"active_infection": True, "pain": True}})
    plans = r.json()["plans"]
    drugs = [rx["drug_name"] for p in plans for rx in p["prescriptions"]]
    codes = {w["code"] for p in plans for rx in p["prescriptions"] for w in rx["contraindication_warnings"]}
    check("treatment plan generated", r.status_code == 201 and len(plans) == 2,
          "; ".join(f"{p['treatment']['treatment_category']}" for p in plans))
    check("penicillin allergy -> no amoxicillin, clindamycin substituted",
          "Amoxicillin" not in drugs and "Clindamycin" in drugs and "FIRST_LINE_EXCLUDED" in codes,
          f"drugs={drugs}")

    # --- step 5: dentist decisions ---------------------------------------------
    clinda = next(rx for p in plans for rx in p["prescriptions"] if rx["drug_name"] == "Clindamycin")
    bare = c.post(f"{BACKEND}/prescriptions/{clinda['id']}/decision", headers=H, json={"decision": "accepted"})
    check("warning cannot be accepted silently", bare.status_code in (409, 422), f"HTTP {bare.status_code}")
    ok = c.post(f"{BACKEND}/prescriptions/{clinda['id']}/decision", headers=H,
                json={"decision": "accepted", "acknowledge_warnings": True})
    check("accepted after acknowledging the warning", ok.status_code == 200, ok.json().get("dentist_status"))
    amox = c.post(f"{BACKEND}/prescriptions/check", headers=H, json={
        "patient_id": patient_id, "drug_name": "Amoxicillin", "indication_type": "active_infection",
        "dosage": "500 mg", "frequency": "every 8 hours"})
    check("manual amoxicillin is flagged contraindicated", amox.json().get("status") == "contraindicated")
    tr = plans[0]["treatment"]
    d = c.post(f"{BACKEND}/treatments/{tr['id']}/decision", headers=H, json={"decision": "confirmed"})
    check("treatment confirmed", d.status_code == 200 and d.json()["status"] == "confirmed")

    # --- step 6: feedback ledger -------------------------------------------------
    # Only departures from the AI are logged: the reject and the relabel, not the confirmation.
    fb = c.get(f"{BACKEND}/feedback", headers=H, params={"scan_id": scan_id}).json()
    kinds = sorted(e["correction_type"] for e in fb["logs"])
    check("feedback ledger records each departure from the AI", kinds == ["false_positive", "misclassification"],
          f"{kinds}")
except Exception as exc:  # report, then still clean up
    import traceback
    traceback.print_exc()
    check("flow completed without an exception", False, repr(exc)[:200])
finally:
    if scan_id:
        code = c.delete(f"{BACKEND}/scans/{scan_id}", headers=H).status_code
        check("cleanup: delete scan (cascade + stored image)", code == 204, f"HTTP {code}")
    if patient_id:
        code = c.delete(f"{BACKEND}/patients/{patient_id}", headers=H).status_code
        check("cleanup: delete patient", code == 204, f"HTTP {code}")
    if user_id:
        code = httpx.delete(f"{SB}/auth/v1/admin/users/{user_id}", headers=admin).status_code
        check("cleanup: delete test dentist", code == 200, f"HTTP {code}")
    after = counts()
    check("database row counts restored", after == before, json.dumps(after))

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
