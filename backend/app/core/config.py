"""
Application configuration using Pydantic settings.
Loads environment variables from .env file.
"""
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import validator
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "DentalAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_JWKS_URL: str = ""
    
    # Security
    SECRET_KEY: str = "default_secret_key_for_development_jwt_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @validator("DEBUG", pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "debug", "dev")
        return bool(v)

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",")]
        return v

    def __init__(self, **values):
        super().__init__(**values)
        if not self.SUPABASE_KEY and self.SUPABASE_PUBLISHABLE_KEY:
            self.SUPABASE_KEY = self.SUPABASE_PUBLISHABLE_KEY
        if not self.SUPABASE_SERVICE_KEY and self.SUPABASE_SECRET_KEY:
            self.SUPABASE_SERVICE_KEY = self.SUPABASE_SECRET_KEY
    
    class Config:
        env_file = (
            str(Path(__file__).resolve().parents[2] / ".env"),
            ".env",
            "backend/.env",
        )
        case_sensitive = True
        extra = "ignore"


# Create global settings instance
settings = Settings()
