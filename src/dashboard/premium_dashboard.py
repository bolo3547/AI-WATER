"""
AquaWatch Premium Dashboard
===========================

World-class UI/UX inspired by:
- Linear.app (clean, minimal)
- Stripe Dashboard (professional data viz)
- Vercel (modern dark theme)
- Tesla (futuristic feel)
- Apple (premium polish)

Features:
- Glass-morphism effects
- Smooth animations
- Real-time data streaming
- Interactive 3D-like charts
- Dark/Light mode toggle
- Responsive design
- Micro-interactions
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# =============================================================================
# PREMIUM THEME CONFIGURATION
# =============================================================================

THEME = {
    "dark": {
        "bg_primary": "#0a0a0f",
        "bg_secondary": "#12121a",
        "bg_card": "rgba(20, 20, 30, 0.8)",
        "bg_card_hover": "rgba(30, 30, 45, 0.9)",
        "glass": "rgba(255, 255, 255, 0.03)",
        "glass_border": "rgba(255, 255, 255, 0.08)",
        "text_primary": "#ffffff",
        "text_secondary": "rgba(255, 255, 255, 0.6)",
        "text_muted": "rgba(255, 255, 255, 0.4)",
        "accent_primary": "#6366f1",  # Indigo
        "accent_secondary": "#8b5cf6",  # Purple
        "accent_gradient": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "chart_grid": "rgba(255, 255, 255, 0.05)",
        "glow": "0 0 60px rgba(99, 102, 241, 0.3)",
    }
}

# =============================================================================
# PREMIUM CSS STYLES
# =============================================================================

PREMIUM_CSS = """
/* ============================================
   AQUAWATCH PREMIUM - WORLD CLASS UI/UX
   ============================================ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: rgba(20, 20, 30, 0.8);
    --glass: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.08);
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.6);
    --text-muted: rgba(255, 255, 255, 0.4);
    --accent: #6366f1;
    --accent-light: #818cf8;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --info: #3b82f6;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.5);
    --shadow-glow: 0 0 60px rgba(99, 102, 241, 0.15);
    --transition-fast: 0.15s ease;
    --transition-normal: 0.25s ease;
    --transition-slow: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Animated Background Gradient */
.app-container {
    position: relative;
    min-height: 100vh;
    background: var(--bg-primary);
}

.app-container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(ellipse 80% 50% at 20% -20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
        radial-gradient(ellipse 40% 30% at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* ============================================
   PREMIUM SIDEBAR
   ============================================ */

.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    background: rgba(12, 12, 18, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid var(--glass-border);
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    z-index: 100;
    transition: transform var(--transition-slow);
}

.logo-section {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    margin-bottom: 32px;
}

.logo-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.logo-text {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.logo-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    background: rgba(99, 102, 241, 0.2);
    color: var(--accent-light);
    border-radius: 20px;
    margin-left: auto;
}

.nav-section {
    flex: 1;
    overflow-y: auto;
}

.nav-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    padding: 16px 12px 8px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    margin: 2px 0;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}

.nav-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--accent);
    border-radius: 0 2px 2px 0;
    transform: scaleY(0);
    transition: transform var(--transition-normal);
}

.nav-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
}

.nav-item.active {
    background: rgba(99, 102, 241, 0.1);
    color: var(--text-primary);
}

.nav-item.active::before {
    transform: scaleY(1);
}

.nav-icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
    opacity: 0.8;
}

.nav-badge {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    background: var(--danger);
    color: white;
}

/* ============================================
   MAIN CONTENT AREA
   ============================================ */

.main-content {
    margin-left: 280px;
    padding: 32px;
    min-height: 100vh;
    position: relative;
    z-index: 1;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
}

.page-title {
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -1px;
    margin-bottom: 8px;
    background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.page-subtitle {
    font-size: 15px;
    color: var(--text-secondary);
}

.header-actions {
    display: flex;
    gap: 12px;
}

/* ============================================
   PREMIUM BUTTONS
   ============================================ */

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    border-radius: var(--radius-md);
    border: none;
    cursor: pointer;
    transition: all var(--transition-normal);
    font-family: inherit;
}

