"""
Webhook System.
Send events to external URLs for third-party integrations.
"""
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp
import hashlib
import hmac
import uuid
import logging

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event types."""
    VIDEO_CREATED = "video.created"
    VIDEO_PUBLISHED = "video.published"
    VIDEO_DELETED = "video.deleted"
    USER_SUBSCRIBED = "user.subscribed"
    USER_CANCELLED = "user.cancelled"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"


class Webhook:
    """Webhook configuration model."""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        url: str,
        events: List[str],
        secret: str
    ):
        self.id = id
        self.user_id = user_id
        self.url = url
        self.events = events
        self.secret = secret
        self.active = True
        self.created_at = datetime.utcnow()
        self.last_triggered: Optional[datetime] = None
        self.delivery_successes = 0
        self.delivery_failures = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "webhook_id": self.id,
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "delivery_stats": {
                "successes": self.delivery_successes,
                "failures": self.delivery_failures,
                "success_rate": round(
                    self.delivery_successes / (self.delivery_successes + self.delivery_failures) * 100, 1
                ) if (self.delivery_successes + self.delivery_failures) > 0 else 0
            }
        }


class WebhookService:
    """Manage webhooks and event delivery."""
    
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.delivery_queue: List[Dict] = []
    
    def register_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict:
        """
        Register webhook endpoint.
        
        Args:
            user_id: User ID
            url: Webhook URL (must be HTTPS)
            events: List of events to subscribe to
            secret: Optional signing secret (generated if not provided)
            
        Returns:
            Webhook details with secret
        """
        # Validate URL
        if not url.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        
        # Validate events
        valid_events = [e.value for e in WebhookEvent]
        for event in events:
            if event not in valid_events:
                raise ValueError(f"Invalid event: {event}")
        
        # Generate webhook ID and secret
        webhook_id = str(uuid.uuid4())
        webhook_secret = secret or self._generate_secret()
        
        # Create webhook
        webhook = Webhook(
            id=webhook_id,
            user_id=user_id,
            url=url,
            events=events,
            secret=webhook_secret
        )
        
        # Save webhook
        self.webhooks[webhook_id] = webhook
        self._save_webhook(webhook)
        
        logger.info(f"Registered webhook {webhook_id} for user {user_id}")
        
        return {
            "webhook_id": webhook_id,
            "url": url,
            "events": events,
            "secret": webhook_secret,
            "message": "Webhook registered successfully. Keep the secret safe!"
        }
    
    def _generate_secret(self) -> str:
        """Generate secure webhook secret."""
        import secrets
        return f"whsec_{secrets.token_urlsafe(32)}"
    
    async def trigger_event(
        self,
        event_type: str,
        data: Dict,
        user_id: str
    ):
        """
        Trigger webhook event.
        
        Sends event to all registered webhooks for this user.
        
        Args:
            event_type: Event type (e.g., "video.created")
            data: Event data
            user_id: User ID
        """
        # Get webhooks for this user and event
        webhooks = self._get_webhooks_for_event(user_id, event_type)
        
        if not webhooks:
            logger.debug(f"No webhooks registered for {event_type}")
            return
        
        logger.info(f"Triggering {len(webhooks)} webhooks for {event_type}")
        
        # Send to each webhook
        for webhook in webhooks:
            # Queue delivery (async)
            asyncio.create_task(self._deliver_webhook(webhook, event_type, data))
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        data: Dict
    ):
        """
        Deliver webhook to endpoint.
        
        Args:
            webhook: Webhook configuration
            event_type: Event type
            data: Event data
        """
        # Build payload
        payload = {
            "id": str(uuid.uuid4()),
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook.id
        }
        
        # Sign payload
        signature = self._sign_payload(payload, webhook.secret)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VideoCreator-Webhooks/1.0",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": webhook.id
        }
        
        # Send HTTP POST with retry
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            # Success
                            webhook.last_triggered = datetime.utcnow()
                            webhook.delivery_successes += 1
                            
                            logger.info(f"Webhook delivered successfully: {webhook.url}")
                            return
                        else:
                            # Server error
                            logger.warning(f"Webhook returned {response.status}: {webhook.url}")
                            retry_count += 1
                            
                            if retry_count < max_retries:
                                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
            except asyncio.TimeoutError:
                logger.error(f"Webhook timeout: {webhook.url}")
                retry_count += 1
                
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
            
            except Exception as e:
                logger.error(f"Webhook delivery error: {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
        
        # All retries failed
        webhook.delivery_failures += 1
        self._record_failure(webhook.id, event_type, str(e) if 'e' in locals() else "Max retries exceeded")
        
        logger.error(f"Webhook delivery failed after {max_retries} attempts: {webhook.url}")
    
    def _sign_payload(self, payload: Dict, secret: str) -> str:
        """
        Sign webhook payload with HMAC-SHA256.
        
        Args:
            payload: Payload to sign
            secret: Webhook secret
            
        Returns:
            Signature string
        """
        import json
        
        # Serialize payload
        payload_str = json.dumps(payload, sort_keys=True)
        
        # Create HMAC signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _get_webhooks_for_event(
        self,
        user_id: str,
        event_type: str
    ) -> List[Webhook]:
        """Get active webhooks for user and event."""
        webhooks = []
        
        for webhook in self.webhooks.values():
            if (
                webhook.user_id == user_id and
                webhook.active and
                event_type in webhook.events
            ):
                webhooks.append(webhook)
        
        return webhooks
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict]:
        """Get webhook by ID."""
        webhook = self.webhooks.get(webhook_id)
        return webhook.to_dict() if webhook else None
    
    def list_webhooks(self, user_id: str) -> List[Dict]:
        """List all webhooks for user."""
        user_webhooks = [
            w for w in self.webhooks.values()
            if w.user_id == user_id
        ]
        
        return [w.to_dict() for w in user_webhooks]
    
    def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """Delete webhook."""
        webhook = self.webhooks.get(webhook_id)
        
        if not webhook:
            return False
        
        if webhook.user_id != user_id:
            raise PermissionError("Not authorized")
        
        del self.webhooks[webhook_id]
        logger.info(f"Deleted webhook {webhook_id}")
        
        return True
    
    def _record_failure(self, webhook_id: str, event_type: str, error: str):
        """Record webhook delivery failure."""
        # Save to database for monitoring
        logger.warning(f"Webhook failure: {webhook_id}, event: {event_type}, error: {error}")
    
    def _save_webhook(self, webhook: Webhook):
        """Save webhook to database."""
        pass


# Example: Trigger webhook when video is created
"""
from app.services.webhook_service import WebhookService, WebhookEvent

webhook_service = WebhookService()

# When video is created
await webhook_service.trigger_event(
    event_type=WebhookEvent.VIDEO_CREATED.value,
    data={
        "video_id": "v123",
        "title": "My Video",
        "created_at": datetime.utcnow().isoformat()
    },
    user_id="user123"
)
"""


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None

@router.post("/")
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user)
):
    '''Register new webhook.'''
    service = WebhookService()
    
    return service.register_webhook(
        user_id=current_user.id,
        url=str(data.url),
        events=data.events,
        secret=data.secret
    )

@router.get("/")
async def list_webhooks(current_user: User = Depends(get_current_user)):
    '''List user webhooks.'''
    service = WebhookService()
    return service.list_webhooks(current_user.id)

@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Get webhook details.'''
    service = WebhookService()
    webhook = service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return webhook

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Delete webhook.'''
    service = WebhookService()
    
    success = service.delete_webhook(webhook_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"success": True}
"""
