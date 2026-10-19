"""In-memory WebSocket broadcast, keyed by scan_run id. One Cyron backend
process only — move to Redis pub/sub if you run more than one worker."""
import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class ScanEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, scan_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subscribers[scan_id].add(ws)

    async def unsubscribe(self, scan_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subscribers[scan_id].discard(ws)

    async def publish(self, scan_id: str, event: dict) -> None:
        payload = json.dumps(event)
        for ws in list(self._subscribers.get(scan_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                await self.unsubscribe(scan_id, ws)


bus = ScanEventBus()
