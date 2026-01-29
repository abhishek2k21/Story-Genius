"""
Referral Program Models and Service.
Incentivize viral growth through referrals.
"""
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets
import string
from typing import Optional, Dict
import enum


class ReferralStatus(str, enum.Enum):
    """Referral status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    REWARDED = "rewarded"
    EXPIRED = "expired"


# Database Models
class Referral(Base):
    """Referral tracking model."""
    
    __tablename__ = "referrals"
    
    id = Column(String(36), primary_key=True)
    referrer_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    referee_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    rewarded_at = Column(DateTime, nullable=True)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_user_id], backref="referrals_made")
    referee = relationship("User", foreign_keys=[referee_user_id], backref="referral_received")
    
    def __repr__(self):
        return f"<Referral {self.referral_code} ({self.status})>"


class ReferralReward(Base):
    """Referral rewards tracking."""
    
    __tablename__ = "referral_rewards"
    
    id = Column(String(36), primary_key=True)
    referral_id = Column(String(36), ForeignKey("referrals.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reward_type = Column(String(50))  # 'credit', 'free_month', 'discount'
    reward_value = Column(Integer)  # Amount in cents or days
    claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    referral = relationship("Referral", backref="rewards")
    user = relationship("User", backref="rewards")


# Service
class ReferralService:
    """Manage referral program logic."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_referral_code(self, user_id: str) -> str:
        """
        Generate unique referral code for user.
        
        Format: USER + 4 random alphanumeric chars
        Example: USER-A7B2
        
        Args:
            user_id: User identifier
            
        Returns:
            Unique referral code
        """
        # Generate random suffix
        chars = string.ascii_uppercase + string.digits
        suffix = ''.join(secrets.choice(chars) for _ in range(4))
        
        # Create code
        code = f"USER-{suffix}"
        
        # Ensure uniqueness
        existing = self.db.query(Referral).filter_by(referral_code=code).first()
        if existing:
            return self.generate_referral_code(user_id)  # Retry
        
        return code
    
    def get_or_create_referral_code(self, user_id: str) -> str:
        """
        Get user's referral code or create one.
        
        Args:
            user_id: User identifier
            
        Returns:
            Referral code
        """
        # Check if user already has a code
        existing = self.db.query(Referral).filter_by(
            referrer_user_id=user_id,
            referee_user_id=None
        ).first()
        
        if existing:
            return existing.referral_code
        
        # Create new referral code
        code = self.generate_referral_code(user_id)
        
        referral = Referral(
            id=self._generate_id(),
            referrer_user_id=user_id,
            referral_code=code,
            status=ReferralStatus.PENDING
        )
        
        self.db.add(referral)
        self.db.commit()
        
        return code
    
    def apply_referral_code(self, referee_user_id: str, code: str) -> Dict:
        """
        Apply referral code during signup.
        
        Args:
            referee_user_id: New user's ID
            code: Referral code
            
        Returns:
            Result with success status and referee reward
        """
        # Find referral by code
        referral = self.db.query(Referral).filter_by(
            referral_code=code,
            status=ReferralStatus.PENDING
        ).first()
        
        if not referral:
            return {
                "success": False,
                "error": "Invalid referral code"
            }
        
        # Can't refer yourself
        if referral.referrer_user_id == referee_user_id:
            return {
                "success": False,
                "error": "Cannot use your own referral code"
            }
        
        # Update referral
        referral.referee_user_id = referee_user_id
        referral.status = ReferralStatus.COMPLETED
        referral.completed_at = datetime.utcnow()
        
        # Create referee reward (20% off first month)
        referee_reward = ReferralReward(
            id=self._generate_id(),
            referral_id=referral.id,
            user_id=referee_user_id,
            reward_type="discount",
            reward_value=20,  # 20% off
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(referee_reward)
        self.db.commit()
        
        return {
            "success": True,
            "reward": {
                "type": "discount",
                "value": 20,
                "description": "20% off your first month"
            }
        }
    
    def process_referee_conversion(self, referee_user_id: str):
        """
        Process when referee makes first payment.
        Trigger referrer reward.
        
        Args:
            referee_user_id: Referee user ID
        """
        # Find completed referral
        referral = self.db.query(Referral).filter_by(
            referee_user_id=referee_user_id,
            status=ReferralStatus.COMPLETED
        ).first()
        
        if not referral:
            return
        
        # Create referrer reward (1 month free Pro = $29 credit)
        referrer_reward = ReferralReward(
            id=self._generate_id(),
            referral_id=referral.id,
            user_id=referral.referrer_user_id,
            reward_type="free_month",
            reward_value=30,  # 30 days
            expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year to use
        )
        
        # Update referral status
        referral.status = ReferralStatus.REWARDED
        referral.rewarded_at = datetime.utcnow()
        
        self.db.add(referrer_reward)
        self.db.commit()
        
        # Send notification to referrer
        self._notify_referrer(referral.referrer_user_id)
    
    def get_referral_stats(self, user_id: str) -> Dict:
        """
        Get user's referral statistics.
        
        Args:
            user_id: User identifier
            
        Returns:
            Referral statistics
        """
        # Count referrals
        total = self.db.query(Referral).filter_by(
            referrer_user_id=user_id
        ).filter(
            Referral.referee_user_id.isnot(None)
        ).count()
        
        completed = self.db.query(Referral).filter_by(
            referrer_user_id=user_id,
            status=ReferralStatus.REWARDED
        ).count()
        
        pending = self.db.query(Referral).filter_by(
            referrer_user_id=user_id,
            status=ReferralStatus.COMPLETED
        ).count()
        
        # Get unclaimed rewards
        unclaimed_rewards = self.db.query(ReferralReward).filter_by(
            user_id=user_id,
            claimed=False
        ).all()
        
        return {
            "referral_code": self.get_or_create_referral_code(user_id),
            "total_referrals": total,
            "completed_referrals": completed,
            "pending_referrals": pending,
            "unclaimed_rewards": len(unclaimed_rewards),
            "rewards": [
                {
                    "type": r.reward_type,
                    "value": r.reward_value,
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None
                }
                for r in unclaimed_rewards
            ]
        }
    
    def claim_reward(self, user_id: str, reward_id: str) -> Dict:
        """
        Claim a referral reward.
        
        Args:
            user_id: User identifier
            reward_id: Reward identifier
            
        Returns:
            Result with success status
        """
        reward = self.db.query(ReferralReward).filter_by(
            id=reward_id,
            user_id=user_id,
            claimed=False
        ).first()
        
        if not reward:
            return {"success": False, "error": "Reward not found"}
        
        # Check expiration
        if reward.expires_at and reward.expires_at < datetime.utcnow():
            return {"success": False, "error": "Reward expired"}
        
        # Mark as claimed
        reward.claimed = True
        reward.claimed_at = datetime.utcnow()
        
        self.db.commit()
        
        # Apply reward (implementation depends on reward type)
        self._apply_reward(user_id, reward)
        
        return {
            "success": True,
            "reward": {
                "type": reward.reward_type,
                "value": reward.reward_value
            }
        }
    
    def _apply_reward(self, user_id: str, reward: ReferralReward):
        """Apply reward to user account."""
        if reward.reward_type == "free_month":
            # Extend subscription by reward_value days
            pass
        elif reward.reward_type == "credit":
            # Add credit to account
            pass
        elif reward.reward_type == "discount":
            # Apply discount code
            pass
    
    def _notify_referrer(self, user_id: str):
        """Send notification to referrer about earned reward."""
        # Send email/in-app notification
        pass
    
    def _generate_id(self) -> str:
        """Generate UUID."""
        import uuid
        return str(uuid.uuid4())


# API Endpoints (FastAPI)
"""
from fastapi import APIRouter, Depends, HTTPException
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/referrals", tags=["referrals"])

@router.get("/code")
async def get_referral_code(current_user: User = Depends(get_current_user)):
    '''Get or create user's referral code.'''
    service = ReferralService(db)
    code = service.get_or_create_referral_code(current_user.id)
    return {"code": code}

@router.post("/apply")
async def apply_referral_code(
    code: str,
    current_user: User = Depends(get_current_user)
):
    '''Apply referral code.'''
    service = ReferralService(db)
    result = service.apply_referral_code(current_user.id, code)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/stats")
async def get_referral_stats(current_user: User = Depends(get_current_user)):
    '''Get referral statistics.'''
    service = ReferralService(db)
    return service.get_referral_stats(current_user.id)

@router.post("/rewards/{reward_id}/claim")
async def claim_reward(
    reward_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Claim a referral reward.'''
    service = ReferralService(db)
    result = service.claim_reward(current_user.id, reward_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
"""
