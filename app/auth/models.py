"""
User and API Key Models
Data structures for authentication.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    CREATOR = "creator"
    ADMIN = "admin"


class KeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class User:
    """User model"""
    user_id: str
    email: str
    username: str
    password_hash: str
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.CREATOR
    email_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self, include_sensitive: bool = False) -> Dict:
        data = {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "status": self.status.value,
            "role": self.role.value,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
        if include_sensitive:
            data["metadata"] = self.metadata
        return data
    
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


@dataclass
class APIKey:
    """API Key model"""
    key_id: str
    user_id: str
    key_hash: str
    key_prefix: str  # First 8 chars for identification
    name: str
    status: KeyStatus = KeyStatus.ACTIVE
    permissions: List[str] = field(default_factory=lambda: ["read", "write"])
    rate_limit: int = 60  # Requests per minute
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    def to_dict(self, show_prefix: bool = True) -> Dict:
        data = {
            "key_id": self.key_id,
            "name": self.name,
            "status": self.status.value,
            "permissions": self.permissions,
            "rate_limit": self.rate_limit,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count
        }
        if show_prefix:
            data["key_prefix"] = f"{self.key_prefix}..."
        return data
    
    def is_valid(self) -> bool:
        if self.status != KeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        if "admin" in self.permissions:
            return True
        return permission in self.permissions


@dataclass
class AuthContext:
    """Authentication context for request"""
    user: User
    api_key: Optional[APIKey] = None
    permissions: List[str] = field(default_factory=list)
    
    def has_permission(self, permission: str) -> bool:
        if self.user.is_admin():
            return True
        return permission in self.permissions
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user.user_id,
            "username": self.user.username,
            "role": self.user.role.value,
            "permissions": self.permissions
        }


def create_user_id() -> str:
    return str(uuid.uuid4())


def create_key_id() -> str:
    return str(uuid.uuid4())
