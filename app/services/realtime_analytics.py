"""
Real-Time Analytics Dashboard.
Live metrics with WebSocket streaming and interactive visualizations.
"""
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class RealtimeAnalytics:
    """Real-time analytics with WebSocket streaming."""
    
    def __init__(self, websocket_manager, analytics_service):
        self.ws_manager = websocket_manager
        self.analytics = analytics_service
        self.active_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of metric names
    
    async def subscribe_metrics(
        self,
        user_id: str,
        metrics: List[str]
    ) -> str:
        """
        Subscribe user to real-time metric updates.
        
        Available metrics:
        - active_users: Current active users count
        - video_views_live: Live video view count
        - revenue_today: Today's revenue
        - api_requests_per_min: API request rate
        - system_health: Platform health score (0-100)
        - videos_created_today: Videos created today
        - conversion_rate: Real-time conversion rate
        
        Args:
            user_id: User ID
            metrics: List of metric names to stream
            
        Returns:
            Subscription ID
        """
        # Validate metrics
        valid_metrics = [
            "active_users",
            "video_views_live",
            "revenue_today",
            "api_requests_per_min",
            "system_health",
            "videos_created_today",
            "conversion_rate"
        ]
        
        for metric in metrics:
            if metric not in valid_metrics:
                raise ValueError(f"Invalid metric: {metric}")
        
        # Store subscription
        if user_id not in self.active_subscriptions:
            self.active_subscriptions[user_id] = set()
        
        self.active_subscriptions[user_id].update(metrics)
        
        # Start streaming task
        asyncio.create_task(self._stream_metrics(user_id))
        
        logger.info(f"User {user_id} subscribed to {len(metrics)} metrics")
        
        return f"subscription_{user_id}"
    
    async def _stream_metrics(self, user_id: str):
        """Stream metrics to user via WebSocket."""
        
        update_interval = 5  # seconds
        
        while user_id in self.active_subscriptions:
            # Get subscribed metrics
            metrics = self.active_subscriptions.get(user_id, set())
            
            if not metrics:
                break
            
            # Fetch current values
            data = await self._get_current_metrics(list(metrics))
            
            # Send via WebSocket
            try:
                await self.ws_manager.send_json(
                    user_id,
                    {
                        "type": "metrics_update",
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send metrics to {user_id}: {e}")
                break
            
            # Wait before next update
            await asyncio.sleep(update_interval)
        
        # Cleanup
        if user_id in self.active_subscriptions:
            del self.active_subscriptions[user_id]
        
        logger.info(f"Stopped streaming metrics to {user_id}")
    
    async def _get_current_metrics(self, metrics: List[str]) -> Dict:
        """Fetch current values for requested metrics."""
        
        data = {}
        
        for metric in metrics:
            if metric == "active_users":
                value = await self._get_active_users()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("active_users", value),
                    "trend": self._calculate_trend(value, await self._get_previous_value("active_users"))
                }
            
            elif metric == "video_views_live":
                value = await self._get_live_video_views()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("video_views_live", value)
                }
            
            elif metric == "revenue_today":
                value = await self._get_revenue_today()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("revenue_today", value),
                    "formatted": f"${value:,.2f}"
                }
            
            elif metric == "api_requests_per_min":
                value = await self._get_api_request_rate()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("api_requests_per_min", value)
                }
            
            elif metric == "system_health":
                value = await self._get_system_health()
                data[metric] = {
                    "value": value,
                    "status": self._health_status(value),
                    "color": self._health_color(value)
                }
            
            elif metric == "videos_created_today":
                value = await self._get_videos_created_today()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("videos_created_today", value)
                }
            
            elif metric == "conversion_rate":
                value = await self._get_conversion_rate()
                data[metric] = {
                    "value": value,
                    "change": await self._get_metric_change("conversion_rate", value),
                    "formatted": f"{value:.1f}%"
                }
        
        return data
    
    # Metric fetchers
    
    async def _get_active_users(self) -> int:
        """Get current active users (last 15 minutes)."""
        # Query active sessions
        # Placeholder
        return 450
    
    async def _get_live_video_views(self) -> int:
        """Get live video views (current minute)."""
        # Query view events
        # Placeholder
        return 1250
    
    async def _get_revenue_today(self) -> float:
        """Get today's revenue."""
        # Query revenue from subscriptions and purchases
        # Placeholder
        return 15420.50
    
    async def _get_api_request_rate(self) -> int:
        """Get API requests per minute."""
        # Query from monitoring system
        # Placeholder
        return 2850
    
    async def _get_system_health(self) -> int:
        """Get system health score (0-100)."""
        # Calculate from platform metrics
        # Placeholder: could use advanced_monitoring.py
        return 96
    
    async def _get_videos_created_today(self) -> int:
        """Get videos created today."""
        # Query database
        # Placeholder
        return 245
    
    async def _get_conversion_rate(self) -> float:
        """Get current conversion rate."""
        # Calculate from signups to paid
        # Placeholder
        return 24.5
    
    # Helper methods
    
    async def _get_metric_change(self, metric: str, current_value: float) -> float:
        """Calculate change from previous value."""
        previous = await self._get_previous_value(metric)
        
        if previous == 0:
            return 0
        
        change = ((current_value - previous) / previous) * 100
        return round(change, 1)
    
    async def _get_previous_value(self, metric: str) -> float:
        """Get previous value for comparison."""
        # Query from cache or database
        # Placeholder
        values = {
            "active_users": 425,
            "video_views_live": 1180,
            "revenue_today": 14800.0,
            "api_requests_per_min": 2750,
            "videos_created_today": 230,
            "conversion_rate": 23.8
        }
        return values.get(metric, 0)
    
    def _calculate_trend(self, current: float, previous: float) -> str:
        """Calculate trend direction."""
        if current > previous:
            return "up"
        elif current < previous:
            return "down"
        else:
            return "stable"
    
    def _health_status(self, score: int) -> str:
        """Get health status from score."""
        if score >= 95:
            return "Excellent"
        elif score >= 85:
            return "Good"
        elif score >= 70:
            return "Fair"
        else:
            return "Poor"
    
    def _health_color(self, score: int) -> str:
        """Get color for health score."""
        if score >= 95:
            return "green"
        elif score >= 85:
            return "blue"
        elif score >= 70:
            return "yellow"
        else:
            return "red"
    
    def unsubscribe_metrics(self, user_id: str):
        """Unsubscribe user from all metrics."""
        if user_id in self.active_subscriptions:
            del self.active_subscriptions[user_id]
            logger.info(f"User {user_id} unsubscribed from metrics")
    
    def get_active_subscriptions(self) -> Dict:
        """Get all active subscriptions."""
        return {
            "total_users": len(self.active_subscriptions),
            "subscriptions": {
                user_id: list(metrics)
                for user_id, metrics in self.active_subscriptions.items()
            }
        }


