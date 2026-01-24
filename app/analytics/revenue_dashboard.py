"""
Revenue Dashboard Service
Tracks business health: clients, revenue, costs, margins.
"""
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ClientRevenue:
    """Revenue tracking for a client."""
    client_id: str
    client_name: str
    
    # Revenue
    monthly_fee: float  # INR
    videos_quota: int
    videos_delivered: int
    
    # Costs
    cost_per_video: float = 1.0  # INR
    total_cost: float = 0.0
    
    # Health
    success_rate: float = 0.0
    avg_quality: float = 0.0
    last_delivery: datetime = None
    
    # Churn signals
    days_since_delivery: int = 0
    support_tickets: int = 0
    complaints: int = 0
    
    @property
    def revenue(self) -> float:
        return self.monthly_fee
    
    @property
    def margin(self) -> float:
        if self.revenue == 0:
            return 0
        return (self.revenue - self.total_cost) / self.revenue * 100
    
    @property
    def churn_risk(self) -> str:
        """Estimate churn risk level."""
        risk_score = 0
        
        if self.days_since_delivery > 7:
            risk_score += 2
        if self.success_rate < 0.8:
            risk_score += 2
        if self.complaints > 0:
            risk_score += self.complaints
        if self.videos_delivered < self.videos_quota * 0.5:
            risk_score += 1
        
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        return "LOW"


@dataclass
class DashboardSnapshot:
    """Point-in-time business snapshot."""
    timestamp: datetime
    
    # Clients
    active_clients: int
    total_clients: int
    
    # Delivery
    videos_this_month: int
    videos_this_week: int
    avg_success_rate: float
    avg_quality: float
    
    # Revenue
    mrr: float  # Monthly Recurring Revenue
    total_cost: float
    gross_margin: float
    
    # Health
    clients_at_risk: int
    open_issues: int


class RevenueDashboard:
    """
    Founder-view revenue dashboard.
    One glance = business health.
    """
    
    def __init__(self):
        self._clients: Dict[str, ClientRevenue] = {}
        self._snapshots: List[DashboardSnapshot] = []
    
    def add_client(
        self,
        client_id: str,
        client_name: str,
        monthly_fee: float,
        videos_quota: int
    ) -> ClientRevenue:
        """Register a paying client."""
        client = ClientRevenue(
            client_id=client_id,
            client_name=client_name,
            monthly_fee=monthly_fee,
            videos_quota=videos_quota,
            last_delivery=datetime.utcnow()
        )
        self._clients[client_id] = client
        logger.info(f"Registered client: {client_name} @ ₹{monthly_fee}/mo")
        return client
    
    def record_delivery(
        self,
        client_id: str,
        videos_count: int,
        success_rate: float,
        avg_quality: float,
        cost: float
    ):
        """Record a delivery for a client."""
        if client_id not in self._clients:
            return
        
        client = self._clients[client_id]
        client.videos_delivered += videos_count
        client.success_rate = success_rate
        client.avg_quality = avg_quality
        client.total_cost += cost
        client.last_delivery = datetime.utcnow()
        client.days_since_delivery = 0
    
    def record_complaint(self, client_id: str):
        """Record a client complaint."""
        if client_id in self._clients:
            self._clients[client_id].complaints += 1
    
    def get_snapshot(self) -> DashboardSnapshot:
        """Get current business snapshot."""
        clients = list(self._clients.values())
        active = [c for c in clients if c.videos_delivered > 0]
        
        total_mrr = sum(c.monthly_fee for c in clients)
        total_cost = sum(c.total_cost for c in clients)
        total_videos = sum(c.videos_delivered for c in clients)
        
        avg_success = sum(c.success_rate for c in active) / len(active) if active else 0
        avg_quality = sum(c.avg_quality for c in active) / len(active) if active else 0
        
        at_risk = len([c for c in clients if c.churn_risk == "HIGH"])
        
        snapshot = DashboardSnapshot(
            timestamp=datetime.utcnow(),
            active_clients=len(active),
            total_clients=len(clients),
            videos_this_month=total_videos,
            videos_this_week=0,  # Would need date filtering
            avg_success_rate=round(avg_success, 2),
            avg_quality=round(avg_quality, 2),
            mrr=total_mrr,
            total_cost=total_cost,
            gross_margin=round((total_mrr - total_cost) / total_mrr * 100, 1) if total_mrr > 0 else 0,
            clients_at_risk=at_risk,
            open_issues=sum(c.complaints for c in clients)
        )
        
        self._snapshots.append(snapshot)
        return snapshot
    
    def display(self) -> str:
        """Generate dashboard display."""
        snap = self.get_snapshot()
        clients = list(self._clients.values())
        
        output = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                     💰 REVENUE DASHBOARD                            ║
║                     {snap.timestamp.strftime('%Y-%m-%d %H:%M')}                              ║
╠══════════════════════════════════════════════════════════════════════╣
║  CLIENTS                        REVENUE
║  ─────────────────              ─────────────────
║  Active:    {snap.active_clients:<3}                    MRR:     ₹{snap.mrr:,.0f}
║  Total:     {snap.total_clients:<3}                    Cost:    ₹{snap.total_cost:,.0f}
║  At Risk:   {snap.clients_at_risk:<3}                    Margin:  {snap.gross_margin:.1f}%
╠══════════════════════════════════════════════════════════════════════╣
║  DELIVERY                       QUALITY
║  ─────────────────              ─────────────────
║  Videos:    {snap.videos_this_month:<5}                 Success: {snap.avg_success_rate:.0%}
║  Issues:    {snap.open_issues:<3}                    Quality: {snap.avg_quality:.2f}
╠══════════════════════════════════════════════════════════════════════╣
║  CLIENT BREAKDOWN
║  ─────────────────────────────────────────────────────────────────"""
        
        for c in clients:
            risk_icon = "🔴" if c.churn_risk == "HIGH" else "🟡" if c.churn_risk == "MEDIUM" else "🟢"
            output += f"""
║  {risk_icon} {c.client_name[:20]:<20}  ₹{c.monthly_fee:>6,.0f}  {c.videos_delivered}/{c.videos_quota} videos  {c.margin:.0f}% margin"""
        
        output += """
╚══════════════════════════════════════════════════════════════════════╝
"""
        return output
    
    def export_json(self) -> str:
        """Export dashboard as JSON."""
        snap = self.get_snapshot()
        data = {
            "snapshot": asdict(snap),
            "clients": [asdict(c) for c in self._clients.values()]
        }
        data["snapshot"]["timestamp"] = snap.timestamp.isoformat()
        for c in data["clients"]:
            if c["last_delivery"]:
                c["last_delivery"] = c["last_delivery"].isoformat() if isinstance(c["last_delivery"], datetime) else c["last_delivery"]
        return json.dumps(data, indent=2, default=str)
