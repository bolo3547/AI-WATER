"""
AquaWatch NRW - Enhanced Multi-Town Dashboard
Dynamic water monitoring across multiple locations
"""

from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_cors import CORS
import hashlib
import random
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aquawatch-secret-key-2026')
CORS(app)

# =============================================================================
# AUTHENTICATION
# =============================================================================

ADMIN_USERS = {
    "admin": hashlib.sha256("AquaWatch@2026".encode()).hexdigest(),
    "denuel": hashlib.sha256("Water@Admin123".encode()).hexdigest(),
}

def verify_login(username, password):
    if username in ADMIN_USERS:
        return ADMIN_USERS[username] == hashlib.sha256(password.encode()).hexdigest()
    return False

# =============================================================================
# TOWNS DATA - Multiple Locations
# =============================================================================

TOWNS = {
    "lusaka": {"name": "Lusaka", "region": "Central", "population": 2500000, "lat": -15.3875, "lng": 28.3228},
    "ndola": {"name": "Ndola", "region": "Copperbelt", "population": 500000, "lat": -12.9587, "lng": 28.6366},
    "kitwe": {"name": "Kitwe", "region": "Copperbelt", "population": 450000, "lat": -12.8024, "lng": 28.2132},
    "livingstone": {"name": "Livingstone", "region": "Southern", "population": 180000, "lat": -17.8419, "lng": 25.8544},
    "chipata": {"name": "Chipata", "region": "Eastern", "population": 120000, "lat": -13.6333, "lng": 32.6500},
    "kabwe": {"name": "Kabwe", "region": "Central", "population": 250000, "lat": -14.4469, "lng": 28.4464},
    "chingola": {"name": "Chingola", "region": "Copperbelt", "population": 200000, "lat": -12.5297, "lng": 27.8511},
    "mufulira": {"name": "Mufulira", "region": "Copperbelt", "population": 160000, "lat": -12.5494, "lng": 28.2403},
    "solwezi": {"name": "Solwezi", "region": "North-Western", "population": 100000, "lat": -12.1667, "lng": 26.3833},
    "kasama": {"name": "Kasama", "region": "Northern", "population": 90000, "lat": -10.2167, "lng": 31.1833},
}

def get_town_data(town_id):
    """Generate dynamic data for a specific town."""
    town = TOWNS.get(town_id, TOWNS["lusaka"])
    
    # Generate realistic variations based on town
    base_nrw = 20 + hash(town_id) % 15
    
    # Simulate some towns having issues
    has_critical = random.random() < 0.15
    has_warning = random.random() < 0.3
    
    status = "critical" if has_critical else "warning" if has_warning else "normal"
    
    sensors_total = int(town["population"] / 10000) + random.randint(5, 20)
    sensors_offline = random.randint(0, 3) if status == "normal" else random.randint(3, 8)
    
    nrw = base_nrw + random.uniform(-3, 3)
    if has_critical:
        nrw += random.uniform(5, 15)
    elif has_warning:
        nrw += random.uniform(2, 7)
    
    return {
        "id": town_id,
        "name": town["name"],
        "region": town["region"],
        "population": town["population"],
        "lat": town["lat"],
        "lng": town["lng"],
        "status": status,
        "sensors_online": sensors_total - sensors_offline,
        "sensors_total": sensors_total,
        "nrw_percentage": round(min(nrw, 50), 1),
        "water_saved_today": round(random.uniform(50, 500) * (town["population"] / 100000), 0),
        "active_alerts": random.randint(5, 15) if has_critical else random.randint(1, 5) if has_warning else random.randint(0, 2),
        "pressure_avg": round(45 + random.uniform(-10, 10), 1),
        "flow_rate": round(100 + random.uniform(-30, 30), 1),
        "last_updated": datetime.now().strftime('%H:%M:%S'),
    }

def get_all_towns_summary():
    """Get summary data for all towns."""
    return [get_town_data(town_id) for town_id in TOWNS.keys()]

