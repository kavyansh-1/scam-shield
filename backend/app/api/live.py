import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..agents.orchestrator import LiveSession

router = APIRouter(tags=["live"])


@router.websocket("/ws/live")
async def live(ws: WebSocket, session_id: str = "", user_id: str = ""):
    await ws.accept()
    sess = LiveSession(ws, session_id, user_id)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if isinstance(msg, dict):
                await sess.handle(msg)
    except WebSocketDisconnect:
        pass
    finally:
        sess.close()
