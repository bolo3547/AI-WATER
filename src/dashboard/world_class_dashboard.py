"""
AquaWatch World-Class Dashboard
================================
Unified dashboard integrating all advanced features inspired by global leaders:
- TaKaDu (Israel) - Central Event Management
- Xylem (USA) - Digital Twin & Advanced Analytics
- Huawei/Alibaba (China) - Smart Infrastructure & AI

Features:
- Executive Command Center
- Real-time Network Digital Twin
- AI-Powered Event Management
- Predictive Analytics Suite
- Asset Health & Risk Dashboard
- Customer Insights Portal
- Performance Benchmarking
- Mobile-Ready Responsive Design
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import our advanced modules
try:
    from src.digital_twin.network_twin import get_digital_twin
    from src.events.event_management import get_event_manager
    from src.acoustic.advanced_acoustic import get_acoustic_system
    from src.ami.smart_meter_integration import get_ami_system
    from src.pressure.dynamic_pressure import get_pressure_manager
    from src.maintenance.predictive_maintenance import get_maintenance_system
    from src.benchmarking.utility_benchmarking import get_benchmarking_engine
    from src.customer.self_service_portal import get_customer_portal
    from src.assets.health_scoring import get_asset_health_system
except ImportError:
    # Fallback for standalone testing
    pass


# Color scheme inspired by premium water utility dashboards
COLORS = {
    'primary': '#0066CC',
    'secondary': '#00A3E0',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'info': '#17A2B8',
    'dark': '#1A1A2E',
    'light': '#F8F9FA',
    'water_blue': '#0077B6',
    'deep_blue': '#023E8A',
    'accent': '#00B4D8',
    'background': '#0F0F23',
    'card_bg': '#16213E',
    'text': '#E8E8E8',
    'muted': '#6C757D'
}

# Custom CSS for world-class appearance
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0F0F23 0%, #1A1A2E 100%);
    color: #E8E8E8;
}

.metric-card {
    background: linear-gradient(145deg, #16213E 0%, #1A1A2E 100%);
    border-radius: 16px;
    border: 1px solid rgba(0, 163, 224, 0.2);
    padding: 20px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.metric-card:hover {
    transform: translateY(-5px);
    border-color: rgba(0, 163, 224, 0.5);
    box-shadow: 0 8px 30px rgba(0, 163, 224, 0.2);
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00A3E0, #0066CC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #00A3E0;
    border-left: 4px solid #00A3E0;
    padding-left: 12px;
    margin-bottom: 20px;
}

.nav-tab {
    background: transparent;
    border: none;
    color: #6C757D;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s;
}

.nav-tab.active {
    background: rgba(0, 163, 224, 0.2);
    color: #00A3E0;
}

.alert-critical {
    background: linear-gradient(90deg, rgba(220, 53, 69, 0.2), transparent);
    border-left: 4px solid #DC3545;
}

.alert-warning {
    background: linear-gradient(90deg, rgba(255, 193, 7, 0.2), transparent);
    border-left: 4px solid #FFC107;
}

.health-excellent { color: #28A745; }
.health-good { color: #20C997; }
.health-fair { color: #FFC107; }
.health-poor { color: #FD7E14; }
.health-critical { color: #DC3545; }

.live-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #28A745;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
"""


def create_kpi_card(title, value, unit, trend=None, trend_value=None, icon=None, color=COLORS['primary']):
    """Create a premium KPI card"""
    trend_icon = "↑" if trend == "up" else "↓" if trend == "down" else "→"
    trend_color = COLORS['success'] if trend == "up" else COLORS['danger'] if trend == "down" else COLORS['muted']
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas {icon} fa-2x", style={'color': color, 'opacity': 0.7}) if icon else None,
                html.Span(title, className="text-muted ms-2", style={'fontSize': '0.9rem'})
            ], className="d-flex align-items-center mb-2"),
            html.Div([
                html.Span(f"{value}", style={
                    'fontSize': '2rem',
                    'fontWeight': '700',
                    'color': color
                }),
                html.Span(f" {unit}", style={'fontSize': '1rem', 'color': COLORS['muted']})
            ]),
            html.Div([
                html.Span(trend_icon, style={'color': trend_color}),
                html.Span(f" {trend_value}", style={'color': trend_color, 'fontSize': '0.85rem'})
            ], className="mt-2") if trend_value else None
        ])
    ], className="metric-card h-100")


def create_gauge_chart(value, max_value, title, thresholds=None):
    """Create a premium gauge chart"""
    if thresholds is None:
        thresholds = {'green': 30, 'yellow': 50, 'red': 100}
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14, 'color': COLORS['text']}},
        number={'font': {'size': 36, 'color': COLORS['text']}},
        gauge={
            'axis': {'range': [0, max_value], 'tickcolor': COLORS['text']},
            'bar': {'color': COLORS['primary']},
            'bgcolor': COLORS['card_bg'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, thresholds['green']], 'color': 'rgba(40, 167, 69, 0.3)'},
                {'range': [thresholds['green'], thresholds['yellow']], 'color': 'rgba(255, 193, 7, 0.3)'},
                {'range': [thresholds['yellow'], max_value], 'color': 'rgba(220, 53, 69, 0.3)'}
            ],
            'threshold': {
                'line': {'color': COLORS['danger'], 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text']},
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_network_map():
    """Create interactive network map with digital twin data"""
    # Lusaka network nodes
    nodes = [
        {"name": "Iolanda WTP", "lat": -15.3847, "lon": 28.3228, "type": "treatment", "status": "operational"},
        {"name": "Chelstone Reservoir", "lat": -15.3600, "lon": 28.3500, "type": "reservoir", "status": "operational"},
        {"name": "CBD Tank", "lat": -15.4167, "lon": 28.2833, "type": "tank", "status": "operational"},
        {"name": "Kabulonga Tank", "lat": -15.4100, "lon": 28.3100, "type": "tank", "status": "warning"},
        {"name": "Matero Booster", "lat": -15.3900, "lon": 28.2500, "type": "pump", "status": "operational"},
        {"name": "Woodlands PRV", "lat": -15.4000, "lon": 28.3200, "type": "prv", "status": "operational"},
        {"name": "Leak Detected", "lat": -15.4050, "lon": 28.2900, "type": "leak", "status": "critical"},
    ]
    
    # Color mapping
    status_colors = {
        "operational": COLORS['success'],
        "warning": COLORS['warning'],
        "critical": COLORS['danger']
    }
    
    fig = go.Figure()
    
    # Add nodes
    for node in nodes:
        fig.add_trace(go.Scattermap(
            lat=[node["lat"]],
            lon=[node["lon"]],
            mode='markers+text',
            marker=dict(
                size=20 if node["type"] == "leak" else 14,
                color=status_colors.get(node["status"], COLORS['primary'])
            ),
            text=[node["name"]],
            textposition="top center",
            name=node["name"],
            hovertemplate=f"<b>{node['name']}</b><br>Status: {node['status']}<extra></extra>"
        ))
    
    # Add pipe connections (simplified)
    pipe_lats = [-15.3847, -15.3600, -15.4167, -15.4100, None, -15.4167, -15.3900]
    pipe_lons = [28.3228, 28.3500, 28.2833, 28.3100, None, 28.2833, 28.2500]
    
    fig.add_trace(go.Scattermap(
        lat=pipe_lats,
        lon=pipe_lons,
        mode='lines',
        line=dict(width=3, color=COLORS['primary']),
        name='Transmission Mains',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=-15.4000, lon=28.3000),
            zoom=11
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        showlegend=False
    )
    
    return fig


def create_event_timeline():
    """Create event timeline visualization"""
    events = [
        {"time": "10:45", "type": "Leak", "location": "Kabulonga Zone", "severity": "high", "status": "active"},
        {"time": "09:30", "type": "Pressure Drop", "location": "CBD Main", "severity": "medium", "status": "investigating"},
        {"time": "08:15", "type": "Meter Anomaly", "location": "Industrial Zone", "severity": "low", "status": "resolved"},
        {"time": "07:00", "type": "Burst", "location": "Matero", "severity": "critical", "status": "active"},
        {"time": "Yesterday", "type": "NRW Alert", "location": "DMA-05", "severity": "medium", "status": "resolved"},
    ]
    
    severity_colors = {
        "critical": COLORS['danger'],
        "high": "#FD7E14",
        "medium": COLORS['warning'],
        "low": COLORS['info']
    }
    
    timeline_items = []
    for event in events:
        timeline_items.append(
            html.Div([
                html.Div([
                    html.Span(event["time"], className="text-muted", style={'fontSize': '0.8rem'}),
                    html.Div(style={
                        'width': '12px',
                        'height': '12px',
                        'borderRadius': '50%',
                        'backgroundColor': severity_colors.get(event["severity"], COLORS['info']),
                        'margin': '5px auto'
                    }),
                    html.Div(style={
                        'width': '2px',
                        'height': '40px',
                        'backgroundColor': COLORS['muted'],
                        'margin': '0 auto'
                    })
                ], style={'width': '60px', 'textAlign': 'center'}),
                html.Div([
                    html.Strong(event["type"], style={'color': severity_colors.get(event["severity"])}),
                    html.Br(),
                    html.Small(event["location"], className="text-muted"),
                    dbc.Badge(event["status"].upper(), color="danger" if event["status"] == "active" else "secondary",
                             className="ms-2", style={'fontSize': '0.7rem'})
                ], className="ms-3")
            ], className="d-flex align-items-start mb-2")
        )
    
    return html.Div(timeline_items)


def create_health_distribution_chart():
    """Create asset health distribution chart"""
    categories = ['Excellent', 'Good', 'Fair', 'Poor', 'Critical']
    values = [15, 35, 28, 18, 4]
    colors = [COLORS['success'], '#20C997', COLORS['warning'], '#FD7E14', COLORS['danger']]
    
    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=[f'{v}%' for v in values],
        textposition='inside',
        textfont=dict(color='white', size=12)
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text']},
        height=200,
        margin=dict(l=80, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False)
    )
    
    return fig


def create_nrw_trend_chart():
    """Create NRW trend chart"""
    months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
    nrw_values = [45, 43, 42, 40, 39, 38, 36]
    target = [35] * 7
    
    fig = go.Figure()
    
    # NRW actual
    fig.add_trace(go.Scatter(
        x=months,
        y=nrw_values,
        mode='lines+markers',
        name='NRW %',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(0, 102, 204, 0.2)'
    ))
    
    # Target line
    fig.add_trace(go.Scatter(
        x=months,
        y=target,
        mode='lines',
        name='Target',
        line=dict(color=COLORS['success'], width=2, dash='dash')
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text']},
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_pressure_zones_chart():
    """Create pressure zones performance chart"""
    zones = ['CBD', 'Kabulonga', 'Woodlands', 'Matero', 'Kabwata', 'Industrial']
    current = [4.2, 3.8, 4.0, 3.5, 3.7, 4.5]
    optimal = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Current (bar)',
        x=zones,
        y=current,
        marker_color=COLORS['primary']
    ))
    
    fig.add_trace(go.Scatter(
        name='Optimal',
        x=zones,
        y=optimal,
        mode='lines+markers',
        line=dict(color=COLORS['success'], width=2, dash='dash'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text']},
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Pressure (bar)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        barmode='group'
    )
    
    return fig


def create_benchmark_radar():
    """Create benchmarking radar chart"""
    categories = ['NRW', 'Service<br>Coverage', 'Supply<br>Continuity', 'Collection<br>Efficiency', 
                  'Water<br>Quality', 'Staff<br>Efficiency']
    
    # Normalize scores to 0-100
    lwsc = [58, 78, 67, 82, 96, 70]  # LWSC scores
    regional_avg = [65, 85, 75, 85, 96, 60]  # Regional average
    best_practice = [95, 98, 100, 99, 100, 85]  # Singapore benchmark
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=lwsc + [lwsc[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(0, 102, 204, 0.3)',
        line=dict(color=COLORS['primary'], width=2),
        name='LWSC'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=regional_avg + [regional_avg[0]],
        theta=categories + [categories[0]],
        fill='none',
        line=dict(color=COLORS['warning'], width=2, dash='dash'),
        name='Regional Avg'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=best_practice + [best_practice[0]],
        theta=categories + [categories[0]],
        fill='none',
        line=dict(color=COLORS['success'], width=2, dash='dot'),
        name='Best Practice'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='rgba(255,255,255,0.1)'
            ),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text'], 'size': 10},
        height=300,
        margin=dict(l=60, r=60, t=40, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
    )
    
    return fig


def create_digital_twin_page():
    """Create Digital Twin page content"""
    return dbc.Container([
        html.H4([html.I(className="fas fa-project-diagram me-2"), "Network Digital Twin"], className="mb-4", style={'color': COLORS['primary']}),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Live Network Visualization"),
                    dbc.CardBody([
                        dcc.Graph(id="network-map", figure=create_network_map(), config={'displayModeBar': True}, style={'height': '500px'})
                    ])
                ], className="metric-card")
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Network Statistics"),
                    dbc.CardBody([
                        html.Div(id="network-stats", children=[
                            html.Div([html.Strong("Total Nodes: "), html.Span("156")], className="mb-2"),
                            html.Div([html.Strong("Pipe Length: "), html.Span("2,800 km")], className="mb-2"),
                            html.Div([html.Strong("Active Sensors: "), html.Span("89")], className="mb-2"),
                            html.Div([html.Strong("DMAs: "), html.Span("24")], className="mb-2"),
                            html.Div([html.Strong("Pressure Zones: "), html.Span("6")], className="mb-2"),
                        ]),
                        html.Hr(),
                        html.H6("Simulation Controls", className="mt-3"),
                        dbc.Button("Run Leak Scenario", id="btn-leak-scenario", color="warning", className="me-2 mb-2", size="sm"),
                        dbc.Button("Pressure Analysis", id="btn-pressure-analysis", color="info", className="me-2 mb-2", size="sm"),
                        dbc.Button("Export GeoJSON", id="btn-export-geojson", color="secondary", className="mb-2", size="sm"),
                        html.Hr(),
                        html.Div(id="simulation-output", className="mt-2")
                    ])
                ], className="metric-card")
            ], width=4)
        ])
    ], fluid=True)


