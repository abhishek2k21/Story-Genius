"""
API Marketplace & Developer Portal.
Third-party app registration, API keys, and developer tools.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limiting tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OAuth2Scope(str, Enum):
    """OAuth 2.0 scopes for third-party apps."""
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    READ_VIDEOS = "read:videos"
    WRITE_VIDEOS = "write:videos"
    READ_ANALYTICS = "read:analytics"
    MANAGE_WEBHOOKS = "manage:webhooks"


class DeveloperPortal:
    """Manage developer accounts and API access."""
    
    def __init__(self, db_session, rate_limiter):
        self.db = db_session
        self.rate_limiter = rate_limiter
        self.developers: Dict[str, Dict] = {}
        self.api_keys: Dict[str, Dict] = {}
    
    def register_developer(
        self,
        user_id: str,
        company_name: Optional[str] = None
    ) -> Dict:
        """
        Register new developer account.
        
        Args:
            user_id: User ID
            company_name: Optional company name
            
        Returns:
            Developer account details
        """
        developer_id = str(uuid.uuid4())
        
        developer = {
            "id": developer_id,
            "user_id": user_id,
            "company_name": company_name,
            "tier": RateLimitTier.FREE.value,
            "registered_at": datetime.utcnow(),
            "apps": [],
            "api_keys": []
        }
        
        self.developers[developer_id] = developer
        self._save_developer(developer)
        
        logger.info(f"Registered developer {developer_id}")
        
        return {
            "developer_id": developer_id,
            "tier": RateLimitTier.FREE.value,
            "rate_limits": self._get_rate_limits(RateLimitTier.FREE.value)
        }
    
    def create_api_key(
        self,
        developer_id: str,
        name: str,
        scopes: List[str]
    ) -> Dict:
        """
        Generate API key for developer.
        
        Args:
            developer_id: Developer ID
            name: Key name/description
            scopes: List of OAuth scopes
            
        Returns:
            API key details (key shown only once)
        """
        developer = self.developers.get(developer_id)
        
        if not developer:
            raise ValueError(f"Developer not found: {developer_id}")
        
        # Validate scopes
        valid_scopes = [s.value for s in OAuth2Scope]
        for scope in scopes:
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}")
        
        # Generate API key and secret
        api_key = self._generate_api_key()
        api_secret = self._generate_api_secret()
        
        # Hash secret for storage
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        key_id = str(uuid.uuid4())
        
        key_data = {
            "id": key_id,
            "developer_id": developer_id,
            "name": name,
            "api_key": api_key,
            "secret_hash": secret_hash,
            "scopes": scopes,
            "tier": developer["tier"],
            "created_at": datetime.utcnow(),
            "last_used": None,
            "enabled": True
        }
        
        self.api_keys[api_key] = key_data
        developer["api_keys"].append(key_id)
        
        self._save_api_key(key_data)
        
        logger.info(f"Created API key {key_id} for developer {developer_id}")
        
        # Return API secret ONLY on creation
        return {
            "key_id": key_id,
            "api_key": api_key,
            "api_secret": api_secret,  # WARNING: Save this - won't be shown again
            "scopes": scopes,
            "rate_limits": self._get_rate_limits(developer["tier"])
        }
    
    def validate_api_key(
        self,
        api_key: str,
        api_secret: str
    ) -> Optional[Dict]:
        """
        Validate API key and secret.
        
        Args:
            api_key: Public API key
            api_secret: API secret
            
        Returns:
            Key data if valid, None if invalid
        """
        key_data = self.api_keys.get(api_key)
        
        if not key_data or not key_data["enabled"]:
            return None
        
        # Verify secret
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        if secret_hash != key_data["secret_hash"]:
            logger.warning(f"Invalid API secret for key {api_key}")
            return None
        
        # Update last used
        key_data["last_used"] = datetime.utcnow()
        
        return key_data
    
    def check_rate_limit(
        self,
        api_key: str
    ) -> Dict:
        """
        Check rate limit status for API key.
        
        Returns:
            Rate limit status with remaining quota
        """
        key_data = self.api_keys.get(api_key)
        
        if not key_data:
            raise ValueError("Invalid API key")
        
        tier = key_data["tier"]
        limits = self._get_rate_limits(tier)
        
        # Check current usage
        usage = self.rate_limiter.get_usage(api_key)
        
        return {
            "tier": tier,
            "limits": limits,
            "usage": {
                "requests_today": usage["requests_today"],
                "requests_this_minute": usage["requests_this_minute"]
            },
            "remaining": {
                "daily": limits["requests_per_day"] - usage["requests_today"],
                "per_minute": limits["requests_per_minute"] - usage["requests_this_minute"]
            },
            "reset_at": usage["reset_at"]
        }
    
    def _get_rate_limits(self, tier: str) -> Dict:
        """Get rate limits for tier."""
        limits = {
            RateLimitTier.FREE.value: {
                "requests_per_day": 1000,
                "requests_per_minute": 10,
                "max_api_keys": 2
            },
            RateLimitTier.PRO.value: {
                "requests_per_day": 10000,
                "requests_per_minute": 100,
                "max_api_keys": 10
            },
            RateLimitTier.ENTERPRISE.value: {
                "requests_per_day": -1,  # Unlimited
                "requests_per_minute": 1000,
                "max_api_keys": -1  # Unlimited
            }
        }
        
        return limits.get(tier, limits[RateLimitTier.FREE.value])
    
    def _generate_api_key(self) -> str:
        """Generate public API key."""
        return f"vc_{secrets.token_urlsafe(32)}"
    
    def _generate_api_secret(self) -> str:
        """Generate API secret."""
        return secrets.token_urlsafe(48)
    
    def get_developer_stats(self, developer_id: str) -> Dict:
        """Get developer usage statistics."""
        developer = self.developers.get(developer_id)
        
        if not developer:
            raise ValueError(f"Developer not found: {developer_id}")
        
        # Aggregate stats from all API keys
        total_requests = 0
        total_errors = 0
        
        for key_id in developer["api_keys"]:
            key_data = next(
                (k for k in self.api_keys.values() if k["id"] == key_id),
                None
            )
            
            if key_data:
                usage = self.rate_limiter.get_usage(key_data["api_key"])
                total_requests += usage["requests_today"]
                total_errors += usage.get("errors_today", 0)
        
        return {
            "developer_id": developer_id,
            "tier": developer["tier"],
            "api_keys_count": len(developer["api_keys"]),
            "apps_count": len(developer["apps"]),
            "today": {
                "requests": total_requests,
                "errors": total_errors,
                "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0
            }
        }
    
    def _save_developer(self, developer: Dict):
        """Save developer to database."""
        pass
    
    def _save_api_key(self, key_data: Dict):
        """Save API key to database."""
        pass


class APIMarketplace:
    """Manage third-party applications."""
    
    def __init__(self, developer_portal):
        self.portal = developer_portal
        self.apps: Dict[str, Dict] = {}
    
    def register_app(
        self,
        developer_id: str,
        app_info: Dict
    ) -> Dict:
        """
        Register new third-party application.
        
        App info structure:
        {
          "name": "Video Analytics Pro",
          "description": "Advanced analytics for your videos",
          "category": "analytics",
          "webhook_url": "https://app.example.com/webhook",
          "redirect_uri": "https://app.example.com/callback",
          "scopes": ["read:videos", "read:analytics"]
        }
        
        Args:
            developer_id: Developer ID
            app_info: Application information
            
        Returns:
            Registered app details with OAuth credentials
        """
        app_id = str(uuid.uuid4())
        
        # Generate OAuth credentials
        client_id = self._generate_client_id()
        client_secret = self._generate_client_secret()
        
        app = {
            "id": app_id,
            "developer_id": developer_id,
            "name": app_info["name"],
            "description": app_info["description"],
            "category": app_info.get("category", "other"),
            "webhook_url": app_info.get("webhook_url"),
            "redirect_uri": app_info.get("redirect_uri"),
            "scopes": app_info["scopes"],
            "client_id": client_id,
            "client_secret": client_secret,
            "status": "pending_review",
            "created_at": datetime.utcnow(),
            "installs": 0,
            "rating": 0.0
        }
        
        self.apps[app_id] = app
        self._save_app(app)
        
        logger.info(f"Registered app {app_id}: {app_info['name']}")
        
        return {
            "app_id": app_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "status": "pending_review"
        }
    
    def list_marketplace_apps(
        self,
        category: Optional[str] = None
    ) -> List[Dict]:
        """List apps in marketplace."""
        apps = [
            a for a in self.apps.values()
            if a["status"] == "approved"
        ]
        
        if category:
            apps = [a for a in apps if a["category"] == category]
        
        # Sort by rating and installs
        apps.sort(key=lambda a: (a["rating"], a["installs"]), reverse=True)
        
        return [
            {
                "app_id": a["id"],
                "name": a["name"],
                "description": a["description"],
                "category": a["category"],
                "rating": a["rating"],
                "installs": a["installs"]
            }
            for a in apps
        ]
    
    def install_app(
        self,
        app_id: str,
        user_id: str
    ) -> Dict:
        """
        Install app for user (initiate OAuth flow).
        
        Returns OAuth authorization URL
        """
        app = self.apps.get(app_id)
        
        if not app or app["status"] != "approved":
            raise ValueError("App not available")
        
        # Generate OAuth state
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_url = (
            f"https://api.ytvideocreator.com/oauth/authorize"
            f"?client_id={app['client_id']}"
            f"&redirect_uri={app['redirect_uri']}"
            f"&scope={','.join(app['scopes'])}"
            f"&state={state}"
            f"&response_type=code"
        )
        
        # Increment install count
        app["installs"] += 1
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    
    def _generate_client_id(self) -> str:
        """Generate OAuth client ID."""
        return f"app_{secrets.token_urlsafe(16)}"
    
    def _generate_client_secret(self) -> str:
        """Generate OAuth client secret."""
        return secrets.token_urlsafe(32)
    
    def _save_app(self, app: Dict):
        """Save app to database."""
        pass


# FastAPI routes for developer portal
"""
from fastapi import APIRouter, Depends, HTTPException
from app.services.developer_portal import DeveloperPortal, APIMarketplace

router = APIRouter(prefix="/api/developers")

@router.post("/register")
async def register_developer(
    company_name: str = None,
    current_user = Depends(get_current_user)
):
    '''Register as developer.'''
    portal = DeveloperPortal(db, rate_limiter)
    
    developer = portal.register_developer(
        user_id=current_user.id,
        company_name=company_name
    )
    
    return developer

@router.post("/keys")
async def create_api_key(
    name: str,
    scopes: List[str],
    current_user = Depends(get_current_user)
):
    '''Create API key.'''
    portal = DeveloperPortal(db, rate_limiter)
    
    # Get developer_id from user
    developer_id = get_developer_id(current_user.id)
    
    api_key = portal.create_api_key(
        developer_id=developer_id,
        name=name,
        scopes=scopes
    )
    
    return api_key

@router.get("/stats")
async def get_stats(current_user = Depends(get_current_user)):
    '''Get developer statistics.'''
    portal = DeveloperPortal(db, rate_limiter)
    developer_id = get_developer_id(current_user.id)
    
    stats = portal.get_developer_stats(developer_id)
    
    return stats
"""
