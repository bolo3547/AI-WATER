"""
AquaWatch Mobile App - Field Technician Dashboard
=================================================
Mobile-optimized Progressive Web App (PWA) for field technicians.
Features:
- Work order management
- Offline support with sync
- GPS navigation to leak locations
- Photo capture for documentation
- Real-time alerts
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import json
import os

# Initialize mobile app
mobile_app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    title="AquaWatch Field",
    update_title=None,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "black-translucent"},
        {"name": "theme-color", "content": "#0ea5e9"},
    ]
)

# =============================================================================
# MOBILE STYLES
# =============================================================================

MOBILE_STYLES = """
/* Mobile-First Design */
* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #f0f4f8;
    margin: 0;
    padding: 0;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
}

/* App Container */
.mobile-app {
    max-width: 480px;
    margin: 0 auto;
    min-height: 100vh;
    background: #f0f4f8;
    position: relative;
    padding-bottom: 80px;
}

/* Header */
.mobile-header {
    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    color: white;
    padding: 20px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(14, 165, 233, 0.3);
}

.mobile-header h1 {
    font-size: 20px;
    font-weight: 700;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.mobile-header .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    font-size: 13px;
    opacity: 0.9;
}

/* Stats Cards */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    padding: 16px;
    margin-top: -30px;
}

