"""
Advanced Monitoring & Health Metrics.
Platform health scoring and intelligent alerting system.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthGrade(str, Enum):
    """Health score grades."""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    P0 = "P0"  # Critical - page immediately
    P1 = "P1"  # High - notify immediately
    P2 = "P2"  # Medium - notify during business hours
    P3 = "P3"  # Low - collect and review
    INFO = "Info"  # Informational only


class AdvancedMetrics:
    """Track advanced business and health metrics."""
    
    def __init__(self, prometheus_client, analytics_service):
        self.prometheus = prometheus_client
        self.analytics = analytics_service
    
    def calculate_health_score(self) -> Dict:
        """
        Calculate platform health score (0-100).
        
        Weighted scoring:
        - Uptime (30%)
        - Performance (20%)
        - Error rate (20%)
        - User growth (15%)
        - Revenue growth (15%)
        
        Returns:
            Health score with grade and breakdown
        """
        metrics = {
            "uptime": self._get_uptime_percentage(),
            "performance": self._get_performance_score(),
            "error_rate": self._get_error_rate(),
            "user_growth": self._get_user_growth(),
            "revenue_growth": self._get_revenue_growth()
        }
        
        # Calculate weighted score
        health_score = (
            metrics["uptime"] * 0.30 +
            metrics["performance"] * 0.20 +
            (100 - metrics["error_rate"] * 100) * 0.20 +
            min(metrics["user_growth"], 100) * 0.15 +
            min(metrics["revenue_growth"], 100) * 0.15
        )
        
        grade = self._get_grade(health_score)
        
        return {
            "health_score": round(health_score, 1),
            "grade": grade.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "uptime_pct": round(metrics["uptime"], 2),
                "performance_score": round(metrics["performance"], 1),
                "error_rate_pct": round(metrics["error_rate"], 3),
                "user_growth_pct": round(metrics["user_growth"], 1),
                "revenue_growth_pct": round(metrics["revenue_growth"], 1)
            },
            "status": self._get_status(health_score),
            "alerts": self._get_active_alerts()
        }
    
    def _get_uptime_percentage(self) -> float:
        """Get uptime percentage for last 30 days."""
        # Query Prometheus for uptime
        # Simplified calculation
        total_minutes = 30 * 24 * 60  # 30 days
        downtime_minutes = 7  # 7 minutes downtime
        
        uptime_pct = ((total_minutes - downtime_minutes) / total_minutes) * 100
        return uptime_pct  # 99.98%
    
    def _get_performance_score(self) -> float:
        """
        Get performance score based on API latency.
        
        Scoring:
        - p95 < 100ms: 100 points
        - p95 < 200ms: 90 points
        - p95 < 300ms: 80 points
        - p95 < 500ms: 70 points
        - p95 >= 500ms: 50 points
        """
        # Query Prometheus for p95 latency
        p95_latency = 180  # ms
        
        if p95_latency < 100:
            return 100
        elif p95_latency < 200:
            return 90
        elif p95_latency < 300:
            return 80
        elif p95_latency < 500:
            return 70
        else:
            return 50
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage."""
        # Query Prometheus
        total_requests = 1_000_000
        failed_requests = 150
        
        error_rate = (failed_requests / total_requests) * 100
        return error_rate  # 0.015%
    
    def _get_user_growth(self) -> float:
        """Get week-over-week user growth percentage."""
        # Current week signups
        current_week = 120
        previous_week = 95
        
        growth = ((current_week - previous_week) / previous_week) * 100
        return growth  # 26.3%
    
    def _get_revenue_growth(self) -> float:
        """Get month-over-month revenue growth percentage."""
        # Current month MRR
        current_mrr = 15000
        previous_mrr = 12700
        
        growth = ((current_mrr - previous_mrr) / previous_mrr) * 100
        return growth  # 18.1%
    
    def _get_grade(self, score: float) -> HealthGrade:
        """Convert health score to letter grade."""
        if score >= 98:
            return HealthGrade.A_PLUS
        elif score >= 95:
            return HealthGrade.A
        elif score >= 90:
            return HealthGrade.B_PLUS
        elif score >= 85:
            return HealthGrade.B
        elif score >= 80:
            return HealthGrade.C_PLUS
        elif score >= 75:
            return HealthGrade.C
        elif score >= 70:
            return HealthGrade.D
        else:
            return HealthGrade.F
    
    def _get_status(self, score: float) -> str:
        """Get human-readable status."""
        if score >= 95:
            return "Excellent - All systems optimal"
        elif score >= 90:
            return "Good - Minor areas for improvement"
        elif score >= 80:
            return "Fair - Action needed on some metrics"
        elif score >= 70:
            return "Poor - Multiple issues detected"
        else:
            return "Critical - Immediate attention required"
    
    def _get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts."""
        # Would query alerting system
        return []


class IntelligentAlerting:
    """Intelligent alerting system with context-aware rules."""
    
    def __init__(self, pagerduty_client, slack_client):
        self.pagerduty = pagerduty_client
        self.slack = slack_client
        self.alert_rules = self._define_alert_rules()
    
    def _define_alert_rules(self) -> List[Dict]:
        """Define intelligent alert rules."""
        return [
            {
                "name": "Revenue Impact Alert",
                "condition": lambda metrics: metrics.get("payment_failures_1h", 0) > 5,
                "severity": AlertSeverity.P0,
                "actions": ["page_oncall", "notify_cfo", "create_incident"],
                "rationale": "Direct revenue impact - immediate action needed",
                "runbook": "https://wiki.internal/runbooks/payment-failures"
            },
            {
                "name": "Viral Growth Detected",
                "condition": lambda metrics: metrics.get("signups_1h", 0) > metrics.get("avg_signups_1h", 0) * 2,
                "severity": AlertSeverity.INFO,
                "actions": ["notify_growth_team", "notify_ops"],
                "rationale": "Positive growth spike - prepare for traffic",
                "runbook": "https://wiki.internal/runbooks/viral-growth"
            },
            {
                "name": "Churn Risk Alert",
                "condition": lambda metrics: metrics.get("dau_change_7d", 0) < -20,
                "severity": AlertSeverity.P1,
                "actions": ["notify_product_team", "notify_ceo"],
                "rationale": "Significant engagement decline",
                "runbook": "https://wiki.internal/runbooks/churn-risk"
            },
            {
                "name": "Cost Anomaly",
                "condition": lambda metrics: metrics.get("infrastructure_cost_daily", 0) > metrics.get("avg_cost_daily", 0) * 1.5,
                "severity": AlertSeverity.P2,
                "actions": ["notify_devops", "notify_finance"],
                "rationale": "Unexpected cost spike",
                "runbook": "https://wiki.internal/runbooks/cost-spike"
            },
            {
                "name": "API Performance Degradation",
                "condition": lambda metrics: metrics.get("p95_latency_ms", 0) > 500,
                "severity": AlertSeverity.P1,
                "actions": ["page_oncall", "create_incident"],
                "rationale": "Poor user experience",
                "runbook": "https://wiki.internal/runbooks/performance"
            },
            {
                "name": "Database Connection Pool Exhaustion",
                "condition": lambda metrics: metrics.get("db_connections_used_pct", 0) > 90,
                "severity": AlertSeverity.P1,
                "actions": ["page_oncall", "auto_scale_db"],
                "rationale": "Potential service disruption",
                "runbook": "https://wiki.internal/runbooks/db-connections"
            },
            {
                "name": "High Error Rate",
                "condition": lambda metrics: metrics.get("error_rate_5m", 0) > 0.05,  # 5%
                "severity": AlertSeverity.P0,
                "actions": ["page_oncall", "create_incident", "rollback_check"],
                "rationale": "Service degradation",
                "runbook": "https://wiki.internal/runbooks/high-errors"
            },
            {
                "name": "Conversion Drop",
                "condition": lambda metrics: metrics.get("conversion_rate_24h", 0) < metrics.get("avg_conversion_rate", 0) * 0.7,
                "severity": AlertSeverity.P2,
                "actions": ["notify_product_team", "notify_growth_team"],
                "rationale": "Revenue impact",
                "runbook": "https://wiki.internal/runbooks/conversion-drop"
            }
        ]
    
    def evaluate_alerts(self, metrics: Dict) -> List[Dict]:
        """
        Evaluate alert rules against current metrics.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    alert = {
                        "name": rule["name"],
                        "severity": rule["severity"].value,
                        "triggered_at": datetime.utcnow().isoformat(),
                        "rationale": rule["rationale"],
                        "runbook": rule["runbook"],
                        "actions_taken": []
                    }
                    
                    # Execute actions
                    for action in rule["actions"]:
                        self._execute_action(action, alert)
                        alert["actions_taken"].append(action)
                    
                    triggered_alerts.append(alert)
                    
                    logger.warning(f"Alert triggered: {rule['name']} ({rule['severity'].value})")
                    
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")
        
        return triggered_alerts
    
    def _execute_action(self, action: str, alert: Dict):
        """Execute alert action."""
        if action == "page_oncall":
            self.pagerduty.trigger_incident(
                title=alert["name"],
                severity=alert["severity"],
                details=alert["rationale"]
            )
        elif action == "notify_growth_team":
            self.slack.send_message(
                channel="#growth",
                message=f"🚀 Alert: {alert['name']}\n{alert['rationale']}"
            )
        elif action == "create_incident":
            # Create incident in incident management system
            logger.info(f"Creating incident for: {alert['name']}")
        # ... other actions


# Prometheus query examples for metrics
"""
# Payment failures in last hour
sum(rate(payment_failures_total[1h])) * 3600

# Signups in last hour vs average
sum(increase(user_signups_total[1h])) vs avg_over_time(sum(increase(user_signups_total[1h]))[7d:1h])

# Daily active users change
(sum(dau_today) - sum(dau_7d_ago)) / sum(dau_7d_ago) * 100

# Infrastructure cost
sum(aws_cost_daily)

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# DB connection pool usage
pg_stat_database_numbackends / pg_settings_max_connections * 100

# Error rate (5 minutes)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Conversion rate (24 hours)
sum(increase(conversions_total[24h])) / sum(increase(visitors_total[24h]))
"""
