"""
AquaWatch Pro - Enterprise Water Intelligence Platform
=======================================================

Ultra-premium dashboard inspired by:
- Notion (clean, minimal)
- Linear (dark mode perfection)
- Figma (professional data display)
- Arc Browser (modern aesthetics)
"""

import dash
from dash import html, dcc, callback, Input, Output, State
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# =============================================================================
# INITIALIZE APP - DISABLE DEV TOOLS FOR CLEAN UI
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="AquaWatch Pro | Water Intelligence",
    update_title=None,  # Disable "Updating..." title
)

# Disable dev tools for clean production look
app.config.suppress_callback_exceptions = True

# =============================================================================
# PREMIUM STYLES
# =============================================================================

STYLES = """
/* ============================================
   AQUAWATCH PRO - ENTERPRISE DASHBOARD
   ============================================ */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body, html {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0d1117;
    color: #e6edf3;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
}

/* Hide Dash dev tools */
._dash-loading, ._dash-error, .dash-debug-menu, 
[class*="dash-debug"], [class*="_dash-error"],
.dash-error-card, ._dash-undo-redo {
    display: none !important;
}

/* Extra aggressive cleanup: hide dev toolbars, plotly modebar and debug banners */
#_dash-debug, #_dash-dev-tools, #_dash-devtools, .dash-devtools, .dash-debug, .dash-debug-menu, ._dash-debug, .debug-menu, .dev-tools, .dash-toolbar, .dash-error-card, .dash-hint {
    display: none !important;
}

/* Hide plotly modebar (export/plotly cloud) for a cleaner UI */
.modebar, .plotly-notifier, .modebar-group {
    display: none !important;
}


/* ============================================
   LAYOUT
   ============================================ */

.app-wrapper {
    display: flex;
    min-height: 100vh;
    background: #0d1117;
}

/* ============================================
   SIDEBAR
   ============================================ */

.sidebar {
    width: 260px;
    background: #010409;
    border-right: 1px solid #21262d;
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 100;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #21262d;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.brand-text {
    font-size: 18px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
}

.brand-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
    color: #fff;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sidebar-nav {
    flex: 1;
    padding: 16px 12px;
    overflow-y: auto;
}

.nav-section {
    margin-bottom: 24px;
}

.nav-section-title {
    font-size: 11px;
    font-weight: 600;
    color: #7d8590;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 0 12px;
    margin-bottom: 8px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    color: #7d8590;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    margin-bottom: 2px;
}

.nav-item:hover {
    background: #161b22;
    color: #e6edf3;
}

.nav-item.active {
    background: rgba(56, 139, 253, 0.15);
    color: #58a6ff;
}

.nav-item i {
    width: 18px;
    font-size: 14px;
    opacity: 0.8;
}

.nav-badge {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    background: #da3633;
    color: #fff;
    border-radius: 10px;
    min-width: 20px;
    text-align: center;
}

.sidebar-footer {
    padding: 16px;
    border-top: 1px solid #21262d;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s ease;
}

.user-info:hover {
    background: #161b22;
}

.user-avatar {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #f78166 0%, #da3633 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
}

.user-details {
    flex: 1;
}

.user-name {
    font-size: 13px;
    font-weight: 600;
    color: #e6edf3;
}

.user-role {
    font-size: 11px;
    color: #7d8590;
}

/* ============================================
   MAIN CONTENT
   ============================================ */

.main-content {
    flex: 1;
    margin-left: 260px;
    padding: 24px 32px;
    background: #0d1117;
    min-height: 100vh;
}

/* ============================================
   HEADER
   ============================================ */

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 28px;
}

.header-left h1 {
    font-size: 26px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
}

.header-subtitle {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    color: #7d8590;
}

.header-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: rgba(56, 139, 253, 0.1);
    border: 1px solid rgba(56, 139, 253, 0.3);
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    color: #58a6ff;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.live-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: rgba(35, 134, 54, 0.15);
    border: 1px solid rgba(46, 160, 67, 0.3);
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    color: #3fb950;
}

.live-dot {
    width: 8px;
    height: 8px;
    background: #3fb950;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.1); }
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.15s ease;
    font-family: inherit;
}

.btn-primary {
    background: #238636;
    color: #fff;
}

.btn-primary:hover {
    background: #2ea043;
}

.btn-secondary {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
}

.btn-secondary:hover {
    background: #30363d;
    border-color: #484f58;
}

/* ============================================
   METRIC CARDS
   ============================================ */

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px;
    position: relative;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: #30363d;
    transform: translateY(-2px);
}

.metric-card.critical {
    border-left: 3px solid #da3633;
}

.metric-card.warning {
    border-left: 3px solid #d29922;
}

.metric-card.success {
    border-left: 3px solid #238636;
}

.metric-card.info {
    border-left: 3px solid #58a6ff;
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}

.metric-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.metric-icon.critical { background: rgba(218, 54, 51, 0.15); color: #f85149; }
.metric-icon.warning { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.metric-icon.success { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.metric-icon.info { background: rgba(56, 139, 253, 0.15); color: #58a6ff; }

.metric-trend {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 6px;
}

.metric-trend.up { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.metric-trend.down { background: rgba(218, 54, 51, 0.15); color: #f85149; }

.metric-value {
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -1px;
    margin-bottom: 4px;
    font-feature-settings: 'tnum';
}

.metric-label {
    font-size: 13px;
    color: #7d8590;
    margin-bottom: 8px;
}

.metric-subtext {
    font-size: 11px;
    color: #484f58;
}

/* ============================================
   SECTION HEADERS
   ============================================ */

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #e6edf3;
}

.section-tabs {
    display: flex;
    gap: 4px;
    background: #21262d;
    padding: 4px;
    border-radius: 8px;
}

.tab-btn {
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    color: #7d8590;
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.tab-btn:hover {
    color: #e6edf3;
}

.tab-btn.active {
    background: #0d1117;
    color: #e6edf3;
}

/* ============================================
   DATA TABLE
   ============================================ */

.data-table-container {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
}

.table-header {
    display: grid;
    grid-template-columns: 2fr 100px 140px 80px 100px 80px 60px;
    gap: 12px;
    padding: 12px 20px;
    background: #0d1117;
    border-bottom: 1px solid #21262d;
    font-size: 11px;
    font-weight: 600;
    color: #7d8590;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.table-group {
    border-bottom: 1px solid #21262d;
}

.table-group:last-child {
    border-bottom: none;
}

.group-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    background: rgba(0, 0, 0, 0.2);
    font-size: 12px;
    font-weight: 600;
    color: #7d8590;
}

.group-header .count {
    font-size: 11px;
    padding: 2px 8px;
    background: #21262d;
    border-radius: 10px;
    color: #7d8590;
}

.table-row {
    display: grid;
    grid-template-columns: 2fr 100px 140px 80px 100px 80px 60px;
    gap: 12px;
    padding: 14px 20px;
    border-bottom: 1px solid #21262d;
    align-items: center;
    transition: background 0.15s ease;
}

.table-row:hover {
    background: rgba(56, 139, 253, 0.04);
}

.table-row:last-child {
    border-bottom: none;
}

.item-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.item-title {
    font-size: 14px;
    font-weight: 500;
    color: #e6edf3;
    display: flex;
    align-items: center;
    gap: 8px;
}

.item-title .tag {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    background: rgba(136, 46, 224, 0.2);
    color: #a371f7;
    border-radius: 4px;
}

.item-meta {
    font-size: 11px;
    color: #484f58;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}

.status-badge.critical {
    background: rgba(218, 54, 51, 0.15);
    color: #f85149;
}

.status-badge.high {
    background: rgba(210, 153, 34, 0.15);
    color: #d29922;
}

.status-badge.medium {
    background: rgba(56, 139, 253, 0.15);
    color: #58a6ff;
}

.status-badge.low {
    background: rgba(35, 134, 54, 0.15);
    color: #3fb950;
}

.category-tag {
    font-size: 11px;
    color: #7d8590;
}

.probability {
    font-size: 13px;
    font-weight: 600;
    color: #e6edf3;
}

.loss-value {
    font-size: 13px;
    font-weight: 500;
    color: #f85149;
}

.owner-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
    color: #fff;
}

.action-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #7d8590;
    cursor: pointer;
    transition: all 0.15s ease;
}

.action-btn:hover {
    background: #21262d;
    color: #e6edf3;
}

/* ============================================
   TWO COLUMN LAYOUT
   ============================================ */

.two-col-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 24px;
}

/* ============================================
   ALERTS PANEL
   ============================================ */

.alerts-panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: hidden;
}

.alerts-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #21262d;
}

.alerts-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
}

.alerts-count {
    font-size: 11px;
    padding: 2px 8px;
    background: #da3633;
    color: #fff;
    border-radius: 10px;
}

.alerts-list {
    max-height: 400px;
    overflow-y: auto;
}

.alert-item {
    padding: 14px 20px;
    border-bottom: 1px solid #21262d;
    transition: background 0.15s ease;
    cursor: pointer;
}

.alert-item:hover {
    background: rgba(56, 139, 253, 0.04);
}

.alert-item:last-child {
    border-bottom: none;
}

.alert-item.critical {
    border-left: 3px solid #da3633;
}

.alert-item.high {
    border-left: 3px solid #d29922;
}

.alert-item.medium {
    border-left: 3px solid #58a6ff;
}

.alert-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}

.alert-title {
    font-size: 13px;
    font-weight: 500;
    color: #e6edf3;
    line-height: 1.4;
}

.alert-time {
    font-size: 11px;
    color: #484f58;
}

.alert-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 11px;
    color: #7d8590;
}

.alert-prob {
    display: flex;
    align-items: center;
    gap: 4px;
}

.alert-prob-bar {
    width: 40px;
    height: 4px;
    background: #21262d;
    border-radius: 2px;
    overflow: hidden;
}

.alert-prob-fill {
    height: 100%;
    border-radius: 2px;
}

.alert-action {
    margin-left: auto;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
    background: rgba(56, 139, 253, 0.1);
    color: #58a6ff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.alert-action:hover {
    background: rgba(56, 139, 253, 0.2);
}

/* ============================================
   DMA STATUS
   ============================================ */

.dma-panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 24px;
}

.dma-header {
    padding: 16px 20px;
    border-bottom: 1px solid #21262d;
}

.dma-title {
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
}

.dma-list {
    padding: 8px;
}

.dma-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    transition: background 0.15s ease;
}

.dma-item:hover {
    background: rgba(255, 255, 255, 0.02);
}

.dma-name {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
    color: #e6edf3;
}

.dma-bar {
    width: 120px;
    height: 6px;
    background: #21262d;
    border-radius: 3px;
    overflow: hidden;
}

.dma-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}

.dma-value {
    width: 45px;
    text-align: right;
    font-size: 13px;
    font-weight: 600;
}

/* ============================================
   CHARTS
   ============================================ */

.chart-container {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.chart-title {
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
}

/* ============================================
   SCROLLBAR
   ============================================ */

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #484f58;
}
"""

