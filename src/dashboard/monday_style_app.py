"""
AquaWatch NRW - Monday.com Style Dashboard
==========================================

Modern, colorful board-based UI inspired by Monday.com
- Kanban-style boards with status columns
- Color-coded items and statuses
- Clean, minimal design with accent colors
- Smooth animations and transitions
- Group-based organization

IWA Water Balance Aligned
"""

import dash
from dash import dcc, html, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# =============================================================================
# MONDAY.COM STYLE CONFIGURATION
# =============================================================================

# Monday.com inspired color palette
MONDAY_COLORS = {
    # Status colors
    "done": "#00C875",           # Green
    "working_on_it": "#FDAB3D",  # Orange
    "stuck": "#E2445C",          # Red
    "pending": "#C4C4C4",        # Gray
    "in_review": "#A25DDC",      # Purple
    "planning": "#579BFC",       # Blue
    
    # NRW Status colors (aligned with IWA)
    "critical": "#E2445C",       # Red - Critical Real Loss
    "high": "#FDAB3D",           # Orange - High priority
    "medium": "#579BFC",         # Blue - Medium priority
    "low": "#00C875",            # Green - Low/Healthy
    
    # UI colors
    "primary": "#0073EA",        # Monday blue
    "secondary": "#323338",      # Dark gray
    "background": "#F6F7FB",     # Light gray bg
    "surface": "#FFFFFF",        # White cards
    "text_primary": "#323338",
    "text_secondary": "#676879",
    "border": "#E6E9EF",
    
    # Accent colors for variety
    "accent_1": "#037F4C",       # Dark green
    "accent_2": "#D974B0",       # Pink
    "accent_3": "#9D99B9",       # Lavender
    "accent_4": "#66CCFF",       # Light blue
}

