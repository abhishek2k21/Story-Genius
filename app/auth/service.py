"""
Authentication Service
User and API key management operations.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

from app.auth.models import (
    User, APIKey, AuthContext, UserStatus, UserRole, KeyStatus,
    create_user_id, create_key_id
)
from app.auth.password import hash_password, verify_password, validate_password_strength
from app.auth.keys import create_api_key, hash_api_key, validate_key_format
from app.auth.tokens import create_token_pair, verify_token
from app.auth.permissions import get_role_permissions, expand_permissions


class AuthService:
    """Central authentication service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users: Dict[str, User] = {}
            cls._instance._users_by_email: Dict[str, str] = {}
            cls._instance._api_keys: Dict[str, APIKey] = {}
            cls._instance._keys_by_hash: Dict[str, str] = {}
            cls._instance._lock = threading.Lock()
            cls._instance._init_admin()
        return cls._instance
    
    def _init_admin(self):
        """Create default admin user"""
        admin_id = create_user_id()
        admin = User(
            user_id=admin_id,
            email="admin@storygenius.ai",
            username="admin",
            password_hash=hash_password("Admin123!"),
            role=UserRole.ADMIN,
            email_verified=True
        )
        self._users[admin_id] = admin
        self._users_by_email[admin.email] = admin_id
    
    # ==================== User Operations ====================
    
    def register_user(
        self,
        email: str,
        username: str,
        password: str
    ) -> Tuple[Optional[User], str]:
        """Register new user"""
        # Validate password
        valid, msg = validate_password_strength(password)
        if not valid:
            return None, msg
        
        # Check email uniqueness
        if email.lower() in self._users_by_email:
            return None, "Email already registered"
        
        # Check username uniqueness
        for u in self._users.values():
            if u.username.lower() == username.lower():
                return None, "Username already taken"
        
        with self._lock:
            user = User(
                user_id=create_user_id(),
                email=email.lower(),
                username=username,
                password_hash=hash_password(password)
            )
            self._users[user.user_id] = user
            self._users_by_email[user.email] = user.user_id
        
        return user, "User registered successfully"
    
    def authenticate(self, email: str, password: str) -> Tuple[Optional[User], str]:
        """Authenticate user with email and password"""
        user_id = self._users_by_email.get(email.lower())
        if not user_id:
            return None, "Invalid credentials"
        
        user = self._users.get(user_id)
        if not user:
            return None, "Invalid credentials"
        
        if not user.is_active():
            return None, f"Account is {user.status.value}"
        
        if not verify_password(password, user.password_hash):
            return None, "Invalid credentials"
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        return user, "Authentication successful"
    
    def login(self, email: str, password: str) -> Tuple[Optional[Dict], str]:
        """Login and get tokens"""
        user, msg = self.authenticate(email, password)
        if not user:
            return None, msg
        
        tokens = create_token_pair(user.user_id, user.role.value)
        tokens["user"] = user.to_dict()
        
        return tokens, "Login successful"
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self._users_by_email.get(email.lower())
        return self._users.get(user_id) if user_id else None
    
    def update_user(self, user_id: str, updates: Dict) -> Tuple[Optional[User], str]:
        """Update user"""
        user = self._users.get(user_id)
        if not user:
            return None, "User not found"
        
        if "username" in updates:
            user.username = updates["username"]
        if "metadata" in updates:
            user.metadata.update(updates["metadata"])
        
        user.updated_at = datetime.utcnow()
        return user, "User updated"
    
    def change_password(
        self, user_id: str, current: str, new: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        user = self._users.get(user_id)
        if not user:
            return False, "User not found"
        
        if not verify_password(current, user.password_hash):
            return False, "Current password incorrect"
        
        valid, msg = validate_password_strength(new)
        if not valid:
            return False, msg
        
        user.password_hash = hash_password(new)
        user.updated_at = datetime.utcnow()
        
        return True, "Password changed"
    
    def list_users(self, include_deleted: bool = False) -> List[User]:
        """List all users (admin only)"""
        users = list(self._users.values())
        if not include_deleted:
            users = [u for u in users if u.status != UserStatus.DELETED]
        return users
    
    # ==================== API Key Operations ====================
    
    def create_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str] = None,
        rate_limit: int = 60
    ) -> Tuple[Optional[APIKey], str, str]:
        """Create API key for user. Returns (key, message, raw_key)"""
        user = self._users.get(user_id)
        if not user:
            return None, "User not found", ""
        
        api_key, raw_key = create_api_key(
            user_id=user_id,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit
        )
        
        with self._lock:
            self._api_keys[api_key.key_id] = api_key
            self._keys_by_hash[api_key.key_hash] = api_key.key_id
        
        return api_key, "API key created", raw_key
    
    def validate_api_key(self, raw_key: str) -> Tuple[Optional[APIKey], Optional[User]]:
        """Validate API key and return key + user"""
        if not validate_key_format(raw_key):
            return None, None
        
        key_hash = hash_api_key(raw_key)
        key_id = self._keys_by_hash.get(key_hash)
        
        if not key_id:
            return None, None
        
        api_key = self._api_keys.get(key_id)
        if not api_key or not api_key.is_valid():
            return None, None
        
        user = self._users.get(api_key.user_id)
        if not user or not user.is_active():
            return None, None
        
        # Update usage
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        
        return api_key, user
    
    def revoke_key(self, key_id: str, user_id: str) -> bool:
        """Revoke API key"""
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return False
        if api_key.user_id != user_id:
            return False
        
        api_key.status = KeyStatus.REVOKED
        return True
    
    def list_user_keys(self, user_id: str) -> List[APIKey]:
        """List user's API keys"""
        return [k for k in self._api_keys.values() if k.user_id == user_id]
    
    # ==================== Auth Context ====================
    
    def get_auth_context(self, user: User, api_key: APIKey = None) -> AuthContext:
        """Build auth context for request"""
        perms = get_role_permissions(user.role.value)
        
        if api_key:
            # Restrict to key permissions
            key_perms = expand_permissions(api_key.permissions)
            perms = perms.intersection(key_perms)
        
        return AuthContext(
            user=user,
            api_key=api_key,
            permissions=list(perms)
        )


# Singleton instance
auth_service = AuthService()
