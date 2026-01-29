"""
Marketing Automation System.
Automated email campaigns for onboarding, engagement, and retention.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class CampaignTrigger(str, Enum):
    """Campaign trigger events."""
    USER_SIGNUP = "user_signup"
    FIRST_VIDEO_CREATED = "first_video_created"
    VIDEO_COUNT_MILESTONE = "video_count_milestone"
    USER_INACTIVE = "user_inactive"
    SUBSCRIPTION_STARTED = "subscription_started"
    SUBSCRIPTION_ENDING = "subscription_ending"
    MONTHLY_NEWSLETTER = "monthly_newsletter"


class EmailCampaign:
    """Automated email campaign."""
    
    def __init__(
        self,
        name: str,
        trigger: CampaignTrigger,
        delay_hours: int,
        subject: str,
        template: str,
        condition: Optional[callable] = None
    ):
        self.name = name
        self.trigger = trigger
        self.delay_hours = delay_hours
        self.subject = subject
        self.template = template
        self.condition = condition  # Optional condition function
        self.enabled = True


class MarketingAutomation:
    """Automated marketing campaigns."""
    
    def __init__(self, email_service, analytics_service):
        self.email_service = email_service
        self.analytics_service = analytics_service
        self.campaigns = self._setup_campaigns()
        self.scheduled_emails: List[Dict] = []
    
    def _setup_campaigns(self) -> List[EmailCampaign]:
        """Define automated email campaigns."""
        campaigns = []
        
        # === ONBOARDING SERIES ===
        
        campaigns.append(EmailCampaign(
            name="Welcome Email",
            trigger=CampaignTrigger.USER_SIGNUP,
            delay_hours=0,
            subject="Welcome to Video Creator! Let's get started 🎬",
            template="welcome",
            condition=None  # Always send
        ))
        
        campaigns.append(EmailCampaign(
            name="First Video Tips",
            trigger=CampaignTrigger.USER_SIGNUP,
            delay_hours=24,
            subject="Create your first video in 5 minutes",
            template="first_video_tips",
            condition=lambda user: user.get("videos_created", 0) == 0
        ))
        
        campaigns.append(EmailCampaign(
            name="Template Showcase",
            trigger=CampaignTrigger.USER_SIGNUP,
            delay_hours=72,
            subject="7 templates to jumpstart your creativity",
            template="template_showcase",
            condition=lambda user: user.get("videos_created", 0) < 3
        ))
        
        campaigns.append(EmailCampaign(
            name="Activation Nudge",
            trigger=CampaignTrigger.USER_INACTIVE,
            delay_hours=0,
            subject="Still there? Here's how to get started",
            template="activation_nudge",
            condition=lambda user: user.get("days_since_signup") == 7 and user.get("videos_created", 0) == 0
        ))
        
        # === ENGAGEMENT SERIES ===
        
        campaigns.append(EmailCampaign(
            name="Feature Discovery",
            trigger=CampaignTrigger.FIRST_VIDEO_CREATED,
            delay_hours=48,
            subject="You created your first video! Here's what's next 🚀",
            template="feature_discovery",
            condition=None
        ))
        
        campaigns.append(EmailCampaign(
            name="Pro Upgrade Offer",
            trigger=CampaignTrigger.VIDEO_COUNT_MILESTONE,
            delay_hours=0,
            subject="Upgrade to Pro and unlock advanced features",
            template="pro_upgrade_offer",
            condition=lambda user: user.get("videos_created") >= 10 and user.get("tier") == "free"
        ))
        
        # === RETENTION SERIES ===
        
        campaigns.append(EmailCampaign(
            name="We Miss You - 30 Days",
            trigger=CampaignTrigger.USER_INACTIVE,
            delay_hours=0,
            subject="We miss you! What can we improve?",
            template="winback_30days",
            condition=lambda user: user.get("days_inactive") == 30
        ))
        
        campaigns.append(EmailCampaign(
            name="Feedback Request - 60 Days",
            trigger=CampaignTrigger.USER_INACTIVE,
            delay_hours=0,
            subject="Quick feedback: Why did you stop creating?",
            template="feedback_request",
            condition=lambda user: user.get("days_inactive") == 60
        ))
        
        # === PRODUCT UPDATES ===
        
        campaigns.append(EmailCampaign(
            name="Monthly Newsletter",
            trigger=CampaignTrigger.MONTHLY_NEWSLETTER,
            delay_hours=0,
            subject="What's new: Features, tips, and success stories",
            template="monthly_newsletter",
            condition=None
        ))
        
        logger.info(f"Initialized {len(campaigns)} email campaigns")
        
        return campaigns
    
    async def trigger_campaign(
        self,
        trigger: str,
        user_id: str,
        user_data: Dict
    ):
        """
        Trigger campaigns for a specific event.
        
        Args:
            trigger: Trigger event
            user_id: User ID
            user_data: User data for conditions
        """
        trigger_enum = CampaignTrigger(trigger)
        
        # Find matching campaigns
        matching_campaigns = [
            c for c in self.campaigns
            if c.trigger == trigger_enum and c.enabled
        ]
        
        for campaign in matching_campaigns:
            # Check condition
            if campaign.condition and not campaign.condition(user_data):
                logger.debug(f"Skipping {campaign.name} - condition not met")
                continue
            
            # Schedule email
            send_at = datetime.utcnow() + timedelta(hours=campaign.delay_hours)
            
            scheduled_email = {
                "campaign_name": campaign.name,
                "user_id": user_id,
                "email": user_data.get("email"),
                "subject": campaign.subject,
                "template": campaign.template,
                "scheduled_for": send_at,
                "status": "scheduled"
            }
            
            self.scheduled_emails.append(scheduled_email)
            
            logger.info(f"Scheduled {campaign.name} for {user_id} at {send_at}")
    
    async def process_email_queue(self):
        """
        Background worker to process scheduled emails.
        Runs every minute.
        """
        logger.info("Starting email queue processor")
        
        while True:
            try:
                now = datetime.utcnow()
                
                # Find due emails
                due_emails = [
                    e for e in self.scheduled_emails
                    if e["status"] == "scheduled" and e["scheduled_for"] <= now
                ]
                
                if due_emails:
                    logger.info(f"Processing {len(due_emails)} due emails")
                
                for email in due_emails:
                    try:
                        # Send email
                        await self._send_campaign_email(email)
                        
                        # Mark as sent
                        email["status"] = "sent"
                        email["sent_at"] = now
                        
                    except Exception as e:
                        logger.error(f"Failed to send email: {e}")
                        email["status"] = "failed"
                        email["error"] = str(e)
                
                # Wait 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in email queue processor: {e}")
                await asyncio.sleep(60)
    
    async def _send_campaign_email(self, email: Dict):
        """Send campaign email."""
        logger.info(f"Sending {email['campaign_name']} to {email['email']}")
        
        # Send via email service
        await self.email_service.send_template_email(
            to=email["email"],
            subject=email["subject"],
            template=email["template"],
            user_id=email["user_id"]
        )
    
    def get_campaign_stats(self, campaign_name: str) -> Dict:
        """Get statistics for a campaign."""
        emails = [
            e for e in self.scheduled_emails
            if e["campaign_name"] == campaign_name
        ]
        
        total_sent = len([e for e in emails if e["status"] == "sent"])
        total_failed = len([e for e in emails if e["status"] == "failed"])
        total_scheduled = len([e for e in emails if e["status"] == "scheduled"])
        
        # Calculate open rate, click rate (would come from email service)
        open_rate = 42.5  # Placeholder
        click_rate = 8.3  # Placeholder
        
        return {
            "campaign_name": campaign_name,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_scheduled": total_scheduled,
            "open_rate": open_rate,
            "click_rate": click_rate
        }


# Email templates (simplified versions)
EMAIL_TEMPLATES = {
    "welcome": """
    <h1>Welcome to Video Creator!</h1>
    <p>We're excited to have you here. Let's create something amazing together.</p>
    <p><a href="{{create_video_url}}">Create Your First Video</a></p>
    """,
    
    "first_video_tips": """
    <h1>Ready to create your first video?</h1>
    <p>Here are 3 quick tips to get started:</p>
    <ol>
        <li>Choose a template to save time</li>
        <li>Keep it short (30-60 seconds)</li>
        <li>Add captions for better engagement</li>
    </ol>
    <p><a href="{{templates_url}}">Browse Templates</a></p>
    """,
    
    "pro_upgrade_offer": """
    <h1>You've created 10 videos! 🎉</h1>
    <p>Upgrade to Pro and unlock:</p>
    <ul>
        <li>Unlimited videos</li>
        <li>Custom branding</li>
        <li>Advanced templates</li>
        <li>Priority support</li>
    </ul>
    <p><a href="{{upgrade_url}}">Upgrade to Pro - 20% Off</a></p>
    """
}
