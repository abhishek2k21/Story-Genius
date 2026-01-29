"""
Net Promoter Score (NPS) Tracking System.
Measure customer satisfaction and loyalty.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class NPSScore(str, Enum):
    """NPS response categories."""
    DETRACTOR = "detractor"  # 0-6
    PASSIVE = "passive"      # 7-8
    PROMOTER = "promoter"    # 9-10


class NPSResponse:
    """NPS survey response model."""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        score: int,
        category: NPSScore,
        feedback: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.score = score
        self.category = category
        self.feedback = feedback
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "score": self.score,
            "category": self.category.value,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat()
        }


class NPSTracker:
    """Track and analyze NPS scores."""
    
    def __init__(self, cs_service, email_service):
        self.cs_service = cs_service
        self.email_service = email_service
        self.responses: List[NPSResponse] = []
    
    def record_nps_response(
        self,
        user_id: str,
        score: int,
        feedback: Optional[str] = None
    ) -> Dict:
        """
        Record NPS survey response.
        
        Args:
            user_id: User ID
            score: NPS score (0-10)
            feedback: Optional written feedback
            
        Returns:
            Response details
        """
        # Validate score
        if not 0 <= score <= 10:
            raise ValueError("Score must be between 0 and 10")
        
        # Categorize response
        if score <= 6:
            category = NPSScore.DETRACTOR
        elif score <= 8:
            category = NPSScore.PASSIVE
        else:
            category = NPSScore.PROMOTER
        
        # Create response
        response_id = str(uuid.uuid4())
        
        response = NPSResponse(
            id=response_id,
            user_id=user_id,
            score=score,
            category=category,
            feedback=feedback
        )
        
        # Save to database
        self.responses.append(response)
        self._save_response(response)
        
        logger.info(f"Recorded NPS response: {score} ({category.value}) from user {user_id}")
        
        # Take action based on category
        if category == NPSScore.DETRACTOR:
            # Create CS task for follow-up
            self._create_cs_task(user_id, score, feedback)
            
            # Send thank you + follow-up email
            self.email_service.send_email(
                to_user_id=user_id,
                template="nps_detractor_followup",
                params={"score": score}
            )
            
        elif category == NPSScore.PROMOTER:
            # Ask for testimonial or referral
            self.email_service.send_email(
                to_user_id=user_id,
                template="nps_promoter_thankyou",
                params={"score": score}
            )
        
        return response.to_dict()
    
    def _create_cs_task(self, user_id: str, score: int, feedback: Optional[str]):
        """Create customer success task for detractor."""
        task = {
            "type": "nps_detractor_followup",
            "user_id": user_id,
            "priority": "high",
            "nps_score": score,
            "feedback": feedback,
            "action_required": "Personal outreach within 24 hours",
            "created_at": datetime.utcnow()
        }
        
        self.cs_service.create_task(task)
        logger.warning(f"Created CS task for detractor (score: {score})")
    
    def calculate_nps(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_segment: Optional[str] = None
    ) -> Dict:
        """
        Calculate NPS score.
        
        NPS = % Promoters - % Detractors
        Range: -100 to +100
        
        Args:
            start_date: Start date for responses
            end_date: End date for responses
            user_segment: Filter by segment (free, pro, enterprise)
            
        Returns:
            NPS score and breakdown
        """
        # Get filtered responses
        responses = self._get_responses(start_date, end_date, user_segment)
        
        if not responses:
            return {
                "nps": 0,
                "responses": 0,
                "message": "No responses in date range"
            }
        
        total = len(responses)
        promoters = len([r for r in responses if r.category == NPSScore.PROMOTER])
        passives = len([r for r in responses if r.category == NPSScore.PASSIVE])
        detractors = len([r for r in responses if r.category == NPSScore.DETRACTOR])
        
        # Calculate percentages
        promoter_pct = (promoters / total) * 100
        passive_pct = (passives / total) * 100
        detractor_pct = (detractors / total) * 100
        
        # Calculate NPS
        nps = promoter_pct - detractor_pct
        
        return {
            "nps": round(nps, 1),
            "grade": self._get_nps_grade(nps),
            "total_responses": total,
            "breakdown": {
                "promoters": {
                    "count": promoters,
                    "percentage": round(promoter_pct, 1)
                },
                "passives": {
                    "count": passives,
                    "percentage": round(passive_pct, 1)
                },
                "detractors": {
                    "count": detractors,
                    "percentage": round(detractor_pct, 1)
                }
            },
            "period": {
                "start": start_date.isoformat() if start_date else "all_time",
                "end": end_date.isoformat() if end_date else "now"
            }
        }
    
    def _get_nps_grade(self, nps: float) -> str:
        """Get NPS grade based on score."""
        if nps >= 70:
            return "World Class"
        elif nps >= 50:
            return "Excellent"
        elif nps >= 30:
            return "Great"
        elif nps >= 0:
            return "Good"
        else:
            return "Needs Improvement"
    
    def get_nps_trend(self, months: int = 6) -> List[Dict]:
        """
        Get NPS trend over time.
        
        Args:
            months: Number of months to analyze
            
        Returns:
            Monthly NPS scores
        """
        trend = []
        
        for i in range(months):
            # Calculate month boundaries
            end_date = datetime.utcnow() - timedelta(days=30 * i)
            start_date = end_date - timedelta(days=30)
            
            # Calculate NPS for month
            month_nps = self.calculate_nps(start_date, end_date)
            
            trend.append({
                "month": start_date.strftime("%B %Y"),
                "nps": month_nps["nps"],
                "responses": month_nps["total_responses"]
            })
        
        return list(reversed(trend))
    
    def get_detractor_feedback(self, limit: int = 10) -> List[Dict]:
        """
        Get recent detractor feedback for analysis.
        
        Args:
            limit: Number of responses to return
            
        Returns:
            Recent detractor responses with feedback
        """
        detractors = [
            r for r in self.responses
            if r.category == NPSScore.DETRACTOR and r.feedback
        ]
        
        # Sort by most recent
        detractors.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "user_id": d.user_id,
                "score": d.score,
                "feedback": d.feedback,
                "created_at": d.created_at.isoformat()
            }
            for d in detractors[:limit]
        ]
    
    def _get_responses(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        user_segment: Optional[str]
    ) -> List[NPSResponse]:
        """Get filtered responses."""
        responses = self.responses
        
        if start_date:
            responses = [r for r in responses if r.created_at >= start_date]
        
        if end_date:
            responses = [r for r in responses if r.created_at <= end_date]
        
        # TODO: Filter by user segment (would query user data)
        
        return responses
    
    def _save_response(self, response: NPSResponse):
        """Save response to database."""
        # Database save logic here
        pass


# NPS Survey Email Templates
NPS_SURVEY_EMAIL = """
<h2>How likely are you to recommend Video Creator?</h2>
<p>On a scale of 0-10, how likely are you to recommend our service to a friend or colleague?</p>

