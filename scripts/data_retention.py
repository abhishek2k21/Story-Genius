"""
Data Retention Policy Automation.
Automatically delete data after retention period expires (GDPR compliance).
"""
from datetime import datetime, timedelta
from app.database import get_db
from app.models.privacy import AuditLog, DataDeletionRequest
from app.models.video import Video
from app.models.user import User
from sql

alchemy.orm import Session
from typing import Dict
import logging

logger = logging.getLogger(__name__)


# Data retention periods (GDPR Article 5)
RETENTION_POLICIES = {
    # User data
    "deleted_accounts": timedelta(days=30),  # 30-day grace period
    
    # Activity logs
    "audit_logs": timedelta(days=90),  # 90 days
    "api_access_logs": timedelta(days=365),  # 1 year
    
    # Business data
    "video_metadata": timedelta(days=365),  # 1 year after deletion
    "temp_files": timedelta(days=7),  # 7 days
    
    # Legal requirements
    "payment_records": timedelta(days=2555),  # 7 years (legal requirement)
    "tax_documents": timedelta(days=2555),  # 7 years
}


class DataRetentionService:
    """Service for automated data retention enforcement."""
    
    def __init__(self):
        self.db: Session = next(get_db())
    
    async def enforce_all_policies(self) -> Dict[str, int]:
        """
        Enforce all data retention policies.
        
        Returns:
            Dictionary of deleted record counts
        """
        results = {}
        
        logger.info("Starting data retention enforcement...")
        
        # Enforce each policy
        results["audit_logs"] = await self.delete_old_audit_logs()
        results["deleted_accounts"] = await self.delete_expired_accounts()
        results["temp_videos"] = await self.delete_temp_videos()
        
        logger.info(f"Data retention enforcement complete: {results}")
        
        return results
    
    async def delete_old_audit_logs(self) -> int:
        """Delete audit logs older than retention period."""
        retention_period = RETENTION_POLICIES["audit_logs"]
        cutoff_date = datetime.utcnow() - retention_period
        
        # Count records to delete
        count = self.db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).count()
        
        if count > 0:
            # Delete old logs
            self.db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Deleted {count} audit logs older than {retention_period}")
        
        return count
    
    async def delete_expired_accounts(self) -> int:
        """Delete accounts that passed grace period."""
        # Find deletion requests that passed grace period
        now = datetime.utcnow()
        
        expired_requests = self.db.query(DataDeletionRequest).filter(
            DataDeletionRequest.status == "pending",
            DataDeletionRequest.grace_period_ends < now,
            DataDeletionRequest.cancelled == False
        ).all()
        
        count = 0
        
        for request in expired_requests:
            try:
                # Delete user data
                await self._delete_user_data(request.user_id)
                
                # Update request status
                request.status = "completed"
                request.completed_at = now
                
                count += 1
                
                logger.warning(f"Deleted account {request.user_id} (grace period expired)")
            
            except Exception as e:
                logger.error(f"Failed to delete account {request.user_id}: {e}")
                request.status = "failed"
        
        self.db.commit()
        
        return count
    
    async def _delete_user_data(self, user_id: str):
        """
        Delete all user data permanently.
        
        Args:
            user_id: User ID to delete
        """
        # Delete videos
        self.db.query(Video).filter_by(user_id=user_id).delete()
        
        # Delete audit logs for this user
        self.db.query(AuditLog).filter_by(user_id=user_id).delete()
        
        # Anonymize user record (keep for audit trail)
        user = self.db.query(User).filter_by(id=user_id).first()
        if user:
            user.email = f"deleted_{user_id}@deleted.local"
            user.name = "Deleted User"
            user.deleted_at = datetime.utcnow()
            user.anonymized = True
        
        logger.warning(f"User data deleted for {user_id}")
    
    async def delete_temp_videos(self) -> int:
        """Delete temporary videos older than 7 days."""
        retention_period = RETENTION_POLICIES["temp_files"]
        cutoff_date = datetime.utcnow() - retention_period
        
        # Find temp/failed videos
        count = self.db.query(Video).filter(
            Video.status.in_(["processing_failed", "temp"]),
            Video.created_at < cutoff_date
        ).count()
        
        if count > 0:
            self.db.query(Video).filter(
                Video.status.in_(["processing_failed", "temp"]),
                Video.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Deleted {count} temporary videos")
        
        return count
    
    async def get_retention_status(self) -> Dict:
        """Get current retention status for all policies."""
        status = {}
        
        # Audit logs
        oldest_audit = self.db.query(AuditLog).order_by(AuditLog.timestamp).first()
        if oldest_audit:
            age = (datetime.utcnow() - oldest_audit.timestamp).days
            status["audit_logs"] = {
                "oldest_record_days": age,
                "retention_days": RETENTION_POLICIES["audit_logs"].days,
                "compliant": age <= RETENTION_POLICIES["audit_logs"].days
            }
        
        # Deleted accounts
        pending_deletions = self.db.query(DataDeletionRequest).filter_by(
            status="pending",
            cancelled=False
        ).count()
        
        status["pending_deletions"] = pending_deletions
        
        return status


# Celery task for automated retention (run daily)
async def enforce_data_retention_task():
    """
    Celery task to enforce data retention policies.
    Run daily at 2 AM UTC.
    """
    service = DataRetentionService()
    results = await service.enforce_all_policies()
    
    logger.info(f"Data retention task completed: {results}")
    
    return results


if __name__ == "__main__":
    # Manual execution for testing
    import asyncio
    
    async def main():
        service = DataRetentionService()
        results = await service.enforce_all_policies()
        print(f"Retention enforcement results: {results}")
    
    asyncio.run(main())
