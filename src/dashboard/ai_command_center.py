"""
AquaWatch NRW - Advanced AI Dashboard with Voice Alerts
========================================================

Features:
- Voice announcements for leak detection
- Advanced AI visualization
- Real-time leak localization
- Complete toolset for all roles
- Interactive pipe network map

Default Users:
- admin / admin123 (Full access)
- operator / operator123 (Operations view)
- technician / tech123 (Field view)
"""

import dash
from dash import dcc, html, callback, Input, Output, State, no_update, clientside_callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import secrets
import json
import random

# =============================================================================
# DEFAULT USERS
# =============================================================================

DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "System Administrator",
        "role": "admin",
        "access": ["national", "operations", "field", "ai", "command", "twin", "events", "assets", "benchmark", "customers", "settings"]
    },
    "operator": {
        "password_hash": hashlib.sha256("operator123".encode()).hexdigest(),
        "name": "Control Room Operator",
        "role": "operator",
        "access": ["operations", "field", "ai", "command", "twin", "events", "assets"]
    },
    "technician": {
        "password_hash": hashlib.sha256("tech123".encode()).hexdigest(),
        "name": "Field Technician",
        "role": "technician",
        "access": ["field", "assets", "events"]
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "name": "Demo User",
        "role": "viewer",
        "access": ["national", "operations", "field", "ai", "command", "twin", "events", "assets", "benchmark", "customers"]
    }
}

active_sessions = {}

def verify_password(username: str, password: str) -> Optional[Dict]:
    if username not in DEFAULT_USERS:
        return None
    user = DEFAULT_USERS[username]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == user["password_hash"]:
        return {"username": username, "name": user["name"], "role": user["role"], "access": user["access"]}
    return None

def create_session(user_info: Dict) -> str:
    token = secrets.token_urlsafe(32)
    active_sessions[token] = {**user_info, "created": datetime.now(), "expires": datetime.now() + timedelta(hours=8)}
    return token

def get_session(token: str) -> Optional[Dict]:
    if not token or token not in active_sessions:
        return None
    session = active_sessions[token]
    if datetime.now() > session["expires"]:
        del active_sessions[token]
        return None
    return session


# =============================================================================
# SIMULATED AI ENGINE - Leak Detection
# =============================================================================

class LeakDetectionAI:
    """Simulated AI engine for leak detection with voice alerts."""
    
    # Pipe network data
    PIPE_NETWORK = {
        "PIPE-KIT-001": {"area": "Kitwe Central", "street": "Independence Avenue", "lat": -12.8024, "lon": 28.2132, "diameter": 300, "material": "Steel"},
        "PIPE-KIT-002": {"area": "Kitwe Central", "street": "President Avenue", "lat": -12.8054, "lon": 28.2165, "diameter": 250, "material": "PVC"},
        "PIPE-KIT-003": {"area": "Kitwe North", "street": "Zambia Way", "lat": -12.7924, "lon": 28.2089, "diameter": 200, "material": "Steel"},
        "PIPE-KIT-004": {"area": "Kitwe South", "street": "Industrial Road", "lat": -12.8224, "lon": 28.2232, "diameter": 400, "material": "Cast Iron"},
        "PIPE-NDL-001": {"area": "Ndola East", "street": "Broadway Street", "lat": -12.9684, "lon": 28.6366, "diameter": 300, "material": "Steel"},
        "PIPE-NDL-002": {"area": "Ndola Central", "street": "Buteko Avenue", "lat": -12.9584, "lon": 28.6266, "diameter": 350, "material": "PVC"},
        "PIPE-LSK-001": {"area": "Lusaka CBD", "street": "Cairo Road", "lat": -15.4167, "lon": 28.2833, "diameter": 500, "material": "Steel"},
        "PIPE-LSK-002": {"area": "Lusaka East", "street": "Great East Road", "lat": -15.4067, "lon": 28.3033, "diameter": 400, "material": "Cast Iron"},
    }
    
    @classmethod
    def get_current_alerts(cls) -> List[Dict]:
        """Get current leak alerts with AI analysis."""
        alerts = []
        
        # Generate 2-4 active alerts
        active_pipes = random.sample(list(cls.PIPE_NETWORK.keys()), k=random.randint(2, 4))
        
        for i, pipe_id in enumerate(active_pipes):
            pipe = cls.PIPE_NETWORK[pipe_id]
            severity = random.choice(["critical", "high", "medium"])
            confidence = random.uniform(0.72, 0.98)
            
            # Calculate estimated leak rate based on severity
            leak_rate = {"critical": random.uniform(50, 150), "high": random.uniform(20, 50), "medium": random.uniform(5, 20)}[severity]
            
            alerts.append({
                "alert_id": f"ALT-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                "pipe_id": pipe_id,
                "area": pipe["area"],
                "street": pipe["street"],
                "lat": pipe["lat"],
                "lon": pipe["lon"],
                "severity": severity,
                "confidence": confidence,
                "leak_rate_lpm": leak_rate,
                "estimated_distance_m": random.randint(10, 200),
                "detected_at": datetime.now() - timedelta(minutes=random.randint(5, 120)),
                "pressure_drop": random.uniform(0.3, 1.2),
                "anomaly_score": random.uniform(0.7, 1.0),
                "pipe_diameter": pipe["diameter"],
                "pipe_material": pipe["material"],
                "recommended_action": cls._get_recommendation(severity)
            })
        
        return sorted(alerts, key=lambda x: {"critical": 0, "high": 1, "medium": 2}[x["severity"]])
    
    @classmethod
    def _get_recommendation(cls, severity: str) -> str:
        recommendations = {
            "critical": "IMMEDIATE: Dispatch emergency crew. Consider isolating section.",
            "high": "URGENT: Schedule inspection within 4 hours. Prepare repair equipment.",
            "medium": "NORMAL: Add to daily inspection route. Monitor pressure trends."
        }
        return recommendations.get(severity, "Monitor situation")
    
    @classmethod
    def generate_voice_alert(cls, alert: Dict) -> str:
        """Generate voice alert text for a leak."""
        severity_word = {"critical": "Critical", "high": "High priority", "medium": "Moderate"}[alert["severity"]]
        
        return (
            f"Attention! {severity_word} leak detected. "
            f"Location: {alert['area']}, {alert['street']}. "
            f"Pipe ID: {alert['pipe_id']}. "
            f"Confidence: {alert['confidence']*100:.0f} percent. "
            f"Estimated leak rate: {alert['leak_rate_lpm']:.0f} liters per minute. "
            f"Recommendation: {alert['recommended_action'].split('.')[0]}."
        )
    
    @classmethod
    def get_ai_analysis(cls) -> Dict:
        """Get overall AI analysis summary."""
        return {
            "total_pipes_monitored": len(cls.PIPE_NETWORK),
            "ai_model_version": "AquaWatch AI v2.1",
            "detection_accuracy": 94.2,
            "false_positive_rate": 3.8,
            "last_model_update": "2026-01-10",
            "predictions_today": random.randint(150, 300),
            "anomalies_detected": random.randint(5, 15),
            "leaks_confirmed": random.randint(2, 5)
        }


# =============================================================================
# Initialize Dash App
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

server = app.server
app.title = "AquaWatch NRW - AI Command Center"

COLORS = {
    "primary": "#0d6efd",
    "success": "#198754",
    "warning": "#ffc107", 
    "danger": "#dc3545",
    "info": "#0dcaf0",
    "dark": "#212529",
    "water_blue": "#0077be",
    "water_dark": "#004d80",
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "accent": "#00d9ff"
}


# =============================================================================
# LOGIN PAGE
# =============================================================================

