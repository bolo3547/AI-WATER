"""
AquaWatch NRW v3.0 - WebSocket API Routes
=========================================

FastAPI WebSocket endpoints for real-time event streaming.

Endpoint:
    /ws/tenants/{tenant_id}/events

Authentication:
    - JWT token passed via query parameter: ?token=<jwt>
    - Or via Sec-WebSocket-Protocol header

Events:
    - leak.detected, leak.updated, leak.confirmed, leak.resolved
    - work_order.created, work_order.updated, work_order.assigned, work_order.completed
    - sensor.offline, sensor.online, sensor.anomaly
    - alert.critical, alert.warning, alert.info, alert.resolved

Usage (JavaScript):
    const ws = new WebSocket('wss://api.aquawatch.io/ws/tenants/lwsc-zambia/events?token=<jwt>');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data.event_type, data.payload);
    };
"""

import logging
from typing import Optional, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status

from ..security.multi_tenant_auth import (
    token_manager,
    TokenPayload,
    TenantRole,
    CurrentUser,
    audit_logger,
    AuditAction
)
from ..events.websocket_events import (
    event_broadcaster,
    WebSocketEventType,
    TenantConnection
)

logger = logging.getLogger(__name__)


# =============================================================================
# WEBSOCKET ROUTER
# =============================================================================

ws_router = APIRouter(tags=["WebSocket Events"])


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

async def authenticate_websocket(
    websocket: WebSocket,
    tenant_id: str,
    token: Optional[str] = None
) -> Optional[TokenPayload]:
    """
    Authenticate WebSocket connection.
    
    Token can be provided via:
    1. Query parameter: ?token=<jwt>
    2. Sec-WebSocket-Protocol header (for browsers that can't set custom headers)
    
    Args:
        websocket: WebSocket connection
        tenant_id: Target tenant from path
        token: JWT token from query parameter
    
    Returns:
        TokenPayload if authenticated, None if failed
    """
    # Try query parameter first
    jwt_token = token
    
    # Fall back to Sec-WebSocket-Protocol header
    if not jwt_token:
        protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
        for protocol in protocols:
            protocol = protocol.strip()
            if protocol.startswith("bearer."):
                jwt_token = protocol[7:]  # Remove "bearer." prefix
                break
    
    if not jwt_token:
        logger.warning(f"WebSocket connection attempt without token: tenant={tenant_id}")
        return None
    
    # Verify token
    payload = token_manager.verify_token(jwt_token)
    
    if not payload:
        logger.warning(f"WebSocket connection with invalid token: tenant={tenant_id}")
        return None
    
    # Check token type
    if payload.type != "access":
        logger.warning(f"WebSocket connection with non-access token: tenant={tenant_id}")
        return None
    
    # Verify tenant access
    user = CurrentUser(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        role=payload.role,
        permissions=set(payload.permissions),
        email=payload.email,
        name=payload.name
    )
    
    if not user.can_access_tenant(tenant_id):
        logger.warning(
            f"WebSocket tenant access denied: user_tenant={payload.tenant_id}, "
            f"requested_tenant={tenant_id}, user={payload.user_id}"
        )
        return None
    
    return payload


