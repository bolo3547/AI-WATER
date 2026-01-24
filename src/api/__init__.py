"""
AquaWatch NRW v3.0 - API Module
===============================

FastAPI and Flask API endpoints for the NRW detection system.

Components:
- integrated_nrw_api.py: Unified NRW API (Flask Blueprint)
- sensor_api.py: Sensor data endpoints
- websocket_api.py: WebSocket real-time events (FastAPI Router)

WebSocket API:
    The WebSocket router must be included in your FastAPI app:
    
    from fastapi import FastAPI
    from src.api import ws_router
    
    app = FastAPI()
    app.include_router(ws_router)
"""

# WebSocket router for FastAPI
from .websocket_api import ws_router

__all__ = [
    "ws_router",
]