# Monday.com style CSS
MONDAY_STYLES = """
/* Monday.com Inspired Styles */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

body {
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: #F6F7FB;
    color: #323338;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #F6F7FB;
}

::-webkit-scrollbar-thumb {
    background: #C4C4C4;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #676879;
}

/* Header styles */
.monday-header {
    background: linear-gradient(135deg, #0073EA 0%, #0060B9 100%);
    padding: 20px 30px;
    color: white;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 4px 12px rgba(0, 115, 234, 0.3);
}

/* Board container */
.monday-board {
    background: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    margin-bottom: 20px;
    overflow: hidden;
}

/* Board header */
.board-header {
    padding: 16px 24px;
    border-bottom: 1px solid #E6E9EF;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.board-title {
    font-size: 18px;
    font-weight: 600;
    color: #323338;
    display: flex;
    align-items: center;
    gap: 10px;
}

.board-title-icon {
    width: 8px;
    height: 24px;
    border-radius: 4px;
}

/* Group styles */
.monday-group {
    margin: 0;
    border-bottom: 1px solid #E6E9EF;
}

.group-header {
    padding: 12px 24px;
    background: #FAFBFC;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    user-select: none;
}

.group-header:hover {
    background: #F0F3F7;
}

.group-color-bar {
    width: 6px;
    height: 20px;
    border-radius: 3px;
}

.group-title {
    font-weight: 500;
    font-size: 14px;
    color: #323338;
}

.group-count {
    background: #E6E9EF;
    color: #676879;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
}

/* Row styles */
.monday-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr 0.5fr;
    align-items: center;
    padding: 12px 24px;
    border-bottom: 1px solid #E6E9EF;
    transition: background 0.2s ease;
}

.monday-row:hover {
    background: #F5F6F8;
}

.row-main {
    display: flex;
    align-items: center;
    gap: 12px;
}

.row-checkbox {
    width: 16px;
    height: 16px;
    border: 2px solid #C4C4C4;
    border-radius: 4px;
    cursor: pointer;
}

.row-title {
    font-weight: 500;
    font-size: 14px;
    color: #323338;
}

.row-subtitle {
    font-size: 12px;
    color: #676879;
}

/* Status pill */
.status-pill {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    text-align: center;
    color: white;
    min-width: 90px;
}

/* NRW Category badge */
.nrw-badge {
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
}

/* Progress bar */
.monday-progress {
    height: 8px;
    border-radius: 4px;
    background: #E6E9EF;
    overflow: hidden;
}

.monday-progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

/* KPI Card */
.monday-kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border-left: 4px solid;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.monday-kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.kpi-label {
    font-size: 12px;
    color: #676879;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 32px;
    font-weight: 600;
    color: #323338;
    line-height: 1;
}

.kpi-trend {
    font-size: 12px;
    margin-top: 8px;
}

.kpi-trend.positive { color: #00C875; }
.kpi-trend.negative { color: #E2445C; }

/* Chart card */
.monday-chart-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-title {
    font-size: 16px;
    font-weight: 600;
    color: #323338;
    margin-bottom: 16px;
}

/* Sidebar */
.monday-sidebar {
    background: #292F4C;
    min-height: 100vh;
    padding: 20px 0;
}

.sidebar-logo {
    padding: 0 20px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 20px;
}

.sidebar-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    color: rgba(255,255,255,0.7);
    text-decoration: none;
    font-size: 14px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.sidebar-item:hover {
    background: rgba(255,255,255,0.1);
    color: white;
}

.sidebar-item.active {
    background: rgba(0, 115, 234, 0.3);
    color: white;
    border-left: 3px solid #0073EA;
}

/* Alert toast */
.monday-alert {
    background: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    border-left: 4px solid;
    margin-bottom: 12px;
    display: flex;
    gap: 12px;
    align-items: flex-start;
}

.alert-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: white;
}

/* Button styles */
.monday-btn {
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.monday-btn-primary {
    background: #0073EA;
    color: white;
}

.monday-btn-primary:hover {
    background: #0060B9;
}

.monday-btn-secondary {
    background: #F0F3F7;
    color: #323338;
}

.monday-btn-secondary:hover {
    background: #E6E9EF;
}

/* Tab navigation */
.monday-tabs {
    display: flex;
    gap: 4px;
    background: #F0F3F7;
    padding: 4px;
    border-radius: 8px;
    width: fit-content;
}

.monday-tab {
    padding: 8px 20px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #676879;
    cursor: pointer;
    transition: all 0.2s ease;
}

.monday-tab:hover {
    color: #323338;
}

.monday-tab.active {
    background: white;
    color: #323338;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

/* Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.3s ease;
}

/* Pulse animation for alerts */
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(226, 68, 92, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(226, 68, 92, 0); }
    100% { box-shadow: 0 0 0 0 rgba(226, 68, 92, 0); }
}

.pulse-alert {
    animation: pulse 2s infinite;
}
"""


# =============================================================================
# INITIALIZE DASH APP
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
    ]
)

app.title = "AquaWatch NRW | Water Intelligence"
server = app.server


# =============================================================================
# SAMPLE DATA GENERATORS
# =============================================================================

