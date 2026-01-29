"""
Error Analysis and Triage System
Aggregates errors and provides recovery recommendations.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import Counter

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorEntry:
    """Single error entry"""
    item_id: str
    error_code: str
    error_type: str
    error_message: str
    timestamp: datetime
    item_index: int
    recoverable: bool = True
    
    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "error_code": self.error_code,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "item_index": self.item_index,
            "recoverable": self.recoverable
        }


@dataclass
class ErrorReport:
    """Aggregated error report"""
    batch_id: str
    total_errors: int
    errors_by_type: Dict[str, int]
    errors_by_code: Dict[str, int]
    error_rate: float
    top_errors: List[ErrorEntry]
    problematic_items: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "total_errors": self.total_errors,
            "errors_by_type": self.errors_by_type,
            "errors_by_code": self.errors_by_code,
            "error_rate": round(self.error_rate, 2),
            "top_errors": [e.to_dict() for e in self.top_errors],
            "problematic_items": self.problematic_items,
            "recommendations": self.recommendations
        }


class ErrorAnalyzer:
    """
    Analyzes batch errors and provides triage recommendations.
    """
    
    def __init__(self):
        # Store errors for each batch
        self._batch_errors: Dict[str, List[ErrorEntry]] = {}
        logger.info("ErrorAnalyzer initialized")
    
    def record_error(
        self,
        batch_id: str,
        item_id: str,
        item_index: int,
        error: Exception,
        error_code: Optional[str] = None,
        recoverable: bool = True
    ):
        """
        Record an error.
        
        Args:
            batch_id: Batch ID
            item_id: Item ID that failed
            item_index: Item index
            error: Exception that occurred
            error_code: Optional error code
            recoverable: Whether error is recoverable
        """
        if batch_id not in self._batch_errors:
            self._batch_errors[batch_id] = []
        
        error_entry = ErrorEntry(
            item_id=item_id,
            error_code=error_code or "UNKNOWN",
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.utcnow(),
            item_index=item_index,
            recoverable=recoverable
        )
        
        self._batch_errors[batch_id].append(error_entry)
        
        logger.error(
            f"Batch {batch_id} error recorded: {error_type} at index {item_index}",
            extra={"item_id": item_id, "error": str(error)}
        )
    
    def aggregate_errors(
        self,
        batch_id: str,
        total_items: int
    ) -> ErrorReport:
        """
        Aggregate errors for batch.
        
        Args:
            batch_id: Batch ID
            total_items: Total number of items in batch
        
        Returns:
            ErrorReport with aggregated data
        """
        errors = self._batch_errors.get(batch_id, [])
        
        if not errors:
            logger.info(f"No errors for batch {batch_id}")
            return ErrorReport(
                batch_id=batch_id,
                total_errors=0,
                errors_by_type={},
                errors_by_code={},
                error_rate=0.0,
                top_errors=[],
                problematic_items=[],
                recommendations=[]
            )
        
        # Count errors by type
        error_types = Counter(e.error_type for e in errors)
        
        # Count errors by code
        error_codes = Counter(e.error_code for e in errors)
        
        # Calculate error rate
        error_rate = (len(errors) / total_items * 100) if total_items > 0 else 0
        
        # Get top 10 errors
        top_errors = sorted(errors, key=lambda e: e.timestamp)[:10]
        
        # Identify problematic items (items that failed multiple times)
        item_fail_count = Counter(e.item_id for e in errors)
        problematic_items = [
            item_id for item_id, count in item_fail_count.items()
            if count > 1
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            errors=errors,
            error_types=error_types,
            error_codes=error_codes,
            error_rate=error_rate
        )
        
        report = ErrorReport(
            batch_id=batch_id,
            total_errors=len(errors),
            errors_by_type=dict(error_types),
            errors_by_code=dict(error_codes),
            error_rate=error_rate,
            top_errors=top_errors,
            problematic_items=problematic_items,
            recommendations=recommendations
        )
        
        logger.info(
            f"Error analysis for batch {batch_id}: "
            f"{len(errors)} errors ({error_rate:.1f}% rate)"
        )
        
        return report
    
    def _generate_recommendations(
        self,
        errors: List[ErrorEntry],
        error_types: Counter,
        error_codes: Counter,
        error_rate: float
    ) -> List[str]:
        """Generate recovery recommendations"""
        recommendations = []
        
        # High error rate
        if error_rate > 50:
            recommendations.append(
                "⚠️ High error rate (>50%). Consider reviewing batch input data."
            )
        
        # Timeout errors
        if any("timeout" in e.error_message.lower() for e in errors):
            recommendations.append(
                "🕐 Timeout errors detected. Increase timeout limits or reduce batch size."
            )
        
        # Rate limit errors
        if any("rate limit" in e.error_message.lower() for e in errors):
            recommendations.append(
                "🚦 Rate limit errors detected. Reduce concurrency or add delays."
            )
        
        # Validation errors
        if any("validation" in e.error_message.lower() for e in errors):
            recommendations.append(
                "✓ Validation errors detected. Review input data format."
            )
        
        # Network errors
        if any(t in ["ConnectionError", "TimeoutError"] for t in error_types):
            recommendations.append(
                "🌐 Connection errors detected. Check network connectivity."
            )
        
        # Recurring error type
        most_common_type = error_types.most_common(1)
        if most_common_type and most_common_type[0][1] > len(errors) * 0.7:
            error_type = most_common_type[0][0]
            recommendations.append(
                f"🔁 {error_type} is recurring ({most_common_type[0][1]} times). "
                "Investigate root cause."
            )
        
        # No recommendations
        if not recommendations:
            recommendations.append(
                "✅ No specific patterns detected. Review individual errors."
            )
        
        return recommendations
    
    def identify_patterns(self, batch_id: str) -> Dict[str, Any]:
        """
        Identify error patterns.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            Pattern analysis
        """
        errors = self._batch_errors.get(batch_id, [])
        
        if not errors:
            return {}
        
        # Time-based patterns (errors concentrated in time windows)
        time_windows = self._analyze_time_windows(errors)
        
        # Item index patterns (errors at specific indices)
        index_patterns = self._analyze_index_patterns(errors)
        
        return {
            "time_clustering": time_windows,
            "index_patterns": index_patterns
        }
    
    def _analyze_time_windows(self, errors: List[ErrorEntry]) -> Dict:
        """Analyze if errors cluster in time windows"""
        if len(errors) < 5:
            return {"clustering": False}
        
        # Simple check: are errors close together in time?
        timestamps = sorted([e.timestamp for e in errors])
        intervals = [
            (timestamps[i+1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps)-1)
        ]
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            "clustering": avg_interval < 5,  # Less than 5 seconds between errors
            "avg_interval_seconds": avg_interval
        }
    
    def _analyze_index_patterns(self, errors: List[ErrorEntry]) -> Dict:
        """Analyze error patterns by item index"""
        indices = [e.item_index for e in errors]
        
        # Check if errors are sequential
        sequential = all(
            indices[i+1] - indices[i] == 1
            for i in range(len(indices)-1)
        )
        
        return {
            "sequential": sequential,
            "indices": sorted(indices)[:10]  # Top 10
        }
    
    def get_errors(self, batch_id: str) -> List[ErrorEntry]:
        """Get all errors for batch"""
        return self._batch_errors.get(batch_id, [])
    
    def clear_errors(self, batch_id: str):
        """Clear errors for batch"""
        if batch_id in self._batch_errors:
            del self._batch_errors[batch_id]
            logger.info(f"Cleared errors for batch {batch_id}")


# Global instance
error_analyzer = ErrorAnalyzer()
