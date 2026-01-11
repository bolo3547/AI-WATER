"""
AquaWatch Sensor API
====================
REST API endpoint for ESP32/ESP8266 devices to send sensor data.
The dashboard reads from this data store.

Endpoints:
  POST /api/sensor   - ESP sends pressure/flow readings
  GET  /api/sensor   - Dashboard fetches latest readings
  GET  /api/pipes    - Get all pipe statuses
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
import threading

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from dashboard

# In-memory data store (replace with database for production)
DATA_FILE = os.path.join(os.path.dirname(__file__), "sensor_data.json")
LOCK = threading.Lock()

# Initialize data structure
def init_data():
    return {
        "pipes": {
            "Pipe_A1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Lusaka Central"},
            "Pipe_A2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Lusaka Central"},
            "Pipe_B1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Lusaka East"},
            "Pipe_B2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Lusaka East"},
            "Pipe_K1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Kitwe Industrial"},
            "Pipe_K2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Kitwe Industrial"},
            "Pipe_N1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Ndola CBD"},
            "Pipe_N2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Ndola CBD"},
            "Pipe_J1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Johannesburg North"},
            "Pipe_J2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Johannesburg North"},
            "Pipe_C1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Cape Town Metro"},
            "Pipe_C2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Cape Town Metro"},
            "Pipe_D1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Durban South"},
            "Pipe_D2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Durban South"},
            "Pipe_P1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Port Elizabeth"},
            "Pipe_P2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Port Elizabeth"},
            "Pipe_G1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Gaborone"},
            "Pipe_G2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Gaborone"},
            "Pipe_H1": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Harare Central"},
            "Pipe_H2": {"pressure": 0, "flow": 0, "status": "normal", "last_update": None, "location": "Harare Central"},
        },
        "history": [],  # Last 100 readings
    }

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return init_data()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Leak detection logic
def detect_status(pressure, flow, prev_pressure=None):
    """
    Simple leak detection based on pressure drop or abnormal flow.
    Returns: 'normal', 'warning', or 'leak'
    """
    # Low pressure = potential leak
    if pressure < 20:
        return "leak"
    if pressure < 30:
        return "warning"
    
    # Sudden pressure drop = potential burst
    if prev_pressure and (prev_pressure - pressure) > 10:
        return "leak"
    if prev_pressure and (prev_pressure - pressure) > 5:
        return "warning"
    
    # High night flow = potential leak (would need time-of-day context)
    if flow > 100:  # Abnormally high
        return "warning"
    
    return "normal"


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():
    """
    ESP sends data here.
    Expected JSON:
    {
        "pipe_id": "Pipe_A1",
        "pressure": 45.2,
        "flow": 12.5,
        "device_id": "ESP32_001"  (optional)
    }
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400
        
        pipe_id = payload.get("pipe_id")
        pressure = payload.get("pressure")
        flow = payload.get("flow", 0)
        device_id = payload.get("device_id", "unknown")
        
        if not pipe_id or pressure is None:
            return jsonify({"error": "Missing pipe_id or pressure"}), 400
        
        with LOCK:
            data = load_data()
            
            # Get previous pressure for leak detection
            prev_pressure = None
            if pipe_id in data["pipes"]:
                prev_pressure = data["pipes"][pipe_id].get("pressure")
            
            # Detect status
            status = detect_status(pressure, flow, prev_pressure)
            
            # Update pipe data
            if pipe_id not in data["pipes"]:
                data["pipes"][pipe_id] = {"location": "Unknown"}
            
            data["pipes"][pipe_id].update({
                "pressure": pressure,
                "flow": flow,
                "status": status,
                "last_update": datetime.now().isoformat(),
                "device_id": device_id,
            })
            
            # Add to history (keep last 1000)
            data["history"].append({
                "pipe_id": pipe_id,
                "pressure": pressure,
                "flow": flow,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            })
            data["history"] = data["history"][-1000:]
            
            save_data(data)
        
        return jsonify({
            "success": True,
            "pipe_id": pipe_id,
            "status": status,
            "message": f"Leak detected on {pipe_id}!" if status == "leak" else "Data received"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sensor", methods=["GET"])
def get_sensor_data():
    """Dashboard fetches latest readings."""
    with LOCK:
        data = load_data()
    return jsonify(data["pipes"])


@app.route("/api/pipes", methods=["GET"])
def get_pipes():
    """Get all pipe statuses grouped by location."""
    with LOCK:
        data = load_data()
    
    # Group by location
    by_location = {}
    for pipe_id, info in data["pipes"].items():
        loc = info.get("location", "Unknown")
        if loc not in by_location:
            by_location[loc] = []
        by_location[loc].append({
            "pipe_id": pipe_id,
            **info
        })
    
    return jsonify(by_location)


@app.route("/api/history", methods=["GET"])
def get_history():
    """Get recent sensor readings history."""
    pipe_id = request.args.get("pipe_id")
    limit = int(request.args.get("limit", 100))
    
    with LOCK:
        data = load_data()
    
    history = data["history"]
    if pipe_id:
        history = [h for h in history if h["pipe_id"] == pipe_id]
    
    return jsonify(history[-limit:])


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Get pipes with leak or warning status."""
    with LOCK:
        data = load_data()
    
    alerts = []
    for pipe_id, info in data["pipes"].items():
        if info.get("status") in ("leak", "warning"):
            alerts.append({
                "pipe_id": pipe_id,
                "status": info["status"],
                "pressure": info.get("pressure"),
                "flow": info.get("flow"),
                "location": info.get("location"),
                "last_update": info.get("last_update"),
            })
    
    # Sort by severity (leak first)
    alerts.sort(key=lambda x: (0 if x["status"] == "leak" else 1))
    return jsonify(alerts)


# =============================================================================
# DEVICE REGISTRATION ENDPOINTS
# =============================================================================

DEVICES_FILE = os.path.join(os.path.dirname(__file__), "devices.json")

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f:
            return json.load(f)
    return {"devices": []}

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Get all registered devices."""
    devices = load_devices()
    
    # Enrich with live status from sensor data
    with LOCK:
        sensor_data = load_data()
    
    for device in devices.get("devices", []):
        pipe_id = device.get("pipe_id")
        if pipe_id and pipe_id in sensor_data.get("pipes", {}):
            pipe_info = sensor_data["pipes"][pipe_id]
            last_update = pipe_info.get("last_update")
            
            # Check if device sent data in last 30 seconds
            if last_update:
                try:
                    last_dt = datetime.fromisoformat(last_update)
                    age = (datetime.now() - last_dt).total_seconds()
                    device["status"] = "online" if age < 30 else "offline"
                    device["pressure"] = pipe_info.get("pressure")
                    device["flow"] = pipe_info.get("flow")
                    device["pipe_status"] = pipe_info.get("status")
                except:
                    device["status"] = "offline"
            else:
                device["status"] = "offline"
        else:
            device["status"] = "offline"
    
    return jsonify(devices)


@app.route("/api/devices", methods=["POST"])
def register_device():
    """Register a new ESP device."""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400
        
        device_id = payload.get("device_id")
        pipe_id = payload.get("pipe_id")
        location = payload.get("location", "Unknown")
        
        if not device_id or not pipe_id:
            return jsonify({"error": "Missing device_id or pipe_id"}), 400
        
        devices = load_devices()
        
        # Check if device already exists
        for d in devices.get("devices", []):
            if d["device_id"] == device_id:
                return jsonify({"error": "Device already registered"}), 409
        
        devices["devices"].append({
            "device_id": device_id,
            "pipe_id": pipe_id,
            "location": location,
            "status": "offline",
            "created": datetime.now().isoformat(),
        })
        save_devices(devices)
        
        # Also update sensor data location
        with LOCK:
            data = load_data()
            if pipe_id not in data["pipes"]:
                data["pipes"][pipe_id] = {"pressure": 0, "flow": 0, "status": "normal", "last_update": None}
            data["pipes"][pipe_id]["location"] = location
            save_data(data)
        
        return jsonify({"success": True, "device_id": device_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/devices/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    """Remove a registered device."""
    devices = load_devices()
    devices["devices"] = [d for d in devices.get("devices", []) if d["device_id"] != device_id]
    save_devices(devices)
    return jsonify({"success": True})


@app.route("/api/test-data", methods=["POST"])
def generate_test_data():
    """Generate fake sensor data for testing (when no ESP connected)."""
    import random
    
    with LOCK:
        data = load_data()
        
        for pipe_id in data["pipes"]:
            # Random pressure 25-50 bar with occasional drops
            pressure = random.uniform(25, 50)
            if random.random() < 0.1:  # 10% chance of low pressure
                pressure = random.uniform(15, 28)
            
            # Random flow 5-30 L/min
            flow = random.uniform(5, 30)
            
            prev_pressure = data["pipes"][pipe_id].get("pressure", pressure)
            status = detect_status(pressure, flow, prev_pressure)
            
            data["pipes"][pipe_id].update({
                "pressure": round(pressure, 1),
                "flow": round(flow, 1),
                "status": status,
                "last_update": datetime.now().isoformat(),
            })
        
        save_data(data)
    
    return jsonify({"success": True, "message": "Test data generated"})


@app.route("/", methods=["GET"])
def index():
    """Health check / info."""
    return jsonify({
        "service": "AquaWatch Sensor API",
        "status": "running",
        "endpoints": {
            "POST /api/sensor": "ESP sends pressure/flow data",
            "GET /api/sensor": "Get all pipe readings",
            "GET /api/pipes": "Get pipes grouped by location",
            "GET /api/history": "Get reading history",
            "GET /api/alerts": "Get leak/warning alerts",
        }
    })


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💧 AQUAWATCH SENSOR API")
    print("="*60)
    print("\n📡 API Endpoint: http://127.0.0.1:5000")
    print("📤 ESP sends POST to: http://<YOUR_PC_IP>:5000/api/sensor")
    print("\nEndpoints:")
    print("  POST /api/sensor  - ESP sends data")
    print("  GET  /api/sensor  - Dashboard reads data")
    print("  GET  /api/pipes   - Pipes grouped by location")
    print("  GET  /api/alerts  - Active leak/warning alerts")
    print("\n" + "="*60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=False)
