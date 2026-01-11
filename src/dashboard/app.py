"""
AquaWatch NRW - Dashboard Application
=====================================

Three-tier dashboard system:
1. National/Ministry level - Strategic overview
2. Utility Operations level - Operational management  
3. Field Technician level - Mobile-optimized work orders

Design Principles:
- Clarity over aesthetics
- Traffic-light indicators (red/yellow/green)
- Minimal cognitive load
- Mobile-responsive for field use

NOW CONNECTED TO REAL API DATA!
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import os

# API Configuration
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:5000")


# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Expose Flask server for Gunicorn (Render deployment)
server = app.server

app.title = "AquaWatch NRW - Water Intelligence Platform"


# =============================================================================
# API DATA FETCHERS - Connect to Real Backend
# =============================================================================

def fetch_from_api(endpoint: str, default=None):
    """Fetch data from the integrated API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API fetch error: {e}")
    return default


def fetch_sensor_data() -> Dict:
    """Fetch real-time sensor data from API."""
    return fetch_from_api("/api/sensor", {})


def fetch_alerts() -> List:
    """Fetch active alerts from API."""
    return fetch_from_api("/api/alerts", [])


def fetch_history(pipe_id: str = None, limit: int = 500) -> List:
    """Fetch sensor history from API."""
    url = f"/api/history?limit={limit}"
    if pipe_id:
        url += f"&pipe_id={pipe_id}"
    return fetch_from_api(url, [])


def fetch_system_status() -> Dict:
    """Fetch system status from API."""
    return fetch_from_api("/api/status", {})


# =============================================================================
# DATA PROCESSORS - Transform API data for display
# =============================================================================

def get_dma_data() -> pd.DataFrame:
    """Get DMA-level data from API or generate sample if unavailable."""
    sensors = fetch_sensor_data()
    
    if not sensors:
        return generate_sample_dma_data()
    
    # Group sensors by location (DMA)
    dma_stats = {}
    for pipe_id, info in sensors.items():
        loc = info.get("location", "Unknown")
        if loc not in dma_stats:
            dma_stats[loc] = {
                "sensors": 0, "alerts": 0, "total_pressure": 0,
                "leak_count": 0, "warning_count": 0
            }
        
        dma_stats[loc]["sensors"] += 1
        dma_stats[loc]["total_pressure"] += info.get("pressure", 0)
        
        status = info.get("status", "normal")
        if status == "leak":
            dma_stats[loc]["leak_count"] += 1
            dma_stats[loc]["alerts"] += 1
        elif status == "warning":
            dma_stats[loc]["warning_count"] += 1
            dma_stats[loc]["alerts"] += 1
    
    # Convert to DataFrame
    dmas = []
    for loc, stats in dma_stats.items():
        # Estimate NRW based on alerts (simplified)
        base_nrw = 20  # Baseline NRW %
        nrw = base_nrw + (stats["leak_count"] * 15) + (stats["warning_count"] * 5)
        nrw = min(nrw, 65)  # Cap at 65%
        
        status = "healthy"
        if stats["leak_count"] > 0:
            status = "critical"
        elif stats["warning_count"] > 0:
            status = "warning"
        
        dmas.append({
            "dma_id": f"DMA-{loc[:3].upper()}-001",
            "name": loc,
            "nrw_percent": nrw,
            "sensors": stats["sensors"],
            "alerts": stats["alerts"],
            "status": status
        })
    
    if not dmas:
        return generate_sample_dma_data()
    
    return pd.DataFrame(dmas)


def get_alerts_data() -> pd.DataFrame:
    """Get alerts from API or generate sample if unavailable."""
    alerts = fetch_alerts()
    
    if not alerts:
        return generate_sample_alerts()
    
    # Convert to DataFrame format expected by dashboard
    df_alerts = []
    for i, alert in enumerate(alerts[:10]):  # Limit to 10
        df_alerts.append({
            "alert_id": alert.get("alert_id", f"ALT-{i:05d}"),
            "timestamp": datetime.fromisoformat(alert["last_update"]) if alert.get("last_update") else datetime.now(),
            "title": f"{'Leak' if alert.get('status') == 'leak' else 'Pressure anomaly'} at {alert.get('pipe_id', 'Unknown')}",
            "severity": alert.get("severity", "medium"),
            "dma_id": alert.get("location", "Unknown"),
            "probability": alert.get("ai_confidence", 0.75),
            "status": "new"
        })
    
    if not df_alerts:
        return generate_sample_alerts()
    
    return pd.DataFrame(df_alerts)


