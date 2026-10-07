# API router: live WebSocket (stub; see docs/CONTRACT.md)
from fastapi import APIRouter, WebSocket

router = APIRouter(tags=["live"])


@router.websocket("/ws/live")
async def live(ws: WebSocket, session_id: str = "", user_id: str = ""):
    await ws.accept()
    await ws.close(code=1011, reason="not implemented")