def create_events_page():
    """Create Events Management page content"""
    events_data = [
        {"id": "EVT001", "time": "10:45", "type": "Leak Detected", "location": "Kabulonga Zone", "severity": "High", "status": "Active"},
        {"id": "EVT002", "time": "09:30", "type": "Pressure Drop", "location": "CBD Main", "severity": "Medium", "status": "Investigating"},
        {"id": "EVT003", "time": "08:15", "type": "Meter Anomaly", "location": "Industrial Zone", "severity": "Low", "status": "Resolved"},
        {"id": "EVT004", "time": "07:00", "type": "Pipe Burst", "location": "Matero", "severity": "Critical", "status": "Active"},
        {"id": "EVT005", "time": "Yesterday", "type": "NRW Alert", "location": "DMA-05", "severity": "Medium", "status": "Resolved"},
    ]
    
    severity_colors = {"Critical": "danger", "High": "warning", "Medium": "info", "Low": "secondary"}
    status_colors = {"Active": "danger", "Investigating": "warning", "Resolved": "success"}
    
    return dbc.Container([
        html.H4([html.I(className="fas fa-bell me-2"), "Central Event Management"], className="mb-4", style={'color': COLORS['warning']}),
        
        # Event action feedback modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Event Action", id="event-modal-title")),
            dbc.ModalBody(id="event-modal-body"),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-event-modal", className="ms-auto")
            ])
        ], id="event-action-modal", is_open=False),
        
        dbc.Row([
            dbc.Col([
                # Quick Actions Bar
                dbc.Card([
                    dbc.CardBody([
                        html.Span("Quick Actions: ", className="me-3", style={'fontWeight': '600'}),
                        dbc.Button([html.I(className="fas fa-plus me-1"), "New Event"], id="btn-new-event", color="primary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-filter me-1"), "Filter"], id="btn-filter-events", color="secondary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-download me-1"), "Export"], id="btn-export-events", color="info", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-sync-alt me-1"), "Refresh"], id="btn-refresh-events", color="success", size="sm"),
                    ], className="d-flex align-items-center")
                ], className="metric-card mb-3"),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("Active Events"),
                        dbc.Badge("5", color="danger", className="ms-2")
                    ]),
                    dbc.CardBody([
                        html.Div(id="events-table-container", children=[
                            dbc.Table([
                                html.Thead(html.Tr([
                                    html.Th("ID"), html.Th("Time"), html.Th("Type"), 
                                    html.Th("Location"), html.Th("Severity"), html.Th("Status"), html.Th("Actions")
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(e["id"]),
                                        html.Td(e["time"]),
                                        html.Td(e["type"]),
                                        html.Td(e["location"]),
                                        html.Td(dbc.Badge(e["severity"], color=severity_colors.get(e["severity"], "secondary"))),
                                        html.Td(dbc.Badge(e["status"], color=status_colors.get(e["status"], "secondary"))),
                                        html.Td([
                                            dbc.Button([html.I(className="fas fa-eye")], id={"type": "view-event", "index": e["id"]}, color="info", size="sm", className="me-1"),
                                            dbc.Button([html.I(className="fas fa-check")], id={"type": "resolve-event", "index": e["id"]}, color="success", size="sm", className="me-1"),
                                            dbc.Button([html.I(className="fas fa-user-plus")], id={"type": "assign-event", "index": e["id"]}, color="warning", size="sm"),
                                        ])
                                    ]) for e in events_data
                                ])
                            ], striped=True, hover=True, responsive=True, className="mb-0")
                        ]),
                        html.Div(id="events-action-feedback", className="mt-3")
                    ])
                ], className="metric-card")
            ], width=12)
        ])
    ], fluid=True)


def create_assets_page():
    """Create Asset Health page content"""
    assets_data = [
        {"name": "Matero Old Cast Iron", "type": "Pipe", "health": 28, "risk": "Critical", "action": "Replace immediately"},
        {"name": "Chelstone Pump P2", "type": "Pump", "health": 45, "risk": "High", "action": "Schedule maintenance"},
        {"name": "Kabulonga Tank", "type": "Tank", "health": 62, "risk": "Medium", "action": "Monitor closely"},
        {"name": "CBD Isolation Valve", "type": "Valve", "health": 55, "risk": "Medium", "action": "Inspect seals"},
        {"name": "Woodlands PRV", "type": "PRV", "health": 88, "risk": "Low", "action": "Routine maintenance"},
    ]
    
    def get_health_color(health):
        if health >= 80: return COLORS['success']
        elif health >= 60: return COLORS['info']
        elif health >= 40: return COLORS['warning']
        else: return COLORS['danger']
    
    return dbc.Container([
        html.H4([html.I(className="fas fa-heartbeat me-2"), "Asset Health Dashboard"], className="mb-4", style={'color': COLORS['danger']}),
        
        # Quick Actions Bar
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Span("Asset Actions: ", className="me-3", style={'fontWeight': '600'}),
                        dbc.Button([html.I(className="fas fa-plus me-1"), "Add Asset"], id="btn-add-asset", color="primary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-wrench me-1"), "Schedule Maintenance"], id="btn-schedule-maintenance", color="warning", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-file-pdf me-1"), "Generate Report"], id="btn-asset-report", color="info", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-sync-alt me-1"), "Refresh Data"], id="btn-refresh-assets", color="success", size="sm"),
                    ], className="d-flex align-items-center")
                ], className="metric-card mb-3"),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Health Distribution"),
                    dbc.CardBody([
                        dcc.Graph(id="health-distribution-chart", figure=create_health_distribution_chart(), config={'displayModeBar': False})
                    ])
                ], className="metric-card")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Priority Assets for Intervention"),
                    dbc.CardBody([
                        html.Div(id="priority-assets-list", children=[
                            html.Div([
                                html.Div([
                                    html.Strong(a["name"]),
                                    dbc.Badge(a["type"], color="secondary", className="ms-2"),
                                    dbc.Badge(a["risk"], color="danger" if a["risk"]=="Critical" else "warning" if a["risk"]=="High" else "info", className="ms-2"),
                                    dbc.Button([html.I(className="fas fa-tools")], id={"type": "maintain-asset", "index": i}, color="primary", size="sm", className="float-end")
                                ]),
                                dbc.Progress(value=a["health"], color="danger" if a["health"]<40 else "warning" if a["health"]<60 else "success", className="my-2", style={'height': '8px'}),
                                html.Small(f"Health: {a['health']}% | {a['action']}", className="text-muted")
                            ], className="mb-3 p-2 rounded", style={'background': 'rgba(255,255,255,0.05)'})
                            for i, a in enumerate(assets_data)
                        ]),
                        html.Div(id="asset-action-feedback", className="mt-3")
                    ])
                ], className="metric-card")
            ], width=8)
        ])
    ], fluid=True)


def create_benchmark_page():
    """Create Benchmarking page content"""
    return dbc.Container([
        html.H4([html.I(className="fas fa-chart-bar me-2"), "Performance Benchmarking"], className="mb-4", style={'color': COLORS['success']}),
        
        # Actions Bar
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Span("Benchmark Actions: ", className="me-3", style={'fontWeight': '600'}),
                        dbc.Button([html.I(className="fas fa-sync-alt me-1"), "Update Data"], id="btn-update-benchmark", color="primary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-file-excel me-1"), "Export to Excel"], id="btn-export-benchmark", color="success", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-share-alt me-1"), "Share Report"], id="btn-share-benchmark", color="info", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-calendar me-1"), "Change Period"], id="btn-period-benchmark", color="secondary", size="sm"),
                    ], className="d-flex align-items-center")
                ], className="metric-card mb-3"),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("KPI Comparison vs Peers"),
                    dbc.CardBody([
                        dcc.Graph(id="benchmark-radar-chart", figure=create_benchmark_radar(), config={'displayModeBar': False})
                    ])
                ], className="metric-card")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Ranking Summary"),
                    dbc.CardBody([
                        html.Div([
                            html.H2("3rd", style={'color': COLORS['primary'], 'fontWeight': '700'}),
                            html.P("Out of 5 utilities in Southern Africa", className="text-muted")
                        ], className="text-center mb-4"),
                        html.Hr(),
                        html.Div(id="benchmark-details", children=[
                            html.Div([html.Strong("NRW Rate: "), html.Span("36.2%"), dbc.Badge("Below Average", color="warning", className="ms-2")], className="mb-2"),
                            html.Div([html.Strong("Service Coverage: "), html.Span("78%"), dbc.Badge("Average", color="info", className="ms-2")], className="mb-2"),
                            html.Div([html.Strong("Water Quality: "), html.Span("95.5%"), dbc.Badge("Good", color="success", className="ms-2")], className="mb-2"),
                            html.Div([html.Strong("Collection Efficiency: "), html.Span("82%"), dbc.Badge("Good", color="success", className="ms-2")], className="mb-2"),
                        ]),
                        html.Hr(),
                        dbc.Button([html.I(className="fas fa-chart-line me-1"), "View Detailed Analysis"], id="btn-detailed-benchmark", color="primary", className="w-100 mt-2"),
                    ])
                ], className="metric-card")
            ], width=6)
        ]),
        html.Div(id="benchmark-action-feedback", className="mt-3")
    ], fluid=True)


