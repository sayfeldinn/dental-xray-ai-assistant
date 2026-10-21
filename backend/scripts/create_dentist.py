"""
Create a dentist account that can sign in immediately (email already confirmed).

    cd backend && python -m scripts.create_dentist --email dr@clinic.eg --name "Dr Sara Adel"

The password is read from the prompt (never pass it on the command line). Uses the service-role key,
so run it only on a trusted machine. Self sign-up in the UI also works, but needs email confirmation.
"""

import argparse
import getpass
import sys

from scripts.auth_admin import create_user


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Full name shown in the app")
    args = parser.parse_args()

    password = getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        print("Password too short", file=sys.stderr)
        return 1
    user = create_user(args.email, password, args.name)
    print(f"Created dentist {user['email']} ({user['id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
