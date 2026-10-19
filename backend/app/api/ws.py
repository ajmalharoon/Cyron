from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import bus

router = APIRouter(tags=["ws"])


@router.websocket("/ws/scans/{scan_id}")
async def scan_events(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    await bus.subscribe(scan_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # client doesn't send anything meaningful; just keep the socket open
    except WebSocketDisconnect:
        pass
    finally:
        await bus.unsubscribe(scan_id, websocket)