def generate_nrw_board_data() -> List[Dict]:
    """Generate Monday.com style board data for NRW alerts."""
    
    items = [
        # Real Losses - Critical
        {
            "id": "NRW-2026-00142",
            "title": "Distribution Main Leak - Kafue Road",
            "dma": "DMA-KIT-003",
            "category": "Real Loss - Leakage",
            "status": "critical",
            "probability": 0.92,
            "loss_m3_day": 125.5,
            "assigned": "John M.",
            "due": datetime.now() + timedelta(hours=4),
            "night_detection": True,
            "group": "Critical - Immediate Action"
        },
        {
            "id": "NRW-2026-00138",
            "title": "Service Connection Leak - Chilenje",
            "dma": "DMA-LSK-002",
            "category": "Real Loss - Service",
            "status": "critical",
            "probability": 0.88,
            "loss_m3_day": 45.2,
            "assigned": "Sarah K.",
            "due": datetime.now() + timedelta(hours=6),
            "night_detection": True,
            "group": "Critical - Immediate Action"
        },
        # High Priority
        {
            "id": "NRW-2026-00135",
            "title": "Night Flow Anomaly - Industrial Zone",
            "dma": "DMA-NDO-001",
            "category": "Real Loss - Leakage",
            "status": "high",
            "probability": 0.76,
            "loss_m3_day": 68.0,
            "assigned": "Peter N.",
            "due": datetime.now() + timedelta(hours=12),
            "night_detection": True,
            "group": "High Priority - Today"
        },
        {
            "id": "NRW-2026-00132",
            "title": "Meter Under-registration Cluster",
            "dma": "DMA-KIT-001",
            "category": "Apparent Loss - Meter",
            "status": "high",
            "probability": 0.71,
            "loss_m3_day": 32.5,
            "assigned": "Grace M.",
            "due": datetime.now() + timedelta(hours=24),
            "night_detection": False,
            "group": "High Priority - Today"
        },
        # Medium Priority
        {
            "id": "NRW-2026-00128",
            "title": "Pressure Gradient Change - Ndola CBD",
            "dma": "DMA-NDO-002",
            "category": "Real Loss - Leakage",
            "status": "medium",
            "probability": 0.58,
            "loss_m3_day": 22.0,
            "assigned": "—",
            "due": datetime.now() + timedelta(hours=48),
            "night_detection": False,
            "group": "Medium Priority - This Week"
        },
        {
            "id": "NRW-2026-00125",
            "title": "Suspected Unauthorized Use",
            "dma": "DMA-LSK-003",
            "category": "Apparent Loss - Unauthorized",
            "status": "medium",
            "probability": 0.62,
            "loss_m3_day": 18.5,
            "assigned": "Revenue Team",
            "due": datetime.now() + timedelta(hours=72),
            "night_detection": False,
            "group": "Medium Priority - This Week"
        },
        # Low Priority / Monitoring
        {
            "id": "NRW-2026-00120",
            "title": "Minor Variance - Monitoring",
            "dma": "DMA-KIT-002",
            "category": "Unknown",
            "status": "low",
            "probability": 0.42,
            "loss_m3_day": 8.0,
            "assigned": "AI Monitoring",
            "due": datetime.now() + timedelta(days=7),
            "night_detection": False,
            "group": "Monitoring"
        }
    ]
    
    return items


def generate_dma_summary() -> List[Dict]:
    """Generate DMA summary data."""
    return [
        {"dma": "DMA-KIT-001", "name": "Kitwe Central", "nrw": 28.5, "status": "high", "alerts": 2, "trend": -2.3},
        {"dma": "DMA-KIT-002", "name": "Kitwe North", "nrw": 22.1, "status": "medium", "alerts": 0, "trend": -1.5},
        {"dma": "DMA-KIT-003", "name": "Kitwe South", "nrw": 45.2, "status": "critical", "alerts": 5, "trend": +3.2},
        {"dma": "DMA-NDO-001", "name": "Ndola CBD", "nrw": 31.0, "status": "high", "alerts": 1, "trend": -0.8},
        {"dma": "DMA-NDO-002", "name": "Ndola Industrial", "nrw": 18.5, "status": "low", "alerts": 0, "trend": -3.1},
        {"dma": "DMA-LSK-001", "name": "Lusaka Central", "nrw": 35.8, "status": "high", "alerts": 3, "trend": +1.2},
        {"dma": "DMA-LSK-002", "name": "Lusaka East", "nrw": 52.3, "status": "critical", "alerts": 7, "trend": +4.5},
        {"dma": "DMA-LSK-003", "name": "Lusaka West", "nrw": 25.0, "status": "medium", "alerts": 1, "trend": -1.8},
    ]


# =============================================================================
# UI COMPONENTS - MONDAY.COM STYLE
# =============================================================================