# =============================================================================
# DATA
# =============================================================================

NRW_ITEMS = [
    {
        "id": "NRW-2026-00142",
        "title": "Distribution Main Leak - Kafue Road",
        "dma": "DMA-KIT-003",
        "status": "Critical",
        "category": "Real Loss - Leakage",
        "probability": 92,
        "loss": 125.5,
        "owner": "JM",
        "owner_color": "#1f6feb",
        "group": "critical",
        "has_mnf": True,
    },
    {
        "id": "NRW-2026-00138",
        "title": "Service Connection Leak - Chilenje",
        "dma": "DMA-LSK-002",
        "status": "Critical",
        "category": "Real Loss - Service",
        "probability": 88,
        "loss": 45.2,
        "owner": "SK",
        "owner_color": "#238636",
        "group": "critical",
        "has_mnf": True,
    },
    {
        "id": "NRW-2026-00135",
        "title": "Night Flow Anomaly - Industrial Zone",
        "dma": "DMA-NDO-001",
        "status": "High",
        "category": "Real Loss - Leakage",
        "probability": 76,
        "loss": 68.0,
        "owner": "PM",
        "owner_color": "#8b5cf6",
        "group": "high",
        "has_mnf": True,
    },
    {
        "id": "NRW-2026-00132",
        "title": "Meter Under-registration Cluster",
        "dma": "DMA-KIT-001",
        "status": "High",
        "category": "Apparent Loss - Meter",
        "probability": 71,
        "loss": 32.5,
        "owner": "GN",
        "owner_color": "#d29922",
        "group": "high",
        "has_mnf": False,
    },
    {
        "id": "NRW-2026-00128",
        "title": "Pressure Gradient Change - Ndola CBD",
        "dma": "DMA-NDO-002",
        "status": "Medium",
        "category": "Real Loss - Leakage",
        "probability": 58,
        "loss": 22.0,
        "owner": "TK",
        "owner_color": "#58a6ff",
        "group": "medium",
        "has_mnf": False,
    },
    {
        "id": "NRW-2026-00125",
        "title": "Suspected Unauthorized Connection",
        "dma": "DMA-LSK-003",
        "status": "Medium",
        "category": "Apparent Loss - Theft",
        "probability": 62,
        "loss": 18.5,
        "owner": "RB",
        "owner_color": "#da3633",
        "group": "medium",
        "has_mnf": False,
    },
    {
        "id": "NRW-2026-00120",
        "title": "Minor Flow Variance - Monitoring Only",
        "dma": "DMA-KIT-002",
        "status": "Low",
        "category": "Under Investigation",
        "probability": 42,
        "loss": 8.0,
        "owner": "AM",
        "owner_color": "#7d8590",
        "group": "monitoring",
        "has_mnf": False,
    },
]

