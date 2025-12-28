"""Authentication models for JWT validation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenPayload:
    """Decoded JWT payload from Better Auth."""
    sub: str  # User ID
    email: str
    iat: int  # Issued at (Unix timestamp)
    exp: int  # Expires at (Unix timestamp)
    iss: Optional[str] = None  # Issuer
    aud: Optional[str] = None  # Audience


@dataclass
class AuthenticatedUser:
    """User info extracted from validated JWT."""
    user_id: str
    email: str