def create_login_page():
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-satellite-dish fa-3x mb-3", style={"color": COLORS["accent"]}),
                                html.H2("AquaWatch NRW", className="mb-1", style={"color": COLORS["accent"]}),
                                html.P("AI-Powered Water Intelligence", className="text-muted mb-4"),
                            ], className="text-center"),
                            
                            dbc.Input(id="login-username", type="text", placeholder="Username", className="mb-3 bg-dark text-white"),
                            dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-3 bg-dark text-white"),
                            html.Div(id="login-error", className="mb-3"),
                            dbc.Button([html.I(className="fas fa-sign-in-alt me-2"), "Access System"],
                                      id="login-button", color="info", className="w-100 mb-3", size="lg"),
                            
                            html.Hr(className="border-secondary"),
                            
                            dbc.Alert([
                                html.Strong("Credentials:"), html.Br(),
                                html.Code("admin / admin123", className="text-info"), " → Full Access", html.Br(),
                                html.Code("operator / operator123", className="text-warning"), " → Operations", html.Br(),
                                html.Code("technician / tech123", className="text-success"), " → Field", html.Br(),
                                html.Code("demo / demo", className="text-light"), " → View Only",
                            ], color="dark", className="mb-0 small border border-secondary"),
                        ])
                    ], className="shadow-lg border-0", style={"backgroundColor": COLORS["bg_card"], "maxWidth": "420px", "margin": "auto"})
                ], width=12, md=6, lg=4)
            ], justify="center", align="center", style={"minHeight": "100vh"})
        ], fluid=True)
    ], style={"background": f"linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['water_dark']} 100%)", "minHeight": "100vh"})


# =============================================================================
# NAVBAR
# =============================================================================

def create_navbar(user_info: Dict):
    access = user_info.get("access", [])
    
    # Main navigation items
    nav_items = []
    
    # Primary nav
    if "national" in access:
        nav_items.append(dbc.NavItem(dbc.NavLink([html.I(className="fas fa-globe me-1"), "National"], href="/dashboard/national", className="text-light")))
    if "command" in access:
        nav_items.append(dbc.NavItem(dbc.NavLink([html.I(className="fas fa-rocket me-1"), "Command"], href="/dashboard/command", className="text-light")))
    if "operations" in access:
        nav_items.append(dbc.NavItem(dbc.NavLink([html.I(className="fas fa-desktop me-1"), "Operations"], href="/dashboard/operations", className="text-light")))
    if "ai" in access:
        nav_items.append(dbc.NavItem(dbc.NavLink([html.I(className="fas fa-brain me-1"), "AI Center"], href="/dashboard/ai", className="text-light")))
    
    # Dropdown for more views
    dropdown_items = []
    if "twin" in access:
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-cube me-2"), "Digital Twin"], href="/dashboard/twin"))
    if "events" in access:
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-calendar-alt me-2"), "Events"], href="/dashboard/events"))
    if "assets" in access:
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-heartbeat me-2"), "Asset Health"], href="/dashboard/assets"))
    if "benchmark" in access:
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-chart-bar me-2"), "Benchmarking"], href="/dashboard/benchmark"))
    if "customers" in access:
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-users me-2"), "Customers"], href="/dashboard/customers"))
    if "field" in access:
        dropdown_items.append(dbc.DropdownMenuItem(divider=True))
        dropdown_items.append(dbc.DropdownMenuItem([html.I(className="fas fa-wrench me-2"), "Field Ops"], href="/dashboard/field"))
    
    if dropdown_items:
        nav_items.append(dbc.DropdownMenu(
            dropdown_items,
            label=[html.I(className="fas fa-th me-1"), "More"],
            nav=True,
            in_navbar=True,
            className="text-light"
        ))
    
    return dbc.Navbar(
        dbc.Container([
            html.A([
                html.I(className="fas fa-satellite-dish me-2"),
                html.Span("AquaWatch AI", className="fw-bold")
            ], href="/dashboard", className="navbar-brand", style={"color": COLORS["accent"]}),
            
            dbc.Nav(nav_items, navbar=True, className="me-auto"),
            
            html.Div([
                dbc.Button([html.I(className="fas fa-volume-up me-1"), "Voice"], id="toggle-voice", color="info", size="sm", className="me-2"),
                dbc.Badge(user_info.get("name", "User"), color="secondary", className="me-2 py-2 px-3"),
                dbc.Button([html.I(className="fas fa-sign-out-alt")], href="/", color="outline-danger", size="sm"),
            ], className="d-flex align-items-center")
        ], fluid=True),
        color=COLORS["bg_card"],
        dark=True,
        sticky="top",
        className="border-bottom border-secondary"
    )


# =============================================================================
# AI COMMAND CENTER - Main Feature
# =============================================================================

def create_ai_center():
    """Create the AI Command Center with voice alerts."""
    
    alerts = LeakDetectionAI.get_current_alerts()
    ai_stats = LeakDetectionAI.get_ai_analysis()
    
    # Generate voice text for most critical alert
    if alerts:
        critical_alert = alerts[0]
        voice_text = LeakDetectionAI.generate_voice_alert(critical_alert)
    else:
        voice_text = "No critical alerts at this time. All systems normal."
    
    return dbc.Container([
        # Hidden store for voice alerts
        dcc.Store(id="voice-alert-text", data=voice_text),
        dcc.Store(id="voice-enabled", data=True),
        dcc.Interval(id="alert-refresh", interval=30000, n_intervals=0),  # Refresh every 30s
        
        # Header
        html.Div([
            html.H3([html.I(className="fas fa-brain me-2"), "AI Leak Detection Center"], 
                   className="mb-0", style={"color": COLORS["accent"]}),
            html.P("Real-time AI-powered leak detection with voice alerts", className="text-muted mb-0"),
        ], className="mt-4 mb-4"),
        
        # AI Status Bar
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-microchip fa-2x mb-2", style={"color": COLORS["accent"]}),
                            html.H5(ai_stats["ai_model_version"], className="mb-0"),
                            html.Small("AI Model", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-bullseye fa-2x mb-2 text-success"),
                            html.H5(f"{ai_stats['detection_accuracy']}%", className="mb-0 text-success"),
                            html.Small("Detection Accuracy", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-search fa-2x mb-2 text-info"),
                            html.H5(str(ai_stats["predictions_today"]), className="mb-0 text-info"),
                            html.Small("Predictions Today", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle fa-2x mb-2 text-warning"),
                            html.H5(str(ai_stats["anomalies_detected"]), className="mb-0 text-warning"),
                            html.Small("Anomalies Detected", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-tint fa-2x mb-2 text-danger"),
                            html.H5(str(ai_stats["leaks_confirmed"]), className="mb-0 text-danger"),
                            html.Small("Leaks Confirmed", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dbc.Button([
                                html.I(className="fas fa-volume-up fa-2x")
                            ], id="speak-alert-btn", color="info", className="rounded-circle p-3"),
                            html.Div("Voice Alert", className="mt-2 small text-muted")
                        ], className="text-center")
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=2),
        ], className="mb-4"),
        
        # Main Content
        dbc.Row([
            # Alert List
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bell me-2 text-danger"),
                        "Active Leak Alerts",
                        dbc.Badge(str(len(alerts)), color="danger", className="ms-2")
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        html.Div([
                            create_alert_card(alert) for alert in alerts
                        ], style={"maxHeight": "500px", "overflowY": "auto"})
                    ], className="p-2")
                ], className="bg-dark border-secondary h-100")
            ], md=5),
            
            # Map
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-map-marked-alt me-2"),
                        "Leak Location Map"
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_leak_map(alerts),
                            config={"displayModeBar": False},
                            style={"height": "450px"}
                        )
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=7),
        ], className="mb-4"),
        
        # AI Analysis Panel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "AI Confidence Analysis"
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_confidence_chart(alerts),
                            config={"displayModeBar": False},
                            style={"height": "250px"}
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-tachometer-alt me-2"),
                        "Pressure Anomaly Detection"
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_pressure_chart(),
                            config={"displayModeBar": False},
                            style={"height": "250px"}
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
        ]),
        
    ], fluid=True)