def create_customers_page():
    """Create Customers page content"""
    return dbc.Container([
        html.H4([html.I(className="fas fa-users me-2"), "Customer Insights"], className="mb-4", style={'color': COLORS['info']}),
        
        # Actions Bar
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Span("Customer Actions: ", className="me-3", style={'fontWeight': '600'}),
                        dbc.Button([html.I(className="fas fa-user-plus me-1"), "Add Customer"], id="btn-add-customer", color="primary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-search me-1"), "Search"], id="btn-search-customer", color="secondary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-envelope me-1"), "Send Notification"], id="btn-notify-customers", color="info", size="sm", className="me-2"),
                        dbc.Button([html.I(className="fas fa-file-csv me-1"), "Export Data"], id="btn-export-customers", color="success", size="sm"),
                    ], className="d-flex align-items-center")
                ], className="metric-card mb-3"),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Customer Statistics"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H3("180,000", style={'color': COLORS['primary'], 'fontWeight': '700'}),
                                    html.P("Total Connections", className="text-muted mb-0")
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("82%", style={'color': COLORS['success'], 'fontWeight': '700'}),
                                    html.P("Collection Rate", className="text-muted mb-0")
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("156", style={'color': COLORS['warning'], 'fontWeight': '700'}),
                                    html.P("Active Complaints", className="text-muted mb-0")
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.H3("4.2★", style={'color': COLORS['info'], 'fontWeight': '700'}),
                                    html.P("Satisfaction Score", className="text-muted mb-0")
                                ], className="text-center")
                            ], width=3),
                        ])
                    ])
                ], className="metric-card mb-3")
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "Recent Service Requests",
                        dbc.Button([html.I(className="fas fa-plus")], id="btn-new-service-request", color="primary", size="sm", className="float-end")
                    ]),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("SR-2026-0145"), html.Span(" - Leak Report", className="text-muted"),
                                    dbc.Button([html.I(className="fas fa-eye")], id="btn-view-sr-145", color="info", size="sm", className="float-end"),
                                    dbc.Badge("High", color="warning", className="float-end me-2")
                                ]),
                                html.Small("Kabulonga, Plot 123 • Submitted 2 hours ago", className="text-muted")
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("SR-2026-0144"), html.Span(" - Low Pressure", className="text-muted"),
                                    dbc.Button([html.I(className="fas fa-eye")], id="btn-view-sr-144", color="info", size="sm", className="float-end"),
                                    dbc.Badge("Medium", color="info", className="float-end me-2")
                                ]),
                                html.Small("Woodlands Ext • Submitted 5 hours ago", className="text-muted")
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("SR-2026-0143"), html.Span(" - Billing Query", className="text-muted"),
                                    dbc.Button([html.I(className="fas fa-eye")], id="btn-view-sr-143", color="info", size="sm", className="float-end"),
                                    dbc.Badge("Low", color="secondary", className="float-end")
                                ]),
                                html.Small("CBD Office • Submitted yesterday", className="text-muted")
                            ]),
                        ], flush=True)
                    ])
                ], className="metric-card")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top Conservation Customers"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-trophy text-warning me-2"),
                                    html.Strong("John Banda"), 
                                    dbc.Badge("Platinum", color="primary", className="ms-2"),
                                    html.Span("5,200 pts", className="float-end text-success")
                                ]),
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-medal text-secondary me-2"),
                                    html.Strong("Mary Mwanza"),
                                    dbc.Badge("Gold", color="warning", className="ms-2"),
                                    html.Span("3,800 pts", className="float-end text-success")
                                ]),
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="fas fa-award text-info me-2"),
                                    html.Strong("Peter Zulu"),
                                    dbc.Badge("Gold", color="warning", className="ms-2"),
                                    html.Span("2,950 pts", className="float-end text-success")
                                ]),
                            ]),
                        ], flush=True)
                    ])
                ], className="metric-card")
            ], width=6)
        ])
    ], fluid=True)


# ===========================================
# USER CREDENTIALS DATABASE
# ===========================================
USERS = {
    "admin": {
        "password": "AquaWatch@2026",
        "name": "Administrator",
        "role": "System Administrator",
        "permissions": ["all"]
    },
    "operator": {
        "password": "Operator@2026",
        "name": "Control Room Operator",
        "role": "Operator",
        "permissions": ["view", "events", "alerts"]
    },
    "engineer": {
        "password": "Engineer@2026",
        "name": "Network Engineer",
        "role": "Engineer",
        "permissions": ["view", "digital_twin", "assets", "maintenance"]
    },
    "manager": {
        "password": "Manager@2026",
        "name": "Operations Manager",
        "role": "Manager",
        "permissions": ["view", "reports", "benchmarking", "customers"]
    }
}


def create_login_page():
    """Create the login page"""
    return html.Div([
        # Background with water effect
        html.Div(style={
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100%',
            'height': '100%',
            'background': 'linear-gradient(135deg, #0F0F23 0%, #1A1A2E 50%, #0F0F23 100%)',
            'zIndex': -1
        }),
        
        # Login container
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    # Logo and title
                    html.Div([
                        html.I(className="fas fa-water fa-4x mb-4", style={'color': COLORS['primary']}),
                        html.H1("AquaWatch", style={
                            'fontWeight': '700',
                            'background': 'linear-gradient(90deg, #00A3E0, #0066CC)',
                            '-webkit-background-clip': 'text',
                            '-webkit-text-fill-color': 'transparent',
                            'marginBottom': '10px'
                        }),
                        html.H4("NRW Detection System", className="text-muted mb-2"),
                        html.P("World-Class Water Network Intelligence", className="text-muted mb-4"),
                    ], className="text-center mb-4"),
                    
                    # Login card
                    dbc.Card([
                        dbc.CardBody([
                            html.H4([
                                html.I(className="fas fa-sign-in-alt me-2"),
                                "Sign In"
                            ], className="text-center mb-4"),
                            
                            # Username
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className="fas fa-user")),
                                dbc.Input(
                                    id="login-username",
                                    placeholder="Username",
                                    type="text",
                                    className="bg-dark text-light border-secondary"
                                )
                            ], className="mb-3"),
                            
                            # Password
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className="fas fa-lock")),
                                dbc.Input(
                                    id="login-password",
                                    placeholder="Password",
                                    type="password",
                                    className="bg-dark text-light border-secondary"
                                )
                            ], className="mb-3"),
                            
                            # Remember me
                            dbc.Checkbox(
                                id="login-remember",
                                label="Remember me",
                                className="mb-3 text-muted"
                            ),
                            
                            # Login button
                            dbc.Button(
                                [html.I(className="fas fa-sign-in-alt me-2"), "Login"],
                                id="login-button",
                                color="primary",
                                className="w-100 mb-3",
                                size="lg"
                            ),
                            
                            # Error message
                            html.Div(id="login-error", className="text-center"),
                            
                            html.Hr(className="my-4"),
                            
                            # Demo credentials hint
                            html.Div([
                                html.Small("Demo Credentials:", className="text-muted d-block mb-2"),
                                html.Small([
                                    html.Strong("Admin: "), "admin / AquaWatch@2026"
                                ], className="text-muted d-block"),
                                html.Small([
                                    html.Strong("Operator: "), "operator / Operator@2026"
                                ], className="text-muted d-block"),
                            ], className="text-center")
                        ])
                    ], className="metric-card", style={'maxWidth': '400px', 'margin': '0 auto'}),
                    
                    # Footer
                    html.Div([
                        html.P([
                            "© 2026 AquaWatch NRW Detection System",
                            html.Br(),
                            "Lusaka Water & Sewerage Company"
                        ], className="text-muted text-center mt-4", style={'fontSize': '0.85rem'})
                    ])
                ], width=12, md=6, lg=4, className="mx-auto")
            ], className="min-vh-100 align-items-center justify-content-center")
        ], fluid=True)
    ])