DMA_DATA = [
    {"name": "Lusaka East", "nrw": 52, "color": "#da3633"},
    {"name": "Kitwe South", "nrw": 45, "color": "#d29922"},
    {"name": "Lusaka Central", "nrw": 36, "color": "#d29922"},
    {"name": "Ndola CBD", "nrw": 31, "color": "#58a6ff"},
    {"name": "Kitwe Central", "nrw": 28, "color": "#3fb950"},
    {"name": "Ndola Industrial", "nrw": 24, "color": "#3fb950"},
]

# =============================================================================
# COMPONENTS
# =============================================================================

def create_sidebar():
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Div("💧", className="brand-icon"),
                html.Span("AquaWatch", className="brand-text"),
                html.Span("PRO", className="brand-badge"),
            ], className="brand"),
        ], className="sidebar-header"),
        
        # Navigation
        html.Div([
            html.Div([
                html.Div("Main", className="nav-section-title"),
                html.Div([
                    html.I(className="fas fa-chart-line"),
                    html.Span("Dashboard"),
                ], className="nav-item active"),
                html.Div([
                    html.I(className="fas fa-table-cells"),
                    html.Span("NRW Board"),
                ], className="nav-item"),
                html.Div([
                    html.I(className="fas fa-bell"),
                    html.Span("Alerts"),
                    html.Span("7", className="nav-badge"),
                ], className="nav-item"),
                html.Div([
                    html.I(className="fas fa-clipboard-list"),
                    html.Span("Work Orders"),
                ], className="nav-item"),
            ], className="nav-section"),
            
            html.Div([
                html.Div("Analytics", className="nav-section-title"),
                html.Div([
                    html.I(className="fas fa-chart-area"),
                    html.Span("Performance"),
                ], className="nav-item"),
                html.Div([
                    html.I(className="fas fa-map"),
                    html.Span("DMA Map"),
                ], className="nav-item"),
                html.Div([
                    html.I(className="fas fa-chart-pie"),
                    html.Span("Reports"),
                ], className="nav-item"),
            ], className="nav-section"),
            
            html.Div([
                html.Div("IWA Standards", className="nav-section-title"),
                html.Div([
                    html.I(className="fas fa-scale-balanced"),
                    html.Span("Water Balance"),
                ], className="nav-item"),
                html.Div([
                    html.I(className="fas fa-gauge-high"),
                    html.Span("ILI Report"),
                ], className="nav-item"),
            ], className="nav-section"),
        ], className="sidebar-nav"),
        
        # Footer
        html.Div([
            html.Div([
                html.Div("DM", className="user-avatar"),
                html.Div([
                    html.Div("Denuel M.", className="user-name"),
                    html.Div("Administrator", className="user-role"),
                ], className="user-details"),
                html.I(className="fas fa-chevron-right", style={"color": "#484f58", "fontSize": "12px"}),
            ], className="user-info"),
        ], className="sidebar-footer"),
    ], id="sidebar", className="sidebar")