def create_alert_card(alert: Dict):
    """Create a detailed alert card."""
    severity_colors = {"critical": "danger", "high": "warning", "medium": "info"}
    severity_icons = {"critical": "fa-radiation", "high": "fa-exclamation-triangle", "medium": "fa-info-circle"}
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className=f"fas {severity_icons[alert['severity']]} fa-2x text-{severity_colors[alert['severity']]}"),
                    ], className="text-center")
                ], width=2),
                dbc.Col([
                    html.Div([
                        html.Div([
                            dbc.Badge(alert["severity"].upper(), color=severity_colors[alert["severity"]], className="me-2"),
                            html.Span(alert["alert_id"], className="text-muted small"),
                        ]),
                        html.H6([
                            html.I(className="fas fa-map-marker-alt me-1"),
                            f"{alert['area']}"
                        ], className="mb-1 mt-2"),
                        html.P([
                            html.I(className="fas fa-road me-1 text-muted"),
                            alert["street"]
                        ], className="mb-1 small"),
                        html.P([
                            html.I(className="fas fa-pipe me-1 text-muted"),
                            f"Pipe: {alert['pipe_id']} ({alert['pipe_diameter']}mm {alert['pipe_material']})"
                        ], className="mb-1 small text-muted"),
                    ])
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Span("AI Confidence", className="small text-muted"),
                            html.H4(f"{alert['confidence']*100:.0f}%", className="mb-0 text-info"),
                        ], className="text-end"),
                        html.Div([
                            html.Span("Leak Rate", className="small text-muted"),
                            html.Div(f"{alert['leak_rate_lpm']:.0f} L/min", className="text-warning"),
                        ], className="text-end mt-2"),
                        html.Div([
                            html.Span("Distance", className="small text-muted"),
                            html.Div(f"~{alert['estimated_distance_m']}m", className="text-success"),
                        ], className="text-end mt-1"),
                    ])
                ], width=4),
            ]),
            html.Hr(className="border-secondary my-2"),
            html.Div([
                html.I(className="fas fa-robot me-2 text-info"),
                html.Span(alert["recommended_action"], className="small")
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button([html.I(className="fas fa-volume-up me-1"), "Announce"], 
                              id={"type": "speak-btn", "index": alert["alert_id"]},
                              color="info", size="sm", className="me-1 mt-2"),
                    dbc.Button([html.I(className="fas fa-map me-1"), "Navigate"], 
                              color="success", size="sm", className="me-1 mt-2"),
                    dbc.Button([html.I(className="fas fa-user-plus me-1"), "Dispatch"], 
                              color="warning", size="sm", className="mt-2"),
                ], className="mt-2")
            ])
        ], className="p-2")
    ], className=f"mb-2 border-{severity_colors[alert['severity']]} bg-dark", 
       style={"borderLeftWidth": "4px"})


def create_leak_map(alerts: List[Dict]):
    """Create a map showing leak locations."""
    if not alerts:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = {"critical": "red", "high": "orange", "medium": "yellow"}
    sizes = {"critical": 25, "high": 20, "medium": 15}
    
    for alert in alerts:
        fig.add_trace(go.Scattermap(
            lat=[alert["lat"]],
            lon=[alert["lon"]],
            mode="markers+text",
            marker=dict(size=sizes[alert["severity"]], color=colors[alert["severity"]]),
            text=f"{alert['pipe_id']}<br>{alert['area']}",
            textposition="top center",
            name=alert["severity"].title(),
            hovertemplate=(
                f"<b>{alert['pipe_id']}</b><br>"
                f"Area: {alert['area']}<br>"
                f"Street: {alert['street']}<br>"
                f"Confidence: {alert['confidence']*100:.0f}%<br>"
                f"Leak Rate: {alert['leak_rate_lpm']:.0f} L/min"
                "<extra></extra>"
            )
        ))
    
    fig.update_layout(
        map=dict(
            style="carto-darkmatter",
            center=dict(lat=alerts[0]["lat"], lon=alerts[0]["lon"]),
            zoom=10
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"]
    )
    
    return fig


def create_confidence_chart(alerts: List[Dict]):
    """Create AI confidence chart."""
    if not alerts:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = {"critical": "#dc3545", "high": "#ffc107", "medium": "#0dcaf0"}
    
    fig.add_trace(go.Bar(
        x=[a["pipe_id"] for a in alerts],
        y=[a["confidence"] * 100 for a in alerts],
        marker_color=[colors[a["severity"]] for a in alerts],
        text=[f"{a['confidence']*100:.0f}%" for a in alerts],
        textposition="outside"
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        margin=dict(l=40, r=20, t=20, b=40),
        yaxis=dict(title="Confidence %", range=[0, 110], gridcolor="rgba(255,255,255,0.1)"),
        xaxis=dict(title=""),
        showlegend=False
    )
    
    return fig


def create_pressure_chart():
    """Create real-time pressure chart with anomaly detection."""
    times = pd.date_range(end=datetime.now(), periods=100, freq="1min")
    
    # Normal pressure with anomaly
    pressure = 3.0 + np.random.normal(0, 0.08, 100)
    pressure[70:85] = pressure[70:85] - np.linspace(0, 0.8, 15)  # Leak event
    
    # Threshold
    threshold = [2.5] * 100
    
    # Anomaly score
    anomaly_score = np.abs(pressure - 3.0) / 0.5
    anomaly_score = np.clip(anomaly_score, 0, 1)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(go.Scatter(
        x=times, y=pressure,
        mode="lines",
        name="Pressure",
        line=dict(color=COLORS["accent"], width=2)
    ), secondary_y=False)
    
    fig.add_trace(go.Scatter(
        x=times, y=threshold,
        mode="lines",
        name="Threshold",
        line=dict(color="red", width=1, dash="dash")
    ), secondary_y=False)
    
    fig.add_trace(go.Scatter(
        x=times, y=anomaly_score,
        mode="lines",
        name="Anomaly Score",
        line=dict(color="orange", width=1),
        fill="tozeroy",
        fillcolor="rgba(255,165,0,0.2)"
    ), secondary_y=True)
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        margin=dict(l=40, r=40, t=20, b=40),
        legend=dict(orientation="h", y=-0.15),
        yaxis=dict(title="Pressure (bar)", gridcolor="rgba(255,255,255,0.1)"),
        yaxis2=dict(title="Anomaly", gridcolor="rgba(255,255,255,0.1)", range=[0, 1.5])
    )
    
    return fig


# =============================================================================
# OTHER VIEWS
# =============================================================================

def create_national_view():
    """National strategic view."""
    return dbc.Container([
        html.H3([html.I(className="fas fa-globe me-2"), "National Overview"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        dbc.Row([
            dbc.Col([dbc.Card([dbc.CardBody([
                html.H6("National NRW Rate", className="text-muted"),
                html.H2("34.2%", className="text-warning"),
                html.Small("↓ 2.1% from last month", className="text-success")
            ])], className="bg-dark border-secondary")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([
                html.H6("Active Sensors", className="text-muted"),
                html.H2("247", style={"color": COLORS["accent"]}),
                html.Small("98.4% online", className="text-success")
            ])], className="bg-dark border-secondary")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([
                html.H6("Active Alerts", className="text-muted"),
                html.H2("12", className="text-danger"),
                html.Small("3 critical", className="text-danger")
            ])], className="bg-dark border-secondary")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([
                html.H6("Water Saved (YTD)", className="text-muted"),
                html.H2("2.4M m³", className="text-success"),
                html.Small("$1.2M recovered", className="text-success")
            ])], className="bg-dark border-secondary")], md=3),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("System Health", className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(figure=go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=87,
                            title={"text": "Overall Score", "font": {"color": "white"}},
                            gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLORS["accent"]},
                                   "steps": [{"range": [0, 50], "color": "#dc3545"}, {"range": [50, 75], "color": "#ffc107"}, {"range": [75, 100], "color": "#198754"}]}
                        )).update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300))
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("AI Predictions vs Confirmed", className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(figure=px.pie(
                            values=[85, 10, 5], names=["Normal", "Suspected", "Confirmed Leak"],
                            color_discrete_sequence=[COLORS["accent"], "#ffc107", "#dc3545"]
                        ).update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300))
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
        ])
    ], fluid=True)


