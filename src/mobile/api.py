"""
AquaWatch NRW - Mobile App API
==============================

"Tesla app, but for your water utility."

Complete mobile API for:
- Real-time dashboard
- Push notifications
- Remote valve control
- Voice commands
- AR pipe visualization
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
import asyncio
import json
import random

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AquaWatch Mobile API",
    description="Mobile app backend for water network management",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# =============================================================================
# MODELS
# =============================================================================

class DeviceType(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class DeviceRegistration(BaseModel):
    device_id: str
    device_type: DeviceType
    push_token: str
    os_version: str
    app_version: str


class VoiceCommand(BaseModel):
    audio_base64: Optional[str] = None
    text: Optional[str] = None
    language: str = "en"


class ValveCommand(BaseModel):
    valve_id: str
    action: str  # open, close, set_position
    position: Optional[float] = None  # 0-100%
    reason: str = ""


class AlertAcknowledge(BaseModel):
    alert_id: str
    action: str  # acknowledge, dismiss, escalate
    notes: str = ""


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy_m: float


# =============================================================================
# SIMULATED DATA
# =============================================================================

def get_dashboard_data(user_id: str) -> Dict:
    """Get personalized dashboard data."""
    return {
        "summary": {
            "nrw_percentage": 32.4 + random.uniform(-2, 2),
            "nrw_trend": -1.2,
            "sensors_online": 487,
            "sensors_total": 500,
            "active_alerts": 5,
            "critical_alerts": 1,
            "water_saved_today_m3": 1245,
            "cost_saved_today_usd": 623
        },
        "dma_performance": [
            {"dma": "Kabulonga", "nrw": 28.5, "status": "good", "trend": -2.1},
            {"dma": "Chelstone", "nrw": 35.2, "status": "warning", "trend": +0.5},
            {"dma": "Matero", "nrw": 45.8, "status": "critical", "trend": -1.0},
            {"dma": "Roma", "nrw": 22.1, "status": "excellent", "trend": -3.2},
        ],
        "recent_activity": [
            {"time": "2m ago", "event": "Leak detected in DMA_MATERO", "severity": "high"},
            {"time": "15m ago", "event": "Drone inspection complete", "severity": "info"},
            {"time": "1h ago", "event": "Valve V-042 auto-adjusted", "severity": "info"},
            {"time": "2h ago", "event": "Sensor ESP32_0124 battery low", "severity": "low"},
        ],
        "quick_actions": [
            {"id": "view_map", "label": "View Map", "icon": "map"},
            {"id": "dispatch_crew", "label": "Dispatch Crew", "icon": "users"},
            {"id": "run_report", "label": "Run Report", "icon": "chart"},
            {"id": "drone_patrol", "label": "Drone Patrol", "icon": "send"},
        ]
    }


def get_network_map_data(bounds: Dict) -> Dict:
    """Get map data for given bounds."""
    base_lat, base_lon = -15.4167, 28.2833
    
    sensors = []
    for i in range(50):
        sensors.append({
            "id": f"ESP32_{i:04d}",
            "lat": base_lat + random.uniform(-0.05, 0.05),
            "lon": base_lon + random.uniform(-0.05, 0.05),
            "type": random.choice(["flow", "pressure", "acoustic"]),
            "status": random.choice(["online", "online", "online", "warning", "offline"]),
            "last_reading": datetime.now(timezone.utc).isoformat()
        })
    
    pipes = []
    for i in range(20):
        start_lat = base_lat + random.uniform(-0.03, 0.03)
        start_lon = base_lon + random.uniform(-0.03, 0.03)
        pipes.append({
            "id": f"PIPE_{i:03d}",
            "start": [start_lat, start_lon],
            "end": [start_lat + random.uniform(-0.01, 0.01), 
                   start_lon + random.uniform(-0.01, 0.01)],
            "diameter_mm": random.choice([100, 150, 200, 300]),
            "material": random.choice(["PVC", "Ductile Iron", "HDPE"]),
            "condition": random.choice(["good", "good", "fair", "poor"])
        })
    
    leaks = []
    for i in range(3):
        leaks.append({
            "id": f"LEAK_{i:03d}",
            "lat": base_lat + random.uniform(-0.02, 0.02),
            "lon": base_lon + random.uniform(-0.02, 0.02),
            "severity": random.choice(["low", "medium", "high"]),
            "estimated_loss_lph": random.randint(100, 1000),
            "detected_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "sensors": sensors,
        "pipes": pipes,
        "leaks": leaks,
        "dma_boundaries": []  # Would contain GeoJSON polygons
    }


def process_voice_command(command: str) -> Dict:
    """Process natural language voice command."""
    command_lower = command.lower()
    
    # Simple intent detection
    if "status" in command_lower or "how" in command_lower:
        return {
            "intent": "query_status",
            "response": "The network is operating normally. NRW is at 32.4%, "
                       "down 1.2% from yesterday. There are 5 active alerts, "
                       "1 critical in DMA Matero.",
            "action": None
        }
    
    elif "leak" in command_lower:
        return {
            "intent": "query_leaks",
            "response": "There are 3 active leaks. The most critical is in "
                       "Matero with an estimated loss of 850 liters per hour. "
                       "Would you like me to dispatch a crew?",
            "action": {"type": "suggest_dispatch", "leak_id": "LEAK_001"}
        }
    
    elif "drone" in command_lower:
        return {
            "intent": "drone_command",
            "response": "I'll dispatch a drone to investigate. Scout-1 is "
                       "available and will be on site in approximately 8 minutes.",
            "action": {"type": "dispatch_drone", "drone_id": "SCOUT_1"}
        }
    
    elif "close" in command_lower and "valve" in command_lower:
        return {
            "intent": "valve_control",
            "response": "I'll close the nearest valve to isolate the area. "
                       "This will affect approximately 50 connections. Confirm?",
            "action": {"type": "close_valve", "valve_id": "V-042", "requires_confirm": True}
        }
    
    elif "report" in command_lower:
        return {
            "intent": "generate_report",
            "response": "Generating your daily NRW report. It will be ready "
                       "in about 30 seconds and sent to your email.",
            "action": {"type": "generate_report", "report_type": "daily_nrw"}
        }
    
    else:
        return {
            "intent": "unknown",
            "response": "I didn't understand that command. You can ask me about "
                       "network status, leaks, drones, valves, or reports.",
            "action": None
        }


# =============================================================================
# WEBSOCKET CONNECTIONS
# =============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal(self, message: Dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: Dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


# =============================================================================
# API ENDPOINTS
# =============================================================================

# --- Device Management ---

@app.post("/api/mobile/v1/device/register")
async def register_device(device: DeviceRegistration):
    """Register mobile device for push notifications."""
    return {
        "success": True,
        "device_id": device.device_id,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "push_enabled": True
    }


# --- Dashboard ---

@app.get("/api/mobile/v1/dashboard")
async def get_dashboard():
    """Get main dashboard data."""
    return get_dashboard_data("user_123")


@app.get("/api/mobile/v1/dashboard/widget/{widget_id}")
async def get_widget_data(widget_id: str):
    """Get data for specific dashboard widget."""
    widgets = {
        "nrw_gauge": {"value": 32.4, "target": 25.0, "trend": -1.2},
        "alerts_summary": {"critical": 1, "high": 2, "medium": 5, "low": 12},
        "savings_today": {"water_m3": 1245, "cost_usd": 623},
        "sensor_health": {"online": 487, "warning": 8, "offline": 5}
    }
    
    if widget_id not in widgets:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    return widgets[widget_id]


# --- Map ---

@app.get("/api/mobile/v1/map")
async def get_map_data(
    min_lat: float = -15.5,
    max_lat: float = -15.3,
    min_lon: float = 28.2,
    max_lon: float = 28.4
):
    """Get map data for given bounding box."""
    return get_network_map_data({
        "min_lat": min_lat, "max_lat": max_lat,
        "min_lon": min_lon, "max_lon": max_lon
    })


@app.get("/api/mobile/v1/map/sensor/{sensor_id}")
async def get_sensor_detail(sensor_id: str):
    """Get detailed sensor information."""
    return {
        "id": sensor_id,
        "type": "flow_pressure",
        "location": {"lat": -15.4167, "lon": 28.2833},
        "status": "online",
        "battery": 85,
        "last_reading": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "flow_rate_lph": 1250,
            "pressure_bar": 3.2,
            "temperature_c": 24.5
        },
        "history_24h": [
            {"hour": h, "flow": 1200 + random.randint(-200, 200)}
            for h in range(24)
        ]
    }


# --- AR Visualization ---

@app.get("/api/mobile/v1/ar/pipes")
async def get_ar_pipe_data(
    latitude: float,
    longitude: float,
    radius_m: float = 50
):
    """Get pipe data for AR visualization."""
    return {
        "pipes": [
            {
                "id": "PIPE_001",
                "path": [
                    {"lat": latitude - 0.0001, "lon": longitude, "depth_m": 1.2},
                    {"lat": latitude + 0.0001, "lon": longitude, "depth_m": 1.5}
                ],
                "diameter_mm": 200,
                "material": "Ductile Iron",
                "age_years": 15,
                "condition_score": 7.2,
                "flow_direction": "north",
                "current_flow_lph": 1500
            },
            {
                "id": "PIPE_002",
                "path": [
                    {"lat": latitude, "lon": longitude - 0.0001, "depth_m": 0.8},
                    {"lat": latitude, "lon": longitude + 0.0001, "depth_m": 1.0}
                ],
                "diameter_mm": 100,
                "material": "PVC",
                "age_years": 5,
                "condition_score": 9.1,
                "flow_direction": "east",
                "current_flow_lph": 450
            }
        ],
        "valves": [
            {
                "id": "V-042",
                "location": {"lat": latitude, "lon": longitude, "depth_m": 1.0},
                "type": "gate",
                "status": "open",
                "position_pct": 100
            }
        ],
        "sensors": [
            {
                "id": "ESP32_0124",
                "location": {"lat": latitude + 0.00005, "lon": longitude},
                "type": "flow",
                "status": "online"
            }
        ]
    }


# --- Alerts ---

@app.get("/api/mobile/v1/alerts")
async def get_alerts(
    status: str = "active",
    severity: Optional[str] = None,
    limit: int = 20
):
    """Get alerts list."""
    alerts = []
    severities = ["critical", "high", "medium", "low"]
    
    for i in range(min(limit, 20)):
        sev = severity if severity else random.choice(severities)
        alerts.append({
            "id": f"ALERT_{i:05d}",
            "severity": sev,
            "type": random.choice(["leak", "sensor_offline", "pressure_anomaly", "low_battery"]),
            "title": f"Alert {i+1}",
            "description": "Sample alert description",
            "location": {"lat": -15.4167 + random.uniform(-0.02, 0.02),
                        "lon": 28.2833 + random.uniform(-0.02, 0.02)},
            "dma": random.choice(["Kabulonga", "Chelstone", "Matero", "Roma"]),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "acknowledged": False
        })
    
    return {"alerts": alerts, "total": len(alerts)}


@app.post("/api/mobile/v1/alerts/{alert_id}/action")
async def alert_action(alert_id: str, action: AlertAcknowledge):
    """Acknowledge or take action on an alert."""
    return {
        "success": True,
        "alert_id": alert_id,
        "action": action.action,
        "actioned_at": datetime.now(timezone.utc).isoformat()
    }


# --- Voice Commands ---

@app.post("/api/mobile/v1/voice/command")
async def voice_command(command: VoiceCommand):
    """Process voice command."""
    if command.text:
        result = process_voice_command(command.text)
    elif command.audio_base64:
        # Would process audio through speech-to-text
        result = process_voice_command("show me the status")
    else:
        raise HTTPException(status_code=400, detail="No command provided")
    
    return result


# --- Valve Control ---

@app.post("/api/mobile/v1/valves/{valve_id}/command")
async def control_valve(valve_id: str, command: ValveCommand):
    """Send command to valve."""
    return {
        "success": True,
        "valve_id": valve_id,
        "action": command.action,
        "new_position": command.position if command.position else (100 if command.action == "open" else 0),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "estimated_completion": "5 seconds"
    }


@app.get("/api/mobile/v1/valves/{valve_id}/status")
async def get_valve_status(valve_id: str):
    """Get valve status."""
    return {
        "id": valve_id,
        "name": f"Valve {valve_id}",
        "type": "gate",
        "location": {"lat": -15.4167, "lon": 28.2833},
        "status": "online",
        "position_pct": random.randint(0, 100),
        "last_operated": datetime.now(timezone.utc).isoformat(),
        "controllable": True
    }


# --- Drones ---

@app.post("/api/mobile/v1/drones/dispatch")
async def dispatch_drone(
    target_lat: float,
    target_lon: float,
    mission_type: str = "investigation"
):
    """Dispatch drone to location."""
    return {
        "success": True,
        "mission_id": "M00123",
        "drone_id": "SCOUT_1",
        "target": {"lat": target_lat, "lon": target_lon},
        "mission_type": mission_type,
        "eta_minutes": random.randint(5, 15),
        "dispatched_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/mobile/v1/drones")
async def get_drone_fleet():
    """Get drone fleet status."""
    return {
        "drones": [
            {"id": "SCOUT_1", "status": "available", "battery": 95, "location": {"lat": -15.4167, "lon": 28.2833}},
            {"id": "SCOUT_2", "status": "on_mission", "battery": 72, "mission_id": "M00122"},
            {"id": "INSPECTOR_1", "status": "charging", "battery": 45, "location": {"lat": -15.4167, "lon": 28.2833}},
        ],
        "active_missions": 1
    }


# --- Location Updates ---

@app.post("/api/mobile/v1/location/update")
async def update_location(location: LocationUpdate):
    """Update user's location for field crew tracking."""
    return {
        "received": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# --- WebSocket for Real-time Updates ---

@app.websocket("/api/mobile/v1/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time updates."""
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Simulate real-time updates
        while True:
            # Simulate random events
            event_type = random.choice(["sensor_reading", "alert", "drone_update"])
            
            if event_type == "sensor_reading":
                data = {
                    "type": "sensor_reading",
                    "sensor_id": f"ESP32_{random.randint(1, 100):04d}",
                    "flow_rate": 1200 + random.randint(-100, 100),
                    "pressure": 3.0 + random.uniform(-0.5, 0.5),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            elif event_type == "alert":
                data = {
                    "type": "new_alert",
                    "alert_id": f"ALERT_{random.randint(1, 1000):05d}",
                    "severity": random.choice(["low", "medium", "high"]),
                    "title": "New alert detected",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                data = {
                    "type": "drone_update",
                    "drone_id": "SCOUT_1",
                    "status": "on_mission",
                    "location": {
                        "lat": -15.4167 + random.uniform(-0.01, 0.01),
                        "lon": 28.2833 + random.uniform(-0.01, 0.01)
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            await websocket.send_json(data)
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("📱 AQUAWATCH MOBILE API")
    print("=" * 60)
    print("\nStarting server...")
    print("API Docs: http://localhost:8080/docs")
    print("WebSocket: ws://localhost:8080/api/mobile/v1/ws/{user_id}")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