def create_metric_card(icon, value, label, subtext, trend=None, trend_dir="up", variant="info"):
    trend_el = None
    if trend:
        trend_el = html.Div([
            html.I(className=f"fas fa-arrow-{'up' if trend_dir == 'up' else 'down'}", style={"fontSize": "10px"}),
            html.Span(trend),
        ], className=f"metric-trend {'up' if trend_dir == 'up' else 'down'}")
    
    return html.Div([
        html.Div([
            html.Div(icon, className=f"metric-icon {variant}"),
            trend_el,
        ], className="metric-header"),
        html.Div(value, className="metric-value"),
        html.Div(label, className="metric-label"),
        html.Div(subtext, className="metric-subtext"),
    ], className=f"metric-card {variant}")


def create_table_row(item):
    status_class = item["status"].lower()
    # Make the whole row clickable to open details modal
    return html.Button([
        html.Div([
            html.Div([
                html.Span(item["title"]),
                html.Span("MNF", className="tag") if item.get("has_mnf") else None,
            ], className="item-title"),
            html.Div(f"{item['id']} • {item['dma']}", className="item-meta"),
        ], className="item-info"),
        html.Div([
            html.Span(item["status"], className=f"status-badge {status_class}")
        ]),
        html.Div(item["category"], className="category-tag"),
        html.Div(f"{item['probability']}%", className="probability"),
        html.Div(f"{item['loss']} m³/d", className="loss-value"),
        html.Div(item["owner"], className="owner-avatar", style={"background": item["owner_color"]}),
        html.Button([
            html.I(className="fas fa-ellipsis"),
        ], className="action-btn"),
    ],
        id={"type": "table-row-btn", "index": item["id"]},
        n_clicks=0,
        className="table-row",
        style={"background": "none", "border": "none", "width": "100%", "textAlign": "left", "padding": 0, "cursor": "pointer"}
    )


