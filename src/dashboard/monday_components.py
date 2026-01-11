"""
AquaWatch NRW - Monday.com Style UI Components
===============================================

Reusable components for the Monday.com inspired dashboard
- Kanban boards
- Timeline views
- Status columns
- Pulse updates
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# =============================================================================
# COLOR PALETTE
# =============================================================================

COLORS = {
    # Status colors
    "critical": "#E2445C",
    "high": "#FDAB3D", 
    "medium": "#579BFC",
    "low": "#00C875",
    "done": "#00C875",
    "stuck": "#E2445C",
    "working": "#FDAB3D",
    
    # UI
    "primary": "#0073EA",
    "bg": "#F6F7FB",
    "surface": "#FFFFFF",
    "text": "#323338",
    "text_secondary": "#676879",
    "border": "#E6E9EF",
    
    # NRW Categories
    "real_loss": "#E2445C",
    "apparent_loss": "#A25DDC",
    "unknown": "#C4C4C4",
}


# =============================================================================
# KANBAN BOARD COMPONENTS
# =============================================================================

def create_kanban_card(item: Dict) -> html.Div:
    """Create a Monday.com style Kanban card."""
    
    status_color = COLORS.get(item.get("status", "medium"), COLORS["medium"])
    category = item.get("category", "Unknown")
    category_color = COLORS["real_loss"] if "Real" in category else \
                    COLORS["apparent_loss"] if "Apparent" in category else COLORS["unknown"]
    
    return html.Div([
        # Top color bar
        html.Div(style={
            "height": "4px",
            "backgroundColor": status_color,
            "borderRadius": "8px 8px 0 0"
        }),
        
        # Content
        html.Div([
            # Title
            html.Div(item.get("title", "Untitled"), style={
                "fontWeight": "500",
                "fontSize": "14px",
                "marginBottom": "8px",
                "color": COLORS["text"]
            }),
            
            # ID and DMA
            html.Div([
                html.Span(item.get("id", ""), style={
                    "fontSize": "11px",
                    "color": COLORS["text_secondary"]
                }),
                html.Span(" • ", style={"color": COLORS["border"]}),
                html.Span(item.get("dma", ""), style={
                    "fontSize": "11px",
                    "color": COLORS["text_secondary"]
                })
            ], style={"marginBottom": "12px"}),
            
            # Category badge
            html.Div([
                html.Span(category, style={
                    "backgroundColor": category_color,
                    "color": "white",
                    "padding": "3px 8px",
                    "borderRadius": "4px",
                    "fontSize": "10px",
                    "fontWeight": "500"
                })
            ], style={"marginBottom": "12px"}),
            
            # Probability bar
            html.Div([
                html.Div([
                    html.Div(style={
                        "width": f"{item.get('probability', 0.5) * 100}%",
                        "height": "100%",
                        "backgroundColor": status_color,
                        "borderRadius": "3px"
                    })
                ], style={
                    "height": "6px",
                    "backgroundColor": COLORS["border"],
                    "borderRadius": "3px",
                    "flex": "1"
                }),
                html.Span(f"{item.get('probability', 0.5):.0%}", style={
                    "fontSize": "11px",
                    "marginLeft": "8px",
                    "color": COLORS["text_secondary"]
                })
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),
            
            # Footer with assignee and loss
            html.Div([
                # Assignee avatar
                html.Div([
                    html.Div(
                        item.get("assigned", "?")[0] if item.get("assigned", "—") != "—" else "?",
                        style={
                            "width": "24px",
                            "height": "24px",
                            "borderRadius": "50%",
                            "backgroundColor": COLORS["primary"] if item.get("assigned", "—") != "—" else COLORS["border"],
                            "color": "white" if item.get("assigned", "—") != "—" else COLORS["text_secondary"],
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontSize": "11px",
                            "fontWeight": "500"
                        }
                    )
                ]),
                
                # Loss estimate
                html.Div([
                    html.I(className="fas fa-tint", style={
                        "color": COLORS["text_secondary"],
                        "marginRight": "4px",
                        "fontSize": "10px"
                    }),
                    html.Span(f"{item.get('loss_m3_day', 0):.0f} m³/d", style={
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"]
                    })
                ], style={"display": "flex", "alignItems": "center"}),
                
                # Night detection badge
                html.Div([
                    html.I(className="fas fa-moon", style={"fontSize": "10px"})
                ], style={
                    "backgroundColor": "#292F4C",
                    "color": "white",
                    "padding": "4px 6px",
                    "borderRadius": "4px",
                    "display": "flex" if item.get("night_detection") else "none"
                })
                
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center"
            })
            
        ], style={"padding": "12px"})
        
    ], style={
        "backgroundColor": "white",
        "borderRadius": "8px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.1)",
        "marginBottom": "12px",
        "transition": "transform 0.2s, box-shadow 0.2s",
        "cursor": "pointer"
    })


def create_kanban_column(title: str, items: List[Dict], color: str, count: int = None) -> html.Div:
    """Create a Monday.com style Kanban column."""
    
    if count is None:
        count = len(items)
    
    return html.Div([
        # Column header
        html.Div([
            html.Div(style={
                "width": "4px",
                "height": "16px",
                "backgroundColor": color,
                "borderRadius": "2px"
            }),
            html.Span(title, style={
                "fontWeight": "600",
                "fontSize": "14px",
                "color": COLORS["text"]
            }),
            html.Span(str(count), style={
                "backgroundColor": COLORS["bg"],
                "padding": "2px 8px",
                "borderRadius": "10px",
                "fontSize": "12px",
                "color": COLORS["text_secondary"]
            })
        ], style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "marginBottom": "16px"
        }),
        
        # Cards container
        html.Div([
            create_kanban_card(item) for item in items
        ], style={
            "minHeight": "200px",
            "maxHeight": "calc(100vh - 300px)",
            "overflowY": "auto",
            "paddingRight": "4px"
        })
        
    ], style={
        "backgroundColor": COLORS["bg"],
        "borderRadius": "8px",
        "padding": "16px",
        "minWidth": "280px",
        "maxWidth": "280px"
    })


def create_kanban_board(items: List[Dict]) -> html.Div:
    """Create a full Monday.com style Kanban board."""
    
    # Group items by status
    columns = {
        "Critical": {"color": COLORS["critical"], "items": []},
        "High Priority": {"color": COLORS["high"], "items": []},
        "In Progress": {"color": COLORS["medium"], "items": []},
        "Monitoring": {"color": COLORS["low"], "items": []},
    }
    
    status_mapping = {
        "critical": "Critical",
        "high": "High Priority",
        "medium": "In Progress",
        "low": "Monitoring"
    }
    
    for item in items:
        col_name = status_mapping.get(item.get("status", "medium"), "In Progress")
        columns[col_name]["items"].append(item)
    
    return html.Div([
        # Board header
        html.Div([
            html.Div([
                html.H3("NRW Detection Board", style={
                    "fontWeight": "600",
                    "margin": 0,
                    "color": COLORS["text"]
                }),
                html.Span("Kanban View", style={
                    "fontSize": "12px",
                    "color": COLORS["text_secondary"],
                    "marginLeft": "12px"
                })
            ], style={"display": "flex", "alignItems": "center"}),
            
            # View toggle
            html.Div([
                html.Button([
                    html.I(className="fas fa-th-list", style={"marginRight": "6px"}),
                    "Table"
                ], style={
                    "padding": "8px 12px",
                    "border": "none",
                    "background": "none",
                    "color": COLORS["text_secondary"],
                    "cursor": "pointer"
                }),
                html.Button([
                    html.I(className="fas fa-columns", style={"marginRight": "6px"}),
                    "Kanban"
                ], style={
                    "padding": "8px 12px",
                    "border": "none",
                    "background": COLORS["primary"],
                    "color": "white",
                    "borderRadius": "6px",
                    "cursor": "pointer"
                }),
            ], style={"display": "flex", "gap": "4px"})
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginBottom": "24px",
            "padding": "20px",
            "backgroundColor": "white",
            "borderRadius": "8px 8px 0 0",
            "borderBottom": f"1px solid {COLORS['border']}"
        }),
        
        # Columns container
        html.Div([
            create_kanban_column(name, data["items"], data["color"])
            for name, data in columns.items()
        ], style={
            "display": "flex",
            "gap": "16px",
            "padding": "20px",
            "backgroundColor": "white",
            "borderRadius": "0 0 8px 8px",
            "overflowX": "auto"
        })
        
    ], style={
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "borderRadius": "8px"
    })


# =============================================================================
# TIMELINE VIEW COMPONENTS
# =============================================================================

def create_timeline_item(item: Dict, start_offset: int = 0) -> html.Div:
    """Create a timeline bar item."""
    
    status_color = COLORS.get(item.get("status", "medium"), COLORS["medium"])
    
    # Calculate width based on severity (more urgent = longer bar for visibility)
    width_pct = {"critical": 80, "high": 60, "medium": 40, "low": 20}.get(item.get("status"), 40)
    
    return html.Div([
        # Label
        html.Div([
            html.Span(item.get("title", "")[:30] + "..." if len(item.get("title", "")) > 30 else item.get("title", ""), style={
                "fontWeight": "500",
                "fontSize": "13px"
            }),
            html.Span(item.get("dma", ""), style={
                "fontSize": "11px",
                "color": COLORS["text_secondary"],
                "marginLeft": "8px"
            })
        ], style={"width": "200px", "flexShrink": 0}),
        
        # Timeline bar area
        html.Div([
            html.Div(style={
                "position": "absolute",
                "left": f"{start_offset}%",
                "width": f"{width_pct}%",
                "height": "24px",
                "backgroundColor": status_color,
                "borderRadius": "4px",
                "display": "flex",
                "alignItems": "center",
                "paddingLeft": "8px",
                "color": "white",
                "fontSize": "11px"
            }, children=[
                f"{item.get('probability', 0.5):.0%}"
            ])
        ], style={
            "flex": 1,
            "height": "32px",
            "backgroundColor": COLORS["bg"],
            "borderRadius": "4px",
            "position": "relative"
        })
        
    ], style={
        "display": "flex",
        "alignItems": "center",
        "gap": "16px",
        "padding": "8px 16px",
        "borderBottom": f"1px solid {COLORS['border']}"
    })


def create_timeline_view(items: List[Dict]) -> html.Div:
    """Create Monday.com style timeline/Gantt view."""
    
    # Time header
    now = datetime.now()
    time_slots = [(now + timedelta(hours=i*4)).strftime("%H:%M") for i in range(7)]
    
    return html.Div([
        # Header
        html.Div([
            html.H3("NRW Timeline", style={
                "fontWeight": "600",
                "margin": 0,
                "color": COLORS["text"]
            }),
        ], style={
            "padding": "20px",
            "borderBottom": f"1px solid {COLORS['border']}"
        }),
        
        # Time axis
        html.Div([
            html.Div(style={"width": "200px", "flexShrink": 0}),
            html.Div([
                html.Div([
                    html.Span(slot, style={
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"]
                    })
                ], style={"flex": 1, "textAlign": "center"})
                for slot in time_slots
            ], style={"display": "flex", "flex": 1})
        ], style={
            "display": "flex",
            "padding": "12px 16px",
            "borderBottom": f"1px solid {COLORS['border']}",
            "backgroundColor": COLORS["bg"]
        }),
        
        # Items
        html.Div([
            create_timeline_item(item, i * 5 % 40) 
            for i, item in enumerate(items)
        ])
        
    ], style={
        "backgroundColor": "white",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)"
    })


# =============================================================================
# PULSE/ACTIVITY FEED COMPONENT
# =============================================================================

def create_pulse_item(activity: Dict) -> html.Div:
    """Create a Monday.com style pulse/activity item."""
    
    return html.Div([
        # Avatar
        html.Div(
            activity.get("user", "S")[0],
            style={
                "width": "32px",
                "height": "32px",
                "borderRadius": "50%",
                "backgroundColor": COLORS["primary"],
                "color": "white",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "fontSize": "14px",
                "fontWeight": "500",
                "flexShrink": 0
            }
        ),
        
        # Content
        html.Div([
            html.Div([
                html.Span(activity.get("user", "System"), style={
                    "fontWeight": "500",
                    "color": COLORS["text"]
                }),
                html.Span(f" {activity.get('action', '')}", style={
                    "color": COLORS["text_secondary"]
                })
            ], style={"fontSize": "13px"}),
            
            html.Div(activity.get("item", ""), style={
                "fontSize": "12px",
                "color": COLORS["primary"],
                "marginTop": "2px"
            }),
            
            html.Div(activity.get("time", ""), style={
                "fontSize": "11px",
                "color": COLORS["text_secondary"],
                "marginTop": "4px"
            })
        ], style={"flex": 1})
        
    ], style={
        "display": "flex",
        "gap": "12px",
        "padding": "12px 16px",
        "borderBottom": f"1px solid {COLORS['border']}",
        "transition": "background 0.2s"
    })


def create_pulse_feed(activities: List[Dict] = None) -> html.Div:
    """Create Monday.com style activity/pulse feed."""
    
    if activities is None:
        activities = [
            {"user": "System", "action": "detected new anomaly in", "item": "DMA-KIT-003", "time": "2 minutes ago"},
            {"user": "John M.", "action": "acknowledged alert", "item": "NRW-2026-00142", "time": "15 minutes ago"},
            {"user": "Sarah K.", "action": "created work order for", "item": "NRW-2026-00138", "time": "1 hour ago"},
            {"user": "AI Model", "action": "updated probability for", "item": "NRW-2026-00135", "time": "2 hours ago"},
            {"user": "Peter N.", "action": "completed investigation", "item": "NRW-2026-00128", "time": "3 hours ago"},
        ]
    
    return html.Div([
        # Header
        html.Div([
            html.Span("📊 Activity Feed", style={
                "fontWeight": "600",
                "fontSize": "14px",
                "color": COLORS["text"]
            }),
            html.Span("Live", style={
                "backgroundColor": COLORS["low"],
                "color": "white",
                "padding": "2px 8px",
                "borderRadius": "10px",
                "fontSize": "10px",
                "marginLeft": "8px"
            })
        ], style={
            "padding": "16px",
            "borderBottom": f"1px solid {COLORS['border']}"
        }),
        
        # Activity items
        html.Div([
            create_pulse_item(activity) for activity in activities
        ], style={
            "maxHeight": "400px",
            "overflowY": "auto"
        })
        
    ], style={
        "backgroundColor": "white",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)"
    })


# =============================================================================
# WIDGET COMPONENTS
# =============================================================================

def create_battery_widget(label: str, value: float, max_value: float = 100, 
                         color: str = None) -> html.Div:
    """Create a Monday.com style battery/progress widget."""
    
    pct = (value / max_value) * 100
    if color is None:
        color = COLORS["critical"] if pct > 80 else \
               COLORS["high"] if pct > 60 else \
               COLORS["medium"] if pct > 40 else COLORS["low"]
    
    return html.Div([
        html.Div(label, style={
            "fontSize": "12px",
            "color": COLORS["text_secondary"],
            "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                html.Div(style={
                    "width": f"{pct}%",
                    "height": "100%",
                    "backgroundColor": color,
                    "borderRadius": "4px",
                    "transition": "width 0.5s ease"
                })
            ], style={
                "height": "8px",
                "backgroundColor": COLORS["border"],
                "borderRadius": "4px",
                "flex": 1
            }),
            html.Span(f"{value:.0f}%", style={
                "fontSize": "14px",
                "fontWeight": "500",
                "marginLeft": "12px",
                "color": color
            })
        ], style={"display": "flex", "alignItems": "center"})
    ], style={
        "backgroundColor": "white",
        "padding": "16px",
        "borderRadius": "8px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"
    })


def create_number_widget(label: str, value: str, subtitle: str = "",
                        color: str = COLORS["primary"]) -> html.Div:
    """Create a Monday.com style number widget."""
    
    return html.Div([
        html.Div(label, style={
            "fontSize": "11px",
            "color": COLORS["text_secondary"],
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "marginBottom": "8px"
        }),
        html.Div(value, style={
            "fontSize": "28px",
            "fontWeight": "600",
            "color": color,
            "lineHeight": "1"
        }),
        html.Div(subtitle, style={
            "fontSize": "12px",
            "color": COLORS["text_secondary"],
            "marginTop": "8px"
        }) if subtitle else None
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "8px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
        "borderLeft": f"4px solid {color}"
    })
