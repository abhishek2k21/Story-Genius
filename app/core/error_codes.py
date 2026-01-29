"""
Error Code Constants
Standardized error codes for the entire API.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes"""
    
    # ========== Authentication (AUTH_*) ==========
    AUTH_001 = "INVALID_CREDENTIALS"
    AUTH_002 = "ACCESS_TOKEN_EXPIRED"
    AUTH_003 = "REFRESH_TOKEN_EXPIRED"
    AUTH_004 = "TOKEN_REVOKED"
    AUTH_005 = "INVALID_TOKEN_SIGNATURE"
    AUTH_006 = "UNAUTHORIZED_ACCESS"
    
    # ========== Validation (VAL_*) ==========
    VAL_001 = "INVALID_PROMPT"
    VAL_002 = "PROMPT_TOO_SHORT"
    VAL_003 = "PROMPT_TOO_LONG"
    VAL_004 = "PROMPT_INJECTION_DETECTED"
    VAL_005 = "INVALID_PLATFORM"
    VAL_006 = "PLATFORM_CONSTRAINT_VIOLATED"
    VAL_007 = "INVALID_AUDIENCE"
    VAL_008 = "CONTENT_RATING_MISMATCH"
    VAL_009 = "INVALID_DURATION"
    VAL_010 = "INVALID_ASPECT_RATIO"
    
    # ========== Rate Limiting (RATE_*) ==========
    RATE_001 = "RATE_LIMIT_EXCEEDED"
    RATE_002 = "BATCH_CREATION_LIMIT_EXCEEDED"
    RATE_003 = "VIDEO_GENERATION_LIMIT_EXCEEDED"
    
    # ========== Quota (QUOTA_*) ==========
    QUOTA_001 = "MONTHLY_QUOTA_EXCEEDED"
    QUOTA_002 = "BATCH_SIZE_LIMIT_EXCEEDED"
    QUOTA_003 = "PLAN_UPGRADE_REQUIRED"
    
    # ========== Resource Not Found (NOT_FOUND_*) ==========
    NOT_FOUND_001 = "VIDEO_NOT_FOUND"
    NOT_FOUND_002 = "BATCH_NOT_FOUND"
    NOT_FOUND_003 = "USER_NOT_FOUND"
    NOT_FOUND_004 = "TEMPLATE_NOT_FOUND"
    
    # ========== LLM Errors (LLM_*) ==========
    LLM_001 = "LLM_TIMEOUT"
    LLM_002 = "LLM_RATE_LIMIT"
    LLM_003 = "LLM_MALFORMED_RESPONSE"
    LLM_004 = "LLM_CONTENT_FILTER"
    
    # ========== Video Generation (VIDEO_*) ==========
    VIDEO_001 = "VIDEO_GENERATION_FAILED"
    VIDEO_002 = "VIDEO_DOWNLOAD_FAILED"
    VIDEO_003 = "VIDEO_PROCESSING_TIMEOUT"
    VIDEO_004 = "INVALID_VIDEO_FORMAT"
    
    # ========== Media Services (MEDIA_*) ==========
    MEDIA_001 = "VEO_GENERATION_FAILED"
    MEDIA_002 = "IMAGEN_GENERATION_FAILED"
    MEDIA_003 = "TTS_GENERATION_FAILED"
    MEDIA_004 = "STORAGE_UPLOAD_FAILED"
    
    # ========== Database (DB_*) ==========
    DB_001 = "DATABASE_CONNECTION_ERROR"
    DB_002 = "DATABASE_TIMEOUT"
    DB_003 = "TRANSACTION_ROLLBACK"
    DB_004 = "INTEGRITY_CONSTRAINT_VIOLATION"
    
    # ========== Batch Processing (BATCH_*) ==========
    BATCH_001 = "BATCH_VALIDATION_FAILED"
    BATCH_002 = "BATCH_LOCKED"
    BATCH_003 = "BATCH_ALREADY_PROCESSING"
    BATCH_004 = "BATCH_ITEM_LIMIT_EXCEEDED"
    
    # ========== Internal (INTERNAL_*) ==========
    INTERNAL_001 = "INTERNAL_SERVER_ERROR"
    INTERNAL_002 = "SERVICE_UNAVAILABLE"
    INTERNAL_003 = "CIRCUIT_BREAKER_OPEN"


# Error code to HTTP status mapping
ERROR_STATUS_CODES = {
    # Authentication 401
    ErrorCode.AUTH_001: 401,
    ErrorCode.AUTH_002: 401,
    ErrorCode.AUTH_003: 401,
    ErrorCode.AUTH_004: 401,
    ErrorCode.AUTH_005: 401,
    ErrorCode.AUTH_006: 403,
    
    # Validation 422
    ErrorCode.VAL_001: 422,
    ErrorCode.VAL_002: 422,
    ErrorCode.VAL_003: 422,
    ErrorCode.VAL_004: 422,
    ErrorCode.VAL_005: 422,
    ErrorCode.VAL_006: 422,
    ErrorCode.VAL_007: 422,
    ErrorCode.VAL_008: 422,
    ErrorCode.VAL_009: 422,
    ErrorCode.VAL_010: 422,
    
    # Rate Limiting 429
    ErrorCode.RATE_001: 429,
    ErrorCode.RATE_002: 429,
    ErrorCode.RATE_003: 429,
    ErrorCode.QUOTA_001: 429,
    ErrorCode.QUOTA_002: 429,
    ErrorCode.QUOTA_003: 402,  # Payment Required
    
    # Not Found 404
    ErrorCode.NOT_FOUND_001: 404,
    ErrorCode.NOT_FOUND_002: 404,
    ErrorCode.NOT_FOUND_003: 404,
    ErrorCode.NOT_FOUND_004: 404,
    
    # Service Errors 500/502/504
    ErrorCode.LLM_001: 504,
    ErrorCode.LLM_002: 429,
    ErrorCode.LLM_003: 502,
    ErrorCode.LLM_004: 422,
    ErrorCode.VIDEO_001: 500,
    ErrorCode.VIDEO_002: 502,
    ErrorCode.VIDEO_003: 504,
    ErrorCode.VIDEO_004: 422,
    ErrorCode.MEDIA_001: 502,
    ErrorCode.MEDIA_002: 502,
    ErrorCode.MEDIA_003: 502,
    ErrorCode.MEDIA_004: 502,
    
    # Database 500
    ErrorCode.DB_001: 500,
    ErrorCode.DB_002: 504,
    ErrorCode.DB_003: 500,
    ErrorCode.DB_004: 409,
    
    # Batch 400/409
    ErrorCode.BATCH_001: 422,
    ErrorCode.BATCH_002: 409,
    ErrorCode.BATCH_003: 409,
    ErrorCode.BATCH_004: 422,
    
    # Internal 500/503
    ErrorCode.INTERNAL_001: 500,
    ErrorCode.INTERNAL_002: 503,
    ErrorCode.INTERNAL_003: 503,
}


def get_status_code(error_code: ErrorCode) -> int:
    """Get HTTP status code for error code"""
    return ERROR_STATUS_CODES.get(error_code, 500)
