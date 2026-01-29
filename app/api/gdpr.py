"""
GDPR Compliance API Endpoints.
Implements GDPR rights: data export, deletion, consent management.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.gdpr_service import GDPRService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class ConsentUpdate(BaseModel):
    """Consent update request."""
    consent_type: str
    granted: bool
    purpose: Optional[str] = None


class DataExportRequest(BaseModel):
    """Data export request."""
    format: str = "json"  # json, csv, xml
    categories: Optional[list] = None  # Specific categories to export


class DataDeletionRequest(BaseModel):
    """Data deletion request."""
    reason: Optional[str] = None
    confirm: bool  # Must be True


@router.post("/consent")
async def update_consent(
    consent: ConsentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Update user consent preferences (GDPR Article 7).
    
    Consent types:
    - marketing: Marketing communications
    - analytics: Usage analytics
    - cookies: Non-essential cookies
    - third_party: Third-party data sharing
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    
    result = await service.update_consent(
        user_id=str(current_user.id),
        consent_type=consent.consent_type,
        granted=consent.granted,
        purpose=consent.purpose,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"Consent updated for user {current_user.id}: {consent.consent_type}={consent.granted}")
    
    return JSONResponse({
        "message": "Consent updated successfully",
        "consent_type": consent.consent_type,
        "granted": consent.granted
    })


@router.get("/consent")
async def get_consents(current_user: User = Depends(get_current_user)):
    """Get all user consent records."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    consents = await service.get_user_consents(str(current_user.id))
    
    return JSONResponse({
        "consents": consents
    })


@router.post("/data-export")
async def request_data_export(
    export_request: DataExportRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Request user data export (GDPR Article 20 - Right to data portability).
    
    Exports all user data in machine-readable format.
    Export link expires in 7 days.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    
    result = await service.create_data_export_request(
        user_id=str(current_user.id),
        format=export_request.format,
        categories=export_request.categories,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"Data export requested for user {current_user.id}")
    
    return JSONResponse({
        "message": "Data export request created",
        "request_id": result["request_id"],
        "estimated_completion": "Within 24 hours",
        "notification": "You will receive an email when your export is ready"
    })


@router.get("/data-export/{request_id}")
async def get_data_export(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of data export request."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    export = await service.get_export_request(request_id, str(current_user.id))
    
    if not export:
        raise HTTPException(status_code=404, detail="Export request not found")
    
    return JSONResponse({
        "request_id": export["id"],
        "status": export["status"],
        "requested_at": export["requested_at"],
        "download_url": export.get("export_file_url"),
        "expires_at": export.get("expires_at")
    })


@router.post("/delete-account")
async def request_account_deletion(
    deletion_request: DataDeletionRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Request account deletion (GDPR Article 17 - Right to erasure).
    
    30-day grace period before permanent deletion.
    User can cancel within this period.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not deletion_request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required for account deletion"
        )
    
    service = GDPRService()
    
    result = await service.create_deletion_request(
        user_id=str(current_user.id),
        reason=deletion_request.reason,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.warning(f"Account deletion requested for user {current_user.id}")
    
    return JSONResponse({
        "message": "Account deletion request created",
        "request_id": result["request_id"],
        "grace_period_ends": result["grace_period_ends"],
        "warning": "Your account will be permanently deleted after the grace period",
        "cancellation": "You can cancel this request before the grace period ends"
    })


@router.post("/delete-account/{request_id}/cancel")
async def cancel_account_deletion(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel account deletion request during grace period."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    
    result = await service.cancel_deletion_request(request_id, str(current_user.id))
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel: deletion already in progress or grace period expired"
        )
    
    logger.info(f"Account deletion cancelled for user {current_user.id}")
    
    return JSONResponse({
        "message": "Account deletion cancelled successfully"
    })


@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get privacy policy (GDPR Article 13).
    Provides information about data processing.
    """
    return JSONResponse({
        "policy_url": "https://ytvideocreator.com/privacy",
        "last_updated": "2026-01-28",
        "contact": {
            "email": "privacy@ytvideocreator.com",
            "dpo": "dpo@ytvideocreator.com"  # Data Protection Officer
        },
        "data_controller": {
            "name": "YT Video Creator Inc.",
            "address": "123 Main St, San Francisco, CA 94105",
            "registration": "US-12345678"
        },
        "data_retention": {
            "account_data": "Until account deletion + 30 days",
            "activity_logs": "90 days",
            "payment_records": "7 years (legal requirement)"
        },
        "user_rights": [
            "Right to access (Article 15)",
            "Right to rectification (Article 16)",
            "Right to erasure (Article 17)",
            "Right to data portability (Article 20)",
            "Right to object (Article 21)",
            "Right to withdraw consent (Article 7)"
        ]
    })


@router.get("/my-data")
async def get_my_data_summary(current_user: User = Depends(get_current_user)):
    """
    Get summary of user's data (GDPR Article 15 - Right of access).
    Quick overview without full export.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    service = GDPRService()
    summary = await service.get_data_summary(str(current_user.id))
    
    return JSONResponse(summary)