def get_town_alerts(town_id):
    """Get alerts for a specific town."""
    town = TOWNS.get(town_id, TOWNS["lusaka"])
    zones = ["Zone A - Central", "Zone B - Industrial", "Zone C - Residential", "Zone D - Commercial", "Zone E - Suburban"]
    
    alert_templates = [
        ("Pressure Drop Detected", "critical", "Significant pressure drop indicating possible main break"),
        ("Unusual Flow Pattern", "warning", "Abnormal flow detected, possible leak"),
        ("Acoustic Anomaly", "warning", "Unusual acoustic signature detected"),
        ("Meter Discrepancy", "info", "Flow meter readings inconsistent"),
        ("Night Flow Alert", "warning", "High minimum night flow detected"),
        ("Burst Detection", "critical", "Potential pipe burst identified"),
    ]
    
    alerts = []
    for i, (title, severity, desc) in enumerate(alert_templates):
        if random.random() < 0.4:
            alerts.append({
                "id": f"ALT-{town_id[:3].upper()}-{1000+i}",
                "title": title,
                "severity": severity,
                "description": desc,
                "zone": random.choice(zones),
                "location": f"{town['name']}, {town['region']}",
                "estimated_loss": round(random.uniform(10, 500), 1) if severity == "critical" else round(random.uniform(1, 50), 1),
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(5, 180))).strftime('%H:%M'),
                "acknowledged": random.random() < 0.3,
            })
    
    return sorted(alerts, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["severity"]])

def get_global_stats():
    """Get aggregated stats across all towns."""
    towns_data = get_all_towns_summary()
    
    total_sensors = sum(t["sensors_total"] for t in towns_data)
    online_sensors = sum(t["sensors_online"] for t in towns_data)
    total_alerts = sum(t["active_alerts"] for t in towns_data)
    avg_nrw = sum(t["nrw_percentage"] for t in towns_data) / len(towns_data)
    total_water_saved = sum(t["water_saved_today"] for t in towns_data)
    
    critical_towns = len([t for t in towns_data if t["status"] == "critical"])
    warning_towns = len([t for t in towns_data if t["status"] == "warning"])
    
    return {
        "total_towns": len(TOWNS),
        "critical_towns": critical_towns,
        "warning_towns": warning_towns,
        "normal_towns": len(TOWNS) - critical_towns - warning_towns,
        "total_sensors": total_sensors,
        "sensors_online": online_sensors,
        "total_alerts": total_alerts,
        "avg_nrw": round(avg_nrw, 1),
        "total_water_saved": round(total_water_saved, 0),
        "ai_confidence": round(random.uniform(92, 98), 1),
    }

