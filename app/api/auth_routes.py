"""
Authentication API Routes
User registration, login, and API key management.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

from app.auth.service import auth_service
from app.auth.tokens import verify_token, extract_user_id
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/auth", tags=["auth"])


# ==================== Request/Response Models ====================

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5)
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    permissions: Optional[List[str]] = None
    rate_limit: int = Field(default=60, ge=1, le=1000)


# ==================== Auth Dependency ====================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> AuthContext:
    """Get current authenticated user"""
    
    # Try API key first
    if x_api_key:
        api_key, user = auth_service.validate_api_key(x_api_key)
        if user:
            return auth_service.get_auth_context(user, api_key)
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Try Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user_id = extract_user_id(token)
        if user_id:
            user = auth_service.get_user(user_id)
            if user and user.is_active():
                return auth_service.get_auth_context(user)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    raise HTTPException(status_code=401, detail="Authentication required")


# ==================== Auth Endpoints ====================

@router.post("/register")
async def register(request: RegisterRequest):
    """Register new user"""
    user, msg = auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password
    )
    
    if not user:
        raise HTTPException(status_code=400, detail=msg)
    
    return {
        "message": msg,
        "user": user.to_dict()
    }


@router.post("/login")
async def login(request: LoginRequest):
    """Login and get tokens"""
    result, msg = auth_service.login(request.email, request.password)
    
    if not result:
        raise HTTPException(status_code=401, detail=msg)
    
    return result


@router.get("/me")
async def get_current_user_info(auth: AuthContext = Depends(get_current_user)):
    """Get current user info"""
    return auth.user.to_dict()


@router.post("/password/change")
async def change_password(
    request: ChangePasswordRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Change password"""
    success, msg = auth_service.change_password(
        auth.user.user_id,
        request.current_password,
        request.new_password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


# ==================== API Key Endpoints ====================

@router.get("/keys")
async def list_api_keys(auth: AuthContext = Depends(get_current_user)):
    """List user's API keys"""
    keys = auth_service.list_user_keys(auth.user.user_id)
    return {
        "count": len(keys),
        "keys": [k.to_dict() for k in keys]
    }


@router.post("/keys")
async def create_api_key(
    request: CreateKeyRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create new API key"""
    api_key, msg, raw_key = auth_service.create_key(
        user_id=auth.user.user_id,
        name=request.name,
        permissions=request.permissions,
        rate_limit=request.rate_limit
    )
    
    if not api_key:
        raise HTTPException(status_code=400, detail=msg)
    
    return {
        "message": "API key created. Save this key - it won't be shown again.",
        "key": raw_key,
        "key_id": api_key.key_id,
        "name": api_key.name,
        "permissions": api_key.permissions
    }


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Revoke API key"""
    if auth_service.revoke_key(key_id, auth.user.user_id):
        return {"message": "Key revoked", "key_id": key_id}
    raise HTTPException(status_code=404, detail="Key not found")
