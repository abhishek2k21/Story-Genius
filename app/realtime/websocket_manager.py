"""
WebSocket Manager for Real-time Notifications
Handles WebSocket connections and broadcasts events.
"""
from typing import Dict, Set, Any
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WebSocketMessage:
    """WebSocket message"""
    type: str  # success, error, warning, info
    message: str
    data: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "message": self.message,
            "data": self.data or {},
            "timestamp": self.timestamp.isoformat()
        })


class WebSocketConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    """
    
    def __init__(self):
        # Active connections: {user_id: set of websockets}
        self._connections: Dict[str, Set] = {}
        logger.info("WebSocketConnectionManager initialized")
    
    async def connect(self, websocket, user_id: str):
        """
        Connect a WebSocket client.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        
        if user_id not in self._connections:
            self._connections[user_id] = set()
        
        self._connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: user={user_id}")
        
        # Send welcome message
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="info",
                message="Connected to real-time notifications"
            )
        )
    
    def disconnect(self, websocket, user_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            
            # Remove user if no more connections
            if not self._connections[user_id]:
                del self._connections[user_id]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_message(
        self,
        user_id: str,
        message: WebSocketMessage
    ):
        """
        Send message to specific user.
        
        Args:
            user_id: User ID
            message: Message to send
        """
        if user_id not in self._connections:
            logger.warning(f"No active connections for user: {user_id}")
            return
        
        # Send to all user's connections
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_text(message.to_json())
                logger.debug(f"Sent message to user {user_id}: {message.type}")
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
    
    async def broadcast(self, message: WebSocketMessage):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        total_sent = 0
        
        for user_id, websockets in self._connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(message.to_json())
                    total_sent += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to {user_id}: {e}")
        
        logger.info(f"Broadcast message to {total_sent} connections")
    
    async def notify_video_created(self, user_id: str, video_id: str, title: str):
        """Notify video creation started"""
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="info",
                message=f"Video generation started: {title}",
                data={"video_id": video_id, "status": "started"}
            )
        )
    
    async def notify_video_completed(self, user_id: str, video_id: str, title: str):
        """Notify video generation completed"""
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="success",
                message=f"Video generation completed: {title}",
                data={"video_id": video_id, "status": "completed"}
            )
        )
    
    async def notify_video_failed(self, user_id: str, video_id: str, error: str):
        """Notify video generation failed"""
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="error",
                message=f"Video generation failed: {error}",
                data={"video_id": video_id, "status": "failed", "error": error}
            )
        )
    
    async def notify_batch_progress(self, user_id: str, batch_id: str, progress: int, total: int):
        """Notify batch processing progress"""
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="info",
                message=f"Batch processing: {progress}/{total} completed",
                data={
                    "batch_id": batch_id,
                    "progress": progress,
                    "total": total,
                    "percentage": round((progress / total) * 100, 1)
                }
            )
        )
    
    async def notify_quality_approved(self, user_id: str, video_id: str, score: float):
        """Notify quality auto-approved"""
        await self.send_personal_message(
            user_id,
            WebSocketMessage(
                type="success",
                message=f"Video auto-approved with quality score: {score}",
                data={"video_id": video_id, "quality_score": score}
            )
        )
    
    def get_active_connections(self) -> int:
        """Get total active connections"""
        return sum(len(sockets) for sockets in self._connections.values())
    
    def get_active_users(self) -> int:
        """Get total active users"""
        return len(self._connections)


# Global instance
ws_manager = WebSocketConnectionManager()
