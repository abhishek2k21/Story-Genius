"""
Launch Monitoring Script.
Continuous monitoring during production launch and first 24 hours.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LaunchMonitor:
    """Monitor system health and performance during launch."""
    
    def __init__(
        self,
        api_url: str = "https://api.ytvideocreator.com",
        prometheus_url: str = "http://prometheus:9090",
        slack_webhook: Optional[str] = None
    ):
        self.api_url = api_url
        self.prometheus_url = prometheus_url
        self.slack_webhook = slack_webhook
        
        # Alert thresholds
        self.thresholds = {
            "error_rate": 0.01,  # 1%
            "p95_latency": 300,  # ms
            "p99_latency": 600,  # ms
            "cpu_usage": 80,  # %
            "memory_usage": 80,  # %
            "disk_usage": 70,  # %
        }
        
        # Track issues
        self.issues = []
        self.last_alert_time = {}
    
    def check_health(self) -> bool:
        """Check API health endpoint."""
        try:
            response = requests.get(
                f"{self.api_url}/health/live",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def query_prometheus(self, query: str) -> Optional[float]:
        """Query Prometheus for a metric."""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    return float(data["data"]["result"][0]["value"][1])
            
            return None
        except Exception as e:
            logger.warning(f"Prometheus query failed: {e}")
            return None
    
    def get_error_rate(self) -> Optional[float]:
        """Get current 5xx error rate."""
        query = 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])'
        result = self.query_prometheus(query)
        return result if result else 0.0
    
    def get_p95_latency(self) -> Optional[float]:
        """Get p95 latency in milliseconds."""
        query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000'
        return self.query_prometheus(query)
    
    def get_p99_latency(self) -> Optional[float]:
        """Get p99 latency in milliseconds."""
        query = 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) * 1000'
        return self.query_prometheus(query)
    
    def get_cpu_usage(self) -> Optional[float]:
        """Get average CPU usage percentage."""
        query = 'avg(rate(container_cpu_usage_seconds_total{namespace="production"}[5m])) * 100'
        return self.query_prometheus(query)
    
    def get_memory_usage(self) -> Optional[float]:
        """Get average memory usage percentage."""
        query = 'avg(container_memory_usage_bytes{namespace="production"} / container_spec_memory_limit_bytes{namespace="production"}) * 100'
        return self.query_prometheus(query)
    
    def get_request_rate(self) -> Optional[float]:
        """Get requests per second."""
        query = 'rate(http_requests_total[1m])'
        return self.query_prometheus(query)
    
    def check_thresholds(self, metrics: Dict) -> list:
        """Check if any metrics exceed thresholds."""
        violations = []
        
        if metrics.get("error_rate", 0) > self.thresholds["error_rate"]:
            violations.append({
                "metric": "Error Rate",
                "value": f"{metrics['error_rate']*100:.2f}%",
                "threshold": f"{self.thresholds['error_rate']*100}%",
                "severity": "HIGH"
            })
        
        if metrics.get("p95_latency", 0) > self.thresholds["p95_latency"]:
            violations.append({
                "metric": "p95 Latency",
                "value": f"{metrics['p95_latency']:.0f}ms",
                "threshold": f"{self.thresholds['p95_latency']}ms",
                "severity": "MEDIUM"
            })
        
        if metrics.get("cpu_usage", 0) > self.thresholds["cpu_usage"]:
            violations.append({
                "metric": "CPU Usage",
                "value": f"{metrics['cpu_usage']:.1f}%",
                "threshold": f"{self.thresholds['cpu_usage']}%",
                "severity": "MEDIUM"
            })
        
        if metrics.get("memory_usage", 0) > self.thresholds["memory_usage"]:
            violations.append({
                "metric": "Memory Usage",
                "value": f"{metrics['memory_usage']:.1f}%",
                "threshold": f"{self.thresholds['memory_usage']}%",
                "severity": "MEDIUM"
            })
        
        return violations
    
    def send_alert(self, message: str, severity: str = "INFO"):
        """Send alert to Slack."""
        if not self.slack_webhook:
            return
        
        colors = {
            "HIGH": "danger",
            "MEDIUM": "warning",
            "LOW": "good",
            "INFO": "#36a64f"
        }
        
        try:
            requests.post(
                self.slack_webhook,
                json={
                    "text": f"🚨 Launch Monitor Alert",
                    "attachments": [{
                        "color": colors.get(severity, "good"),
                        "text": message,
                        "footer": "Launch Monitoring",
                        "ts": int(time.time())
                    }]
                },
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def collect_metrics(self) -> Dict:
        """Collect all metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "healthy": self.check_health(),
            "error_rate": self.get_error_rate(),
            "p95_latency": self.get_p95_latency(),
            "p99_latency": self.get_p99_latency(),
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "request_rate": self.get_request_rate()
        }
        
        return metrics
    
    def print_status(self, metrics: Dict):
        """Print current status."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{'='*80}")
        print(f"[{timestamp}] Launch Monitoring Status")
        print(f"{'='*80}")
        
        # Health
        health_status = "✅ HEALTHY" if metrics["healthy"] else "❌ UNHEALTHY"
        print(f"Health: {health_status}")
        
        # Metrics
        if metrics["error_rate"] is not None:
            print(f"Error Rate: {metrics['error_rate']*100:.2f}% (threshold: {self.thresholds['error_rate']*100}%)")
        
        if metrics["p95_latency"] is not None:
            print(f"p95 Latency: {metrics['p95_latency']:.0f}ms (threshold: {self.thresholds['p95_latency']}ms)")
        
        if metrics["p99_latency"] is not None:
            print(f"p99 Latency: {metrics['p99_latency']:.0f}ms (threshold: {self.thresholds['p99_latency']}ms)")
        
        if metrics["cpu_usage"] is not None:
            print(f"CPU Usage: {metrics['cpu_usage']:.1f}% (threshold: {self.thresholds['cpu_usage']}%)")
        
        if metrics["memory_usage"] is not None:
            print(f"Memory Usage: {metrics['memory_usage']:.1f}% (threshold: {self.thresholds['memory_usage']}%)")
        
        if metrics["request_rate"] is not None:
            print(f"Request Rate: {metrics['request_rate']:.1f} req/s")
        
        print(f"{'='*80}")
    
    def monitor_continuously(self, duration_hours: int = 24, check_interval: int = 60):
        """
        Monitor continuously for specified duration.
        
        Args:
            duration_hours: How long to monitor (hours)
            check_interval: Seconds between checks
        """
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        logger.info(f"🚀 Launch monitoring started")
        logger.info(f"Duration: {duration_hours} hours")
        logger.info(f"Check interval: {check_interval} seconds")
        logger.info(f"Will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Send start notification
        self.send_alert(
            f"Launch monitoring started for {duration_hours} hours",
            severity="INFO"
        )
        
        iteration = 0
        
        while datetime.now() < end_time:
            iteration += 1
            
            # Collect metrics
            metrics = self.collect_metrics()
            
            # Print status
            self.print_status(metrics)
            
            # Check for threshold violations
            violations = self.check_thresholds(metrics)
            
            if violations:
                # Log violations
                logger.warning(f"❌ {len(violations)} threshold violation(s)")
                for violation in violations:
                    logger.warning(
                        f"  - {violation['metric']}: {violation['value']} "
                        f"(threshold: {violation['threshold']})"
                    )
                    
                    # Send alert (throttled - max once per 5 minutes)
                    alert_key = violation['metric']
                    last_alert = self.last_alert_time.get(alert_key, datetime.min)
                    
                    if datetime.now() - last_alert > timedelta(minutes=5):
                        self.send_alert(
                            f"⚠️ {violation['metric']} exceeded threshold!\n"
                            f"Value: {violation['value']}\n"
                            f"Threshold: {violation['threshold']}",
                            severity=violation['severity']
                        )
                        self.last_alert_time[alert_key] = datetime.now()
                
                self.issues.append({
                    "timestamp": metrics["timestamp"],
                    "violations": violations
                })
            else:
                logger.info("✅ All metrics within thresholds")
            
            # Save metrics to file
            if iteration % 10 == 0:
                self.save_metrics(metrics)
            
            # Sleep until next check
            time.sleep(check_interval)
        
        # Monitoring complete
        logger.info("🎉 Launch monitoring completed")
        self.send_alert(
            f"Launch monitoring completed after {duration_hours} hours. "
            f"Total issues: {len(self.issues)}",
            severity="INFO"
        )
        
        # Generate summary report
        self.generate_report()
    
    def save_metrics(self, metrics: Dict):
        """Save metrics to file."""
        filename = f"logs/launch_metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        try:
            with open(filename, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def generate_report(self):
        """Generate monitoring summary report."""
        print(f"\n{'='*80}")
        print("LAUNCH MONITORING SUMMARY")
        print(f"{'='*80}")
        print(f"Total Issues: {len(self.issues)}")
        
        if self.issues:
            print("\nIssues by Type:")
            issue_types = {}
            for issue in self.issues:
                for violation in issue["violations"]:
                    metric = violation["metric"]
                    issue_types[metric] = issue_types.get(metric, 0) + 1
            
            for metric, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {metric}: {count} occurrence(s)")
        else:
            print("\n✅ No issues detected during monitoring period!")
        
        print(f"{'='*80}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch Monitoring")
    parser.add_argument(
        "--duration",
        type=int,
        default=24,
        help="Monitoring duration in hours (default: 24)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--slack-webhook",
        type=str,
        help="Slack webhook URL for alerts"
    )
    
    args = parser.parse_args()
    
    monitor = LaunchMonitor(slack_webhook=args.slack_webhook)
    monitor.monitor_continuously(
        duration_hours=args.duration,
        check_interval=args.interval
    )