<div style="text-align: center; margin: 20px 0;">
  <!-- 0-10 buttons -->
  <a href="{{survey_url}}?score=10" style="padding: 10px; margin: 2px; background: #4CAF50; color: white; text-decoration: none;">10</a>
  <a href="{{survey_url}}?score=9" style="padding: 10px; margin: 2px; background: #8BC34A; color: white; text-decoration: none;">9</a>
  <!-- ... other scores ... -->
  <a href="{{survey_url}}?score=0" style="padding: 10px; margin: 2px; background: #F44336; color: white; text-decoration: none;">0</a>
</div>

<p style="font-size: 12px; color: #666;">
  0 = Not at all likely | 10 = Extremely likely
</p>
"""

# FastAPI endpoints
"""
from fastapi import APIRouter, Depends
from app.services.nps_tracker import NPSTracker
from pydantic import BaseModel

router = APIRouter(prefix="/nps", tags=["nps"])

class NPSSubmission(BaseModel):
    score: int
    feedback: Optional[str] = None

@router.post("/submit")
async def submit_nps(
    data: NPSSubmission,
    current_user: User = Depends(get_current_user)
):
    '''Submit NPS survey response.'''
    tracker = NPSTracker(cs_service, email_service)
    
    return tracker.record_nps_response(
        user_id=current_user.id,
        score=data.score,
        feedback=data.feedback
    )

@router.get("/score")
async def get_nps_score(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    '''Get current NPS score (admin only).'''
    tracker = NPSTracker(cs_service, email_service)
    
    return tracker.calculate_nps(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None
    )

@router.get("/trend")
async def get_nps_trend(months: int = 6):
    '''Get NPS trend over time (admin only).'''
    tracker = NPSTracker(cs_service, email_service)
    return tracker.get_nps_trend(months)
"""