def get_pressure_series(pipe_id: str = None) -> pd.DataFrame:
    """Get pressure time series from API or generate sample."""
    history = fetch_history(pipe_id, limit=500)
    
    if not history or len(history) < 10:
        return generate_sample_pressure_series()
    
    # Convert to DataFrame
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    return df

def generate_sample_dma_data() -> pd.DataFrame:
    """Generate sample DMA-level data for demonstration."""
    
    dmas = [
        {"dma_id": "DMA-KIT-001", "name": "Kitwe Central", "nrw_percent": 28.5, "sensors": 12, "alerts": 2, "status": "warning"},
        {"dma_id": "DMA-KIT-002", "name": "Kitwe North", "nrw_percent": 22.1, "sensors": 8, "alerts": 0, "status": "healthy"},
        {"dma_id": "DMA-KIT-003", "name": "Kitwe South", "nrw_percent": 45.2, "sensors": 10, "alerts": 5, "status": "critical"},
        {"dma_id": "DMA-NDO-001", "name": "Ndola CBD", "nrw_percent": 31.0, "sensors": 15, "alerts": 1, "status": "warning"},
        {"dma_id": "DMA-NDO-002", "name": "Ndola Industrial", "nrw_percent": 18.5, "sensors": 6, "alerts": 0, "status": "healthy"},
        {"dma_id": "DMA-LSK-001", "name": "Lusaka Central", "nrw_percent": 35.8, "sensors": 20, "alerts": 3, "status": "warning"},
        {"dma_id": "DMA-LSK-002", "name": "Lusaka East", "nrw_percent": 52.3, "sensors": 14, "alerts": 7, "status": "critical"},
        {"dma_id": "DMA-LSK-003", "name": "Lusaka West", "nrw_percent": 25.0, "sensors": 11, "alerts": 1, "status": "warning"},
    ]
    
    return pd.DataFrame(dmas)


def generate_sample_alerts() -> pd.DataFrame:
    """Generate sample alert data."""
    
    alerts = []
    base_time = datetime.now()
    
    alert_types = [
        ("Pressure anomaly detected", "high", "DMA-KIT-003"),
        ("Night pressure drop", "critical", "DMA-LSK-002"),
        ("Gradient increase", "medium", "DMA-KIT-001"),
        ("MNF deviation", "high", "DMA-LSK-001"),
        ("Sustained pressure drop", "critical", "DMA-LSK-002"),
    ]
    
    for i, (title, severity, dma) in enumerate(alert_types):
        alerts.append({
            "alert_id": f"ALT-2026-{1000+i:05d}",
            "timestamp": base_time - timedelta(hours=i*3),
            "title": title,
            "severity": severity,
            "dma_id": dma,
            "probability": np.random.uniform(0.6, 0.95),
            "status": "new" if i < 2 else "acknowledged"
        })
    
    return pd.DataFrame(alerts)


def generate_sample_pressure_series() -> pd.DataFrame:
    """Generate sample pressure time series."""
    
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=7),
        end=datetime.now(),
        freq='15min'
    )
    
    # Generate realistic pressure pattern
    hours = np.array([t.hour for t in timestamps])
    
    # Base pressure with diurnal pattern
    base_pressure = 3.5
    diurnal = 0.3 * np.sin(np.pi * (hours - 6) / 12)
    
    # Add noise
    noise = np.random.normal(0, 0.05, len(timestamps))
    
    # Simulate leak starting 2 days ago
    leak_start = datetime.now() - timedelta(days=2)
    leak_effect = np.where(
        timestamps > leak_start,
        -0.15 * (1 - np.exp(-(timestamps - leak_start).total_seconds() / 86400 / 0.5)),
        0
    )
    
    pressure = base_pressure + diurnal + noise + leak_effect
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'pressure': pressure,
        'sensor_id': 'SENSOR_001'
    })


