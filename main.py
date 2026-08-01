import asyncio
import os
import socket
from pathlib import Path
from datetime import datetime, timezone
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api.v1.api import api_router

tags_metadata = [
    {
        "name": "Simulation",
        "description": "Math-based climate risk modeling and scenario execution.",
    },
    {
        "name": "Climate Copilot",
        "description": "RAG-backed conversational AI assistant for disaster intelligence.",
    },
    {
        "name": "Health",
        "description": "System health and telemetry monitoring.",
    },
]

app = FastAPI(
    title="Bharat Climate Twin (BCT) API",
    version="1.0.0",
    description="Backend Engine for Spatial Climate Digital Twin & Disaster Intelligence",
    openapi_tags=tags_metadata,
)
# Enable CORS for Frontend/Dashboard safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with explicit domains like ["http://localhost:3000"]
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Iterate over a copy of the list to safely handle removals during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws/live-telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            telemetry_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "avg_temp": 32.6,
                "rainfall_24h": 48.7,
                "active_alerts": 3,
                "aqi": 62,
            }
            await websocket.send_json(telemetry_data)
            await asyncio.sleep(5)
    except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
        # Catch expected socket disconnects gracefully
        pass
    finally:
        # Guarantees the connection is removed from active_connections on exit
        manager.disconnect(websocket)


@app.get("/", tags=["Health"])  # or tags=["Core"]
def read_root():
    return {
        "message": "Welcome to Bharat Climate Twin (BCT) API Engine",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/dashboard", tags=["Health"])
def dashboard_page():
    dashboard_file = Path(__file__).resolve().parent / "dashboard.html"
    return FileResponse(dashboard_file)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "Bharat Climate Twin (BCT) API Engine",
    }


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def run_dashboard_server() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    preferred_port = int(os.environ.get("PORT", "8000"))
    port_candidates = [preferred_port] + list(range(preferred_port + 1, preferred_port + 6))

    selected_port = None
    for port in port_candidates:
        if _port_is_free(host, port):
            selected_port = port
            break

    if selected_port is None:
        raise RuntimeError("No free dashboard port available.")

    uvicorn.run(app, host=host, port=selected_port)


if __name__ == "__main__":
    run_dashboard_server()