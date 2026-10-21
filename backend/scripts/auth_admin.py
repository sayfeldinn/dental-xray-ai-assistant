"""
Minimal Supabase Auth admin client (service-role key) for the maintenance scripts.
Plain HTTP on purpose: the auth admin calls in the pinned supabase-py/gotrue combination are unreliable.
"""

from typing import Optional

import httpx

from app.core.config import settings


def _client() -> httpx.Client:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return httpx.Client(base_url=f"{settings.auth_issuer}/admin", timeout=20,
                        headers={"apikey": key, "Authorization": f"Bearer {key}"})


def create_user(email: str, password: str, full_name: str) -> dict:
    with _client() as c:
        r = c.post("/users", json={"email": email, "password": password, "email_confirm": True,
                                   "user_metadata": {"full_name": full_name}})
        r.raise_for_status()
        return r.json()


def find_user(email: str) -> Optional[dict]:
    page = 1
    with _client() as c:
        while True:
            r = c.get("/users", params={"page": page, "per_page": 200})
            r.raise_for_status()
            users = r.json().get("users", [])
            if not users:
                return None
            match = next((u for u in users if (u.get("email") or "").lower() == email.lower()), None)
            if match:
                return match
            page += 1


def delete_user(user_id: str) -> None:
    with _client() as c:
        c.delete(f"/users/{user_id}").raise_for_status()
