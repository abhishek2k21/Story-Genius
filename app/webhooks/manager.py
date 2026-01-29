"""
Webhook Manager
Implements webhook subscription and event delivery with retry logic.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """Webhook event types"""
    VIDEO_CREATED = "video.created"
    VIDEO_PUBLISHED = "video.published"
    BATCH_COMPLETED = "batch.completed"
    QUALITY_APPROVED = "quality.approved"
    GENERATION_FAILED = "generation.failed"


@dataclass
class WebhookSubscription:
    """Webhook subscription"""
    id: str
    url: str
    events: List[EventType]
    secret: str  # For HMAC signing
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    id: str
    subscription_id: str
    event_type: EventType
    payload: Dict[str, Any]
    url: str
    status: str  # pending, success, failed
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class WebhookManager:
    """
    Manages webhook subscriptions and event delivery.
    """
    
    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._deliveries: List[WebhookDelivery] = []
        logger.info("WebhookManager initialized")
    
    def subscribe(
        self,
        url: str,
        events: List[EventType],
        secret: Optional[str] = None
    ) -> WebhookSubscription:
        """
        Subscribe to webhook events.
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Secret for HMAC signing (generated if not provided)
        
        Returns:
            WebhookSubscription
        """
        import uuid
        
        subscription_id = str(uuid.uuid4())
        
        if secret is None:
            # Generate random secret
            secret = hashlib.sha256(subscription_id.encode()).hexdigest()
        
        subscription = WebhookSubscription(
            id=subscription_id,
            url=url,
            events=events,
            secret=secret
        )
        
        self._subscriptions[subscription_id] = subscription
        
        logger.info(
            f"Webhook subscribed: {url} for events: "
            f"{[e.value for e in events]}"
        )
        
        return subscription
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe webhook"""
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].active = False
            logger.info(f"Webhook unsubscribed: {subscription_id}")
    
    def deliver_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any]
    ):
        """
        Deliver event to all subscribers.
        
        Args:
            event_type: Event type
            payload: Event payload
        """
        import uuid
        
        # Find subscriptions for this event
        subscribers = [
            sub for sub in self._subscriptions.values()
            if sub.active and event_type in sub.events
        ]
        
        if not subscribers:
            logger.debug(f"No subscribers for event: {event_type.value}")
            return
        
        logger.info(
            f"Delivering event {event_type.value} to {len(subscribers)} subscribers"
        )
        
        # Create delivery for each subscriber
        for subscription in subscribers:
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                url=subscription.url,
                status="pending"
            )
            
            self._deliveries.append(delivery)
            
            # Attempt delivery
            self._attempt_delivery(delivery, subscription)
    
    def _attempt_delivery(
        self,
        delivery: WebhookDelivery,
        subscription: WebhookSubscription
    ):
        """
        Attempt to deliver webhook.
        
        Args:
            delivery: Webhook delivery
            subscription: Webhook subscription
        """
        delivery.attempts += 1
        
        # Create signed payload
        signed_payload = self._sign_payload(
            delivery.payload,
            subscription.secret
        )
        
        # Mock HTTP delivery (in production: use requests/httpx)
        try:
            logger.info(
                f"Delivering webhook to {delivery.url} "
                f"(attempt {delivery.attempts}/{delivery.max_attempts})"
            )
            
            # Mock: 90% success rate
            import random
            success = random.random() < 0.9
            
            if success:
                delivery.status = "success"
                delivery.delivered_at = datetime.utcnow()
                logger.info(f"Webhook delivered successfully: {delivery.id}")
            else:
                raise Exception("Delivery failed (mock)")
                
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            
            if delivery.attempts >= delivery.max_attempts:
                delivery.status = "failed"
                logger.error(
                    f"Webhook delivery failed permanently: {delivery.id} "
                    f"(max attempts reached)"
                )
            else:
                # Retry
                logger.info(
                    f"Webhook will be retried: {delivery.id} "
                    f"({delivery.attempts}/{delivery.max_attempts})"
                )
                # In production: schedule retry with exponential backoff
    
    def _sign_payload(self, payload: Dict, secret: str) -> Dict:
        """
        Sign payload with HMAC.
        
        Args:
            payload: Payload to sign
            secret: Secret key
        
        Returns:
            Signed payload with signature
        """
        payload_json = json.dumps(payload, sort_keys=True)
        
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "payload": payload,
            "signature": signature,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_deliveries(
        self,
        subscription_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get webhook deliveries"""
        deliveries = self._deliveries
        
        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]
        
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        
        # Sort by most recent
        deliveries.sort(key=lambda d: d.created_at, reverse=True)
        
        return deliveries[:limit]
    
    def get_stats(self) -> Dict:
        """Get webhook statistics"""
        total_deliveries = len(self._deliveries)
        
        if total_deliveries == 0:
            return {
                "total_subscriptions": len(self._subscriptions),
                "active_subscriptions": sum(1 for s in self._subscriptions.values() if s.active),
                "total_deliveries": 0,
                "success_rate": 0.0
            }
        
        successful = sum(1 for d in self._deliveries if d.status == "success")
        
        return {
            "total_subscriptions": len(self._subscriptions),
            "active_subscriptions": sum(1 for s in self._subscriptions.values() if s.active),
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": sum(1 for d in self._deliveries if d.status == "failed"),
            "pending_deliveries": sum(1 for d in self._deliveries if d.status == "pending"),
            "success_rate": round((successful / total_deliveries) * 100, 2)
        }


# Global instance
webhook_manager = WebhookManager()