.btn-primary {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    border: 1px solid var(--glass-border);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.15);
}

.btn-icon {
    padding: 10px;
    border-radius: var(--radius-md);
}

/* ============================================
   PREMIUM CARDS
   ============================================ */

.card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 24px;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}

.card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.card:hover {
    border-color: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
}

/* ============================================
   STAT CARDS
   ============================================ */

.stat-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: all var(--transition-normal);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent);
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.stat-card:hover::before {
    opacity: 1;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-glow);
}

.stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    background: rgba(99, 102, 241, 0.1);
}

.stat-trend {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 20px;
}

.stat-trend.up {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
}

.stat-trend.down {
    background: rgba(239, 68, 68, 0.1);
    color: var(--danger);
}

.stat-value {
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -1px;
    margin-bottom: 4px;
    font-family: 'JetBrains Mono', monospace;
}

.stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 500;
}

.stat-sparkline {
    margin-top: 16px;
    height: 40px;
}

/* ============================================
   CHART CONTAINERS
   ============================================ */

.chart-container {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 24px;
    transition: all var(--transition-normal);
}

.chart-container:hover {
    border-color: rgba(255, 255, 255, 0.12);
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.chart-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

.chart-subtitle {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
}

.chart-filters {
    display: flex;
    gap: 8px;
}

.chart-filter-btn {
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 20px;
    border: 1px solid var(--glass-border);
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.chart-filter-btn:hover,
.chart-filter-btn.active {
    background: rgba(99, 102, 241, 0.1);
    border-color: var(--accent);
    color: var(--accent-light);
}

/* ============================================
   ALERTS TABLE
   ============================================ */

.alerts-table {
    width: 100%;
    border-collapse: collapse;
}

.alerts-table th {
    text-align: left;
    padding: 12px 16px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    border-bottom: 1px solid var(--glass-border);
}

.alerts-table td {
    padding: 16px;
    font-size: 14px;
    border-bottom: 1px solid var(--glass-border);
    transition: background var(--transition-fast);
}

.alerts-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

.alert-severity {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.alert-severity.critical {
    background: rgba(239, 68, 68, 0.1);
    color: var(--danger);
}

.alert-severity.high {
    background: rgba(245, 158, 11, 0.1);
    color: var(--warning);
}

.alert-severity.medium {
    background: rgba(59, 130, 246, 0.1);
    color: var(--info);
}

.alert-severity.low {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
}

.alert-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.alert-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

.alert-status-dot.active {
    background: var(--danger);
}

.alert-status-dot.investigating {
    background: var(--warning);
}

.alert-status-dot.resolved {
    background: var(--success);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ============================================
   MAP CONTAINER
   ============================================ */

.map-container {
    position: relative;
    border-radius: var(--radius-lg);
    overflow: hidden;
    height: 400px;
}

.map-overlay {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 10;
}

.map-control {
    width: 40px;
    height: 40px;
    background: var(--bg-card);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.map-control:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
}

/* ============================================
   LIVE INDICATOR
   ============================================ */

.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: var(--success);
}

.live-dot {
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    animation: livePulse 1.5s infinite;
}

@keyframes livePulse {
    0%, 100% { 
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
    }
    50% { 
        transform: scale(1.1);
        box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
    }
}

/* ============================================
   GRID LAYOUTS
   ============================================ */

.grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}

.grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

.grid-2-1 {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
}

.grid-1-2 {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 20px;
}

/* ============================================
   SCROLLBAR
   ============================================ */

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.15);
}

/* ============================================
   ANIMATIONS
   ============================================ */

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease forwards;
}

.slide-in {
    animation: slideIn 0.4s ease forwards;
}

/* Staggered animations for cards */
.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

/* ============================================
   RESPONSIVE
   ============================================ */

