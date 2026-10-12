"""API v1 routes."""

from fastapi import APIRouter
from .patients import router as patients_router
from .scans import router as scans_router
from .findings import router as findings_router

api_router = APIRouter()

api_router.include_router(patients_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)

__all__ = ['api_router']
