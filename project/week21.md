Week 21: User Authentication & Monetization
Goal: Add user accounts, credit system, and payment integration to enable SaaS revenue

Day 1: Database Schema for Users & Authentication
Why: Need to track users, their subscriptions, and usage before monetizing
Tasks:

Design user and subscription tables
Create Alembic migration
Add password hashing utilities

Migration Code:
python# alembic/versions/xxxx_add_users_and_auth.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime, nullable=True)
    )
    
    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False),  # 'free', 'starter', 'pro', 'agency'
        sa.Column('status', sa.String(20), nullable=False),  # 'active', 'canceled', 'expired'
        sa.Column('credits_total', sa.Integer, default=0),
        sa.Column('credits_used', sa.Integer, default=0),
        sa.Column('credits_remaining', sa.Integer, default=0),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime, nullable=True),
        sa.Column('current_period_end', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'))
    )
    
    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('last_used', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Usage logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('credits_used', sa.Integer, default=1),
        sa.Column('action', sa.String(50), nullable=False),  # 'video_generation', 'api_call'
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Add user_id to jobs table
    op.add_column('jobs', sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    
    # Indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])

def downgrade():
    op.drop_table('usage_logs')
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('users')
    op.drop_column('jobs', 'user_id')
Password Hashing Utility:
python# app/auth/utils.py
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key() -> str:
    """Generate a secure random API key"""
    return f"sk_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return pwd_context.hash(api_key)
Install Dependencies:
bashpip install passlib[bcrypt] python-jose[cryptography]
Run Migration:
bashalembic upgrade head
Deliverable: Database schema ready for user management

Day 2: JWT Authentication Implementation
Tasks:

Create JWT token generation and validation
Build signup and login endpoints
Add authentication middleware

JWT Configuration:
python# app/core/config.py
class Settings:
    # ... existing settings ...
    
    # JWT settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

# Generate secret key: openssl rand -hex 32
JWT Service:
python# app/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
Auth Models:
python# app/auth/models.py
from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_verified: bool
    created_at: str
Auth Endpoints:
python# app/api/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends
from app.auth.models import SignupRequest, LoginRequest, TokenResponse
from app.auth.utils import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.core.database import db

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """Create new user account"""
    
    # Check if user exists
    existing = await db.fetch_one(
        "SELECT id FROM users WHERE email = $1",
        request.email
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    user = await db.fetch_one(
        """
        INSERT INTO users (email, password_hash, full_name)
        VALUES ($1, $2, $3)
        RETURNING id, email, full_name, is_verified, created_at
        """,
        request.email, password_hash, request.full_name
    )
    
    # Create free subscription
    await db.execute(
        """
        INSERT INTO subscriptions (user_id, tier, status, credits_total, credits_remaining)
        VALUES ($1, 'free', 'active', 5, 5)
        """,
        user['id']
    )
    
    # Generate token
    access_token = create_access_token({"sub": str(user['id']), "email": user['email']})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": str(user['id']),
            "email": user['email'],
            "full_name": user['full_name'],
            "is_verified": user['is_verified']
        }
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    
    # Get user
    user = await db.fetch_one(
        """
        SELECT id, email, password_hash, full_name, is_verified, is_active
        FROM users WHERE email = $1
        """,
        request.email
    )
    
    if not user or not verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user['is_active']:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Update last login
    await db.execute(
        "UPDATE users SET last_login = NOW() WHERE id = $1",
        user['id']
    )
    
    # Generate token
    access_token = create_access_token({"sub": str(user['id']), "email": user['email']})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": str(user['id']),
            "email": user['email'],
            "full_name": user['full_name'],
            "is_verified": user['is_verified']
        }
    )

@router.get("/me")
async def get_current_user(user = Depends(get_current_user)):
    """Get current user profile"""
    return user