def parse_event_filter(event_types_param: Optional[str]) -> Set[str]:
    """Parse comma-separated event type filter."""
    if not event_types_param:
        return set()  # Empty set means subscribe to all
    
    valid_types = {e.value for e in WebSocketEventType}
    requested = {e.strip() for e in event_types_param.split(",") if e.strip()}
    
    # Filter to valid types
    return requested & valid_types


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@ws_router.websocket("/ws/tenants/{tenant_id}/events")
async def websocket_tenant_events(
    websocket: WebSocket,
    tenant_id: str,
    token: Optional[str] = Query(None, description="JWT access token"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to subscribe to"),
    replay_since: Optional[str] = Query(None, description="ISO timestamp to replay events from")
):
    """
    WebSocket endpoint for real-time tenant events.
    
    Authentication:
        Pass JWT token via query parameter: /ws/tenants/{tenant_id}/events?token=<jwt>
    
    Event Filtering:
        Filter specific event types: ?event_types=leak.detected,sensor.offline
    
    Event Replay:
        Replay missed events: ?replay_since=2024-01-15T10:00:00Z
    
    Message Format (JSON):
        {
            "event_id": "evt_1705320000.123",
            "event_type": "leak.detected",
            "tenant_id": "lwsc-zambia",
            "payload": { ... },
            "timestamp": "2024-01-15T10:00:00.123Z",
            "source": "leak_detection_engine"
        }
    
    Client Messages:
        - {"type": "heartbeat"} - Client heartbeat (optional)
        - {"type": "subscribe", "event_types": ["leak.detected", ...]} - Update subscription
        - {"type": "unsubscribe", "event_types": ["sensor.offline", ...]} - Remove subscription
    """
    # Authenticate before accepting
    payload = await authenticate_websocket(websocket, tenant_id, token)
    
    if not payload:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Accept connection with subprotocol if used
    subprotocol = None
    protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
    for protocol in protocols:
        protocol = protocol.strip()
        if protocol.startswith("bearer."):
            subprotocol = protocol
            break
    
    await websocket.accept(subprotocol=subprotocol)
    
    # Parse event filter
    subscribed_events = parse_event_filter(event_types)
    
    # Register connection
    connection = await event_broadcaster.connect(
        websocket=websocket,
        tenant_id=tenant_id,
        user_id=payload.user_id,
        role=payload.role.value,
        event_types=subscribed_events
    )
    
    # Log connection
    logger.info(
        f"WebSocket connected: tenant={tenant_id}, user={payload.user_id}, "
        f"role={payload.role.value}, subscribed={subscribed_events or 'all'}"
    )
    
    # Replay events if requested
    if replay_since:
        try:
            since_dt = datetime.fromisoformat(replay_since.replace("Z", "+00:00"))
            replayed = await event_broadcaster.replay_history(
                connection=connection,
                since=since_dt.replace(tzinfo=None),  # Remove timezone for comparison
                event_types=subscribed_events if subscribed_events else None,
                limit=50
            )
            logger.info(f"Replayed {replayed} events to {payload.user_id}")
        except ValueError as e:
            logger.warning(f"Invalid replay_since timestamp: {replay_since}")
    
    try:
        # Message handling loop
        while True:
            try:
                # Receive and parse message
                data = await websocket.receive_json()
                
                msg_type = data.get("type", "")
                
                if msg_type == "heartbeat":
                    # Client heartbeat - update connection timestamp
                    connection.update_heartbeat()
                    await websocket.send_json({
                        "event_type": "connection.heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "subscribe":
                    # Add event types to subscription
                    new_types = set(data.get("event_types", []))
                    connection.subscribed_event_types.update(new_types)
                    await websocket.send_json({
                        "event_type": "connection.subscription_updated",
                        "subscribed_events": list(connection.subscribed_event_types)
                    })
                
                elif msg_type == "unsubscribe":
                    # Remove event types from subscription
                    remove_types = set(data.get("event_types", []))
                    connection.subscribed_event_types -= remove_types
                    await websocket.send_json({
                        "event_type": "connection.subscription_updated",
                        "subscribed_events": list(connection.subscribed_event_types)
                    })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "event_type": "connection.error",
                        "error": f"Unknown message type: {msg_type}"
                    })
                    
            except Exception as e:
                # JSON parse error or other issue
                logger.warning(f"WebSocket message error: {e}")
                await websocket.send_json({
                    "event_type": "connection.error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: tenant={tenant_id}, user={payload.user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # Clean up connection
        await event_broadcaster.disconnect(connection)


# =============================================================================
# REST API FOR WEBSOCKET MANAGEMENT
# =============================================================================

@ws_router.get("/ws/tenants/{tenant_id}/connections")
async def get_tenant_connections(tenant_id: str):
    """
    Get information about active WebSocket connections for a tenant.
    
    Useful for monitoring and debugging.
    """
    connections = event_broadcaster.get_tenant_connections(tenant_id)
    return {
        "tenant_id": tenant_id,
        "connection_count": len(connections),
        "connections": connections
    }


@ws_router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get overall WebSocket statistics.
    
    Returns connection counts per tenant.
    """
    total_connections = event_broadcaster.get_connection_count()
    
    # Get per-tenant counts
    tenant_counts = {}
    for tenant_id in event_broadcaster._connections.keys():
        tenant_counts[tenant_id] = event_broadcaster.get_connection_count(tenant_id)
    
    return {
        "total_connections": total_connections,
        "tenants": tenant_counts,
        "heartbeat_interval": event_broadcaster.heartbeat_interval,
        "stale_timeout": event_broadcaster.stale_timeout
    }


# =============================================================================
# EVENT TESTING ENDPOINT (DEV ONLY)
# =============================================================================

@ws_router.post("/ws/tenants/{tenant_id}/test-event")
async def send_test_event(
    tenant_id: str,
    event_type: str = Query(..., description="Event type to send"),
    payload: Optional[dict] = None
):
    """
    Send a test event to all connections for a tenant.
    
    FOR DEVELOPMENT/TESTING ONLY - should be disabled in production.
    """
    try:
        event_type_enum = WebSocketEventType(event_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_type}. Valid types: {[e.value for e in WebSocketEventType]}"
        )
    
    count = await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=event_type_enum,
        payload=payload or {"test": True, "message": "This is a test event"},
        source="test_endpoint"
    )
    
    return {
        "success": True,
        "event_type": event_type,
        "tenant_id": tenant_id,
        "connections_notified": count
    }
