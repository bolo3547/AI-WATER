"""
AquaWatch NRW - Premium Dashboard
=================================

Modern dark-theme dashboard with inline styles for reliability.
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# =============================================================================
# STYLE CONSTANTS
# =============================================================================

# Colors
BG_DARK = "#0f0f23"
BG_CARD = "rgba(30, 30, 50, 0.95)"
PRIMARY = "#6366f1"
SECONDARY = "#8b5cf6"
ACCENT = "#22d3ee"
SUCCESS = "#10b981"
WARNING = "#f59e0b"
DANGER = "#ef4444"
INFO = "#3b82f6"
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"

# Common styles
CARD_STYLE = {
    "background": BG_CARD,
    "borderRadius": "16px",
    "padding": "24px",
    "border": "1px solid rgba(255, 255, 255, 0.08)",
    "boxShadow": "0 4px 20px rgba(0, 0, 0, 0.3)",
}

METRIC_CARD_STYLE = {
    **CARD_STYLE,
    "position": "relative",
    "overflow": "hidden",
    "minHeight": "140px",
}


# =============================================================================
# INITIALIZE APP
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "AquaWatch | NRW Intelligence"
server = app.server


# =============================================================================
# DATA GENERATORS
# =============================================================================

def get_alerts_data():
    return [
        {
            "id": "ALT-0142",
            "title": "Distribution Main Leak",
            "location": "Kafue Road, Kitwe",
            "dma": "DMA-KIT-003",
            "status": "critical",
            "probability": 92,
            "loss": 125.5,
            "time": "2 min ago"
        },
        {
            "id": "ALT-0138",
            "title": "Service Connection Anomaly",
            "location": "Chilenje, Lusaka",
            "dma": "DMA-LSK-002",
            "status": "critical",
            "probability": 88,
            "loss": 45.2,
            "time": "15 min ago"
        },
        {
            "id": "ALT-0135",
            "title": "Night Flow Anomaly",
            "location": "Industrial Zone, Ndola",
            "dma": "DMA-NDO-001",
            "status": "high",
            "probability": 76,
            "loss": 68.0,
            "time": "1 hour ago"
        },
        {
            "id": "ALT-0132",
            "title": "Meter Under-registration",
            "location": "CBD, Kitwe",
            "dma": "DMA-KIT-001",
            "status": "high",
            "probability": 71,
            "loss": 32.5,
            "time": "2 hours ago"
        },
    ]


def get_dma_data():
    return [
        {"code": "DMA-KIT-001", "name": "Kitwe Central", "nrw": 28.5, "trend": -2.3},
        {"code": "DMA-KIT-002", "name": "Kitwe North", "nrw": 22.1, "trend": -1.5},
        {"code": "DMA-KIT-003", "name": "Kitwe South", "nrw": 45.2, "trend": +3.2},
        {"code": "DMA-NDO-001", "name": "Ndola CBD", "nrw": 31.0, "trend": -0.8},
        {"code": "DMA-LSK-002", "name": "Lusaka East", "nrw": 52.3, "trend": +4.5},
    ]


# =============================================================================
# CHARTS
# =============================================================================

def create_trend_chart():
    dates = pd.date_range(start='2025-10-01', end='2026-01-16', freq='D')
    np.random.seed(42)
    base = 35
    trend = np.linspace(0, -3, len(dates))
    noise = np.random.normal(0, 1.5, len(dates))
    seasonal = 2 * np.sin(np.linspace(0, 4*np.pi, len(dates)))
    nrw = base + trend + noise + seasonal

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=nrw,
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color=PRIMARY, width=2),
        hovertemplate='%{x|%b %d}<br>NRW: %{y:.1f}%<extra></extra>'
    ))
    fig.add_hline(y=25, line_dash="dash", line_color=SUCCESS,
                  annotation_text="Target: 25%", annotation_position="right")
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=250,
        font=dict(color=TEXT_SECONDARY),
        xaxis=dict(showgrid=False, color=TEXT_MUTED),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', 
                   color=TEXT_MUTED, ticksuffix='%'),
        showlegend=False
    )
    return fig


def create_donut_chart():
    labels = ['Leakage', 'Service', 'Apparent', 'Unbilled']
    values = [45, 25, 20, 10]
    colors = [DANGER, WARNING, SECONDARY, SUCCESS]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors, line=dict(color=BG_DARK, width=3)),
        textinfo='percent', textfont=dict(color=TEXT_PRIMARY, size=12),
        hovertemplate='%{label}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
        showlegend=False,
        annotations=[dict(text='<b>IWA</b><br>Balance', x=0.5, y=0.5,
                         font=dict(size=14, color=TEXT_PRIMARY), showarrow=False)]
    )
    return fig


def create_flow_chart():
    hours = list(range(24))
    np.random.seed(123)
    base = [60, 55, 50, 48, 52, 80, 150, 200, 180, 160, 145, 140,
            145, 150, 140, 135, 150, 180, 200, 190, 160, 130, 100, 75]
    actual = [v + np.random.normal(0, 8) for v in base]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=actual,
        fill='tozeroy',
        fillcolor='rgba(34, 211, 238, 0.15)',
        line=dict(color=ACCENT, width=2),
    ))
    fig.add_hline(y=50, line_dash="dot", line_color=DANGER)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=20, t=20, b=50),
        height=200,
        font=dict(color=TEXT_SECONDARY),
        xaxis=dict(showgrid=False, color=TEXT_MUTED, tickmode='array',
                   tickvals=[0, 6, 12, 18, 23], ticktext=['00:00', '06:00', '12:00', '18:00', '23:00']),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color=TEXT_MUTED),
        showlegend=False
    )
    return fig


# =============================================================================
# COMPONENTS
# =============================================================================

def make_metric_card(label, value, subtitle, icon, color):
    return html.Div([
        # Gradient top bar
        html.Div(style={
            "position": "absolute",
            "top": "0",
            "left": "0",
            "right": "0",
            "height": "4px",
            "background": f"linear-gradient(90deg, {color}, {SECONDARY})",
            "borderRadius": "16px 16px 0 0",
        }),
        # Icon
        html.Div([
            html.I(className=f"fas {icon}", style={"fontSize": "24px", "color": color})
        ], style={
            "position": "absolute",
            "top": "20px",
            "right": "20px",
            "opacity": "0.5"
        }),
        # Content
        html.Div([
            html.P(label, style={
                "fontSize": "12px",
                "fontWeight": "500",
                "color": TEXT_MUTED,
                "textTransform": "uppercase",
                "letterSpacing": "1px",
                "marginBottom": "8px"
            }),
            html.H2(value, style={
                "fontSize": "36px",
                "fontWeight": "700",
                "color": TEXT_PRIMARY,
                "margin": "0",
                "lineHeight": "1"
            }),
            html.P(subtitle, style={
                "fontSize": "13px",
                "color": SUCCESS if "improvement" in subtitle.lower() or "↓" in subtitle else WARNING,
                "marginTop": "10px",
                "marginBottom": "0"
            })
        ])
    ], style=METRIC_CARD_STYLE)


def make_alert_item(alert):
    status_colors = {"critical": DANGER, "high": WARNING, "medium": INFO}
    color = status_colors.get(alert["status"], TEXT_MUTED)
    
    return html.Div([
        # Status indicator
        html.Div(style={
            "width": "4px",
            "background": color,
            "borderRadius": "4px",
            "marginRight": "16px",
        }),
        # Icon
        html.Div([
            html.I(className="fas fa-exclamation-triangle", style={"color": color})
        ], style={
            "width": "40px",
            "height": "40px",
            "borderRadius": "10px",
            "background": f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "marginRight": "16px",
            "flexShrink": "0"
        }),
        # Content
        html.Div([
            html.Div([
                html.Span(alert["title"], style={"fontWeight": "600", "color": TEXT_PRIMARY}),
                html.Span(f" • {alert['time']}", style={"color": TEXT_MUTED, "fontSize": "12px"})
            ]),
            html.Div([
                html.Span(alert["location"], style={"color": TEXT_SECONDARY, "fontSize": "13px"}),
            ], style={"marginTop": "4px"}),
            html.Div([
                html.Span(f"{alert['probability']}%", style={
                    "background": f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)",
                    "color": color,
                    "padding": "2px 10px",
                    "borderRadius": "20px",
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "marginRight": "10px"
                }),
                html.Span(f"{alert['loss']} m³/day", style={"color": DANGER, "fontSize": "12px"})
            ], style={"marginTop": "8px"})
        ], style={"flex": "1"})
    ], style={
        "display": "flex",
        "alignItems": "stretch",
        "padding": "16px",
        "background": "rgba(255, 255, 255, 0.02)",
        "borderRadius": "12px",
        "marginBottom": "10px",
    })


def make_dma_item(dma):
    if dma['nrw'] > 40:
        color = DANGER
    elif dma['nrw'] > 30:
        color = WARNING
    elif dma['nrw'] > 20:
        color = INFO
    else:
        color = SUCCESS
    
    trend_color = SUCCESS if dma['trend'] < 0 else DANGER
    trend_icon = "fa-arrow-down" if dma['trend'] < 0 else "fa-arrow-up"
    
    return html.Div([
        html.Div([
            html.Div(dma['name'], style={"fontWeight": "500", "color": TEXT_PRIMARY, "fontSize": "14px"}),
            html.Div(dma['code'], style={"color": TEXT_MUTED, "fontSize": "11px", "fontFamily": "monospace"})
        ]),
        html.Div([
            html.Span(f"{dma['nrw']:.1f}%", style={
                "fontSize": "18px",
                "fontWeight": "700",
                "color": color,
                "marginRight": "12px"
            }),
            html.Span([
                html.I(className=f"fas {trend_icon}", style={"marginRight": "4px", "fontSize": "10px"}),
                f"{abs(dma['trend']):.1f}%"
            ], style={"fontSize": "12px", "color": trend_color})
        ], style={"display": "flex", "alignItems": "center"})
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "14px 16px",
        "background": "rgba(255, 255, 255, 0.02)",
        "borderRadius": "10px",
        "marginBottom": "8px",
    })


# =============================================================================
# MAIN LAYOUT
# =============================================================================

def create_layout():
    alerts = get_alerts_data()
    dmas = get_dma_data()
    
    total_loss = sum(a['loss'] for a in alerts)
    critical_count = len([a for a in alerts if a['status'] == 'critical'])
    avg_nrw = sum(d['nrw'] for d in dmas) / len(dmas)
    
    return html.Div([
        # Main Container
        html.Div([
            # ===== HEADER =====
            html.Div([
                # Logo & Title
                html.Div([
                    html.Div([
                        html.I(className="fas fa-water", style={"fontSize": "24px"})
                    ], style={
                        "width": "48px",
                        "height": "48px",
                        "background": f"linear-gradient(135deg, {PRIMARY}, {SECONDARY})",
                        "borderRadius": "12px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginRight": "16px",
                        "color": "white"
                    }),
                    html.Div([
                        html.H1("AquaWatch", style={
                            "fontSize": "24px",
                            "fontWeight": "700",
                            "color": TEXT_PRIMARY,
                            "margin": "0"
                        }),
                        html.P("NRW Intelligence Platform", style={
                            "fontSize": "12px",
                            "color": TEXT_MUTED,
                            "margin": "0",
                            "textTransform": "uppercase",
                            "letterSpacing": "1px"
                        })
                    ])
                ], style={"display": "flex", "alignItems": "center"}),
                
                # Live Status
                html.Div([
                    html.Span("●", style={
                        "color": SUCCESS,
                        "marginRight": "8px",
                        "fontSize": "12px"
                    }),
                    html.Span("Live", style={"color": SUCCESS, "fontWeight": "600", "marginRight": "20px"}),
                    html.Span(datetime.now().strftime("%B %d, %Y • %H:%M"), style={
                        "color": TEXT_MUTED,
                        "fontSize": "14px"
                    })
                ], style={"display": "flex", "alignItems": "center"})
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "24px 32px",
                "borderBottom": "1px solid rgba(255, 255, 255, 0.05)"
            }),
            
            # ===== CONTENT =====
            html.Div([
                # Metrics Row
                dbc.Row([
                    dbc.Col([
                        make_metric_card("Network NRW", f"{avg_nrw:.1f}%", "↓ 2.3% improvement", "fa-chart-pie", PRIMARY)
                    ], lg=3, md=6, className="mb-4"),
                    dbc.Col([
                        make_metric_card("Critical Alerts", str(critical_count), "Immediate attention needed", "fa-bell", DANGER)
                    ], lg=3, md=6, className="mb-4"),
                    dbc.Col([
                        make_metric_card("Daily Loss", f"{total_loss:.0f} m³", f"~${total_loss * 2.5:.0f}/day revenue", "fa-tint", WARNING)
                    ], lg=3, md=6, className="mb-4"),
                    dbc.Col([
                        make_metric_card("Active Sensors", "247", "All systems operational", "fa-satellite-dish", SUCCESS)
                    ], lg=3, md=6, className="mb-4"),
                ]),
                
                # Main Content Row
                dbc.Row([
                    # Left Column - Charts
                    dbc.Col([
                        # Trend Chart
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-chart-line", style={"color": PRIMARY, "marginRight": "10px"}),
                                html.Span("NRW Performance Trend", style={"fontWeight": "600", "fontSize": "16px", "color": TEXT_PRIMARY}),
                                html.Span("90 Days", style={
                                    "marginLeft": "auto",
                                    "background": f"linear-gradient(135deg, {PRIMARY}, {SECONDARY})",
                                    "color": "white",
                                    "padding": "4px 12px",
                                    "borderRadius": "20px",
                                    "fontSize": "12px",
                                    "fontWeight": "600"
                                })
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),
                            dcc.Graph(figure=create_trend_chart(), config={'displayModeBar': False})
                        ], style=CARD_STYLE),
                        
                        # Two charts side by side
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.I(className="fas fa-pie-chart", style={"color": SECONDARY, "marginRight": "10px"}),
                                        html.Span("Loss Breakdown", style={"fontWeight": "600", "color": TEXT_PRIMARY})
                                    ], style={"marginBottom": "16px"}),
                                    dcc.Graph(figure=create_donut_chart(), config={'displayModeBar': False})
                                ], style=CARD_STYLE)
                            ], md=6, className="mt-4"),
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.I(className="fas fa-wave-square", style={"color": ACCENT, "marginRight": "10px"}),
                                        html.Span("24h Flow Pattern", style={"fontWeight": "600", "color": TEXT_PRIMARY})
                                    ], style={"marginBottom": "16px"}),
                                    dcc.Graph(figure=create_flow_chart(), config={'displayModeBar': False})
                                ], style=CARD_STYLE)
                            ], md=6, className="mt-4"),
                        ])
                    ], lg=8),
                    
                    # Right Column - Alerts & DMAs
                    dbc.Col([
                        # Alerts
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-bell", style={"color": DANGER, "marginRight": "10px"}),
                                html.Span("Active Alerts", style={"fontWeight": "600", "color": TEXT_PRIMARY}),
                                html.Span(str(len(alerts)), style={
                                    "marginLeft": "auto",
                                    "background": DANGER,
                                    "color": "white",
                                    "padding": "2px 10px",
                                    "borderRadius": "20px",
                                    "fontSize": "12px",
                                    "fontWeight": "600"
                                })
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),
                            html.Div([make_alert_item(a) for a in alerts], style={"maxHeight": "350px", "overflowY": "auto"})
                        ], style=CARD_STYLE),
                        
                        # DMA Status
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-map-location-dot", style={"color": SUCCESS, "marginRight": "10px"}),
                                html.Span("DMA Status", style={"fontWeight": "600", "color": TEXT_PRIMARY})
                            ], style={"marginBottom": "20px"}),
                            html.Div([make_dma_item(d) for d in sorted(dmas, key=lambda x: x['nrw'], reverse=True)])
                        ], style={**CARD_STYLE, "marginTop": "20px"})
                    ], lg=4),
                ])
            ], style={"padding": "24px 32px"})
        ])
    ], style={
        "minHeight": "100vh",
        "background": f"linear-gradient(135deg, {BG_DARK} 0%, #1a1a2e 50%, #16213e 100%)",
        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    })


app.layout = create_layout()


def create_premium_dashboard():
    """Factory function for external use."""
    return app


if __name__ == "__main__":
    app.run(debug=True, port=8050)
