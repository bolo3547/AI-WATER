"""
AquaWatch NRW - Vercel Dashboard
Simple HTML-based dashboard for reliable Vercel deployment
"""

from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_cors import CORS
import hashlib
import random
from datetime import datetime
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
# DATA GENERATORS
# =============================================================================

def get_stats():
    return {
        "sensors_online": 241,
        "total_sensors": 247,
        "nrw_percentage": round(random.uniform(18, 28), 1),
        "water_saved": round(random.uniform(1500, 3500), 0),
        "active_alerts": random.randint(3, 12),
        "ai_confidence": round(random.uniform(92, 98), 1),
    }

def get_alerts():
    alerts = [
        {"title": "Pressure Drop Detected", "severity": "critical", "zone": "Zone A - Downtown", "loss": round(random.uniform(100, 500), 1)},
        {"title": "Unusual Flow Pattern", "severity": "warning", "zone": "Zone B - Industrial", "loss": round(random.uniform(20, 100), 1)},
        {"title": "Acoustic Anomaly", "severity": "warning", "zone": "Zone C - Residential", "loss": round(random.uniform(10, 50), 1)},
    ]
    return [a for a in alerts if random.random() < 0.7]

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
                        <p class="text-muted">Water Intelligence Platform</p>
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
                    <p class="text-center text-muted small mb-0">© 2026 AquaWatch NRW</p>
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
    <title>AquaWatch NRW - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #f5f7fa; }
        .stat-card { border-radius: 12px; border: none; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .alert-critical { border-left: 4px solid #dc3545; }
        .alert-warning { border-left: 4px solid #ffc107; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .gauge-container { position: relative; width: 200px; height: 100px; margin: 0 auto; }
        .gauge-value { font-size: 2.5rem; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container-fluid">
            <a class="navbar-brand d-flex align-items-center" href="/">
                <i class="fas fa-water fa-2x text-primary me-2"></i>
                <div>
                    <span class="fw-bold fs-4">AquaWatch NRW</span>
                    <small class="d-block text-muted" style="font-size: 0.7rem;">Water Intelligence Platform</small>
                </div>
            </a>
            <div class="d-flex align-items-center">
                <span class="badge bg-success pulse me-2">LIVE</span>
                <span class="text-muted me-3">{{ time }}</span>
                <a href="/logout" class="btn btn-outline-secondary btn-sm">
                    <i class="fas fa-sign-out-alt me-1"></i>Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <!-- Stats Cards -->
        <div class="row g-4 mb-4">
            <div class="col-md-3">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-broadcast-tower fa-2x text-primary me-3"></i>
                            <div>
                                <h6 class="text-muted mb-1">Active Sensors</h6>
                                <h3 class="mb-0 fw-bold">{{ stats.sensors_online }}/{{ stats.total_sensors }}</h3>
                                <small class="text-muted">{{ stats.total_sensors - stats.sensors_online }} offline</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-tint-slash fa-2x {% if stats.nrw_percentage > 20 %}text-warning{% else %}text-success{% endif %} me-3"></i>
                            <div>
                                <h6 class="text-muted mb-1">NRW Rate</h6>
                                <h3 class="mb-0 fw-bold">{{ stats.nrw_percentage }}%</h3>
                                <small class="text-muted">Target: &lt;20%</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-hand-holding-water fa-2x text-success me-3"></i>
                            <div>
                                <h6 class="text-muted mb-1">Water Saved Today</h6>
                                <h3 class="mb-0 fw-bold">{{ "{:,.0f}".format(stats.water_saved) }} m³</h3>
                                <small class="text-muted">Through leak detection</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-bell fa-2x {% if stats.active_alerts > 5 %}text-danger{% else %}text-warning{% endif %} me-3"></i>
                            <div>
                                <h6 class="text-muted mb-1">Active Alerts</h6>
                                <h3 class="mb-0 fw-bold">{{ stats.active_alerts }}</h3>
                                <small class="text-muted">Requires attention</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row g-4 mb-4">
            <div class="col-md-4">
                <div class="card shadow-sm h-100" style="border-radius: 12px;">
                    <div class="card-body text-center">
                        <h5 class="card-title">NRW Rate Gauge</h5>
                        <div class="gauge-value mt-4 {% if stats.nrw_percentage > 25 %}text-danger{% elif stats.nrw_percentage > 20 %}text-warning{% else %}text-success{% endif %}">
                            {{ stats.nrw_percentage }}%
                        </div>
                        <div class="progress mt-3" style="height: 25px; border-radius: 15px;">
                            <div class="progress-bar {% if stats.nrw_percentage > 25 %}bg-danger{% elif stats.nrw_percentage > 20 %}bg-warning{% else %}bg-success{% endif %}" 
                                 style="width: {{ (stats.nrw_percentage / 50) * 100 }}%"></div>
                        </div>
                        <small class="text-muted mt-2 d-block">Target: Below 20%</small>
                    </div>
                </div>
            </div>
            <div class="col-md-8">
                <div class="card shadow-sm h-100" style="border-radius: 12px;">
                    <div class="card-body">
                        <h5 class="card-title">NRW Trend - Last 30 Days</h5>
                        <canvas id="trendChart" height="150"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alerts and AI Status -->
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white">
                        <i class="fas fa-bell text-danger me-2"></i>
                        <strong>Active Alerts</strong>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        {% for alert in alerts %}
                        <div class="card mb-2 alert-{{ alert.severity }}" style="border-radius: 8px;">
                            <div class="card-body py-2">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <i class="fas fa-exclamation-triangle {% if alert.severity == 'critical' %}text-danger{% else %}text-warning{% endif %} me-2"></i>
                                        <strong>{{ alert.title }}</strong>
                                        <span class="badge {% if alert.severity == 'critical' %}bg-danger{% else %}bg-warning{% endif %} ms-2">{{ alert.severity|upper }}</span>
                                    </div>
                                </div>
                                <small class="text-muted">
                                    <i class="fas fa-map-marker-alt me-1"></i>{{ alert.zone }} | 
                                    <i class="fas fa-tint me-1"></i>Est. Loss: {{ alert.loss }} m³
                                </small>
                            </div>
                        </div>
                        {% endfor %}
                        {% if not alerts %}
                        <p class="text-muted text-center">No active alerts</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm" style="border-radius: 12px;">
                    <div class="card-header bg-white">
                        <i class="fas fa-robot text-primary me-2"></i>
                        <strong>AI System Status</strong>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-brain text-success me-2"></i>Anomaly Detection Model</span>
                                <span class="badge bg-success">Online</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-map-marked-alt text-success me-2"></i>Leak Localization</span>
                                <span class="badge bg-success">Online</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-volume-up text-success me-2"></i>Acoustic Analysis</span>
                                <span class="badge bg-success">Online</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-chart-line text-primary me-2"></i>AI Confidence</span>
                                <span class="badge bg-primary">{{ stats.ai_confidence }}%</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
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
        <p class="text-center text-muted">© 2026 AquaWatch NRW | Powered by AI | <a href="/api/stats">API</a></p>
    </div>

    <script>
        // Trend Chart
        const ctx = document.getElementById('trendChart').getContext('2d');
        const labels = [];
        const data = [];
        for (let i = 29; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            labels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            data.push(28 - (29-i) * 0.3 + (Math.random() - 0.5) * 4);
        }
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'NRW %',
                    data: data,
                    borderColor: '#0066CC',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: 20,
                                yMax: 20,
                                borderColor: '#28A745',
                                borderDash: [5, 5],
                                label: { content: 'Target', enabled: true }
                            }
                        }
                    }
                },
                scales: {
                    y: { min: 0, max: 40 }
                }
            }
        });

        // Auto refresh every 30 seconds
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
        return render_template_string(DASHBOARD_HTML, 
            stats=get_stats(), 
            alerts=get_alerts(),
            time=datetime.now().strftime('%H:%M:%S'))
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

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/alerts')
def api_alerts():
    return jsonify(get_alerts())

# For Vercel
if __name__ == '__main__':
    app.run(debug=True)
