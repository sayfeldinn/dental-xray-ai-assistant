"""
DentalAI - Core Configuration Management
Loads environment variables and provides typed settings access.
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "DentalAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_PROJECT_REF: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SECRET_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "xray-scans"
    
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
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = "../.env"  # Load from project root
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
