"""
DentalAI - Authentication
Every /api/v1 request carries a Supabase Auth access token (Authorization: Bearer <jwt>).
The token is verified locally against the project's public signing keys (JWKS, cached), so no
call to Supabase is made per request. The dentist's id (the token's `sub`) is what every write is
stamped with and what every read is scoped to (see app/services/access.py).
"""

from functools import lru_cache
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


class AuthenticatedDentist(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None


class InvalidToken(Exception):
    pass


class TokenVerifier:
    """Verifies Supabase access tokens: signature, expiry, audience and issuer."""

    def __init__(self, issuer: str, jwt_secret: str = ""):
        self.issuer = issuer
        self.jwt_secret = jwt_secret
        self._jwks = jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True, lifespan=3600)

    def verify(self, token: str) -> AuthenticatedDentist:
        try:
            alg = jwt.get_unverified_header(token).get("alg")
            if alg == "HS256":
                if not self.jwt_secret:
                    raise InvalidToken("HS256 tokens need SUPABASE_JWT_SECRET")
                key = self.jwt_secret
            else:
                key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=["ES256", "RS256", "HS256"],
                                audience="authenticated", issuer=self.issuer)
        except InvalidToken:
            raise
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc
        if claims.get("role") != "authenticated" or not claims.get("sub"):
            raise InvalidToken("Not an authenticated user token")
        meta = claims.get("user_metadata") or {}
        return AuthenticatedDentist(id=claims["sub"], email=claims.get("email"), full_name=meta.get("full_name"))


@lru_cache
def get_token_verifier() -> TokenVerifier:
    return TokenVerifier(settings.auth_issuer, settings.SUPABASE_JWT_SECRET)


def get_current_dentist(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> AuthenticatedDentist:
    """FastAPI dependency (sync, so the first JWKS fetch runs in the threadpool). 401 when missing or invalid."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    try:
        return verifier.verify(credentials.credentials)
    except InvalidToken:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid; sign in again",
                            headers={"WWW-Authenticate": "Bearer"})
