"""JWT validation middleware for Better Auth tokens.

This module provides FastAPI dependencies for validating JWTs issued by Better Auth
using JWKS (JSON Web Key Set) endpoint for public key retrieval.
"""

import os
from functools import lru_cache
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient

from models.auth import AuthenticatedUser, TokenPayload

load_dotenv()

# HTTP Bearer security scheme
# auto_error=False allows us to handle missing tokens ourselves
security = HTTPBearer(auto_error=False)


def get_better_auth_url() -> str:
    """Get the Better Auth URL from environment."""
    url = os.getenv("BETTER_AUTH_URL", "http://localhost:3000")
    return url.rstrip("/")


@lru_cache(maxsize=1)
def get_jwk_client() -> PyJWKClient:
    """
    Get cached JWKS client.
    
    The client is cached as a module-level singleton to avoid
    repeated JWKS endpoint calls. PyJWKClient handles key caching
    and rotation internally.
    """
    better_auth_url = get_better_auth_url()
    jwks_url = f"{better_auth_url}/api/auth/jwks"
    
    return PyJWKClient(
        jwks_url,
        cache_keys=True,
        lifespan=300,  # Cache keys for 5 minutes
    )


def verify_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, str]:
    """
    FastAPI dependency to verify JWT token and extract user info.
    
    This dependency:
    1. Extracts the Bearer token from Authorization header
    2. Fetches the signing key from Better Auth's JWKS endpoint
    3. Validates the JWT signature and claims
    4. Returns user info on success
    
    Args:
        credentials: HTTP Authorization credentials from Bearer token
        
    Returns:
        dict with user_id and email
        
    Raises:
        HTTPException 401 on missing, invalid, or expired token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Get signing key from JWKS
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        
        # Decode and validate JWT
        # Better Auth uses EdDSA (Ed25519) by default, but we also support RS256
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "RS256", "ES256"],
            options={
                "verify_aud": False,  # Better Auth may not set audience
                "verify_iss": False,  # We verify issuer separately if needed
            },
        )
        
        # Extract user info from claims
        user_id = payload.get("sub")
        email = payload.get("email", "")
        
        if not user_id:
            raise ValueError("Missing sub claim in JWT")
        
        return {"user_id": user_id, "email": email}
    
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_EXPIRED",
                "message": "Token has expired. Please sign in again.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except jwt.exceptions.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Invalid token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except Exception as e:
        # Log the error for debugging but don't expose details
        print(f"JWT validation error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Invalid token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    user_info: Dict[str, str] = Depends(verify_jwt_token),
) -> AuthenticatedUser:
    """
    FastAPI dependency to get the current authenticated user.
    
    This is a convenience wrapper around verify_jwt_token that
    returns an AuthenticatedUser dataclass.
    
    Args:
        user_info: User info from JWT validation
        
    Returns:
        AuthenticatedUser instance
    """
    return AuthenticatedUser(
        user_id=user_info["user_id"],
        email=user_info["email"],
    )