Auth Dependency:
python# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt import verify_token
from app.core.database import db

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = await db.fetch_one(
        """
        SELECT u.id, u.email, u.full_name, u.is_verified,
               s.tier, s.credits_remaining
        FROM users u
        LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
        WHERE u.id = $1 AND u.is_active = true
        """,
        user_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
Register Auth Router:
python# app/api/main.py
from app.api.auth_routes import router as auth_router

app.include_router(auth_router)
Test:
bash# Signup
curl -X POST http://localhost:8000/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123",
    "full_name": "Test User"
  }'

# Response: {"access_token": "eyJ...", "user": {...}}

# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123"
  }'

# Get profile
curl http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer eyJ..."
Deliverable: Working JWT authentication system

Day 3: Protect API Endpoints with Auth
Tasks:

Add authentication to video generation endpoint
Deduct credits on job creation
Track usage logs

Protected Endpoint:
python# app/api/routes.py
from app.auth.dependencies import get_current_user

@router.post("/v1/shorts/generate")
async def generate_short(
    request: GenerateRequest,
    user = Depends(get_current_user)
):
    """Generate video (requires authentication)"""
    
    # Check credits
    if user['credits_remaining'] <= 0:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please upgrade your plan."
        )
    
    # Create job
    job = await create_job(request, user_id=user['id'])
    
    # Deduct credit
    await db.execute(
        """
        UPDATE subscriptions
        SET credits_used = credits_used + 1,
            credits_remaining = credits_remaining - 1
        WHERE user_id = $1 AND status = 'active'
        """,
        user['id']
    )
    
    # Log usage
    await db.execute(
        """
        INSERT INTO usage_logs (user_id, job_id, credits_used, action)
        VALUES ($1, $2, 1, 'video_generation')
        """,
        user['id'], job['id']
    )
    
    # Queue job
    job_queue.enqueue(job['id'])
    
    return {
        "job_id": job['id'],
        "status": "queued",
        "credits_remaining": user['credits_remaining'] - 1
    }

@router.get("/v1/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    user = Depends(get_current_user)
):
    """Get job status (user can only see their own jobs)"""
    
    job = await db.fetch_one(
        "SELECT * FROM jobs WHERE id = $1 AND user_id = $2",
        job_id, user['id']
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job['id'],
        "status": job['status'],
        "progress": job.get('progress_percent'),
        "video_url": job.get('output_url'),
        "error": job.get('error_message')
    }

@router.get("/v1/user/credits")
async def get_user_credits(user = Depends(get_current_user)):
    """Get user's current credit balance"""
    
    subscription = await db.fetch_one(
        """
        SELECT tier, credits_total, credits_used, credits_remaining,
               current_period_end
        FROM subscriptions
        WHERE user_id = $1 AND status = 'active'
        """,
        user['id']
    )
    
    return {
        "tier": subscription['tier'],
        "credits_total": subscription['credits_total'],
        "credits_used": subscription['credits_used'],
        "credits_remaining": subscription['credits_remaining'],
        "renews_at": subscription['current_period_end'].isoformat() if subscription['current_period_end'] else None
    }

@router.get("/v1/user/usage")
async def get_user_usage(
    user = Depends(get_current_user),
    days: int = 30
):
    """Get user's usage history"""
    
    logs = await db.fetch_all(
        """
        SELECT action, credits_used, created_at
        FROM usage_logs
        WHERE user_id = $1 AND created_at > NOW() - INTERVAL '{days} days'
        ORDER BY created_at DESC
        LIMIT 100
        """.format(days=days),
        user['id']
    )
    
    return {
        "usage": [
            {
                "action": log['action'],
                "credits": log['credits_used'],
                "timestamp": log['created_at'].isoformat()
            }
            for log in logs
        ]
    }
Test:
bash# Get token first
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123"}' \
  | jq -r '.access_token')

# Check credits
curl http://localhost:8000/v1/user/credits \
  -H "Authorization: Bearer $TOKEN"

# Generate video (uses 1 credit)
curl -X POST http://localhost:8000/v1/shorts/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"platform":"youtube_shorts","topic":"AI trends"}'

