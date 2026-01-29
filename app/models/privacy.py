"""
GDPR Compliance Models.
Database models for GDPR compliance tracking.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
import uuid


class UserConsent(Base):
    """
    Track user consent for data processing (GDPR Article 7).
    Records when and how user gave consent.
    """
    __tablename__ = "user_consents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Consent details
    consent_type = Column(String, nullable=False)  # marketing, analytics, cookies, etc.
    purpose = Column(Text)  # Purpose of data processing
    granted = Column(Boolean, default=False)
    
    # Audit trail
    granted_at = Column(DateTime, default=func.now())
    revoked_at = Column(DateTime, nullable=True)
    ip_address = Column(String)  # Proof of consent
    user_agent = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DataProcessingRecord(Base):
    """
    Record of processing activities (GDPR Article 30).
    Documents what data is processed, why, and how long it's kept.
    """
    __tablename__ = "data_processing_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Processing details
    processing_purpose = Column(String, nullable=False)  # Contract performance, legitimate interest, etc.
    data_categories = Column(JSON)  # ["personal_data", "contact_info", "usage_data"]
    legal_basis = Column(String, nullable=False)  # consent, contract, legal_obligation, etc.
    
    # Data subjects
    data_subject_categories = Column(JSON)  # ["customers", "employees", "visitors"]
    
    # Recipients
    third_parties = Column(JSON)  # List of third parties who receive data
    international_transfers = Column(Boolean, default=False)
    transfer_safeguards = Column(Text)  # Standard contractual clauses, etc.
    
    # Retention
    retention_period = Column(String)  # "30 days", "1 year", "until account deletion"
    
    # Security
    security_measures = Column(JSON)  # ["encryption", "access_control", "audit_logging"]
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DataDeletionRequest(Base):
    """
    GDPR right to erasure requests (Article 17).
    Tracks account deletion and data removal.
    """
    __tablename__ = "data_deletion_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Request details
    requested_at = Column(DateTime, default=func.now())
    reason = Column(Text)  # User's reason for deletion
    
    # Processing
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Audit
    deleted_data = Column(JSON)  # List of deleted data categories
    retention_exceptions = Column(JSON)  # Data retained for legal reasons
    
    # Grace period (30 days to cancel)
    grace_period_ends = Column(DateTime)
    cancelled = Column(Boolean, default=False)
    
    # Metadata
    ip_address = Column(String)
    user_agent = Column(Text)


class DataExportRequest(Base):
    """
    GDPR right to data portability (Article 20).
    Tracks user data export requests.
    """
    __tablename__ = "data_export_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Request details
    requested_at = Column(DateTime, default=func.now())
    data_categories = Column(JSON)  # Categories of data to export
    
    # Processing
    status = Column(String, default="pending")  # pending, processing, completed, failed
    completed_at = Column(DateTime, nullable=True)
    
    # Export
    export_file_url = Column(String, nullable=True)  # S3 URL (signed, expires in 7 days)
    export_format = Column(String, default="json")  # json, csv, xml
    expires_at = Column(DateTime)  # Export link expiration
    
    # Metadata
    ip_address = Column(String)
    user_agent = Column(Text)


class DataBreachIncident(Base):
    """
    Data breach incident tracking (GDPR Article 33).
    Records data breaches for reporting to authorities.
    """
    __tablename__ = "data_breach_incidents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Incident details
    incident_date = Column(DateTime, nullable=False)
    discovered_date = Column(DateTime, default=func.now())
    description = Column(Text, nullable=False)
    
    # Impact
    data_categories_affected = Column(JSON)
    number_of_users_affected = Column(String)
    severity = Column(String)  # low, medium, high, critical
    
    # Notification
    authority_notified = Column(Boolean, default=False)
    authority_notified_at = Column(DateTime, nullable=True)
    users_notified = Column(Boolean, default=False)
    users_notified_at = Column(DateTime, nullable=True)
    
    # Response
    mitigation_actions = Column(JSON)
    resolution_status = Column(String, default="investigating")
    resolved_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """
    Audit log for GDPR compliance.
    Tracks all data access and modifications.
    """
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Request details
    timestamp = Column(DateTime, default=func.now(), index=True)
    user_id = Column(String, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    
    # Action
    action = Column(String, nullable=False)  # read, create, update, delete
    resource_type = Column(String)  # user, video, payment, etc.
    resource_id = Column(String)
    
    # Request details
    method = Column(String)  # GET, POST, PUT, DELETE
    path = Column(String)
    status_code = Column(String)
    
    # Data accessed
    data_accessed = Column(JSON)  # List of fields accessed
    changes = Column(JSON)  # Before/after values for updates
    
    # Metadata
    request_id = Column(String, index=True)  # Trace ID for correlation
