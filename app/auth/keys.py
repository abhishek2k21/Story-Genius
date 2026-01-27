"""
API Key Utilities
Key generation, hashing, and validation.
"""
import secrets
import hashlib
from typing import Tuple, Optional
from datetime import datetime

from app.auth.models import APIKey, KeyStatus, create_key_id


# Key configuration
KEY_PREFIX = "sg"
KEY_LENGTH = 32


def generate_api_key(environment: str = "live") -> Tuple[str, str]:
    """
    Generate new API key.
    Returns (raw_key, key_hash) - raw_key shown once, hash stored.
    """
    # Generate random token
    token = secrets.token_hex(KEY_LENGTH // 2)
    
    # Format: sg_live_xxxxx or sg_test_xxxxx
    raw_key = f"{KEY_PREFIX}_{environment}_{token}"
    
    # Hash for storage
    key_hash = hash_api_key(raw_key)
    
    return raw_key, key_hash


def hash_api_key(raw_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def validate_key_format(raw_key: str) -> bool:
    """Validate API key format"""
    if not raw_key:
        return False
    
    parts = raw_key.split('_')
    if len(parts) != 3:
        return False
    
    prefix, env, token = parts
    
    if prefix != KEY_PREFIX:
        return False
    
    if env not in ["live", "test"]:
        return False
    
    if len(token) != KEY_LENGTH:
        return False
    
    return True


def get_key_prefix(raw_key: str) -> str:
    """Extract prefix for identification"""
    return raw_key[:12] if len(raw_key) >= 12 else raw_key


def create_api_key(
    user_id: str,
    name: str,
    permissions: list = None,
    rate_limit: int = 60,
    expires_at: datetime = None,
    environment: str = "live"
) -> Tuple[APIKey, str]:
    """
    Create new API key for user.
    Returns (APIKey object, raw_key) - raw_key shown once to user.
    """
    raw_key, key_hash = generate_api_key(environment)
    
    api_key = APIKey(
        key_id=create_key_id(),
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=get_key_prefix(raw_key),
        name=name,
        permissions=permissions or ["read", "write"],
        rate_limit=rate_limit,
        expires_at=expires_at
    )
    
    return api_key, raw_key


def rotate_api_key(
    old_key: APIKey,
    environment: str = "live"
) -> Tuple[APIKey, str]:
    """
    Rotate API key - create new, old remains active for grace period.
    Returns (new APIKey, raw_key).
    """
    raw_key, key_hash = generate_api_key(environment)
    
    new_key = APIKey(
        key_id=create_key_id(),
        user_id=old_key.user_id,
        key_hash=key_hash,
        key_prefix=get_key_prefix(raw_key),
        name=f"{old_key.name} (rotated)",
        permissions=old_key.permissions,
        rate_limit=old_key.rate_limit
    )
    
    return new_key, raw_key
