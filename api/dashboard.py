"""
AquaWatch NRW - Vercel Dashboard
================================
Full dashboard deployment for Vercel serverless
"""

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# =============================================================================
# SIMULATED DATA (Serverless - no persistent state)
# =============================================================================

def generate_sensor_data():
    """Generate realistic sensor data."""
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
            "pipe_id": f"PIPE-{zone.split()[0]}-{i+1:02d}",
            "zone": zone,
            "pressure_psi": round(base_pressure, 2),
            "flow_rate_gpm": round(100 + random.uniform(-20, 20), 2),
            "acoustic_level_db": round(25 + random.uniform(-5, 15), 1),
            "temperature_c": round(22 + random.uniform(-3, 3), 1),
            "battery_level": round(random.uniform(60, 100), 1),
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
        if random.random() < 0.7:
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
    }


# =============================================================================
# STYLES
# =============================================================================

COLORS = {
    'primary': '#0066CC',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'info': '#17A2B8',
    'dark': '#1a1a2e',
    'light': '#F8F9FA',
    'card_bg': '#FFFFFF',
    'text': '#212529',
    'text_muted': '#6C757D',
    'border': '#DEE2E6',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2',
}

# =============================================================================
# DASHBOARD APP
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    requests_pathname_prefix='/'
)

app.title = "AquaWatch NRW - Water Intelligence Platform"
server = app.server


