"""
AquaWatch NRW - Vercel Serverless API
=====================================
Lightweight API wrapper for Vercel deployment
Serves both API and Dashboard
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime, timedelta
import random

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Dash app
from dashboard import app as dash_app, server as dash_server

app = dash_server  # Use Dash's Flask server
CORS(app)

# =============================================================================
# SIMULATED DATA (Vercel serverless - no persistent state)
# =============================================================================

def generate_sensor_data():
    """Generate realistic sensor data."""
    zones = ["Zone A - Downtown", "Zone B - Industrial", "Zone C - Residential", "Zone D - Commercial"]
    
    sensors = []
    for i in range(12):
        zone = zones[i % len(zones)]
        base_pressure = 45 + random.uniform(-5, 5)
        
        # Simulate some anomalies
        has_anomaly = random.random() < 0.15
        if has_anomaly:
            base_pressure -= random.uniform(5, 15)
        
        sensors.append({
            "sensor_id": f"SENSOR-{i+1:03d}",
            "pipe_id": f"PIPE-{zone.split()[0]}-{i+1:02d}",
            "zone": zone,
            "pressure_psi": round(base_pressure, 2),
            "flow_rate_gpm": round(100 + random.uniform(-20, 20), 2),
            "acoustic_level_db": round(25 + random.uniform(-5, 15), 1),
            "temperature_c": round(22 + random.uniform(-3, 3), 1),
            "battery_level": round(random.uniform(60, 100), 1),
            "signal_strength": round(random.uniform(-70, -40), 1),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "anomaly" if has_anomaly else "normal",
            "anomaly_score": round(random.uniform(0.7, 0.95), 3) if has_anomaly else round(random.uniform(0.1, 0.3), 3)
        })
    
    return sensors


def generate_alerts():
    """Generate active alerts."""
    alert_types = [
        ("Pressure Drop Detected", "critical", "Zone A - Downtown"),
        ("Unusual Flow Pattern", "warning", "Zone B - Industrial"),
        ("Acoustic Anomaly", "warning", "Zone C - Residential"),
        ("Meter Discrepancy", "info", "Zone D - Commercial"),
    ]
    
    alerts = []
    for i, (title, severity, zone) in enumerate(alert_types):
        if random.random() < 0.7:  # 70% chance alert is active
            alerts.append({
                "id": f"ALERT-{1000+i}",
                "title": title,
                "severity": severity,
                "zone": zone,
                "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(5, 120))).isoformat(),
                "acknowledged": random.random() < 0.3,
                "estimated_loss_m3": round(random.uniform(10, 500), 1) if severity == "critical" else round(random.uniform(1, 50), 1)
            })
    
    return alerts


def get_system_stats():
    """Get system-wide statistics."""
    return {
        "total_sensors": 247,
        "sensors_online": 241,
        "sensors_offline": 6,
        "active_alerts": random.randint(3, 12),
        "nrw_percentage": round(random.uniform(18, 28), 1),
        "water_saved_m3_today": round(random.uniform(1500, 3500), 0),
        "leaks_detected_today": random.randint(2, 8),
        "leaks_repaired_today": random.randint(1, 5),
        "system_uptime": "99.7%",
        "ai_confidence": round(random.uniform(92, 98), 1),
        "last_updated": datetime.utcnow().isoformat()
    }


# =============================================================================
# API ROUTES
# =============================================================================

@app.route("/", methods=["GET"])
def home():
    """API Home - Health check and info."""
    return jsonify({
        "service": "AquaWatch NRW API",
        "version": "2.0.0",
        "status": "operational",
        "deployment": "Vercel Serverless",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/api/health",
            "sensors": "/api/sensors",
            "alerts": "/api/alerts",
            "stats": "/api/stats",
            "zones": "/api/zones"
        }
    })


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "ai_engine": "operational",
            "database": "simulated"
        }
    })


@app.route("/api/sensors", methods=["GET"])
@app.route("/api/sensor", methods=["GET"])
def sensors():
    """Get all sensor data."""
    zone = request.args.get("zone")
    data = generate_sensor_data()
    
    if zone:
        data = [s for s in data if zone.lower() in s["zone"].lower()]
    
    return jsonify({
        "sensors": data,
        "count": len(data),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/alerts", methods=["GET"])
def alerts():
    """Get active alerts."""
    severity = request.args.get("severity")
    data = generate_alerts()
    
    if severity:
        data = [a for a in data if a["severity"] == severity]
    
    return jsonify({
        "alerts": data,
        "count": len(data),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/stats", methods=["GET"])
def stats():
    """Get system statistics."""
    return jsonify(get_system_stats())


@app.route("/api/zones", methods=["GET"])
def zones():
    """Get zone information."""
    zone_data = [
        {
            "id": "zone-a",
            "name": "Zone A - Downtown",
            "sensors": 62,
            "nrw_percentage": round(random.uniform(15, 25), 1),
            "status": "normal",
            "priority": "high"
        },
        {
            "id": "zone-b", 
            "name": "Zone B - Industrial",
            "sensors": 48,
            "nrw_percentage": round(random.uniform(20, 35), 1),
            "status": "warning",
            "priority": "critical"
        },
        {
            "id": "zone-c",
            "name": "Zone C - Residential",
            "sensors": 85,
            "nrw_percentage": round(random.uniform(12, 22), 1),
            "status": "normal",
            "priority": "medium"
        },
        {
            "id": "zone-d",
            "name": "Zone D - Commercial",
            "sensors": 52,
            "nrw_percentage": round(random.uniform(18, 28), 1),
            "status": "normal",
            "priority": "medium"
        }
    ]
    return jsonify({
        "zones": zone_data,
        "count": len(zone_data)
    })


@app.route("/api/history", methods=["GET"])
def history():
    """Get sensor history data."""
    limit = int(request.args.get("limit", 100))
    pipe_id = request.args.get("pipe_id")
    
    history_data = []
    for i in range(min(limit, 500)):
        timestamp = datetime.utcnow() - timedelta(minutes=i*5)
        history_data.append({
            "timestamp": timestamp.isoformat(),
            "pipe_id": pipe_id or f"PIPE-Zone-A-{(i % 10) + 1:02d}",
            "pressure_psi": round(45 + random.uniform(-3, 3) + (0.5 * (i % 24)), 2),
            "flow_rate_gpm": round(100 + random.uniform(-10, 10), 2),
            "acoustic_level_db": round(25 + random.uniform(-2, 2), 1)
        })
    
    return jsonify({
        "history": history_data,
        "count": len(history_data)
    })


@app.route("/api/analytics/nrw", methods=["GET"])
def nrw_analytics():
    """Get NRW analytics data."""
    days = int(request.args.get("days", 30))
    
    daily_data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
        daily_data.append({
            "date": date,
            "nrw_percentage": round(22 + random.uniform(-5, 5) - (i * 0.1), 1),
            "water_input_m3": round(50000 + random.uniform(-5000, 5000), 0),
            "water_billed_m3": round(40000 + random.uniform(-4000, 4000), 0),
            "leaks_detected": random.randint(1, 8),
            "leaks_repaired": random.randint(0, 5)
        })
    
    return jsonify({
        "analytics": daily_data,
        "period_days": days,
        "trend": "improving" if random.random() > 0.3 else "stable"
    })


# Vercel WSGI handler - expose app directly
# Vercel automatically uses the Flask app object

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
