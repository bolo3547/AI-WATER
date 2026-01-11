"""
AquaWatch Admin Dashboard
=========================
Admin panel to:
- Register new ESP sensor devices
- Generate configuration codes for ESP
- Monitor all connected devices
- View real-time water flow data
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import uuid
import requests
import hashlib
import time

# =============================================================================
# APP INITIALIZATION
# =============================================================================

# Cache buster for CSS
CACHE_BUSTER = str(int(time.time()))

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        f"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap&v={CACHE_BUSTER}",
        f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css?v={CACHE_BUSTER}",
    ],
    suppress_callback_exceptions=True,
    title="AquaWatch Admin",
    update_title=None,
)

# =============================================================================
# AUTHENTICATION
# =============================================================================

# Default admin credentials (change these!)
ADMIN_USERS = {
    "admin": hashlib.sha256("aquawatch2024".encode()).hexdigest(),
    "denuel": hashlib.sha256("password123".encode()).hexdigest(),
}

def verify_login(username, password):
    """Verify username and password."""
    if username in ADMIN_USERS:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return ADMIN_USERS[username] == password_hash
    return False

# =============================================================================
# DATA STORAGE
# =============================================================================

DEVICES_FILE = os.path.join(os.path.dirname(__file__), "..", "api", "devices.json")
API_URL = "http://127.0.0.1:5000"

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f:
            return json.load(f)
    return {"devices": []}

def save_devices(data):
    os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
    with open(DEVICES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_device_code():
    """Generate unique device registration code."""
    return f"AQW-{uuid.uuid4().hex[:8].upper()}"

def get_sensor_data():
    """Fetch live sensor data from API."""
    try:
        resp = requests.get(f"{API_URL}/api/sensor", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {}

def get_alerts():
    """Fetch active alerts from API."""
    try:
        resp = requests.get(f"{API_URL}/api/alerts", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

# =============================================================================
# STYLES (External CSS loaded from assets/admin_styles.css)
# =============================================================================

# CSS is loaded from assets/admin_styles.css automatically by Dash
ADMIN_STYLES = ""

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_stats_row():
    devices = load_devices()
    sensor_data = get_sensor_data()
    alerts = get_alerts()
    
    total_devices = len(devices.get("devices", []))
    online_devices = sum(1 for d in devices.get("devices", []) if d.get("status") == "online")
    leak_count = sum(1 for a in alerts if a.get("status") == "leak")
    warning_count = sum(1 for a in alerts if a.get("status") == "warning")
    
    return html.Div([
        html.Div([
            html.Div([html.I(className="fas fa-microchip")], className="icon blue"),
            html.Div(str(total_devices), className="value"),
            html.Div("Registered Devices", className="label"),
        ], className="stat-card"),
        html.Div([
            html.Div([html.I(className="fas fa-wifi")], className="icon green"),
            html.Div(str(online_devices), className="value"),
            html.Div("Online Now", className="label"),
        ], className="stat-card"),
        html.Div([
            html.Div([html.I(className="fas fa-exclamation-triangle")], className="icon yellow"),
            html.Div(str(warning_count), className="value"),
            html.Div("Warnings", className="label"),
        ], className="stat-card"),
        html.Div([
            html.Div([html.I(className="fas fa-tint-slash")], className="icon red"),
            html.Div(str(leak_count), className="value"),
            html.Div("Leaks Detected", className="label"),
        ], className="stat-card"),
    ], className="stats-row", id="stats-row")


def create_device_table():
    devices = load_devices()
    sensor_data = get_sensor_data()
    
    if not devices.get("devices"):
        return html.Div([
            html.I(className="fas fa-microchip"),
            html.P("No devices registered yet"),
            html.P("Click 'Add New Device' to get started", style={"fontSize": "13px"}),
        ], className="empty-state")
    
    rows = []
    for device in devices["devices"]:
        device_id = device.get("device_id", "")
        pipe_id = device.get("pipe_id", "")
        location = device.get("location", "Unknown")
        
        # Get live data for this pipe
        pipe_data = sensor_data.get(pipe_id, {})
        pressure = pipe_data.get("pressure", "-")
        flow = pipe_data.get("flow", "-")
        status = pipe_data.get("status", "offline")
        last_update = pipe_data.get("last_update", "-")
        
        if isinstance(pressure, (int, float)):
            pressure = f"{pressure:.1f} bar"
        if isinstance(flow, (int, float)):
            flow = f"{flow:.1f} L/min"
        
        status_class = {
            "normal": "online",
            "warning": "warning",
            "leak": "leak",
        }.get(status, "offline")
        
        rows.append(html.Tr([
            html.Td(device_id),
            html.Td(pipe_id),
            html.Td(location),
            html.Td(pressure),
            html.Td(flow),
            html.Td(html.Span([
                html.Span(className="status-dot"),
                status.capitalize()
            ], className=f"status-badge {status_class}")),
            html.Td(last_update[:19] if len(str(last_update)) > 10 else last_update),
        ]))
    
    return html.Table([
        html.Thead(html.Tr([
            html.Th("Device ID"),
            html.Th("Pipe ID"),
            html.Th("Location"),
            html.Th("Pressure"),
            html.Th("Flow"),
            html.Th("Status"),
            html.Th("Last Update"),
        ])),
        html.Tbody(rows),
    ], className="device-table")


def create_live_data_cards():
    sensor_data = get_sensor_data()
    
    if not sensor_data:
        return html.Div([
            html.I(className="fas fa-database"),
            html.P("No live data available"),
            html.P("Start the Sensor API and connect ESP devices", style={"fontSize": "13px"}),
        ], className="empty-state")
    
    cards = []
    for pipe_id, data in sensor_data.items():
        pressure = data.get("pressure", 0)
        flow = data.get("flow", 0)
        status = data.get("status", "offline")
        location = data.get("location", "Unknown")
        
        is_alert = status in ("leak", "warning")
        
        cards.append(html.Div([
            html.Div([
                html.Div(pipe_id.replace("_", " "), className="pipe-name"),
                html.Div(location, className="location"),
            ]),
            html.Div([
                html.Div([
                    html.Div(f"{pressure:.1f}" if isinstance(pressure, (int, float)) else "-", className="metric-value"),
                    html.Div("Pressure (bar)", className="metric-label"),
                ], className="metric"),
                html.Div([
                    html.Div(f"{flow:.1f}" if isinstance(flow, (int, float)) else "-", className="metric-value"),
                    html.Div("Flow (L/min)", className="metric-label"),
                ], className="metric"),
            ], className="metrics"),
            html.Div([
                html.Span([
                    html.Span(className="status-dot"),
                    status.capitalize()
                ], className=f"status-badge {status if status in ('warning', 'leak') else 'online' if status == 'normal' else 'offline'}"),
            ], style={"marginTop": "12px"}),
            html.Div([html.Div(className="flow-bar")], className="flow-animation") if flow > 0 else None,
        ], className=f"live-card {'alert' if is_alert else ''}"))
    
    return html.Div(cards, className="live-data-grid")


def generate_esp_code(device_id, pipe_id, location, wifi_ssid="YOUR_WIFI", wifi_pass="YOUR_PASSWORD", server_ip="192.168.1.100"):
    """Generate Arduino code for ESP device."""
    return f'''/*
 * AquaWatch Sensor Node
 * Device: {device_id}
 * Pipe: {pipe_id}
 * Location: {location}
 * Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION =====
const char* WIFI_SSID = "{wifi_ssid}";
const char* WIFI_PASSWORD = "{wifi_pass}";
const char* SERVER_IP = "{server_ip}";
const int SERVER_PORT = 5000;
const char* DEVICE_ID = "{device_id}";
const char* PIPE_ID = "{pipe_id}";

// Sensor pins
const int PRESSURE_PIN = 34;
const int FLOW_PIN = 35;

// Send interval (ms)
const unsigned long INTERVAL = 10000;

unsigned long lastSend = 0;
volatile int flowPulses = 0;

void IRAM_ATTR flowISR() {{ flowPulses++; }}

void setup() {{
    Serial.begin(115200);
    pinMode(PRESSURE_PIN, INPUT);
    pinMode(FLOW_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(FLOW_PIN), flowISR, RISING);
    
    Serial.println("\\n=== AquaWatch Sensor ===");
    Serial.printf("Device: %s\\n", DEVICE_ID);
    Serial.printf("Pipe: %s\\n", PIPE_ID);
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {{
        delay(500);
        Serial.print(".");
    }}
    Serial.printf("\\nConnected! IP: %s\\n", WiFi.localIP().toString().c_str());
}}

void loop() {{
    if (millis() - lastSend >= INTERVAL) {{
        lastSend = millis();
        
        // Read pressure (adjust for your sensor)
        int raw = analogRead(PRESSURE_PIN);
        float voltage = raw * (3.3 / 4095.0);
        float pressure = ((voltage - 0.5) / 4.0) * 100.0 * 0.0689476;
        if (pressure < 0) pressure = 0;
        
        // Read flow
        noInterrupts();
        int pulses = flowPulses;
        flowPulses = 0;
        interrupts();
        float flow = (pulses / (INTERVAL / 1000.0)) / 7.5;
        
        // Send to server
        if (WiFi.status() == WL_CONNECTED) {{
            HTTPClient http;
            String url = String("http://") + SERVER_IP + ":" + SERVER_PORT + "/api/sensor";
            http.begin(url);
            http.addHeader("Content-Type", "application/json");
            
            StaticJsonDocument<256> doc;
            doc["pipe_id"] = PIPE_ID;
            doc["device_id"] = DEVICE_ID;
            doc["pressure"] = pressure;
            doc["flow"] = flow;
            
            String json;
            serializeJson(doc, json);
            
            int code = http.POST(json);
            Serial.printf("Sent: P=%.1f bar, F=%.1f L/min -> %d\\n", pressure, flow, code);
            http.end();
        }}
    }}
    delay(100);
}}
'''


# =============================================================================
# MAIN LAYOUT
# =============================================================================

def create_login_page():
    """Create the login page layout."""
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-water"),
            ], style={"fontSize": "48px", "color": "#0ea5e9", "marginBottom": "16px"}),
            html.H2("AquaWatch Admin"),
            html.P("Sign in to manage your devices"),
        ], className="login-logo"),
        
        html.Div(id="login-error"),
        
        html.Div([
            html.Div([
                html.Label("Username", className="form-label"),
                html.Div([
                    html.I(className="fas fa-user"),
                    dcc.Input(
                        id="login-username",
                        type="text",
                        placeholder="Enter username",
                        className="form-input form-control",
                    ),
                ], className="input-icon"),
            ], className="form-group"),
            
            html.Div([
                html.Label("Password", className="form-label"),
                html.Div([
                    html.I(className="fas fa-lock"),
                    dcc.Input(
                        id="login-password",
                        type="password",
                        placeholder="Enter password",
                        className="form-input form-control",
                        n_submit=0,
                    ),
                ], className="input-icon"),
            ], className="form-group"),
            
            dbc.Button([
                html.I(className="fas fa-sign-in-alt"),
                " Sign In"
            ], id="btn-login", className="btn-primary login-btn", n_clicks=0),
        ], className="login-form"),
        
        html.Div([
            html.P("Default: admin / aquawatch2024"),
        ], className="login-footer"),
    ], className="login-box")


def create_admin_panel(username):
    """Create the main admin panel after login."""
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.I(className="fas fa-water", style={"fontSize": "28px", "color": "#0ea5e9"}),
                html.Div([
                    html.H1("AquaWatch Admin"),
                    html.Span("Device Management", className="badge"),
                ]),
            ], className="admin-title"),
            html.Div([
                html.Div([
                    html.I(className="fas fa-user-circle"),
                    html.Span(username, style={"fontWeight": "500"}),
                ], className="user-badge"),
                html.Span(id="current-time", style={"color": "#64748b", "marginRight": "20px"}),
                dbc.Button([
                    html.I(className="fas fa-plus"),
                    "Add New Device"
                ], id="btn-add-device", className="btn-primary"),
                dbc.Button([
                    html.I(className="fas fa-sign-out-alt"),
                    " Logout"
                ], id="btn-logout", className="btn-logout", style={"marginLeft": "12px"}),
            ], style={"display": "flex", "alignItems": "center"}),
        ], className="admin-header"),
        
        # Stats
        html.Div(id="stats-container", children=create_stats_row()),
        
        # Tabs
        html.Div([
            html.Button("Devices", id="tab-devices", className="tab-btn active", n_clicks=0),
            html.Button("Live Data", id="tab-live", className="tab-btn", n_clicks=0),
            html.Button("Generate Code", id="tab-code", className="tab-btn", n_clicks=0),
        ], className="tabs-nav"),
        
        # Tab Content
        html.Div(id="tab-content"),
        
        # Add Device Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Register New Device")),
            dbc.ModalBody([
                html.Div([
                    html.Label("Device ID", className="form-label"),
                    dcc.Input(id="input-device-id", type="text", placeholder="Auto-generated", 
                              className="form-input form-control", disabled=True),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Label("Pipe ID", className="form-label"),
                    dcc.Dropdown(
                        id="input-pipe-id",
                        options=[
                            {"label": f"Pipe {x}", "value": f"Pipe_{x}"} 
                            for x in ["A1", "A2", "B1", "B2", "K1", "K2", "N1", "N2", "J1", "J2", "C1", "C2", "D1", "D2", "P1", "P2", "G1", "G2", "H1", "H2"]
                        ],
                        placeholder="Select pipe to monitor",
                        style={"backgroundColor": "#1e293b", "color": "#f1f5f9"},
                    ),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Label("Location", className="form-label"),
                    dcc.Input(id="input-location", type="text", placeholder="e.g., Lusaka Central", 
                              className="form-input form-control"),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Label("WiFi SSID", className="form-label"),
                    dcc.Input(id="input-wifi-ssid", type="text", placeholder="Your WiFi network name", 
                              className="form-input form-control"),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Label("WiFi Password", className="form-label"),
                    dcc.Input(id="input-wifi-pass", type="password", placeholder="Your WiFi password", 
                              className="form-input form-control"),
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Label("Server IP (Your PC)", className="form-label"),
                    dcc.Input(id="input-server-ip", type="text", placeholder="e.g., 192.168.1.100", 
                              className="form-input form-control"),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="btn-cancel", className="btn btn-secondary"),
                dbc.Button("Register & Generate Code", id="btn-register", className="btn-primary"),
            ]),
        ], id="modal-add-device", is_open=False, size="lg"),
        
        # Generated Code Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("ESP Arduino Code")),
            dbc.ModalBody([
                html.P("Copy this code and upload it to your ESP32/ESP8266:", style={"color": "#94a3b8"}),
                html.Div(id="generated-code", className="code-block"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Download .ino", id="btn-download", className="btn btn-secondary"),
                dbc.Button("Close", id="btn-close-code", className="btn-primary"),
            ]),
        ], id="modal-code", is_open=False, size="xl"),
        
        # Download component
        dcc.Download(id="download-code"),
        
        # Auto-refresh
        dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0),
        dcc.Store(id="generated-code-store"),
    ], className="admin-container")


app.layout = html.Div([
    dcc.Store(id="auth-store", storage_type="session"),
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content", children=html.Div([create_login_page()], className="login-container")),
])


# =============================================================================
# CALLBACKS
# =============================================================================

# Login callback
@app.callback(
    [Output("page-content", "children"),
     Output("auth-store", "data")],
    [Input("btn-login", "n_clicks"),
     Input("login-password", "n_submit")],
    [State("login-username", "value"),
     State("login-password", "value"),
     State("auth-store", "data")],
    prevent_initial_call=True
)
def handle_login(login_clicks, password_submit, username, password, auth_data):
    if not username or not password:
        return dash.no_update, dash.no_update
    
    if verify_login(username, password):
        return create_admin_panel(username), {"username": username, "logged_in": True}
    else:
        # Show error on failed login
        return html.Div([create_login_page()], className="login-container"), None


# Logout callback
@app.callback(
    [Output("page-content", "children", allow_duplicate=True),
     Output("auth-store", "data", allow_duplicate=True)],
    Input("btn-logout", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks:
        return html.Div([create_login_page()], className="login-container"), None
    return dash.no_update, dash.no_update


@app.callback(
    Output("current-time", "children"),
    Input("refresh-interval", "n_intervals"),
    prevent_initial_call=True
)
def update_time(n):
    return datetime.now().strftime("%A, %d %B %Y  %H:%M:%S")


@app.callback(
    Output("stats-container", "children"),
    Input("refresh-interval", "n_intervals"),
    prevent_initial_call=True
)
def refresh_stats(n):
    return create_stats_row()


@app.callback(
    [Output("tab-devices", "className"),
     Output("tab-live", "className"),
     Output("tab-code", "className"),
     Output("tab-content", "children")],
    [Input("tab-devices", "n_clicks"),
     Input("tab-live", "n_clicks"),
     Input("tab-code", "n_clicks"),
     Input("refresh-interval", "n_intervals")]
)
def switch_tab(devices_clicks, live_clicks, code_clicks, n):
    trigger = ctx.triggered_id
    
    if trigger == "tab-live":
        return "tab-btn", "tab-btn active", "tab-btn", html.Div([
            html.Div([
                html.Div([html.I(className="fas fa-chart-line"), " Live Sensor Data"], className="section-title"),
            ], className="section-header"),
            create_live_data_cards(),
        ], className="section-card")
    
    elif trigger == "tab-code":
        return "tab-btn", "tab-btn", "tab-btn active", html.Div([
            html.Div([
                html.Div([html.I(className="fas fa-code"), " Code Generator"], className="section-title"),
            ], className="section-header"),
            html.P("Select a registered device to generate its Arduino code, or add a new device first.", 
                   style={"color": "#94a3b8", "marginBottom": "20px"}),
            html.Div(id="code-generator-content"),
        ], className="section-card")
    
    else:  # Default to devices tab
        return "tab-btn active", "tab-btn", "tab-btn", html.Div([
            html.Div([
                html.Div([html.I(className="fas fa-microchip"), " Registered Devices"], className="section-title"),
            ], className="section-header"),
            create_device_table(),
        ], className="section-card")


@app.callback(
    [Output("modal-add-device", "is_open"),
     Output("input-device-id", "value")],
    [Input("btn-add-device", "n_clicks"),
     Input("btn-cancel", "n_clicks"),
     Input("btn-register", "n_clicks")],
    [State("modal-add-device", "is_open")]
)
def toggle_modal(add_clicks, cancel_clicks, register_clicks, is_open):
    trigger = ctx.triggered_id
    
    if trigger == "btn-add-device":
        return True, generate_device_code()
    elif trigger in ("btn-cancel", "btn-register"):
        return False, ""
    
    return is_open, ""


@app.callback(
    [Output("modal-code", "is_open"),
     Output("generated-code", "children"),
     Output("generated-code-store", "data")],
    [Input("btn-register", "n_clicks"),
     Input("btn-close-code", "n_clicks")],
    [State("input-device-id", "value"),
     State("input-pipe-id", "value"),
     State("input-location", "value"),
     State("input-wifi-ssid", "value"),
     State("input-wifi-pass", "value"),
     State("input-server-ip", "value")]
)
def register_device(register_clicks, close_clicks, device_id, pipe_id, location, wifi_ssid, wifi_pass, server_ip):
    trigger = ctx.triggered_id
    
    if trigger == "btn-close-code":
        return False, "", None
    
    if trigger == "btn-register" and device_id and pipe_id:
        # Save device
        devices = load_devices()
        devices["devices"].append({
            "device_id": device_id,
            "pipe_id": pipe_id,
            "location": location or "Unknown",
            "status": "offline",
            "created": datetime.now().isoformat(),
        })
        save_devices(devices)
        
        # Generate code
        code = generate_esp_code(
            device_id, 
            pipe_id, 
            location or "Unknown",
            wifi_ssid or "YOUR_WIFI",
            wifi_pass or "YOUR_PASSWORD",
            server_ip or "192.168.1.100"
        )
        
        return True, code, {"code": code, "device_id": device_id}
    
    return False, "", None


@app.callback(
    Output("download-code", "data"),
    Input("btn-download", "n_clicks"),
    State("generated-code-store", "data"),
    prevent_initial_call=True
)
def download_code(n_clicks, stored_data):
    if stored_data:
        return dict(
            content=stored_data["code"],
            filename=f"aquawatch_{stored_data['device_id']}.ino"
        )
    return None


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 AQUAWATCH ADMIN DASHBOARD")
    print("="*60)
    print("\n📊 Admin Panel: http://127.0.0.1:8060")
    print("📡 Make sure Sensor API is running on port 5000")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=False, port=8060)
