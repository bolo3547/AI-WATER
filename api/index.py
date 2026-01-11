"""
AquaWatch NRW - Vercel Serverless Dashboard
============================================
Complete dashboard with login for Vercel deployment
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib

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

def generate_sensor_data():
    zones = ["Zone A - Downtown", "Zone B - Industrial", "Zone C - Residential", "Zone D - Commercial"]
    sensors = []
    for i in range(12):
        zone = zones[i % len(zones)]
        base_pressure = 45 + random.uniform(-5, 5)
        has_anomaly = random.random() < 0.15
        if has_anomaly:
            base_pressure -= random.uniform(5, 15)
        sensors.append({
            "sensor_id": f"SENSOR-{i+1:03d}",
            "zone": zone,
            "pressure_psi": round(base_pressure, 2),
            "flow_rate_gpm": round(100 + random.uniform(-20, 20), 2),
            "status": "anomaly" if has_anomaly else "normal",
            "anomaly_score": round(random.uniform(0.7, 0.95), 3) if has_anomaly else round(random.uniform(0.1, 0.3), 3)
        })
    return sensors

def generate_alerts():
    alert_types = [
        ("Pressure Drop Detected", "critical", "Zone A - Downtown"),
        ("Unusual Flow Pattern", "warning", "Zone B - Industrial"),
        ("Acoustic Anomaly", "warning", "Zone C - Residential"),
    ]
    alerts = []
    for i, (title, severity, zone) in enumerate(alert_types):
        if random.random() < 0.7:
            alerts.append({
                "id": f"ALERT-{1000+i}",
                "title": title,
                "severity": severity,
                "zone": zone,
                "estimated_loss_m3": round(random.uniform(10, 500), 1) if severity == "critical" else round(random.uniform(1, 50), 1)
            })
    return alerts

def get_stats():
    return {
        "total_sensors": 247,
        "sensors_online": 241,
        "nrw_percentage": round(random.uniform(18, 28), 1),
        "water_saved": round(random.uniform(1500, 3500), 0),
        "active_alerts": random.randint(3, 12),
        "ai_confidence": round(random.uniform(92, 98), 1),
    }

# =============================================================================
# COLORS
# =============================================================================

COLORS = {
    'primary': '#0066CC',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'dark': '#1a1a2e',
    'light': '#F8F9FA',
    'text': '#212529',
}

# =============================================================================
# APP
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "AquaWatch NRW"
server = app.server

# =============================================================================
# COMPONENTS
# =============================================================================

def stat_card(title, value, icon, color, subtitle=""):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas {icon} fa-2x me-3", style={"color": color}),
                html.Div([
                    html.H6(title, className="text-muted mb-1"),
                    html.H3(value, className="mb-0 fw-bold"),
                    html.Small(subtitle, className="text-muted") if subtitle else None,
                ]),
            ], className="d-flex align-items-center"),
        ])
    ], className="shadow-sm h-100", style={"borderRadius": "12px"})

def alert_card(alert):
    colors = {"critical": COLORS['danger'], "warning": COLORS['warning']}
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-exclamation-triangle me-2", style={"color": colors.get(alert['severity'], COLORS['warning'])}),
                html.Strong(alert['title']),
                dbc.Badge(alert['severity'].upper(), color="danger" if alert['severity'] == "critical" else "warning", className="ms-2"),
            ]),
            html.Small(f"{alert['zone']} | Est. Loss: {alert['estimated_loss_m3']} m³", className="text-muted"),
        ])
    ], className="mb-2", style={"borderLeft": f"4px solid {colors.get(alert['severity'], COLORS['warning'])}"})

def create_gauge(value, title):
    color = COLORS['success'] if value < 20 else COLORS['warning'] if value < 30 else COLORS['danger']
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [0, 50]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 20], 'color': '#E8F5E9'},
                {'range': [20, 30], 'color': '#FFF3E0'},
                {'range': [30, 50], 'color': '#FFEBEE'}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def create_pressure_chart(sensors):
    df = pd.DataFrame(sensors)
    fig = px.bar(df, x='sensor_id', y='pressure_psi', color='status',
                 color_discrete_map={'normal': COLORS['success'], 'anomaly': COLORS['danger']},
                 title='Sensor Pressure Readings')
    fig.add_hline(y=35, line_dash="dash", line_color=COLORS['warning'])
    fig.add_hline(y=55, line_dash="dash", line_color=COLORS['warning'])
    fig.update_layout(height=300, margin=dict(l=40, r=20, t=50, b=40), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def create_trend():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    values = [28 - i*0.3 + random.uniform(-2, 2) for i in range(30)]
    fig = go.Figure(go.Scatter(x=dates, y=values, mode='lines+markers', fill='tozeroy',
                               line=dict(color=COLORS['primary'], width=3)))
    fig.add_hline(y=20, line_dash="dash", line_color=COLORS['success'], annotation_text="Target")
    fig.update_layout(title='NRW Trend - 30 Days', height=300, margin=dict(l=40, r=20, t=50, b=40),
                     paper_bgcolor='rgba(0,0,0,0)')
    return fig

# =============================================================================
# LOGIN PAGE
# =============================================================================

login_page = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-water fa-4x mb-3", style={"color": COLORS['primary']}),
                html.H2("AquaWatch NRW", className="fw-bold mb-1"),
                html.P("Water Intelligence Platform", className="text-muted mb-4"),
                dbc.Card([
                    dbc.CardHeader(html.H5("Admin Login", className="mb-0 text-center")),
                    dbc.CardBody([
                        dbc.Input(type="text", id="username", placeholder="Username", className="mb-3"),
                        dbc.Input(type="password", id="password", placeholder="Password", className="mb-3"),
                        html.Div(id="login-error", className="text-danger mb-3 text-center"),
                        dbc.Button("Login", id="login-btn", color="primary", className="w-100"),
                    ])
                ], className="shadow", style={"borderRadius": "12px"}),
                html.Hr(className="my-4"),
                html.Small("© 2026 AquaWatch NRW", className="text-muted"),
            ], className="text-center", style={"maxWidth": "400px", "margin": "0 auto", "paddingTop": "80px"})
        ])
    ])
], fluid=True, style={"backgroundColor": "#F5F7FA", "minHeight": "100vh"})

# =============================================================================
# DASHBOARD PAGE
# =============================================================================

def dashboard_page():
    stats = get_stats()
    sensors = generate_sensor_data()
    alerts = generate_alerts()
    
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-water fa-2x me-3", style={"color": COLORS['primary']}),
                        html.Div([
                            html.H2("AquaWatch NRW", className="mb-0 fw-bold"),
                            html.Small("Water Intelligence Platform", className="text-muted"),
                        ]),
                    ], className="d-flex align-items-center"),
                    html.Div([
                        dbc.Badge("LIVE", color="success", className="me-2"),
                        html.Small(datetime.now().strftime('%H:%M:%S'), className="text-muted me-3"),
                        dbc.Button([html.I(className="fas fa-sign-out-alt me-1"), "Logout"], 
                                  id="logout-btn", color="outline-secondary", size="sm"),
                    ], className="d-flex align-items-center"),
                ], className="d-flex justify-content-between align-items-center py-3"),
            ])
        ], className="mb-4"),
        
        # Stats
        dbc.Row([
            dbc.Col(stat_card("Active Sensors", f"{stats['sensors_online']}/247", "fa-broadcast-tower", COLORS['primary']), md=3, className="mb-3"),
            dbc.Col(stat_card("NRW Rate", f"{stats['nrw_percentage']}%", "fa-tint-slash", COLORS['warning'] if stats['nrw_percentage'] > 20 else COLORS['success'], "Target: <20%"), md=3, className="mb-3"),
            dbc.Col(stat_card("Water Saved", f"{stats['water_saved']:,.0f} m³", "fa-hand-holding-water", COLORS['success']), md=3, className="mb-3"),
            dbc.Col(stat_card("Active Alerts", str(stats['active_alerts']), "fa-bell", COLORS['danger'] if stats['active_alerts'] > 5 else COLORS['warning']), md=3, className="mb-3"),
        ]),
        
        # Charts
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_gauge(stats['nrw_percentage'], "NRW Rate"), config={'displayModeBar': False})), className="shadow-sm", style={"borderRadius": "12px"}), md=4, className="mb-4"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_pressure_chart(sensors), config={'displayModeBar': False})), className="shadow-sm", style={"borderRadius": "12px"}), md=8, className="mb-4"),
        ]),
        
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_trend(), config={'displayModeBar': False})), className="shadow-sm", style={"borderRadius": "12px"}), md=8, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-bell me-2"), "Active Alerts"]),
                    dbc.CardBody([alert_card(a) for a in alerts] if alerts else html.P("No alerts", className="text-muted"))
                ], className="shadow-sm", style={"borderRadius": "12px"})
            ], md=4, className="mb-4"),
        ]),
        
        # Footer
        html.Hr(),
        html.Div(html.Small("© 2026 AquaWatch NRW | Powered by AI", className="text-muted"), className="text-center py-3"),
        
        dcc.Interval(id='refresh', interval=30000, n_intervals=0),
    ], fluid=True, style={"backgroundColor": "#F5F7FA", "minHeight": "100vh", "padding": "20px"})

# =============================================================================
# LAYOUT
# =============================================================================

app.layout = html.Div([
    dcc.Location(id='url'),
    dcc.Store(id='auth', storage_type='session'),
    html.Div(id='content')
])

# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output('content', 'children'),
    Output('auth', 'data'),
    Input('url', 'pathname'),
    Input('login-btn', 'n_clicks'),
    Input('logout-btn', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    State('auth', 'data'),
    prevent_initial_call=False
)
def router(path, login_click, logout_click, user, pwd, auth):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if trigger == 'logout-btn':
        return login_page, None
    
    if trigger == 'login-btn' and user and pwd:
        if verify_login(user, pwd):
            return dashboard_page(), {'user': user}
    
    if auth and auth.get('user'):
        return dashboard_page(), auth
    
    return login_page, None

@callback(
    Output('login-error', 'children'),
    Input('login-btn', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    prevent_initial_call=True
)
def login_error(n, user, pwd):
    if n and user and pwd and not verify_login(user, pwd):
        return "Invalid credentials"
    return ""

# For Vercel - this is the handler
if __name__ == "__main__":
    app.run_server(debug=True)
