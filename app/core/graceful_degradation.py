"""
Graceful Degradation System
Implements fallback mechanisms for service failures.
"""
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class DegradationLevel(str, Enum):
    """Degradation level"""
    FULL = "full"  # All features available
    REDUCED = "reduced"  # Some features disabled
    MINIMAL = "minimal"  # Minimal functionality only
    MAINTENANCE = "maintenance"  # Maintenance mode


@dataclass
class FallbackStrategy:
    """Fallback strategy for a service"""
    primary_service: str
    fallback_service: Optional[str]
    fallback_mode: str  # cache, alternative, disabled
    degradation_level: DegradationLevel
    description: str
    
    def to_dict(self) -> dict:
        return {
            "primary_service": self.primary_service,
            "fallback_service": self.fallback_service,
            "fallback_mode": self.fallback_mode,
            "degradation_level": self.degradation_level.value,
            "description": self.description
        }


# Fallback strategies for each service
FALLBACK_STRATEGIES = {
    "veo_video": FallbackStrategy(
        primary_service="veo_video",
        fallback_service="imagen",
        fallback_mode="alternative",
        degradation_level=DegradationLevel.REDUCED,
        description="Use Imagen static images if Veo video unavailable"
    ),
    "vertex_ai": FallbackStrategy(
        primary_service="vertex_ai",
        fallback_service="gemini_flash",
        fallback_mode="alternative",
        degradation_level=DegradationLevel.REDUCED,
        description="Use Gemini Flash (faster, cheaper) if Vertex AI slow"
    ),
    "tts_audio": FallbackStrategy(
        primary_service="tts_audio",
        fallback_service="cache",
        fallback_mode="cache",
        degradation_level=DegradationLevel.REDUCED,
        description="Use cached TTS if service unavailable"
    ),
    "database": FallbackStrategy(
        primary_service="database",
        fallback_service="cache",
        fallback_mode="cache",
        degradation_level=DegradationLevel.MINIMAL,
        description="Use in-memory cache if database slow"
    ),
    "imagen": FallbackStrategy(
        primary_service="imagen",
        fallback_service="placeholder",
        fallback_mode="disabled",
        degradation_level=DegradationLevel.MINIMAL,
        description="Use placeholder images if Imagen unavailable"
    )
}


class GracefulDegradation:
    """
    Manages graceful degradation and fallback mechanisms.
    """
    
    def __init__(self):
        self._current_level = DegradationLevel.FULL
        self._degraded_services: set = set()
        self._fallback_cache: Dict[str, Any] = {}
        logger.info("GracefulDegradation initialized")
    
    def get_fallback_service(self, service: str) -> Optional[str]:
        """
        Get fallback service for primary service.
        
        Args:
            service: Primary service name
        
        Returns:
            Fallback service name or None
        """
        strategy = FALLBACK_STRATEGIES.get(service)
        
        if strategy:
            logger.info(
                f"Fallback for {service}: {strategy.fallback_service} "
                f"(mode: {strategy.fallback_mode})"
            )
            return strategy.fallback_service
        
        return None
    
    def execute_with_fallback(
        self,
        service: str,
        primary_fn: Callable,
        fallback_fn: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with fallback on failure.
        
        Args:
            service: Service name
            primary_fn: Primary function to execute
            fallback_fn: Fallback function
            *args, **kwargs: Function arguments
        
        Returns:
            Result from primary or fallback
        """
        try:
            # Try primary service
            result = primary_fn(*args, **kwargs)
            
            # Remove from degraded if successful
            if service in self._degraded_services:
                self._degraded_services.remove(service)
                logger.info(f"Service {service} recovered")
            
            return result
            
        except Exception as e:
            logger.error(f"Primary service {service} failed: {e}")
            
            # Mark as degraded
            self._degraded_services.add(service)
            
            # Get fallback strategy
            strategy = FALLBACK_STRATEGIES.get(service)
            
            if not strategy:
                logger.error(f"No fallback strategy for {service}")
                raise
            
            # Execute fallback
            if strategy.fallback_mode == "cache":
                return self._get_cached_response(service, *args, **kwargs)
            
            elif strategy.fallback_mode == "alternative":
                if fallback_fn:
                    logger.info(f"Using fallback for {service}")
                    result = fallback_fn(*args, **kwargs)
                    return result
                else:
                    logger.error(f"No fallback function provided for {service}")
                    raise
            
            elif strategy.fallback_mode == "disabled":
                logger.warning(f"Service {service} degraded to disabled mode")
                return self._get_placeholder_response(service)
            
            else:
                raise
    
    def degrade_to_level(self, level: DegradationLevel):
        """
        Manually degrade system to level.
        
        Args:
            level: Target degradation level
        """
        self._current_level = level
        logger.warning(f"System degraded to: {level.value}")
        
        # In production: send alert, update dashboard
        # Example: send_alert(f"System degraded to {level.value}")
    
    def get_system_status(self) -> Dict:
        """
        Get current system degradation status.
        
        Returns:
            Status information
        """
        return {
            "degradation_level": self._current_level.value,
            "degraded_services": list(self._degraded_services),
            "fallback_strategies": {
                service: strategy.to_dict()
                for service, strategy in FALLBACK_STRATEGIES.items()
            },
            "features_available": self._get_available_features()
        }
    
    def is_feature_available(self, feature: str) -> bool:
        """
        Check if feature is available at current degradation level.
        
        Args:
            feature: Feature name
        
        Returns:
            True if available
        """
        if self._current_level == DegradationLevel.FULL:
            return True
        elif self._current_level == DegradationLevel.REDUCED:
            # Most features available except non-critical
            return feature not in ["advanced_analytics", "real_time_preview"]
        elif self._current_level == DegradationLevel.MINIMAL:
            # Only core features
            return feature in ["basic_generation", "status_check"]
        else:  # MAINTENANCE
            return False
    
    def cache_response(self, service: str, key: str, response: Any):
        """Cache response for fallback"""
        cache_key = f"{service}:{key}"
        self._fallback_cache[cache_key] = response
        logger.debug(f"Cached response for {cache_key}")
    
    def _get_cached_response(self, service: str, *args, **kwargs) -> Any:
        """Get cached response"""
        # Simple key generation (in production, use better hashing)
        cache_key = f"{service}:{str(args)}"
        
        if cache_key in self._fallback_cache:
            logger.info(f"Returning cached response for {service}")
            return self._fallback_cache[cache_key]
        
        logger.error(f"No cached response for {service}")
        raise Exception(f"Service {service} unavailable and no cache")
    
    def _get_placeholder_response(self, service: str) -> Any:
        """Get placeholder response"""
        placeholders = {
            "veo_video": {"status": "unavailable", "placeholder": "video_placeholder.mp4"},
            "imagen": {"status": "unavailable", "placeholder": "image_placeholder.png"},
            "tts_audio": {"status": "unavailable", "placeholder": "silence.mp3"}
        }
        
        return placeholders.get(service, {"status": "unavailable"})
    
    def _get_available_features(self) -> List[str]:
        """Get list of available features"""
        if self._current_level == DegradationLevel.FULL:
            return ["all_features"]
        elif self._current_level == DegradationLevel.REDUCED:
            return ["basic_generation", "status_check", "batch_processing"]
        elif self._current_level == DegradationLevel.MINIMAL:
            return ["basic_generation", "status_check"]
        else:
            return []


# Global instance
graceful_degradation = GracefulDegradation()