def create_operations_view():
    """Operations control view."""
    alerts = LeakDetectionAI.get_current_alerts()
    
    times = pd.date_range(end=datetime.now(), periods=100, freq="5min")
    pressure = 3.0 + np.random.normal(0, 0.15, 100)
    pressure[70:80] -= 0.8
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-desktop me-2"), "Operations Control"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-bell me-2 text-danger"), "Live Alerts"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                dbc.Row([
                                    dbc.Col([html.Strong(a["alert_id"]), html.Br(), html.Small(a["area"])], width=5),
                                    dbc.Col([dbc.Badge(a["severity"].upper(), color="danger" if a["severity"]=="critical" else "warning")], width=3),
                                    dbc.Col([dbc.Button("View", size="sm", color="info")], width=4)
                                ])
                            ], className="bg-dark border-secondary") for a in alerts[:5]
                        ], flush=True)
                    ])
                ], className="bg-dark border-secondary")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Pressure Monitoring", className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(figure=go.Figure([
                            go.Scatter(x=times, y=pressure, mode="lines", name="Pressure", line={"color": COLORS["accent"]}),
                            go.Scatter(x=times, y=[3.5]*100, mode="lines", name="High", line={"color": "red", "dash": "dash"}),
                            go.Scatter(x=times, y=[2.5]*100, mode="lines", name="Low", line={"color": "orange", "dash": "dash"}),
                        ]).update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=300, margin=dict(l=40,r=20,t=20,b=40), yaxis_title="Pressure (bar)", legend=dict(orientation="h", y=-0.2)))
                    ])
                ], className="bg-dark border-secondary")
            ], md=8),
        ])
    ], fluid=True)


def create_field_view():
    """Field technician view."""
    alerts = LeakDetectionAI.get_current_alerts()
    
    work_orders = [
        {"id": "WO-001", "pipe": alerts[0]["pipe_id"] if alerts else "PIPE-001", "location": alerts[0]["area"] + ", " + alerts[0]["street"] if alerts else "Kitwe Central", "type": "Leak Repair", "priority": "High"},
        {"id": "WO-002", "pipe": "PIPE-KIT-005", "location": "Ndola East, Market Rd", "type": "Sensor Install", "priority": "Medium"},
        {"id": "WO-003", "pipe": "PIPE-NDL-003", "location": "Kitwe South, Industrial", "type": "Valve Check", "priority": "Low"},
    ]
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-wrench me-2"), "Field Operations"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        dbc.Row([
            dbc.Col([dbc.Card([dbc.CardBody([html.H4("3", style={"color": COLORS["accent"]}), html.Small("Assigned")])], className="bg-dark border-secondary text-center")], width=4),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4("1", className="text-warning"), html.Small("In Progress")])], className="bg-dark border-secondary text-center")], width=4),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4("12", className="text-success"), html.Small("Completed")])], className="bg-dark border-secondary text-center")], width=4),
        ], className="mb-4"),
        
        html.H5("My Work Orders", className="mb-3"),
        
        *[dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5(wo["id"]), 
                        html.P([html.I(className="fas fa-map-marker-alt me-1"), wo["location"]], className="mb-1"),
                        html.P([html.I(className="fas fa-pipe me-1"), f"Pipe: {wo['pipe']}"]),
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(wo["priority"], color="danger" if wo["priority"]=="High" else "warning" if wo["priority"]=="Medium" else "secondary"),
                        html.Br(),
                        dbc.Button([html.I(className="fas fa-volume-up me-1"), "Voice"], color="info", size="sm", className="mt-2 me-1"),
                        dbc.Button([html.I(className="fas fa-map me-1"), "Navigate"], color="success", size="sm", className="mt-2"),
                    ], md=4, className="text-end")
                ])
            ])
        ], className="bg-dark border-secondary mb-3") for wo in work_orders],
        
        dbc.Row([
            dbc.Col([dbc.Button([html.I(className="fas fa-camera me-2"), "Photo"], color="secondary", className="w-100")], width=6),
            dbc.Col([dbc.Button([html.I(className="fas fa-microphone me-2"), "Voice Note"], color="secondary", className="w-100")], width=6),
        ])
    ], fluid=True, className="pb-5")


# =============================================================================
# COMMAND CENTER VIEW
# =============================================================================

def create_command_center_view():
    """Mission Control / Command Center view."""
    
    alerts = LeakDetectionAI.get_current_alerts()
    
    # System metrics
    metrics = {
        "system_uptime": "99.7%",
        "active_sensors": 247,
        "offline_sensors": 4,
        "data_points_today": 1_847_293,
        "ai_predictions": 2847,
        "response_time_ms": 45,
        "bandwidth_usage": "2.4 GB/day",
        "storage_used": "847 GB / 2 TB"
    }
    
    # Simulated real-time data streams
    times = pd.date_range(end=datetime.now(), periods=60, freq="1min")
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-rocket me-2"), "Command Center"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Status Banner
        dbc.Alert([
            dbc.Row([
                dbc.Col([
                    html.I(className="fas fa-check-circle fa-2x text-success me-3"),
                ], width="auto"),
                dbc.Col([
                    html.H5("All Systems Operational", className="mb-0"),
                    html.Small(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", className="text-muted")
                ])
            ], align="center")
        ], color="dark", className="border border-success mb-4"),
        
        # Main Metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-server fa-2x mb-2", style={"color": COLORS["accent"]}),
                        html.H4(metrics["system_uptime"], className="text-success"),
                        html.Small("System Uptime", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-satellite fa-2x mb-2 text-info"),
                        html.H4(f"{metrics['active_sensors']}", className="text-info"),
                        html.Small("Active Sensors", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-database fa-2x mb-2 text-warning"),
                        html.H4(f"{metrics['data_points_today']:,}", className="text-warning"),
                        html.Small("Data Points Today", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-brain fa-2x mb-2 text-success"),
                        html.H4(f"{metrics['ai_predictions']}", className="text-success"),
                        html.Small("AI Predictions", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-bolt fa-2x mb-2 text-warning"),
                        html.H4(f"{metrics['response_time_ms']}ms", className="text-warning"),
                        html.Small("Response Time", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-hdd fa-2x mb-2 text-info"),
                        html.H4("42%", className="text-info"),
                        html.Small("Storage Used", className="text-muted")
                    ], className="text-center")
                ], className="bg-dark border-secondary")
            ], md=2),
        ], className="mb-4"),
        
        # Live Feeds
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-area me-2"), "System Load (Real-time)"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(x=times, y=30 + np.random.normal(0, 5, 60), fill='tozeroy', name="CPU", line=dict(color=COLORS["accent"])),
                                go.Scatter(x=times, y=45 + np.random.normal(0, 8, 60), fill='tozeroy', name="Memory", line=dict(color="#ffc107")),
                            ]).update_layout(
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=200, margin=dict(l=40,r=20,t=10,b=30),
                                yaxis=dict(title="%", range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                                legend=dict(orientation="h", y=-0.2)
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-network-wired me-2"), "Data Throughput"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(x=times, y=np.abs(np.random.normal(150, 30, 60)), name="Incoming", line=dict(color="#198754")),
                                go.Scatter(x=times, y=np.abs(np.random.normal(80, 20, 60)), name="Outgoing", line=dict(color="#dc3545")),
                            ]).update_layout(
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=200, margin=dict(l=40,r=20,t=10,b=30),
                                yaxis=dict(title="KB/s", gridcolor="rgba(255,255,255,0.1)"),
                                legend=dict(orientation="h", y=-0.2)
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=6),
        ], className="mb-4"),
        
        # Active Alerts & Quick Actions
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-exclamation-triangle me-2 text-warning"), "Active Incidents"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([html.Tr([html.Th("ID"), html.Th("Location"), html.Th("Severity"), html.Th("Status")])]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(a["alert_id"]),
                                    html.Td(a["area"]),
                                    html.Td(dbc.Badge(a["severity"].upper(), color="danger" if a["severity"]=="critical" else "warning")),
                                    html.Td(dbc.Badge("Active", color="info"))
                                ]) for a in alerts[:4]
                            ])
                        ], dark=True, striped=True, hover=True, size="sm")
                    ])
                ], className="bg-dark border-secondary")
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-bolt me-2"), "Quick Actions"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Button([html.I(className="fas fa-bell me-2"), "Sound Alarm"], color="danger", className="w-100 mb-2"),
                        dbc.Button([html.I(className="fas fa-broadcast-tower me-2"), "Alert All"], color="warning", className="w-100 mb-2"),
                        dbc.Button([html.I(className="fas fa-file-export me-2"), "Export Report"], color="info", className="w-100 mb-2"),
                        dbc.Button([html.I(className="fas fa-sync me-2"), "Refresh Data"], color="secondary", className="w-100"),
                    ])
                ], className="bg-dark border-secondary")
            ], md=4),
        ])
    ], fluid=True)


