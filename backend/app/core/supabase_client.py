"""
DentalAI - Supabase Client Factory
Provides the service-role client used by the backend for all database and storage operations.

The backend always authenticates requests itself (JWT verification in core/auth.py) and then acts
with the service-role key; there is no anon-key (RLS-respecting) code path, so only one client is
provided.
"""

from supabase import create_client, Client
from .config import settings


def get_supabase_client() -> Client:
    """Create the service-role Supabase client (bypasses RLS; the backend enforces ownership itself)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# Default client instance
supabase_admin = get_supabase_client()