def create_stat_card(title, value, icon, color, subtitle=""):
    """Create a statistics card."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon} fa-2x", style={"color": color}),
                ], className="me-3"),
                html.Div([
                    html.H6(title, className="text-muted mb-1", style={"fontSize": "0.85rem"}),
                    html.H3(value, className="mb-0 fw-bold", style={"color": COLORS['text']}),
                    html.Small(subtitle, className="text-muted") if subtitle else None,
                ]),
            ], className="d-flex align-items-center"),
        ])
    ], className="shadow-sm h-100", style={"borderRadius": "12px", "border": "none"})


def create_alert_card(alert):
    """Create an alert card."""
    severity_colors = {
        "critical": COLORS['danger'],
        "warning": COLORS['warning'],
        "info": COLORS['info']
    }
    severity_icons = {
        "critical": "fa-exclamation-circle",
        "warning": "fa-exclamation-triangle",
        "info": "fa-info-circle"
    }
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"fas {severity_icons.get(alert['severity'], 'fa-bell')} me-2",
                    style={"color": severity_colors.get(alert['severity'], COLORS['info'])}
                ),
                html.Strong(alert['title']),
                dbc.Badge(
                    alert['severity'].upper(),
                    color="danger" if alert['severity'] == "critical" else "warning" if alert['severity'] == "warning" else "info",
                    className="ms-2"
                ),
            ], className="d-flex align-items-center mb-2"),
            html.Div([
                html.Small([
                    html.I(className="fas fa-map-marker-alt me-1"),
                    alert['zone']
                ], className="text-muted me-3"),
                html.Small([
                    html.I(className="fas fa-tint me-1"),
                    f"Est. Loss: {alert['estimated_loss_m3']} m³"
                ], className="text-muted"),
            ]),
        ])
    ], className="mb-2 shadow-sm", style={
        "borderLeft": f"4px solid {severity_colors.get(alert['severity'], COLORS['info'])}",
        "borderRadius": "8px"
    })


def create_gauge_chart(value, title, max_val=100, threshold_good=20, threshold_warn=30):
    """Create a gauge chart for NRW percentage."""
    color = COLORS['success'] if value < threshold_good else COLORS['warning'] if value < threshold_warn else COLORS['danger']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': COLORS['text']}},
        delta={'reference': threshold_good, 'increasing': {'color': COLORS['danger']}, 'decreasing': {'color': COLORS['success']}},
        gauge={
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': COLORS['text']},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': COLORS['border'],
            'steps': [
                {'range': [0, threshold_good], 'color': '#E8F5E9'},
                {'range': [threshold_good, threshold_warn], 'color': '#FFF3E0'},
                {'range': [threshold_warn, max_val], 'color': '#FFEBEE'}
            ],
            'threshold': {
                'line': {'color': COLORS['danger'], 'width': 4},
                'thickness': 0.75,
                'value': threshold_warn
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_pressure_chart(sensors):
    """Create pressure distribution chart."""
    df = pd.DataFrame(sensors)
    
    fig = px.bar(
        df,
        x='sensor_id',
        y='pressure_psi',
        color='status',
        color_discrete_map={'normal': COLORS['success'], 'anomaly': COLORS['danger']},
        title='Sensor Pressure Readings'
    )
    
    fig.add_hline(y=35, line_dash="dash", line_color=COLORS['warning'], annotation_text="Min Threshold")
    fig.add_hline(y=55, line_dash="dash", line_color=COLORS['warning'], annotation_text="Max Threshold")
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_zone_chart(sensors):
    """Create zone performance pie chart."""
    df = pd.DataFrame(sensors)
    zone_stats = df.groupby('zone').agg({
        'anomaly_score': 'mean',
        'sensor_id': 'count'
    }).reset_index()
    zone_stats.columns = ['zone', 'avg_anomaly', 'sensor_count']
    
    fig = px.pie(
        zone_stats,
        values='sensor_count',
        names='zone',
        title='Sensors by Zone',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_trend_chart():
    """Create NRW trend chart."""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    nrw_values = [28 - i*0.3 + random.uniform(-2, 2) for i in range(30)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=nrw_values,
        mode='lines+markers',
        name='NRW %',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(0, 102, 204, 0.1)'
    ))
    
    fig.add_hline(y=20, line_dash="dash", line_color=COLORS['success'], annotation_text="Target (20%)")
    
    fig.update_layout(
        title='NRW Trend - Last 30 Days',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title='Date',
        yaxis_title='NRW %',
        showlegend=False
    )
    
    return fig


# =============================================================================
# LAYOUT
# =============================================================================

def serve_layout():
    """Generate layout with fresh data."""
    stats = get_system_stats()
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
                            html.H2("AquaWatch NRW", className="mb-0 fw-bold", style={"color": COLORS['dark']}),
                            html.Small("Water Intelligence Platform", className="text-muted"),
                        ]),
                    ], className="d-flex align-items-center"),
                    html.Div([
                        dbc.Badge("LIVE", color="success", className="me-2 pulse-badge"),
                        html.Small(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", className="text-muted"),
                    ], className="d-flex align-items-center"),
                ], className="d-flex justify-content-between align-items-center py-3"),
            ])
        ], className="mb-4"),
        
        # Stats Row
        dbc.Row([
            dbc.Col([
                create_stat_card(
                    "Active Sensors",
                    f"{stats['sensors_online']}/{stats['total_sensors']}",
                    "fa-broadcast-tower",
                    COLORS['primary'],
                    f"{stats['sensors_offline']} offline"
                )
            ], md=3, sm=6, className="mb-3"),
            dbc.Col([
                create_stat_card(
                    "NRW Rate",
                    f"{stats['nrw_percentage']}%",
                    "fa-tint-slash",
                    COLORS['warning'] if stats['nrw_percentage'] > 20 else COLORS['success'],
                    "Target: <20%"
                )
            ], md=3, sm=6, className="mb-3"),
            dbc.Col([
                create_stat_card(
                    "Water Saved Today",
                    f"{stats['water_saved_m3_today']:,.0f} m³",
                    "fa-hand-holding-water",
                    COLORS['success'],
                    "Through leak detection"
                )
            ], md=3, sm=6, className="mb-3"),
            dbc.Col([
                create_stat_card(
                    "Active Alerts",
                    str(stats['active_alerts']),
                    "fa-bell",
                    COLORS['danger'] if stats['active_alerts'] > 5 else COLORS['warning'],
                    f"{stats['leaks_detected_today']} leaks today"
                )
            ], md=3, sm=6, className="mb-3"),
        ]),
        
        # Charts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_gauge_chart(stats['nrw_percentage'], "Current NRW Rate"),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm h-100", style={"borderRadius": "12px", "border": "none"})
            ], md=4, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_pressure_chart(sensors),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm h-100", style={"borderRadius": "12px", "border": "none"})
            ], md=8, className="mb-4"),
        ]),
        
        # Second Charts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_trend_chart(),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm h-100", style={"borderRadius": "12px", "border": "none"})
            ], md=8, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=create_zone_chart(sensors),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm h-100", style={"borderRadius": "12px", "border": "none"})
            ], md=4, className="mb-4"),
        ]),
        
        # Alerts Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-bell me-2", style={"color": COLORS['danger']}),
                            html.H5("Active Alerts", className="mb-0 d-inline"),
                        ]),
                    ], style={"backgroundColor": COLORS['light'], "borderBottom": f"2px solid {COLORS['border']}"}),
                    dbc.CardBody([
                        html.Div([create_alert_card(alert) for alert in alerts]) if alerts else html.P("No active alerts", className="text-muted text-center")
                    ], style={"maxHeight": "400px", "overflowY": "auto"})
                ], className="shadow-sm", style={"borderRadius": "12px", "border": "none"})
            ], md=6, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-robot me-2", style={"color": COLORS['primary']}),
                            html.H5("AI System Status", className="mb-0 d-inline"),
                        ]),
                    ], style={"backgroundColor": COLORS['light'], "borderBottom": f"2px solid {COLORS['border']}"}),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-brain me-2", style={"color": COLORS['success']}),
                                    "Anomaly Detection Model"
                                ], className="d-flex align-items-center"),
                                dbc.Badge("Online", color="success")
                            ], className="d-flex justify-content-between align-items-center"),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-map-marked-alt me-2", style={"color": COLORS['success']}),
                                    "Leak Localization"
                                ], className="d-flex align-items-center"),
                                dbc.Badge("Online", color="success")
                            ], className="d-flex justify-content-between align-items-center"),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-volume-up me-2", style={"color": COLORS['success']}),
                                    "Acoustic Analysis"
                                ], className="d-flex align-items-center"),
                                dbc.Badge("Online", color="success")
                            ], className="d-flex justify-content-between align-items-center"),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-chart-line me-2", style={"color": COLORS['primary']}),
                                    f"AI Confidence: {stats['ai_confidence']}%"
                                ], className="d-flex align-items-center"),
                                dbc.Badge("High", color="primary")
                            ], className="d-flex justify-content-between align-items-center"),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-server me-2", style={"color": COLORS['success']}),
                                    f"System Uptime: {stats['system_uptime']}"
                                ], className="d-flex align-items-center"),
                                dbc.Badge("Healthy", color="success")
                            ], className="d-flex justify-content-between align-items-center"),
                        ], flush=True)
                    ])
                ], className="shadow-sm", style={"borderRadius": "12px", "border": "none"})
            ], md=6, className="mb-4"),
        ]),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.Div([
                    html.Small([
                        "© 2026 AquaWatch NRW | ",
                        html.A("API Status", href="/api", className="text-decoration-none"),
                        " | Powered by AI"
                    ], className="text-muted")
                ], className="text-center py-3")
            ])
        ]),
        
        # Auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 seconds
            n_intervals=0
        )
        
    ], fluid=True, style={"backgroundColor": "#F5F7FA", "minHeight": "100vh", "padding": "20px"})


app.layout = serve_layout


# Callback for auto-refresh (regenerates layout)
@callback(
    Output('interval-component', 'interval'),
    Input('interval-component', 'n_intervals')
)
def update_data(n):
    return 30*1000


# =============================================================================
# CUSTOM CSS
# =============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .pulse-badge {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .card:hover {
                transform: translateY(-2px);
                transition: transform 0.2s ease-in-out;
            }
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# For Vercel serverless
if __name__ == "__main__":
    app.run_server(debug=True)