# =============================================================================
# DIGITAL TWIN VIEW
# =============================================================================

def create_digital_twin_view():
    """Digital Twin - 3D network visualization."""
    
    pipes = LeakDetectionAI.PIPE_NETWORK
    alerts = LeakDetectionAI.get_current_alerts()
    alert_pipes = [a["pipe_id"] for a in alerts]
    
    # Create network graph
    nodes = []
    edges = []
    
    # Create nodes for each pipe endpoint
    node_positions = {}
    for i, (pipe_id, pipe) in enumerate(pipes.items()):
        lat, lon = pipe["lat"], pipe["lon"]
        # Create two nodes for each pipe (start and end)
        node_id = f"N-{i}"
        node_positions[pipe_id] = (lat, lon)
        
        status = "critical" if pipe_id in alert_pipes else "normal"
        nodes.append({
            "id": pipe_id,
            "lat": lat,
            "lon": lon,
            "label": pipe_id,
            "area": pipe["area"],
            "diameter": pipe["diameter"],
            "material": pipe["material"],
            "status": status
        })
    
    # Network statistics
    stats = {
        "total_pipes": len(pipes),
        "total_length_km": 127.5,
        "avg_pipe_age": 18.3,
        "critical_pipes": len([p for p in alert_pipes if p in pipes]),
        "pressure_zones": 5,
        "dmas": 12
    }
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-cube me-2"), "Digital Twin - Network Model"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Stats Row
        dbc.Row([
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(stats["total_pipes"]), html.Small("Total Pipes")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['total_length_km']} km"), html.Small("Network Length")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['avg_pipe_age']} yrs"), html.Small("Avg Pipe Age")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(stats["critical_pipes"], className="text-danger"), html.Small("Critical")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(stats["pressure_zones"]), html.Small("Pressure Zones")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(stats["dmas"]), html.Small("DMAs")])], className="bg-dark border-secondary text-center")], md=2),
        ], className="mb-4"),
        
        dbc.Row([
            # 3D-like Network View
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-project-diagram me-2"), "Network Topology"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                # Pipes as markers
                                go.Scattermap(
                                    lat=[n["lat"] for n in nodes],
                                    lon=[n["lon"] for n in nodes],
                                    mode="markers+text",
                                    marker=dict(
                                        size=[20 if n["status"]=="critical" else 12 for n in nodes],
                                        color=["#dc3545" if n["status"]=="critical" else COLORS["accent"] for n in nodes]
                                    ),
                                    text=[n["id"] for n in nodes],
                                    textposition="top center",
                                    hovertemplate="<b>%{text}</b><br>Area: %{customdata[0]}<br>Diameter: %{customdata[1]}mm<br>Material: %{customdata[2]}<extra></extra>",
                                    customdata=[[n["area"], n["diameter"], n["material"]] for n in nodes]
                                )
                            ]).update_layout(
                                map=dict(style="carto-darkmatter", center=dict(lat=-12.85, lon=28.3), zoom=8),
                                margin=dict(l=0, r=0, t=0, b=0),
                                height=400,
                                paper_bgcolor=COLORS["bg_card"]
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=8),
            
            # Pipe Details Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-info-circle me-2"), "Pipe Details"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        html.Div([
                            dbc.ListGroup([
                                dbc.ListGroupItem([
                                    html.Div([
                                        html.Strong(n["id"]),
                                        dbc.Badge("ALERT" if n["status"]=="critical" else "OK", 
                                                 color="danger" if n["status"]=="critical" else "success",
                                                 className="ms-2")
                                    ]),
                                    html.Small(f"{n['area']} • {n['diameter']}mm {n['material']}", className="text-muted")
                                ], className="bg-dark border-secondary py-2") for n in nodes[:6]
                            ], flush=True)
                        ], style={"maxHeight": "350px", "overflowY": "auto"})
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=4),
        ], className="mb-4"),
        
        # Simulation Controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-play-circle me-2"), "Simulation Controls"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([html.I(className="fas fa-play me-2"), "Run Simulation"], color="success", className="me-2"),
                                dbc.Button([html.I(className="fas fa-tint me-2"), "Simulate Leak"], color="warning", className="me-2"),
                                dbc.Button([html.I(className="fas fa-bolt me-2"), "Simulate Burst"], color="danger", className="me-2"),
                                dbc.Button([html.I(className="fas fa-redo me-2"), "Reset"], color="secondary"),
                            ])
                        ])
                    ])
                ], className="bg-dark border-secondary")
            ])
        ])
    ], fluid=True)


# =============================================================================
# EVENTS VIEW
# =============================================================================