def create_sidebar():
    """Create Monday.com style sidebar navigation."""
    
    return html.Div([
        # Logo
        html.Div([
            html.Div([
                html.I(className="fas fa-water", style={"fontSize": "24px", "marginRight": "10px"}),
                html.Span("AquaWatch", style={"fontSize": "20px", "fontWeight": "600"})
            ], style={"color": "white", "display": "flex", "alignItems": "center"})
        ], className="sidebar-logo"),
        
        # Navigation items
        html.Div([
            html.Div("MAIN", style={"color": "rgba(255,255,255,0.4)", "fontSize": "11px", 
                                    "padding": "8px 20px", "letterSpacing": "1px"}),
            
            html.Div([
                html.I(className="fas fa-home", style={"width": "20px"}),
                "Dashboard"
            ], className="sidebar-item active", id="nav-dashboard"),
            
            html.Div([
                html.I(className="fas fa-clipboard-list", style={"width": "20px"}),
                "NRW Board"
            ], className="sidebar-item", id="nav-board"),
            
            html.Div([
                html.I(className="fas fa-bell", style={"width": "20px"}),
                "Alerts",
                html.Span("7", style={
                    "background": MONDAY_COLORS["critical"],
                    "color": "white",
                    "padding": "2px 8px",
                    "borderRadius": "10px",
                    "fontSize": "11px",
                    "marginLeft": "auto"
                })
            ], className="sidebar-item", id="nav-alerts"),
            
            html.Div([
                html.I(className="fas fa-wrench", style={"width": "20px"}),
                "Work Orders"
            ], className="sidebar-item", id="nav-workorders"),
            
            html.Div("ANALYTICS", style={"color": "rgba(255,255,255,0.4)", "fontSize": "11px", 
                                          "padding": "20px 20px 8px", "letterSpacing": "1px"}),
            
            html.Div([
                html.I(className="fas fa-chart-line", style={"width": "20px"}),
                "Performance"
            ], className="sidebar-item", id="nav-performance"),
            
            html.Div([
                html.I(className="fas fa-map-marked-alt", style={"width": "20px"}),
                "DMA Map"
            ], className="sidebar-item", id="nav-map"),
            
            html.Div("IWA REPORTS", style={"color": "rgba(255,255,255,0.4)", "fontSize": "11px", 
                                           "padding": "20px 20px 8px", "letterSpacing": "1px"}),
            
            html.Div([
                html.I(className="fas fa-file-alt", style={"width": "20px"}),
                "Water Balance"
            ], className="sidebar-item", id="nav-balance"),
            
            html.Div([
                html.I(className="fas fa-tachometer-alt", style={"width": "20px"}),
                "ILI Report"
            ], className="sidebar-item", id="nav-ili"),
        ])
    ], className="monday-sidebar", style={"width": "240px", "position": "fixed", "left": 0, "top": 0})


def create_status_pill(status: str, text: str = None) -> html.Div:
    """Create a Monday.com style status pill."""
    
    colors = {
        "critical": MONDAY_COLORS["critical"],
        "high": MONDAY_COLORS["high"],
        "medium": MONDAY_COLORS["medium"],
        "low": MONDAY_COLORS["low"],
        "done": MONDAY_COLORS["done"],
        "working": MONDAY_COLORS["working_on_it"],
        "stuck": MONDAY_COLORS["stuck"],
    }
    
    labels = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "done": "Done",
        "working": "Working on it",
        "stuck": "Stuck",
    }
    
    return html.Div(
        text or labels.get(status, status.title()),
        className="status-pill",
        style={"backgroundColor": colors.get(status, MONDAY_COLORS["pending"])}
    )


def create_nrw_category_badge(category: str) -> html.Span:
    """Create IWA NRW category badge."""
    
    colors = {
        "Real Loss - Leakage": "#E2445C",
        "Real Loss - Service": "#FF7575",
        "Real Loss - Overflow": "#BB3354",
        "Apparent Loss - Meter": "#A25DDC",
        "Apparent Loss - Unauthorized": "#784BD1",
        "Unknown": "#C4C4C4",
    }
    
    return html.Span(
        category,
        className="nrw-badge",
        style={
            "backgroundColor": colors.get(category, "#C4C4C4"),
            "color": "white"
        }
    )


def create_kpi_card(label: str, value: str, trend: str = None, trend_positive: bool = True, 
                    color: str = MONDAY_COLORS["primary"]) -> html.Div:
    """Create Monday.com style KPI card."""
    
    trend_element = None
    if trend:
        trend_element = html.Div([
            html.I(className=f"fas fa-arrow-{'up' if trend_positive else 'down'}", 
                   style={"marginRight": "4px"}),
            trend
        ], className=f"kpi-trend {'positive' if trend_positive else 'negative'}")
    
    return html.Div([
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value"),
        trend_element
    ], className="monday-kpi-card fade-in", style={"borderLeftColor": color})


