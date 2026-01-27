"""
Password Utilities
Secure password hashing and validation.
"""
import hashlib
import secrets
import re
from typing import Tuple


# Password requirements
MIN_LENGTH = 8
SALT_LENGTH = 32
HASH_ITERATIONS = 100000


def hash_password(password: str) -> str:
    """Hash password with salt using PBKDF2"""
    salt = secrets.token_hex(SALT_LENGTH // 2)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        HASH_ITERATIONS
    )
    return f"{salt}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        salt, key_hex = password_hash.split('$')
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            HASH_ITERATIONS
        )
        return key.hex() == key_hex
    except (ValueError, AttributeError):
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password meets requirements"""
    if len(password) < MIN_LENGTH:
        return False, f"Password must be at least {MIN_LENGTH} characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password meets requirements"


def generate_temp_password() -> str:
    """Generate temporary password for reset"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%"
    return ''.join(secrets.choice(chars) for _ in range(12))