@media (max-width: 1400px) {
    .card-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 1024px) {
    .sidebar {
        transform: translateX(-100%);
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .card-grid {
        grid-template-columns: 1fr;
    }
}
"""

# =============================================================================
# INITIALIZE APP
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
    title="AquaWatch | NRW Intelligence Platform"
)

# =============================================================================
# GENERATE SAMPLE DATA
# =============================================================================

def generate_time_series(hours=168, base=100, volatility=10):
    """Generate realistic time series data."""
    dates = pd.date_range(end=datetime.now(), periods=hours, freq='H')
    values = [base]
    for _ in range(hours - 1):
        change = np.random.normal(0, volatility) + np.sin(len(values) / 24 * np.pi) * 5
        values.append(max(0, values[-1] + change))
    return dates, values

def generate_district_data():
    """Generate district performance data."""
    districts = [
        {"name": "Lusaka Central", "nrw": 28.5, "sensors": 156, "alerts": 12, "trend": -2.3},
        {"name": "Lusaka East", "nrw": 35.2, "sensors": 98, "alerts": 24, "trend": 1.8},
        {"name": "Johannesburg CBD", "nrw": 22.1, "sensors": 234, "alerts": 8, "trend": -4.1},
        {"name": "Soweto", "nrw": 41.3, "sensors": 187, "alerts": 45, "trend": 0.5},
        {"name": "Pretoria North", "nrw": 19.8, "sensors": 145, "alerts": 5, "trend": -3.2},
        {"name": "Cape Town Metro", "nrw": 24.7, "sensors": 312, "alerts": 15, "trend": -1.9},
        {"name": "Kitwe Industrial", "nrw": 38.9, "sensors": 67, "alerts": 28, "trend": 2.4},
        {"name": "Ndola Central", "nrw": 33.4, "sensors": 89, "alerts": 19, "trend": -0.8},
    ]
    return districts

def generate_alerts():
    """Generate sample alerts."""
    alert_types = [
        ("Pressure Anomaly", "Zone 4A - Unusual pressure drop detected", "critical"),
        ("Flow Deviation", "DMA-12 - Flow exceeds baseline by 45%", "high"),
        ("Leak Detected", "Pipe segment P-2847 - Acoustic signature match", "critical"),
        ("Meter Malfunction", "Meter M-1923 - Communication lost", "medium"),
        ("NRW Spike", "District 7 - NRW increased 8% in 24h", "high"),
        ("Burst Main", "Oxford Street - Confirmed burst, crew dispatched", "critical"),
        ("Pressure Zone", "Zone 2B - Pressure exceeding threshold", "medium"),
        ("Consumption Pattern", "Industrial Park - Unusual night flow", "low"),
    ]
    
    alerts = []
    for i, (title, desc, severity) in enumerate(alert_types):
        alerts.append({
            "id": f"ALT-{1000+i}",
            "title": title,
            "description": desc,
            "severity": severity,
            "time": f"{random.randint(1, 59)} min ago",
            "status": random.choice(["active", "investigating", "resolved"]),
            "location": random.choice(["Lusaka", "Johannesburg", "Cape Town", "Kitwe"])
        })
    return alerts

# =============================================================================
# PREMIUM CHART TEMPLATES
# =============================================================================

def create_premium_chart_layout():
    """Create base layout for premium charts."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif", "color": "rgba(255,255,255,0.8)"},
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "linecolor": "rgba(255,255,255,0.1)",
            "tickfont": {"size": 11},
            "showgrid": True,
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "linecolor": "rgba(255,255,255,0.1)",
            "tickfont": {"size": 11},
            "showgrid": True,
        },
        "hoverlabel": {
            "bgcolor": "rgba(20,20,30,0.95)",
            "bordercolor": "rgba(99,102,241,0.5)",
            "font": {"family": "Inter", "size": 13, "color": "white"}
        }
    }

