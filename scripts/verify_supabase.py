#!/usr/bin/env python3
"""
DentalAI - Supabase Connectivity & Schema Verification Script
Tests REST API connectivity, authentication keys, and checks table presence
using standard library urllib (no pip dependencies required).
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Load environment variables from .env if present
def load_dotenv(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    env_file = os.path.join(root_dir, ".env")
    load_dotenv(env_file)

    supabase_url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    print("=" * 65)
    print("DentalAI — Supabase Health & Schema Verification")
    print("=" * 65)

    if not supabase_url or not anon_key:
        print("[FAIL] Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment.")
        sys.exit(1)

    print(f"[*] Supabase URL: {supabase_url}")
    print(f"[*] Anon Key:     {anon_key[:15]}...{anon_key[-8:]}")
    if service_role_key:
        print(f"[*] Service Key:  {service_role_key[:15]}...{service_role_key[-8:]}")
    print("-" * 65)

    # 1. Test REST endpoint connectivity
    rest_url = f"{supabase_url.rstrip('/')}/rest/v1/"
    req = urllib.request.Request(
        rest_url,
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.getcode()
            print(f"[PASS] Supabase REST API connected successfully (HTTP {status_code}).")
    except urllib.error.HTTPError as e:
        print(f"[INFO] REST endpoint responded with HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"[FAIL] Could not connect to Supabase: {e.reason}")
        print("       Check internet connection or Supabase URL.")
        sys.exit(1)

    # 2. Check clinical tables
    tables = ["patients", "scans", "findings", "treatments", "prescriptions", "clinical_feedback_logs"]
    key_to_use = service_role_key or anon_key

    print("-" * 65)
    print("[*] Checking clinical tables in Supabase:")
    
    missing_tables = []
    for table in tables:
        tbl_url = f"{supabase_url.rstrip('/')}/rest/v1/{table}?select=id&limit=1"
        tbl_req = urllib.request.Request(
            tbl_url,
            headers={
                "apikey": key_to_use,
                "Authorization": f"Bearer {key_to_use}",
                "Range": "0-0"
            }
        )
        try:
            with urllib.request.urlopen(tbl_req, timeout=10) as tbl_resp:
                print(f"  [+] Table '{table}' exists and is accessible.")
        except urllib.error.HTTPError as e:
            if e.code == 404 or "relation" in str(e.read()):
                print(f"  [-] Table '{table}' is NOT found in database.")
                missing_tables.append(table)
            else:
                print(f"  [?] Table '{table}' check returned HTTP {e.code} ({e.reason}).")
        except Exception as e:
            print(f"  [!] Table '{table}' check error: {e}")

    # 3. Storage bucket check
    storage_url = f"{supabase_url.rstrip('/')}/storage/v1/bucket/xray-scans"
    stg_req = urllib.request.Request(
        storage_url,
        headers={
            "apikey": key_to_use,
            "Authorization": f"Bearer {key_to_use}"
        }
    )
    try:
        with urllib.request.urlopen(stg_req, timeout=10) as stg_resp:
            print(f"  [+] Storage bucket 'xray-scans' exists.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  [-] Storage bucket 'xray-scans' not found.")
        else:
            print(f"  [?] Storage bucket check returned HTTP {e.code}.")
    except Exception as e:
        print(f"  [!] Storage bucket check error: {e}")

    print("=" * 65)
    if missing_tables:
        print(f"[ACTION REQUIRED] {len(missing_tables)} tables need to be created.")
        print("Please copy the contents of 'supabase/schema.sql' and run it in:")
        print(f"https://supabase.com/dashboard/project/{os.environ.get('SUPABASE_PROJECT_REF', 'vudxogycxfaarnirtxhf')}/sql")
    else:
        print("[SUCCESS] All tables are configured and ready for Phase 2!")
    print("=" * 65)

if __name__ == "__main__":
    main()

