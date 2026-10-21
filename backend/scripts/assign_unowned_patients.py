"""
Give patients that have no owner (dentist_id IS NULL, e.g. the seed/demo data created before
authentication existed) to one dentist, so they appear in that dentist's patient list.

    cd backend && python -m scripts.assign_unowned_patients --email dr@clinic.eg            # dry run
    cd backend && python -m scripts.assign_unowned_patients --email dr@clinic.eg --apply
"""

import argparse
import sys

from app.core.supabase_client import supabase_admin as db
from scripts.auth_admin import find_user


def main() -> int:
    parser = argparse.ArgumentParser(description="Assign unowned patients to a dentist")
    parser.add_argument("--email", required=True)
    parser.add_argument("--apply", action="store_true", help="Write the change (default is a dry run)")
    args = parser.parse_args()

    user = find_user(args.email)
    if not user:
        print(f"No user with email {args.email}", file=sys.stderr)
        return 1
    unowned = db.table("patients").select("id, first_name, last_name").is_("dentist_id", "null").execute().data
    for p in unowned:
        print(f"  {p['first_name']} {p['last_name']} ({p['id']})")
    if not args.apply:
        print(f"Dry run: {len(unowned)} unowned patient(s) would go to {args.email}. Re-run with --apply.")
        return 0
    if unowned:
        db.table("patients").update({"dentist_id": user["id"]}).is_("dentist_id", "null").execute()
    print(f"Assigned {len(unowned)} patient(s) to {args.email}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