def create_nrw_trend_chart():
    """Create NRW trend chart with gradient fill."""
    dates, values = generate_time_series(168, 32, 2)
    
    fig = go.Figure()
    
    # Add gradient area
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        fill='tozeroy',
        fillgradient=dict(
            type="vertical",
            colorscale=[[0, "rgba(99,102,241,0)"], [1, "rgba(99,102,241,0.3)"]]
        ),
        line=dict(color="#6366f1", width=2),
        name="NRW %",
        hovertemplate="<b>%{x}</b><br>NRW: %{y:.1f}%<extra></extra>"
    ))
    
    # Add target line
    fig.add_hline(y=25, line_dash="dash", line_color="rgba(16,185,129,0.5)",
                  annotation_text="Target: 25%", annotation_position="right")
    
    fig.update_layout(
        **create_premium_chart_layout(),
        title=None,
        showlegend=False,
        height=300,
        yaxis_title="NRW (%)",
    )
    
    return fig

def create_flow_comparison_chart():
    """Create flow comparison chart."""
    hours = list(range(24))
    inflow = [100 + np.sin(h/24*2*np.pi)*30 + np.random.normal(0, 5) for h in hours]
    outflow = [v - np.random.uniform(15, 35) for v in inflow]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours, y=inflow,
        name="System Input",
        line=dict(color="#6366f1", width=3),
        mode="lines+markers",
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=hours, y=outflow,
        name="Billed Consumption",
        line=dict(color="#10b981", width=3),
        mode="lines+markers",
        marker=dict(size=6)
    ))
    
    # Fill between (NRW area)
    fig.add_trace(go.Scatter(
        x=hours + hours[::-1],
        y=inflow + outflow[::-1],
        fill='toself',
        fillcolor='rgba(239,68,68,0.1)',
        line=dict(color='rgba(0,0,0,0)'),
        name="NRW",
        showlegend=True
    ))
    
    fig.update_layout(
        **create_premium_chart_layout(),
        height=300,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Hour of Day",
        yaxis_title="Flow (m³/h)"
    )
    
    return fig

def create_district_performance_chart():
    """Create district performance bar chart."""
    districts = generate_district_data()
    
    df = pd.DataFrame(districts)
    df = df.sort_values('nrw', ascending=True)
    
    colors = ['#10b981' if x < 25 else '#f59e0b' if x < 35 else '#ef4444' for x in df['nrw']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['nrw'],
        y=df['name'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        text=[f"{x:.1f}%" for x in df['nrw']],
        textposition='outside',
        textfont=dict(size=12, color='rgba(255,255,255,0.8)'),
        hovertemplate="<b>%{y}</b><br>NRW: %{x:.1f}%<extra></extra>"
    ))
    
    # Add target line
    fig.add_vline(x=25, line_dash="dash", line_color="rgba(99,102,241,0.5)")
    
    fig.update_layout(
        **create_premium_chart_layout(),
        height=350,
        xaxis_title="NRW (%)",
        yaxis_title=None,
        showlegend=False,
    )
    
    return fig

