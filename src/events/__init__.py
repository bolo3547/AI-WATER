"""
AquaWatch NRW v3.0 - Events Module
==================================

Real-time event management and WebSocket broadcasting.

Components:
- event_management.py: Core event types and management system
- websocket_events.py: WebSocket event broadcaster with tenant isolation

Usage:
    from src.events import (
        event_broadcaster,
        broadcast_leak_detected,
        broadcast_sensor_offline,
        WebSocketEventType,
    )
    
    # Broadcast a leak detection
    await broadcast_leak_detected(
        tenant_id="lwsc-zambia",
        leak_id="L001",
        dma_id="DMA-01",
        location="Corner of Cairo Rd and Kafue Rd",
        estimated_loss_m3=150.0,
        confidence=0.87,
        priority="high"
    )
"""

from .event_management import (
    EventType,
    EventSeverity,
    EventStatus,
    Event,
)

from .websocket_events import (
    # Main broadcaster
    event_broadcaster,
    TenantEventBroadcaster,
    
    # Event types
    WebSocketEventType,
    WebSocketEvent,
    TenantConnection,
    
    # Convenience functions
    broadcast_leak_detected,
    broadcast_leak_updated,
    broadcast_work_order_created,
    broadcast_sensor_offline,
    broadcast_sensor_online,
    broadcast_critical_alert,
)

__all__ = [
    # Event management
    "EventType",
    "EventSeverity",
    "EventStatus",
    "Event",
    
    # WebSocket broadcasting
    "event_broadcaster",
    "TenantEventBroadcaster",
    "WebSocketEventType",
    "WebSocketEvent",
    "TenantConnection",
    
    # Convenience functions
    "broadcast_leak_detected",
    "broadcast_leak_updated",
    "broadcast_work_order_created",
    "broadcast_sensor_offline",
    "broadcast_sensor_online",
    "broadcast_critical_alert",
]
