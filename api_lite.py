#!/usr/bin/env python3
"""
Lightweight API Server for Dashboard
=====================================
This version loads faster by deferring heavy imports.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

# Simple JWT-like token (for demo)
SECRET_KEY = "aquawatch-nrw-secret-2026"
TOKENS = {}  # In-memory token store

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
    }
}

def generate_token(username):
    """Generate a simple token"""
    import secrets
    token = secrets.token_hex(32)
    TOKENS[token] = {
        "username": username,
        "expires": datetime.now() + timedelta(hours=24)
    }
    return token

def verify_token(token):
    """Verify token is valid"""
    if token in TOKENS:
        if TOKENS[token]["expires"] > datetime.now():
            return TOKENS[token]["username"]
    return None

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Check user exists
        if username not in USERS:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if USERS[username]["password_hash"] != password_hash:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate token
        token = generate_token(username)
        
        return jsonify({
            "success": True,
            "access_token": token,  # Dashboard expects 'access_token'
            "token": token,         # Keep for backward compatibility
            "user": {
                "username": username,
                "name": USERS[username]["name"],
                "role": USERS[username]["role"]
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in TOKENS:
        del TOKENS[token]
    return jsonify({"success": True})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = verify_token(token)
    
    if not username:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "username": username,
        "name": USERS[username]["name"],
        "role": USERS[username]["role"]
    })

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": "connected",
            "ai_engine": "ready"
        }
    })

@app.route('/api/status', methods=['GET'])
def status():
    """System status"""
    return jsonify({
        "status": "operational",
        "uptime": "99.9%",
        "active_sensors": 24,
        "active_dmas": 8,
        "alerts_today": 3,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Executive dashboard metrics"""
    return jsonify({
        "nrw_percentage": 28.5,
        "nrw_trend": -2.3,
        "total_leaks_detected": 156,
        "leaks_this_month": 12,
        "water_saved_m3": 45000,
        "cost_saved_php": 900000,
        "active_alerts": 3,
        "sensors_online": 24,
        "sensors_total": 26,
        "system_health": 95,
        "ai_accuracy": 87.5,
        "response_time_avg_hours": 2.3,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/dmas', methods=['GET'])
def get_dmas():
    """Get all DMAs"""
    dmas = [
        {
            "id": "DMA-001",
            "name": "Barangay San Antonio",
            "connections": 1250,
            "nrw_percentage": 22.5,
            "status": "normal",
            "pressure": 3.2,
            "flow": 45.0,
            "leaks_active": 0
        },
        {
            "id": "DMA-002", 
            "name": "Barangay Poblacion",
            "connections": 2100,
            "nrw_percentage": 35.2,
            "status": "warning",
            "pressure": 2.8,
            "flow": 78.5,
            "leaks_active": 2
        },
        {
            "id": "DMA-003",
            "name": "Industrial Zone",
            "connections": 450,
            "nrw_percentage": 18.3,
            "status": "normal",
            "pressure": 3.5,
            "flow": 120.0,
            "leaks_active": 0
        },
        {
            "id": "DMA-004",
            "name": "Barangay Rizal",
            "connections": 1800,
            "nrw_percentage": 42.1,
            "status": "critical",
            "pressure": 2.1,
            "flow": 95.0,
            "leaks_active": 3
        }
    ]
    return jsonify(dmas)

@app.route('/api/dmas/<dma_id>', methods=['GET'])
def get_dma(dma_id):
    """Get specific DMA details"""
    return jsonify({
        "id": dma_id,
        "name": f"DMA {dma_id}",
        "connections": 1250,
        "nrw_percentage": 22.5,
        "status": "normal",
        "pressure_current": 3.2,
        "pressure_avg": 3.1,
        "flow_current": 45.0,
        "flow_avg": 42.5,
        "mnf": 8.5,
        "leaks": [],
        "history": [
            {"date": "2026-01-17", "nrw": 23.1},
            {"date": "2026-01-16", "nrw": 22.8},
            {"date": "2026-01-15", "nrw": 24.2}
        ]
    })

@app.route('/api/leaks', methods=['GET'])
def get_leaks():
    """Get detected leaks"""
    leaks = [
        {
            "id": "LEAK-001",
            "dma_id": "DMA-002",
            "location": "Between V-12 and V-15",
            "severity": "high",
            "confidence": 87,
            "estimated_loss_m3h": 15.5,
            "detected_at": "2026-01-18T06:30:00Z",
            "status": "investigating",
            "coordinates": {"lat": 14.5995, "lng": 120.9842}
        },
        {
            "id": "LEAK-002",
            "dma_id": "DMA-004",
            "location": "Near Junction J-08",
            "severity": "critical",
            "confidence": 92,
            "estimated_loss_m3h": 28.0,
            "detected_at": "2026-01-18T02:15:00Z",
            "status": "repair_scheduled",
            "coordinates": {"lat": 14.6012, "lng": 120.9856}
        },
        {
            "id": "LEAK-003",
            "dma_id": "DMA-004",
            "location": "Service connection SC-445",
            "severity": "medium",
            "confidence": 75,
            "estimated_loss_m3h": 5.2,
            "detected_at": "2026-01-17T18:45:00Z",
            "status": "confirmed",
            "coordinates": {"lat": 14.5988, "lng": 120.9830}
        }
    ]
    return jsonify(leaks)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    alerts = [
        {
            "id": "ALERT-001",
            "type": "leak_detected",
            "severity": "high",
            "message": "Potential leak detected in DMA-002",
            "timestamp": "2026-01-18T06:30:00Z",
            "acknowledged": False
        },
        {
            "id": "ALERT-002",
            "type": "pressure_low",
            "severity": "warning",
            "message": "Low pressure warning in DMA-004",
            "timestamp": "2026-01-18T05:15:00Z",
            "acknowledged": True
        },
        {
            "id": "ALERT-003",
            "type": "sensor_offline",
            "severity": "info",
            "message": "Sensor PRESS-004 offline for maintenance",
            "timestamp": "2026-01-18T04:00:00Z",
            "acknowledged": True
        }
    ]
    return jsonify(alerts)

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Get all sensors"""
    sensors = [
        {"id": "PRESS-001", "type": "pressure", "dma": "DMA-001", "value": 3.2, "unit": "bar", "status": "online"},
        {"id": "PRESS-002", "type": "pressure", "dma": "DMA-002", "value": 2.8, "unit": "bar", "status": "online"},
        {"id": "FLOW-001", "type": "flow", "dma": "DMA-001", "value": 45.0, "unit": "m³/h", "status": "online"},
        {"id": "FLOW-002", "type": "flow", "dma": "DMA-002", "value": 78.5, "unit": "m³/h", "status": "online"},
        {"id": "PRESS-003", "type": "pressure", "dma": "DMA-003", "value": 3.5, "unit": "bar", "status": "online"},
        {"id": "PRESS-004", "type": "pressure", "dma": "DMA-004", "value": 2.1, "unit": "bar", "status": "offline"},
    ]
    return jsonify(sensors)

# ============================================================================
# SENSOR DATA INGESTION
# ============================================================================

@app.route('/api/sensor', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from IoT devices"""
    try:
        data = request.get_json()
        
        # Simple anomaly check
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

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   🌊 AQUAWATCH NRW - LITE API                            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Server running at: http://localhost:8000                                ║
║                                                                          ║
║  Demo Credentials:                                                       ║
║    👤 admin / admin123     (Administrator)                               ║
║    👤 operator / operator123 (Field Operator)                            ║
║    👤 viewer / viewer123   (Dashboard Viewer)                            ║
║                                                                          ║
║  Endpoints:                                                              ║
║    POST /api/auth/login   - Login                                        ║
║    GET  /api/health       - Health check                                 ║
║    GET  /api/metrics      - Dashboard metrics                            ║
║    GET  /api/dmas         - List DMAs                                    ║
║    GET  /api/leaks        - Detected leaks                               ║
║    GET  /api/alerts       - Active alerts                                ║
║    GET  /api/sensors      - Sensor status                                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=8000, debug=False)