def create_data_table():
    groups = {
        "critical": {"label": "Critical - Immediate Action", "items": []},
        "high": {"label": "High Priority - Today", "items": []},
        "medium": {"label": "Medium Priority - This Week", "items": []},
        "monitoring": {"label": "Monitoring", "items": []},
    }
    
    for item in NRW_ITEMS:
        groups[item["group"]]["items"].append(item)
    
    table_groups = []
    for group_key, group_data in groups.items():
        if group_data["items"]:
            table_groups.append(
                html.Div([
                    html.Div([
                        html.Span(group_data["label"]),
                        html.Span(f"{len(group_data['items'])} items", className="count"),
                    ], className="group-header"),
                    *[create_table_row(item) for item in group_data["items"]]
                ], className="table-group")
            )
    
    return html.Div([
        html.Div([
            html.Span("Item"),
            html.Span("Status"),
            html.Span("Category"),
            html.Span("Prob."),
            html.Span("Est. Loss"),
            html.Span("Owner"),
            html.Span(""),
        ], className="table-header"),
        *table_groups
    ], className="data-table-container")


def create_alerts_panel():
    alerts = [item for item in NRW_ITEMS if item["probability"] >= 70]
    
    alert_items = []
    for alert in alerts:
        prob_color = "#da3633" if alert["probability"] >= 85 else "#d29922" if alert["probability"] >= 70 else "#58a6ff"
        severity = "critical" if alert["status"] == "Critical" else "high" if alert["status"] == "High" else "medium"
        
        alert_items.append(
            html.Div([
                html.Div([
                    html.Div(f"{alert['title']} • {alert['dma']}", className="alert-title"),
                    html.Span("2m ago", className="alert-time"),
                ], className="alert-header"),
                html.Div([
                    html.Span(alert["category"]),
                    html.Div([
                        html.Span(f"{alert['probability']}%"),
                        html.Div([
                            html.Div(style={"width": f"{alert['probability']}%", "background": prob_color}, className="alert-prob-fill")
                        ], className="alert-prob-bar"),
                    ], className="alert-prob"),
                    html.Button("View", className="alert-action"),
                ], className="alert-meta"),
            ], className=f"alert-item {severity}")
        )
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-bell", style={"color": "#f85149"}),
                html.Span("Live Alerts"),
                html.Span(str(len(alerts)), className="alerts-count"),
            ], className="alerts-title"),
        ], className="alerts-header"),
        html.Div(alert_items, className="alerts-list"),
    ], className="alerts-panel")


