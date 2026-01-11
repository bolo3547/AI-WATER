"""
AquaWatch NRW - Secure Dashboard with Login
============================================

Dashboard with authentication:
- Login page with username/password
- Role-based access (Admin, Operator, Technician)
- Session management
- Three dashboard tiers

Default Users:
- admin / admin123 (Full access)
- operator / operator123 (Operations view)
- technician / tech123 (Field view)
"""

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import secrets
import os

# =============================================================================
# DEFAULT USERS - Change these in production!
# =============================================================================

DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "System Administrator",
        "role": "admin",
        "email": "admin@aquawatch.zm",
        "access": ["national", "operations", "field", "settings"]
    },
    "operator": {
        "password_hash": hashlib.sha256("operator123".encode()).hexdigest(),
        "name": "Control Room Operator",
        "role": "operator",
        "email": "operator@aquawatch.zm",
        "access": ["operations", "field"]
    },
    "technician": {
        "password_hash": hashlib.sha256("tech123".encode()).hexdigest(),
        "name": "Field Technician",
        "role": "technician",
        "email": "tech@aquawatch.zm",
        "access": ["field"]
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "name": "Demo User",
        "role": "viewer",
        "email": "demo@aquawatch.zm",
        "access": ["national", "operations", "field"]
    }
}

# Session storage (in-memory for demo, use Redis in production)
active_sessions = {}


def verify_password(username: str, password: str) -> Optional[Dict]:
    """Verify username and password, return user info if valid."""
    if username not in DEFAULT_USERS:
        return None
    
    user = DEFAULT_USERS[username]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash == user["password_hash"]:
        return {
            "username": username,
            "name": user["name"],
            "role": user["role"],
            "access": user["access"]
        }
    return None


def create_session(user_info: Dict) -> str:
    """Create a session token for authenticated user."""
    token = secrets.token_urlsafe(32)
    active_sessions[token] = {
        **user_info,
        "created": datetime.now(),
        "expires": datetime.now() + timedelta(hours=8)
    }
    return token


def get_session(token: str) -> Optional[Dict]:
    """Get session info from token."""
    if not token or token not in active_sessions:
        return None
    
    session = active_sessions[token]
    if datetime.now() > session["expires"]:
        del active_sessions[token]
        return None
    
    return session


# =============================================================================
# Initialize Dash App
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

server = app.server
app.title = "AquaWatch NRW - Login"


# =============================================================================
# STYLES
# =============================================================================

COLORS = {
    "primary": "#0d6efd",
    "success": "#198754",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "dark": "#212529",
    "light": "#f8f9fa",
    "water_blue": "#0077be",
    "water_dark": "#004d80"
}

LOGIN_STYLE = {
    "background": "linear-gradient(135deg, #0077be 0%, #004d80 100%)",
    "minHeight": "100vh",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center"
}


# =============================================================================
# LOGIN PAGE
# =============================================================================

def create_login_page():
    """Create the login page layout."""
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            # Logo and Title
                            html.Div([
                                html.I(className="fas fa-water fa-3x mb-3", 
                                      style={"color": COLORS["water_blue"]}),
                                html.H2("AquaWatch NRW", className="mb-1"),
                                html.P("Water Intelligence Platform", 
                                      className="text-muted mb-4"),
                            ], className="text-center"),
                            
                            # Login Form
                            html.Div([
                                dbc.Label("Username", className="fw-bold"),
                                dbc.Input(
                                    id="login-username",
                                    type="text",
                                    placeholder="Enter username",
                                    className="mb-3"
                                ),
                                
                                dbc.Label("Password", className="fw-bold"),
                                dbc.Input(
                                    id="login-password",
                                    type="password",
                                    placeholder="Enter password",
                                    className="mb-3"
                                ),
                                
                                # Error message
                                html.Div(id="login-error", className="mb-3"),
                                
                                dbc.Button(
                                    [html.I(className="fas fa-sign-in-alt me-2"), "Login"],
                                    id="login-button",
                                    color="primary",
                                    className="w-100 mb-3",
                                    size="lg"
                                ),
                            ]),
                            
                            html.Hr(),
                            
                            # Default credentials hint
                            dbc.Alert([
                                html.Strong("Demo Credentials:"),
                                html.Br(),
                                html.Code("admin / admin123"), " - Full access",
                                html.Br(),
                                html.Code("operator / operator123"), " - Operations",
                                html.Br(),
                                html.Code("technician / tech123"), " - Field only",
                                html.Br(),
                                html.Code("demo / demo"), " - View only",
                            ], color="info", className="mb-0 small"),
                            
                        ])
                    ], className="shadow-lg", style={"maxWidth": "400px", "margin": "auto"})
                ], width=12, md=6, lg=4)
            ], justify="center")
        ], fluid=True)
    ], style=LOGIN_STYLE)