def create_board_row(item: Dict) -> html.Div:
    """Create a Monday.com style board row."""
    
    probability_color = MONDAY_COLORS["critical"] if item["probability"] > 0.8 else \
                       MONDAY_COLORS["high"] if item["probability"] > 0.6 else \
                       MONDAY_COLORS["medium"]
    
    night_badge = html.Span([
        html.I(className="fas fa-moon", style={"marginRight": "4px"}),
        "MNF"
    ], style={
        "backgroundColor": "#292F4C",
        "color": "white",
        "padding": "2px 8px",
        "borderRadius": "4px",
        "fontSize": "10px",
        "marginLeft": "8px"
    }) if item.get("night_detection") else None
    
    return html.Div([
        # Main title column
        html.Div([
            html.Div(className="row-checkbox"),
            html.Div([
                html.Div([
                    html.Span(item["title"], className="row-title"),
                    night_badge
                ]),
                html.Div(f"{item['id']} • {item['dma']}", className="row-subtitle")
            ])
        ], className="row-main"),
        
        # Status column
        html.Div([
            create_status_pill(item["status"])
        ], style={"display": "flex", "justifyContent": "center"}),
        
        # Category column
        html.Div([
            create_nrw_category_badge(item["category"])
        ], style={"display": "flex", "justifyContent": "center"}),
        
        # Probability column
        html.Div([
            html.Div([
                html.Div(
                    style={
                        "width": f"{item['probability']*100}%",
                        "backgroundColor": probability_color
                    },
                    className="monday-progress-fill"
                )
            ], className="monday-progress", style={"width": "60px"}),
            html.Span(f"{item['probability']:.0%}", style={
                "fontSize": "12px", "marginLeft": "8px", "color": "#676879"
            })
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),
        
        # Loss column
        html.Div([
            html.Span(f"{item['loss_m3_day']:.1f}", style={"fontWeight": "500"}),
            html.Span(" m³/d", style={"color": "#676879", "fontSize": "11px"})
        ], style={"textAlign": "center"}),
        
        # Assigned column
        html.Div([
            html.Div(
                item["assigned"][0] if item["assigned"] != "—" else "?",
                style={
                    "width": "28px",
                    "height": "28px",
                    "borderRadius": "50%",
                    "backgroundColor": MONDAY_COLORS["primary"] if item["assigned"] != "—" else "#E6E9EF",
                    "color": "white" if item["assigned"] != "—" else "#676879",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "12px",
                    "fontWeight": "500"
                }
            )
        ], style={"display": "flex", "justifyContent": "center"})
        
    ], className="monday-row")


def create_group_header(title: str, count: int, color: str) -> html.Div:
    """Create Monday.com style group header."""
    
    return html.Div([
        html.I(className="fas fa-chevron-down", style={"color": "#676879", "fontSize": "12px"}),
        html.Div(className="group-color-bar", style={"backgroundColor": color}),
        html.Span(title, className="group-title"),
        html.Span(f"{count} items", className="group-count")
    ], className="group-header")


def create_board_header() -> html.Div:
    """Create Monday.com style board header with columns."""
    
    return html.Div([
        html.Div("Item", style={"gridColumn": "1", "paddingLeft": "40px"}),
        html.Div("Status", style={"textAlign": "center"}),
        html.Div("NRW Category", style={"textAlign": "center"}),
        html.Div("Probability", style={"textAlign": "center"}),
        html.Div("Est. Loss", style={"textAlign": "center"}),
        html.Div("Owner", style={"textAlign": "center"}),
    ], style={
        "display": "grid",
        "gridTemplateColumns": "2fr 1fr 1fr 1fr 1fr 0.5fr",
        "padding": "10px 24px",
        "backgroundColor": "#FAFBFC",
        "borderBottom": "1px solid #E6E9EF",
        "fontSize": "12px",
        "fontWeight": "500",
        "color": "#676879",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px"
    })


def create_alert_toast(item: Dict) -> html.Div:
    """Create Monday.com style alert toast."""
    
    icon_bg = MONDAY_COLORS[item["status"]]
    
    return html.Div([
        html.Div([
            html.I(className="fas fa-exclamation", style={"fontSize": "12px"})
        ], className="alert-icon", style={"backgroundColor": icon_bg}),
        html.Div([
            html.Div([
                html.Span(item["title"], style={"fontWeight": "500", "color": "#323338"}),
                html.Span(f" • {item['dma']}", style={"color": "#676879", "fontSize": "12px"})
            ]),
            html.Div([
                create_nrw_category_badge(item["category"]),
                html.Span(f" {item['probability']:.0%} probability", 
                         style={"fontSize": "12px", "color": "#676879", "marginLeft": "8px"})
            ], style={"marginTop": "6px"})
        ], style={"flex": "1"}),
        html.Div([
            html.Button("View", className="monday-btn monday-btn-primary", 
                       style={"fontSize": "12px", "padding": "6px 12px"})
        ])
    ], className="monday-alert" + (" pulse-alert" if item["status"] == "critical" else ""),
       style={"borderLeftColor": icon_bg})


# =============================================================================
# MAIN LAYOUTS
# =============================================================================

def create_main_dashboard():
    """Create the main Monday.com style dashboard."""
    
    board_data = generate_nrw_board_data()
    dma_data = generate_dma_summary()
    
    # Group items
    groups = {}
    for item in board_data:
        group = item["group"]
        if group not in groups:
            groups[group] = []
        groups[group].append(item)
    
    group_colors = {
        "Critical - Immediate Action": MONDAY_COLORS["critical"],
        "High Priority - Today": MONDAY_COLORS["high"],
        "Medium Priority - This Week": MONDAY_COLORS["medium"],
        "Monitoring": MONDAY_COLORS["low"]
    }
    
    # Calculate KPIs
    total_loss = sum(item["loss_m3_day"] for item in board_data)
    critical_count = len([i for i in board_data if i["status"] == "critical"])
    avg_nrw = sum(d["nrw"] for d in dma_data) / len(dma_data)
    
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.H1("Water Intelligence Dashboard", 
                       style={"fontSize": "24px", "fontWeight": "600", "marginBottom": "4px"}),
                html.P("IWA Water Balance Aligned • Real-time NRW Monitoring", 
                      style={"opacity": "0.8", "fontSize": "14px", "margin": 0})
            ]),
            html.Div([
                html.Span("Last updated: ", style={"opacity": "0.7"}),
                html.Span(datetime.now().strftime("%H:%M:%S"), style={"fontWeight": "500"}),
                html.Button([
                    html.I(className="fas fa-sync-alt", style={"marginRight": "6px"}),
                    "Refresh"
                ], className="monday-btn", style={
                    "backgroundColor": "rgba(255,255,255,0.2)",
                    "color": "white",
                    "marginLeft": "16px"
                })
            ], style={"display": "flex", "alignItems": "center"})
        ], className="monday-header", style={
            "display": "flex", 
            "justifyContent": "space-between", 
            "alignItems": "center"
        }),
        
        # Content
        html.Div([
            # KPI Row
            dbc.Row([
                dbc.Col([
                    create_kpi_card(
                        "National NRW",
                        f"{avg_nrw:.1f}%",
                        "↓ 2.3% vs last month",
                        True,
                        MONDAY_COLORS["high"]
                    )
                ], width=3),
                dbc.Col([
                    create_kpi_card(
                        "Critical Alerts",
                        str(critical_count),
                        "Immediate action required",
                        False,
                        MONDAY_COLORS["critical"]
                    )
                ], width=3),
                dbc.Col([
                    create_kpi_card(
                        "Est. Daily Loss",
                        f"{total_loss:.0f} m³",
                        f"~${total_loss * 2.5:.0f}/day revenue",
                        False,
                        MONDAY_COLORS["medium"]
                    )
                ], width=3),
                dbc.Col([
                    create_kpi_card(
                        "Active DMAs",
                        str(len(dma_data)),
                        "All sensors online",
                        True,
                        MONDAY_COLORS["low"]
                    )
                ], width=3),
            ], className="mb-4"),
            
            # Main content row
            dbc.Row([
                # Left column - Board
                dbc.Col([
                    html.Div([
                        # Board header
                        html.Div([
                            html.Div([
                                html.Div(className="board-title-icon", 
                                        style={"backgroundColor": MONDAY_COLORS["primary"]}),
                                html.Span("NRW Detection Board", className="board-title")
                            ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
                            html.Div([
                                html.Div([
                                    html.Span("Main View", className="monday-tab active"),
                                    html.Span("Kanban", className="monday-tab"),
                                    html.Span("Timeline", className="monday-tab"),
                                ], className="monday-tabs")
                            ])
                        ], className="board-header"),
                        
                        # Column headers
                        create_board_header(),
                        
                        # Groups and rows
                        html.Div([
                            html.Div([
                                create_group_header(group_name, len(items), group_colors.get(group_name, "#C4C4C4")),
                                html.Div([
                                    create_board_row(item) for item in items
                                ])
                            ], className="monday-group")
                            for group_name, items in groups.items()
                        ])
                        
                    ], className="monday-board")
                ], width=8),
                
                # Right column - Alerts & Quick stats
                dbc.Col([
                    # Active alerts
                    html.Div([
                        html.Div([
                            html.Span("🔔 Live Alerts", style={"fontWeight": "600"}),
                            html.Span(f"{len([i for i in board_data if i['status'] in ['critical', 'high']])}",
                                     style={
                                         "backgroundColor": MONDAY_COLORS["critical"],
                                         "color": "white",
                                         "padding": "2px 10px",
                                         "borderRadius": "12px",
                                         "fontSize": "12px",
                                         "marginLeft": "10px"
                                     })
                        ], style={"marginBottom": "16px"}),
                        
                        html.Div([
                            create_alert_toast(item) 
                            for item in board_data if item["status"] in ["critical", "high"]
                        ], style={"maxHeight": "400px", "overflowY": "auto"})
                    ], className="monday-chart-card mb-4"),
                    
                    # Quick DMA status
                    html.Div([
                        html.Div("DMA Status Overview", className="chart-title"),
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Span(d["name"], style={"fontWeight": "500", "fontSize": "13px"}),
                                    html.Div([
                                        create_status_pill(d["status"], f"{d['nrw']:.0f}%"),
                                    ], style={"marginLeft": "auto"})
                                ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}),
                                html.Div([
                                    html.Div(
                                        style={
                                            "width": f"{min(d['nrw'], 60)/60*100}%",
                                            "backgroundColor": MONDAY_COLORS["critical"] if d["nrw"] > 40 else 
                                                             MONDAY_COLORS["high"] if d["nrw"] > 30 else
                                                             MONDAY_COLORS["medium"] if d["nrw"] > 20 else
                                                             MONDAY_COLORS["low"]
                                        },
                                        className="monday-progress-fill"
                                    )
                                ], className="monday-progress", style={"marginTop": "8px"})
                            ], style={"marginBottom": "16px"})
                            for d in sorted(dma_data, key=lambda x: x["nrw"], reverse=True)[:5]
                        ])
                    ], className="monday-chart-card")
                    
                ], width=4)
            ])
            
        ], style={"padding": "24px"})
        
    ], style={"marginLeft": "240px", "backgroundColor": MONDAY_COLORS["background"], "minHeight": "100vh"})


# =============================================================================
# APP LAYOUT
# =============================================================================

app.layout = html.Div([
    # Inject custom styles using dcc.Markdown for CSS
    dcc.Store(id='styles-store'),
    html.Div(style={'display': 'none'}, children=[
        dcc.Markdown(f"<style>{MONDAY_STYLES}</style>", dangerously_allow_html=True)
    ]),
    
    # Sidebar
    create_sidebar(),
    
    # Main content
    html.Div(id="page-content", children=[
        create_main_dashboard()
    ])
], style={'fontFamily': "'Figtree', 'Roboto', sans-serif"})


# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)
