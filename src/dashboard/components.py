"""
AquaWatch NRW - Dashboard Components
=====================================

Reusable UI components for the dashboard application.
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, List, Optional
from datetime import datetime


def create_status_badge(status: str) -> dbc.Badge:
    """Create a colored status badge."""
    
    status_map = {
        "healthy": ("✓ Healthy", "success"),
        "warning": ("⚠ Warning", "warning"),
        "critical": ("✗ Critical", "danger"),
        "unknown": ("? Unknown", "secondary"),
        "new": ("New", "info"),
        "acknowledged": ("Acknowledged", "primary"),
        "in_progress": ("In Progress", "warning"),
        "resolved": ("Resolved", "success"),
        "closed": ("Closed", "dark")
    }
    
    text, color = status_map.get(status.lower(), ("?", "secondary"))
    return dbc.Badge(text, color=color)


def create_severity_badge(severity: str) -> dbc.Badge:
    """Create a severity indicator badge."""
    
    severity_map = {
        "critical": ("CRITICAL", "danger"),
        "high": ("HIGH", "warning"),
        "medium": ("MEDIUM", "info"),
        "low": ("LOW", "secondary")
    }
    
    text, color = severity_map.get(severity.lower(), ("?", "secondary"))
    return dbc.Badge(text, color=color, className="px-2")


def create_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = None,
    color: str = "primary",
    trend: Optional[Dict] = None
) -> dbc.Card:
    """
    Create a KPI/metric card.
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Optional subtitle
        icon: Optional icon class (e.g., "fas fa-water")
        color: Bootstrap color class
        trend: Optional dict with 'direction' ('up'/'down') and 'value'
    """
    
    header_content = []
    if icon:
        header_content.append(html.I(className=f"{icon} me-2"))
    header_content.append(title)
    
    body_content = [
        html.H3(value, className=f"text-{color} mb-0")
    ]
    
    if trend:
        trend_icon = "↑" if trend.get('direction') == 'up' else "↓"
        trend_color = "success" if trend.get('positive', True) else "danger"
        body_content.append(
            html.Span(
                f"{trend_icon} {trend.get('value', '')}",
                className=f"text-{trend_color} small ms-2"
            )
        )
    
    if subtitle:
        body_content.append(html.Small(subtitle, className="text-muted d-block mt-1"))
    
    return dbc.Card([
        dbc.CardBody([
            html.H6(header_content, className="text-muted mb-1"),
            html.Div(body_content)
        ])
    ], className="mb-3 shadow-sm")


def create_alert_list_item(alert: Dict, show_actions: bool = True) -> dbc.ListGroupItem:
    """Create a list item for an alert."""
    
    severity_colors = {
        "critical": "danger",
        "high": "warning",
        "medium": "info",
        "low": "secondary"
    }
    
    color = severity_colors.get(alert.get('severity', '').lower(), 'secondary')
    
    content = [
        dbc.Row([
            dbc.Col([
                create_severity_badge(alert.get('severity', 'unknown')),
                html.Span(f" {alert.get('title', 'Alert')}", className="fw-bold")
            ], width=8),
            dbc.Col([
                html.Small(
                    alert.get('timestamp', datetime.now()).strftime("%H:%M") 
                    if isinstance(alert.get('timestamp'), datetime) 
                    else str(alert.get('timestamp', '')),
                    className="text-muted"
                )
            ], width=4, className="text-end")
        ], className="mb-1"),
        
        html.Small([
            html.Span(f"DMA: {alert.get('dma_id', 'Unknown')}", className="me-3"),
            html.Span(f"Probability: {alert.get('probability', 0):.0%}")
        ], className="text-muted")
    ]
    
    if show_actions:
        content.append(
            html.Div([
                dbc.Button("View", size="sm", color="primary", outline=True, className="me-1 mt-2"),
                dbc.Button("Acknowledge", size="sm", color="secondary", outline=True, className="mt-2")
            ])
        )
    
    return dbc.ListGroupItem(content, className="py-2")


def create_work_order_card(work_order: Dict, compact: bool = False) -> dbc.Card:
    """Create a work order card."""
    
    priority_colors = {
        "critical": "danger",
        "high": "warning",
        "normal": "primary",
        "low": "secondary"
    }
    
    color = priority_colors.get(work_order.get('priority', '').lower(), 'primary')
    
    if compact:
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_severity_badge(work_order.get('priority', 'normal')),
                        html.Span(f" {work_order.get('title', 'Work Order')}", className="small fw-bold")
                    ], width=8),
                    dbc.Col([
                        create_status_badge(work_order.get('status', 'new'))
                    ], width=4, className="text-end")
                ]),
                html.Small(work_order.get('location', ''), className="text-muted")
            ], className="py-2")
        ], className="mb-2 shadow-sm")
    
    return dbc.Card([
        dbc.CardHeader([
            dbc.Badge(work_order.get('priority', 'normal').upper(), color=color, className="me-2"),
            html.Span(work_order.get('order_id', 'WO-XXXXX'), className="fw-bold")
        ]),
        dbc.CardBody([
            html.H6(work_order.get('title', 'Work Order'), className="card-title"),
            
            html.Div([
                html.Strong("Location: "),
                html.Span(work_order.get('location', 'Unknown'))
            ], className="small mb-1"),
            
            html.Div([
                html.Strong("DMA: "),
                html.Span(work_order.get('dma_id', 'Unknown'))
            ], className="small mb-1"),
            
            html.Div([
                html.Strong("Status: "),
                create_status_badge(work_order.get('status', 'new'))
            ], className="small mb-2"),
            
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button("Details", color="primary", size="sm", outline=True)
                ], width=6),
                dbc.Col([
                    dbc.Button("Navigate", color="secondary", size="sm", outline=True)
                ], width=6)
            ])
        ])
    ], className="mb-3 shadow-sm")


def create_sensor_status_table(sensors: List[Dict]) -> dbc.Table:
    """Create a table showing sensor status."""
    
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Sensor ID"),
                html.Th("Location"),
                html.Th("Last Reading"),
                html.Th("Status"),
                html.Th("Battery")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(s.get('sensor_id', '')),
                html.Td(s.get('location', '')),
                html.Td(f"{s.get('last_value', 0):.2f} bar"),
                html.Td(create_status_badge(s.get('status', 'unknown'))),
                html.Td([
                    dbc.Progress(
                        value=s.get('battery', 100),
                        color="success" if s.get('battery', 100) > 30 else "danger",
                        style={"width": "60px", "height": "15px"}
                    )
                ])
            ]) for s in sensors
        ])
    ], striped=True, hover=True, responsive=True, size="sm")


def create_confidence_indicator(confidence: float, label: str = "AI Confidence") -> html.Div:
    """Create a confidence level indicator."""
    
    if confidence >= 0.8:
        color = "success"
    elif confidence >= 0.6:
        color = "warning"
    else:
        color = "danger"
    
    return html.Div([
        html.Label(label, className="text-muted small"),
        dbc.Progress(
            value=int(confidence * 100),
            color=color,
            striped=confidence < 0.8,
            className="mb-1",
            style={"height": "20px"}
        ),
        html.Span(f"{confidence:.0%}", className=f"text-{color} small fw-bold")
    ])


def create_network_map_placeholder() -> dbc.Card:
    """Create a placeholder for the network map component."""
    
    return dbc.Card([
        dbc.CardHeader("Network Map"),
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-map-marked-alt fa-3x text-muted"),
                html.P("Interactive network map would load here", className="text-muted mt-2"),
                html.Small("Integration with Leaflet/Mapbox", className="text-muted")
            ], className="text-center py-5")
        ])
    ], className="shadow-sm")


def create_data_quality_indicator(quality_metrics: Dict) -> dbc.Card:
    """Create a data quality indicator panel."""
    
    return dbc.Card([
        dbc.CardHeader("Data Quality"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Sensor Coverage", className="text-muted small"),
                        dbc.Progress(value=quality_metrics.get('sensor_coverage', 0) * 100, 
                                    color="primary", className="mb-1"),
                        html.Span(f"{quality_metrics.get('sensor_coverage', 0):.0%}", 
                                 className="small")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H6("Data Completeness", className="text-muted small"),
                        dbc.Progress(value=quality_metrics.get('completeness', 0) * 100,
                                    color="success", className="mb-1"),
                        html.Span(f"{quality_metrics.get('completeness', 0):.0%}",
                                 className="small")
                    ])
                ], width=6)
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Transmission Rate", className="text-muted small"),
                        dbc.Progress(value=quality_metrics.get('transmission_rate', 0) * 100,
                                    color="info", className="mb-1"),
                        html.Span(f"{quality_metrics.get('transmission_rate', 0):.0%}",
                                 className="small")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H6("Battery Health", className="text-muted small"),
                        dbc.Progress(
                            value=quality_metrics.get('battery_health', 0) * 100,
                            color="success" if quality_metrics.get('battery_health', 0) > 0.5 else "warning",
                            className="mb-1"
                        ),
                        html.Span(f"{quality_metrics.get('battery_health', 0):.0%}",
                                 className="small")
                    ])
                ], width=6)
            ])
        ])
    ], className="shadow-sm")
