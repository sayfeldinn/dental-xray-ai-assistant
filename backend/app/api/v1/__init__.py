"""API v1 routes."""

from fastapi import APIRouter, Depends

from app.core.auth import get_current_dentist
from .patients import router as patients_router
from .scans import router as scans_router
from .findings import router as findings_router
from .recommendations import router as recommendations_router
from .treatments import router as treatments_router
from .prescriptions import router as prescriptions_router
from .feedback import router as feedback_router

# Every v1 route requires a signed-in dentist; routes that need the identity also declare it.
api_router = APIRouter(dependencies=[Depends(get_current_dentist)])

api_router.include_router(patients_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)
api_router.include_router(recommendations_router)
api_router.include_router(treatments_router)
api_router.include_router(prescriptions_router)
api_router.include_router(feedback_router)

__all__ = ['api_router']