def create_dma_panel():
    dma_items = []
    for i, dma in enumerate(DMA_DATA):
        dma_items.append(
            html.Div([
                html.Button(
                    dma["name"],
                    id={"type": "dma-name-btn", "index": i},
                    n_clicks=0,
                    className="dma-name",
                    style={"background": "none", "border": "none", "color": dma["color"], "cursor": "pointer", "fontWeight": 600, "fontSize": "13px"}
                ),
                html.Div([
                    html.Div(style={"width": f"{dma['nrw']}%", "background": dma["color"]}, className="dma-bar-fill")
                ], className="dma-bar"),
                html.Span(f"{dma['nrw']}%", className="dma-value", style={"color": dma["color"]}),
            ], className="dma-item")
        )
    
    return html.Div([
        html.Div([
            html.Div("DMA Status Overview", className="dma-title"),
        ], className="dma-header"),
        html.Div(dma_items, className="dma-list"),
    ], className="dma-panel")


def create_nrw_chart():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    values = [32 + np.random.normal(0, 2) + np.sin(i/7)*3 for i in range(30)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        fill='tozeroy',
        fillcolor='rgba(56, 139, 253, 0.1)',
        line=dict(color='#58a6ff', width=2),
        mode='lines',
        hovertemplate='<b>%{x|%b %d}</b><br>NRW: %{y:.1f}%<extra></extra>'
    ))
    
    fig.add_hline(y=25, line_dash="dash", line_color="rgba(63, 185, 80, 0.5)",
                  annotation_text="Target: 25%", annotation_position="right",
                  annotation_font_color="#3fb950", annotation_font_size=11)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=20, b=40),
        height=250,
        font=dict(family='Inter', color='#7d8590', size=11),
        xaxis=dict(
            gridcolor='rgba(48, 54, 61, 0.5)',
            linecolor='#21262d',
            tickformat='%b %d',
        ),
        yaxis=dict(
            gridcolor='rgba(48, 54, 61, 0.5)',
            linecolor='#21262d',
            ticksuffix='%',
            range=[0, 50],
        ),
        hoverlabel=dict(
            bgcolor='#161b22',
            bordercolor='#30363d',
            font_size=12,
            font_family='Inter'
        ),
        showlegend=False,
    )
    
    return fig


# =============================================================================
# LAYOUT
# =============================================================================

