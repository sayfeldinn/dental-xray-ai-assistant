"""
Authentication endpoints using Supabase Auth.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from supabase import Client
from app.core.supabase import get_supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignUpRequest(BaseModel):
    """Sign up request schema."""
    email: EmailStr
    password: str
    full_name: str


class SignInRequest(BaseModel):
    """Sign in request schema."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response schema."""
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    request: SignUpRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Register a new dentist user.
    """
    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sign up failed. Email may already be registered."
            )
        
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": request.full_name
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sign up failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
@router.post("/signin", response_model=AuthResponse)
async def sign_in(
    request: SignInRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Sign in an existing dentist user.
    """
    try:
        # Sign in with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": auth_response.user.user_metadata.get("full_name", "")
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sign in failed: {str(e)}"
        )


@router.post("/signout")
async def sign_out(supabase: Client = Depends(get_supabase)):
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sign out failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(supabase: Client = Depends(get_supabase)):
    """Get current authenticated user information."""
    try:
        user = supabase.auth.get_user()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        return {
            "id": user.user.id,
            "email": user.user.email,
            "full_name": user.user.user_metadata.get("full_name", "")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
