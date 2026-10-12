"""
DentalAI - Supabase Client Factory
Provides typed Supabase clients for database and storage operations.
"""

from supabase import create_client, Client
from .config import settings


def get_supabase_client(use_service_role: bool = False) -> Client:
    """
    Create a Supabase client instance.
    
    Args:
        use_service_role: If True, uses service_role key (bypasses RLS).
                         If False, uses anon key (respects RLS policies).
    
    Returns:
        Configured Supabase client
    """
    key = settings.SUPABASE_SERVICE_ROLE_KEY if use_service_role else settings.SUPABASE_ANON_KEY
    return create_client(settings.SUPABASE_URL, key)


# Default client instances
supabase_admin = get_supabase_client(use_service_role=True)
supabase_anon = get_supabase_client(use_service_role=False)
