"""
Supabase client initialization and helper functions.
"""
from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Singleton Supabase client wrapper."""
    
    _instance: Client = None
    _service_instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get Supabase client with anon key (for user operations)."""
        if cls._instance is None:
            cls._instance = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
        return cls._instance
    
    @classmethod
    def get_service_client(cls) -> Client:
        """Get Supabase client with service role key (for admin operations)."""
        if cls._service_instance is None:
            cls._service_instance = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
        return cls._service_instance


def get_supabase() -> Client:
    """Dependency to get Supabase client."""
    return SupabaseClient.get_client()


def get_supabase_service() -> Client:
    """Dependency to get Supabase service client."""
    return SupabaseClient.get_service_client()
