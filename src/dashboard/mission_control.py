"""
AquaWatch NRW - Mission Control Dashboard
=========================================

"Like SpaceX Mission Control, but for water."

A real-time command center for monitoring the entire
water network across multiple utilities and countries.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json

# =============================================================================
# STYLES - SPACEX/TESLA INSPIRED DARK THEME
# =============================================================================

COLORS = {
    'background': '#0a0a0a',
    'card_bg': '#141414',
    'card_border': '#2a2a2a',
    'text_primary': '#ffffff',
    'text_secondary': '#888888',
    'accent_blue': '#00a6ff',
    'accent_green': '#00ff88',
    'accent_red': '#ff4444',
    'accent_yellow': '#ffaa00',
    'accent_purple': '#aa66ff',
    'grid': '#1a1a1a'
}

FONTS = {
    'primary': 'Inter, -apple-system, sans-serif',
    'mono': 'JetBrains Mono, Consolas, monospace'
}

# Global styles
GLOBAL_STYLE = {
    'backgroundColor': COLORS['background'],
    'color': COLORS['text_primary'],
    'fontFamily': FONTS['primary'],
    'minHeight': '100vh',
    'padding': '0'
}

CARD_STYLE = {
    'backgroundColor': COLORS['card_bg'],
    'border': f"1px solid {COLORS['card_border']}",
    'borderRadius': '4px',
    'padding': '16px',
    'marginBottom': '16px'
}

HEADER_STYLE = {
    'backgroundColor': '#000000',
    'borderBottom': f"1px solid {COLORS['card_border']}",
    'padding': '12px 24px',
    'display': 'flex',
    'justifyContent': 'space-between',
    'alignItems': 'center'
}

METRIC_VALUE_STYLE = {
    'fontSize': '42px',
    'fontWeight': '600',
    'fontFamily': FONTS['mono'],
    'margin': '0',
    'lineHeight': '1.2'
}

METRIC_LABEL_STYLE = {
    'fontSize': '11px',
    'textTransform': 'uppercase',
    'letterSpacing': '1px',
    'color': COLORS['text_secondary'],
    'marginTop': '4px'
}


# =============================================================================
# DATA GENERATORS (Simulated real-time data)
# =============================================================================

def generate_network_status():
    """Generate network-wide status."""
    return {
        'total_sensors': 2847,
        'sensors_online': 2791,
        'uptime': 98.03,
        'data_points_today': 4_832_891,
        'alerts_active': 23,
        'alerts_critical': 3,
        'leaks_detected_today': 7,
        'drones_active': 4,
        'water_saved_ytd_m3': 2_847_293,
        'nrw_current': 32.4,
        'nrw_target': 25.0,
        'autonomy_level': 3
    }


def generate_utility_data():
    """Generate utility-level data."""
    utilities = [
        {'id': 'LWSC', 'name': 'Lusaka Water', 'country': 'Zambia', 'sensors': 487, 'nrw': 35.2, 'status': 'nominal'},
        {'id': 'NWSC', 'name': 'Nkana Water', 'country': 'Zambia', 'sensors': 312, 'nrw': 42.1, 'status': 'warning'},
        {'id': 'JHB_WATER', 'name': 'Johannesburg Water', 'country': 'South Africa', 'sensors': 892, 'nrw': 38.4, 'status': 'nominal'},
        {'id': 'CAPE_TOWN', 'name': 'Cape Town Water', 'country': 'South Africa', 'sensors': 756, 'nrw': 28.1, 'status': 'optimal'},
        {'id': 'ETHEKWINI', 'name': 'eThekwini Water', 'country': 'South Africa', 'sensors': 400, 'nrw': 36.7, 'status': 'nominal'},
    ]
    return utilities


def generate_live_events():
    """Generate live event feed."""
    events = [
        {'time': '00:00:12', 'type': 'LEAK', 'severity': 'HIGH', 'message': 'Leak detected in DMA_KABULONGA (450 L/hr)', 'utility': 'LWSC'},
        {'time': '00:00:08', 'type': 'DRONE', 'severity': 'INFO', 'message': 'Scout-2 mission complete, returning to base', 'utility': 'LWSC'},
        {'time': '00:00:05', 'type': 'SENSOR', 'severity': 'LOW', 'message': 'Sensor ESP32_0124 battery low (15%)', 'utility': 'JHB_WATER'},
        {'time': '00:00:03', 'type': 'AUTO', 'severity': 'INFO', 'message': 'Valve V-042 auto-adjusted, pressure normalized', 'utility': 'CAPE_TOWN'},
        {'time': '00:00:01', 'type': 'CREDITS', 'severity': 'INFO', 'message': '12,500 water credits minted from verified repair', 'utility': 'LWSC'},
    ]
    return events


def generate_flow_timeseries():
    """Generate flow rate time series."""
    now = datetime.now()
    times = [now - timedelta(hours=i) for i in range(24, 0, -1)]
    
    base_flow = 1500
    data = []
    for t in times:
        hour = t.hour
        # Simulate daily pattern
        if 6 <= hour <= 9:
            multiplier = 1.8  # Morning peak
        elif 18 <= hour <= 21:
            multiplier = 1.6  # Evening peak
        elif 0 <= hour <= 5:
            multiplier = 0.4  # Night low
        else:
            multiplier = 1.0
        
        flow = base_flow * multiplier + random.uniform(-100, 100)
        data.append({'time': t, 'flow': flow})
    
    return data


# =============================================================================
# COMPONENTS
# =============================================================================

def create_status_indicator(status, size=10):
    """Create a status dot."""
    color = {
        'optimal': COLORS['accent_green'],
        'nominal': COLORS['accent_blue'],
        'warning': COLORS['accent_yellow'],
        'critical': COLORS['accent_red']
    }.get(status, COLORS['text_secondary'])
    
    return html.Div(style={
        'width': f'{size}px',
        'height': f'{size}px',
        'borderRadius': '50%',
        'backgroundColor': color,
        'display': 'inline-block',
        'marginRight': '8px',
        'animation': 'pulse 2s infinite' if status == 'critical' else 'none'
    })


def create_metric_card(value, label, color=None, trend=None, unit=''):
    """Create a metric display card."""
    value_color = color if color else COLORS['text_primary']
    
    trend_element = None
    if trend:
        trend_color = COLORS['accent_green'] if trend > 0 else COLORS['accent_red']
        trend_icon = '▲' if trend > 0 else '▼'
        trend_element = html.Span(
            f" {trend_icon} {abs(trend):.1f}%",
            style={'fontSize': '14px', 'color': trend_color}
        )
    
    return html.Div([
        html.Div([
            html.Span(f"{value}{unit}", style={**METRIC_VALUE_STYLE, 'color': value_color}),
            trend_element
        ]),
        html.Div(label, style=METRIC_LABEL_STYLE)
    ], style=CARD_STYLE)


def create_utility_row(utility):
    """Create a row for utility in the table."""
    status_color = {
        'optimal': COLORS['accent_green'],
        'nominal': COLORS['accent_blue'],
        'warning': COLORS['accent_yellow'],
        'critical': COLORS['accent_red']
    }.get(utility['status'], COLORS['text_secondary'])
    
    return html.Tr([
        html.Td([
            create_status_indicator(utility['status']),
            html.Span(utility['name'])
        ], style={'padding': '12px'}),
        html.Td(utility['country'], style={'padding': '12px', 'color': COLORS['text_secondary']}),
        html.Td(f"{utility['sensors']:,}", style={'padding': '12px', 'fontFamily': FONTS['mono']}),
        html.Td(
            f"{utility['nrw']}%",
            style={
                'padding': '12px',
                'fontFamily': FONTS['mono'],
                'color': COLORS['accent_green'] if utility['nrw'] < 30 else 
                         COLORS['accent_yellow'] if utility['nrw'] < 40 else COLORS['accent_red']
            }
        ),
        html.Td(
            utility['status'].upper(),
            style={
                'padding': '12px',
                'fontSize': '11px',
                'fontWeight': '600',
                'color': status_color,
                'textTransform': 'uppercase'
            }
        )
    ], style={'borderBottom': f"1px solid {COLORS['card_border']}"})


def create_event_item(event):
    """Create an event feed item."""
    severity_colors = {
        'HIGH': COLORS['accent_red'],
        'MEDIUM': COLORS['accent_yellow'],
        'LOW': COLORS['accent_blue'],
        'INFO': COLORS['text_secondary']
    }
    
    type_icons = {
        'LEAK': '💧',
        'DRONE': '🚁',
        'SENSOR': '📡',
        'AUTO': '🤖',
        'CREDITS': '🪙'
    }
    
    return html.Div([
        html.Div([
            html.Span(
                f"T-{event['time']}", 
                style={
                    'fontFamily': FONTS['mono'],
                    'fontSize': '11px',
                    'color': COLORS['text_secondary']
                }
            ),
            html.Span(
                event['severity'],
                style={
                    'marginLeft': '12px',
                    'fontSize': '10px',
                    'fontWeight': '600',
                    'color': severity_colors.get(event['severity'], COLORS['text_secondary']),
                    'padding': '2px 6px',
                    'borderRadius': '2px',
                    'border': f"1px solid {severity_colors.get(event['severity'], COLORS['text_secondary'])}"
                }
            )
        ]),
        html.Div([
            html.Span(
                type_icons.get(event['type'], '•'),
                style={'marginRight': '8px'}
            ),
            html.Span(event['message'])
        ], style={'marginTop': '4px', 'fontSize': '13px'}),
        html.Div(
            event['utility'],
            style={
                'fontSize': '11px',
                'color': COLORS['text_secondary'],
                'marginTop': '2px'
            }
        )
    ], style={
        'padding': '12px',
        'borderBottom': f"1px solid {COLORS['card_border']}"
    })


def create_flow_chart():
    """Create the main flow rate chart."""
    data = generate_flow_timeseries()
    
    fig = go.Figure()
    
    # Flow rate line
    fig.add_trace(go.Scatter(
        x=[d['time'] for d in data],
        y=[d['flow'] for d in data],
        mode='lines',
        line=dict(color=COLORS['accent_blue'], width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 166, 255, 0.1)',
        name='Flow Rate'
    ))
    
    # Expected baseline
    fig.add_trace(go.Scatter(
        x=[d['time'] for d in data],
        y=[1200] * len(data),  # Baseline
        mode='lines',
        line=dict(color=COLORS['text_secondary'], width=1, dash='dot'),
        name='Expected'
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font=dict(color=COLORS['text_secondary'], family=FONTS['primary']),
        margin=dict(l=50, r=20, t=30, b=40),
        height=300,
        xaxis=dict(
            gridcolor=COLORS['grid'],
            zerolinecolor=COLORS['grid'],
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            zerolinecolor=COLORS['grid'],
            title='Flow Rate (L/hr)'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        hovermode='x unified'
    )
    
    return fig


def create_map():
    """Create network map."""
    # Sample sensor locations
    locations = [
        {'lat': -15.4167, 'lon': 28.2833, 'name': 'Lusaka HQ', 'status': 'optimal', 'sensors': 150},
        {'lat': -15.3500, 'lon': 28.3000, 'name': 'Lusaka North', 'status': 'nominal', 'sensors': 120},
        {'lat': -15.5000, 'lon': 28.2500, 'name': 'Lusaka South', 'status': 'warning', 'sensors': 95},
        {'lat': -26.2041, 'lon': 28.0473, 'name': 'Johannesburg', 'status': 'nominal', 'sensors': 450},
        {'lat': -33.9249, 'lon': 18.4241, 'name': 'Cape Town', 'status': 'optimal', 'sensors': 380},
    ]
    
    colors = {
        'optimal': COLORS['accent_green'],
        'nominal': COLORS['accent_blue'],
        'warning': COLORS['accent_yellow'],
        'critical': COLORS['accent_red']
    }
    
    fig = go.Figure()
    
    for loc in locations:
        fig.add_trace(go.Scattermapbox(
            lat=[loc['lat']],
            lon=[loc['lon']],
            mode='markers',
            marker=dict(
                size=max(15, loc['sensors'] / 15),
                color=colors.get(loc['status'], COLORS['accent_blue']),
                opacity=0.8
            ),
            text=f"{loc['name']}<br>{loc['sensors']} sensors<br>Status: {loc['status']}",
            hoverinfo='text',
            name=loc['name']
        ))
    
    fig.update_layout(
        mapbox=dict(
            style='carto-darkmatter',
            center=dict(lat=-22, lon=25),
            zoom=3.5
        ),
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        showlegend=False
    )
    
    return fig


def create_autonomy_gauge(level):
    """Create autonomy level gauge."""
    level_names = [
        'L0 - Manual',
        'L1 - Assisted',
        'L2 - Partial Auto',
        'L3 - Conditional Auto',
        'L4 - High Auto',
        'L5 - Full Auto'
    ]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=level,
        delta={'reference': level - 0.5, 'relative': False},
        gauge={
            'axis': {'range': [0, 5], 'tickwidth': 1, 'tickcolor': COLORS['text_secondary']},
            'bar': {'color': COLORS['accent_blue']},
            'bgcolor': COLORS['card_bg'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, 1], 'color': COLORS['grid']},
                {'range': [1, 2], 'color': '#1a1a2a'},
                {'range': [2, 3], 'color': '#1a2a2a'},
                {'range': [3, 4], 'color': '#1a3a2a'},
                {'range': [4, 5], 'color': '#1a4a2a'}
            ],
            'threshold': {
                'line': {'color': COLORS['accent_green'], 'width': 4},
                'thickness': 0.75,
                'value': level
            }
        },
        title={'text': level_names[level], 'font': {'size': 14, 'color': COLORS['text_secondary']}}
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': COLORS['text_primary'], 'family': FONTS['mono']},
        height=200,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


# =============================================================================
# LAYOUT
# =============================================================================

def create_mission_control_layout():
    """Create the Mission Control layout."""
    status = generate_network_status()
    utilities = generate_utility_data()
    events = generate_live_events()
    
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Span('AQUAWATCH', style={
                    'fontSize': '24px',
                    'fontWeight': '700',
                    'letterSpacing': '2px'
                }),
                html.Span(' MISSION CONTROL', style={
                    'fontSize': '24px',
                    'fontWeight': '300',
                    'letterSpacing': '2px',
                    'color': COLORS['accent_blue']
                })
            ]),
            html.Div([
                html.Span('●', style={'color': COLORS['accent_green'], 'marginRight': '8px'}),
                html.Span('LIVE', style={
                    'fontFamily': FONTS['mono'],
                    'fontSize': '12px',
                    'letterSpacing': '2px',
                    'marginRight': '24px'
                }),
                html.Span(
                    id='mission-clock',
                    style={'fontFamily': FONTS['mono'], 'fontSize': '16px'}
                )
            ])
        ], style=HEADER_STYLE),
        
        # Main content
        html.Div([
            # Top metrics row
            html.Div([
                html.Div([
                    create_metric_card(
                        f"{status['sensors_online']:,}",
                        f"SENSORS ONLINE / {status['total_sensors']:,}",
                        color=COLORS['accent_green']
                    )
                ], style={'flex': '1', 'marginRight': '16px'}),
                
                html.Div([
                    create_metric_card(
                        f"{status['data_points_today']:,}",
                        'DATA POINTS TODAY',
                        color=COLORS['accent_blue']
                    )
                ], style={'flex': '1', 'marginRight': '16px'}),
                
                html.Div([
                    create_metric_card(
                        status['alerts_active'],
                        f"ACTIVE ALERTS ({status['alerts_critical']} CRITICAL)",
                        color=COLORS['accent_yellow'] if status['alerts_critical'] == 0 else COLORS['accent_red']
                    )
                ], style={'flex': '1', 'marginRight': '16px'}),
                
                html.Div([
                    create_metric_card(
                        status['leaks_detected_today'],
                        'LEAKS DETECTED TODAY',
                        color=COLORS['accent_red']
                    )
                ], style={'flex': '1', 'marginRight': '16px'}),
                
                html.Div([
                    create_metric_card(
                        f"{status['water_saved_ytd_m3']:,}",
                        'WATER SAVED YTD (M³)',
                        color=COLORS['accent_green']
                    )
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '16px'}),
            
            # Main content grid
            html.Div([
                # Left column - Main chart and utilities
                html.Div([
                    # Flow chart
                    html.Div([
                        html.Div([
                            html.H3('NETWORK FLOW RATE', style={
                                'margin': '0',
                                'fontSize': '14px',
                                'fontWeight': '500',
                                'letterSpacing': '1px'
                            }),
                            html.Span('24H', style={
                                'fontSize': '11px',
                                'color': COLORS['text_secondary'],
                                'padding': '2px 8px',
                                'border': f"1px solid {COLORS['card_border']}",
                                'borderRadius': '2px'
                            })
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '16px'}),
                        dcc.Graph(
                            figure=create_flow_chart(),
                            config={'displayModeBar': False}
                        )
                    ], style=CARD_STYLE),
                    
                    # Utilities table
                    html.Div([
                        html.H3('CONNECTED UTILITIES', style={
                            'margin': '0 0 16px 0',
                            'fontSize': '14px',
                            'fontWeight': '500',
                            'letterSpacing': '1px'
                        }),
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th('Utility', style={'textAlign': 'left', 'padding': '12px', 'color': COLORS['text_secondary'], 'fontSize': '11px', 'textTransform': 'uppercase'}),
                                    html.Th('Country', style={'textAlign': 'left', 'padding': '12px', 'color': COLORS['text_secondary'], 'fontSize': '11px', 'textTransform': 'uppercase'}),
                                    html.Th('Sensors', style={'textAlign': 'left', 'padding': '12px', 'color': COLORS['text_secondary'], 'fontSize': '11px', 'textTransform': 'uppercase'}),
                                    html.Th('NRW', style={'textAlign': 'left', 'padding': '12px', 'color': COLORS['text_secondary'], 'fontSize': '11px', 'textTransform': 'uppercase'}),
                                    html.Th('Status', style={'textAlign': 'left', 'padding': '12px', 'color': COLORS['text_secondary'], 'fontSize': '11px', 'textTransform': 'uppercase'}),
                                ], style={'borderBottom': f"2px solid {COLORS['card_border']}"})
                            ]),
                            html.Tbody([create_utility_row(u) for u in utilities])
                        ], style={'width': '100%', 'borderCollapse': 'collapse'})
                    ], style=CARD_STYLE),
                ], style={'flex': '2', 'marginRight': '16px'}),
                
                # Right column - Map, Autonomy, Events
                html.Div([
                    # Map
                    html.Div([
                        html.H3('NETWORK MAP', style={
                            'margin': '0 0 16px 0',
                            'fontSize': '14px',
                            'fontWeight': '500',
                            'letterSpacing': '1px'
                        }),
                        dcc.Graph(
                            figure=create_map(),
                            config={'displayModeBar': False}
                        )
                    ], style=CARD_STYLE),
                    
                    # Autonomy gauge and drone status
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H3('AUTONOMY LEVEL', style={
                                    'margin': '0',
                                    'fontSize': '14px',
                                    'fontWeight': '500',
                                    'letterSpacing': '1px'
                                }),
                                dcc.Graph(
                                    figure=create_autonomy_gauge(status['autonomy_level']),
                                    config={'displayModeBar': False}
                                )
                            ], style={'flex': '1'}),
                            
                            html.Div([
                                html.H3('DRONE FLEET', style={
                                    'margin': '0 0 16px 0',
                                    'fontSize': '14px',
                                    'fontWeight': '500',
                                    'letterSpacing': '1px'
                                }),
                                html.Div([
                                    html.Div([
                                        html.Span('🚁', style={'fontSize': '24px', 'marginRight': '12px'}),
                                        html.Div([
                                            html.Div(f"{status['drones_active']} ACTIVE", style={
                                                'fontSize': '20px',
                                                'fontFamily': FONTS['mono'],
                                                'fontWeight': '600'
                                            }),
                                            html.Div('of 6 total', style={
                                                'fontSize': '12px',
                                                'color': COLORS['text_secondary']
                                            })
                                        ])
                                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                                    
                                    html.Div([
                                        html.Div('Scout-1', style={'color': COLORS['accent_green']}),
                                        html.Div('• PATROL', style={'fontSize': '11px', 'color': COLORS['text_secondary']})
                                    ], style={'marginBottom': '8px'}),
                                    html.Div([
                                        html.Div('Scout-2', style={'color': COLORS['accent_blue']}),
                                        html.Div('• RETURNING', style={'fontSize': '11px', 'color': COLORS['text_secondary']})
                                    ], style={'marginBottom': '8px'}),
                                    html.Div([
                                        html.Div('Inspector-1', style={'color': COLORS['accent_green']}),
                                        html.Div('• INVESTIGATING', style={'fontSize': '11px', 'color': COLORS['text_secondary']})
                                    ])
                                ])
                            ], style={'flex': '1', 'marginLeft': '24px'})
                        ], style={'display': 'flex'})
                    ], style=CARD_STYLE),
                    
                    # Live events
                    html.Div([
                        html.H3('LIVE FEED', style={
                            'margin': '0 0 8px 0',
                            'fontSize': '14px',
                            'fontWeight': '500',
                            'letterSpacing': '1px'
                        }),
                        html.Div([
                            create_event_item(event) for event in events
                        ], style={'maxHeight': '300px', 'overflowY': 'auto'})
                    ], style=CARD_STYLE),
                    
                ], style={'flex': '1'})
            ], style={'display': 'flex'})
        ], style={'padding': '16px 24px'}),
        
        # Update interval
        dcc.Interval(
            id='mission-interval',
            interval=1000,  # 1 second
            n_intervals=0
        )
    ], style=GLOBAL_STYLE)


# =============================================================================
# INITIALIZE APP
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='AquaWatch Mission Control'
)

app.layout = create_mission_control_layout()


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('mission-clock', 'children'),
    Input('mission-interval', 'n_intervals')
)
def update_clock(n):
    """Update the mission clock."""
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S UTC')


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AQUAWATCH MISSION CONTROL")
    print("=" * 60)
    print("\nStarting server at http://localhost:8050")
    print("Press Ctrl+C to stop\n")
    
    app.run_server(debug=True, host='0.0.0.0', port=8050)
