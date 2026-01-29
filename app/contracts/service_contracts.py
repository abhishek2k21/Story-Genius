"""
Service Contracts and SLA Monitoring
Defines service-level agreements and monitors compliance.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ServiceType(str, Enum):
    """Service type enumeration"""
    VERTEX_AI = "vertex_ai"
    VEO_VIDEO = "veo_video"
    TTS_AUDIO = "tts_audio"
    IMAGEN = "imagen"
    DATABASE = "database"
    API = "api"


@dataclass
class SLA:
    """Service Level Agreement"""
    service: ServiceType
    response_time_p50: float  # 50th percentile (seconds)
    response_time_p95: float  # 95th percentile (seconds)
    response_time_p99: float  # 99th percentile (seconds)
    availability_target: float  # Percentage (99.9 = 99.9%)
    error_rate_threshold: float  # Percentage (1.0 = 1%)
    
    def to_dict(self) -> dict:
        return {
            "service": self.service.value,
            "response_time_p50": self.response_time_p50,
            "response_time_p95": self.response_time_p95,
            "response_time_p99": self.response_time_p99,
            "availability_target": self.availability_target,
            "error_rate_threshold": self.error_rate_threshold
        }


# Defined SLAs for each service
SERVICE_SLAS = {
    ServiceType.VERTEX_AI: SLA(
        service=ServiceType.VERTEX_AI,
        response_time_p50=1.0,
        response_time_p95=2.0,
        response_time_p99=5.0,
        availability_target=99.9,
        error_rate_threshold=1.0
    ),
    ServiceType.VEO_VIDEO: SLA(
        service=ServiceType.VEO_VIDEO,
        response_time_p50=30.0,
        response_time_p95=60.0,
        response_time_p99=120.0,
        availability_target=99.5,
        error_rate_threshold=2.0
    ),
    ServiceType.TTS_AUDIO: SLA(
        service=ServiceType.TTS_AUDIO,
        response_time_p50=2.0,
        response_time_p95=5.0,
        response_time_p99=10.0,
        availability_target=99.8,
        error_rate_threshold=1.0
    ),
    ServiceType.IMAGEN: SLA(
        service=ServiceType.IMAGEN,
        response_time_p50=5.0,
        response_time_p95=10.0,
        response_time_p99=20.0,
        availability_target=99.8,
        error_rate_threshold=1.0
    ),
    ServiceType.DATABASE: SLA(
        service=ServiceType.DATABASE,
        response_time_p50=0.01,
        response_time_p95=0.05,
        response_time_p99=0.1,
        availability_target=99.99,
        error_rate_threshold=0.1
    ),
    ServiceType.API: SLA(
        service=ServiceType.API,
        response_time_p50=0.2,
        response_time_p95=0.5,
        response_time_p99=1.0,
        availability_target=99.95,
        error_rate_threshold=0.5
    )
}


@dataclass
class SLAViolation:
    """SLA violation record"""
    service: ServiceType
    violation_type: str  # response_time, availability, error_rate
    timestamp: datetime
    actual_value: float
    expected_value: float
    severity: str  # low, medium, high, critical
    
    def to_dict(self) -> dict:
        return {
            "service": self.service.value,
            "violation_type": self.violation_type,
            "timestamp": self.timestamp.isoformat(),
            "actual_value": actual_value,
            "expected_value": self.expected_value,
            "severity": self.severity
        }


class SLAMonitor:
    """
    Monitors SLA compliance for services.
    """
    
    def __init__(self):
        # Store metrics for each service
        self._service_metrics: Dict[ServiceType, List[float]] = {}
        self._violations: List[SLAViolation] = []
        logger.info("SLAMonitor initialized")
    
    def record_request(
        self,
        service: ServiceType,
        response_time: float,
        success: bool
    ):
        """
        Record service request metrics.
        
        Args:
            service: Service type
            response_time: Response time in seconds
            success: Whether request succeeded
        """
        if service not in self._service_metrics:
            self._service_metrics[service] = []
        
        # Record response time (negative if error)
        self._service_metrics[service].append(
            response_time if success else -response_time
        )
        
        # Check SLA immediately
        self._check_sla(service, response_time, success)
    
    def get_sla_compliance(self, service: ServiceType) -> Dict:
        """
        Get SLA compliance report for service.
        
        Args:
            service: Service type
        
        Returns:
            Compliance report
        """
        if service not in self._service_metrics:
            return {
                "service": service.value,
                "compliant": True,
                "metrics": {},
                "violations": []
            }
        
        sla = SERVICE_SLAS[service]
        metrics = self._service_metrics[service]
        
        # Separate successful and failed requests
        successful = [m for m in metrics if m > 0]
        failed = [abs(m) for m in metrics if m < 0]
        
        total_requests = len(metrics)
        error_rate = (len(failed) / total_requests * 100) if total_requests > 0 else 0
        availability = 100 - error_rate
        
        # Calculate percentiles for successful requests
        if successful:
            successful_sorted = sorted(successful)
            p50 = self._percentile(successful_sorted, 50)
            p95 = self._percentile(successful_sorted, 95)
            p99 = self._percentile(successful_sorted, 99)
        else:
            p50 = p95 = p99 = 0.0
        
        # Check compliance
        compliant = (
            p95 <= sla.response_time_p95 and
            availability >= sla.availability_target and
            error_rate <= sla.error_rate_threshold
        )
        
        return {
            "service": service.value,
            "compliant": compliant,
            "metrics": {
                "response_time_p50": round(p50, 3),
                "response_time_p95": round(p95, 3),
                "response_time_p99": round(p99, 3),
                "availability": round(availability, 2),
                "error_rate": round(error_rate, 2),
                "total_requests": total_requests
            },
            "sla_targets": sla.to_dict(),
            "violations": [
                v.to_dict() for v in self._violations
                if v.service == service
            ][-10:]  # Last 10 violations
        }
    
    def get_all_violations(
        self,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[SLAViolation]:
        """
        Get SLA violations.
        
        Args:
            severity: Filter by severity
            limit: Max violations to return
        
        Returns:
            List of violations
        """
        violations = self._violations
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        # Sort by timestamp descending
        violations.sort(key=lambda v: v.timestamp, reverse=True)
        
        return violations[:limit]
    
    def _check_sla(
        self,
        service: ServiceType,
        response_time: float,
        success: bool
    ):
        """Check if request violates SLA"""
        sla = SERVICE_SLAS[service]
        
        # Check response time (P95 threshold)
        if success and response_time > sla.response_time_p95:
            severity = "critical" if response_time > sla.response_time_p99 else "high"
            
            violation = SLAViolation(
                service=service,
                violation_type="response_time",
                timestamp=datetime.utcnow(),
                actual_value=response_time,
                expected_value=sla.response_time_p95,
                severity=severity
            )
            
            self._violations.append(violation)
            self._alert_violation(violation)
        
        # Check error (availability)
        if not success:
            violation = SLAViolation(
                service=service,
                violation_type="availability",
                timestamp=datetime.utcnow(),
                actual_value=0.0,  # Failed request
                expected_value=sla.availability_target,
                severity="medium"
            )
            
            self._violations.append(violation)
            self._alert_violation(violation)
    
    def _alert_violation(self, violation: SLAViolation):
        """Trigger alert for SLA violation"""
        logger.error(
            f"SLA VIOLATION: {violation.service.value} - {violation.violation_type}",
            extra={
                "service": violation.service.value,
                "violation_type": violation.violation_type,
                "actual": violation.actual_value,
                "expected": violation.expected_value,
                "severity": violation.severity
            }
        )
        
        # In production: send alert to monitoring system
        # Example: send_pagerduty_alert(violation)
    
    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not sorted_list:
            return 0.0
        
        index = int(len(sorted_list) * percentile / 100)
        index = min(index, len(sorted_list) - 1)
        
        return sorted_list[index]


# Global instance
sla_monitor = SLAMonitor()
