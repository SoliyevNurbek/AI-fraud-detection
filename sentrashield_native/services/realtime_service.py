from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from fastapi import WebSocket


@dataclass
class AlertEvent:
    alert_id: str
    severity: str
    status: str
    title: str
    description: str
    risk_score: float
    created_at: str


class AlertStreamManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, event: AlertEvent) -> None:
        payload = json.dumps(asdict(event))
        stale_connections: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_text(payload)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)

    async def heartbeat(self, websocket: WebSocket) -> None:
        await websocket.send_json(
            {
                "type": "heartbeat",
                "time": datetime.utcnow().isoformat(),
                "connections": len(self._connections),
            }
        )


alert_stream = AlertStreamManager()