def create_app():
    """Create the world-class dashboard application"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ],
        suppress_callback_exceptions=True
    )
    
    # Header
    header = dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-water fa-2x me-3", style={'color': COLORS['primary']}),
                html.Div([
                    html.H3("AquaWatch NRW", className="mb-0", style={'fontWeight': '700'}),
                    html.Small("World-Class Water Network Intelligence", className="text-muted")
                ])
            ], className="d-flex align-items-center")
        ], width=4),
        dbc.Col([
            html.Div([
                html.Div([
                    html.Span(className="live-indicator"),
                    html.Span("LIVE", style={'color': COLORS['success'], 'fontWeight': '600', 'marginRight': '20px'})
                ]),
                html.Span(id="current-time", children=datetime.now().strftime("%Y-%m-%d %H:%M"), className="text-muted me-3"),
                dbc.Button([html.I(className="fas fa-bell")], id="btn-notifications", color="link", className="text-light position-relative", 
                          n_clicks=0),
                dbc.Badge("3", color="danger", className="position-absolute", 
                         style={'top': '0', 'right': '0', 'fontSize': '0.6rem'}),
                dbc.Button([html.I(className="fas fa-cog")], id="btn-settings", color="link", className="text-light ms-2",
                          n_clicks=0),
                html.Span("|", className="text-muted mx-3"),
                html.Span(id="logged-in-user", children=[
                    html.I(className="fas fa-user-circle me-2"),
                    "Admin"
                ], className="text-light me-3"),
                dbc.Button([html.I(className="fas fa-sign-out-alt me-1"), "Logout"], 
                          id="btn-logout", color="outline-danger", size="sm"),
            ], className="d-flex align-items-center justify-content-end")
        ], width=8)
    ], className="mb-4 pb-3", style={'borderBottom': f'1px solid {COLORS["muted"]}'})
    
    # KPI Summary Row
    kpi_row = dbc.Row([
        dbc.Col(create_kpi_card("NRW Rate", "36.2", "%", "down", "2.1% vs last month", "fa-tint", COLORS['primary']), width=2),
        dbc.Col(create_kpi_card("Active Leaks", "7", "detected", "down", "3 less than yesterday", "fa-exclamation-triangle", COLORS['warning']), width=2),
        dbc.Col(create_kpi_card("System Pressure", "4.1", "bar", "up", "Optimal range", "fa-gauge-high", COLORS['success']), width=2),
        dbc.Col(create_kpi_card("Asset Health", "72", "/100", "up", "+3 points", "fa-heart", COLORS['info']), width=2),
        dbc.Col(create_kpi_card("Water Produced", "385K", "m³/day", "up", "98% of capacity", "fa-industry", COLORS['secondary']), width=2),
        dbc.Col(create_kpi_card("Revenue Recovery", "82", "%", "up", "+5% this quarter", "fa-coins", COLORS['success']), width=2),
    ], className="mb-4 g-3")
    
    # Main content area
    main_content = dbc.Row([
        # Left column - Network map and events
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-map-marked-alt me-2", style={'color': COLORS['primary']}),
                        html.Span("Network Digital Twin", style={'fontWeight': '600'})
                    ]),
                    dbc.ButtonGroup([
                        dbc.Button("2D", size="sm", outline=True, color="light", active=True),
                        dbc.Button("3D", size="sm", outline=True, color="light"),
                    ], size="sm")
                ], className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    dcc.Graph(figure=create_network_map(), config={'displayModeBar': False})
                ])
            ], className="metric-card mb-3"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-clock me-2", style={'color': COLORS['warning']}),
                    html.Span("Live Events", style={'fontWeight': '600'}),
                    dbc.Badge("5 Active", color="danger", className="ms-2")
                ]),
                dbc.CardBody([
                    create_event_timeline()
                ], style={'maxHeight': '300px', 'overflowY': 'auto'})
            ], className="metric-card")
        ], width=5),
        
        # Right column - Analytics
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-chart-line me-2", style={'color': COLORS['primary']}),
                            html.Span("NRW Trend", style={'fontWeight': '600'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=create_nrw_trend_chart(), config={'displayModeBar': False})
                        ])
                    ], className="metric-card")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-compress-arrows-alt me-2", style={'color': COLORS['info']}),
                            html.Span("Pressure Zones", style={'fontWeight': '600'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=create_pressure_zones_chart(), config={'displayModeBar': False})
                        ])
                    ], className="metric-card")
                ], width=6)
            ], className="mb-3 g-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-heartbeat me-2", style={'color': COLORS['danger']}),
                            html.Span("Asset Health Distribution", style={'fontWeight': '600'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=create_health_distribution_chart(), config={'displayModeBar': False})
                        ])
                    ], className="metric-card")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-chart-radar me-2", style={'color': COLORS['success']}),
                            html.Span("Performance Benchmark", style={'fontWeight': '600'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=create_benchmark_radar(), config={'displayModeBar': False})
                        ])
                    ], className="metric-card")
                ], width=6)
            ], className="g-3")
        ], width=7)
    ], className="g-3")
    
    # AI Insights Panel
    ai_insights = dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-brain me-2", style={'color': COLORS['accent']}),
                html.Span("AI-Powered Insights", style={'fontWeight': '600'})
            ]),
            dbc.Badge("Powered by ML", color="info")
        ], className="d-flex justify-content-between align-items-center"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-exclamation-circle text-danger me-2"),
                        html.Strong("Priority Alert: "),
                        html.Span("Predicted pipe failure in Matero Zone within 14 days. Recommend proactive replacement.")
                    ], className="p-2 mb-2 rounded", style={'background': 'rgba(220, 53, 69, 0.1)'})
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-lightbulb text-warning me-2"),
                        html.Strong("Optimization: "),
                        html.Span("Reducing pressure in Zone 3 by 0.3 bar could save 45,000 L/day leakage.")
                    ], className="p-2 mb-2 rounded", style={'background': 'rgba(255, 193, 7, 0.1)'})
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-chart-line text-success me-2"),
                        html.Strong("Forecast: "),
                        html.Span("NRW projected to reach 32% target by March 2026 if current trend continues.")
                    ], className="p-2 mb-2 rounded", style={'background': 'rgba(40, 167, 69, 0.1)'})
                ], width=4)
            ])
        ])
    ], className="metric-card mt-4")
    
    # Footer
    footer = html.Div([
        html.Hr(style={'borderColor': COLORS['muted']}),
        html.Div([
            html.Span("AquaWatch NRW Detection System", className="text-muted"),
            html.Span(" | ", className="text-muted"),
            html.Span("Lusaka Water & Sewerage Company", className="text-muted"),
            html.Span(" | ", className="text-muted"),
            html.Span(f"© {datetime.now().year} All Rights Reserved", className="text-muted")
        ], className="text-center py-3")
    ])
    
    # Use dcc.Tabs for proper tab navigation
    tabs = dcc.Tabs(id="main-tabs", value='command', children=[
        dcc.Tab(label='Command Center', value='command', 
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
        dcc.Tab(label='Digital Twin', value='twin',
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
        dcc.Tab(label='Events', value='events',
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
        dcc.Tab(label='Asset Health', value='assets',
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
        dcc.Tab(label='Benchmarking', value='benchmark',
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
        dcc.Tab(label='Customers', value='customers',
                style={'backgroundColor': COLORS['card_bg'], 'color': COLORS['text'], 'border': 'none', 'padding': '12px 20px'},
                selected_style={'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'padding': '12px 20px', 'borderRadius': '8px'}),
    ], style={'marginBottom': '20px'})
    
    # Notifications Modal
    notifications_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-bell me-2"), "Notifications"])),
        dbc.ModalBody([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                        html.Strong("Critical Leak Detected"),
                        html.Small(" - 15 min ago", className="text-muted float-end")
                    ]),
                    html.P("Kabulonga Zone - Estimated 50 L/min water loss", className="mb-0 mt-1 text-muted", style={'fontSize': '0.85rem'})
                ]),
                dbc.ListGroupItem([
                    html.Div([
                        html.I(className="fas fa-gauge-high text-warning me-2"),
                        html.Strong("Pressure Anomaly"),
                        html.Small(" - 1 hour ago", className="text-muted float-end")
                    ]),
                    html.P("CBD Main - Pressure dropped below threshold", className="mb-0 mt-1 text-muted", style={'fontSize': '0.85rem'})
                ]),
                dbc.ListGroupItem([
                    html.Div([
                        html.I(className="fas fa-check-circle text-success me-2"),
                        html.Strong("Maintenance Complete"),
                        html.Small(" - 3 hours ago", className="text-muted float-end")
                    ]),
                    html.P("Woodlands PRV - Routine inspection completed", className="mb-0 mt-1 text-muted", style={'fontSize': '0.85rem'})
                ]),
            ], flush=True)
        ]),
        dbc.ModalFooter([
            dbc.Button("Mark All Read", id="btn-mark-all-read", color="secondary", size="sm", className="me-2"),
            dbc.Button("View All", id="btn-view-all-notif", color="primary", size="sm"),
            dbc.Button("Close", id="close-notifications", className="ms-auto")
        ])
    ], id="notifications-modal", is_open=False, size="lg")
    
    # Settings Modal
    settings_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-cog me-2"), "Settings"])),
        dbc.ModalBody([
            html.H6("Dashboard Preferences", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Refresh Interval"),
                    dbc.Select(
                        id="refresh-interval-select",
                        options=[
                            {"label": "15 seconds", "value": "15"},
                            {"label": "30 seconds", "value": "30"},
                            {"label": "1 minute", "value": "60"},
                            {"label": "5 minutes", "value": "300"},
                        ],
                        value="30"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Default View"),
                    dbc.Select(
                        id="default-view-select",
                        options=[
                            {"label": "Command Center", "value": "command"},
                            {"label": "Digital Twin", "value": "twin"},
                            {"label": "Events", "value": "events"},
                        ],
                        value="command"
                    )
                ], width=6),
            ], className="mb-3"),
            html.Hr(),
            html.H6("Notifications", className="mb-3"),
            dbc.Checklist(
                options=[
                    {"label": " Email alerts for critical events", "value": "email"},
                    {"label": " SMS alerts for leaks", "value": "sms"},
                    {"label": " Desktop notifications", "value": "desktop"},
                    {"label": " Daily summary reports", "value": "daily"},
                ],
                value=["email", "desktop"],
                id="notification-settings"
            ),
            html.Hr(),
            html.H6("User Profile", className="mb-3"),
            html.Div([
                html.Strong("Logged in as: "), html.Span("Admin User"),
                html.Br(),
                html.Strong("Role: "), html.Span("System Administrator"),
                html.Br(),
                html.Strong("Last Login: "), html.Span(datetime.now().strftime("%Y-%m-%d %H:%M"))
            ]),
            html.Div(id="settings-save-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Save Changes", id="btn-save-settings", color="primary"),
            dbc.Button("Close", id="close-settings", className="ms-auto")
        ])
    ], id="settings-modal", is_open=False, size="lg")
    
    # ===========================================
    # FUNCTIONAL MODALS FOR REAL ACTIONS
    # ===========================================
    
    # New Event Modal (REAL FORM)
    new_event_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-plus-circle me-2"), "Create New Event"])),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Event Type", html_for="event-type-input"),
                        dbc.Select(
                            id="event-type-input",
                            options=[
                                {"label": "Leak Detected", "value": "leak"},
                                {"label": "Pipe Burst", "value": "burst"},
                                {"label": "Pressure Anomaly", "value": "pressure"},
                                {"label": "Meter Anomaly", "value": "meter"},
                                {"label": "Water Quality Issue", "value": "quality"},
                                {"label": "NRW Alert", "value": "nrw"},
                            ],
                            value="leak"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Severity", html_for="event-severity-input"),
                        dbc.Select(
                            id="event-severity-input",
                            options=[
                                {"label": "Critical", "value": "critical"},
                                {"label": "High", "value": "high"},
                                {"label": "Medium", "value": "medium"},
                                {"label": "Low", "value": "low"},
                            ],
                            value="medium"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Location / Zone", html_for="event-location-input"),
                        dbc.Select(
                            id="event-location-input",
                            options=[
                                {"label": "Kabulonga Zone", "value": "kabulonga"},
                                {"label": "CBD Main", "value": "cbd"},
                                {"label": "Woodlands", "value": "woodlands"},
                                {"label": "Matero", "value": "matero"},
                                {"label": "Chelstone", "value": "chelstone"},
                                {"label": "Industrial Zone", "value": "industrial"},
                                {"label": "Kabwata", "value": "kabwata"},
                            ],
                            value="kabulonga"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Assigned To", html_for="event-assigned-input"),
                        dbc.Select(
                            id="event-assigned-input",
                            options=[
                                {"label": "Field Team Alpha", "value": "alpha"},
                                {"label": "Field Team Beta", "value": "beta"},
                                {"label": "Emergency Response", "value": "emergency"},
                                {"label": "Maintenance Crew", "value": "maintenance"},
                                {"label": "Unassigned", "value": "none"},
                            ],
                            value="none"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", html_for="event-description-input"),
                        dbc.Textarea(
                            id="event-description-input",
                            placeholder="Enter detailed description of the event...",
                            style={'height': '100px'}
                        )
                    ])
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Estimated Water Loss (L/min)"),
                        dbc.Input(id="event-water-loss-input", type="number", placeholder="e.g., 50", value="")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Priority Response Time"),
                        dbc.Select(
                            id="event-response-input",
                            options=[
                                {"label": "Immediate (< 1 hour)", "value": "immediate"},
                                {"label": "Urgent (< 4 hours)", "value": "urgent"},
                                {"label": "Normal (< 24 hours)", "value": "normal"},
                                {"label": "Scheduled", "value": "scheduled"},
                            ],
                            value="normal"
                        )
                    ], width=6),
                ], className="mb-3"),
            ]),
            html.Div(id="new-event-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Create Event", id="btn-submit-new-event", color="primary"),
            dbc.Button("Cancel", id="close-new-event-modal", color="secondary", className="ms-2")
        ])
    ], id="new-event-modal", is_open=False, size="lg")
    
    # Filter Events Modal
    filter_events_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-filter me-2"), "Filter Events"])),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Event Status"),
                    dbc.Checklist(
                        id="filter-status",
                        options=[
                            {"label": " Active", "value": "active"},
                            {"label": " Investigating", "value": "investigating"},
                            {"label": " Resolved", "value": "resolved"},
                        ],
                        value=["active", "investigating"]
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Severity"),
                    dbc.Checklist(
                        id="filter-severity",
                        options=[
                            {"label": " Critical", "value": "critical"},
                            {"label": " High", "value": "high"},
                            {"label": " Medium", "value": "medium"},
                            {"label": " Low", "value": "low"},
                        ],
                        value=["critical", "high", "medium", "low"]
                    )
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Date Range"),
                    dcc.DatePickerRange(
                        id="filter-date-range",
                        start_date=datetime.now() - timedelta(days=7),
                        end_date=datetime.now(),
                        display_format="YYYY-MM-DD"
                    )
                ], width=12),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Location"),
                    dbc.Select(
                        id="filter-location",
                        options=[
                            {"label": "All Locations", "value": "all"},
                            {"label": "Kabulonga Zone", "value": "kabulonga"},
                            {"label": "CBD Main", "value": "cbd"},
                            {"label": "Woodlands", "value": "woodlands"},
                            {"label": "Matero", "value": "matero"},
                        ],
                        value="all"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Event Type"),
                    dbc.Select(
                        id="filter-event-type",
                        options=[
                            {"label": "All Types", "value": "all"},
                            {"label": "Leak Detected", "value": "leak"},
                            {"label": "Pipe Burst", "value": "burst"},
                            {"label": "Pressure Anomaly", "value": "pressure"},
                            {"label": "Meter Anomaly", "value": "meter"},
                        ],
                        value="all"
                    )
                ], width=6),
            ]),
            html.Div(id="filter-result-count", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Apply Filters", id="btn-apply-filters", color="primary"),
            dbc.Button("Reset", id="btn-reset-filters", color="secondary", className="ms-2"),
            dbc.Button("Close", id="close-filter-modal", color="light", className="ms-2")
        ])
    ], id="filter-events-modal", is_open=False, size="lg")
    
    # View Event Detail Modal
    view_event_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="view-event-title")),
        dbc.ModalBody(id="view-event-body"),
        dbc.ModalFooter([
            dbc.Button("Assign Team", id="btn-assign-from-view", color="warning"),
            dbc.Button("Mark Resolved", id="btn-resolve-from-view", color="success", className="ms-2"),
            dbc.Button("Close", id="close-view-event-modal", color="secondary", className="ms-2")
        ])
    ], id="view-event-modal", is_open=False, size="lg")
    
    # Add Asset Modal
    add_asset_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-plus-circle me-2"), "Register New Asset"])),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Asset Name"),
                        dbc.Input(id="asset-name-input", placeholder="e.g., Kabulonga Main Valve V-101")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Asset Type"),
                        dbc.Select(
                            id="asset-type-input",
                            options=[
                                {"label": "Pipe", "value": "pipe"},
                                {"label": "Valve", "value": "valve"},
                                {"label": "Pump", "value": "pump"},
                                {"label": "Tank/Reservoir", "value": "tank"},
                                {"label": "PRV", "value": "prv"},
                                {"label": "Meter", "value": "meter"},
                                {"label": "Sensor", "value": "sensor"},
                            ],
                            value="pipe"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Location / Zone"),
                        dbc.Select(
                            id="asset-location-input",
                            options=[
                                {"label": "Kabulonga", "value": "kabulonga"},
                                {"label": "CBD", "value": "cbd"},
                                {"label": "Woodlands", "value": "woodlands"},
                                {"label": "Matero", "value": "matero"},
                                {"label": "Chelstone", "value": "chelstone"},
                            ],
                            value="kabulonga"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Installation Date"),
                        dbc.Input(id="asset-install-date", type="date", value=datetime.now().strftime("%Y-%m-%d"))
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Material"),
                        dbc.Select(
                            id="asset-material-input",
                            options=[
                                {"label": "Cast Iron", "value": "cast_iron"},
                                {"label": "Ductile Iron", "value": "ductile_iron"},
                                {"label": "PVC", "value": "pvc"},
                                {"label": "HDPE", "value": "hdpe"},
                                {"label": "Steel", "value": "steel"},
                                {"label": "Concrete", "value": "concrete"},
                            ],
                            value="ductile_iron"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Diameter (mm)"),
                        dbc.Input(id="asset-diameter-input", type="number", placeholder="e.g., 200")
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Expected Lifespan (years)"),
                        dbc.Input(id="asset-lifespan-input", type="number", value="50")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Initial Health Score"),
                        dbc.Input(id="asset-health-input", type="number", value="100", min="0", max="100")
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("GPS Coordinates"),
                        dbc.Input(id="asset-gps-input", placeholder="e.g., -15.4050, 28.2900")
                    ])
                ], className="mb-3"),
            ]),
            html.Div(id="add-asset-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Register Asset", id="btn-submit-new-asset", color="primary"),
            dbc.Button("Cancel", id="close-add-asset-modal", color="secondary", className="ms-2")
        ])
    ], id="add-asset-modal", is_open=False, size="lg")
    
    # Schedule Maintenance Modal
    maintenance_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-wrench me-2"), "Schedule Maintenance"])),
        dbc.ModalBody([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "5 assets flagged for priority maintenance"
            ], color="warning"),
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select Asset"),
                        dbc.Select(
                            id="maint-asset-select",
                            options=[
                                {"label": "Matero Old Cast Iron (Critical - 28%)", "value": "matero_pipe"},
                                {"label": "Chelstone Pump P2 (High - 45%)", "value": "chelstone_pump"},
                                {"label": "CBD Isolation Valve (Medium - 55%)", "value": "cbd_valve"},
                                {"label": "Kabulonga Tank (Medium - 62%)", "value": "kabulonga_tank"},
                                {"label": "Woodlands PRV (Low - 88%)", "value": "woodlands_prv"},
                            ],
                            value="matero_pipe"
                        )
                    ])
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Maintenance Type"),
                        dbc.Select(
                            id="maint-type-select",
                            options=[
                                {"label": "Emergency Replacement", "value": "emergency_replace"},
                                {"label": "Scheduled Replacement", "value": "scheduled_replace"},
                                {"label": "Major Repair", "value": "major_repair"},
                                {"label": "Minor Repair", "value": "minor_repair"},
                                {"label": "Inspection", "value": "inspection"},
                                {"label": "Preventive Maintenance", "value": "preventive"},
                            ],
                            value="scheduled_replace"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Priority"),
                        dbc.Select(
                            id="maint-priority-select",
                            options=[
                                {"label": "Critical (Immediate)", "value": "critical"},
                                {"label": "High (This Week)", "value": "high"},
                                {"label": "Medium (This Month)", "value": "medium"},
                                {"label": "Low (Scheduled)", "value": "low"},
                            ],
                            value="high"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Scheduled Date"),
                        dbc.Input(id="maint-date-input", type="date", value=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"))
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Assigned Team"),
                        dbc.Select(
                            id="maint-team-select",
                            options=[
                                {"label": "Maintenance Crew A", "value": "crew_a"},
                                {"label": "Maintenance Crew B", "value": "crew_b"},
                                {"label": "External Contractor", "value": "contractor"},
                                {"label": "Emergency Response", "value": "emergency"},
                            ],
                            value="crew_a"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Estimated Cost (ZMW)"),
                        dbc.Input(id="maint-cost-input", type="number", placeholder="e.g., 15000")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Estimated Duration (hours)"),
                        dbc.Input(id="maint-duration-input", type="number", value="8")
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Work Description"),
                        dbc.Textarea(id="maint-description-input", placeholder="Describe maintenance work to be performed...", style={'height': '80px'})
                    ])
                ], className="mb-3"),
            ]),
            html.Div(id="schedule-maint-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Schedule Maintenance", id="btn-submit-maintenance", color="primary"),
            dbc.Button("Cancel", id="close-maintenance-modal", color="secondary", className="ms-2")
        ])
    ], id="maintenance-modal", is_open=False, size="lg")
    
    # Customer Search Modal
    customer_search_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-search me-2"), "Customer Search"])),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(id="customer-search-input", placeholder="Enter account number, name, or phone..."),
                        dbc.Button([html.I(className="fas fa-search")], id="btn-do-customer-search", color="primary")
                    ])
                ])
            ], className="mb-4"),
            html.Div(id="customer-search-results", children=[
                html.P("Enter search criteria above to find customers.", className="text-muted text-center")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-customer-search-modal", color="secondary")
        ])
    ], id="customer-search-modal", is_open=False, size="lg")
    
    # Add Customer Modal
    add_customer_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-user-plus me-2"), "Register New Customer"])),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Full Name"),
                        dbc.Input(id="cust-name-input", placeholder="e.g., John Banda")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Account Type"),
                        dbc.Select(
                            id="cust-type-input",
                            options=[
                                {"label": "Residential", "value": "residential"},
                                {"label": "Commercial", "value": "commercial"},
                                {"label": "Industrial", "value": "industrial"},
                                {"label": "Government", "value": "government"},
                            ],
                            value="residential"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Phone Number"),
                        dbc.Input(id="cust-phone-input", placeholder="+260 97X XXX XXX")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Email"),
                        dbc.Input(id="cust-email-input", type="email", placeholder="email@example.com")
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Address"),
                        dbc.Textarea(id="cust-address-input", placeholder="Full physical address", style={'height': '60px'})
                    ])
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Zone"),
                        dbc.Select(
                            id="cust-zone-input",
                            options=[
                                {"label": "Kabulonga", "value": "kabulonga"},
                                {"label": "Woodlands", "value": "woodlands"},
                                {"label": "CBD", "value": "cbd"},
                                {"label": "Matero", "value": "matero"},
                            ],
                            value="kabulonga"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Meter Size"),
                        dbc.Select(
                            id="cust-meter-input",
                            options=[
                                {"label": "15mm (Residential)", "value": "15"},
                                {"label": "20mm (Small Commercial)", "value": "20"},
                                {"label": "25mm (Commercial)", "value": "25"},
                                {"label": "50mm (Industrial)", "value": "50"},
                            ],
                            value="15"
                        )
                    ], width=6),
                ], className="mb-3"),
            ]),
            html.Div(id="add-customer-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Register Customer", id="btn-submit-new-customer", color="primary"),
            dbc.Button("Cancel", id="close-add-customer-modal", color="secondary", className="ms-2")
        ])
    ], id="add-customer-modal", is_open=False, size="lg")
    
    # Send Notification Modal
    send_notification_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-envelope me-2"), "Send Customer Notification"])),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Notification Type"),
                        dbc.Select(
                            id="notif-type-input",
                            options=[
                                {"label": "SMS", "value": "sms"},
                                {"label": "Email", "value": "email"},
                                {"label": "Both SMS & Email", "value": "both"},
                            ],
                            value="sms"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Target Group"),
                        dbc.Select(
                            id="notif-target-input",
                            options=[
                                {"label": "All Customers", "value": "all"},
                                {"label": "Kabulonga Zone", "value": "kabulonga"},
                                {"label": "CBD Zone", "value": "cbd"},
                                {"label": "Woodlands Zone", "value": "woodlands"},
                                {"label": "Customers with Arrears", "value": "arrears"},
                                {"label": "High Usage Customers", "value": "high_usage"},
                            ],
                            value="all"
                        )
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Subject"),
                        dbc.Input(id="notif-subject-input", placeholder="e.g., Scheduled Maintenance Notice")
                    ])
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Message"),
                        dbc.Textarea(
                            id="notif-message-input",
                            placeholder="Type your message here...",
                            style={'height': '150px'}
                        )
                    ])
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="notif-schedule-check",
                            options=[{"label": " Schedule for later", "value": "schedule"}],
                            value=[]
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Input(id="notif-schedule-time", type="datetime-local", disabled=True)
                    ], width=6),
                ], className="mb-3"),
            ]),
            dbc.Alert(id="notif-recipient-count", children=[
                html.I(className="fas fa-users me-2"),
                "Estimated recipients: 180,000 customers"
            ], color="info"),
            html.Div(id="send-notif-feedback", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Send Now", id="btn-send-notification", color="primary"),
            dbc.Button("Cancel", id="close-send-notif-modal", color="secondary", className="ms-2")
        ])
    ], id="send-notification-modal", is_open=False, size="lg")
    
    # Leak Simulation Results Modal
    leak_simulation_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-tint me-2 text-warning"), "Leak Scenario Simulation Results"])),
        dbc.ModalBody(id="leak-simulation-results"),
        dbc.ModalFooter([
            dbc.Button("Export Results", id="btn-export-simulation", color="info"),
            dbc.Button("Close", id="close-leak-simulation-modal", color="secondary", className="ms-2")
        ])
    ], id="leak-simulation-modal", is_open=False, size="xl")
    
    # Pressure Analysis Modal
    pressure_analysis_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-gauge-high me-2 text-info"), "Pressure Zone Analysis"])),
        dbc.ModalBody(id="pressure-analysis-results"),
        dbc.ModalFooter([
            dbc.Button("Apply Recommendations", id="btn-apply-pressure-rec", color="success"),
            dbc.Button("Close", id="close-pressure-analysis-modal", color="secondary", className="ms-2")
        ])
    ], id="pressure-analysis-modal", is_open=False, size="xl")
    
    # Detailed Benchmark Modal
    detailed_benchmark_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([html.I(className="fas fa-chart-line me-2"), "Detailed Performance Analysis"])),
        dbc.ModalBody(id="detailed-benchmark-content"),
        dbc.ModalFooter([
            dbc.Button("Download Full Report", id="btn-download-benchmark-report", color="primary"),
            dbc.Button("Close", id="close-detailed-benchmark-modal", color="secondary", className="ms-2")
        ])
    ], id="detailed-benchmark-modal", is_open=False, size="xl")
    
    # Download confirmation store
    download_store = dcc.Store(id="download-store", data={})
    
    # Main app layout - direct dashboard (login handled separately)
    # Create initial content for the command center tab
    initial_content = html.Div([kpi_row, main_content, ai_insights])
    
    app.layout = dbc.Container([
        dcc.Store(id='auth-store', storage_type='session', data={'authenticated': True, 'username': 'admin', 'role': 'Admin'}),
        header,
        tabs,
        html.Div(id="tab-content-area", children=initial_content),
        footer,
        # All modals
        notifications_modal,
        settings_modal,
        new_event_modal,
        filter_events_modal,
        view_event_modal,
        add_asset_modal,
        maintenance_modal,
        customer_search_modal,
        add_customer_modal,
        send_notification_modal,
        leak_simulation_modal,
        pressure_analysis_modal,
        detailed_benchmark_modal,
        download_store,
        dcc.Download(id="download-export"),
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),
        # Hidden placeholders for feedback elements
        html.Div([
            html.Div(id="twin-action-feedback"),
            html.Div(id="events-action-feedback"),
            html.Div(id="assets-action-feedback"),
            html.Div(id="benchmark-action-feedback"),
            html.Div(id="customer-action-feedback"),
            html.Div(id="new-event-feedback"),
            html.Div(id="add-customer-feedback"),
            html.Div(id="add-asset-feedback"),
            html.Div(id="maintenance-feedback"),
            html.Div(id="send-notification-feedback"),
            html.Div(id="settings-save-feedback"),
        ], style={'display': 'none'})
    ], fluid=True, style={'padding': '20px', 'minHeight': '100vh', 'backgroundColor': '#0F0F23'})
    
    # Callback to render tab content
    @app.callback(
        Output("tab-content-area", "children"),
        Input("main-tabs", "value")
    )
    def render_tab_content(tab):
        if tab == 'command':
            return html.Div([kpi_row, main_content, ai_insights])
        elif tab == 'twin':
            return create_digital_twin_page()
        elif tab == 'events':
            return create_events_page()
        elif tab == 'assets':
            return create_assets_page()
        elif tab == 'benchmark':
            return create_benchmark_page()
        elif tab == 'customers':
            return create_customers_page()
        return html.Div([kpi_row, main_content, ai_insights])
    
    # ========================================
    # HEADER MODAL CALLBACKS
    # ========================================
    @app.callback(
        Output("notifications-modal", "is_open"),
        [Input("btn-notifications", "n_clicks"),
         Input("close-notifications", "n_clicks")],
        [State("notifications-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_notifications_modal(open_clicks, close_clicks, is_open):
        return not is_open
    
    @app.callback(
        Output("settings-modal", "is_open"),
        [Input("btn-settings", "n_clicks"),
         Input("close-settings", "n_clicks")],
        [State("settings-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_settings_modal(open_clicks, close_clicks, is_open):
        return not is_open
    
    @app.callback(
        Output("settings-save-feedback", "children"),
        Input("btn-save-settings", "n_clicks"),
        [State("refresh-interval-select", "value"),
         State("default-view-select", "value"),
         State("notification-settings", "value")],
        prevent_initial_call=True
    )
    def save_settings(n_clicks, refresh_interval, default_view, notifications):
        if n_clicks:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Settings saved! Refresh: {refresh_interval}s, View: {default_view}, Notifications: {', '.join(notifications)}"
            ], color="success")
        return ""
    
    # Update time display
    @app.callback(
        Output("current-time", "children"),
        Input("interval-component", "n_intervals")
    )
    def update_time(n):
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # ========================================
    # DIGITAL TWIN - LEAK SIMULATION
    # ========================================
    @app.callback(
        Output("leak-simulation-modal", "is_open"),
        Output("leak-simulation-results", "children"),
        [Input("btn-leak-scenario", "n_clicks"),
         Input("close-leak-simulation-modal", "n_clicks")],
        [State("leak-simulation-modal", "is_open")],
        prevent_initial_call=True
    )
    def handle_leak_simulation(open_clicks, close_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id == "close-leak-simulation-modal":
            return False, ""
        
        if ctx.triggered_id == "btn-leak-scenario":
            # Generate simulation results
            simulation_results = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "Simulation Complete - Leak scenario analyzed successfully"
                ], color="success"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Simulation Parameters"),
                            dbc.CardBody([
                                html.P([html.Strong("Location: "), "Kabulonga Zone, Pipe K-045"]),
                                html.P([html.Strong("Leak Rate: "), "50 L/min (simulated)"]),
                                html.P([html.Strong("Duration: "), "24 hours"]),
                                html.P([html.Strong("Pressure Drop: "), "0.8 bar at leak point"]),
                            ])
                        ], className="metric-card")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Impact Analysis"),
                            dbc.CardBody([
                                html.P([html.Strong("Daily Water Loss: "), "72,000 L/day"]),
                                html.P([html.Strong("Monthly Loss: "), "2,160 m³"]),
                                html.P([html.Strong("Annual Cost: "), "ZMW 108,000"]),
                                html.P([html.Strong("Affected Customers: "), "~450 connections"]),
                            ])
                        ], className="metric-card")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Detection Probability"),
                            dbc.CardBody([
                                dbc.Progress(value=87, label="87%", color="success", className="mb-2"),
                                html.P([html.Strong("Acoustic Detection: "), "High confidence"]),
                                html.P([html.Strong("Pressure Analysis: "), "Detected"]),
                                html.P([html.Strong("Flow Analysis: "), "Anomaly flagged"]),
                            ])
                        ], className="metric-card")
                    ], width=4),
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("Pressure Propagation Map"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure(
                                data=[go.Heatmap(
                                    z=np.random.rand(10, 10) * 2 + 2,
                                    colorscale='Blues',
                                    colorbar=dict(title='Pressure (bar)')
                                )],
                                layout=go.Layout(
                                    title='Pressure Distribution After Leak',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    font={'color': '#E8E8E8'},
                                    height=300
                                )
                            ),
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="metric-card mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("Recommendations"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                                html.Strong("Priority 1: "), "Deploy field team to K-045 for verification within 4 hours"
                            ]),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-wrench text-warning me-2"),
                                html.Strong("Priority 2: "), "Prepare repair materials (200mm pipe section, couplings)"
                            ]),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-users text-info me-2"),
                                html.Strong("Priority 3: "), "Notify affected customers of potential service disruption"
                            ]),
                        ], flush=True)
                    ])
                ], className="metric-card")
            ])
            return True, simulation_results
        
        return is_open, ""
    
    # ========================================
    # DIGITAL TWIN - PRESSURE ANALYSIS
    # ========================================
    @app.callback(
        Output("pressure-analysis-modal", "is_open"),
        Output("pressure-analysis-results", "children"),
        [Input("btn-pressure-analysis", "n_clicks"),
         Input("close-pressure-analysis-modal", "n_clicks")],
        [State("pressure-analysis-modal", "is_open")],
        prevent_initial_call=True
    )
    def handle_pressure_analysis(open_clicks, close_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id == "close-pressure-analysis-modal":
            return False, ""
        
        if ctx.triggered_id == "btn-pressure-analysis":
            zones_data = [
                {"zone": "CBD", "current": 4.2, "optimal": 3.8, "savings": 12000, "status": "Over-pressured"},
                {"zone": "Kabulonga", "current": 3.8, "optimal": 3.5, "savings": 8500, "status": "Slightly high"},
                {"zone": "Woodlands", "current": 4.0, "optimal": 3.6, "savings": 10200, "status": "Over-pressured"},
                {"zone": "Matero", "current": 3.5, "optimal": 3.5, "savings": 0, "status": "Optimal"},
                {"zone": "Kabwata", "current": 3.7, "optimal": 3.4, "savings": 6800, "status": "Slightly high"},
                {"zone": "Industrial", "current": 4.5, "optimal": 4.2, "savings": 15000, "status": "Over-pressured"},
            ]
            
            analysis_results = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-chart-line me-2"),
                    "Analysis Complete - 6 pressure zones analyzed"
                ], color="info"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Summary"),
                            dbc.CardBody([
                                html.H3("52,500 L/day", className="text-success"),
                                html.P("Potential Leakage Reduction", className="text-muted"),
                                html.Hr(),
                                html.P([html.Strong("Annual Savings: "), "ZMW 2.6 million"]),
                                html.P([html.Strong("Infrastructure Life Extension: "), "+15%"]),
                            ])
                        ], className="metric-card")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Zone Performance"),
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=[
                                            go.Bar(name='Current', x=[z['zone'] for z in zones_data], y=[z['current'] for z in zones_data], marker_color='#0066CC'),
                                            go.Bar(name='Optimal', x=[z['zone'] for z in zones_data], y=[z['optimal'] for z in zones_data], marker_color='#28A745')
                                        ],
                                        layout=go.Layout(
                                            barmode='group',
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)',
                                            font={'color': '#E8E8E8'},
                                            height=250,
                                            margin=dict(l=40, r=20, t=20, b=40),
                                            yaxis=dict(title='Pressure (bar)', gridcolor='rgba(255,255,255,0.1)'),
                                            legend=dict(orientation='h', y=1.1)
                                        )
                                    ),
                                    config={'displayModeBar': False}
                                )
                            ])
                        ], className="metric-card")
                    ], width=8),
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("Zone-by-Zone Recommendations"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead(html.Tr([
                                html.Th("Zone"), html.Th("Current (bar)"), html.Th("Target (bar)"), 
                                html.Th("Adjustment"), html.Th("Daily Savings (L)"), html.Th("Status")
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td(z["zone"]),
                                    html.Td(f"{z['current']:.1f}"),
                                    html.Td(f"{z['optimal']:.1f}"),
                                    html.Td(f"-{z['current'] - z['optimal']:.1f}" if z['current'] > z['optimal'] else "None"),
                                    html.Td(f"{z['savings']:,}"),
                                    html.Td(dbc.Badge(z["status"], color="danger" if "Over" in z["status"] else "warning" if "high" in z["status"] else "success"))
                                ]) for z in zones_data
                            ])
                        ], striped=True, hover=True, responsive=True)
                    ])
                ], className="metric-card")
            ])
            return True, analysis_results
        
        return is_open, ""
    
    # ========================================
    # DIGITAL TWIN - EXPORT GEOJSON
    # ========================================
    @app.callback(
        Output("download-export", "data"),
        Input("btn-export-geojson", "n_clicks"),
        prevent_initial_call=True
    )
    def export_geojson(n_clicks):
        if n_clicks:
            # Create GeoJSON data
            geojson_data = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {"name": "Iolanda WTP", "type": "treatment"}, 
                     "geometry": {"type": "Point", "coordinates": [28.3228, -15.3847]}},
                    {"type": "Feature", "properties": {"name": "Chelstone Reservoir", "type": "reservoir"}, 
                     "geometry": {"type": "Point", "coordinates": [28.3500, -15.3600]}},
                    {"type": "Feature", "properties": {"name": "CBD Tank", "type": "tank"}, 
                     "geometry": {"type": "Point", "coordinates": [28.2833, -15.4167]}},
                    {"type": "Feature", "properties": {"name": "Kabulonga Tank", "type": "tank"}, 
                     "geometry": {"type": "Point", "coordinates": [28.3100, -15.4100]}},
                ]
            }
            return dict(content=json.dumps(geojson_data, indent=2), filename="lusaka_network_2026-01-12.geojson")
        return None
    
    @app.callback(
        Output("simulation-output", "children"),
        Input("btn-export-geojson", "n_clicks"),
        prevent_initial_call=True
    )
    def show_export_feedback(n_clicks):
        if n_clicks:
            return dbc.Alert([
                html.I(className="fas fa-download me-2"),
                "GeoJSON exported successfully! Check your downloads folder."
            ], color="success")
        return ""
    
    # ========================================
    # EVENTS - NEW EVENT MODAL
    # ========================================
    @app.callback(
        Output("new-event-modal", "is_open"),
        [Input("btn-new-event", "n_clicks"),
         Input("close-new-event-modal", "n_clicks"),
         Input("btn-submit-new-event", "n_clicks")],
        [State("new-event-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_new_event_modal(open_clicks, close_clicks, submit_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-new-event-modal", "btn-submit-new-event"]:
            return False
        return not is_open
    
    @app.callback(
        Output("new-event-feedback", "children"),
        Input("btn-submit-new-event", "n_clicks"),
        [State("event-type-input", "value"),
         State("event-severity-input", "value"),
         State("event-location-input", "value"),
         State("event-description-input", "value")],
        prevent_initial_call=True
    )
    def submit_new_event(n_clicks, event_type, severity, location, description):
        if n_clicks:
            event_id = f"EVT{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Event {event_id} created successfully!",
                html.Br(),
                html.Small(f"Type: {event_type}, Severity: {severity}, Location: {location}")
            ], color="success")
        return ""
    
    @app.callback(
        Output("events-action-feedback", "children"),
        Input("btn-submit-new-event", "n_clicks"),
        [State("event-type-input", "value"),
         State("event-location-input", "value")],
        prevent_initial_call=True
    )
    def show_event_created(n_clicks, event_type, location):
        if n_clicks:
            return dbc.Alert([
                html.I(className="fas fa-check me-2"),
                f"New event created: {event_type} at {location}"
            ], color="success", duration=5000)
        return ""
    
    # ========================================
    # EVENTS - FILTER MODAL
    # ========================================
    @app.callback(
        Output("filter-events-modal", "is_open"),
        [Input("btn-filter-events", "n_clicks"),
         Input("close-filter-modal", "n_clicks"),
         Input("btn-apply-filters", "n_clicks")],
        [State("filter-events-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_filter_modal(open_clicks, close_clicks, apply_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-filter-modal", "btn-apply-filters"]:
            return False
        return not is_open
    
    @app.callback(
        Output("filter-result-count", "children"),
        [Input("filter-status", "value"),
         Input("filter-severity", "value")],
        prevent_initial_call=True
    )
    def update_filter_count(status, severity):
        # Simulated filter count
        count = len(status or []) * len(severity or []) * 3
        return dbc.Alert([
            html.I(className="fas fa-filter me-2"),
            f"Filters will return approximately {count} events"
        ], color="info")
    
    # ========================================
    # EVENTS - EXPORT
    # ========================================
    @app.callback(
        Output("download-export", "data", allow_duplicate=True),
        Input("btn-export-events", "n_clicks"),
        prevent_initial_call=True
    )
    def export_events(n_clicks):
        if n_clicks:
            events_csv = "ID,Time,Type,Location,Severity,Status\n"
            events_csv += "EVT001,10:45,Leak Detected,Kabulonga Zone,High,Active\n"
            events_csv += "EVT002,09:30,Pressure Drop,CBD Main,Medium,Investigating\n"
            events_csv += "EVT003,08:15,Meter Anomaly,Industrial Zone,Low,Resolved\n"
            events_csv += "EVT004,07:00,Pipe Burst,Matero,Critical,Active\n"
            events_csv += "EVT005,Yesterday,NRW Alert,DMA-05,Medium,Resolved\n"
            return dict(content=events_csv, filename=f"events_report_{datetime.now().strftime('%Y-%m-%d')}.csv")
        return None
    
    # ========================================
    # ASSETS - ADD ASSET MODAL
    # ========================================
    @app.callback(
        Output("add-asset-modal", "is_open"),
        [Input("btn-add-asset", "n_clicks"),
         Input("close-add-asset-modal", "n_clicks"),
         Input("btn-submit-new-asset", "n_clicks")],
        [State("add-asset-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_add_asset_modal(open_clicks, close_clicks, submit_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-add-asset-modal", "btn-submit-new-asset"]:
            return False
        return not is_open
    
    @app.callback(
        Output("add-asset-feedback", "children"),
        Input("btn-submit-new-asset", "n_clicks"),
        [State("asset-name-input", "value"),
         State("asset-type-input", "value"),
         State("asset-location-input", "value")],
        prevent_initial_call=True
    )
    def submit_new_asset(n_clicks, name, asset_type, location):
        if n_clicks and name:
            asset_id = f"AST{datetime.now().strftime('%Y%m%d%H%M')}"
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Asset {asset_id} registered successfully!",
                html.Br(),
                html.Small(f"Name: {name}, Type: {asset_type}, Location: {location}")
            ], color="success")
        return ""
    
    # ========================================
    # ASSETS - MAINTENANCE MODAL
    # ========================================
    @app.callback(
        Output("maintenance-modal", "is_open"),
        [Input("btn-schedule-maintenance", "n_clicks"),
         Input("close-maintenance-modal", "n_clicks"),
         Input("btn-submit-maintenance", "n_clicks")],
        [State("maintenance-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_maintenance_modal(open_clicks, close_clicks, submit_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-maintenance-modal", "btn-submit-maintenance"]:
            return False
        return not is_open
    
    @app.callback(
        Output("schedule-maint-feedback", "children"),
        Input("btn-submit-maintenance", "n_clicks"),
        [State("maint-asset-select", "value"),
         State("maint-type-select", "value"),
         State("maint-date-input", "value"),
         State("maint-team-select", "value")],
        prevent_initial_call=True
    )
    def submit_maintenance(n_clicks, asset, maint_type, date, team):
        if n_clicks:
            wo_id = f"WO{datetime.now().strftime('%Y%m%d%H%M')}"
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Work Order {wo_id} created!",
                html.Br(),
                html.Small(f"Asset: {asset}, Type: {maint_type}, Date: {date}, Team: {team}")
            ], color="success")
        return ""
    
    @app.callback(
        Output("asset-action-feedback", "children"),
        Input("btn-submit-maintenance", "n_clicks"),
        [State("maint-asset-select", "value")],
        prevent_initial_call=True
    )
    def show_maintenance_scheduled(n_clicks, asset):
        if n_clicks:
            return dbc.Alert([
                html.I(className="fas fa-wrench me-2"),
                f"Maintenance scheduled for {asset}"
            ], color="success", duration=5000)
        return ""
    
    # ========================================
    # ASSETS - GENERATE REPORT
    # ========================================
    @app.callback(
        Output("download-export", "data", allow_duplicate=True),
        Input("btn-asset-report", "n_clicks"),
        prevent_initial_call=True
    )
    def generate_asset_report(n_clicks):
        if n_clicks:
            report = f"""AQUAWATCH ASSET HEALTH REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