# Check credits again (should be 4 remaining)
curl http://localhost:8000/v1/user/credits \
  -H "Authorization: Bearer $TOKEN"
Deliverable: Credit-based video generation system

Day 4: Frontend Auth Integration
Tasks:

Create login/signup pages
Store JWT in localStorage
Add auth context provider
Protect routes

Auth Context:
typescript// frontend/src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  credits_remaining: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async (authToken: string) => {
    try {
      const userData = await apiClient.getCurrentUser(authToken);
      setUser(userData);
    } catch (error) {
      // Token invalid, clear it
      localStorage.removeItem('auth_token');
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem('auth_token', response.access_token);
  };

  const signup = async (email: string, password: string, fullName?: string) => {
    const response = await apiClient.signup(email, password, fullName);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem('auth_token', response.access_token);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
Update API Client:
typescript// frontend/src/lib/api-client.ts
export class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Auth methods
  async login(email: string, password: string) {
    return this.request<TokenResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async signup(email: string, password: string, fullName?: string) {
    return this.request<TokenResponse>('/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async getCurrentUser(token: string) {
    this.setToken(token);
    return this.request<User>('/v1/auth/me');
  }

  async getUserCredits() {
    return this.request<CreditsResponse>('/v1/user/credits');
  }
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  credits_remaining: number;
}

interface CreditsResponse {
  tier: string;
  credits_total: number;
  credits_used: number;
  credits_remaining: number;
  renews_at: string | null;
}
Login Page:
typescript// frontend/src/pages/Login.tsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Login failed', {
        description: error instanceof Error ? error.message : 'Invalid credentials',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Login to Story Genius</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
          <p className="text-sm text-center mt-4 text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary underline">
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
Signup Page:
typescript// frontend/src/pages/Signup.tsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';

export function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await signup(email, password, fullName);
      toast.success('Account created! You have 5 free credits.');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Signup failed', {
        description: error instanceof Error ? error.message : 'Could not create account',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Full Name</label>
              <Input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Minimum 8 characters
              </p>
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating account...' : 'Sign up'}
            </Button>
          </form>
          <p className="text-sm text-center mt-4 text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary underline">
              Login
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
Protected Route Component:
typescript// frontend/src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-Continue7:02 PMscreen">
<LoadingSpinner size="lg" />
</div>
);
}
if (!isAuthenticated) {
return <Navigate to="/login" replace />;
}
return <>{children}</>;
}

**Update App Router:**
```typescript
// frontend/src/App.tsx
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Login } from '@/pages/Login';
import { Signup } from '@/pages/Signup';

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  );
}
```

**Credits Display in Header:**
```typescript
// frontend/src/components/Header.tsx
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Coins } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuth();
  
  const { data: credits } = useQuery({
    queryKey: ['user-credits'],
    queryFn: () => apiClient.getUserCredits(),
    refetchInterval: 30000, // Refresh every 30s
  });

  return (
    <header className="border-b px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="font-bold">Story Genius</h1>
        
        {/* Credits Display */}
        <div className="flex items-center gap-2 px-3 py-1 bg-accent rounded-full">
          <Coins className="h-4 w-4" />
          <span className="text-sm font-medium">
            {credits?.credits_remaining || 0} credits
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">{user?.email}</span>
        <Button variant="outline" size="sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  );
}
```

**Test:**
```bash
# 1. Start frontend
npm run dev

# 2. Go to /signup
# 3. Create account
# 4. Should redirect to /dashboard
# 5. Check header shows "5 credits"
# 6. Generate video
# 7. Credits should decrease to 4
```

**Deliverable:** Full auth flow with protected routes and credit display

---

### **Day 5: Stripe Payment Integration**

**Tasks:**
1. Set up Stripe account and get API keys
2. Create subscription plans in Stripe
3. Build checkout endpoint
4. Handle webhooks

**Install Stripe:**
```bash
pip install stripe
```

