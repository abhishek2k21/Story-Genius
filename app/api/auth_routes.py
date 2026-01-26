"""
Authentication routes for signup, login, and user management.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.auth.models import SignupRequest, LoginRequest, TokenResponse
from app.auth.utils import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from app.core.database import get_db
import uuid
from datetime import datetime

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create new user account"""
    
    # For now, using simple in-memory storage until we set up proper database tables
    # This is a placeholder implementation
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Generate user ID
    user_id = str(uuid.uuid4())
    
    # Create mock user data
    user = {
        "id": user_id,
        "email": request.email,
        "full_name": request.full_name,
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Generate token
    access_token = create_access_token({
        "sub": user_id,
        "email": request.email
    })
    
    return TokenResponse(
        access_token=access_token,
        user=user
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    
    # Placeholder implementation - will be replaced with actual database query
    # For testing, we'll accept any email/password
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": request.email,
        "full_name": "Test User",
        "is_verified": False
    }
    
    # Generate token
    access_token = create_access_token({
        "sub": user_id,
        "email": request.email
    })
    
    return TokenResponse(
        access_token=access_token,
        user=user
    )


@router.get("/me")
async def get_current_user_profile(user = Depends(get_current_user)):
    """Get current user profile"""
    return user