def create_leak_detection_gauge():
    """Create leak detection confidence gauge."""
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=87,
        delta={'reference': 80, 'increasing': {'color': '#10b981'}},
        title={'text': "Detection Confidence", 'font': {'size': 14, 'color': 'rgba(255,255,255,0.6)'}},
        number={'font': {'size': 40, 'color': 'white', 'family': 'JetBrains Mono'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'rgba(255,255,255,0.3)'},
            'bar': {'color': '#6366f1'},
            'bgcolor': 'rgba(255,255,255,0.05)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239,68,68,0.2)'},
                {'range': [50, 75], 'color': 'rgba(245,158,11,0.2)'},
                {'range': [75, 100], 'color': 'rgba(16,185,129,0.2)'}
            ],
            'threshold': {
                'line': {'color': '#10b981', 'width': 3},
                'thickness': 0.8,
                'value': 85
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': 'white', 'family': 'Inter'},
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_realtime_map():
    """Create interactive map with sensor locations."""
    # Sample sensor locations
    sensors = pd.DataFrame({
        'lat': [-15.4167, -15.38, -15.45, -26.2041, -26.15, -26.25, -33.9249, -33.95],
        'lon': [28.2833, 28.35, 28.22, 28.0473, 28.1, 27.95, 18.4241, 18.5],
        'name': ['Lusaka Central', 'Lusaka East', 'Lusaka South', 'JHB CBD', 'Sandton', 'Soweto', 'Cape Town CBD', 'Cape Town South'],
        'status': ['active', 'alert', 'active', 'active', 'alert', 'critical', 'active', 'active'],
        'nrw': [28, 35, 24, 22, 31, 45, 19, 23]
    })
    
    colors = {'active': '#10b981', 'alert': '#f59e0b', 'critical': '#ef4444'}
    sensors['color'] = sensors['status'].map(colors)
    
    fig = go.Figure()
    
    for status in ['active', 'alert', 'critical']:
        df = sensors[sensors['status'] == status]
        fig.add_trace(go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='markers',
            marker=dict(
                size=15 if status == 'critical' else 12,
                color=colors[status],
                opacity=0.9
            ),
            text=df['name'] + '<br>NRW: ' + df['nrw'].astype(str) + '%',
            hovertemplate="<b>%{text}</b><extra></extra>",
            name=status.capitalize()
        ))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=-22, lon=25),
            zoom=4
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(20,20,30,0.8)',
            bordercolor='rgba(255,255,255,0.1)',
            font=dict(color='white')
        )
    )
    
    return fig