**Stripe Configuration:**
```python
# app/core/config.py
class Settings:
    # ... existing settings ...
    
    STRIPE_SECRET_KEY: str = Field(..., env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(..., env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(..., env="STRIPE_WEBHOOK_SECRET")
    
    # Pricing plans (Stripe Price IDs)
    STRIPE_PRICE_STARTER: str = Field(..., env="STRIPE_PRICE_STARTER")
    STRIPE_PRICE_PRO: str = Field(..., env="STRIPE_PRICE_PRO")
    STRIPE_PRICE_AGENCY: str = Field(..., env="STRIPE_PRICE_AGENCY")
```

**Pricing Plans:**
```python
# app/billing/plans.py
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    AGENCY = "agency"

PLANS = {
    SubscriptionTier.FREE: {
        "name": "Free",
        "price": 0,
        "credits": 5,
        "features": ["5 videos/month", "Basic quality", "Watermark"]
    },
    SubscriptionTier.STARTER: {
        "name": "Starter",
        "price": 9,
        "credits": 20,
        "features": ["20 videos/month", "HD quality", "No watermark", "Priority support"]
    },
    SubscriptionTier.PRO: {
        "name": "Pro",
        "price": 29,
        "credits": 100,
        "features": ["100 videos/month", "4K quality", "API access", "Custom branding"]
    },
    SubscriptionTier.AGENCY: {
        "name": "Agency",
        "price": 99,
        "credits": 500,
        "features": ["500 videos/month", "White-label", "Team accounts", "Dedicated support"]
    }
}
```

**Billing Endpoints:**
```typescript
// app/api/billing_routes.py
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.config import settings
from app.auth.dependencies import get_current_user
from app.billing.plans import PLANS, SubscriptionTier

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/v1/billing", tags=["billing"])

@router.post("/create-checkout-session")
async def create_checkout_session(
    tier: SubscriptionTier,
    user = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
    
    if tier == SubscriptionTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for free tier")
    
    # Map tier to Stripe Price ID
    price_ids = {
        SubscriptionTier.STARTER: settings.STRIPE_PRICE_STARTER,
        SubscriptionTier.PRO: settings.STRIPE_PRICE_PRO,
        SubscriptionTier.AGENCY: settings.STRIPE_PRICE_AGENCY
    }
    
    try:
        # Create or get Stripe customer
        customer_id = await get_or_create_stripe_customer(user['id'], user['email'])
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_ids[tier],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/canceled",
            metadata={
                'user_id': str(user['id']),
                'tier': tier
            }
        )
        
        return {"checkout_url": session.url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_or_create_stripe_customer(user_id, email):
    """Get existing or create new Stripe customer"""
    
    # Check if customer exists
    sub = await db.fetch_one(
        "SELECT stripe_customer_id FROM subscriptions WHERE user_id = $1",
        user_id
    )
    
    if sub and sub['stripe_customer_id']:
        return sub['stripe_customer_id']
    
    # Create new customer
    customer = stripe.Customer.create(
        email=email,
        metadata={'user_id': str(user_id)}
    )
    
    # Save customer ID
    await db.execute(
        "UPDATE subscriptions SET stripe_customer_id = $1 WHERE user_id = $2",
        customer.id, user_id
    )
    
    return customer.id

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])
    
    elif event['type'] == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event['data']['object'])
    
    return {"status": "success"}

async def handle_checkout_completed(session):
    """Handle successful checkout"""
    user_id = session['metadata']['user_id']
    tier = session['metadata']['tier']
    subscription_id = session['subscription']
    
    # Get subscription details
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Update user subscription
    await db.execute(
        """
        UPDATE subscriptions
        SET tier = $1,
            status = 'active',
            stripe_subscription_id = $2,
            credits_total = $3,
            credits_remaining = credits_remaining + $3,
            current_period_start = $4,
            current_period_end = $5
        WHERE user_id = $6
        """,
        tier,
        subscription_id,
        PLANS[tier]['credits'],
        datetime.fromtimestamp(subscription.current_period_start),
        datetime.fromtimestamp(subscription.current_period_end),
        user_id
    )

async def handle_payment_succeeded(invoice):
    """Handle monthly subscription renewal"""
    customer_id = invoice['customer']
    subscription_id = invoice['subscription']
    
    # Get user
    sub = await db.fetch_one(
        "SELECT user_id, tier FROM subscriptions WHERE stripe_subscription_id = $1",
        subscription_id
    )
    
    if not sub:
        return
    
    # Renew credits
    await db.execute(
        """
        UPDATE subscriptions
        SET credits_used = 0,
            credits_remaining = $1,
            current_period_start = NOW(),
            current_period_end = NOW() + INTERVAL '1 month'
        WHERE user_id = $2
        """,
        PLANS[sub['tier']]['credits'],
        sub['user_id']
    )

@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "tier": tier,
                **details
            }
            for tier, details in PLANS.items()
        ]
    }

@router.get("/portal")
async def get_billing_portal(user = Depends(get_current_user)):
    """Get Stripe billing portal link"""
    
    sub = await db.fetch_one(
        "SELECT stripe_customer_id FROM subscriptions WHERE user_id = $1",
        user['id']
    )
    
    if not sub or not sub['stripe_customer_id']:
        raise HTTPException(status_code=404, detail="No billing account found")
    
    session = stripe.billing_portal.Session.create(
        customer=sub['stripe_customer_id'],
        return_url=f"{settings.FRONTEND_URL}/billing"
    )
    
    return {"portal_url": session.url}
```

