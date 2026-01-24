"""
Automated Reporting
Scheduled report generation without manual triggers.
"""
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.agency.report_generator import ReportGenerator, WeeklyReport
from app.analytics.revenue_dashboard import RevenueDashboard

logger = get_logger(__name__)


@dataclass
class ScheduledReport:
    """A scheduled report configuration."""
    client_id: str
    frequency: str  # "daily", "weekly", "monthly"
    day_of_week: int = 0  # 0=Monday for weekly
    hour: int = 9  # 9 AM
    last_sent: datetime = None
    next_scheduled: datetime = None


class ReportScheduler:
    """
    Automated report scheduling and generation.
    """
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self._schedules: Dict[str, ScheduledReport] = {}
    
    def schedule_weekly(
        self,
        client_id: str,
        day_of_week: int = 0,  # Monday
        hour: int = 9
    ):
        """Schedule weekly report for a client."""
        schedule = ScheduledReport(
            client_id=client_id,
            frequency="weekly",
            day_of_week=day_of_week,
            hour=hour,
            next_scheduled=self._next_weekly(day_of_week, hour)
        )
        self._schedules[client_id] = schedule
        logger.info(f"Scheduled weekly report for {client_id[:8]} on day {day_of_week} at {hour}:00")
    
    def _next_weekly(self, day_of_week: int, hour: int) -> datetime:
        """Calculate next weekly occurrence."""
        now = datetime.utcnow()
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_date = now + timedelta(days=days_ahead)
        return next_date.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    def get_due_reports(self) -> List[str]:
        """Get list of client IDs with due reports."""
        now = datetime.utcnow()
        due = []
        
        for client_id, schedule in self._schedules.items():
            if schedule.next_scheduled and now >= schedule.next_scheduled:
                due.append(client_id)
        
        return due
    
    def generate_and_mark(
        self,
        client_id: str,
        job_results: List[Dict]
    ) -> Optional[WeeklyReport]:
        """Generate report and update schedule."""
        schedule = self._schedules.get(client_id)
        if not schedule:
            return None
        
        # Get previous report for comparison
        previous = self.report_generator.get_report(client_id, week_offset=1)
        
        # Generate new report
        report = self.report_generator.generate_weekly_report(
            client_id=client_id,
            client_name=client_id,  # Would get from client service
            agency_id="",
            job_results=job_results,
            previous_report=previous
        )
        
        # Update schedule
        schedule.last_sent = datetime.utcnow()
        if schedule.frequency == "weekly":
            schedule.next_scheduled = self._next_weekly(
                schedule.day_of_week, schedule.hour
            )
        
        logger.info(f"Generated scheduled report for {client_id[:8]}")
        return report
    
    def run_scheduled_reports(self, job_results_by_client: Dict[str, List[Dict]]):
        """Run all due scheduled reports."""
        due = self.get_due_reports()
        
        for client_id in due:
            results = job_results_by_client.get(client_id, [])
            self.generate_and_mark(client_id, results)
    
    def get_schedule_summary(self) -> Dict:
        """Get summary of all schedules."""
        return {
            "total_schedules": len(self._schedules),
            "schedules": [
                {
                    "client_id": s.client_id[:8],
                    "frequency": s.frequency,
                    "next": s.next_scheduled.isoformat() if s.next_scheduled else None
                }
                for s in self._schedules.values()
            ]
        }


class AutoInsights:
    """
    Auto-generated insights for reports.
    """
    
    @staticmethod
    def generate_insights(job_results: List[Dict]) -> Dict:
        """Generate insights from job results."""
        if not job_results:
            return {"status": "no_data"}
        
        successful = [j for j in job_results if j.get("success")]
        scores = [j.get("score", 0) for j in successful if j.get("score")]
        
        # Find best hook
        best_job = max(successful, key=lambda x: x.get("score", 0)) if successful else {}
        
        # Detect anomalies
        anomalies = []
        if len(successful) < len(job_results) * 0.8:
            anomalies.append(f"High failure rate: {len(successful)}/{len(job_results)}")
        
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.7:
            anomalies.append(f"Quality below threshold: {avg_score:.2f}")
        
        return {
            "output_delivered": len(successful),
            "total_requested": len(job_results),
            "success_rate": len(successful) / len(job_results) if job_results else 0,
            "avg_quality": round(avg_score, 2),
            "best_hook": best_job.get("hook_text", "N/A")[:50],
            "best_score": best_job.get("score", 0),
            "anomalies": anomalies
        }