app.layout = html.Div([
    # Inject styles
    dcc.Markdown(f"<style>{STYLES}</style>", dangerously_allow_html=True),
    
    html.Div([
        # Sidebar
        create_sidebar(),
        
        # Main Content
        html.Div([
            # Header
            html.Div([
                html.Div([
                    html.H1("Water Intelligence Dashboard"),
                    html.Div([
                        html.Span([
                            html.I(className="fas fa-certificate", style={"fontSize": "10px"}),
                            "IWA Water Balance Aligned"
                        ], className="header-tag"),
                        html.Span("•"),
                        html.Span("Real-time NRW Monitoring"),
                    ], className="header-subtitle"),
                ], className="header-left"),
                
                html.Div([
                    html.Div([
                        html.Div(className="live-dot"),
                        html.Span("Live"),
                        html.Span(f"• Updated {datetime.now().strftime('%H:%M:%S')}", style={"color": "#484f58"}),
                    ], className="live-indicator"),
                    html.Button([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "8px"}),
                        "Customize"
                    ], id='open-customize', className="btn btn-secondary"),
                    html.Button([
                        html.I(className="fas fa-sync-alt"),
                        "Refresh"
                    ], className="btn btn-secondary"),
                    html.Button([
                        html.I(className="fas fa-plus"),
                        "New Alert"
                    ], className="btn btn-primary"),
                ], className="header-right"),
            ], className="page-header"),
            
            # Metrics
            html.Div(id="metrics-section", children=[
                html.Div([
                    create_metric_card("📊", "32.3%", "National NRW", "↓ 2.3% vs last month", "-2.3%", "down", "warning"),
                    create_metric_card("🚨", "2", "Critical Alerts", "Immediate action required", None, None, "critical"),
                    create_metric_card("💧", "320 m³", "Est. Daily Loss", "~$799/day revenue impact", None, None, "info"),
                    create_metric_card("📡", "8", "Active DMAs", "All sensors online", "+1", "up", "success"),
                ], className="metrics-grid")
            ]),
            
            # Table Section
            html.Div([
                html.Div([
                    html.Span("NRW Detection Board", className="section-title"),
                    html.Div([
                        html.Button("Table", className="tab-btn active"),
                        html.Button("Kanban", className="tab-btn"),
                        html.Button("Timeline", className="tab-btn"),
                    ], className="section-tabs"),
                ], className="section-header"),
                html.Div(create_data_table(), id="board-section"),
            ]),
            
            # Two Column Layout
            html.Div(id="chart-section", children=[
                # Chart
                html.Div([
                    html.Div([
                        html.Span("NRW Trend - 30 Days", className="chart-title"),
                        html.Div([
                            html.Button("7D", className="tab-btn"),
                            html.Button("30D", className="tab-btn active"),
                            html.Button("90D", className="tab-btn"),
                        ], className="section-tabs"),
                    ], className="chart-header"),
                    dcc.Graph(figure=create_nrw_chart(), config={"displayModeBar": False}),
                ], className="chart-container"),
                
                # Alerts & DMA
                html.Div([
                    html.Div(create_alerts_panel(), id="alerts-section"),
                    html.Div(create_dma_panel(), id="dma-section"),
                ], className="right-column"),
            ], className="two-col-grid"),
            
        ], id="main-content", className="main-content"),
    ], className="app-wrapper"),

    # Offcanvas customize panel
    dbc.Offcanvas([
        html.Div("Customize dashboard sections", style={"fontWeight":"600","marginBottom":"8px"}),
        dcc.Checklist(
            id='view-checklist',
            options=[
                {'label':'Metrics','value':'metrics'},
                {'label':'NRW Board','value':'board'},
                {'label':'NRW Trend Chart','value':'chart'},
                {'label':'Alerts Panel','value':'alerts'},
                {'label':'DMA Panel','value':'dma'},
                {'label':'Sidebar','value':'sidebar'},
            ],
            value=['metrics','board','chart','alerts','dma','sidebar'],
            labelStyle={'display':'block'}
        ),
        html.Div([
            html.Button("Reset to default", id='reset-view', className='btn btn-secondary', n_clicks=0)
        ], style={"marginTop":"12px"})
    ], id='customize-offcanvas', title='Customize View', is_open=False, placement='end'),

    # Details modal (hidden until opened)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
        dbc.ModalBody(id='modal-body'),
        dbc.ModalFooter(dbc.Button("Close", id='close-modal', className='btn btn-secondary', n_clicks=0)),
    ], id='details-modal', is_open=False, size='lg'),
    
    # Auto refresh
    dcc.Interval(id='refresh-interval', interval=60*1000, n_intervals=0),
], style={"minHeight": "100vh"})


