"""
JWT Token Utilities
Token generation and validation for session-based auth.
"""
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


# Token configuration
SECRET_KEY = secrets.token_hex(32)  # In production, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, role: str, extra: Dict = None) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    if extra:
        payload.update(extra)
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # Unique token ID
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user_id: str, role: str) -> Dict:
    """Create access and refresh token pair"""
    access = create_access_token(user_id, role)
    refresh = create_refresh_token(user_id)
    
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_user_id(token: str) -> Optional[str]:
    """Extract user ID from token"""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


def is_access_token(token: str) -> bool:
    """Check if token is access token"""
    payload = verify_token(token)
    if payload:
        return payload.get("type") == "access"
    return False


def is_refresh_token(token: str) -> bool:
    """Check if token is refresh token"""
    payload = verify_token(token)
    if payload:
        return payload.get("type") == "refresh"
    return False