**Register Router:**
```python
# app/api/main.py
from app.api.billing_routes import router as billing_router

app.include_router(billing_router)
```

**Test Stripe Integration:**
```bash
# Use Stripe CLI for webhook testing
stripe listen --forward-to localhost:8000/v1/billing/webhook

# Create checkout session
curl -X POST http://localhost:8000/v1/billing/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier": "starter"}'

# Response: {"checkout_url": "https://checkout.stripe.com/..."}
```

**Deliverable:** Working Stripe checkout and webhook handling

---

### **Day 6: Frontend Pricing Page & Checkout**

**Tasks:**
1. Create pricing page with plan cards
2. Integrate Stripe checkout
3. Build billing dashboard

**Pricing Page:**
```typescript
// frontend/src/pages/Pricing.tsx
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Check, Zap } from 'lucide-react';
import { toast } from 'sonner';

export function Pricing() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const { data: plans, isLoading } = useQuery({
    queryKey: ['billing-plans'],
    queryFn: () => apiClient.getBillingPlans(),
  });

  const checkoutMutation = useMutation({
    mutationFn: (tier: string) => apiClient.createCheckoutSession(tier),
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
    onError: () => {
      toast.error('Failed to start checkout');
    },
  });

  const handleSelectPlan = (tier: string) => {
    if (!isAuthenticated) {
      navigate('/signup');
      return;
    }
    
    if (tier === 'free') {
      toast.info('You already have free credits!');
      return;
    }
    
    checkoutMutation.mutate(tier);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Simple, transparent pricing</h1>
        <p className="text-xl text-muted-foreground">
          Choose the plan that's right for you
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {plans?.plans.map((plan: any) => (
          <Card
            key={plan.tier}
            className={plan.tier === 'pro' ? 'border-primary border-2' : ''}
          >
            {plan.tier === 'pro' && (
              <div className="bg-primary text-primary-foreground text-center py-1 text-sm font-medium">
                Most Popular
              </div>
            )}
            
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                {plan.name}
                {plan.tier === 'pro' && <Zap className="h-5 w-5 text-primary" />}
              </CardTitle>
              <div className="mt-4">
                <span className="text-4xl font-bold">${plan.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {plan.credits} videos/month
              </p>
            </CardHeader>
            
            <CardContent>
              <Button
                className="w-full mb-4"
                variant={plan.tier === 'pro' ? 'default' : 'outline'}
                onClick={() => handleSelectPlan(plan.tier)}
                disabled={checkoutMutation.isPending}
              >
                {plan.tier === 'free' ? 'Get Started' : 'Upgrade'}
              </Button>
              
              <ul className="space-y-2">
                {plan.features.map((feature: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-green-500 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

**Billing Page:**
```typescript
// frontend/src/pages/Billing.tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ExternalLink } from 'lucide-react';