def create_events_view():
    """Events and incident management view."""
    
    # Sample events data
    events = [
        {"id": "EVT-001", "type": "Leak Detected", "location": "Kitwe Central", "time": datetime.now() - timedelta(hours=2), "status": "Active", "priority": "High", "assigned": "John M."},
        {"id": "EVT-002", "type": "Pressure Drop", "location": "Ndola East", "time": datetime.now() - timedelta(hours=5), "status": "Investigating", "priority": "Medium", "assigned": "Sarah K."},
        {"id": "EVT-003", "type": "Sensor Offline", "location": "Lusaka CBD", "time": datetime.now() - timedelta(hours=8), "status": "Resolved", "priority": "Low", "assigned": "Mike T."},
        {"id": "EVT-004", "type": "Burst Main", "location": "Kitwe South", "time": datetime.now() - timedelta(days=1), "status": "Resolved", "priority": "Critical", "assigned": "Emergency Team"},
        {"id": "EVT-005", "type": "Meter Tampering", "location": "Ndola Central", "time": datetime.now() - timedelta(days=2), "status": "Under Review", "priority": "Medium", "assigned": "Inspection Team"},
        {"id": "EVT-006", "type": "Water Quality Alert", "location": "Kitwe North", "time": datetime.now() - timedelta(hours=12), "status": "Monitoring", "priority": "High", "assigned": "Lab Team"},
    ]
    
    # Event statistics
    stats = {
        "total_today": 8,
        "active": 3,
        "resolved": 5,
        "avg_resolution_hrs": 4.2
    }
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-calendar-alt me-2"), "Events & Incidents"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Stats
        dbc.Row([
            dbc.Col([dbc.Card([dbc.CardBody([html.H3(stats["total_today"], style={"color": COLORS["accent"]}), html.Small("Events Today")])], className="bg-dark border-secondary text-center")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([html.H3(stats["active"], className="text-warning"), html.Small("Active")])], className="bg-dark border-secondary text-center")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([html.H3(stats["resolved"], className="text-success"), html.Small("Resolved")])], className="bg-dark border-secondary text-center")], md=3),
            dbc.Col([dbc.Card([dbc.CardBody([html.H3(f"{stats['avg_resolution_hrs']}h"), html.Small("Avg Resolution")])], className="bg-dark border-secondary text-center")], md=3),
        ], className="mb-4"),
        
        # Events Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-list me-2"),
                        "Event Log",
                        dbc.Button([html.I(className="fas fa-plus me-1"), "New Event"], color="info", size="sm", className="float-end")
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("ID"),
                                    html.Th("Type"),
                                    html.Th("Location"),
                                    html.Th("Time"),
                                    html.Th("Priority"),
                                    html.Th("Status"),
                                    html.Th("Assigned"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(e["id"]),
                                    html.Td([
                                        html.I(className=f"fas fa-{'tint' if 'Leak' in e['type'] else 'exclamation-triangle' if 'Burst' in e['type'] else 'info-circle'} me-2"),
                                        e["type"]
                                    ]),
                                    html.Td(e["location"]),
                                    html.Td(e["time"].strftime("%m/%d %H:%M")),
                                    html.Td(dbc.Badge(e["priority"], color={
                                        "Critical": "danger", "High": "warning", "Medium": "info", "Low": "secondary"
                                    }.get(e["priority"], "secondary"))),
                                    html.Td(dbc.Badge(e["status"], color={
                                        "Active": "danger", "Investigating": "warning", "Monitoring": "info", 
                                        "Under Review": "secondary", "Resolved": "success"
                                    }.get(e["status"], "secondary"))),
                                    html.Td(e["assigned"]),
                                    html.Td([
                                        dbc.Button([html.I(className="fas fa-eye")], color="info", size="sm", className="me-1"),
                                        dbc.Button([html.I(className="fas fa-edit")], color="warning", size="sm"),
                                    ])
                                ]) for e in events
                            ])
                        ], dark=True, striped=True, hover=True, responsive=True)
                    ])
                ], className="bg-dark border-secondary")
            ])
        ], className="mb-4"),
        
        # Timeline
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-history me-2"), "Recent Activity Timeline"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.I(className=f"fas fa-circle text-{'danger' if e['status']=='Active' else 'success' if e['status']=='Resolved' else 'warning'} me-2"),
                                    html.Strong(e["time"].strftime("%H:%M")),
                                    html.Span(f" - {e['type']} at {e['location']}", className="text-muted"),
                                    dbc.Badge(e["status"], className="ms-2", color="secondary")
                                ], className="mb-2")
                            ]) for e in sorted(events, key=lambda x: x["time"], reverse=True)[:5]
                        ])
                    ])
                ], className="bg-dark border-secondary")
            ])
        ])
    ], fluid=True)


# =============================================================================
# ASSET HEALTH VIEW
# =============================================================================

def create_assets_view():
    """Asset Health monitoring view."""
    
    # Sample assets data
    assets = [
        {"id": "PUMP-001", "name": "Main Distribution Pump", "type": "Pump", "location": "Kitwe WTP", "health": 92, "status": "Good", "last_maintenance": datetime.now() - timedelta(days=30), "next_maintenance": datetime.now() + timedelta(days=60)},
        {"id": "VALVE-042", "name": "Zone Isolation Valve", "type": "Valve", "location": "Kitwe Central", "health": 78, "status": "Fair", "last_maintenance": datetime.now() - timedelta(days=90), "next_maintenance": datetime.now() + timedelta(days=5)},
        {"id": "METER-128", "name": "Bulk Flow Meter", "type": "Meter", "location": "DMA-KIT-001", "health": 95, "status": "Good", "last_maintenance": datetime.now() - timedelta(days=15), "next_maintenance": datetime.now() + timedelta(days=75)},
        {"id": "TANK-003", "name": "Elevated Storage Tank", "type": "Tank", "location": "Kitwe North", "health": 65, "status": "Needs Attention", "last_maintenance": datetime.now() - timedelta(days=180), "next_maintenance": datetime.now() - timedelta(days=10)},
        {"id": "SENSOR-247", "name": "Pressure Sensor Array", "type": "Sensor", "location": "Ndola East", "health": 88, "status": "Good", "last_maintenance": datetime.now() - timedelta(days=45), "next_maintenance": datetime.now() + timedelta(days=45)},
        {"id": "PUMP-002", "name": "Booster Pump Station", "type": "Pump", "location": "Lusaka CBD", "health": 45, "status": "Critical", "last_maintenance": datetime.now() - timedelta(days=200), "next_maintenance": datetime.now() - timedelta(days=20)},
    ]
    
    # Calculate overall health
    avg_health = sum(a["health"] for a in assets) / len(assets)
    critical_count = len([a for a in assets if a["health"] < 50])
    needs_maintenance = len([a for a in assets if a["next_maintenance"] < datetime.now()])
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-heartbeat me-2"), "Asset Health Monitor"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Health Overview
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=avg_health,
                                title={"text": "Overall Fleet Health", "font": {"color": "white"}},
                                gauge={
                                    "axis": {"range": [0, 100]},
                                    "bar": {"color": COLORS["accent"]},
                                    "steps": [
                                        {"range": [0, 50], "color": "#dc3545"},
                                        {"range": [50, 75], "color": "#ffc107"},
                                        {"range": [75, 100], "color": "#198754"}
                                    ]
                                }
                            )).update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=200, margin=dict(t=50, b=0))
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=4),
            dbc.Col([
                dbc.Row([
                    dbc.Col([dbc.Card([dbc.CardBody([html.H3(len(assets)), html.Small("Total Assets")])], className="bg-dark border-secondary text-center")], md=4),
                    dbc.Col([dbc.Card([dbc.CardBody([html.H3(critical_count, className="text-danger"), html.Small("Critical")])], className="bg-dark border-secondary text-center")], md=4),
                    dbc.Col([dbc.Card([dbc.CardBody([html.H3(needs_maintenance, className="text-warning"), html.Small("Overdue")])], className="bg-dark border-secondary text-center")], md=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Asset Health Distribution"),
                                dcc.Graph(
                                    figure=px.pie(
                                        values=[len([a for a in assets if a["health"] >= 80]),
                                               len([a for a in assets if 50 <= a["health"] < 80]),
                                               len([a for a in assets if a["health"] < 50])],
                                        names=["Good", "Fair", "Critical"],
                                        color_discrete_sequence=["#198754", "#ffc107", "#dc3545"],
                                        hole=0.4
                                    ).update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=150, margin=dict(t=0,b=0,l=0,r=0), showlegend=True, legend=dict(orientation="h"))
                                )
                            ])
                        ], className="bg-dark border-secondary")
                    ])
                ])
            ], md=8),
        ], className="mb-4"),
        
        # Assets Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-cogs me-2"), "Asset Inventory"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([html.Tr([html.Th("Asset ID"), html.Th("Name"), html.Th("Type"), html.Th("Location"), html.Th("Health"), html.Th("Status"), html.Th("Next Maintenance"), html.Th("Actions")])]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(a["id"]),
                                    html.Td(a["name"]),
                                    html.Td([html.I(className=f"fas fa-{'cog' if a['type']=='Pump' else 'door-closed' if a['type']=='Valve' else 'tachometer-alt' if a['type']=='Meter' else 'database' if a['type']=='Tank' else 'broadcast-tower'} me-2"), a["type"]]),
                                    html.Td(a["location"]),
                                    html.Td([
                                        dbc.Progress(value=a["health"], color="success" if a["health"]>=80 else "warning" if a["health"]>=50 else "danger", style={"height": "20px"}, className="mb-0"),
                                        html.Small(f"{a['health']}%", className="ms-2")
                                    ]),
                                    html.Td(dbc.Badge(a["status"], color="success" if a["status"]=="Good" else "warning" if a["status"]=="Fair" else "danger" if a["status"]=="Critical" else "info")),
                                    html.Td([
                                        html.Span(a["next_maintenance"].strftime("%Y-%m-%d"), className="text-danger" if a["next_maintenance"] < datetime.now() else "")
                                    ]),
                                    html.Td([
                                        dbc.Button([html.I(className="fas fa-tools")], color="info", size="sm", className="me-1", title="Schedule Maintenance"),
                                        dbc.Button([html.I(className="fas fa-chart-line")], color="secondary", size="sm", title="View History"),
                                    ])
                                ]) for a in assets
                            ])
                        ], dark=True, striped=True, hover=True, responsive=True)
                    ])
                ], className="bg-dark border-secondary")
            ])
        ])
    ], fluid=True)


