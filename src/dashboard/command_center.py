"""
AquaWatch Command Center - National Water Operations Dashboard
================================================================

Design Philosophy:
- Command-center grade control room interface
- Dark background with cyan/aqua glowing accents
- Everything visible at once - no scrolling
- Designed for large screens and wall displays
- Calm, powerful, and authoritative

Reference: NASA Control Room, Power Grid Operations, Water Authority HQ
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
import json

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="AquaWatch Command Center",
    update_title=None,
)

# Inject custom CSS properly via index_string
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        /* ============================================
           AQUAWATCH COMMAND CENTER
           National Water Operations Dashboard
           Dark • Powerful • Authoritative
           ============================================ */
        
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --bg-darkest: #020617;
            --bg-darker: #0f172a;
            --bg-dark: #1e293b;
            --bg-panel: rgba(15, 23, 42, 0.8);
            --bg-card: rgba(30, 41, 59, 0.6);
            --sky-400: #38bdf8;
            --sky-500: #0ea5e9;
            --sky-glow: rgba(56, 189, 248, 0.15);
            --cyan-400: #22d3ee;
            --cyan-500: #06b6d4;
            --cyan-glow: rgba(34, 211, 238, 0.12);
            --blue-400: #60a5fa;
            --blue-500: #3b82f6;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --status-normal: #34d399;
            --status-normal-bg: rgba(52, 211, 153, 0.1);
            --status-warning: #fbbf24;
            --status-warning-bg: rgba(251, 191, 36, 0.1);
            --status-alert: #f87171;
            --status-alert-bg: rgba(248, 113, 113, 0.1);
            --border-dark: #334155;
            --border-light: #475569;
            --glow-cyan: 0 0 20px rgba(34, 211, 238, 0.15);
            --glow-sky: 0 0 30px rgba(56, 189, 248, 0.12);
            --glow-intense: 0 0 40px rgba(34, 211, 238, 0.25);
        }
        
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: #020617 !important;
            color: #f1f5f9;
            min-height: 100vh;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
        }
        
        ._dash-loading, ._dash-error, .dash-debug-menu,
        .modebar, .plotly-notifier, [class*="dash-debug"] {
            display: none !important;
        }
        
        .command-center {
            display: grid;
            grid-template-columns: 80px 1fr 320px;
            grid-template-rows: 70px 1fr 140px;
            height: 100vh;
            gap: 1px;
            background: #334155;
        }
        
        .header-bar {
            grid-column: 1 / -1;
            background: #0f172a;
            border-bottom: 1px solid #334155;
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .brand-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #22d3ee 0%, #38bdf8 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 25px rgba(34, 211, 238, 0.4);
        }
        
        .brand-title {
            font-size: 20px;
            font-weight: 600;
            color: #f1f5f9;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        .brand-subtitle {
            font-size: 11px;
            color: #64748b;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        .header-center {
            display: flex;
            align-items: center;
            gap: 48px;
        }
        
        .header-stat {
            text-align: center;
        }
        
        .header-stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 28px;
            font-weight: 600;
            color: #22d3ee;
            text-shadow: 0 0 20px rgba(34, 211, 238, 0.5);
        }
        
        .header-stat-label {
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .header-time { text-align: right; }
        
        .time-display {
            font-family: 'JetBrains Mono', monospace;
            font-size: 36px;
            font-weight: 300;
            color: #38bdf8;
            text-shadow: 0 0 30px rgba(56, 189, 248, 0.5);
            letter-spacing: 3px;
        }
        
        .date-display {
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .left-panel {
            background: #0f172a;
            border-right: 1px solid #334155;
            padding: 16px 8px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .status-indicator {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 12px 4px;
            border-radius: 8px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid #334155;
            transition: all 0.3s ease;
        }
        
        .status-indicator:hover {
            border-color: #22d3ee;
            box-shadow: 0 0 20px rgba(34, 211, 238, 0.2);
        }
        
        .status-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            margin-bottom: 8px;
        }
        
        .status-icon.online {
            background: rgba(52, 211, 153, 0.15);
            color: #34d399;
            box-shadow: 0 0 15px rgba(52, 211, 153, 0.4);
        }
        
        .status-icon.warning {
            background: rgba(251, 191, 36, 0.15);
            color: #fbbf24;
            box-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
        }
        
        .status-icon.alert {
            background: rgba(248, 113, 113, 0.15);
            color: #f87171;
            box-shadow: 0 0 15px rgba(248, 113, 113, 0.4);
        }
        
        .status-label {
            font-size: 8px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: center;
            line-height: 1.3;
        }
        
        .main-area {
            background: #020617;
            display: grid;
            grid-template-rows: 180px 1fr;
            gap: 1px;
        }
        
        .pressure-panel {
            background: #0f172a;
            padding: 16px 24px;
            border-bottom: 1px solid #334155;
        }
        
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .panel-title {
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 2px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel-title::before {
            content: '';
            width: 10px;
            height: 10px;
            background: #22d3ee;
            border-radius: 2px;
            box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
        }
        
        .panel-legend {
            display: flex;
            gap: 24px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: #94a3b8;
        }
        
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .legend-dot.p1 { background: #38bdf8; box-shadow: 0 0 10px #38bdf8; }
        .legend-dot.p2 { background: #22d3ee; box-shadow: 0 0 10px #22d3ee; }
        
        .map-panel {
            background: #020617;
            position: relative;
            overflow: hidden;
        }
        
        .map-grid {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(51, 65, 85, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(51, 65, 85, 0.3) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
        }
        
        .map-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            background: 
                radial-gradient(ellipse at 30% 40%, rgba(34, 211, 238, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 60%, rgba(56, 189, 248, 0.08) 0%, transparent 50%);
        }
        
        .right-panel {
            background: #0f172a;
            border-left: 1px solid #334155;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .data-section {
            padding: 16px;
            border-bottom: 1px solid #334155;
        }
        
        .section-title {
            font-size: 10px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-title::before {
            content: '';
            width: 6px;
            height: 6px;
            background: #22d3ee;
            border-radius: 1px;
        }
        
        .dma-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .dma-item {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 12px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .dma-item:hover {
            border-color: #22d3ee;
            background: rgba(34, 211, 238, 0.05);
        }
        
        .dma-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .dma-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .dma-status.normal { background: #34d399; box-shadow: 0 0 10px #34d399; }
        .dma-status.warning { background: #fbbf24; box-shadow: 0 0 10px #fbbf24; }
        .dma-status.alert { background: #f87171; box-shadow: 0 0 10px #f87171; }
        
        .dma-name {
            font-size: 13px;
            color: #f1f5f9;
            font-weight: 500;
        }
        
        .dma-location {
            font-size: 10px;
            color: #64748b;
        }
        
        .dma-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            font-weight: 600;
            color: #22d3ee;
        }
        
        .dma-unit {
            font-size: 11px;
            color: #64748b;
            margin-left: 2px;
        }
        
        .alert-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex: 1;
            overflow-y: auto;
            padding-right: 4px;
        }
        
        .alert-item {
            background: rgba(30, 41, 59, 0.6);
            border-left: 3px solid #fbbf24;
            padding: 12px 14px;
            border-radius: 0 6px 6px 0;
        }
        
        .alert-item.critical { border-left-color: #f87171; }
        .alert-item.info { border-left-color: #22d3ee; }
        
        .alert-time {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #64748b;
            margin-bottom: 4px;
        }
        
        .alert-message {
            font-size: 12px;
            color: #cbd5e1;
            line-height: 1.4;
        }
        
        .alert-zone {
            font-size: 10px;
            color: #22d3ee;
            margin-top: 6px;
        }
        
        .bottom-panel {
            grid-column: 1 / -1;
            background: #0f172a;
            border-top: 1px solid #334155;
            padding: 16px 32px;
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 20px;
        }
        
        .metric-gauge {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 12px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid #334155;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .metric-gauge:hover {
            border-color: #22d3ee;
            box-shadow: 0 0 25px rgba(34, 211, 238, 0.2);
        }
        
        .gauge-ring {
            position: relative;
            width: 80px;
            height: 80px;
            margin-bottom: 8px;
        }
        
        .gauge-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 10;
        }
        
        .gauge-number {
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            font-weight: 600;
            color: #f1f5f9;
        }
        
        .gauge-unit {
            font-size: 10px;
            color: #64748b;
            display: block;
        }
        
        .gauge-label {
            font-size: 10px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: center;
        }
        
        .scan-effect {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #22d3ee, transparent);
            opacity: 0.4;
            animation: scan-line 8s linear infinite;
            pointer-events: none;
            z-index: 1000;
        }
        
        @keyframes scan-line {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100vh); }
        }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
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

# =============================================================================
# DATA
# =============================================================================

def generate_pressure_data():
    """Generate 24-hour pressure data for visualization."""
    hours = 24
    times = pd.date_range(end=datetime.now(), periods=hours*4, freq='15min')
    
    # Create smooth pressure curves with day/night variation
    base_p1 = 48
    base_p2 = 44
    
    p1_values = []
    p2_values = []
    
    for i, t in enumerate(times):
        hour = t.hour
        # Lower pressure at night (0-5 AM)
        night_factor = 1.0 if 6 <= hour <= 22 else 0.85
        
        p1 = base_p1 * night_factor + 4*np.sin(i/16*np.pi) + np.random.normal(0, 0.2)
        p2 = base_p2 * night_factor + 3.5*np.sin(i/16*np.pi + 0.3) + np.random.normal(0, 0.2)
        
        p1_values.append(p1)
        p2_values.append(p2)
    
    # Introduce anomaly
    for i in range(-10, 0):
        p2_values[i] -= 2.5 + np.random.normal(0, 0.3)
    
    return times, p1_values, p2_values

DMA_DATA = [
    {"name": "Lusaka Central", "zone": "ZM-LSK-001", "nrw": 28, "status": "normal"},
    {"name": "Lusaka East", "zone": "ZM-LSK-002", "nrw": 38, "status": "warning"},
    {"name": "Kitwe Industrial", "zone": "ZM-KTW-001", "nrw": 45, "status": "alert"},
    {"name": "Ndola CBD", "zone": "ZM-NDL-001", "nrw": 24, "status": "normal"},
    {"name": "Johannesburg N", "zone": "ZA-JHB-001", "nrw": 32, "status": "normal"},
    {"name": "Cape Town Metro", "zone": "ZA-CPT-001", "nrw": 21, "status": "normal"},
]

ALERTS = [
    {"time": "06:12:45", "message": "Pressure drop detected in segment P1-P2", "zone": "ZM-LSK-002", "level": "warning"},
    {"time": "05:48:22", "message": "High NRW alert: 45% threshold exceeded", "zone": "ZM-KTW-001", "level": "critical"},
    {"time": "05:15:00", "message": "Scheduled pressure review completed", "zone": "ZM-LSK-001", "level": "info"},
    {"time": "04:30:18", "message": "Night flow analysis: elevated minimum", "zone": "ZA-JHB-001", "level": "warning"},
]

# =============================================================================
# CHARTS
# =============================================================================

def create_pressure_chart():
    """Create command-center style pressure chart."""
    times, p1, p2 = generate_pressure_data()
    delta_p = [a - b for a, b in zip(p1, p2)]
    
    fig = go.Figure()
    
    # P1 - Primary sensor
    fig.add_trace(go.Scatter(
        x=times, y=p1,
        name='P1',
        line=dict(color='#38bdf8', width=2),
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.05)',
        hovertemplate='<b>P1</b>: %{y:.1f} bar<extra></extra>'
    ))
    
    # P2 - Secondary sensor
    fig.add_trace(go.Scatter(
        x=times, y=p2,
        name='P2',
        line=dict(color='#22d3ee', width=2),
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(34, 211, 238, 0.05)',
        hovertemplate='<b>P2</b>: %{y:.1f} bar<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=10, b=30),
        height=140,
        font=dict(family='JetBrains Mono', color='#94a3b8', size=10),
        xaxis=dict(
            gridcolor='rgba(51, 65, 85, 0.5)',
            linecolor='#334155',
            tickformat='%H:%M',
            showgrid=True,
            gridwidth=1,
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor='rgba(51, 65, 85, 0.5)',
            linecolor='#334155',
            showgrid=True,
            gridwidth=1,
            zeroline=False,
            title=dict(text='bar', font=dict(size=10)),
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=1.15,
            xanchor='right',
            x=1,
            font=dict(size=10),
            bgcolor='rgba(0,0,0,0)'
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#1e293b',
            bordercolor='#334155',
            font_size=11,
            font_family='JetBrains Mono'
        ),
    )
    
    return fig

def create_gauge_chart(value, max_val=100, color='#22d3ee'):
    """Create a ring gauge chart."""
    fig = go.Figure()
    
    # Background ring
    fig.add_trace(go.Pie(
        values=[1],
        hole=0.75,
        marker=dict(colors=['rgba(51, 65, 85, 0.3)']),
        textinfo='none',
        hoverinfo='none',
        showlegend=False,
    ))
    
    # Value ring
    remaining = max_val - value
    fig.add_trace(go.Pie(
        values=[value, remaining],
        hole=0.75,
        marker=dict(colors=[color, 'rgba(0,0,0,0)']),
        textinfo='none',
        hoverinfo='none',
        showlegend=False,
        direction='clockwise',
        sort=False,
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=5, r=5, t=5, b=5),
        height=80,
        width=80,
        showlegend=False,
    )
    
    return fig

def create_map_figure():
    """Create a stylized map visualization."""
    # City coordinates (approximate)
    cities = [
        {"name": "Lusaka", "lat": -15.4, "lon": 28.3, "nrw": 33, "country": "Zambia"},
        {"name": "Kitwe", "lat": -12.8, "lon": 28.2, "nrw": 45, "country": "Zambia"},
        {"name": "Ndola", "lat": -13.0, "lon": 28.6, "nrw": 24, "country": "Zambia"},
        {"name": "Livingstone", "lat": -17.8, "lon": 25.9, "nrw": 29, "country": "Zambia"},
        {"name": "Johannesburg", "lat": -26.2, "lon": 28.0, "nrw": 32, "country": "South Africa"},
        {"name": "Cape Town", "lat": -33.9, "lon": 18.4, "nrw": 21, "country": "South Africa"},
        {"name": "Durban", "lat": -29.9, "lon": 31.0, "nrw": 28, "country": "South Africa"},
        {"name": "Pretoria", "lat": -25.7, "lon": 28.2, "nrw": 30, "country": "South Africa"},
    ]
    
    df = pd.DataFrame(cities)
    
    # Color based on NRW
    def get_color(nrw):
        if nrw < 25:
            return '#34d399'  # Normal
        elif nrw < 35:
            return '#fbbf24'  # Warning
        else:
            return '#f87171'  # Alert
    
    df['color'] = df['nrw'].apply(get_color)
    df['size'] = df['nrw'] * 0.8 + 10
    
    fig = go.Figure()
    
    # Add city markers
    for _, city in df.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[city['lon']],
            lat=[city['lat']],
            mode='markers+text',
            marker=dict(
                size=city['size'],
                color=city['color'],
                opacity=0.8,
                line=dict(width=1, color='rgba(255,255,255,0.3)'),
            ),
            text=city['name'],
            textposition='top center',
            textfont=dict(size=10, color='#cbd5e1'),
            hovertemplate=f"<b>{city['name']}</b><br>NRW: {city['nrw']}%<br>{city['country']}<extra></extra>",
            showlegend=False,
        ))
        
        # Add glow effect
        fig.add_trace(go.Scattergeo(
            lon=[city['lon']],
            lat=[city['lat']],
            mode='markers',
            marker=dict(
                size=city['size'] * 2,
                color=city['color'],
                opacity=0.15,
            ),
            hoverinfo='skip',
            showlegend=False,
        ))
    
    fig.update_geos(
        visible=True,
        resolution=50,
        scope='africa',
        showcountries=True,
        countrycolor='#334155',
        showsubunits=True,
        subunitcolor='#334155',
        showland=True,
        landcolor='#0f172a',
        showocean=True,
        oceancolor='#020617',
        showlakes=True,
        lakecolor='#1e3a5f',
        showrivers=True,
        rivercolor='#1e3a5f',
        bgcolor='rgba(0,0,0,0)',
        lonaxis=dict(range=[10, 40]),
        lataxis=dict(range=[-40, -5]),
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=None,
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
        ),
        hoverlabel=dict(
            bgcolor='#1e293b',
            bordercolor='#334155',
            font_size=12,
            font_family='Inter'
        ),
    )
    
    return fig

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_header():
    return html.Div([
        # Brand
        html.Div([
            html.Div("💧", className="brand-icon"),
            html.Div([
                html.Div("AquaWatch", className="brand-title"),
                html.Div("Command Center", className="brand-subtitle"),
            ]),
        ], className="header-brand"),
        
        # Center Stats
        html.Div([
            html.Div([
                html.Div("6", className="header-stat-value"),
                html.Div("Active DMAs", className="header-stat-label"),
            ], className="header-stat"),
            html.Div([
                html.Div("147", className="header-stat-value"),
                html.Div("Sensors Online", className="header-stat-label"),
            ], className="header-stat"),
            html.Div([
                html.Div("99.7%", className="header-stat-value"),
                html.Div("Uptime", className="header-stat-label"),
            ], className="header-stat"),
        ], className="header-center"),
        
        # Time
        html.Div([
            html.Div(id="live-time-display", className="time-display"),
            html.Div(datetime.now().strftime("%d %B %Y").upper(), className="date-display"),
        ], className="header-time"),
    ], className="header-bar")


def create_left_panel():
    indicators = [
        {"icon": "●", "label": "System Health", "status": "online"},
        {"icon": "◉", "label": "Sensors", "status": "online"},
        {"icon": "◎", "label": "Data Link", "status": "online"},
        {"icon": "◈", "label": "AI Engine", "status": "online"},
        {"icon": "◇", "label": "Alerts", "status": "warning"},
        {"icon": "◆", "label": "Archive", "status": "online"},
    ]
    
    return html.Div([
        html.Div([
            html.Div([
                html.Span(ind["icon"]),
            ], className=f"status-icon {ind['status']}"),
            html.Div(ind["label"], className="status-label"),
        ], className="status-indicator")
        for ind in indicators
    ], className="left-panel")


def create_pressure_panel():
    return html.Div([
        html.Div([
            html.Div("Live Pressure Intelligence", className="panel-title"),
            html.Div([
                html.Div([
                    html.Div(className="legend-dot p1"),
                    html.Span("Sensor P1"),
                ], className="legend-item"),
                html.Div([
                    html.Div(className="legend-dot p2"),
                    html.Span("Sensor P2"),
                ], className="legend-item"),
            ], className="panel-legend"),
        ], className="panel-header"),
        dcc.Graph(
            figure=create_pressure_chart(),
            config={"displayModeBar": False, "staticPlot": False},
            style={"height": "140px"},
        ),
    ], className="pressure-panel")


def create_map_panel():
    return html.Div([
        html.Div(className="map-grid"),
        html.Div(className="map-overlay"),
        dcc.Graph(
            figure=create_map_figure(),
            config={"displayModeBar": False, "scrollZoom": False},
            style={"height": "100%", "width": "100%"},
        ),
    ], className="map-panel")


def create_right_panel():
    return html.Div([
        # DMA Section
        html.Div([
            html.Div("Priority Zones", className="section-title"),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div(className=f"dma-status {dma['status']}"),
                        html.Div([
                            html.Div(dma["name"], className="dma-name"),
                            html.Div(dma["zone"], className="dma-location"),
                        ]),
                    ], className="dma-info"),
                    html.Div([
                        html.Span(f"{dma['nrw']}", className="dma-value"),
                        html.Span("%", className="dma-unit"),
                    ]),
                ], className="dma-item")
                for dma in sorted(DMA_DATA, key=lambda x: x['nrw'], reverse=True)[:5]
            ], className="dma-list"),
        ], className="data-section"),
        
        # Alerts Section
        html.Div([
            html.Div("Active Alerts", className="section-title"),
            html.Div([
                html.Div([
                    html.Div(alert["time"], className="alert-time"),
                    html.Div(alert["message"], className="alert-message"),
                    html.Div(alert["zone"], className="alert-zone"),
                ], className=f"alert-item {alert['level']}")
                for alert in ALERTS
            ], className="alert-list"),
        ], className="data-section", style={"flex": "1", "display": "flex", "flexDirection": "column"}),
    ], className="right-panel")


def create_bottom_panel():
    metrics = [
        {"label": "NRW Rate", "value": 31, "unit": "%", "color": "#fbbf24"},
        {"label": "Leak Probability", "value": 72, "unit": "%", "color": "#f87171"},
        {"label": "Volume Loss", "value": 45, "unit": "m³/d", "color": "#22d3ee"},
        {"label": "Pressure Index", "value": 87, "unit": "%", "color": "#34d399"},
        {"label": "Response Time", "value": 24, "unit": "min", "color": "#38bdf8"},
        {"label": "Coverage", "value": 94, "unit": "%", "color": "#a78bfa"},
    ]
    
    return html.Div([
        html.Div([
            html.Div([
                dcc.Graph(
                    figure=create_gauge_chart(m["value"], color=m["color"]),
                    config={"displayModeBar": False, "staticPlot": True},
                    style={"height": "80px", "width": "80px"},
                ),
                html.Div([
                    html.Span(m["value"], className="gauge-number"),
                    html.Span(m["unit"], className="gauge-unit"),
                ], className="gauge-value"),
            ], className="gauge-ring"),
            html.Div(m["label"], className="gauge-label"),
        ], className="metric-gauge")
        for m in metrics
    ], className="bottom-panel")


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    # Scan Line Effect
    html.Div(className="scan-effect"),
    
    # Main Grid
    html.Div([
        # Header
        create_header(),
        
        # Left Panel
        create_left_panel(),
        
        # Main Area
        html.Div([
            create_pressure_panel(),
            create_map_panel(),
        ], className="main-area"),
        
        # Right Panel
        create_right_panel(),
        
        # Bottom Panel
        create_bottom_panel(),
    ], className="command-center"),
    
    # Live time update
    dcc.Interval(id="time-interval", interval=1000, n_intervals=0),
])

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output("live-time-display", "children"),
    Input("time-interval", "n_intervals")
)
def update_time(n):
    return datetime.now().strftime("%H:%M:%S")


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌊 AQUAWATCH COMMAND CENTER")
    print("   National Water Operations Dashboard")
    print("="*70)
    print("\n   🖥️  Dashboard: http://127.0.0.1:8050")
    print("   🎨  Design: Dark • Powerful • Authoritative")
    print("   📺  Optimized for wall displays")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=False, port=8052)