=====================================

SUMMARY
-------
Total Assets: 2,450
Average Health Score: 72/100
Critical Assets: 45
Assets Due for Replacement: 12

PRIORITY ASSETS
---------------
1. Matero Old Cast Iron - Health: 28% - ACTION: Replace immediately
2. Chelstone Pump P2 - Health: 45% - ACTION: Schedule maintenance
3. CBD Isolation Valve - Health: 55% - ACTION: Inspect seals
4. Kabulonga Tank - Health: 62% - ACTION: Monitor closely
5. Woodlands PRV - Health: 88% - ACTION: Routine maintenance

RECOMMENDATIONS
---------------
- Allocate ZMW 2.5M for emergency replacements
- Schedule 45 preventive maintenance visits
- Train 2 additional maintenance crews

Report generated by AquaWatch NRW Detection System
"""
            return dict(content=report, filename=f"asset_health_report_{datetime.now().strftime('%Y-%m-%d')}.txt")
        return None
    
    # ========================================
    # BENCHMARKING - DETAILED ANALYSIS
    # ========================================
    @app.callback(
        Output("detailed-benchmark-modal", "is_open"),
        Output("detailed-benchmark-content", "children"),
        [Input("btn-detailed-benchmark", "n_clicks"),
         Input("close-detailed-benchmark-modal", "n_clicks")],
        [State("detailed-benchmark-modal", "is_open")],
        prevent_initial_call=True
    )
    def show_detailed_benchmark(open_clicks, close_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id == "close-detailed-benchmark-modal":
            return False, ""
        
        if ctx.triggered_id == "btn-detailed-benchmark":
            content = html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("24-Month NRW Trend"),
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=[go.Scatter(
                                            x=pd.date_range(start='2024-01-01', periods=24, freq='M'),
                                            y=[48, 47, 46, 45, 44, 43, 43, 42, 41, 40, 40, 39, 
                                               39, 38, 38, 37, 37, 37, 36, 36, 36, 36, 36, 36],
                                            mode='lines+markers',
                                            fill='tozeroy',
                                            fillcolor='rgba(0,102,204,0.2)',
                                            line=dict(color='#0066CC', width=2)
                                        )],
                                        layout=go.Layout(
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)',
                                            font={'color': '#E8E8E8'},
                                            height=250,
                                            margin=dict(l=40, r=20, t=20, b=40),
                                            yaxis=dict(title='NRW %', gridcolor='rgba(255,255,255,0.1)'),
                                        )
                                    ),
                                    config={'displayModeBar': False}
                                )
                            ])
                        ], className="metric-card")
                    ], width=8),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Progress Summary"),
                            dbc.CardBody([
                                html.H3("12%", className="text-success"),
                                html.P("NRW Reduction (24 months)"),
                                html.Hr(),
                                html.P([html.Strong("Start: "), "48% (Jan 2024)"]),
                                html.P([html.Strong("Current: "), "36.2% (Jan 2026)"]),
                                html.P([html.Strong("Target: "), "30% (Dec 2026)"]),
                                html.P([html.Strong("Water Saved: "), "45,000 m³/day"]),
                            ])
                        ], className="metric-card")
                    ], width=4),
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("KPI Comparison Table"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead(html.Tr([
                                html.Th("KPI"), html.Th("LWSC"), html.Th("Regional Avg"), 
                                html.Th("Best Practice"), html.Th("Gap"), html.Th("Trend")
                            ])),
                            html.Tbody([
                                html.Tr([html.Td("NRW Rate"), html.Td("36.2%"), html.Td("35%"), html.Td("5%"), html.Td("-1.2%"), html.Td(dbc.Badge("↓", color="success"))]),
                                html.Tr([html.Td("Service Coverage"), html.Td("78%"), html.Td("85%"), html.Td("98%"), html.Td("-7%"), html.Td(dbc.Badge("↑", color="success"))]),
                                html.Tr([html.Td("Supply Continuity"), html.Td("67%"), html.Td("75%"), html.Td("100%"), html.Td("-8%"), html.Td(dbc.Badge("↑", color="success"))]),
                                html.Tr([html.Td("Collection Efficiency"), html.Td("82%"), html.Td("85%"), html.Td("99%"), html.Td("-3%"), html.Td(dbc.Badge("↑", color="success"))]),
                                html.Tr([html.Td("Water Quality"), html.Td("95.5%"), html.Td("96%"), html.Td("100%"), html.Td("-0.5%"), html.Td(dbc.Badge("→", color="secondary"))]),
                            ])
                        ], striped=True, hover=True, responsive=True)
                    ])
                ], className="metric-card")
            ])
            return True, content
        
        return is_open, ""
    
    # ========================================
    # BENCHMARKING - EXPORT
    # ========================================
    @app.callback(
        Output("download-export", "data", allow_duplicate=True),
        Input("btn-export-benchmark", "n_clicks"),
        prevent_initial_call=True
    )
    def export_benchmark(n_clicks):
        if n_clicks:
            csv_content = "KPI,LWSC,Regional Average,Best Practice,Gap\n"
            csv_content += "NRW Rate,36.2%,35%,5%,-1.2%\n"
            csv_content += "Service Coverage,78%,85%,98%,-7%\n"
            csv_content += "Supply Continuity,67%,75%,100%,-8%\n"
            csv_content += "Collection Efficiency,82%,85%,99%,-3%\n"
            csv_content += "Water Quality,95.5%,96%,100%,-0.5%\n"
            return dict(content=csv_content, filename=f"benchmark_report_{datetime.now().strftime('%Y-%m-%d')}.csv")
        return None
    
    @app.callback(
        Output("benchmark-action-feedback", "children"),
        [Input("btn-update-benchmark", "n_clicks"),
         Input("btn-share-benchmark", "n_clicks"),
         Input("btn-period-benchmark", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_benchmark_buttons(update, share, period):
        from dash import ctx
        if ctx.triggered_id == "btn-update-benchmark":
            return dbc.Alert([html.I(className="fas fa-check me-2"), "Benchmark data updated from IWA database"], color="success", duration=5000)
        elif ctx.triggered_id == "btn-share-benchmark":
            return dbc.Alert([html.I(className="fas fa-link me-2"), "Share link: https://aquawatch.zm/share/benchmark/2026"], color="info")
        elif ctx.triggered_id == "btn-period-benchmark":
            return dbc.Alert([html.I(className="fas fa-calendar me-2"), "Select period: Monthly | Quarterly | Annual"], color="secondary")
        return ""
    
    # ========================================
    # CUSTOMERS - ADD CUSTOMER MODAL
    # ========================================
    @app.callback(
        Output("add-customer-modal", "is_open"),
        [Input("btn-add-customer", "n_clicks"),
         Input("close-add-customer-modal", "n_clicks"),
         Input("btn-submit-new-customer", "n_clicks")],
        [State("add-customer-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_add_customer_modal(open_clicks, close_clicks, submit_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-add-customer-modal", "btn-submit-new-customer"]:
            return False
        return not is_open
    
    @app.callback(
        Output("add-customer-feedback", "children"),
        Input("btn-submit-new-customer", "n_clicks"),
        [State("cust-name-input", "value"),
         State("cust-type-input", "value"),
         State("cust-zone-input", "value"),
         State("cust-phone-input", "value")],
        prevent_initial_call=True
    )
    def submit_new_customer(n_clicks, name, cust_type, zone, phone):
        if n_clicks and name:
            account_no = f"LW{datetime.now().strftime('%Y%m%d%H%M')}"
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Customer registered! Account: {account_no}",
                html.Br(),
                html.Small(f"Name: {name}, Type: {cust_type}, Zone: {zone}")
            ], color="success")
        return ""
    
    # ========================================
    # CUSTOMERS - SEARCH MODAL
    # ========================================
    @app.callback(
        Output("customer-search-modal", "is_open"),
        [Input("btn-search-customer", "n_clicks"),
         Input("close-customer-search-modal", "n_clicks")],
        [State("customer-search-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_customer_search_modal(open_clicks, close_clicks, is_open):
        return not is_open
    
    @app.callback(
        Output("customer-search-results", "children"),
        Input("btn-do-customer-search", "n_clicks"),
        [State("customer-search-input", "value")],
        prevent_initial_call=True
    )
    def do_customer_search(n_clicks, search_term):
        if n_clicks and search_term:
            # Simulated search results
            results = [
                {"account": "LW2024001234", "name": "John Banda", "zone": "Kabulonga", "balance": "ZMW 450"},
                {"account": "LW2024001235", "name": "Mary Banda", "zone": "Kabulonga", "balance": "ZMW 0"},
                {"account": "LW2023008765", "name": "Banda Enterprises", "zone": "Industrial", "balance": "ZMW 12,500"},
            ]
            return dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(r["name"]),
                        dbc.Badge(r["zone"], color="info", className="ms-2"),
                        html.Span(r["balance"], className="float-end text-success" if r["balance"] == "ZMW 0" else "float-end text-warning")
                    ]),
                    html.Small(f"Account: {r['account']}", className="text-muted")
                ], action=True) for r in results
            ], flush=True)
        return html.P("Enter search criteria above to find customers.", className="text-muted text-center")
    
    # ========================================
    # CUSTOMERS - NOTIFICATION MODAL
    # ========================================
    @app.callback(
        Output("send-notification-modal", "is_open"),
        [Input("btn-notify-customers", "n_clicks"),
         Input("close-send-notif-modal", "n_clicks"),
         Input("btn-send-notification", "n_clicks")],
        [State("send-notification-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_send_notification_modal(open_clicks, close_clicks, send_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id in ["close-send-notif-modal", "btn-send-notification"]:
            return False
        return not is_open
    
    @app.callback(
        Output("send-notif-feedback", "children"),
        Input("btn-send-notification", "n_clicks"),
        [State("notif-type-input", "value"),
         State("notif-target-input", "value"),
         State("notif-message-input", "value")],
        prevent_initial_call=True
    )
    def send_notification(n_clicks, notif_type, target, message):
        if n_clicks and message:
            counts = {"all": 180000, "kabulonga": 25000, "cbd": 15000, "woodlands": 20000, "arrears": 8500, "high_usage": 3200}
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Notification sent via {notif_type.upper()}!",
                html.Br(),
                html.Small(f"Recipients: {counts.get(target, 1000):,} customers in {target}")
            ], color="success")
        return ""
    
    @app.callback(
        Output("notif-recipient-count", "children"),
        Input("notif-target-input", "value"),
        prevent_initial_call=True
    )
    def update_recipient_count(target):
        counts = {"all": 180000, "kabulonga": 25000, "cbd": 15000, "woodlands": 20000, "arrears": 8500, "high_usage": 3200}
        return [html.I(className="fas fa-users me-2"), f"Estimated recipients: {counts.get(target, 1000):,} customers"]
    
    # ========================================
    # CUSTOMERS - EXPORT
    # ========================================
    @app.callback(
        Output("download-export", "data", allow_duplicate=True),
        Input("btn-export-customers", "n_clicks"),
        prevent_initial_call=True
    )
    def export_customers(n_clicks):
        if n_clicks:
            csv_content = "Account,Name,Type,Zone,Balance,Status\n"
            csv_content += "LW2024001234,John Banda,Residential,Kabulonga,450,Active\n"
            csv_content += "LW2024001235,Mary Mwanza,Residential,Woodlands,0,Active\n"
            csv_content += "LW2023008765,Banda Enterprises,Commercial,Industrial,12500,Active\n"
            return dict(content=csv_content, filename=f"customers_{datetime.now().strftime('%Y-%m-%d')}.csv")
        return None
    
    return app


# Create the app
app = create_app()
server = app.server


if __name__ == "__main__":
    print("=" * 60)
    print("AquaWatch World-Class Dashboard")
    print("=" * 60)
    print("\nStarting server...")
    print("Dashboard URL: http://localhost:8050")
    print("\nFeatures integrated:")
    print("  ✓ Digital Twin Network Visualization")
    print("  ✓ Central Event Management")
    print("  ✓ AI-Powered Insights")
    print("  ✓ Asset Health Scoring")
    print("  ✓ Performance Benchmarking")
    print("  ✓ Pressure Zone Management")
    print("  ✓ NRW Trend Analytics")
    print("\nPress Ctrl+C to stop")
    
    app.run(debug=False, host='0.0.0.0', port=8050)
