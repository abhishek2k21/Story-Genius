"""
WebSocket API Route
Real-time notifications endpoint.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.realtime import ws_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = "default_user"):
    """
    WebSocket endpoint for real-time notifications.
    
    Query params:
    - user_id: User ID (from auth token in production)
    
    Sends real-time notifications for:
    - Video generation started/completed/failed
    - Batch processing progress
    - Quality approval
    """
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client (heartbeat, etc.)
            data = await websocket.receive_text()
            
            # Echo back for heartbeat
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected: {user_id}")


@router.get("/ws/stats")
async def get_ws_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Connection stats
    """
    return {
        "active_connections": ws_manager.get_active_connections(),
        "active_users": ws_manager.get_active_users()
    }