# =============================================================================
# UI COMPONENTS
# =============================================================================

def create_status_indicator(status: str) -> html.Span:
    """Create a colored status indicator."""
    
    colors = {
        "healthy": "success",
        "warning": "warning", 
        "critical": "danger"
    }
    
    icons = {
        "healthy": "✓",
        "warning": "⚠",
        "critical": "✗"
    }
    
    return dbc.Badge(
        icons.get(status, "?"),
        color=colors.get(status, "secondary"),
        className="ms-2"
    )


def create_kpi_card(title: str, value: str, subtitle: str = "", color: str = "primary") -> dbc.Card:
    """Create a KPI summary card."""
    
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H3(value, className=f"text-{color} mb-0"),
            html.Small(subtitle, className="text-muted") if subtitle else None
        ])
    ], className="mb-3 shadow-sm")


def create_alert_card(alert: Dict) -> dbc.Card:
    """Create an alert card for the dashboard."""
    
    severity_colors = {
        "critical": "danger",
        "high": "warning",
        "medium": "info",
        "low": "secondary"
    }
    
    return dbc.Card([
        dbc.CardHeader([
            dbc.Badge(alert['severity'].upper(), color=severity_colors.get(alert['severity'], 'secondary')),
            html.Span(f" {alert['alert_id']}", className="text-muted small ms-2")
        ]),
        dbc.CardBody([
            html.H6(alert['title'], className="card-title"),
            html.P([
                html.Strong("DMA: "), alert['dma_id'],
                html.Br(),
                html.Strong("Probability: "), f"{alert['probability']:.0%}",
                html.Br(),
                html.Strong("Time: "), alert['timestamp'].strftime("%Y-%m-%d %H:%M")
            ], className="card-text small"),
            dbc.Button("View Details", color="primary", size="sm", outline=True)
        ])
    ], className="mb-3 shadow-sm")


# =============================================================================
# DASHBOARD LAYOUTS
# =============================================================================

def create_national_dashboard() -> html.Div:
    """
    National/Ministry Level Dashboard
    
    Shows:
    - Overall NRW statistics
    - Regional comparison
    - Utility performance
    - Budget allocation recommendations
    """
    
    # FETCH REAL DATA FROM API
    dma_data = get_dma_data()
    
    # Calculate national statistics
    total_sensors = dma_data['sensors'].sum()
    total_alerts = dma_data['alerts'].sum()
    avg_nrw = dma_data['nrw_percent'].mean()
    critical_dmas = len(dma_data[dma_data['status'] == 'critical'])
    
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("National Water Intelligence Overview", className="mb-3"),
                html.P("Ministry of Water Development - Decision Support Dashboard", 
                       className="text-muted")
            ])
        ], className="mb-4"),
        
        # KPI Cards
        dbc.Row([
            dbc.Col(create_kpi_card("National NRW", f"{avg_nrw:.1f}%", "Average across all utilities", 
                                   "danger" if avg_nrw > 30 else "warning" if avg_nrw > 20 else "success"), width=3),
            dbc.Col(create_kpi_card("Active Sensors", f"{total_sensors:,}", "Across all DMAs", "primary"), width=3),
            dbc.Col(create_kpi_card("Active Alerts", f"{total_alerts}", "Requiring attention",
                                   "danger" if total_alerts > 5 else "warning" if total_alerts > 0 else "success"), width=3),
            dbc.Col(create_kpi_card("Critical DMAs", f"{critical_dmas}", "Immediate action needed",
                                   "danger" if critical_dmas > 0 else "success"), width=3),
        ], className="mb-4"),
        
        # Charts Row
        dbc.Row([
            # NRW by DMA Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("NRW by District Metered Area"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.bar(
                                dma_data.sort_values('nrw_percent', ascending=True),
                                y='name',
                                x='nrw_percent',
                                orientation='h',
                                color='nrw_percent',
                                color_continuous_scale=['green', 'yellow', 'red'],
                                range_color=[0, 60]
                            ).update_layout(
                                height=400,
                                xaxis_title="NRW (%)",
                                yaxis_title="",
                                showlegend=False,
                                coloraxis_showscale=False
                            ).add_vline(x=25, line_dash="dash", line_color="orange",
                                       annotation_text="Target: 25%")
                        )
                    ])
                ], className="shadow-sm")
            ], width=6),
            
            # Status Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("DMA Status Distribution"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.pie(
                                dma_data.groupby('status').size().reset_index(name='count'),
                                values='count',
                                names='status',
                                color='status',
                                color_discrete_map={
                                    'healthy': 'green',
                                    'warning': 'orange',
                                    'critical': 'red'
                                }
                            ).update_layout(height=400)
                        )
                    ])
                ], className="shadow-sm")
            ], width=6)
        ], className="mb-4"),
        
        # DMA Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("DMA Performance Summary"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("DMA"),
                                    html.Th("NRW %"),
                                    html.Th("Sensors"),
                                    html.Th("Active Alerts"),
                                    html.Th("Status")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(row['name']),
                                    html.Td(f"{row['nrw_percent']:.1f}%"),
                                    html.Td(row['sensors']),
                                    html.Td(row['alerts']),
                                    html.Td(create_status_indicator(row['status']))
                                ]) for _, row in dma_data.iterrows()
                            ])
                        ], striped=True, hover=True, responsive=True)
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])