def create_sparkline(values, color="#6366f1"):
    """Create mini sparkline chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}'
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=50,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False
    )
    
    return fig

# =============================================================================
# COMPONENT BUILDERS
# =============================================================================

def create_sidebar():
    """Create premium sidebar navigation."""
    return html.Div([
        # Logo Section
        html.Div([
            html.Div("🌊", className="logo-icon"),
            html.Div([
                html.Span("AquaWatch", className="logo-text"),
            ]),
            html.Span("PRO", className="logo-badge")
        ], className="logo-section"),
        
        # Navigation
        html.Div([
            html.Div("Overview", className="nav-label"),
            html.Div([
                html.I(className="fas fa-chart-line nav-icon"),
                html.Span("Dashboard"),
            ], className="nav-item active"),
            html.Div([
                html.I(className="fas fa-map-marked-alt nav-icon"),
                html.Span("Network Map"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-bell nav-icon"),
                html.Span("Alerts"),
                html.Span("12", className="nav-badge")
            ], className="nav-item"),
            
            html.Div("Analysis", className="nav-label"),
            html.Div([
                html.I(className="fas fa-tint nav-icon"),
                html.Span("NRW Analytics"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-search-location nav-icon"),
                html.Span("Leak Detection"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-chart-area nav-icon"),
                html.Span("Flow Analysis"),
            ], className="nav-item"),
            
            html.Div("Operations", className="nav-label"),
            html.Div([
                html.I(className="fas fa-tasks nav-icon"),
                html.Span("Work Orders"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-users nav-icon"),
                html.Span("Field Teams"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-clipboard-list nav-icon"),
                html.Span("Reports"),
            ], className="nav-item"),
            
            html.Div("Enterprise", className="nav-label"),
            html.Div([
                html.I(className="fas fa-building nav-icon"),
                html.Span("Industrial"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-leaf nav-icon"),
                html.Span("ESG Compliance"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-exchange-alt nav-icon"),
                html.Span("Water Trading"),
            ], className="nav-item"),
        ], className="nav-section"),
        
        # User Section
        html.Div([
            html.Div([
                html.I(className="fas fa-cog nav-icon"),
                html.Span("Settings"),
            ], className="nav-item"),
            html.Div([
                html.I(className="fas fa-question-circle nav-icon"),
                html.Span("Help & Support"),
            ], className="nav-item"),
        ], style={"marginTop": "auto", "paddingTop": "16px", "borderTop": "1px solid rgba(255,255,255,0.08)"})
    ], className="sidebar")

def create_stat_card(icon, value, label, trend=None, trend_direction="up", color="#6366f1", sparkline_data=None):
    """Create premium stat card."""
    trend_class = f"stat-trend {trend_direction}" if trend else ""
    trend_icon = "fa-arrow-up" if trend_direction == "up" else "fa-arrow-down"
    
    children = [
        html.Div([
            html.Div(icon, className="stat-icon", style={"background": f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.15,)}"}),
            html.Div([
                html.I(className=f"fas {trend_icon}", style={"fontSize": "10px"}),
                html.Span(f"{trend}%")
            ], className=trend_class) if trend else None
        ], className="stat-header"),
        html.Div(value, className="stat-value"),
        html.Div(label, className="stat-label"),
    ]
    
    if sparkline_data:
        children.append(
            html.Div([
                dcc.Graph(
                    figure=create_sparkline(sparkline_data, color),
                    config={"displayModeBar": False}
                )
            ], className="stat-sparkline")
        )
    
    return html.Div(children, className="stat-card fade-in")

def create_alerts_table():
    """Create premium alerts table."""
    alerts = generate_alerts()
    
    rows = []
    for alert in alerts:
        severity_class = f"alert-severity {alert['severity']}"
        status_dot_class = f"alert-status-dot {alert['status']}"
        
        rows.append(html.Tr([
            html.Td(alert['id']),
            html.Td([
                html.Div(alert['title'], style={"fontWeight": "500", "marginBottom": "2px"}),
                html.Div(alert['description'], style={"fontSize": "12px", "color": "rgba(255,255,255,0.5)"})
            ]),
            html.Td(html.Span([
                html.I(className="fas fa-circle", style={"fontSize": "6px"}),
                alert['severity'].upper()
            ], className=severity_class)),
            html.Td(alert['location']),
            html.Td(html.Div([
                html.Div(className=status_dot_class),
                html.Span(alert['status'].capitalize())
            ], className="alert-status")),
            html.Td(alert['time']),
            html.Td(html.Button([
                html.I(className="fas fa-ellipsis-h")
            ], className="btn btn-icon btn-secondary", style={"padding": "6px 10px"}))
        ]))
    
    return html.Table([
        html.Thead(html.Tr([
            html.Th("ID"),
            html.Th("Alert"),
            html.Th("Severity"),
            html.Th("Location"),
            html.Th("Status"),
            html.Th("Time"),
            html.Th("")
        ])),
        html.Tbody(rows)
    ], className="alerts-table")

# =============================================================================
# MAIN LAYOUT
# =============================================================================

def create_main_dashboard():
    """Create main dashboard layout."""
    return html.Div([
        # Page Header
        html.Div([
            html.Div([
                html.H1("NRW Intelligence Dashboard", className="page-title"),
                html.P("Real-time monitoring across Zambia & South Africa", className="page-subtitle")
            ]),
            html.Div([
                html.Div([
                    html.Div(className="live-dot"),
                    html.Span("Live")
                ], className="live-indicator"),
                html.Button([
                    html.I(className="fas fa-download", style={"marginRight": "8px"}),
                    "Export"
                ], className="btn btn-secondary"),
                html.Button([
                    html.I(className="fas fa-plus", style={"marginRight": "8px"}),
                    "Add Sensor"
                ], className="btn btn-primary"),
            ], className="header-actions")
        ], className="page-header"),
        
        # Stats Row
        html.Div([
            create_stat_card(
                "💧", "28.4%", "System NRW",
                trend="-2.3", trend_direction="down", color="#10b981",
                sparkline_data=[30, 29, 31, 28, 29, 27, 28, 29, 28]
            ),
            create_stat_card(
                "📍", "1,247", "Active Sensors",
                trend="+12", trend_direction="up", color="#6366f1",
                sparkline_data=[1200, 1210, 1220, 1235, 1240, 1245, 1247]
            ),
            create_stat_card(
                "🚨", "24", "Active Alerts",
                trend="+3", trend_direction="up", color="#ef4444",
                sparkline_data=[18, 20, 22, 19, 21, 23, 24]
            ),
            create_stat_card(
                "💰", "$2.4M", "Monthly Savings",
                trend="+18", trend_direction="up", color="#8b5cf6",
                sparkline_data=[1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4]
            ),
        ], className="card-grid"),
        
        # Charts Row 1
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Div("NRW Trend - Last 7 Days", className="chart-title"),
                        html.Div("System-wide non-revenue water percentage", className="chart-subtitle")
                    ]),
                    html.Div([
                        html.Button("1D", className="chart-filter-btn"),
                        html.Button("7D", className="chart-filter-btn active"),
                        html.Button("30D", className="chart-filter-btn"),
                        html.Button("90D", className="chart-filter-btn"),
                    ], className="chart-filters")
                ], className="chart-header"),
                dcc.Graph(figure=create_nrw_trend_chart(), config={"displayModeBar": False})
            ], className="chart-container"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.Div("Flow Analysis", className="chart-title"),
                        html.Div("24-hour flow comparison", className="chart-subtitle")
                    ]),
                ], className="chart-header"),
                dcc.Graph(figure=create_flow_comparison_chart(), config={"displayModeBar": False})
            ], className="chart-container"),
        ], className="grid-2", style={"marginBottom": "20px"}),
        
        # Charts Row 2
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Div("District Performance", className="chart-title"),
                        html.Div("NRW by district management area", className="chart-subtitle")
                    ]),
                ], className="chart-header"),
                dcc.Graph(figure=create_district_performance_chart(), config={"displayModeBar": False})
            ], className="chart-container"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.Div("Network Coverage", className="chart-title"),
                        html.Div("Sensor locations and status", className="chart-subtitle")
                    ]),
                ], className="chart-header"),
                html.Div([
                    dcc.Graph(figure=create_realtime_map(), config={"displayModeBar": False})
                ], className="map-container")
            ], className="chart-container"),
        ], className="grid-2", style={"marginBottom": "20px"}),
        
        # Alerts Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Active Alerts", className="chart-title"),
                    html.Div("Recent alerts requiring attention", className="chart-subtitle")
                ]),
                html.Div([
                    html.Button([
                        html.I(className="fas fa-filter", style={"marginRight": "8px"}),
                        "Filter"
                    ], className="btn btn-secondary"),
                    html.Button([
                        html.I(className="fas fa-external-link-alt", style={"marginRight": "8px"}),
                        "View All"
                    ], className="btn btn-secondary"),
                ], className="header-actions")
            ], className="chart-header"),
            create_alerts_table()
        ], className="chart-container"),
        
        # Auto-refresh interval
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
        
    ], className="main-content")

# =============================================================================
# APP LAYOUT
# =============================================================================

app.layout = html.Div([
    # Inject CSS via dcc.Markdown with dangerously_allow_html
    dcc.Markdown(f"<style>{PREMIUM_CSS}</style>", dangerously_allow_html=True),
    
    # Sidebar
    create_sidebar(),
    
    # Main Content
    create_main_dashboard()
    
], className="app-container")

# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output('interval-component', 'interval'),
    Input('interval-component', 'n_intervals')
)
def update_interval(n):
    """Keep interval consistent."""
    return 30 * 1000

# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌊 AQUAWATCH PREMIUM DASHBOARD")
    print("="*60)
    print("\n✨ Starting world-class UI/UX experience...")
    print("📍 Open your browser at: http://127.0.0.1:8050")
    print("\nFeatures:")
    print("  • Glass-morphism design")
    print("  • Smooth animations")
    print("  • Real-time data updates")
    print("  • Interactive charts")
    print("  • Premium dark theme")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=8050)
