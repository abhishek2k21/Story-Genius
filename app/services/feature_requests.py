"""
Feature Request Management System.
Track, vote, and prioritize feature requests.
"""
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FeatureStatus(str, Enum):
    """Feature request status."""
    OPEN = "open"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    DECLINED = "declined"


class FeatureCategory(str, Enum):
    """Feature category."""
    UI_UX = "ui_ux"
    API = "api"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    OTHER = "other"


class FeatureRequest:
    """Feature request model."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        category: FeatureCategory,
        created_by: str,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.status = FeatureStatus.OPEN
        self.votes = 1  # Creator auto-votes
        self.voters: List[str] = [created_by]
        self.comments: List[Dict] = []
        
        # Internal fields
        self.business_value = 0  # 1-10
        self.implementation_effort = 0  # 1-10 (higher = more effort)
        self.rice_score = 0  # Calculated
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "votes": self.votes,
            "voters_count": len(self.voters),
            "comments_count": len(self.comments),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "business_value": self.business_value,
            "implementation_effort": self.implementation_effort,
            "rice_score": self.rice_score
        }


class FeatureRequestManager:
    """Manage feature requests and voting."""
    
    def __init__(self):
        self.requests: Dict[str, FeatureRequest] = {}
    
    def create_request(
        self,
        title: str,
        description: str,
        category: str,
        user_id: str
    ) -> FeatureRequest:
        """
        Create a new feature request.
        
        Args:
            title: Feature title
            description: Detailed description
            category: Feature category
            user_id: Creator user ID
            
        Returns:
            Created feature request
        """
        request_id = self._generate_id()
        
        request = FeatureRequest(
            id=request_id,
            title=title,
            description=description,
            category=FeatureCategory(category),
            created_by=user_id
        )
        
        self.requests[request_id] = request
        
        logger.info(f"Created feature request: {title} by {user_id}")
        
        return request
    
    def vote(self, request_id: str, user_id: str) -> bool:
        """
        Vote for a feature request.
        
        Args:
            request_id: Feature request ID
            user_id: User ID
            
        Returns:
            Success status
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        # Check if already voted
        if user_id in request.voters:
            logger.warning(f"User {user_id} already voted for {request_id}")
            return False
        
        # Add vote
        request.votes += 1
        request.voters.append(user_id)
        
        logger.info(f"User {user_id} voted for {request_id} (total: {request.votes})")
        
        return True
    
    def unvote(self, request_id: str, user_id: str) -> bool:
        """Remove vote from feature request."""
        request = self.requests.get(request_id)
        if not request or user_id not in request.voters:
            return False
        
        request.votes -= 1
        request.voters.remove(user_id)
        
        return True
    
    def add_comment(
        self,
        request_id: str,
        user_id: str,
        comment: str
    ) -> bool:
        """
        Add comment to feature request.
        
        Args:
            request_id: Feature request ID
            user_id: User ID
            comment: Comment text
            
        Returns:
            Success status
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        request.comments.append({
            "id": self._generate_id(),
            "user_id": user_id,
            "comment": comment,
            "created_at": datetime.now().isoformat()
        })
        
        return True
    
    def update_status(
        self,
        request_id: str,
        status: str,
        admin_user_id: str
    ) -> bool:
        """
        Update feature request status (admin only).
        
        Args:
            request_id: Feature request ID
            status: New status
            admin_user_id: Admin user ID
            
        Returns:
            Success status
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        request.status = FeatureStatus(status)
        
        logger.info(f"Admin {admin_user_id} updated {request_id} status to {status}")
        
        return True
    
    def get_top_requests(self, limit: int = 10, category: Optional[str] = None) -> List[Dict]:
        """
        Get top-voted feature requests.
        
        Args:
            limit: Number of requests to return
            category: Optional category filter
            
        Returns:
            List of top feature requests
        """
        requests = list(self.requests.values())
        
        # Filter by status (only open)
        requests = [r for r in requests if r.status == FeatureStatus.OPEN]
        
        # Filter by category if specified
        if category:
            requests = [r for r in requests if r.category.value == category]
        
        # Sort by votes
        requests.sort(key=lambda x: x.votes, reverse=True)
        
        return [r.to_dict() for r in requests[:limit]]
    
    def prioritize_with_rice(self) -> List[Dict]:
        """
        Prioritize feature requests using RICE scoring.
        
        RICE = (Reach × Impact × Confidence) / Effort
        
        - Reach: Number of votes (user demand)
        - Impact: Business value (1-10)
        - Confidence: Always 0.8 for voted features
        - Effort: Implementation effort (1-10, higher = more effort)
        
        Returns:
            Prioritized list of features
        """
        requests = [r for r in self.requests.values() if r.status == FeatureStatus.OPEN]
        
        # Calculate RICE scores
        for request in requests:
            reach = request.votes
            impact = request.business_value or 5  # Default medium impact
            confidence = 0.8
            effort = request.implementation_effort or 5  # Default medium effort
            
            request.rice_score = (reach * impact * confidence) / effort if effort > 0 else 0
        
        # Sort by RICE score
        requests.sort(key=lambda x: x.rice_score, reverse=True)
        
        return [r.to_dict() for r in requests]
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """Get a specific feature request."""
        request = self.requests.get(request_id)
        return request.to_dict() if request else None
    
    def get_user_requests(self, user_id: str) -> List[Dict]:
        """Get all requests created by user."""
        user_requests = [
            r for r in self.requests.values()
            if r.created_by == user_id
        ]
        
        return [r.to_dict() for r in user_requests]
    
    def get_user_voted_requests(self, user_id: str) -> List[Dict]:
        """Get all requests user has voted for."""
        voted_requests = [
            r for r in self.requests.values()
            if user_id in r.voters
        ]
        
        return [r.to_dict() for r in voted_requests]
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return str(uuid.uuid4())


# API Endpoints (FastAPI)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.feature_requests import FeatureRequestManager

router = APIRouter(prefix="/features", tags=["features"])
manager = FeatureRequestManager()

class CreateFeatureRequest(BaseModel):
    title: str
    description: str
    category: str

@router.post("/requests")
async def create_feature_request(
    data: CreateFeatureRequest,
    current_user: User = Depends(get_current_user)
):
    '''Create a feature request.'''
    request = manager.create_request(
        title=data.title,
        description=data.description,
        category=data.category,
        user_id=current_user.id
    )
    return request.to_dict()

@router.get("/requests")
async def list_feature_requests(
    limit: int = 10,
    category: Optional[str] = None
):
    '''Get top feature requests.'''
    return manager.get_top_requests(limit=limit, category=category)

@router.post("/requests/{request_id}/vote")
async def vote_for_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Vote for a feature request.'''
    success = manager.vote(request_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot vote")
    return {"success": True}

@router.delete("/requests/{request_id}/vote")
async def unvote_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Remove vote from feature request.'''
    success = manager.unvote(request_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot unvote")
    return {"success": True}

@router.get("/requests/prioritized")
async def get_prioritized_requests(admin: User = Depends(require_admin)):
    '''Get RICE-prioritized feature requests (admin only).'''
    return manager.prioritize_with_rice()
"""