# ===================== CALLBACKS FOR CUSTOMIZE/DRILLDOWN =====================

@app.callback(
    Output('customize-offcanvas', 'is_open'),
    Input('open-customize', 'n_clicks'),
    State('customize-offcanvas', 'is_open'),
)
def toggle_offcanvas(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output('metrics-section', 'style'),
     Output('board-section', 'style'),
     Output('chart-section', 'style'),
     Output('alerts-section', 'style'),
     Output('dma-section', 'style'),
     Output('sidebar', 'style'),
     Output('main-content', 'style')],
    Input('view-checklist', 'value')
)
def update_visibility(values):
    visible = set(values or [])
    metrics_style = {} if 'metrics' in visible else {'display': 'none'}
    board_style = {} if 'board' in visible else {'display': 'none'}
    chart_style = {} if 'chart' in visible else {'display': 'none'}
    alerts_style = {} if 'alerts' in visible else {'display': 'none'}
    dma_style = {} if 'dma' in visible else {'display': 'none'}
    sidebar_style = {} if 'sidebar' in visible else {'display': 'none'}

    # If sidebar hidden, remove left margin on main-content
    main_style = {'marginLeft': '260px'}
    if 'sidebar' not in visible:
        main_style = {'marginLeft': '0'}

    return metrics_style, board_style, chart_style, alerts_style, dma_style, sidebar_style, main_style


@app.callback(
    Output('view-checklist', 'value'),
    Input('reset-view', 'n_clicks'),
    prevent_initial_call=True
)
def reset_view(n):
    return ['metrics','board','chart','alerts','dma','sidebar']


@app.callback(
    [Output('details-modal','is_open'), Output('modal-title','children'), Output('modal-body','children')],
    [Input({'type':'dma-name-btn','index': ALL}, 'n_clicks'), Input({'type':'table-row-btn','index': ALL}, 'n_clicks'), Input('close-modal','n_clicks')],
    [State('details-modal','is_open')]
)
def toggle_details(dma_clicks, row_clicks, close_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", ""
    prop = ctx.triggered[0]
    trigger_id = prop['prop_id'].split('.')[0]

    # DMA button clicked
    if 'dma-name-btn' in trigger_id:
        # find last clicked index
        idxs = [i for i, n in enumerate(dma_clicks) if n]
        if idxs:
            i = idxs[-1]
            dma = DMA_DATA[i]
            body = html.Div([
                html.P(f"NRW: {dma['nrw']}%"),
                html.P(f"Status: DMA status overview"),
                html.P("Detailed analytics and charts can be added here."),
            ])
            return True, f"DMA: {dma['name']}", body

    # Table row clicked
    if 'table-row-btn' in trigger_id:
        idxs = [i for i, n in enumerate(row_clicks) if n]
        if idxs:
            i = idxs[-1]
            item = NRW_ITEMS[i]
            body = html.Div([
                html.P(f"DMA: {item['dma']}"),
                html.P(f"Status: {item['status']}"),
                html.P(f"Category: {item['category']}"),
                html.P(f"Probability: {item['probability']}%"),
                html.P(f"Est. Loss: {item['loss']} m³/d"),
            ])
            return True, f"{item['id']} - {item['title']}", body

    # Close
    if close_click and is_open:
        return False, "", ""

    return is_open, dash.no_update, dash.no_update


# ===================== RUN =====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌊 AQUAWATCH PRO - Enterprise Water Intelligence")
    print("="*60)
    print(f"\n✨ Dashboard: http://127.0.0.1:8050")
    print("📊 Real-time NRW monitoring for Zambia & South Africa")
    print("\n" + "="*60 + "\n")
    app.run(debug=False, port=8050)
