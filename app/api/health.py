"""
Health check endpoints for Kubernetes liveness and readiness probes.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.core.database import database
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Liveness probe endpoint.
    
    Returns 200 if the application is running.
    Kubernetes restarts the pod if this fails.
    """
    return {"status": "healthy"}


@router.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe endpoint.
    
    Checks all critical dependencies before allowing traffic.
    Kubernetes removes pod from service if this fails.
    
    Returns:
        Status and individual dependency checks
        
    Raises:
        HTTPException: 503 if any dependency is unhealthy
    """
    checks = {
        "database": await check_database(),
        "cache": check_cache(),
    }
    
    all_healthy = all(checks.values())
    
    if all_healthy:
        return {
            "status": "ready",
            "checks": checks
        }
    else:
        logger.warning(f"Readiness check failed: {checks}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "checks": checks
            }
        )


async def check_database() -> bool:
    """
    Check database connectivity.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        # Simple query to check connection
        from sqlalchemy import text
        await database.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_cache() -> bool:
    """
    Check Redis cache connectivity.
    
    Returns:
        True if cache is accessible, False otherwise
    """
    try:
        return cache_manager.health_check()
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False


@router.get("/metrics", tags=["Health"])
async def metrics() -> Dict[str, Any]:
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        Application metrics
    """
    return {
        "uptime": "TODO: implement uptime tracking",
        "requests_total": "TODO: implement request counter",
        "requests_per_second": "TODO: implement rate tracking",
    }
