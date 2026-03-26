from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import Set
from simulator import set_broadcast

router = APIRouter()

class WSManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except:
                dead.add(ws)
        for ws in dead:
            self.active.discard(ws)

manager = WSManager()
set_broadcast(manager.broadcast)

@router.websocket("/live")
async def ws_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)
