"""
Usage Logging Module
Track API usage, tokens, and costs for external services.
"""
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UsageRecord:
    """Record of API usage."""
    service: str
    operation: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


# Cost estimates per 1K tokens/units
COST_ESTIMATES = {
    "gemini": {"input": 0.00025, "output": 0.0005},
    "veo": {"per_second": 0.05},
    "imagen": {"per_image": 0.02},
    "elevenlabs": {"per_char": 0.00003},
    "edge_tts": {"per_char": 0.0},
}


class UsageTracker:
    """Track and log API usage."""

    def __init__(self):
        self._records: list[UsageRecord] = []

    def log(self, record: UsageRecord) -> None:
        """Log a usage record."""
        self._records.append(record)

        # Calculate cost
        cost = self._estimate_cost(record)
        record.cost_usd = cost

        # Log for monitoring
        logger.info(
            f"API Usage: {record.service}/{record.operation}",
            extra={
                "service": record.service,
                "operation": record.operation,
                "tokens_input": record.tokens_input,
                "tokens_output": record.tokens_output,
                "duration_ms": record.duration_ms,
                "cost_usd": cost,
                "success": record.success,
            },
        )

    def _estimate_cost(self, record: UsageRecord) -> float:
        """Estimate cost for a usage record."""
        service = record.service.lower()

        if service == "gemini":
            rates = COST_ESTIMATES["gemini"]
            return (record.tokens_input / 1000 * rates["input"]) + \
                   (record.tokens_output / 1000 * rates["output"])

        elif service == "veo":
            duration = record.metadata.get("duration_seconds", 5)
            return duration * COST_ESTIMATES["veo"]["per_second"]

        elif service == "imagen":
            return COST_ESTIMATES["imagen"]["per_image"]

        elif service == "elevenlabs":
            chars = record.metadata.get("char_count", 0)
            return chars * COST_ESTIMATES["elevenlabs"]["per_char"]

        return 0.0

    def get_summary(self, hours: int = 24) -> dict:
        """Get usage summary for recent hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        recent = [r for r in self._records if r.timestamp.timestamp() > cutoff]

        summary = {
            "period_hours": hours,
            "total_requests": len(recent),
            "total_cost_usd": sum(r.cost_usd for r in recent),
            "by_service": {},
        }

        for record in recent:
            if record.service not in summary["by_service"]:
                summary["by_service"][record.service] = {
                    "requests": 0,
                    "cost_usd": 0.0,
                    "errors": 0,
                }

            summary["by_service"][record.service]["requests"] += 1
            summary["by_service"][record.service]["cost_usd"] += record.cost_usd
            if not record.success:
                summary["by_service"][record.service]["errors"] += 1

        return summary


# Singleton tracker
_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    """Get usage tracker singleton."""
    return _tracker


def log_usage(
    service: str,
    operation: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    duration_ms: float = 0.0,
    success: bool = True,
    error: Optional[str] = None,
    **metadata,
) -> None:
    """Convenience function to log usage."""
    record = UsageRecord(
        service=service,
        operation=operation,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        duration_ms=duration_ms,
        success=success,
        error=error,
        metadata=metadata,
    )
    _tracker.log(record)
