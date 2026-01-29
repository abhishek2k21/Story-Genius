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
from app.core.database import get_db_session, DBUser, DBAPIKey
import json


class AuthService:
    """Central authentication service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize admin if not exists
            cls._instance._init_admin()
        return cls._instance
    
    def _to_domain_user(self, db_user: DBUser) -> Optional[User]:
        if not db_user:
            return None
        return User(
            user_id=db_user.user_id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            status=UserStatus(db_user.status),
            role=UserRole(db_user.role),
            email_verified=bool(db_user.email_verified),
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            last_login_at=db_user.last_login_at,
            metadata=json.loads(db_user.metadata_json)
        )

    def _init_admin(self):
        """Create default admin user if not exists"""
        db = get_db_session()
        try:
            # Check if admin exists
            admin = db.query(DBUser).filter(DBUser.email == "admin@storygenius.ai").first()
            if not admin:
                admin_id = create_user_id()
                admin = DBUser(
                    user_id=admin_id,
                    email="admin@storygenius.ai",
                    username="admin",
                    password_hash=hash_password("Admin123!"),
                    status=UserStatus.ACTIVE.value,
                    role=UserRole.ADMIN.value,
                    email_verified=1,
                    metadata_json="{}"
                )
                db.add(admin)
                db.commit()
        finally:
            db.close()
    
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
        
        db = get_db_session()
        try:
            # Check email uniqueness
            if db.query(DBUser).filter(DBUser.email == email.lower()).first():
                return None, "Email already registered"
            
            # Check username uniqueness
            if db.query(DBUser).filter(DBUser.username == username).first():
                return None, "Username already taken"
            
            user = DBUser(
                user_id=create_user_id(),
                email=email.lower(),
                username=username,
                password_hash=hash_password(password),
                status=UserStatus.ACTIVE.value,
                role=UserRole.CREATOR.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return self._to_domain_user(user), "User registered successfully"
        finally:
            db.close()
    
    def authenticate(self, identifier: str, password: str) -> Tuple[Optional[User], str]:
        """Authenticate user with email or username"""
        db = get_db_session()
        try:
            # Try email first
            user = db.query(DBUser).filter(DBUser.email == identifier.lower()).first()
            
            # Try username if not found by email
            if not user:
                user = db.query(DBUser).filter(DBUser.username == identifier).first()
            
            if not user:
                return None, "Invalid credentials"
            
            if user.status != UserStatus.ACTIVE.value:
                return None, f"Account is {user.status}"
            
            if not verify_password(password, user.password_hash):
                return None, "Invalid credentials"
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            db.commit()
            
            return self._to_domain_user(user), "Authentication successful"
        finally:
            db.close()
    
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
        db = get_db_session()
        try:
            user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            return self._to_domain_user(user)
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = get_db_session()
        try:
            user = db.query(DBUser).filter(DBUser.email == email.lower()).first()
            return self._to_domain_user(user)
        finally:
            db.close()
    
    def update_user(self, user_id: str, updates: Dict) -> Tuple[Optional[User], str]:
        """Update user"""
        db = get_db_session()
        try:
            user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if not user:
                return None, "User not found"
            
            if "username" in updates:
                user.username = updates["username"]
            if "metadata" in updates:
                meta = json.loads(user.metadata_json)
                meta.update(updates["metadata"])
                user.metadata_json = json.dumps(meta)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            return self._to_domain_user(user), "User updated"
        finally:
            db.close()
    
    def change_password(
        self, user_id: str, current: str, new: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        db = get_db_session()
        try:
            user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if not user:
                return False, "User not found"
            
            if not verify_password(current, user.password_hash):
                return False, "Current password incorrect"
            
            valid, msg = validate_password_strength(new)
            if not valid:
                return False, msg
            
            user.password_hash = hash_password(new)
            user.updated_at = datetime.utcnow()
            db.commit()
            
            return True, "Password changed"
        finally:
            db.close()
    
    def list_users(self, include_deleted: bool = False) -> List[User]:
        """List all users (admin only)"""
        db = get_db_session()
        try:
            query = db.query(DBUser)
            if not include_deleted:
                query = query.filter(DBUser.status != UserStatus.DELETED.value)
            
            users = query.all()
            return [self._to_domain_user(u) for u in users]
        finally:
            db.close()
    
    # ==================== API Key Operations ====================
    
    def _to_domain_key(self, db_key: DBAPIKey) -> Optional[APIKey]:
        if not db_key:
            return None
        return APIKey(
            key_id=db_key.key_id,
            user_id=db_key.user_id,
            key_hash=db_key.key_hash,
            key_prefix=db_key.key_prefix,
            name=db_key.name,
            status=KeyStatus(db_key.status),
            permissions=db_key.permissions.split(","),
            rate_limit=db_key.rate_limit,
            created_at=db_key.created_at,
            expires_at=db_key.expires_at,
            last_used_at=db_key.last_used_at,
            usage_count=db_key.usage_count
        )

    def create_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str] = None,
        rate_limit: int = 60
    ) -> Tuple[Optional[APIKey], str, str]:
        """Create API key for user. Returns (key, message, raw_key)"""
        db = get_db_session()
        try:
            user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if not user:
                return None, "User not found", ""
            
            api_key, raw_key = create_api_key(
                user_id=user_id,
                name=name,
                permissions=permissions,
                rate_limit=rate_limit
            )
            
            db_key = DBAPIKey(
                key_id=api_key.key_id,
                user_id=user_id,
                key_hash=api_key.key_hash,
                key_prefix=api_key.key_prefix,
                name=name,
                status=KeyStatus.ACTIVE.value,
                permissions=",".join(api_key.permissions),
                rate_limit=rate_limit,
                created_at=datetime.utcnow()
            )
            
            db.add(db_key)
            db.commit()
            db.refresh(db_key)
            
            return self._to_domain_key(db_key), "API key created", raw_key
        finally:
            db.close()
    
    def validate_api_key(self, raw_key: str) -> Tuple[Optional[APIKey], Optional[User]]:
        """Validate API key and return key + user"""
        if not validate_key_format(raw_key):
            return None, None
        
        key_hash = hash_api_key(raw_key)
        
        db = get_db_session()
        try:
            db_key = db.query(DBAPIKey).filter(DBAPIKey.key_hash == key_hash).first()
            
            if not db_key:
                return None, None
            
            api_key = self._to_domain_key(db_key)
            if not api_key.is_valid():
                return None, None
            
            user = db.query(DBUser).filter(DBUser.user_id == db_key.user_id).first()
            if not user or user.status != UserStatus.ACTIVE.value:
                return None, None
            
            # Update usage
            db_key.last_used_at = datetime.utcnow()
            db_key.usage_count += 1
            db.commit()
            
            return api_key, self._to_domain_user(user)
        finally:
            db.close()
    
    def revoke_key(self, key_id: str, user_id: str) -> bool:
        """Revoke API key"""
        db = get_db_session()
        try:
            db_key = db.query(DBAPIKey).filter(DBAPIKey.key_id == key_id).first()
            if not db_key:
                return False
            if db_key.user_id != user_id:
                return False
            
            db_key.status = KeyStatus.REVOKED.value
            db.commit()
            return True
        finally:
            db.close()
    
    def list_user_keys(self, user_id: str) -> List[APIKey]:
        """List user's API keys"""
        db = get_db_session()
        try:
            keys = db.query(DBAPIKey).filter(DBAPIKey.user_id == user_id).all()
            return [self._to_domain_key(k) for k in keys]
        finally:
            db.close()
    
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
