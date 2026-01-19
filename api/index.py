"""
AquaWatch NRW - Vercel Serverless API
=====================================
This provides API endpoints for the Next.js dashboard when deployed to Vercel.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import hashlib
import secrets
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
CORS(app)

# In-memory storage (resets on cold start - use Redis/DB for production)
TOKENS = {}

# Demo users
USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "System Administrator"
    },
    "operator": {
        "password_hash": hashlib.sha256("operator123".encode()).hexdigest(),
        "role": "operator",
        "name": "Field Operator"
    },
    "viewer": {
        "password_hash": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": "viewer",
        "name": "Dashboard Viewer"
    },
    "denuel": {
        "password_hash": hashlib.sha256("Water@Admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Denuel Admin"
    }
}

def generate_token(username):
    token = secrets.token_hex(32)
    TOKENS[token] = {"username": username, "expires": datetime.now() + timedelta(hours=24)}
    return token

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        if username not in USERS:
            return jsonify({"error": "Invalid credentials"}), 401
        
        if USERS[username]["password_hash"] != hashlib.sha256(password.encode()).hexdigest():
            return jsonify({"error": "Invalid credentials"}), 401
        
        token = generate_token(username)
        return jsonify({
            "success": True,
            "access_token": token,
            "token": token,
            "user": {
                "username": username,
                "name": USERS[username]["name"],
                "role": USERS[username]["role"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in TOKENS and TOKENS[token]["expires"] > datetime.now():
        username = TOKENS[token]["username"]
        return jsonify({
            "username": username,
            "name": USERS[username]["name"],
            "role": USERS[username]["role"]
        })
    return jsonify({"error": "Not authenticated"}), 401

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": "vercel"
    })

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "operational",
        "uptime": "99.9%",
        "active_sensors": 24 + random.randint(-2, 2),
        "active_dmas": 8,
        "alerts_today": random.randint(2, 5),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/metrics', methods=['GET'])
def metrics():
    return jsonify({
        "nrw_percentage": round(28.5 + random.uniform(-3, 3), 1),
        "nrw_trend": round(-2.3 + random.uniform(-1, 1), 1),
        "total_leaks_detected": 156 + random.randint(0, 5),
        "leaks_this_month": 12 + random.randint(-2, 2),
        "water_saved_m3": 45000 + random.randint(-1000, 1000),
        "cost_saved_php": 900000 + random.randint(-50000, 50000),
        "active_alerts": random.randint(2, 5),
        "sensors_online": 24 + random.randint(-2, 0),
        "sensors_total": 26,
        "system_health": random.randint(93, 98),
        "ai_accuracy": round(87.5 + random.uniform(-2, 2), 1),
        "response_time_avg_hours": round(2.3 + random.uniform(-0.5, 0.5), 1),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/dmas', methods=['GET'])
def get_dmas():
    dmas = [
        {"id": "DMA-001", "name": "Barangay San Antonio", "connections": 1250, 
         "nrw_percentage": round(22.5 + random.uniform(-2, 2), 1), "status": "normal",
         "pressure": round(3.2 + random.uniform(-0.2, 0.2), 1), "flow": round(45 + random.uniform(-5, 5), 0),
         "leaks_active": 0, "lat": 14.5995, "lng": 120.9842},
        {"id": "DMA-002", "name": "Barangay Poblacion", "connections": 2100,
         "nrw_percentage": round(35.2 + random.uniform(-2, 2), 1), "status": "warning",
         "pressure": round(2.8 + random.uniform(-0.2, 0.2), 1), "flow": round(78.5 + random.uniform(-5, 5), 0),
         "leaks_active": 2, "lat": 14.6012, "lng": 120.9856},
        {"id": "DMA-003", "name": "Industrial Zone", "connections": 450,
         "nrw_percentage": round(18.3 + random.uniform(-2, 2), 1), "status": "normal",
         "pressure": round(3.5 + random.uniform(-0.2, 0.2), 1), "flow": round(120 + random.uniform(-10, 10), 0),
         "leaks_active": 0, "lat": 14.5950, "lng": 120.9900},
        {"id": "DMA-004", "name": "Barangay Rizal", "connections": 1800,
         "nrw_percentage": round(42.1 + random.uniform(-2, 2), 1), "status": "critical",
         "pressure": round(2.1 + random.uniform(-0.2, 0.2), 1), "flow": round(95 + random.uniform(-5, 5), 0),
         "leaks_active": 3, "lat": 14.5988, "lng": 120.9830},
        {"id": "DMA-005", "name": "Barangay Mabini", "connections": 980,
         "nrw_percentage": round(25.8 + random.uniform(-2, 2), 1), "status": "normal",
         "pressure": round(3.0 + random.uniform(-0.2, 0.2), 1), "flow": round(55 + random.uniform(-5, 5), 0),
         "leaks_active": 1, "lat": 14.6050, "lng": 120.9880},
    ]
    return jsonify(dmas)

@app.route('/api/dmas/<dma_id>', methods=['GET'])
def get_dma(dma_id):
    return jsonify({
        "id": dma_id,
        "name": f"DMA {dma_id}",
        "connections": 1250,
        "nrw_percentage": round(22.5 + random.uniform(-2, 2), 1),
        "status": "normal",
        "pressure_current": round(3.2 + random.uniform(-0.2, 0.2), 1),
        "flow_current": round(45 + random.uniform(-5, 5), 0),
        "mnf": round(8.5 + random.uniform(-1, 1), 1),
        "history": [
            {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
             "nrw": round(22 + random.uniform(-3, 3), 1)} for i in range(7)
        ]
    })

@app.route('/api/leaks', methods=['GET'])
def get_leaks():
    leaks = [
        {"id": "LEAK-001", "dma_id": "DMA-002", "location": "Between V-12 and V-15",
         "severity": "high", "confidence": 87, "estimated_loss_m3h": 15.5,
         "detected_at": (datetime.now() - timedelta(hours=2)).isoformat(),
         "status": "investigating", "coordinates": {"lat": 14.5995, "lng": 120.9842}},
        {"id": "LEAK-002", "dma_id": "DMA-004", "location": "Near Junction J-08",
         "severity": "critical", "confidence": 92, "estimated_loss_m3h": 28.0,
         "detected_at": (datetime.now() - timedelta(hours=6)).isoformat(),
         "status": "repair_scheduled", "coordinates": {"lat": 14.6012, "lng": 120.9856}},
        {"id": "LEAK-003", "dma_id": "DMA-004", "location": "Service connection SC-445",
         "severity": "medium", "confidence": 75, "estimated_loss_m3h": 5.2,
         "detected_at": (datetime.now() - timedelta(hours=14)).isoformat(),
         "status": "confirmed", "coordinates": {"lat": 14.5988, "lng": 120.9830}},
    ]
    return jsonify(leaks)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = [
        {"id": "ALERT-001", "type": "leak_detected", "severity": "high",
         "message": "Potential leak detected in DMA-002", 
         "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(), "acknowledged": False},
        {"id": "ALERT-002", "type": "pressure_low", "severity": "warning",
         "message": "Low pressure warning in DMA-004",
         "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(), "acknowledged": True},
        {"id": "ALERT-003", "type": "sensor_offline", "severity": "info",
         "message": "Sensor PRESS-004 offline for maintenance",
         "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(), "acknowledged": True},
    ]
    return jsonify(alerts)

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    sensors = []
    for i in range(1, 27):
        dma = f"DMA-00{(i % 5) + 1}"
        sensor_type = "pressure" if i % 2 == 0 else "flow"
        value = round(3.0 + random.uniform(-0.5, 0.5), 1) if sensor_type == "pressure" else round(50 + random.uniform(-10, 10), 0)
        sensors.append({
            "id": f"{'PRESS' if sensor_type == 'pressure' else 'FLOW'}-{i:03d}",
            "type": sensor_type,
            "dma": dma,
            "value": value,
            "unit": "bar" if sensor_type == "pressure" else "m³/h",
            "status": "offline" if random.random() < 0.08 else "online",
            "battery": random.randint(60, 100),
            "last_reading": (datetime.now() - timedelta(minutes=random.randint(1, 15))).isoformat()
        })
    return jsonify(sensors)

@app.route('/api/sensor', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json() or {}
        pressure = data.get('pressure', 3.0)
        anomaly = pressure < 2.0 or pressure > 4.5
        return jsonify({
            "status": "received",
            "sensor_id": data.get('sensor_id'),
            "anomaly_detected": anomaly,
            "leak_probability": 0.85 if anomaly else 0.1,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Catch-all route
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({"message": "AquaWatch NRW API", "path": path, "status": "ok"})

# For local testing
if __name__ == '__main__':
    print("Running locally on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