export function Billing() {
  const { data: credits } = useQuery({
    queryKey: ['user-credits'],
    queryFn: () => apiClient.getUserCredits(),
  });

  const { data: usage } = useQuery({
    queryKey: ['user-usage'],
    queryFn: () => apiClient.getUserUsage(30),
  });

  const portalMutation = useMutation({
    mutationFn: () => apiClient.getBillingPortal(),
    onSuccess: (data) => {
      window.location.href = data.portal_url;
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Billing & Usage</h1>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold capitalize">{credits?.tier}</p>
              <p className="text-sm text-muted-foreground">
                {credits?.credits_remaining} of {credits?.credits_total} credits remaining
              </p>
              {credits?.renews_at && (
                <p className="text-xs text-muted-foreground mt-1">
                  Renews on {new Date(credits.renews_at).toLocaleDateString()}
                </p>
              )}
            </div>
            <Button
              variant="outline"
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
            >
              Manage Subscription <ExternalLink className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Usage History */}
      <Card>
        <CardHeader>
          <CardTitle>Usage History (Last 30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {usage?.usage.map((item: any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b last:border-0"
              >
                <div>
                  <p className="text-sm font-medium capitalize">
                    {item.action.replace('_', ' ')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.timestamp).toLocaleString()}
                  </p>
                </div>
                <span className="text-sm font-medium">-{item.credits} credit</span>
              </div>
            ))}
            
            {!usage?.usage.length && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No usage yet
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Update API Client:**
```typescript
// frontend/src/lib/api-client.ts
export class ApiClient {
  // ... existing methods ...

  async getBillingPlans() {
    return this.request<{ plans: any[] }>('/v1/billing/plans');
  }

  async createCheckoutSession(tier: string) {
    return this.request<{ checkout_url: string }>('/v1/billing/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({ tier }),
    });
  }

  async getBillingPortal() {
    return this.request<{ portal_url: string }>('/v1/billing/portal');
  }

  async getUserUsage(days = 30) {
    return this.request<{ usage: UsageLog[] }>(`/v1/user/usage?days=${days}`);
  }
}

interface UsageLog {
  action: string;
  credits: number;
  timestamp: string;
}
```

**Test Flow:**
```bash
# 1. Visit /pricing
# 2. Click "Upgrade" on Starter plan
# 3. Redirects to Stripe Checkout
# 4. Use test card: 4242 4242 4242 4242
# 5. Complete purchase
# 6. Webhook updates subscription
# 7. Redirected back to /billing/success
# 8. Credits increased to 20
```

**Deliverable:** Complete billing flow with Stripe integration

---

### **Day 7: Testing, Documentation & Deployment**

**Tasks:**
1. Test complete auth + payment flow
2. Update environment variables for production
3. Deploy to Railway/Vercel
4. Document week's achievements

**Production Environment Variables:**
```bash
# Backend (Railway)
DATABASE_URL=postgresql://...
SECRET_KEY=your_generated_secret_key
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_AGENCY=price_...
FRONTEND_URL=https://your-app.vercel.app

# Frontend (Vercel)
VITE_API_BASE_URL=https://your-api.railway.app
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

**E2E Test Checklist:**
```markdown
## Week 21 Production Test Checklist

### Authentication
- [ ] Signup creates user with 5 free credits
- [ ] Login works with correct credentials
- [ ] JWT token stored in localStorage
- [ ] Protected routes redirect to /login
- [ ] Logout clears token and redirects

### Credit System
- [ ] Free user starts with 5 credits
- [ ] Video generation deducts 1 credit
- [ ] Credits display updates in header
- [ ] Out of credits shows upgrade prompt
- [ ] Usage logs track all actions

### Stripe Integration
- [ ] Pricing page displays all tiers
- [ ] Checkout redirects to Stripe
- [ ] Test payment completes successfully
- [ ] Webhook updates subscription
- [ ] Credits added after payment
- [ ] Billing portal link works
- [ ] Monthly renewal handled correctly

### User Experience
- [ ] Toast notifications for all actions
- [ ] Loading states during API calls
- [ ] Error handling works gracefully
- [ ] Credits sync across tabs
- [ ] Mobile responsive
```

**Week 21 Report Template:**
```markdown
# Week 21 Report: User Authentication & Monetization

## Status
✅ Complete

## Summary
Implemented full user authentication system with JWT, credit-based usage tracking, and Stripe payment integration. Platform is now a revenue-generating SaaS.

## Achievements

### Backend
- ✅ User registration and login with JWT
- ✅ Protected API endpoints
- ✅ Credit system with usage tracking
- ✅ Stripe checkout integration
- ✅ Webhook handling for subscriptions
- ✅ Billing portal access

### Frontend
- ✅ Login/Signup pages
- ✅ Auth context provider
- ✅ Protected routes
- ✅ Credits display in header
- ✅ Pricing page with plan cards
- ✅ Billing dashboard
- ✅ Stripe checkout flow

### Database
- ✅ Users table
- ✅ Subscriptions table
- ✅ API keys table
- ✅ Usage logs table

## Metrics
- Users created: X
- Paid conversions: Y
- Total revenue: $Z
- Avg credits/user: N

## Next Steps (Week 22)
- Email verification
- Password reset flow
- Team/agency accounts
- API key management
- Referral system
```

**Deploy Updates:**
```bash
# Backend
git add .
git commit -m "Add authentication and billing"
git push origin main
# Railway auto-deploys

# Frontend
git add .
git commit -m "Add auth UI and billing pages"
git push origin main
# Vercel auto-deploys
```

**Stripe Webhook Configuration:**
```bash
# In Stripe Dashboard:
# 1. Go to Developers > Webhooks
# 2. Add endpoint: https://your-api.railway.app/v1/billing/webhook
# 3. Select events:
#    - checkout.session.completed
#    - customer.subscription.updated
#    - customer.subscription.deleted
#    - invoice.payment_succeeded
# 4. Copy webhook secret to Railway env vars
```

**Documentation:**
```markdown
# Authentication & Billing Setup Guide

## User Flow
1. Signup → Get 5 free credits
2. Create videos (1 credit each)
3. Run out → Upgrade prompt
4. Choose plan → Stripe checkout
5. Payment → Credits added
6. Monthly renewal automatic

## Pricing Tiers
- **Free**: $0/mo, 5 videos
- **Starter**: $9/mo, 20 videos
- **Pro**: $29/mo, 100 videos
- **Agency**: $99/mo, 500 videos

## Environment Setup
See `.env.example` for required variables

## Stripe Test Cards
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
```

**Deliverable:** Production-ready SaaS with authentication and payments

---

## **Week 21 Summary**

### **What You Built:**
✅ JWT authentication system
✅ User registration and login
✅ Protected API endpoints
✅ Credit-based usage system
✅ Stripe payment integration
✅ Subscription management
✅ Billing dashboard
✅ Usage tracking
✅ Webhook handling

### **Revenue Model Activated:**
- Free tier: 5 videos/month
- Paid tiers: $9-$99/month
- Recurring revenue enabled
- Automatic renewals
- Billing portal for management

### **Tech Stack Added:**
- **Auth:** JWT with passlib/bcrypt
- **Payments:** Stripe Checkout + Webhooks
- **State:** Auth context in React
- **Storage:** localStorage for tokens

---

## **Next Week Preview (Week 22): Advanced Features & Growth**

**Goal:** Add features that increase user retention and drive upgrades

**What You'll Build:**
- Email verification system
- Password reset flow
- API key management for developers
- Batch video generation
- Team/agency workspaces
- Referral program

---

Ready to start Week 21? This is where your project becomes a real business! Let me know if you need any clarification.