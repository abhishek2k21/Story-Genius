"""
Compliance Dashboard API.
Real-time SOC 2, GDPR, and security compliance metrics.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.services.compliance_service import ComplianceService
from app.auth.dependencies import get_current_user
from app.compliance.evidence_collector import SOC2EvidenceCollector
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/dashboard")
async def get_compliance_dashboard(current_user: Dict = Depends(get_current_user)):
    """
    Get comprehensive compliance dashboard.
    
    Returns SOC 2, GDPR, and security metrics.
    """
    service = ComplianceService()
    
    dashboard = {
        "overview": await service.get_compliance_overview(),
        "soc2": await service.get_soc2_status(),
        "gdpr": await service.get_gdpr_status(),
        "security": await service.get_security_status(),
        "score": await service.calculate_overall_score()
    }
    
    return JSONResponse(dashboard)


@router.get("/soc2/controls")
async def get_soc2_controls():
    """
    Get SOC 2 controls implementation status.
    
    Returns status of all 50+ SOC 2 controls.
    """
    service = ComplianceService()
    controls = await service.get_soc2_controls_status()
    
    return JSONResponse({
        "total_controls": controls["total"],
        "implemented": controls["implemented"],
        "percentage": controls["percentage"],
        "by_category": controls["by_category"],
        "details": controls["controls"]
    })


@router.get("/soc2/evidence")
async def collect_soc2_evidence():
    """
    Trigger SOC 2 evidence collection.
    
    Collects evidence for all controls.
    """
    collector = SOC2EvidenceCollector()
    evidence = await collector.collect_all_evidence()
    
    return JSONResponse({
        "message": "Evidence collection complete",
        "summary": evidence["summary"],
        "timestamp": evidence["collection_date"]
    })


@router.get("/soc2/readiness")
async def get_soc2_readiness():
    """
    Get SOC 2 audit readiness assessment.
    
    Checks if organization is ready for SOC 2 Type II audit.
    """
    service = ComplianceService()
    readiness = await service.assess_soc2_readiness()
    
    return JSONResponse({
        "ready_for_audit": readiness["ready"],
        "compliance_score": readiness["score"],
        "missing_controls": readiness["missing"],
        "recommendations": readiness["recommendations"]
    })


@router.get("/gdpr/status")
async def get_gdpr_status():
    """
    Get GDPR compliance status.
    
    Returns status of all GDPR user rights and privacy controls.
    """
    service = ComplianceService()
    gdpr = await service.get_gdpr_compliance_status()
    
    return JSONResponse({
        "compliant": gdpr["compliant"],
        "user_rights": gdpr["user_rights"],
        "privacy_controls": gdpr["privacy_controls"],
        "data_protection": gdpr["data_protection"],
        "audit_logs": gdpr["audit_coverage"]
    })


@router.get("/security/posture")
async def get_security_posture():
    """
    Get overall security posture.
    
    Returns security metrics and vulnerability status.
    """
    service = ComplianceService()
    security = await service.get_security_posture()
    
    return JSONResponse({
        "overall_score": security["score"],
        "authentication": security["auth"],
        "encryption": security["encryption"],
        "vulnerabilities": security["vulns"],
        "network_security": security["network"],
        "access_controls": security["access"]
    })


@router.get("/metrics")
async def get_compliance_metrics():
    """
    Get key compliance metrics for monitoring.
    
    Returns metrics suitable for Prometheus/Grafana.
    """
    service = ComplianceService()
    metrics = await service.get_compliance_metrics()
    
    return JSONResponse({
        "soc2_controls_implemented": metrics["soc2_controls"],
        "gdpr_compliance_percentage": metrics["gdpr_percentage"],
        "security_score": metrics["security_score"],
        "critical_vulnerabilities": metrics["critical_vulns"],
        "high_vulnerabilities": metrics["high_vulns"],
        "encryption_coverage": metrics["encryption_coverage"],
        "audit_log_coverage": metrics["audit_coverage"],
        "uptime_percentage": metrics["uptime"]
    })


@router.get("/reports/monthly")
async def get_monthly_compliance_report():
    """
    Generate monthly compliance report.
    
    Returns comprehensive compliance status for the month.
    """
    service = ComplianceService()
    report = await service.generate_monthly_report()
    
    return JSONResponse({
        "period": report["period"],
        "executive_summary": report["summary"],
        "soc2": report["soc2"],
        "gdpr": report["gdpr"],
        "security": report["security"],
        "incidents": report["incidents"],
        "changes": report["changes"],
        "recommendations": report["recommendations"]
    })


@router.post("/scan/vulnerabilities")
async def trigger_vulnerability_scan():
    """
    Trigger on-demand vulnerability scan.
    
    Runs comprehensive security scanning.
    """
    service = ComplianceService()
    result = await service.run_vulnerability_scan()
    
    return JSONResponse({
        "message": "Vulnerability scan initiated",
        "scan_id": result["scan_id"],
        "estimated_completion": "15 minutes",
        "status_url": f"/compliance/scan/{result['scan_id']}"
    })


@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get status of vulnerability scan."""
    service = ComplianceService()
    status = await service.get_scan_status(scan_id)
    
    return JSONResponse({
        "scan_id": scan_id,
        "status": status["status"],
        "progress": status["progress"],
        "findings": status.get("findings"),
        "started_at": status["started_at"],
        "completed_at": status.get("completed_at")
    })
