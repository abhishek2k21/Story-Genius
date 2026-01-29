"""
Authentication Module
JWT and API key authentication.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# JWT settings
JWT_SECRET = getattr(settings, "jwt_secret", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


# ========================
# Models
# ========================

class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    email: Optional[str] = None
    exp: datetime


class UserAuth(BaseModel):
    """Authenticated user."""
    user_id: str
    email: Optional[str] = None
    is_authenticated: bool = True


# ========================
# Password Utilities
# ========================

def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against hash."""
    return pwd_context.verify(plain, hashed)


# ========================
# JWT Utilities
# ========================

def create_access_token(user_id: str, email: Optional[str] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
        )
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


# ========================
# API Key Storage (simple in-memory)
# ========================

# In production, use database
_api_keys: dict[str, str] = {
    # api_key -> user_id
}


def register_api_key(user_id: str) -> str:
    """Generate and register an API key for a user."""
    api_key = secrets.token_urlsafe(32)
    _api_keys[api_key] = user_id
    return api_key


def validate_api_key(api_key: str) -> Optional[str]:
    """Validate API key and return user_id."""
    return _api_keys.get(api_key)


# ========================
# FastAPI Dependencies
# ========================

async def get_current_user(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserAuth:
    """
    Get current authenticated user.

    Checks:
    1. API key in X-API-Key header
    2. Bearer token in Authorization header
    """
    # Check API key
    if api_key:
        user_id = validate_api_key(api_key)
        if user_id:
            return UserAuth(user_id=user_id)

    # Check Bearer token
    if bearer:
        token_data = decode_token(bearer.credentials)
        if token_data:
            return UserAuth(user_id=token_data.user_id, email=token_data.email)

    # No valid auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[UserAuth]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work with or without auth.
    """
    # Check API key
    if api_key:
        user_id = validate_api_key(api_key)
        if user_id:
            return UserAuth(user_id=user_id)

    # Check Bearer token
    if bearer:
        token_data = decode_token(bearer.credentials)
        if token_data:
            return UserAuth(user_id=token_data.user_id, email=token_data.email)

    return None


# Default user for unauthenticated requests
def get_user_id_or_default(user: Optional[UserAuth]) -> str:
    """Get user ID or return default."""
    if user:
        return user.user_id
    return "anonymous"
