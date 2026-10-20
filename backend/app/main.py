"""
DentalAI - Main FastAPI Application
Clean backend service for IEEE IC-FTAI competition.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.domain.errors import ConflictError, NotFoundError, RuleViolationError
from app.api.v1 import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Assisted Clinical Decision-Support System for Dental Clinics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Detailed health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "supabase_configured": bool(settings.SUPABASE_URL),
        "ml_service_url": settings.ML_SERVICE_URL
    }


# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


def _domain_error_handler(status_code: int):
    async def handler(request: Request, exc: Exception):
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})
    return handler


app.add_exception_handler(NotFoundError, _domain_error_handler(404))
app.add_exception_handler(ConflictError, _domain_error_handler(409))
app.add_exception_handler(RuleViolationError, _domain_error_handler(422))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for uncaught errors.
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