def create_utility_dashboard() -> html.Div:
    """
    Utility Operations Dashboard
    
    Shows:
    - Real-time DMA status
    - Active alerts and work orders
    - Pressure/flow trends
    - AI confidence indicators
    """
    
    # FETCH REAL DATA FROM API
    alerts_data = get_alerts_data()
    pressure_data = get_pressure_series()
    
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Utility Operations Center", className="mb-3"),
                html.P("Real-time monitoring and alert management", className="text-muted")
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Span("Last Update: ", className="text-muted"),
                    html.Span(datetime.now().strftime("%H:%M:%S"), id="last-update", className="fw-bold")
                ], className="text-end")
            ], width=4)
        ], className="mb-4"),
        
        # Alert Summary and Quick Stats
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Strong("Active Alerts"),
                        dbc.Badge(str(len(alerts_data)), color="danger", className="ms-2")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            create_alert_card(alert.to_dict()) 
                            for _, alert in alerts_data.head(3).iterrows()
                        ], style={"maxHeight": "500px", "overflowY": "auto"})
                    ])
                ], className="shadow-sm h-100")
            ], width=4),
            
            # Pressure Trend
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Pressure Trend - Selected Sensor"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(
                                    x=pressure_data['timestamp'],
                                    y=pressure_data['pressure'],
                                    mode='lines',
                                    name='Pressure',
                                    line=dict(color='#2196F3', width=1.5)
                                ),
                                # Add threshold lines
                                go.Scatter(
                                    x=[pressure_data['timestamp'].min(), pressure_data['timestamp'].max()],
                                    y=[3.0, 3.0],
                                    mode='lines',
                                    name='Min Threshold',
                                    line=dict(color='red', dash='dash', width=1)
                                )
                            ]).update_layout(
                                height=300,
                                margin=dict(l=50, r=20, t=30, b=50),
                                xaxis_title="Time",
                                yaxis_title="Pressure (bar)",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                                # Highlight anomaly region
                                shapes=[
                                    dict(
                                        type="rect",
                                        xref="x",
                                        yref="paper",
                                        x0=datetime.now() - timedelta(days=2),
                                        x1=datetime.now(),
                                        y0=0,
                                        y1=1,
                                        fillcolor="rgba(255,0,0,0.1)",
                                        line=dict(width=0)
                                    )
                                ],
                                annotations=[
                                    dict(
                                        x=datetime.now() - timedelta(days=1),
                                        y=3.5,
                                        text="Anomaly Period",
                                        showarrow=True,
                                        arrowhead=2
                                    )
                                ]
                            )
                        )
                    ])
                ], className="shadow-sm")
            ], width=8)
        ], className="mb-4"),
        
        # AI Analysis Panel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("AI Analysis - Current Assessment"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Leak Probability", className="text-muted"),
                                html.Div([
                                    dbc.Progress(
                                        value=78,
                                        color="danger",
                                        striped=True,
                                        animated=True,
                                        className="mb-2",
                                        style={"height": "25px"}
                                    ),
                                    html.Span("78%", className="h4 text-danger")
                                ])
                            ], width=4),
                            dbc.Col([
                                html.H6("Model Confidence", className="text-muted"),
                                html.Div([
                                    dbc.Progress(
                                        value=85,
                                        color="success",
                                        className="mb-2",
                                        style={"height": "25px"}
                                    ),
                                    html.Span("85%", className="h4 text-success")
                                ])
                            ], width=4),
                            dbc.Col([
                                html.H6("Estimated Loss", className="text-muted"),
                                html.H4("~75 m³/day", className="text-warning")
                            ], width=4)
                        ]),
                        html.Hr(),
                        html.H6("Key Evidence:", className="mt-3 mb-2"),
                        html.Ul([
                            html.Li("Night pressure 0.15 bar below normal"),
                            html.Li("Night/day ratio: 0.94 (threshold: 0.98)"),
                            html.Li("Gradient to downstream sensor increased 20%")
                        ], className="small")
                    ])
                ], className="shadow-sm")
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recommended Actions"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                dbc.Badge("1", color="danger", className="me-2"),
                                "Deploy acoustic logger at valve V-1234",
                                dbc.Button("Create Work Order", color="primary", size="sm", 
                                          className="float-end")
                            ]),
                            dbc.ListGroupItem([
                                dbc.Badge("2", color="warning", className="me-2"),
                                "Check pressure at hydrant H-567"
                            ]),
                            dbc.ListGroupItem([
                                dbc.Badge("3", color="info", className="me-2"),
                                "Visual inspection of pipe section near school"
                            ])
                        ], flush=True)
                    ])
                ], className="shadow-sm")
            ], width=6)
        ])
    ])


