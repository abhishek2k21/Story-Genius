"""
Custom Report Builder.
Drag-and-drop report creation with scheduled generation and exports.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import csv
import io
import uuid
import logging

logger = logging.getLogger(__name__)


class ReportMetric(str, Enum):
    """Available report metrics."""
    VIEWS = "views"
    LIKES = "likes"
    SHARES = "shares"
    ENGAGEMENT = "engagement"
    REVENUE = "revenue"
    CONVERSIONS = "conversions"
    ACTIVE_USERS = "active_users"
    NEW_USERS = "new_users"
    CHURN_RATE = "churn_rate"


class ReportDimension(str, Enum):
    """Available report dimensions."""
    DATE = "date"
    PLATFORM = "platform"
    VIDEO = "video"
    USER = "user"
    COUNTRY = "country"
    DEVICE = "device"


class ExportFormat(str, Enum):
    """Export formats."""
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    PDF = "pdf"


class ReportBuilder:
    """Build and schedule custom analytics reports."""
    
    def __init__(self, analytics_service, export_service, scheduler):
        self.analytics = analytics_service
        self.export_service = export_service
        self.scheduler = scheduler
        self.reports: Dict[str, Dict] = {}
    
    def create_report(
        self,
        user_id: str,
        config: Dict
    ) -> Dict:
        """
        Create custom report template.
        
        Config structure:
        {
          "name": "Monthly Performance",
          "description": "Track monthly video performance",
          "metrics": ["views", "engagement", "revenue"],
          "dimensions": ["platform", "date"],
          "filters": [
            {"field": "date", "operator": ">=", "value": "2026-01-01"},
            {"field": "platform", "operator": "in", "value": ["youtube", "instagram"]}
          ],
          "groupBy": "platform",
          "orderBy": {"field": "views", "direction": "desc"},
          "limit": 100,
          "schedule": "0 9 * * 1"  # Every Monday at 9am (cron)
        }
        
        Args:
            user_id: User ID
            config: Report configuration
            
        Returns:
            Created report details
        """
        # Validate configuration
        self._validate_report_config(config)
        
        # Create report
        report_id = str(uuid.uuid4())
        
        report = {
            "id": report_id,
            "user_id": user_id,
            "name": config["name"],
            "description": config.get("description", ""),
            "config": config,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_run": None,
            "next_run": None,
            "enabled": True
        }
        
        # Save report
        self.reports[report_id] = report
        self._save_report(report)
        
        # Schedule if requested
        if config.get("schedule"):
            next_run = self.scheduler.schedule_job(
                job_id=report_id,
                cron_expression=config["schedule"],
                callback=lambda: self.generate_report(report_id)
            )
            report["next_run"] = next_run
        
        logger.info(f"Created report {report_id}: {config['name']}")
        
        return {
            "report_id": report_id,
            "name": report["name"],
            "metrics": config["metrics"],
            "schedule": config.get("schedule"),
            "next_run": report["next_run"].isoformat() if report["next_run"] else None
        }
    
    def _validate_report_config(self, config: Dict):
        """Validate report configuration."""
        # Required fields
        if "name" not in config:
            raise ValueError("Report name is required")
        
        if "metrics" not in config or not config["metrics"]:
            raise ValueError("At least one metric is required")
        
        # Validate metrics
        valid_metrics = [m.value for m in ReportMetric]
        for metric in config["metrics"]:
            if metric not in valid_metrics:
                raise ValueError(f"Invalid metric: {metric}")
        
        # Validate dimensions
        if "dimensions" in config:
            valid_dimensions = [d.value for d in ReportDimension]
            for dimension in config["dimensions"]:
                if dimension not in valid_dimensions:
                    raise ValueError(f"Invalid dimension: {dimension}")
    
    async def generate_report(
        self,
        report_id: str,
        date_range: Optional[Dict] = None
    ) -> Dict:
        """
        Generate report data.
        
        Args:
            report_id: Report ID
            date_range: Optional custom date range
            
        Returns:
            Report data with visualizations
        """
        report = self.reports.get(report_id)
        
        if not report:
            raise ValueError(f"Report not found: {report_id}")
        
        logger.info(f"Generating report {report_id}")
        
        config = report["config"]
        
        # Apply date range if provided
        filters = config.get("filters", [])
        if date_range:
            filters.append({
                "field": "date",
                "operator": ">=",
                "value": date_range["start"]
            })
            filters.append({
                "field": "date",
                "operator": "<=",
                "value": date_range["end"]
            })
        
        # Build query
        query = {
            "user_id": report["user_id"],
            "metrics": config["metrics"],
            "dimensions": config.get("dimensions", []),
            "filters": filters,
            "group_by": config.get("groupBy"),
            "order_by": config.get("orderBy"),
            "limit": config.get("limit", 1000)
        }
        
        # Execute query
        data = await self._execute_report_query(query)
        
        # Generate visualizations
        charts = self._generate_charts(data, config)
        
        # Calculate summary statistics
        summary = self._calculate_summary(data, config["metrics"])
        
        # Update report metadata
        report["last_run"] = datetime.utcnow()
        self._save_report(report)
        
        result = {
            "report_id": report_id,
            "name": report["name"],
            "generated_at": datetime.utcnow().isoformat(),
            "data": data,
            "charts": charts,
            "summary": summary,
            "row_count": len(data)
        }
        
        logger.info(f"Generated report {report_id} with {len(data)} rows")
        
        return result
    
    async def _execute_report_query(self, query: Dict) -> List[Dict]:
        """Execute analytics query."""
        # Query analytics data
        # Placeholder: would query from analytics service
        
        # Example data
        return [
            {
                "date": "2026-01-01",
                "platform": "youtube",
                "views": 1250,
                "engagement": 8.5,
                "revenue": 125.50
            },
            {
                "date": "2026-01-01",
                "platform": "instagram",
                "views": 850,
                "engagement": 12.3,
                "revenue": 85.20
            }
        ]
    
    def _generate_charts(self, data: List[Dict], config: Dict) -> List[Dict]:
        """Generate chart configurations for visualization."""
        charts = []
        
        metrics = config["metrics"]
        dimensions = config.get("dimensions", [])
        
        # Line chart for time series
        if "date" in dimensions:
            for metric in metrics:
                charts.append({
                    "type": "line",
                    "title": f"{metric.capitalize()} Over Time",
                    "x_axis": "date",
                    "y_axis": metric,
                    "data": [
                        {"x": row["date"], "y": row.get(metric, 0)}
                        for row in data
                    ]
                })
        
        # Bar chart for platform comparison
        if "platform" in dimensions:
            for metric in metrics:
                charts.append({
                    "type": "bar",
                    "title": f"{metric.capitalize()} by Platform",
                    "x_axis": "platform",
                    "y_axis": metric,
                    "data": [
                        {"x": row["platform"], "y": row.get(metric, 0)}
                        for row in data
                    ]
                })
        
        return charts
    
    def _calculate_summary(self, data: List[Dict], metrics: List[str]) -> Dict:
        """Calculate summary statistics."""
        summary = {}
        
        for metric in metrics:
            values = [row.get(metric, 0) for row in data if metric in row]
            
            if values:
                summary[metric] = {
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return summary
    
    def list_reports(self, user_id: str) -> List[Dict]:
        """List all reports for user."""
        user_reports = [
            r for r in self.reports.values()
            if r["user_id"] == user_id
        ]
        
        return [
            {
                "report_id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "metrics": r["config"]["metrics"],
                "schedule": r["config"].get("schedule"),
                "last_run": r["last_run"].isoformat() if r["last_run"] else None,
                "next_run": r["next_run"].isoformat() if r["next_run"] else None,
                "enabled": r["enabled"]
            }
            for r in user_reports
        ]
    
    def delete_report(self, report_id: str, user_id: str) -> bool:
        """Delete report."""
        report = self.reports.get(report_id)
        
        if not report or report["user_id"] != user_id:
            return False
        
        # Unschedule if scheduled
        if report["config"].get("schedule"):
            self.scheduler.cancel_job(report_id)
        
        # Delete report
        del self.reports[report_id]
        self._delete_report(report_id)
        
        logger.info(f"Deleted report {report_id}")
        
        return True
    
    def _save_report(self, report: Dict):
        """Save report to database."""
        pass
    
    def _delete_report(self, report_id: str):
        """Delete report from database."""
        pass


class DataExportService:
    """Export analytics data in multiple formats."""
    
    def __init__(self, s3_client, email_service):
        self.s3 = s3_client
        self.email = email_service
    
    async def export_report(
        self,
        report_data: Dict,
        format: str,
        user_email: str
    ) -> str:
        """
        Export report data to file.
        
        Args:
            report_data: Report data from ReportBuilder
            format: Export format (csv, xlsx, json, pdf)
            user_email: User email for delivery
            
        Returns:
            Download URL
        """
        export_format = ExportFormat(format)
        
        logger.info(f"Exporting report to {format}")
        
        # Generate file
        if export_format == ExportFormat.CSV:
            file_path = await self._export_csv(report_data)
        
        elif export_format == ExportFormat.XLSX:
            file_path = await self._export_excel(report_data)
        
        elif export_format == ExportFormat.JSON:
            file_path = await self._export_json(report_data)
        
        elif export_format == ExportFormat.PDF:
            file_path = await self._export_pdf(report_data)
        
        # Upload to S3
        download_url = await self._upload_to_s3(file_path)
        
        # Send email with download link
        await self.email.send_export_ready(
            to_email=user_email,
            report_name=report_data["name"],
            download_url=download_url,
            expires_in_hours=24
        )
        
        logger.info(f"Export ready: {download_url}")
        
        return download_url
    
    async def _export_csv(self, report_data: Dict) -> str:
        """Export to CSV format."""
        file_path = f"/tmp/report_{report_data['report_id']}.csv"
        
        with open(file_path, 'w', newline='') as f:
            if report_data["data"]:
                writer = csv.DictWriter(f, fieldnames=report_data["data"][0].keys())
                writer.writeheader()
                writer.writerows(report_data["data"])
        
        return file_path
    
    async def _export_excel(self, report_data: Dict) -> str:
        """Export to Excel format with formatting."""
        # Placeholder: would use openpyxl or xlsxwriter
        file_path = f"/tmp/report_{report_data['report_id']}.xlsx"
        return file_path
    
    async def _export_json(self, report_data: Dict) -> str:
        """Export to JSON format."""
        file_path = f"/tmp/report_{report_data['report_id']}.json"
        
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return file_path
    
    async def _export_pdf(self, report_data: Dict) -> str:
        """Export to PDF report with charts."""
        # Placeholder: would use reportlab or weasyprint
        file_path = f"/tmp/report_{report_data['report_id']}.pdf"
        return file_path
    
    async def _upload_to_s3(self, file_path: str) -> str:
        """Upload file to S3 and return download URL."""
        # Upload to S3 with presigned URL
        # Placeholder
        return f"https://downloads.ytvideocreator.com/{file_path.split('/')[-1]}"
