"""
DentalAI - Core Configuration Management
Loads environment variables and provides typed settings access.
"""

import json
from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List

# Repo root = backend/app/core/ -> up three levels. Resolved from this file so settings load
# regardless of the process working directory (the old "../.env" only worked from backend/).
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "DentalAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Supabase. Only these two are required by the backend at runtime.
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    # Kept for parity with .env.example / the frontend, but unused server-side.
    SUPABASE_PROJECT_REF: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "xray-scans"
    # Only for projects still on the legacy shared-secret (HS256) JWTs; projects with asymmetric
    # signing keys are verified against the public JWKS and need no secret.
    SUPABASE_JWT_SECRET: str = ""
    SIGNED_URL_TTL_SECONDS: int = 3600
    MAX_UPLOAD_MB: int = 20
    
    # AI Microservice (dentex_week3)
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_TIMEOUT_SECONDS: int = 60
    ML_DEFAULT_CONFIDENCE: float = 0.20
    
    # Backend API
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"]'
    
    @property
    def auth_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except Exception:
            return ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = str(_REPO_ROOT / ".env")  # repo-root .env, CWD-independent
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
