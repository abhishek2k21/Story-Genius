"""
Settings API Routes
User settings, preferences, and API key management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.settings import settings_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Request/Response Models

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    video_complete_notifications: Optional[bool] = None


class APIKeyCreate(BaseModel):
    name: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# Profile Routes

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    try:
        profile = settings_service.get_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile.to_dict()
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{user_id}")
async def update_profile(user_id: str, update: ProfileUpdate):
    """Update user profile"""
    try:
        profile = settings_service.update_profile(
            user_id=user_id,
            name=update.name,
            bio=update.bio,
            avatar_url=update.avatar_url
        )
        
        return profile.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Preferences Routes

@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get user preferences"""
    try:
        prefs = settings_service.get_preferences(user_id)
        return prefs.to_dict()
    except Exception as e:
        logger.error(f"Failed to get preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{user_id}")
async def update_preferences(user_id: str, update: PreferencesUpdate):
    """Update user preferences"""
    try:
        prefs = settings_service.update_preferences(
            user_id=user_id,
            theme=update.theme,
            language=update.language,
            email_notifications=update.email_notifications,
            push_notifications=update.push_notifications,
            video_complete_notifications=update.video_complete_notifications
        )
        
        return prefs.to_dict()
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# API Key Routes

@router.get("/api-keys/{user_id}")
async def get_api_keys(user_id: str):
    """Get all API keys for user"""
    try:
        keys = settings_service.get_api_keys(user_id)
        return [key.to_dict(include_key=False) for key in keys]
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys/{user_id}")
async def create_api_key(user_id: str, create: APIKeyCreate):
    """Create new API key"""
    try:
        key = settings_service.create_api_key(user_id, create.name)
        
        # Return with full key only once
        return key.to_dict(include_key=True)
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str, user_id: str):
    """Revoke API key"""
    try:
        success = settings_service.revoke_api_key(key_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"status": "success", "key_id": key_id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security Routes

@router.post("/security/change-password")
async def change_password(user_id: str, change: PasswordChange):
    """Change user password"""
    try:
        success = settings_service.change_password(
            user_id=user_id,
            current_password=change.current_password,
            new_password=change.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid current password")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/enable-2fa/{user_id}")
async def enable_2fa(user_id: str):
    """Enable two-factor authentication"""
    try:
        setup_data = settings_service.enable_2fa(user_id)
        return setup_data
    except Exception as e:
        logger.error(f"Failed to enable 2FA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/account/{user_id}")
async def delete_account(user_id: str):
    """Delete user account (GDPR compliance)"""
    try:
        success = settings_service.delete_account(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return {"status": "success", "message": "Account deleted"}
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        raise HTTPException(status_code=500, detail=str(e))