def create_field_dashboard() -> html.Div:
    """
    Field Technician Dashboard (Mobile-Optimized)
    
    Shows:
    - Active work orders
    - Navigation to inspection points
    - Data entry for observations
    - Photo upload
    """
    
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H4("Field Operations", className="mb-2"),
                html.P("Work Orders & Inspections", className="text-muted small")
            ])
        ], className="mb-3"),
        
        # Active Work Order Card (Mobile-optimized)
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        dbc.Badge("HIGH PRIORITY", color="danger"),
                        html.Span(" WO-2026-00123", className="fw-bold ms-2")
                    ], width=8),
                    dbc.Col([
                        html.Small("2 hrs ago", className="text-muted")
                    ], width=4, className="text-end")
                ])
            ]),
            dbc.CardBody([
                html.H5("Leak Investigation - Kafue Road", className="mb-3"),
                
                # Location
                dbc.Row([
                    dbc.Col([
                        html.I(className="fas fa-map-marker-alt me-2"),
                        html.Strong("Location:")
                    ], width=4),
                    dbc.Col([
                        "Between pump station and school",
                        html.Br(),
                        html.Small("-15.4123, 28.2876", className="text-muted")
                    ], width=8)
                ], className="mb-2"),
                
                # DMA
                dbc.Row([
                    dbc.Col([
                        html.I(className="fas fa-water me-2"),
                        html.Strong("DMA:")
                    ], width=4),
                    dbc.Col("DMA-KIT-015", width=8)
                ], className="mb-2"),
                
                # AI Summary
                dbc.Row([
                    dbc.Col([
                        html.I(className="fas fa-brain me-2"),
                        html.Strong("AI Confidence:")
                    ], width=4),
                    dbc.Col([
                        dbc.Badge("78%", color="warning", className="me-2"),
                        html.Small("~75 m³/day estimated loss")
                    ], width=8)
                ], className="mb-3"),
                
                html.Hr(),
                
                # Instructions
                html.H6("Instructions:", className="mb-2"),
                html.Ol([
                    html.Li("Check visible pipe sections for wet spots"),
                    html.Li("Listen at valve V-1234 with acoustic stick"),
                    html.Li("Take pressure reading at hydrant H-567"),
                    html.Li("Document findings with photos")
                ], className="small"),
                
                html.Hr(),
                
                # Action Buttons
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-directions me-2"),
                            "Navigate"
                        ], color="primary", className="w-100 mb-2")
                    ], width=6),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-phone me-2"),
                            "Call Control"
                        ], color="secondary", outline=True, className="w-100 mb-2")
                    ], width=6)
                ])
            ])
        ], className="shadow-sm mb-3"),
        
        # Quick Entry Form
        dbc.Card([
            dbc.CardHeader("Report Findings"),
            dbc.CardBody([
                dbc.Label("Leak Found?"),
                dbc.RadioItems(
                    options=[
                        {"label": "Yes - Leak Confirmed", "value": "yes"},
                        {"label": "No - Area Clear", "value": "no"},
                        {"label": "Inconclusive - Need More Investigation", "value": "maybe"}
                    ],
                    id="leak-found-radio",
                    className="mb-3"
                ),
                
                dbc.Label("Notes"),
                dbc.Textarea(
                    placeholder="Describe what you found...",
                    className="mb-3",
                    style={"height": "100px"}
                ),
                
                dbc.Label("Photo Evidence"),
                dcc.Upload(
                    id="photo-upload",
                    children=dbc.Button([
                        html.I(className="fas fa-camera me-2"),
                        "Take Photo"
                    ], color="secondary", outline=True, className="w-100"),
                    className="mb-3"
                ),
                
                dbc.Button([
                    html.I(className="fas fa-check me-2"),
                    "Submit Report"
                ], color="success", className="w-100")
            ])
        ], className="shadow-sm")
    ])