# =============================================================================
# BENCHMARKING VIEW
# =============================================================================

def create_benchmarking_view():
    """Utility benchmarking and comparison view."""
    
    # Sample utility comparison data
    utilities = [
        {"name": "Kitwe Water", "nrw": 34.2, "coverage": 87, "efficiency": 72, "customer_sat": 78, "collection": 82},
        {"name": "Ndola Water", "nrw": 38.5, "coverage": 82, "efficiency": 68, "customer_sat": 72, "collection": 78},
        {"name": "Lusaka Water", "nrw": 42.1, "coverage": 78, "efficiency": 65, "customer_sat": 68, "collection": 75},
        {"name": "Livingstone Water", "nrw": 45.8, "coverage": 75, "efficiency": 62, "customer_sat": 70, "collection": 72},
        {"name": "Industry Average", "nrw": 40.5, "coverage": 80, "efficiency": 67, "customer_sat": 72, "collection": 77},
    ]
    
    # IWA Performance Indicators
    kpis = [
        {"indicator": "Op24 - NRW by volume", "your_value": "34.2%", "benchmark": "25%", "status": "Below"},
        {"indicator": "Fi36 - Collection Efficiency", "your_value": "82%", "benchmark": "90%", "status": "Below"},
        {"indicator": "Op29 - Real Losses", "your_value": "180 L/conn/day", "benchmark": "100 L/conn/day", "status": "Below"},
        {"indicator": "QS23 - Response Time", "your_value": "4.2 hrs", "benchmark": "2 hrs", "status": "Below"},
        {"indicator": "Pe12 - Staff Efficiency", "your_value": "4.2 staff/1000", "benchmark": "5 staff/1000", "status": "Above"},
    ]
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-chart-bar me-2"), "Benchmarking & Performance"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Comparison Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-balance-scale me-2"), "Utility Comparison"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Bar(name="NRW %", x=[u["name"] for u in utilities], y=[u["nrw"] for u in utilities], marker_color="#dc3545"),
                                go.Bar(name="Coverage %", x=[u["name"] for u in utilities], y=[u["coverage"] for u in utilities], marker_color="#198754"),
                                go.Bar(name="Efficiency %", x=[u["name"] for u in utilities], y=[u["efficiency"] for u in utilities], marker_color=COLORS["accent"]),
                            ]).update_layout(
                                barmode="group",
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=300, margin=dict(l=40,r=20,t=20,b=40),
                                legend=dict(orientation="h", y=-0.15),
                                yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-trophy me-2"), "Your Ranking"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        html.Div([
                            html.H1("2nd", className="text-warning display-4 text-center mb-2"),
                            html.P("Out of 5 utilities", className="text-center text-muted"),
                            html.Hr(className="border-secondary"),
                            html.Div([
                                html.Div([html.Strong("NRW Rate:"), html.Span(" Best in region", className="text-success")], className="mb-2"),
                                html.Div([html.Strong("Coverage:"), html.Span(" 2nd place", className="text-warning")], className="mb-2"),
                                html.Div([html.Strong("Collection:"), html.Span(" Above average", className="text-success")]),
                            ])
                        ])
                    ])
                ], className="bg-dark border-secondary h-100")
            ], md=4),
        ], className="mb-4"),
        
        # IWA KPIs Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-award me-2"), "IWA Performance Indicators"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([html.Tr([html.Th("Indicator"), html.Th("Your Value"), html.Th("IWA Benchmark"), html.Th("Status"), html.Th("Gap")])]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(k["indicator"]),
                                    html.Td(k["your_value"]),
                                    html.Td(k["benchmark"]),
                                    html.Td(dbc.Badge(k["status"], color="success" if k["status"]=="Above" else "danger")),
                                    html.Td([
                                        html.I(className=f"fas fa-arrow-{'up text-success' if k['status']=='Above' else 'down text-danger'} me-1"),
                                        "Meeting target" if k["status"]=="Above" else "Improvement needed"
                                    ])
                                ]) for k in kpis
                            ])
                        ], dark=True, striped=True, hover=True)
                    ])
                ], className="bg-dark border-secondary")
            ])
        ], className="mb-4"),
        
        # Trend Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-line me-2"), "Performance Trend (12 Months)"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(x=pd.date_range(end=datetime.now(), periods=12, freq="M"), 
                                          y=[45, 44, 42, 41, 40, 39, 38, 37, 36, 35, 34.5, 34.2],
                                          name="Your NRW %", line=dict(color=COLORS["accent"], width=3)),
                                go.Scatter(x=pd.date_range(end=datetime.now(), periods=12, freq="M"),
                                          y=[40.5]*12, name="Industry Average", line=dict(color="#ffc107", dash="dash")),
                                go.Scatter(x=pd.date_range(end=datetime.now(), periods=12, freq="M"),
                                          y=[25]*12, name="IWA Target", line=dict(color="#198754", dash="dot")),
                            ]).update_layout(
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=250, margin=dict(l=40,r=20,t=20,b=40),
                                yaxis=dict(title="NRW %", gridcolor="rgba(255,255,255,0.1)"),
                                legend=dict(orientation="h", y=-0.2)
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ])
        ])
    ], fluid=True)


# =============================================================================
# CUSTOMERS VIEW
# =============================================================================