# FastAPI WebSocket endpoint
"""
from fastapi import WebSocket, WebSocketDisconnect
from app.services.realtime_analytics import RealtimeAnalytics

@app.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    '''Real-time analytics WebSocket endpoint.'''
    
    await websocket.accept()
    
    user_id = None
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data["type"] == "subscribe":
                user_id = data["user_id"]
                metrics = data["metrics"]
                
                # Subscribe to metrics
                realtime = RealtimeAnalytics(websocket_manager, analytics_service)
                await realtime.subscribe_metrics(user_id, metrics)
            
            elif data["type"] == "unsubscribe":
                if user_id:
                    realtime.unsubscribe_metrics(user_id)
    
    except WebSocketDisconnect:
        if user_id:
            realtime.unsubscribe_metrics(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
"""


# React dashboard component
"""
// RealtimeDashboard.tsx

import React, { useEffect, useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';

interface Metric {
  value: number;
  change: number;
  trend?: string;
  formatted?: string;
}

const RealtimeDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Record<string, Metric>>({});
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('wss://api.ytvideocreator.com/ws/analytics');
    
    ws.onopen = () => {
      setConnected(true);
      
      // Subscribe to metrics
      ws.send(JSON.stringify({
        type: 'subscribe',
        user_id: currentUser.id,
        metrics: [
          'active_users',
          'video_views_live',
          'revenue_today',
          'system_health'
        ]
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'metrics_update') {
        setMetrics(data.data);
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
    };
    
    return () => {
      ws.send(JSON.stringify({ type: 'unsubscribe' }));
      ws.close();
    };
  }, []);
  
  return (
    <div className="realtime-dashboard">
      <div className="connection-status">
        {connected ? '🟢 Live' : '🔴 Disconnected'}
      </div>
      
      <div className="metrics-grid">
        <MetricCard
          title="Active Users"
          value={metrics.active_users?.value}
          change={metrics.active_users?.change}
          trend={metrics.active_users?.trend}
          icon="👥"
        />
        
        <MetricCard
          title="Live Views"
          value={metrics.video_views_live?.value}
          change={metrics.video_views_live?.change}
          icon="👁️"
        />
        
        <MetricCard
          title="Revenue Today"
          value={metrics.revenue_today?.formatted}
          change={metrics.revenue_today?.change}
          icon="💰"
        />
        
        <MetricCard
          title="System Health"
          value={`${metrics.system_health?.value}%`}
          status={metrics.system_health?.status}
          color={metrics.system_health?.color}
          icon="❤️"
        />
      </div>
    </div>
  );
};
"""
