"""
Agency Report Generator
Creates professional weekly reports for agency clients.
"""
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.analytics.economics import EconomicsService

logger = get_logger(__name__)


@dataclass
class WeeklyReport:
    """A weekly report for an agency client."""
    client_id: str
    client_name: str
    agency_id: str
    
    # Time period
    week_start: datetime
    week_end: datetime
    
    # Production metrics
    shorts_produced: int
    shorts_requested: int
    success_rate: float
    
    # Quality metrics
    avg_quality_score: float
    best_hook: str
    best_hook_score: float
    
    # Economics
    total_cost: float
    cost_per_video: float
    estimated_value: float
    roi_multiplier: float
    
    # Comparison to last week
    production_change: int      # +/- videos
    quality_change: float       # +/- score
    
    # Insights
    recommendations: List[str]
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        return f"""
📊 WEEKLY REPORT: {self.client_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {self.week_start.strftime('%Y-%m-%d')} → {self.week_end.strftime('%Y-%m-%d')}

📈 PRODUCTION
   Shorts Produced: {self.shorts_produced}
   Success Rate:    {self.success_rate:.1%}
   Change vs Last:  {self.production_change:+d} videos

⭐ QUALITY
   Avg Score:       {self.avg_quality_score:.2f}
   Change vs Last:  {self.quality_change:+.2f}
   Best Hook:       "{self.best_hook[:50]}..."
   
💰 ECONOMICS
   Total Cost:      ${self.total_cost:.2f}
   Per Video:       ${self.cost_per_video:.4f}
   Est. Value:      ${self.estimated_value:.2f}
   ROI:             {self.roi_multiplier:.1f}x

💡 RECOMMENDATIONS
{chr(10).join('   • ' + r for r in self.recommendations)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class ReportGenerator:
    """
    Generates professional reports for agency clients.
    """
    
    def __init__(self):
        self.economics = EconomicsService()
        self._reports: Dict[str, List[WeeklyReport]] = {}
    
    def generate_weekly_report(
        self,
        client_id: str,
        client_name: str,
        agency_id: str,
        job_results: List[Dict],
        previous_report: WeeklyReport = None
    ) -> WeeklyReport:
        """
        Generate a weekly report for a client.
        
        Args:
            client_id: Client ID
            client_name: Client name
            agency_id: Agency ID
            job_results: List of job result dicts
            previous_report: Last week's report for comparison
            
        Returns:
            WeeklyReport
        """
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        
        # Calculate metrics
        successful = [j for j in job_results if j.get("success")]
        shorts_produced = len(successful)
        shorts_requested = len(job_results)
        success_rate = shorts_produced / shorts_requested if shorts_requested > 0 else 0
        
        # Quality
        scores = [j.get("score", 0) for j in successful if j.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Find best hook
        best_job = max(successful, key=lambda x: x.get("score", 0)) if successful else {}
        best_hook = best_job.get("hook_text", "N/A")
        best_hook_score = best_job.get("score", 0)
        
        # Economics
        total_cost = len(successful) * 0.01  # Rough estimate
        cost_per_video = total_cost / shorts_produced if shorts_produced > 0 else 0
        estimated_value = shorts_produced * 0.02  # Rough estimate
        roi = estimated_value / total_cost if total_cost > 0 else 0
        
        # Comparison
        production_change = 0
        quality_change = 0.0
        if previous_report:
            production_change = shorts_produced - previous_report.shorts_produced
            quality_change = avg_score - previous_report.avg_quality_score
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            avg_score, success_rate, quality_change
        )
        
        report = WeeklyReport(
            client_id=client_id,
            client_name=client_name,
            agency_id=agency_id,
            week_start=week_start,
            week_end=now,
            shorts_produced=shorts_produced,
            shorts_requested=shorts_requested,
            success_rate=success_rate,
            avg_quality_score=round(avg_score, 3),
            best_hook=best_hook,
            best_hook_score=best_hook_score,
            total_cost=round(total_cost, 4),
            cost_per_video=round(cost_per_video, 4),
            estimated_value=round(estimated_value, 2),
            roi_multiplier=round(roi, 1),
            production_change=production_change,
            quality_change=round(quality_change, 3),
            recommendations=recommendations
        )
        
        # Store report
        if client_id not in self._reports:
            self._reports[client_id] = []
        self._reports[client_id].append(report)
        
        logger.info(f"Generated weekly report for {client_name}: {shorts_produced} videos")
        
        return report
    
    def _generate_recommendations(
        self,
        avg_score: float,
        success_rate: float,
        quality_change: float
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if avg_score < 0.7:
            recommendations.append("Consider trying different hook types for this genre")
        
        if success_rate < 0.9:
            recommendations.append("Review failed jobs for common issues")
        
        if quality_change < 0:
            recommendations.append("Quality dipped - check for topic fatigue")
        elif quality_change > 0.05:
            recommendations.append("Quality improved! Continue with current strategy")
        
        if not recommendations:
            recommendations.append("Performance is stable. Consider A/B testing hooks")
        
        return recommendations
    
    def get_report(self, client_id: str, week_offset: int = 0) -> Optional[WeeklyReport]:
        """Get a specific week's report."""
        reports = self._reports.get(client_id, [])
        if not reports:
            return None
        
        index = -(1 + week_offset)
        if abs(index) > len(reports):
            return None
        
        return reports[index]
    
    def export_report_json(self, report: WeeklyReport) -> str:
        """Export report as JSON."""
        data = asdict(report)
        # Convert datetime to string
        data["week_start"] = report.week_start.isoformat()
        data["week_end"] = report.week_end.isoformat()
        return json.dumps(data, indent=2)
    
    def generate_headline(self, report: WeeklyReport) -> str:
        """Generate a headline for client communication."""
        return (
            f"Generated {report.shorts_produced} Shorts this week at "
            f"₹{report.cost_per_video * 83:.1f}/video. "
            f"Top hook: '{report.best_hook[:40]}...'"
        )