# =============================================================================
# HTML TEMPLATES
# =============================================================================

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaWatch NRW - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .login-card { max-width: 400px; margin: 100px auto; }
        .logo { color: #0066CC; }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-card">
            <div class="card shadow-lg border-0" style="border-radius: 15px;">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-water fa-4x logo mb-3"></i>
                        <h2 class="fw-bold">AquaWatch NRW</h2>
                        <p class="text-muted">Multi-Town Water Intelligence</p>
                    </div>
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    <form method="POST" action="/login">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Username</label>
                            <input type="text" name="username" class="form-control form-control-lg" placeholder="Enter username" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Password</label>
                            <input type="password" name="password" class="form-control form-control-lg" placeholder="Enter password" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg w-100">
                            <i class="fas fa-sign-in-alt me-2"></i>Login
                        </button>
                    </form>
                    <hr class="my-4">
                    <p class="text-center text-muted small mb-0">© 2026 AquaWatch NRW - Zambia</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaWatch NRW - National Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { background-color: #f5f7fa; }
        .stat-card { border-radius: 12px; border: none; transition: all 0.3s; cursor: pointer; }
        .stat-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; }
        .town-card { border-radius: 12px; border: none; transition: all 0.3s; cursor: pointer; }
        .town-card:hover { transform: scale(1.02); }
        .town-card.critical { border-left: 5px solid #dc3545; }
        .town-card.warning { border-left: 5px solid #ffc107; }
        .town-card.normal { border-left: 5px solid #28a745; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .status-dot.critical { background: #dc3545; animation: blink 1s infinite; }
        .status-dot.warning { background: #ffc107; }
        .status-dot.normal { background: #28a745; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        #map { height: 400px; border-radius: 12px; }
        .alert-item { border-radius: 8px; margin-bottom: 8px; }
        .alert-critical { border-left: 4px solid #dc3545; background: #fff5f5; }
        .alert-warning { border-left: 4px solid #ffc107; background: #fffbf0; }
        .alert-info { border-left: 4px solid #17a2b8; background: #f0f9ff; }
        .region-badge { font-size: 0.7rem; }
        .nav-pills .nav-link.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="container-fluid">
            <a class="navbar-brand d-flex align-items-center" href="/">
                <i class="fas fa-water fa-2x me-2"></i>
                <div>
                    <span class="fw-bold fs-4">AquaWatch NRW</span>
                    <small class="d-block" style="font-size: 0.7rem; opacity: 0.8;">National Water Intelligence - Zambia</small>
                </div>
            </a>
            <div class="d-flex align-items-center">
                <span class="badge bg-success pulse me-2">LIVE</span>
                <span class="text-white me-3" id="current-time">{{ time }}</span>
                <span class="text-white me-3"><i class="fas fa-user me-1"></i>{{ user }}</span>
                <a href="/logout" class="btn btn-outline-light btn-sm">
                    <i class="fas fa-sign-out-alt me-1"></i>Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <!-- Global Stats -->
        <div class="row g-3 mb-4">
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-city fa-2x text-primary mb-2"></i>
                        <h3 class="mb-0 fw-bold">{{ stats.total_towns }}</h3>
                        <small class="text-muted">Towns Monitored</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-exclamation-circle fa-2x text-danger mb-2"></i>
                        <h3 class="mb-0 fw-bold text-danger">{{ stats.critical_towns }}</h3>
                        <small class="text-muted">Critical Issues</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-broadcast-tower fa-2x text-info mb-2"></i>
                        <h3 class="mb-0 fw-bold">{{ stats.sensors_online }}/{{ stats.total_sensors }}</h3>
                        <small class="text-muted">Sensors Online</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-tint-slash fa-2x {% if stats.avg_nrw > 25 %}text-danger{% elif stats.avg_nrw > 20 %}text-warning{% else %}text-success{% endif %} mb-2"></i>
                        <h3 class="mb-0 fw-bold">{{ stats.avg_nrw }}%</h3>
                        <small class="text-muted">Avg NRW Rate</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-hand-holding-water fa-2x text-success mb-2"></i>
                        <h3 class="mb-0 fw-bold">{{ "{:,.0f}".format(stats.total_water_saved) }}</h3>
                        <small class="text-muted">m³ Saved Today</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card shadow-sm h-100 text-center">
                    <div class="card-body py-3">
                        <i class="fas fa-bell fa-2x text-warning mb-2"></i>
                        <h3 class="mb-0 fw-bold">{{ stats.total_alerts }}</h3>
                        <small class="text-muted">Active Alerts</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="row g-4">
            <!-- Map -->
            <div class="col-lg-8">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-map-marked-alt text-primary me-2"></i>
                            <strong>National Water Network Map</strong>
                        </div>
                        <div>
                            <span class="badge bg-danger me-1"><span class="status-dot critical me-1"></span> Critical</span>
                            <span class="badge bg-warning text-dark me-1"><span class="status-dot warning me-1"></span> Warning</span>
                            <span class="badge bg-success"><span class="status-dot normal me-1"></span> Normal</span>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <div id="map"></div>
                    </div>
                </div>
            </div>

            <!-- Town List -->
            <div class="col-lg-4">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white">
                        <i class="fas fa-list text-primary me-2"></i>
                        <strong>Towns Status</strong>
                    </div>
                    <div class="card-body p-2" style="max-height: 400px; overflow-y: auto;">
                        {% for town in towns %}
                        <div class="card town-card {{ town.status }} shadow-sm mb-2" onclick="showTownDetails('{{ town.id }}')">
                            <div class="card-body py-2 px-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <span class="status-dot {{ town.status }} me-2"></span>
                                        <strong>{{ town.name }}</strong>
                                        <span class="badge bg-secondary region-badge ms-1">{{ town.region }}</span>
                                    </div>
                                    <div class="text-end">
                                        <span class="{% if town.nrw_percentage > 25 %}text-danger{% elif town.nrw_percentage > 20 %}text-warning{% else %}text-success{% endif %} fw-bold">{{ town.nrw_percentage }}%</span>
                                        <small class="d-block text-muted">NRW</small>
                                    </div>
                                </div>
                                <div class="d-flex justify-content-between mt-1">
                                    <small class="text-muted"><i class="fas fa-broadcast-tower me-1"></i>{{ town.sensors_online }}/{{ town.sensors_total }}</small>
                                    <small class="text-muted"><i class="fas fa-bell me-1"></i>{{ town.active_alerts }} alerts</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Town Details Modal Content -->
        <div class="row g-4 mt-2" id="town-details" style="display: none;">
            <div class="col-12">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-building text-primary me-2"></i>
                            <strong id="detail-town-name">Town Details</strong>
                            <span class="badge ms-2" id="detail-status">Status</span>
                        </div>
                        <button class="btn btn-sm btn-outline-secondary" onclick="hideTownDetails()">
                            <i class="fas fa-times"></i> Close
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="row g-3" id="detail-content">
                            <!-- Filled by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alerts Section -->
        <div class="row g-4 mt-2">
            <div class="col-lg-8">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white">
                        <i class="fas fa-bell text-danger me-2"></i>
                        <strong>Critical Alerts Across All Towns</strong>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        {% for alert in critical_alerts %}
                        <div class="alert-item alert-{{ alert.severity }} p-2">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <span class="badge {% if alert.severity == 'critical' %}bg-danger{% elif alert.severity == 'warning' %}bg-warning text-dark{% else %}bg-info{% endif %} me-2">{{ alert.severity|upper }}</span>
                                    <strong>{{ alert.title }}</strong>
                                </div>
                                <small class="text-muted">{{ alert.timestamp }}</small>
                            </div>
                            <small class="text-muted d-block">
                                <i class="fas fa-map-marker-alt me-1"></i>{{ alert.location }} - {{ alert.zone }}
                                | <i class="fas fa-tint me-1"></i>Est. Loss: {{ alert.estimated_loss }} m³
                            </small>
                        </div>
                        {% endfor %}
                        {% if not critical_alerts %}
                        <p class="text-muted text-center mb-0"><i class="fas fa-check-circle text-success me-2"></i>No critical alerts</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white">
                        <i class="fas fa-robot text-primary me-2"></i>
                        <strong>AI System Status</strong>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between px-0">
                                <span><i class="fas fa-brain text-success me-2"></i>Anomaly Detection</span>
                                <span class="badge bg-success">Online</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between px-0">
                                <span><i class="fas fa-map-marked-alt text-success me-2"></i>Leak Localization</span>
                                <span class="badge bg-success">Online</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between px-0">
                                <span><i class="fas fa-chart-line text-primary me-2"></i>AI Confidence</span>
                                <span class="badge bg-primary">{{ stats.ai_confidence }}%</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between px-0">
                                <span><i class="fas fa-server text-success me-2"></i>System Uptime</span>
                                <span class="badge bg-success">99.7%</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <hr class="my-4">
        <p class="text-center text-muted">© 2026 AquaWatch NRW - Zambia | Powered by AI | <a href="/api/towns">API</a></p>
    </div>

    <script>
        // Town data from server
        const townsData = {{ towns_json | safe }};
        
        // Initialize Map
        const map = L.map('map').setView([-14.5, 28.5], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        // Custom markers
        const markers = {};
        townsData.forEach(town => {
            const color = town.status === 'critical' ? '#dc3545' : town.status === 'warning' ? '#ffc107' : '#28a745';
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="background: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            
            const marker = L.marker([town.lat, town.lng], {icon: icon})
                .addTo(map)
                .bindPopup(`
                    <strong>${town.name}</strong><br>
                    <span class="badge bg-${town.status === 'critical' ? 'danger' : town.status === 'warning' ? 'warning' : 'success'}">${town.status.toUpperCase()}</span><br>
                    NRW: ${town.nrw_percentage}%<br>
                    Sensors: ${town.sensors_online}/${town.sensors_total}<br>
                    Alerts: ${town.active_alerts}
                `);
            
            marker.on('click', () => showTownDetails(town.id));
            markers[town.id] = marker;
        });

        // Show town details
        function showTownDetails(townId) {
            fetch(`/api/town/${townId}`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById('town-details').style.display = 'block';
                    document.getElementById('detail-town-name').textContent = data.name + ' - ' + data.region;
                    
                    const statusBadge = document.getElementById('detail-status');
                    statusBadge.textContent = data.status.toUpperCase();
                    statusBadge.className = `badge bg-${data.status === 'critical' ? 'danger' : data.status === 'warning' ? 'warning' : 'success'}`;
                    
                    document.getElementById('detail-content').innerHTML = `
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <i class="fas fa-users fa-2x text-primary mb-2"></i>
                                    <h4>${(data.population/1000).toFixed(0)}K</h4>
                                    <small>Population</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <i class="fas fa-tint-slash fa-2x ${data.nrw_percentage > 25 ? 'text-danger' : data.nrw_percentage > 20 ? 'text-warning' : 'text-success'} mb-2"></i>
                                    <h4>${data.nrw_percentage}%</h4>
                                    <small>NRW Rate</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <i class="fas fa-broadcast-tower fa-2x text-info mb-2"></i>
                                    <h4>${data.sensors_online}/${data.sensors_total}</h4>
                                    <small>Sensors</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <i class="fas fa-bell fa-2x text-warning mb-2"></i>
                                    <h4>${data.active_alerts}</h4>
                                    <small>Active Alerts</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mt-3">
                            <div class="card">
                                <div class="card-body">
                                    <h6><i class="fas fa-tachometer-alt me-2"></i>Pressure</h6>
                                    <div class="progress" style="height: 25px;">
                                        <div class="progress-bar bg-info" style="width: ${(data.pressure_avg/60)*100}%">${data.pressure_avg} PSI</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mt-3">
                            <div class="card">
                                <div class="card-body">
                                    <h6><i class="fas fa-water me-2"></i>Flow Rate</h6>
                                    <div class="progress" style="height: 25px;">
                                        <div class="progress-bar bg-primary" style="width: ${(data.flow_rate/150)*100}%">${data.flow_rate} GPM</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Pan map to town
                    map.setView([data.lat, data.lng], 10);
                    markers[townId].openPopup();
                    
                    document.getElementById('town-details').scrollIntoView({behavior: 'smooth'});
                });
        }

        function hideTownDetails() {
            document.getElementById('town-details').style.display = 'none';
            map.setView([-14.5, 28.5], 6);
        }

        // Update time
        setInterval(() => {
            document.getElementById('current-time').textContent = new Date().toLocaleTimeString();
        }, 1000);

        // Auto refresh data every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    if 'user' in session:
        towns = get_all_towns_summary()
        stats = get_global_stats()
        
        # Get critical alerts from all towns
        critical_alerts = []
        for town in towns:
            alerts = get_town_alerts(town['id'])
            for alert in alerts:
                if alert['severity'] in ['critical', 'warning']:
                    critical_alerts.append(alert)
        
        critical_alerts = sorted(critical_alerts, key=lambda x: {"critical": 0, "warning": 1}[x["severity"]])[:10]
        
        import json
        return render_template_string(DASHBOARD_HTML, 
            towns=towns,
            towns_json=json.dumps(towns),
            stats=stats,
            critical_alerts=critical_alerts,
            time=datetime.now().strftime('%H:%M:%S'),
            user=session.get('user', 'Admin'))
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    if verify_login(username, password):
        session['user'] = username
        return redirect('/')
    
    return render_template_string(LOGIN_HTML, error='Invalid username or password')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# API Endpoints
@app.route('/api/towns')
def api_towns():
    return jsonify(get_all_towns_summary())

@app.route('/api/town/<town_id>')
def api_town(town_id):
    return jsonify(get_town_data(town_id))

@app.route('/api/town/<town_id>/alerts')
def api_town_alerts(town_id):
    return jsonify(get_town_alerts(town_id))

@app.route('/api/stats')
def api_stats():
    return jsonify(get_global_stats())

# For Vercel
if __name__ == '__main__':
    app.run(debug=True)
