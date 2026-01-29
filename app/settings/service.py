"""
User Settings Service
Manages user profile, preferences, and API keys.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import secrets
import hashlib

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserProfile:
    """User profile"""
    user_id: str
    name: str
    email: str
    bio: str = ""
    avatar_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class UserPreferences:
    """User preferences"""
    theme: str = "light"  # light, dark, system
    language: str = "en"
    email_notifications: bool = True
    push_notifications: bool = True
    video_complete_notifications: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "theme": self.theme,
            "language": self.language,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "video_complete_notifications": self.video_complete_notifications
        }


@dataclass
class APIKey:
    """API Key"""
    id: str
    name: str
    key: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    active: bool = True
    
    def mask_key(self) -> str:
        """Return masked API key for display"""
        return f"{self.key[:8]}...{self.key[-4:]}"
    
    def to_dict(self, include_key: bool = False) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "key": self.key if include_key else self.mask_key(),
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "active": self.active
        }


class UserSettingsService:
    """
    User settings service for managing profiles, preferences, and API keys.
    """
    
    def __init__(self):
        # Mock storage (in production: use database)
        self._profiles: Dict[str, UserProfile] = {}
        self._preferences: Dict[str, UserPreferences] = {}
        self._api_keys: Dict[str, APIKey] = {}
        logger.info("UserSettingsService initialized")
    
    # Profile Management
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self._profiles.get(user_id)
    
    def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> UserProfile:
        """Update user profile"""
        profile = self._profiles.get(user_id)
        
        if not profile:
            raise ValueError(f"Profile not found for user: {user_id}")
        
        if name is not None:
            profile.name = name
        if bio is not None:
            profile.bio = bio
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        
        logger.info(f"Updated profile for user: {user_id}")
        
        return profile
    
    def create_profile(
        self,
        user_id: str,
        name: str,
        email: str
    ) -> UserProfile:
        """Create user profile"""
        profile = UserProfile(
            user_id=user_id,
            name=name,
            email=email
        )
        
        self._profiles[user_id] = profile
        
        # Create default preferences
        self._preferences[user_id] = UserPreferences()
        
        logger.info(f"Created profile for user: {user_id}")
        
        return profile
    
    # Preferences Management
    
    def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences"""
        if user_id not in self._preferences:
            self._preferences[user_id] = UserPreferences()
        
        return self._preferences[user_id]
    
    def update_preferences(
        self,
        user_id: str,
        theme: Optional[str] = None,
        language: Optional[str] = None,
        email_notifications: Optional[bool] = None,
        push_notifications: Optional[bool] = None,
        video_complete_notifications: Optional[bool] = None
    ) -> UserPreferences:
        """Update user preferences"""
        prefs = self.get_preferences(user_id)
        
        if theme is not None:
            prefs.theme = theme
        if language is not None:
            prefs.language = language
        if email_notifications is not None:
            prefs.email_notifications = email_notifications
        if push_notifications is not None:
            prefs.push_notifications = push_notifications
        if video_complete_notifications is not None:
            prefs.video_complete_notifications = video_complete_notifications
        
        logger.info(f"Updated preferences for user: {user_id}")
        
        return prefs
    
    # API Key Management
    
    def create_api_key(
        self,
        user_id: str,
        name: str
    ) -> APIKey:
        """
        Create new API key.
        
        Args:
            user_id: User ID
            name: Key name/description
        
        Returns:
            Created API key
        """
        import uuid
        
        # Generate secure API key
        key = self._generate_api_key()
        
        api_key = APIKey(
            id=str(uuid.uuid4()),
            name=name,
            key=key,
            user_id=user_id
        )
        
        self._api_keys[api_key.id] = api_key
        
        logger.info(f"Created API key for user {user_id}: {name}")
        
        return api_key
    
    def get_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for user"""
        keys = [
            key for key in self._api_keys.values()
            if key.user_id == user_id and key.active
        ]
        
        return keys
    
    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """
        Revoke API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization)
        
        Returns:
            True if revoked, False if not found
        """
        if key_id not in self._api_keys:
            return False
        
        api_key = self._api_keys[key_id]
        
        # Verify ownership
        if api_key.user_id != user_id:
            raise PermissionError("Cannot revoke API key of another user")
        
        api_key.active = False
        
        logger.info(f"Revoked API key: {key_id}")
        
        return True
    
    def validate_api_key(self, key: str) -> Optional[str]:
        """
        Validate API key and return user ID.
        
        Args:
            key: API key to validate
        
        Returns:
            User ID if valid, None otherwise
        """
        for api_key in self._api_keys.values():
            if api_key.key == key and api_key.active:
                # Update last used
                api_key.last_used = datetime.utcnow()
                
                logger.debug(f"API key validated for user: {api_key.user_id}")
                
                return api_key.user_id
        
        logger.warning(f"Invalid API key attempt")
        return None
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        # Generate 32-byte random key
        random_bytes = secrets.token_bytes(32)
        
        # Create API key with prefix
        key = f"sk_{secrets.token_hex(32)}"
        
        return key
    
    # Security Settings
    
    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
        
        Returns:
            True if successful
        """
        # In production: verify current password hash
        # Hash new password and store
        
        # Mock implementation
        logger.info(f"Password changed for user: {user_id}")
        return True
    
    def enable_2fa(self, user_id: str) -> Dict:
        """
        Enable two-factor authentication.
        
        Args:
            user_id: User ID
        
        Returns:
            2FA setup data (QR code, secret)
        """
        # In production: generate TOTP secret, create QR code
        
        # Mock implementation
        secret = secrets.token_hex(16)
        
        logger.info(f"2FA enabled for user: {user_id}")
        
        return {
            "secret": secret,
            "qr_code_url": f"otpauth://totp/VideoCreator:{user_id}?secret={secret}",
            "backup_codes": [secrets.token_hex(4) for _ in range(10)]
        }
    
    def delete_account(self, user_id: str) -> bool:
        """
        Delete user account (GDPR compliance).
        
        Args:
            user_id: User ID
        
        Returns:
            True if successful
        """
        # Delete profile
        if user_id in self._profiles:
            del self._profiles[user_id]
        
        # Delete preferences
        if user_id in self._preferences:
            del self._preferences[user_id]
        
        # Revoke all API keys
        for key_id, api_key in list(self._api_keys.items()):
            if api_key.user_id == user_id:
                del self._api_keys[key_id]
        
        logger.info(f"Deleted account for user: {user_id}")
        
        return True


# Global instance
settings_service = UserSettingsService()
