"""
WebSocket Manager
Real-time job progress updates.
"""
import asyncio
import json
from typing import Dict, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from src.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for job progress."""

    def __init__(self):
        # job_id -> set of connected WebSockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> set of connected WebSockets
        self._user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()

        if job_id not in self._connections:
            self._connections[job_id] = set()

        self._connections[job_id].add(websocket)
        logger.debug(f"WebSocket connected for job {job_id}")

    async def connect_user(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a user-level WebSocket connection."""
        await websocket.accept()

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()

        self._user_connections[user_id].add(websocket)
        logger.debug(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """Remove a WebSocket connection."""
        if job_id in self._connections:
            self._connections[job_id].discard(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]

    def disconnect_user(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a user-level WebSocket connection."""
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

    async def send_progress(
        self,
        job_id: str,
        progress: float,
        step: str,
        message: str = "",
    ) -> None:
        """Send progress update to all connections for a job."""
        if job_id not in self._connections:
            return

        data = {
            "type": "progress",
            "job_id": job_id,
            "progress": progress,
            "step": step,
            "message": message,
        }

        await self._broadcast(self._connections[job_id], data)

    async def send_completed(
        self,
        job_id: str,
        result: dict,
    ) -> None:
        """Send completion notification."""
        if job_id not in self._connections:
            return

        data = {
            "type": "completed",
            "job_id": job_id,
            "result": result,
        }

        await self._broadcast(self._connections[job_id], data)

    async def send_error(
        self,
        job_id: str,
        error: str,
    ) -> None:
        """Send error notification."""
        if job_id not in self._connections:
            return

        data = {
            "type": "error",
            "job_id": job_id,
            "error": error,
        }

        await self._broadcast(self._connections[job_id], data)

    async def send_to_user(
        self,
        user_id: str,
        data: dict,
    ) -> None:
        """Send message to all user connections."""
        if user_id not in self._user_connections:
            return

        await self._broadcast(self._user_connections[user_id], data)

    async def _broadcast(self, connections: Set[WebSocket], data: dict) -> None:
        """Broadcast message to a set of connections."""
        disconnected = set()

        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(data)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                disconnected.add(websocket)

        # Clean up disconnected
        for ws in disconnected:
            connections.discard(ws)


# Singleton manager
_manager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    """Get WebSocket manager singleton."""
    return _manager


async def broadcast_progress(
    job_id: str,
    progress: float,
    step: str,
    message: str = "",
) -> None:
    """Convenience function to broadcast progress."""
    await _manager.send_progress(job_id, progress, step, message)
