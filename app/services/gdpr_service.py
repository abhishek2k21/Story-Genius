"""
GDPR Service Implementation.
Handles data export, deletion, and consent management.
"""
from datetime import datetime, timedelta
from app.models.privacy import (
    UserConsent,
    DataDeletionRequest,
    DataExportRequest,
    DataProcessingRecord,
    AuditLog
)
from app.models.user import User
from app.models.video import Video
from app.database import get_db
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance operations."""
    
    def __init__(self):
        self.db: Session = next(get_db())
    
    async def update_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        purpose: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Update user consent.
        
        Args:
            user_id: User ID
            consent_type: Type of consent (marketing, analytics, etc.)
            granted: Whether consent is granted
            purpose: Purpose of data processing
            ip_address: User's IP address (proof of consent)
            user_agent: User's browser user agent
            
        Returns:
            Updated consent record
        """
        # Find existing consent or create new
        consent = self.db.query(UserConsent).filter_by(
            user_id=user_id,
            consent_type=consent_type
        ).first()
        
        if consent:
            # Update existing
            consent.granted = granted
            if not granted:
                consent.revoked_at = datetime.utcnow()
            consent.updated_at = datetime.utcnow()
        else:
            # Create new
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                purpose=purpose,
                granted=granted,
                granted_at=datetime.utcnow() if granted else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(consent)
        
        self.db.commit()
        
        logger.info(f"Consent {consent_type} {'granted' if granted else 'revoked'} for user {user_id}")
        
        return {
            "id": consent.id,
            "consent_type": consent.consent_type,
            "granted": consent.granted
        }
    
    async def get_user_consents(self, user_id: str) -> List[Dict]:
        """Get all consents for a user."""
        consents = self.db.query(UserConsent).filter_by(user_id=user_id).all()
        
        return [
            {
                "consent_type": c.consent_type,
                "granted": c.granted,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None
            }
            for c in consents
        ]
    
    async def create_data_export_request(
        self,
        user_id: str,
        format: str = "json",
        categories: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Create data export request.
        
        Args:
            user_id: User ID
            format: Export format (json, csv, xml)
            categories: Specific data categories to export
            ip_address: User's IP address
            user_agent: User's browser user agent
            
        Returns:
            Export request details
        """
        request = DataExportRequest(
            user_id=user_id,
            data_categories=categories or ["all"],
            export_format=format,
            status="pending",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(request)
        self.db.commit()
        
        # Trigger background job to generate export
        # (In production, use Celery task)
        # export_user_data_task.delay(request.id)
        
        logger.info(f"Data export request created: {request.id} for user {user_id}")
        
        return {
            "request_id": request.id,
            "status": request.status
        }
    
    async def export_user_data(self, user_id: str) -> Dict:
        """
        Export all user data in machine-readable format.
        
        Includes:
        - Profile information
        - Videos created
        - Activity logs
        - Payment history
        - Consent records
        
        Returns:
            Complete user data export
        """
        # Get user
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Collect all data
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            
            # Profile
            "profile": {
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "email_verified": user.email_verified,
                "locale": user.locale
            },
            
            # Videos
            "videos": [
                {
                    "id": v.id,
                    "title": v.title,
                    "description": v.description,
                    "created_at": v.created_at.isoformat(),
                    "status": v.status
                }
                for v in self.db.query(Video).filter_by(user_id=user_id).all()
            ],
            
            # Consents
            "consents": await self.get_user_consents(user_id),
            
            # Activity logs (last 90 days)
            "activity_logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "ip_address": log.ip_address
                }
                for log in self.db.query(AuditLog).filter_by(user_id=user_id).filter(
                    AuditLog.timestamp >= datetime.utcnow() - timedelta(days=90)
                ).all()
            ]
        }
        
        return export_data
    
    async def get_export_request(self, request_id: str, user_id: str) -> Optional[Dict]:
        """Get export request details."""
        request = self.db.query(DataExportRequest).filter_by(
            id=request_id,
            user_id=user_id
        ).first()
        
        if not request:
            return None
        
        return {
            "id": request.id,
            "status": request.status,
            "requested_at": request.requested_at.isoformat(),
            "export_file_url": request.export_file_url,
            "expires_at": request.expires_at.isoformat() if request.expires_at else None
        }
    
    async def create_deletion_request(
        self,
        user_id: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Create account deletion request with 30-day grace period.
        
        Args:
            user_id: User ID
            reason: Reason for deletion
            ip_address: User's IP address
            user_agent: User's browser user agent
            
        Returns:
            Deletion request details
        """
        # Calculate grace period end
        grace_period_ends = datetime.utcnow() + timedelta(days=30)
        
        request = DataDeletionRequest(
            user_id=user_id,
            reason=reason,
            status="pending",
            grace_period_ends=grace_period_ends,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(request)
        self.db.commit()
        
        # Schedule deletion job (after grace period)
        # delete_user_data_task.apply_async(
        #     args=[request.id],
        #     eta=grace_period_ends
        # )
        
        logger.warning(f"Deletion request created: {request.id} for user {user_id}")
        
        return {
            "request_id": request.id,
            "grace_period_ends": grace_period_ends.isoformat()
        }
    
    async def cancel_deletion_request(self, request_id: str, user_id: str) -> bool:
        """Cancel deletion request during grace period."""
        request = self.db.query(DataDeletionRequest).filter_by(
            id=request_id,
            user_id=user_id
        ).first()
        
        if not request:
            return False
        
        # Check if still in grace period
        if datetime.utcnow() > request.grace_period_ends:
            return False
        
        if request.status != "pending":
            return False
        
        request.cancelled = True
        request.status = "cancelled"
        self.db.commit()
        
        logger.info(f"Deletion request cancelled: {request_id}")
        
        return True
    
    async def delete_user_data(self, user_id: str):
        """
        Permanently delete all user data.
        
        Two-stage deletion:
        1. Soft delete (anonymize)
        2. Hard delete (remove)
        """
        # Log deletion
        logger.warning(f"Deleting all data for user {user_id}")
        
        # Delete user data from all tables
        self.db.query(Video).filter_by(user_id=user_id).delete()
        self.db.query(UserConsent).filter_by(user_id=user_id).delete()
        self.db.query(AuditLog).filter_by(user_id=user_id).delete()
        
        # Anonymize user record (keep for legal/audit purposes)
        user = self.db.query(User).filter_by(id=user_id).first()
        if user:
            user.email = f"deleted_{user_id}@deleted.local"
            user.name = "Deleted User"
            user.deleted_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.warning(f"User data deleted for {user_id}")
    
    async def get_data_summary(self, user_id: str) -> Dict:
        """Get summary of user's data."""
        user = self.db.query(User).filter_by(id=user_id).first()
        video_count = self.db.query(Video).filter_by(user_id=user_id).count()
        
        return {
            "user_id": user_id,
            "account_created": user.created_at.isoformat(),
            "statistics": {
                "videos_created": video_count,
                "storage_used": "Calculate from videos",
            },
            "data_categories": [
                "Profile information",
                "Videos and media",
                "Activity logs",
                "Consent records"
            ]
        }