# =============================================================================
# MAIN APP LAYOUT
# =============================================================================

app.layout = html.Div([
    # Navigation Bar
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand([
                html.I(className="fas fa-water me-2"),
                "AquaWatch NRW"
            ], href="/"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("National", href="/national", id="nav-national")),
                    dbc.NavItem(dbc.NavLink("Operations", href="/operations", id="nav-operations")),
                    dbc.NavItem(dbc.NavLink("Field", href="/field", id="nav-field")),
                ], navbar=True),
                id="navbar-collapse",
                navbar=True
            )
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    ),
    
    # URL for routing
    dcc.Location(id='url', refresh=False),
    
    # Main content
    dbc.Container(
        id='page-content',
        fluid=True,
        className="px-4"
    ),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 60 seconds
        n_intervals=0
    )
])


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route to appropriate dashboard based on URL."""
    
    if pathname == '/operations':
        return create_utility_dashboard()
    elif pathname == '/field':
        return create_field_dashboard()
    else:
        return create_national_dashboard()


@app.callback(
    [Output('nav-national', 'active'),
     Output('nav-operations', 'active'),
     Output('nav-field', 'active')],
    Input('url', 'pathname')
)
def update_nav_active(pathname):
    """Update navigation active states."""
    
    return (
        pathname == '/' or pathname == '/national',
        pathname == '/operations',
        pathname == '/field'
    )


# =============================================================================
# RUN SERVER
# =============================================================================

def run_dashboard(debug: bool = True, port: int = 8050):
    """Start the dashboard server."""
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                 AquaWatch NRW Dashboard                 ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                          ║
    ║  Dashboard URLs:                                         ║
    ║  • National:   http://localhost:{port}/national          ║
    ║  • Operations: http://localhost:{port}/operations        ║
    ║  • Field:      http://localhost:{port}/field             ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=debug, port=port)


if __name__ == '__main__':
    run_dashboard()