.stat-card {
    background: white;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.stat-card .number {
    font-size: 28px;
    font-weight: 700;
    color: #0ea5e9;
}

.stat-card .label {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}

.stat-card.urgent .number { color: #ef4444; }
.stat-card.warning .number { color: #f59e0b; }
.stat-card.success .number { color: #22c55e; }

/* Section */
.section {
    padding: 0 16px 16px;
}

.section-title {
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Work Order Cards */
.order-card {
    background: white;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    border-left: 4px solid #0ea5e9;
    transition: transform 0.2s, box-shadow 0.2s;
}

.order-card:active {
    transform: scale(0.98);
}

.order-card.critical {
    border-left-color: #ef4444;
    background: linear-gradient(to right, #fef2f2, white);
}

.order-card.high {
    border-left-color: #f59e0b;
    background: linear-gradient(to right, #fffbeb, white);
}

.order-card .order-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.order-card .order-id {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

.order-card .priority-badge {
    font-size: 10px;
    padding: 4px 8px;
    border-radius: 20px;
    font-weight: 600;
    text-transform: uppercase;
}

.priority-badge.critical {
    background: #fef2f2;
    color: #ef4444;
}

.priority-badge.high {
    background: #fffbeb;
    color: #f59e0b;
}

.priority-badge.medium {
    background: #f0f9ff;
    color: #0ea5e9;
}

.order-card .order-title {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 8px;
}

.order-card .order-location {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #64748b;
    margin-bottom: 12px;
}

.order-card .order-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #94a3b8;
}

.order-card .order-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f1f5f9;
}

.btn-action {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: transform 0.1s;
}

.btn-action:active {
    transform: scale(0.95);
}

.btn-action.primary {
    background: #0ea5e9;
    color: white;
}

.btn-action.secondary {
    background: #f1f5f9;
    color: #475569;
}

.btn-action.success {
    background: #22c55e;
    color: white;
}

/* Bottom Navigation */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 480px;
    background: white;
    display: flex;
    justify-content: space-around;
    padding: 12px 0 20px;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
    border-radius: 20px 20px 0 0;
    z-index: 100;
}

.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    color: #94a3b8;
    font-size: 11px;
    cursor: pointer;
    padding: 8px 16px;
    border-radius: 12px;
    transition: all 0.2s;
}

.nav-item i {
    font-size: 20px;
}

.nav-item.active {
    color: #0ea5e9;
    background: #f0f9ff;
}

.nav-item .badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ef4444;
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
}

/* Pull to Refresh Indicator */
.refresh-indicator {
    text-align: center;
    padding: 20px;
    color: #0ea5e9;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #94a3b8;
}

.empty-state i {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state h3 {
    font-size: 16px;
    color: #64748b;
    margin-bottom: 8px;
}

/* Alert Toast */
.alert-toast {
    position: fixed;
    top: 80px;
    left: 16px;
    right: 16px;
    max-width: 448px;
    margin: 0 auto;
    background: #ef4444;
    color: white;
    padding: 16px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
    z-index: 200;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateY(-100%); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Map Placeholder */
.map-container {
    height: 200px;
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #0284c7;
    margin: 16px;
}

/* Photo Grid */
.photo-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 12px;
}

.photo-item {
    aspect-ratio: 1;
    background: #f1f5f9;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    cursor: pointer;
}

.photo-item.add-photo {
    border: 2px dashed #cbd5e1;
}

/* Form Styles */
.form-group {
    margin-bottom: 16px;
}

.form-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 15px;
    transition: border-color 0.2s;
}

.form-input:focus {
    outline: none;
    border-color: #0ea5e9;
}

.form-textarea {
    min-height: 100px;
    resize: vertical;
}

/* Offline Banner */
.offline-banner {
    background: #fef3c7;
    color: #92400e;
    padding: 10px 16px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Sync Status */
.sync-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
}

.sync-status.synced { color: #22c55e; }
.sync-status.pending { color: #f59e0b; }
.sync-status.error { color: #ef4444; }

/* Loading Spinner */
.spinner {
    width: 24px;
    height: 24px;
    border: 3px solid #e2e8f0;
    border-top-color: #0ea5e9;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
"""

# =============================================================================
# SAMPLE DATA - Fallback when API unavailable
# =============================================================================

import requests

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:5000")

def fetch_api_data(endpoint: str, default=None):
    """Fetch data from integrated API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return default


def get_work_orders():
    """Get work orders from API or use sample data."""
    # Fetch alerts from API and convert to work orders
    alerts = fetch_api_data("/api/alerts", [])
    
    if alerts:
        work_orders = []
        for i, alert in enumerate(alerts[:5]):
            priority = "critical" if alert.get("status") == "leak" else "high"
            work_orders.append({
                "order_id": f"WO-2026-{i+1:03d}",
                "priority": priority,
                "title": f"{'Suspected Leak' if priority == 'critical' else 'Pressure Anomaly'} - {alert.get('pipe_id', 'Unknown')}",
                "location": alert.get("location", "Unknown"),
                "pipe_id": alert.get("pipe_id"),
                "latitude": -15.4167,
                "longitude": 28.2833,
                "created": alert.get("last_update", "Recent"),
                "distance": f"{(i+1) * 1.5:.1f} km",
                "pressure_drop": f"{alert.get('pressure', 0):.1f} bar",
                "status": "pending"
            })
        if work_orders:
            return work_orders
    
    return SAMPLE_WORK_ORDERS


SAMPLE_WORK_ORDERS = [
    {
        "order_id": "WO-2026-001",
        "priority": "critical",
        "title": "Suspected Burst - Pipe A1",
        "location": "Kitwe Central, Near Market",
        "pipe_id": "Pipe_A1",
        "latitude": -12.8025,
        "longitude": 28.2135,
        "created": "2 hours ago",
        "distance": "1.2 km",
        "pressure_drop": "1.8 bar",
        "status": "pending"
    },
    {
        "order_id": "WO-2026-002",
        "priority": "high",
        "title": "Pressure Anomaly - Pipe B2",
        "location": "Ndola Industrial Area",
        "pipe_id": "Pipe_B2",
        "latitude": -12.9584,
        "longitude": 28.6366,
        "created": "5 hours ago",
        "distance": "3.5 km",
        "pressure_drop": "0.5 bar",
        "status": "pending"
    },
    {
        "order_id": "WO-2026-003",
        "priority": "medium",
        "title": "Scheduled Inspection - Pipe C1",
        "location": "Lusaka East",
        "pipe_id": "Pipe_C1",
        "latitude": -15.4067,
        "longitude": 28.2871,
        "created": "1 day ago",
        "distance": "8.2 km",
        "pressure_drop": "N/A",
        "status": "in_progress"
    }
]

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_header(user_name: str = "John"):
    return html.Div([
        html.H1([
            html.I(className="fas fa-water"),
            "AquaWatch Field"
        ]),
        html.Div([
            html.Span([
                html.I(className="fas fa-user-circle", style={"marginRight": "6px"}),
                f"Hi, {user_name}"
            ]),
            html.Span([
                html.I(className="fas fa-wifi", style={"marginRight": "6px"}),
                "Online"
            ], className="sync-status synced")
        ], className="status-bar")
    ], className="mobile-header")


def create_stats():
    return html.Div([
        html.Div([
            html.Div("3", className="number"),
            html.Div("Pending", className="label")
        ], className="stat-card urgent"),
        html.Div([
            html.Div("1", className="number"),
            html.Div("In Progress", className="label")
        ], className="stat-card warning"),
        html.Div([
            html.Div("12", className="number"),
            html.Div("Completed", className="label")
        ], className="stat-card success"),
    ], className="stats-grid")


def create_work_order_card(order: dict):
    return html.Div([
        html.Div([
            html.Span(order["order_id"], className="order-id"),
            html.Span(order["priority"].upper(), className=f"priority-badge {order['priority']}")
        ], className="order-header"),
        
        html.Div(order["title"], className="order-title"),
        
        html.Div([
            html.I(className="fas fa-map-marker-alt"),
            order["location"]
        ], className="order-location"),
        
        html.Div([
            html.Span([html.I(className="fas fa-clock"), f" {order['created']}"]),
            html.Span([html.I(className="fas fa-route"), f" {order['distance']}"]),
            html.Span([html.I(className="fas fa-tachometer-alt"), f" {order['pressure_drop']}"])
        ], className="order-meta"),
        
        html.Div([
            html.Button([
                html.I(className="fas fa-directions"),
                "Navigate"
            ], className="btn-action secondary"),
            html.Button([
                html.I(className="fas fa-play"),
                "Start"
            ], className="btn-action primary") if order["status"] == "pending" else
            html.Button([
                html.I(className="fas fa-check"),
                "Complete"
            ], className="btn-action success")
        ], className="order-actions")
    ], className=f"order-card {order['priority']}")


def create_work_orders_list():
    # FETCH FROM API
    work_orders = get_work_orders()
    
    if not work_orders:
        return html.Div([
            html.I(className="fas fa-clipboard-check"),
            html.H3("All caught up!"),
            html.P("No pending work orders")
        ], className="empty-state")
    
    return html.Div([
        create_work_order_card(order) for order in work_orders
    ])


def create_bottom_nav(active: str = "orders"):
    return html.Div([
        html.Div([
            html.I(className="fas fa-clipboard-list"),
            html.Span("Orders"),
            html.Span("3", className="badge") if active != "orders" else None
        ], className=f"nav-item {'active' if active == 'orders' else ''}", id="nav-orders"),
        
        html.Div([
            html.I(className="fas fa-map"),
            html.Span("Map")
        ], className=f"nav-item {'active' if active == 'map' else ''}", id="nav-map"),
        
        html.Div([
            html.I(className="fas fa-bell"),
            html.Span("Alerts"),
            html.Span("2", className="badge") if active != "alerts" else None
        ], className=f"nav-item {'active' if active == 'alerts' else ''}", id="nav-alerts"),
        
        html.Div([
            html.I(className="fas fa-user"),
            html.Span("Profile")
        ], className=f"nav-item {'active' if active == 'profile' else ''}", id="nav-profile"),
    ], className="bottom-nav")


def create_map_view():
    return html.Div([
        html.Div([
            html.I(className="fas fa-map-marked-alt", style={"fontSize": "48px", "marginBottom": "12px"}),
            html.Div("Map View", style={"fontWeight": "600"}),
            html.Div("Shows work order locations", style={"fontSize": "13px", "opacity": "0.8"})
        ], className="map-container"),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle"),
                " Integration with Google Maps / OpenStreetMap"
            ], style={"color": "#64748b", "fontSize": "13px", "textAlign": "center", "padding": "16px"})
        ])
    ])


def create_alerts_view():
    return html.Div([
        html.Div([
            html.I(className="fas fa-bell"),
            " Recent Alerts"
        ], className="section-title"),
        
        html.Div([
            html.Div([
                html.Div([
                    html.Span("🚨", style={"fontSize": "24px"}),
                ], style={"marginRight": "12px"}),
                html.Div([
                    html.Div("Burst Detected - Pipe A1", style={"fontWeight": "600", "color": "#ef4444"}),
                    html.Div("Kitwe Central • 2 min ago", style={"fontSize": "13px", "color": "#64748b"})
                ])
            ], style={"display": "flex", "alignItems": "center", "padding": "16px", "background": "white", "borderRadius": "12px", "marginBottom": "12px"}),
            
            html.Div([
                html.Div([
                    html.Span("⚠️", style={"fontSize": "24px"}),
                ], style={"marginRight": "12px"}),
                html.Div([
                    html.Div("Pressure Drop - Pipe B2", style={"fontWeight": "600", "color": "#f59e0b"}),
                    html.Div("Ndola Industrial • 15 min ago", style={"fontSize": "13px", "color": "#64748b"})
                ])
            ], style={"display": "flex", "alignItems": "center", "padding": "16px", "background": "white", "borderRadius": "12px", "marginBottom": "12px"}),
        ])
    ], className="section")


# =============================================================================
# MAIN LAYOUT
# =============================================================================

mobile_app.layout = html.Div([
    # Styles
    html.Style(MOBILE_STYLES),
    
    # Store for navigation state
    dcc.Store(id="nav-state", data="orders"),
    dcc.Store(id="offline-queue", storage_type="local"),
    
    # App Container
    html.Div([
        # Header
        create_header("Technician"),
        
        # Stats
        create_stats(),
        
        # Main Content
        html.Div(id="main-content", children=[
            html.Div([
                html.Div([
                    html.I(className="fas fa-clipboard-list"),
                    " Work Orders"
                ], className="section-title"),
                create_work_orders_list()
            ], className="section")
        ]),
        
        # Bottom Navigation
        create_bottom_nav("orders"),
        
        # Auto-refresh
        dcc.Interval(id="refresh-interval", interval=30000, n_intervals=0)
        
    ], className="mobile-app")
])


# =============================================================================
# CALLBACKS
# =============================================================================

@mobile_app.callback(
    [Output("main-content", "children"),
     Output("nav-state", "data")],
    [Input("nav-orders", "n_clicks"),
     Input("nav-map", "n_clicks"),
     Input("nav-alerts", "n_clicks"),
     Input("nav-profile", "n_clicks")],
    prevent_initial_call=True
)
def navigate(orders_clicks, map_clicks, alerts_clicks, profile_clicks):
    trigger = ctx.triggered_id
    
    if trigger == "nav-map":
        return create_map_view(), "map"
    
    elif trigger == "nav-alerts":
        return create_alerts_view(), "alerts"
    
    elif trigger == "nav-profile":
        return html.Div([
            html.Div([
                html.I(className="fas fa-user-circle", style={"fontSize": "64px", "color": "#0ea5e9"}),
                html.H3("John Mwale", style={"marginTop": "16px", "marginBottom": "4px"}),
                html.Div("Field Technician", style={"color": "#64748b"}),
                html.Div("Kitwe District", style={"color": "#94a3b8", "fontSize": "13px"})
            ], style={"textAlign": "center", "padding": "32px"}),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={"width": "24px", "color": "#0ea5e9"}),
                    html.Span("My Performance"),
                    html.I(className="fas fa-chevron-right", style={"marginLeft": "auto", "color": "#94a3b8"})
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "padding": "16px", "background": "white", "borderRadius": "12px", "marginBottom": "8px"}),
                
                html.Div([
                    html.I(className="fas fa-cog", style={"width": "24px", "color": "#0ea5e9"}),
                    html.Span("Settings"),
                    html.I(className="fas fa-chevron-right", style={"marginLeft": "auto", "color": "#94a3b8"})
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "padding": "16px", "background": "white", "borderRadius": "12px", "marginBottom": "8px"}),
                
                html.Div([
                    html.I(className="fas fa-sign-out-alt", style={"width": "24px", "color": "#ef4444"}),
                    html.Span("Logout", style={"color": "#ef4444"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "padding": "16px", "background": "white", "borderRadius": "12px"}),
            ], style={"padding": "0 16px"})
        ]), "profile"
    
    else:  # orders (default)
        return html.Div([
            html.Div([
                html.I(className="fas fa-clipboard-list"),
                " Work Orders"
            ], className="section-title"),
            create_work_orders_list()
        ], className="section"), "orders"


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("📱 AQUAWATCH FIELD TECHNICIAN APP")
    print("=" * 50)
    print("\n🌐 Mobile App: http://127.0.0.1:8070")
    print("📱 Open on your phone for best experience")
    print("\n" + "=" * 50 + "\n")
    
    mobile_app.run(debug=True, port=8070, host="0.0.0.0")
