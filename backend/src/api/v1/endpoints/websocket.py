"""
WebSocket Endpoints
Real-time job progress via WebSocket.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.logging import get_logger
from src.core.websocket import get_ws_manager

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for job progress updates.

    Connect to receive real-time updates for a specific job.

    Messages sent:
    - {"type": "progress", "job_id": "...", "progress": 0.5, "step": "generating"}
    - {"type": "completed", "job_id": "...", "result": {...}}
    - {"type": "error", "job_id": "...", "error": "..."}
    """
    manager = get_ws_manager()
    await manager.connect(websocket, job_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to job progress stream",
        })

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Client can send ping to keep alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
        logger.debug(f"WebSocket disconnected for job {job_id}")


@router.websocket("/user/{user_id}")
async def user_notifications_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for user-level notifications.

    Receive updates for all jobs belonging to a user.
    """
    manager = get_ws_manager()
    await manager.connect_user(websocket, user_id)

    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Connected to user notification stream",
        })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)
        logger.debug(f"WebSocket disconnected for user {user_id}")
