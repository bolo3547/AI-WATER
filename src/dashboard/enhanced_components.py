"""
AquaWatch NRW - Enhanced Dashboard Components
==============================================

Integration module for all new AquaWatch features.
Adds dashboard views for:
- Work Orders
- Community Reports  
- Weather/Predictions
- Financial Analytics
- Regulatory Compliance
- Field Technician Tracking

For Zambian/Southern African water utilities.
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
import json


# =============================================================================
# STYLING
# =============================================================================

COLORS = {
    "primary": "#1E88E5",      # Blue
    "success": "#43A047",      # Green
    "warning": "#FB8C00",      # Orange  
    "danger": "#E53935",       # Red
    "info": "#00ACC1",         # Cyan
    "dark": "#263238",         # Dark gray
    "light": "#F5F7FA",        # Light gray
    "white": "#FFFFFF"
}

CARD_STYLE = {
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    "marginBottom": "16px"
}


# =============================================================================
# WORK ORDER DASHBOARD
# =============================================================================

def create_work_order_stats(work_orders: List[Dict] = None) -> html.Div:
    """Create work order statistics cards."""
    
    # Sample data if none provided
    if not work_orders:
        work_orders = [
            {"status": "assigned", "priority": "critical"},
            {"status": "assigned", "priority": "high"},
            {"status": "in_progress", "priority": "high"},
            {"status": "in_progress", "priority": "medium"},
            {"status": "completed", "priority": "high"},
            {"status": "completed", "priority": "medium"},
            {"status": "completed", "priority": "low"},
        ]
    
    total = len(work_orders)
    open_orders = len([w for w in work_orders if w["status"] not in ["completed", "cancelled"]])
    critical = len([w for w in work_orders if w["priority"] == "critical"])
    completed_today = len([w for w in work_orders if w["status"] == "completed"])
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Open Orders", className="text-muted mb-1"),
                    html.H2(open_orders, className="mb-0"),
                    html.Small(f"of {total} total", className="text-muted")
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Critical", className="text-muted mb-1"),
                    html.H2(critical, className="mb-0 text-danger"),
                    html.Small("Immediate response", className="text-muted")
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("In Progress", className="text-muted mb-1"),
                    html.H2(len([w for w in work_orders if w["status"] == "in_progress"]), 
                           className="mb-0 text-warning"),
                    html.Small("Active repairs", className="text-muted")
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Completed Today", className="text-muted mb-1"),
                    html.H2(completed_today, className="mb-0 text-success"),
                    html.Small("✓ Resolved", className="text-muted")
                ])
            ], style=CARD_STYLE)
        ], md=3),
    ], className="mb-4")


def create_work_order_table(work_orders: List[Dict] = None) -> html.Div:
    """Create work order table."""
    
    if not work_orders:
        work_orders = [
            {
                "id": "WO-2024-001",
                "title": "Major leak - Cairo Road",
                "zone": "Lusaka CBD",
                "priority": "critical",
                "status": "in_progress",
                "technician": "Moses Banda",
                "created": "2 hours ago"
            },
            {
                "id": "WO-2024-002", 
                "title": "Pressure drop - Industrial Area",
                "zone": "Ndola North",
                "priority": "high",
                "status": "assigned",
                "technician": "Grace Mwanza",
                "created": "5 hours ago"
            },
            {
                "id": "WO-2024-003",
                "title": "Meter replacement",
                "zone": "Kitwe Central",
                "priority": "medium",
                "status": "assigned",
                "technician": "John Phiri",
                "created": "1 day ago"
            }
        ]
    
    priority_badges = {
        "critical": dbc.Badge("CRITICAL", color="danger", className="me-1"),
        "high": dbc.Badge("HIGH", color="warning", className="me-1"),
        "medium": dbc.Badge("MEDIUM", color="info", className="me-1"),
        "low": dbc.Badge("LOW", color="secondary", className="me-1")
    }
    
    status_badges = {
        "assigned": dbc.Badge("Assigned", color="secondary"),
        "en_route": dbc.Badge("En Route", color="info"),
        "in_progress": dbc.Badge("In Progress", color="warning"),
        "completed": dbc.Badge("Completed", color="success"),
    }
    
    rows = []
    for wo in work_orders:
        rows.append(
            html.Tr([
                html.Td(wo["id"]),
                html.Td([priority_badges.get(wo["priority"], ""), wo["title"]]),
                html.Td(wo["zone"]),
                html.Td(wo.get("technician", "-")),
                html.Td(status_badges.get(wo["status"], wo["status"])),
                html.Td(wo.get("created", "-")),
                html.Td(
                    dbc.Button("View", color="primary", size="sm", outline=True)
                )
            ])
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Active Work Orders", className="mb-0"),
        ]),
        dbc.CardBody([
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("ID"),
                        html.Th("Description"),
                        html.Th("Zone"),
                        html.Th("Technician"),
                        html.Th("Status"),
                        html.Th("Created"),
                        html.Th("Action")
                    ])
                ]),
                html.Tbody(rows)
            ], className="table table-hover")
        ])
    ], style=CARD_STYLE)


# =============================================================================
# COMMUNITY REPORTS DASHBOARD
# =============================================================================

def create_community_reports_map(reports: List[Dict] = None) -> dcc.Graph:
    """Create map of community reports."""
    
    if not reports:
        reports = [
            {"lat": -15.4167, "lng": 28.2833, "type": "leak", "status": "pending", "reporter": "Anonymous"},
            {"lat": -15.4200, "lng": 28.2900, "type": "burst_pipe", "status": "verified", "reporter": "John M."},
            {"lat": -15.4100, "lng": 28.2750, "type": "low_pressure", "status": "resolved", "reporter": "Grace C."},
            {"lat": -12.8167, "lng": 28.2167, "type": "leak", "status": "pending", "reporter": "Anonymous"},  # Kitwe
            {"lat": -12.9700, "lng": 28.6333, "type": "no_water", "status": "verified", "reporter": "Peter N."},  # Ndola
        ]
    
    df = pd.DataFrame(reports)
    
    color_map = {
        "pending": COLORS["warning"],
        "verified": COLORS["danger"],
        "resolved": COLORS["success"]
    }
    
    df["color"] = df["status"].map(color_map)
    
    fig = go.Figure(go.Scattermapbox(
        lat=df["lat"],
        lon=df["lng"],
        mode="markers",
        marker=dict(
            size=14,
            color=df["color"],
            opacity=0.8
        ),
        text=df.apply(lambda r: f"{r['type']}<br>Status: {r['status']}<br>By: {r['reporter']}", axis=1),
        hoverinfo="text"
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=-15.0, lng=28.3),
            zoom=6
        ),
        height=400,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def create_community_stats() -> html.Div:
    """Create community engagement stats."""
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Reports Today", className="text-muted mb-1"),
                    html.H2("12", className="mb-0"),
                    dbc.Progress(value=75, color="success", className="mt-2", style={"height": "5px"})
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Pending Review", className="text-muted mb-1"),
                    html.H2("5", className="mb-0 text-warning"),
                    dbc.Progress(value=40, color="warning", className="mt-2", style={"height": "5px"})
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Active Reporters", className="text-muted mb-1"),
                    html.H2("234", className="mb-0 text-primary"),
                    html.Small("Top: John M. (156 pts)", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Leaks Found", className="text-muted mb-1"),
                    html.H2("89", className="mb-0 text-success"),
                    html.Small("Via community reports", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
    ])


# =============================================================================
# FINANCIAL DASHBOARD
# =============================================================================

def create_financial_summary() -> html.Div:
    """Create financial impact summary."""
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-money-bill-wave fa-2x text-danger"),
                    ], className="float-end"),
                    html.H6("Daily Revenue Loss", className="text-muted"),
                    html.H3("$4,250", className="text-danger"),
                    html.Small([
                        html.I(className="fas fa-arrow-up text-danger me-1"),
                        "8% from last week"
                    ])
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-tint fa-2x text-info"),
                    ], className="float-end"),
                    html.H6("Water Lost Today", className="text-muted"),
                    html.H3("2,450 m³", className="text-info"),
                    html.Small([
                        "≈ 980 households' daily use"
                    ])
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-line fa-2x text-success"),
                    ], className="float-end"),
                    html.H6("Recovery Potential", className="text-muted"),
                    html.H3("$1.2M/year", className="text-success"),
                    html.Small([
                        "With 50% NRW reduction"
                    ])
                ])
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-percent fa-2x text-warning"),
                    ], className="float-end"),
                    html.H6("Current NRW", className="text-muted"),
                    html.H3("38.5%", className="text-warning"),
                    html.Small([
                        "Target: 25% by 2025"
                    ])
                ])
            ], style=CARD_STYLE)
        ], md=3),
    ])


def create_nrw_cost_chart() -> dcc.Graph:
    """Create NRW cost over time chart."""
    
    dates = pd.date_range(start="2024-01-01", periods=12, freq="M")
    
    fig = go.Figure()
    
    # Lost revenue
    fig.add_trace(go.Bar(
        x=dates,
        y=[45000, 48000, 52000, 49000, 47000, 51000, 55000, 53000, 50000, 48000, 46000, 44000],
        name="Lost Revenue ($)",
        marker_color=COLORS["danger"]
    ))
    
    # Production waste
    fig.add_trace(go.Bar(
        x=dates,
        y=[22000, 24000, 26000, 24500, 23500, 25500, 27500, 26500, 25000, 24000, 23000, 22000],
        name="Production Waste ($)",
        marker_color=COLORS["warning"]
    ))
    
    # Target line
    fig.add_trace(go.Scatter(
        x=dates,
        y=[40000] * 12,
        name="Target",
        line=dict(color=COLORS["success"], dash="dash")
    ))
    
    fig.update_layout(
        title="Monthly NRW Financial Impact",
        barmode="stack",
        height=350,
        margin=dict(l=50, r=20, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def create_intervention_roi_chart() -> dcc.Graph:
    """Create intervention ROI comparison chart."""
    
    interventions = [
        {"name": "Active Leak Detection", "cost": 25000, "payback": 1.8, "roi": 180},
        {"name": "Pressure Management", "cost": 45000, "payback": 2.5, "roi": 145},
        {"name": "Meter Replacement", "cost": 60000, "payback": 4.2, "roi": 85},
        {"name": "Pipe Replacement", "cost": 150000, "payback": 6.5, "roi": 65},
        {"name": "DMA Creation", "cost": 80000, "payback": 3.8, "roi": 110},
    ]
    
    df = pd.DataFrame(interventions)
    
    fig = px.scatter(
        df,
        x="payback",
        y="roi",
        size="cost",
        text="name",
        color="roi",
        color_continuous_scale=["red", "yellow", "green"],
        labels={
            "payback": "Payback Period (years)",
            "roi": "ROI (%)",
            "cost": "Capital Cost ($)"
        }
    )
    
    fig.update_traces(textposition="top center")
    fig.update_layout(
        title="Intervention ROI Analysis",
        height=350,
        margin=dict(l=50, r=20, t=50, b=50)
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


# =============================================================================
# COMPLIANCE DASHBOARD
# =============================================================================

def create_compliance_scorecard() -> html.Div:
    """Create regulatory compliance scorecard."""
    
    kpis = [
        {"name": "Non-Revenue Water", "value": 38.5, "target": 25, "unit": "%", "lower_better": True},
        {"name": "Water Quality Compliance", "value": 92.0, "target": 95, "unit": "%", "lower_better": False},
        {"name": "Hours of Supply", "value": 18, "target": 20, "unit": "hrs", "lower_better": False},
        {"name": "Metering Ratio", "value": 75.0, "target": 90, "unit": "%", "lower_better": False},
        {"name": "Collection Efficiency", "value": 72.0, "target": 85, "unit": "%", "lower_better": False},
        {"name": "Coverage Rate", "value": 78.0, "target": 85, "unit": "%", "lower_better": False},
    ]
    
    cards = []
    for kpi in kpis:
        if kpi["lower_better"]:
            is_good = kpi["value"] <= kpi["target"]
            progress = max(0, 100 - (kpi["value"] / kpi["target"] * 100 - 100))
        else:
            is_good = kpi["value"] >= kpi["target"]
            progress = min(100, kpi["value"] / kpi["target"] * 100)
        
        color = "success" if is_good else ("warning" if progress > 70 else "danger")
        
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(kpi["name"], className="text-muted mb-2"),
                        html.H4(f"{kpi['value']}{kpi['unit']}", className=f"mb-1 text-{color}"),
                        html.Small(f"Target: {kpi['target']}{kpi['unit']}", className="text-muted"),
                        dbc.Progress(
                            value=progress, 
                            color=color, 
                            className="mt-2",
                            style={"height": "6px"}
                        )
                    ])
                ], style=CARD_STYLE)
            ], md=4, className="mb-3")
        )
    
    return dbc.Row(cards)


def create_compliance_radar() -> dcc.Graph:
    """Create compliance radar chart."""
    
    categories = ["NRW", "Water Quality", "Supply Hours", 
                  "Metering", "Collection", "Coverage"]
    
    # Normalized scores (0-100)
    current = [65, 97, 90, 83, 85, 92]  # Current performance
    target = [100, 100, 100, 100, 100, 100]  # Target
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=current,
        theta=categories,
        fill="toself",
        name="Current",
        line_color=COLORS["primary"]
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=target,
        theta=categories,
        fill="toself",
        name="Target",
        line_color=COLORS["success"],
        opacity=0.3
    ))
    
    fig.update_layout(
        title="NWASCO Compliance Score",
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


# =============================================================================
# WEATHER & PREDICTIONS DASHBOARD
# =============================================================================

def create_weather_risk_card() -> html.Div:
    """Create weather-based risk assessment card."""
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-cloud-sun me-2"),
            "Weather Risk Assessment"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Current Conditions", className="text-muted"),
                    html.P([
                        html.I(className="fas fa-sun text-warning me-2"),
                        "Hot & Dry - 32°C"
                    ]),
                    html.Small("Lusaka, Zambia", className="text-muted")
                ], md=4),
                dbc.Col([
                    html.H6("Pipe Burst Risk", className="text-muted"),
                    dbc.Progress([
                        dbc.Progress(value=65, color="warning", bar=True)
                    ], className="mb-2"),
                    html.Small("Moderate-High (65%)", className="text-warning")
                ], md=4),
                dbc.Col([
                    html.H6("Recommended Action", className="text-muted"),
                    dbc.Badge("Increase Monitoring", color="warning", className="me-1"),
                    html.Br(),
                    html.Small("Ground movement risk due to soil drying")
                ], md=4)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H6("7-Day Forecast Impact"),
                    html.Small([
                        html.Span("Mon: ", className="fw-bold"), "Low risk", html.Br(),
                        html.Span("Tue: ", className="fw-bold"), "Low risk", html.Br(),
                        html.Span("Wed: ", className="fw-bold"), html.Span("Moderate - Rain expected", className="text-warning"), html.Br(),
                        html.Span("Thu: ", className="fw-bold"), html.Span("High - Heavy rain", className="text-danger"), html.Br(),
                        html.Span("Fri: ", className="fw-bold"), "Moderate risk", html.Br(),
                    ])
                ])
            ])
        ])
    ], style=CARD_STYLE)


# =============================================================================
# FIELD TECHNICIAN TRACKING
# =============================================================================

def create_technician_map() -> dcc.Graph:
    """Create map showing technician locations."""
    
    technicians = [
        {"name": "Moses Banda", "lat": -15.4100, "lng": 28.2800, "status": "busy", "current_job": "WO-001"},
        {"name": "Grace Mwanza", "lat": -15.4250, "lng": 28.3000, "status": "available", "current_job": None},
        {"name": "John Phiri", "lat": -12.8200, "lng": 28.2200, "status": "en_route", "current_job": "WO-003"},
        {"name": "Peter Ng'andu", "lat": -12.9750, "lng": 28.6400, "status": "busy", "current_job": "WO-005"},
    ]
    
    df = pd.DataFrame(technicians)
    
    status_colors = {
        "available": COLORS["success"],
        "busy": COLORS["warning"],
        "en_route": COLORS["info"],
        "offline": COLORS["dark"]
    }
    
    df["color"] = df["status"].map(status_colors)
    
    fig = go.Figure(go.Scattermapbox(
        lat=df["lat"],
        lon=df["lng"],
        mode="markers+text",
        marker=dict(size=16, color=df["color"]),
        text=df["name"],
        textposition="top center",
        hovertext=df.apply(
            lambda r: f"{r['name']}<br>Status: {r['status']}<br>Job: {r['current_job'] or 'None'}", 
            axis=1
        ),
        hoverinfo="text"
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=-14.5, lng=28.3),
            zoom=5.5
        ),
        height=400,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def create_technician_stats() -> html.Div:
    """Create technician statistics."""
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-users fa-2x text-primary mb-2"),
                    html.H4("12", className="mb-0"),
                    html.Small("Active Technicians", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-truck fa-2x text-info mb-2"),
                    html.H4("5", className="mb-0"),
                    html.Small("En Route", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-wrench fa-2x text-warning mb-2"),
                    html.H4("7", className="mb-0"),
                    html.Small("On Site Working", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-check-circle fa-2x text-success mb-2"),
                    html.H4("23", className="mb-0"),
                    html.Small("Jobs Today", className="text-muted")
                ], className="text-center")
            ], style=CARD_STYLE)
        ], md=3),
    ])


# =============================================================================
# MAIN LAYOUT COMPONENTS
# =============================================================================

def create_enhanced_sidebar() -> html.Div:
    """Create enhanced sidebar with all new modules."""
    
    nav_items = [
        {"icon": "fas fa-tachometer-alt", "label": "Dashboard", "href": "/", "active": True},
        {"icon": "fas fa-map-marked-alt", "label": "Network Map", "href": "/map"},
        {"icon": "fas fa-exclamation-triangle", "label": "Alerts", "href": "/alerts"},
        {"icon": "fas fa-clipboard-list", "label": "Work Orders", "href": "/work-orders"},
        {"icon": "fas fa-users", "label": "Community", "href": "/community"},
        {"icon": "fas fa-dollar-sign", "label": "Financial", "href": "/financial"},
        {"icon": "fas fa-file-contract", "label": "Compliance", "href": "/compliance"},
        {"icon": "fas fa-cloud-sun", "label": "Weather/Risk", "href": "/weather"},
        {"icon": "fas fa-hard-hat", "label": "Field Teams", "href": "/field-teams"},
        {"icon": "fas fa-cog", "label": "Settings", "href": "/settings"},
    ]
    
    items = []
    for item in nav_items:
        items.append(
            dbc.NavLink([
                html.I(className=f"{item['icon']} me-2"),
                item["label"]
            ], href=item["href"], active=item.get("active", False))
        )
    
    return html.Div([
        html.Div([
            html.H4([
                html.I(className="fas fa-water me-2"),
                "AquaWatch"
            ], className="text-primary mb-0"),
            html.Small("NRW Intelligence", className="text-muted")
        ], className="p-3 border-bottom"),
        dbc.Nav(items, vertical=True, pills=True, className="p-2")
    ], style={
        "width": "240px",
        "minHeight": "100vh",
        "backgroundColor": COLORS["white"],
        "borderRight": "1px solid #e0e0e0"
    })


def create_work_orders_page() -> html.Div:
    """Create work orders page layout."""
    
    return html.Div([
        html.H4("Work Order Management", className="mb-4"),
        create_work_order_stats(),
        create_work_order_table()
    ])


def create_community_page() -> html.Div:
    """Create community reports page layout."""
    
    return html.Div([
        html.H4("Community Reports", className="mb-4"),
        create_community_stats(),
        html.Div(className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Report Locations"),
                    dbc.CardBody([create_community_reports_map()])
                ], style=CARD_STYLE)
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top Contributors"),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("🥇 ", style={"fontSize": "1.2em"}),
                                "John Mwale", 
                                dbc.Badge("156 pts", color="warning", className="float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Span("🥈 ", style={"fontSize": "1.2em"}),
                                "Grace Chanda",
                                dbc.Badge("142 pts", color="secondary", className="float-end")
                            ], className="mb-2"),
                            html.Div([
                                html.Span("🥉 ", style={"fontSize": "1.2em"}),
                                "Peter Ng'andu",
                                dbc.Badge("98 pts", color="warning", className="float-end")
                            ], className="mb-2"),
                        ])
                    ])
                ], style=CARD_STYLE),
                dbc.Card([
                    dbc.CardHeader("Report Types"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.pie(
                                names=["Leaks", "Bursts", "Low Pressure", "No Water", "Quality"],
                                values=[45, 20, 15, 12, 8],
                                hole=0.5
                            ).update_layout(
                                height=200,
                                margin=dict(l=20, r=20, t=20, b=20),
                                showlegend=True,
                                legend=dict(orientation="h")
                            ),
                            config={"displayModeBar": False}
                        )
                    ])
                ], style=CARD_STYLE)
            ], md=4)
        ])
    ])


def create_financial_page() -> html.Div:
    """Create financial analytics page layout."""
    
    return html.Div([
        html.H4("Financial Analytics", className="mb-4"),
        create_financial_summary(),
        html.Div(className="mb-4"),
        dbc.Row([
            dbc.Col([create_nrw_cost_chart()], md=6),
            dbc.Col([create_intervention_roi_chart()], md=6)
        ])
    ])


def create_compliance_page() -> html.Div:
    """Create compliance dashboard page layout."""
    
    return html.Div([
        html.H4([
            html.I(className="fas fa-file-contract me-2"),
            "NWASCO Regulatory Compliance"
        ], className="mb-4"),
        dbc.Alert([
            html.I(className="fas fa-calendar me-2"),
            "Next NWASCO Report Due: January 31, 2025 (18 days)"
        ], color="info"),
        create_compliance_scorecard(),
        dbc.Row([
            dbc.Col([create_compliance_radar()], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent Audit Trail"),
                    dbc.CardBody([
                        html.Div([
                            html.Small("Today 14:23", className="text-muted"),
                            html.P("KPI recorded: NRW = 38.5%", className="mb-1"),
                        ], className="mb-3 border-bottom pb-2"),
                        html.Div([
                            html.Small("Today 10:15", className="text-muted"),
                            html.P("Water quality test: Compliant ✓", className="mb-1"),
                        ], className="mb-3 border-bottom pb-2"),
                        html.Div([
                            html.Small("Yesterday 16:45", className="text-muted"),
                            html.P("Incident resolved: INC-2024-089", className="mb-1"),
                        ], className="mb-3 border-bottom pb-2"),
                        html.Div([
                            html.Small("Yesterday 09:00", className="text-muted"),
                            html.P("Monthly report generated", className="mb-1"),
                        ], className="mb-3"),
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ])
    ])


def create_field_teams_page() -> html.Div:
    """Create field teams tracking page layout."""
    
    return html.Div([
        html.H4("Field Team Operations", className="mb-4"),
        create_technician_stats(),
        html.Div(className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Live Technician Locations"),
                    dbc.CardBody([create_technician_map()])
                ], style=CARD_STYLE)
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Team Status"),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("●", className="text-success me-2"),
                                "Moses Banda",
                                dbc.Badge("On Site", color="warning", className="float-end")
                            ], className="py-2 border-bottom"),
                            html.Div([
                                html.Span("●", className="text-success me-2"),
                                "Grace Mwanza",
                                dbc.Badge("Available", color="success", className="float-end")
                            ], className="py-2 border-bottom"),
                            html.Div([
                                html.Span("●", className="text-info me-2"),
                                "John Phiri",
                                dbc.Badge("En Route", color="info", className="float-end")
                            ], className="py-2 border-bottom"),
                            html.Div([
                                html.Span("●", className="text-success me-2"),
                                "Peter Ng'andu",
                                dbc.Badge("On Site", color="warning", className="float-end")
                            ], className="py-2"),
                        ])
                    ])
                ], style=CARD_STYLE),
                dbc.Card([
                    dbc.CardHeader("Today's Performance"),
                    dbc.CardBody([
                        html.Div([
                            html.P("Avg Response Time", className="text-muted mb-1"),
                            html.H4("28 min", className="text-success mb-3"),
                            html.P("Avg Repair Time", className="text-muted mb-1"),
                            html.H4("1.8 hrs", className="text-primary mb-0"),
                        ])
                    ])
                ], style=CARD_STYLE)
            ], md=4)
        ])
    ])


def create_weather_page() -> html.Div:
    """Create weather/predictions page layout."""
    
    return html.Div([
        html.H4("Weather & Predictive Analytics", className="mb-4"),
        dbc.Row([
            dbc.Col([create_weather_risk_card()], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("AI Predictions - Next 7 Days"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(
                                    x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                                    y=[15, 18, 35, 65, 45, 30, 22],
                                    mode="lines+markers",
                                    name="Burst Risk %",
                                    line=dict(color=COLORS["danger"])
                                ),
                                go.Scatter(
                                    x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                                    y=[25, 22, 40, 55, 50, 35, 28],
                                    mode="lines+markers",
                                    name="Leak Risk %",
                                    line=dict(color=COLORS["warning"])
                                )
                            ]).update_layout(
                                height=300,
                                margin=dict(l=40, r=20, t=30, b=40),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02)
                            ),
                            config={"displayModeBar": False}
                        )
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Maintenance Windows"),
                    dbc.CardBody([
                        html.P("Recommended optimal maintenance periods based on weather:"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                dbc.Badge("OPTIMAL", color="success", className="me-2"),
                                "Monday 06:00-12:00 - Clear, mild conditions"
                            ]),
                            dbc.ListGroupItem([
                                dbc.Badge("GOOD", color="info", className="me-2"),
                                "Tuesday 08:00-16:00 - Partly cloudy"
                            ]),
                            dbc.ListGroupItem([
                                dbc.Badge("AVOID", color="danger", className="me-2"),
                                "Thursday - Heavy rain expected"
                            ]),
                        ])
                    ])
                ], style=CARD_STYLE)
            ])
        ])
    ])


# =============================================================================
# EXPORT LAYOUT FUNCTION
# =============================================================================

def get_enhanced_layout(page: str = "dashboard") -> html.Div:
    """Get the layout for a specific page."""
    
    pages = {
        "work-orders": create_work_orders_page(),
        "community": create_community_page(),
        "financial": create_financial_page(),
        "compliance": create_compliance_page(),
        "field-teams": create_field_teams_page(),
        "weather": create_weather_page(),
    }
    
    return pages.get(page, html.Div("Page not found"))


# Export components for use in main app
__all__ = [
    "create_work_order_stats",
    "create_work_order_table",
    "create_community_reports_map",
    "create_community_stats",
    "create_financial_summary",
    "create_nrw_cost_chart",
    "create_intervention_roi_chart",
    "create_compliance_scorecard",
    "create_compliance_radar",
    "create_weather_risk_card",
    "create_technician_map",
    "create_technician_stats",
    "create_enhanced_sidebar",
    "create_work_orders_page",
    "create_community_page",
    "create_financial_page",
    "create_compliance_page",
    "create_field_teams_page",
    "create_weather_page",
    "get_enhanced_layout",
    "COLORS",
    "CARD_STYLE"
]