def create_customers_view():
    """Customer management and analytics view."""
    
    # Sample customer data
    customers = [
        {"id": "CUS-001", "name": "Zambia Breweries Ltd", "type": "Industrial", "zone": "Kitwe Industrial", "consumption": 45000, "billing": "On Time", "status": "Active"},
        {"id": "CUS-002", "name": "Kitwe Central Hospital", "type": "Institutional", "zone": "Kitwe Central", "consumption": 28000, "billing": "On Time", "status": "Active"},
        {"id": "CUS-003", "name": "Shoprite Kitwe", "type": "Commercial", "zone": "Kitwe CBD", "consumption": 12000, "billing": "Overdue", "status": "Active"},
        {"id": "CUS-004", "name": "Residential Block A", "type": "Residential", "zone": "Kitwe North", "consumption": 850, "billing": "On Time", "status": "Active"},
        {"id": "CUS-005", "name": "Ndola Primary School", "type": "Institutional", "zone": "Ndola Central", "consumption": 5200, "billing": "On Time", "status": "Active"},
        {"id": "CUS-006", "name": "Mining Corp HQ", "type": "Industrial", "zone": "Kitwe South", "consumption": 78000, "billing": "On Time", "status": "Active"},
    ]
    
    # Customer statistics
    stats = {
        "total": 45892,
        "active": 43521,
        "residential": 38450,
        "commercial": 4200,
        "industrial": 850,
        "institutional": 2392,
        "collection_rate": 82.5,
        "avg_consumption": 15.2
    }
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-users me-2"), "Customer Management"], className="mt-4 mb-4", style={"color": COLORS["accent"]}),
        
        # Stats Row
        dbc.Row([
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['total']:,}"), html.Small("Total Customers")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['active']:,}", className="text-success"), html.Small("Active")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['residential']:,}"), html.Small("Residential")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['commercial']:,}"), html.Small("Commercial")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['collection_rate']}%", className="text-warning"), html.Small("Collection Rate")])], className="bg-dark border-secondary text-center")], md=2),
            dbc.Col([dbc.Card([dbc.CardBody([html.H4(f"{stats['avg_consumption']} m³"), html.Small("Avg Consumption")])], className="bg-dark border-secondary text-center")], md=2),
        ], className="mb-4"),
        
        dbc.Row([
            # Customer Distribution Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-pie-chart me-2"), "Customer Distribution"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.pie(
                                values=[stats["residential"], stats["commercial"], stats["industrial"], stats["institutional"]],
                                names=["Residential", "Commercial", "Industrial", "Institutional"],
                                color_discrete_sequence=[COLORS["accent"], "#ffc107", "#dc3545", "#198754"],
                                hole=0.4
                            ).update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=250, margin=dict(t=20,b=20))
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=4),
            
            # Consumption by Type
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-tint me-2"), "Consumption by Sector (m³/month)"], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Bar(x=["Residential", "Commercial", "Industrial", "Institutional"],
                                      y=[580000, 250000, 420000, 150000],
                                      marker_color=[COLORS["accent"], "#ffc107", "#dc3545", "#198754"])
                            ]).update_layout(
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=250, margin=dict(l=40,r=20,t=20,b=40),
                                yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
                            )
                        )
                    ])
                ], className="bg-dark border-secondary")
            ], md=8),
        ], className="mb-4"),
        
        # Top Customers Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-star me-2"),
                        "Top Customers",
                        dbc.Input(placeholder="Search customers...", size="sm", className="float-end bg-dark text-white", style={"width": "200px"})
                    ], className="bg-dark border-secondary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([html.Tr([html.Th("ID"), html.Th("Name"), html.Th("Type"), html.Th("Zone"), html.Th("Consumption (m³)"), html.Th("Billing"), html.Th("Actions")])]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(c["id"]),
                                    html.Td(c["name"]),
                                    html.Td(dbc.Badge(c["type"], color="info" if c["type"]=="Industrial" else "warning" if c["type"]=="Commercial" else "success" if c["type"]=="Institutional" else "secondary")),
                                    html.Td(c["zone"]),
                                    html.Td(f"{c['consumption']:,}"),
                                    html.Td(dbc.Badge(c["billing"], color="success" if c["billing"]=="On Time" else "danger")),
                                    html.Td([
                                        dbc.Button([html.I(className="fas fa-eye")], color="info", size="sm", className="me-1"),
                                        dbc.Button([html.I(className="fas fa-file-invoice")], color="warning", size="sm", className="me-1"),
                                        dbc.Button([html.I(className="fas fa-chart-line")], color="secondary", size="sm"),
                                    ])
                                ]) for c in customers
                            ])
                        ], dark=True, striped=True, hover=True, responsive=True)
                    ])
                ], className="bg-dark border-secondary")
            ])
        ])
    ], fluid=True)


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    dcc.Store(id="current-voice-text", data=""),
    html.Div(id="page-content")
])


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("page-content", "children"),
    Output("session-store", "data"),
    Input("url", "pathname"),
    State("session-store", "data")
)
def display_page(pathname, session_data):
    user_info = None
    if session_data:
        user_info = get_session(session_data.get("token"))
    
    if pathname == "/" or pathname == "/login":
        return create_login_page(), session_data
    
    if pathname and pathname.startswith("/dashboard"):
        if not user_info:
            return create_login_page(), None
        
        view = "national"
        if "/operations" in pathname:
            view = "operations"
        elif "/ai" in pathname:
            view = "ai"
        elif "/field" in pathname:
            view = "field"
        elif "/command" in pathname:
            view = "command"
        elif "/twin" in pathname:
            view = "twin"
        elif "/events" in pathname:
            view = "events"
        elif "/assets" in pathname:
            view = "assets"
        elif "/benchmark" in pathname:
            view = "benchmark"
        elif "/customers" in pathname:
            view = "customers"
        
        content_map = {
            "national": create_national_view,
            "operations": create_operations_view,
            "ai": create_ai_center,
            "field": create_field_view,
            "command": create_command_center_view,
            "twin": create_digital_twin_view,
            "events": create_events_view,
            "assets": create_assets_view,
            "benchmark": create_benchmarking_view,
            "customers": create_customers_view
        }
        
        if view not in user_info.get("access", []):
            content = dbc.Alert(f"Access denied: {view}", color="danger", className="m-4")
        else:
            content = content_map.get(view, create_national_view)()
        
        return html.Div([create_navbar(user_info), content], style={"backgroundColor": COLORS["bg_dark"], "minHeight": "100vh"}), session_data
    
    return create_login_page(), session_data


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Output("login-error", "children"),
    Input("login-button", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not n_clicks:
        return no_update, no_update, no_update
    
    if not username or not password:
        return no_update, no_update, dbc.Alert("Enter username and password", color="warning")
    
    user_info = verify_password(username, password)
    
    if user_info:
        token = create_session(user_info)
        session_data = {"token": token, **user_info}
        
        # Route to AI center if available, otherwise first available
        if "ai" in user_info["access"]:
            return "/dashboard/ai", session_data, None
        elif "national" in user_info["access"]:
            return "/dashboard/national", session_data, None
        elif "operations" in user_info["access"]:
            return "/dashboard/operations", session_data, None
        else:
            return "/dashboard/field", session_data, None
    
    return no_update, no_update, dbc.Alert([html.I(className="fas fa-exclamation-triangle me-2"), "Invalid credentials"], color="danger")


# Client-side callback for voice - speaks the alert text
app.clientside_callback(
    """
    function(n_clicks, voiceText) {
        if (n_clicks > 0 && voiceText) {
            // Check if browser supports speech
            if ('speechSynthesis' in window) {
                // Cancel any ongoing speech
                window.speechSynthesis.cancel();
                
                // Create utterance
                var utterance = new SpeechSynthesisUtterance(voiceText);
                utterance.rate = 0.9;
                utterance.pitch = 1;
                utterance.volume = 1;
                
                // Play alert beep first
                try {
                    var audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    var oscillator = audioContext.createOscillator();
                    var gainNode = audioContext.createGain();
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    oscillator.frequency.value = 880;
                    oscillator.type = 'sine';
                    gainNode.gain.value = 0.3;
                    oscillator.start();
                    setTimeout(function() { oscillator.stop(); }, 200);
                } catch(e) {}
                
                // Speak after beep
                setTimeout(function() {
                    window.speechSynthesis.speak(utterance);
                }, 300);
            } else {
                alert('Voice not supported in this browser. Alert: ' + voiceText);
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("speak-alert-btn", "n_clicks"),
    Input("speak-alert-btn", "n_clicks"),
    State("voice-alert-text", "data"),
    prevent_initial_call=True
)


# =============================================================================
# RUN
# =============================================================================

if __name__ == '__main__':
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║         AquaWatch NRW - AI Command Center with Voice              ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║  🌐 URL: http://localhost:8050                                    ║
    ║                                                                   ║
    ║  ┌─────────────────────────────────────────────────────────────┐  ║
    ║  │  LOGIN CREDENTIALS                                          │  ║
    ║  ├─────────────────────────────────────────────────────────────┤  ║
    ║  │  admin / admin123        → All views + AI Center            │  ║
    ║  │  operator / operator123  → Operations + AI + Field          │  ║
    ║  │  technician / tech123    → Field only                       │  ║
    ║  │  demo / demo             → All views (read-only)            │  ║
    ║  └─────────────────────────────────────────────────────────────┘  ║
    ║                                                                   ║
    ║  🔊 VOICE ALERTS: Click the speaker button to hear leak info!    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=True, port=8050, host="0.0.0.0")