# =============================================================================
# MAIN DASHBOARD LAYOUT
# =============================================================================

def create_navbar(user_info: Dict):
    """Create the navigation bar with user info."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.A([
                        html.I(className="fas fa-water me-2"),
                        html.Span("AquaWatch NRW", className="fw-bold")
                    ], href="/dashboard", className="navbar-brand text-white")
                ]),
            ], align="center"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink(
                            [html.I(className="fas fa-globe me-1"), "National"],
                            href="/dashboard/national",
                            id="nav-national",
                            className="text-white"
                        )) if "national" in user_info.get("access", []) else None,
                        
                        dbc.NavItem(dbc.NavLink(
                            [html.I(className="fas fa-cogs me-1"), "Operations"],
                            href="/dashboard/operations",
                            id="nav-operations",
                            className="text-white"
                        )) if "operations" in user_info.get("access", []) else None,
                        
                        dbc.NavItem(dbc.NavLink(
                            [html.I(className="fas fa-wrench me-1"), "Field"],
                            href="/dashboard/field",
                            id="nav-field",
                            className="text-white"
                        )) if "field" in user_info.get("access", []) else None,
                    ], navbar=True)
                ])
            ], align="center"),
            
            dbc.Row([
                dbc.Col([
                    dbc.DropdownMenu([
                        dbc.DropdownMenuItem([
                            html.I(className="fas fa-user me-2"),
                            user_info.get("name", "User")
                        ], header=True),
                        dbc.DropdownMenuItem(f"Role: {user_info.get('role', 'Unknown').title()}"),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem(
                            [html.I(className="fas fa-sign-out-alt me-2"), "Logout"],
                            id="logout-button",
                            href="/"
                        ),
                    ],
                    label=html.I(className="fas fa-user-circle fa-lg"),
                    nav=True,
                    in_navbar=True,
                    className="text-white"
                    )
                ])
            ], align="center")
        ], fluid=True),
        color=COLORS["water_dark"],
        dark=True,
        sticky="top"
    )


def create_dashboard_content(view: str, user_info: Dict):
    """Create dashboard content based on view and user access."""
    
    # Check access
    if view not in user_info.get("access", []):
        return dbc.Container([
            dbc.Alert([
                html.I(className="fas fa-lock me-2"),
                f"Access Denied: You don't have permission to view the {view.title()} dashboard."
            ], color="danger", className="mt-4")
        ])
    
    if view == "national":
        return create_national_view()
    elif view == "operations":
        return create_operations_view()
    elif view == "field":
        return create_field_view()
    else:
        return create_national_view()


def create_national_view():
    """National/Ministry level strategic view."""
    
    # Sample data
    dma_data = pd.DataFrame([
        {"dma": "Kitwe Central", "nrw": 28.5, "status": "warning"},
        {"dma": "Kitwe North", "nrw": 22.1, "status": "healthy"},
        {"dma": "Kitwe South", "nrw": 45.2, "status": "critical"},
        {"dma": "Ndola East", "nrw": 31.8, "status": "warning"},
        {"dma": "Lusaka CBD", "nrw": 38.9, "status": "critical"},
    ])
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-globe me-2"), "National Overview"], className="mt-4 mb-4"),
        
        # KPI Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("National NRW Rate", className="text-muted"),
                        html.H2("34.2%", className="text-warning"),
                        html.Small("↓ 2.1% from last month", className="text-success")
                    ])
                ], className="shadow-sm h-100")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Active Sensors", className="text-muted"),
                        html.H2("247", className="text-primary"),
                        html.Small("98.4% online", className="text-success")
                    ])
                ], className="shadow-sm h-100")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Active Alerts", className="text-muted"),
                        html.H2("12", className="text-danger"),
                        html.Small("3 critical", className="text-danger")
                    ])
                ], className="shadow-sm h-100")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Water Saved (YTD)", className="text-muted"),
                        html.H2("2.4M m³", className="text-success"),
                        html.Small("$1.2M revenue recovered", className="text-success")
                    ])
                ], className="shadow-sm h-100")
            ], md=3),
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("NRW by District"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=px.bar(
                                dma_data, x="dma", y="nrw",
                                color="status",
                                color_discrete_map={"healthy": "green", "warning": "orange", "critical": "red"},
                                title=""
                            ).update_layout(showlegend=False, height=300)
                        )
                    ])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("System Health"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=87,
                                title={"text": "Overall System Score"},
                                gauge={
                                    "axis": {"range": [0, 100]},
                                    "bar": {"color": "green"},
                                    "steps": [
                                        {"range": [0, 50], "color": "red"},
                                        {"range": [50, 75], "color": "orange"},
                                        {"range": [75, 100], "color": "lightgreen"}
                                    ]
                                }
                            )).update_layout(height=300)
                        )
                    ])
                ], className="shadow-sm")
            ], md=6),
        ])
    ], fluid=True)


def create_operations_view():
    """Operations/Control Room view."""
    
    # Generate time series data
    times = pd.date_range(end=datetime.now(), periods=100, freq="5min")
    pressure_data = pd.DataFrame({
        "time": times,
        "pressure": 3.0 + np.random.normal(0, 0.15, 100),
        "threshold_high": [3.5] * 100,
        "threshold_low": [2.5] * 100
    })
    
    # Simulate a leak event
    pressure_data.loc[70:80, "pressure"] = pressure_data.loc[70:80, "pressure"] - 0.8
    
    alerts = [
        {"id": "ALT-001", "pipe": "PIPE-KIT-042", "type": "Pressure Drop", "severity": "High", "time": "2 min ago"},
        {"id": "ALT-002", "pipe": "PIPE-NDL-018", "type": "Flow Anomaly", "severity": "Medium", "time": "15 min ago"},
        {"id": "ALT-003", "pipe": "PIPE-KIT-089", "type": "Sensor Offline", "severity": "Low", "time": "1 hour ago"},
    ]
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-cogs me-2"), "Operations Control"], className="mt-4 mb-4"),
        
        dbc.Row([
            # Live alerts panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bell me-2 text-danger"),
                        "Live Alerts"
                    ], className="bg-dark text-white"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                dbc.Row([
                                    dbc.Col([
                                        html.Strong(a["id"]),
                                        html.Br(),
                                        html.Small(a["pipe"], className="text-muted")
                                    ], width=4),
                                    dbc.Col([
                                        dbc.Badge(a["severity"], 
                                                 color="danger" if a["severity"]=="High" else "warning" if a["severity"]=="Medium" else "secondary"),
                                        html.Br(),
                                        html.Small(a["type"])
                                    ], width=4),
                                    dbc.Col([
                                        html.Small(a["time"], className="text-muted"),
                                        html.Br(),
                                        dbc.Button("View", size="sm", color="primary", className="mt-1")
                                    ], width=4, className="text-end")
                                ])
                            ], className="py-2") for a in alerts
                        ], flush=True)
                    ])
                ], className="shadow-sm h-100")
            ], md=4),
            
            # Pressure chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Real-Time Pressure Monitoring"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=go.Figure([
                                go.Scatter(x=pressure_data["time"], y=pressure_data["pressure"],
                                          mode="lines", name="Pressure", line={"color": "blue"}),
                                go.Scatter(x=pressure_data["time"], y=pressure_data["threshold_high"],
                                          mode="lines", name="High Threshold", line={"color": "red", "dash": "dash"}),
                                go.Scatter(x=pressure_data["time"], y=pressure_data["threshold_low"],
                                          mode="lines", name="Low Threshold", line={"color": "orange", "dash": "dash"}),
                            ]).update_layout(
                                height=350,
                                margin={"l": 40, "r": 20, "t": 20, "b": 40},
                                legend={"orientation": "h", "y": -0.15},
                                yaxis_title="Pressure (bar)",
                                xaxis_title=""
                            )
                        )
                    ])
                ], className="shadow-sm")
            ], md=8),
        ], className="mb-4"),
        
        # Sensor status grid
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sensor Network Status"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className=f"fas fa-circle {'text-success' if i % 7 != 0 else 'text-danger'} me-1"),
                                    f"S-{i:03d}"
                                ], className="small mb-1")
                            ], width=2) for i in range(1, 25)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ])
    ], fluid=True)


def create_field_view():
    """Field Technician mobile-optimized view."""
    
    work_orders = [
        {"id": "WO-2026-001", "location": "Kitwe Central, Main St", "type": "Leak Repair", "priority": "High", "status": "In Progress"},
        {"id": "WO-2026-002", "location": "Ndola East, Market Rd", "type": "Sensor Install", "priority": "Medium", "status": "Pending"},
        {"id": "WO-2026-003", "location": "Kitwe South, Industrial", "type": "Valve Check", "priority": "Low", "status": "Pending"},
    ]
    
    return dbc.Container([
        html.H3([html.I(className="fas fa-wrench me-2"), "Field Operations"], className="mt-4 mb-4"),
        
        # Quick stats for technician
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("3", className="text-primary mb-0"),
                        html.Small("Assigned Tasks")
                    ], className="text-center")
                ], className="shadow-sm")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("1", className="text-warning mb-0"),
                        html.Small("In Progress")
                    ], className="text-center")
                ], className="shadow-sm")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("12", className="text-success mb-0"),
                        html.Small("Completed (MTD)")
                    ], className="text-center")
                ], className="shadow-sm")
            ], width=4),
        ], className="mb-4"),
        
        # Work orders list
        html.H5("My Work Orders", className="mb-3"),
        
        *[dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5(wo["id"], className="mb-1"),
                        html.P([
                            html.I(className="fas fa-map-marker-alt me-2"),
                            wo["location"]
                        ], className="text-muted mb-1"),
                        html.P([
                            html.I(className="fas fa-tools me-2"),
                            wo["type"]
                        ], className="mb-0"),
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(wo["priority"], 
                                 color="danger" if wo["priority"]=="High" else "warning" if wo["priority"]=="Medium" else "secondary",
                                 className="mb-2"),
                        html.Br(),
                        dbc.Badge(wo["status"], 
                                 color="primary" if wo["status"]=="In Progress" else "secondary"),
                        html.Br(),
                        dbc.Button([
                            html.I(className="fas fa-arrow-right me-1"),
                            "Open"
                        ], color="primary", size="sm", className="mt-2")
                    ], md=4, className="text-end")
                ])
            ])
        ], className="shadow-sm mb-3") for wo in work_orders],
        
        # Quick action buttons
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-camera me-2"),
                    "Take Photo"
                ], color="secondary", className="w-100 mb-2")
            ], width=6),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-microphone me-2"),
                    "Voice Note"
                ], color="secondary", className="w-100 mb-2")
            ], width=6),
        ])
    ], fluid=True, className="pb-5")


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="page-content")
])


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("page-content", "children"),
    Output("session-store", "data"),
    Input("url", "pathname"),
    State("session-store", "data"),
    prevent_initial_call=False
)
def display_page(pathname, session_data):
    """Route to appropriate page based on authentication state."""
    
    # Check if user has valid session
    user_info = None
    if session_data:
        user_info = get_session(session_data.get("token"))
    
    # Login page
    if pathname == "/" or pathname == "/login":
        return create_login_page(), session_data
    
    # Dashboard pages require authentication
    if pathname and pathname.startswith("/dashboard"):
        if not user_info:
            return create_login_page(), None
        
        # Determine which view
        view = "national"  # default
        if "/operations" in pathname:
            view = "operations"
        elif "/field" in pathname:
            view = "field"
        
        return html.Div([
            create_navbar(user_info),
            create_dashboard_content(view, user_info)
        ]), session_data
    
    # Default to login
    return create_login_page(), session_data


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Output("login-error", "children"),
    Input("login-button", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    """Handle login form submission."""
    if not n_clicks:
        return no_update, no_update, no_update
    
    if not username or not password:
        return no_update, no_update, dbc.Alert(
            "Please enter username and password", 
            color="warning"
        )
    
    # Verify credentials
    user_info = verify_password(username, password)
    
    if user_info:
        # Create session
        token = create_session(user_info)
        session_data = {"token": token, **user_info}
        
        # Redirect based on role
        if "national" in user_info["access"]:
            return "/dashboard/national", session_data, None
        elif "operations" in user_info["access"]:
            return "/dashboard/operations", session_data, None
        else:
            return "/dashboard/field", session_data, None
    else:
        return no_update, no_update, dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"),
             "Invalid username or password"],
            color="danger"
        )


# =============================================================================
# RUN SERVER
# =============================================================================

def run_dashboard(debug: bool = True, port: int = 8050):
    """Start the secure dashboard server."""
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║           AquaWatch NRW - Secure Dashboard                   ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  🌐 Open: http://localhost:{port}                             ║
    ║                                                              ║
    ║  ┌────────────────────────────────────────────────────────┐  ║
    ║  │  DEFAULT LOGIN CREDENTIALS                             │  ║
    ║  ├────────────────────────────────────────────────────────┤  ║
    ║  │  admin / admin123       → Full access (all views)      │  ║
    ║  │  operator / operator123 → Operations + Field           │  ║
    ║  │  technician / tech123   → Field only                   │  ║
    ║  │  demo / demo            → View only (all views)        │  ║
    ║  └────────────────────────────────────────────────────────┘  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=debug, port=port, host="0.0.0.0")


if __name__ == '__main__':
    run_dashboard()
