"""API routes."""
from app.api import auth, patients, scans, recommendations, ml_inference, feedback, treatments

__all__ = [
    "auth",
    "patients",
    "scans",
    "recommendations",
    "ml_inference",
    "feedback",
    "treatments",
]
