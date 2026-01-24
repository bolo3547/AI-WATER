"""
AquaWatch NRW v3.0 - WebSocket Event Broadcasting System
========================================================

Real-time event broadcasting with tenant isolation for:
- leak.detected, leak.updated
- work_order.created, work_order.updated
- sensor.offline, sensor.online
- alert.critical

Architecture:
- In-memory pub/sub with tenant-isolated channels
- Support for Redis backend (optional, for horizontal scaling)
- Event deduplication and rate limiting
- Heartbeat/ping-pong for connection health

Usage:
    from src.events.websocket_events import event_broadcaster
    
    # Broadcast to all connections for a tenant
    await event_broadcaster.broadcast(
        tenant_id="lwsc-zambia",
        event_type="leak.detected",
        payload={"leak_id": "L001", "dma_id": "DMA-01", ...}
    )
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import weakref

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TYPES
# =============================================================================

class WebSocketEventType(str, Enum):
    """WebSocket event types for real-time updates."""
    
    # Leak events
    LEAK_DETECTED = "leak.detected"
    LEAK_UPDATED = "leak.updated"
    LEAK_CONFIRMED = "leak.confirmed"
    LEAK_RESOLVED = "leak.resolved"
    
    # Work order events
    WORK_ORDER_CREATED = "work_order.created"
    WORK_ORDER_UPDATED = "work_order.updated"
    WORK_ORDER_ASSIGNED = "work_order.assigned"
    WORK_ORDER_COMPLETED = "work_order.completed"
    
    # Sensor events
    SENSOR_OFFLINE = "sensor.offline"
    SENSOR_ONLINE = "sensor.online"
    SENSOR_ANOMALY = "sensor.anomaly"
    
    # Alert events
    ALERT_CRITICAL = "alert.critical"
    ALERT_WARNING = "alert.warning"
    ALERT_INFO = "alert.info"
    ALERT_RESOLVED = "alert.resolved"
    
    # System events
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_UPDATE = "system.update"
    
    # Connection events (internal)
    CONNECTED = "connection.established"
    HEARTBEAT = "connection.heartbeat"
    ERROR = "connection.error"


@dataclass
class WebSocketEvent:
    """Structured WebSocket event."""
    
    event_type: WebSocketEventType
    tenant_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: f"evt_{datetime.utcnow().timestamp()}")
    source: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, Enum) else self.event_type,
            "tenant_id": self.tenant_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class TenantConnection:
    """Represents a WebSocket connection for a tenant user."""
    
    websocket: WebSocket
    tenant_id: str
    user_id: str
    role: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    subscribed_event_types: Set[str] = field(default_factory=set)
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def is_stale(self, timeout_seconds: int = 60) -> bool:
        """Check if connection is stale (no heartbeat)."""
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() > timeout_seconds


# =============================================================================
# EVENT BROADCASTER
# =============================================================================

class TenantEventBroadcaster:
    """
    In-memory event broadcaster with tenant isolation.
    
    Features:
    - Tenant-isolated channels
    - Event type filtering per connection
    - Rate limiting (optional)
    - Heartbeat monitoring
    - Graceful disconnection handling
    """
    
    def __init__(self, heartbeat_interval: int = 30, stale_timeout: int = 90):
        """
        Initialize the broadcaster.
        
        Args:
            heartbeat_interval: Seconds between heartbeat pings
            stale_timeout: Seconds before considering a connection stale
        """
        # Connections indexed by tenant_id
        self._connections: Dict[str, Set[TenantConnection]] = defaultdict(set)
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Event history for replay (limited)
        self._event_history: Dict[str, List[WebSocketEvent]] = defaultdict(list)
        self._history_limit = 100
        
        # Rate limiting
        self._rate_limit_window = 60  # seconds
        self._rate_limit_max = 100  # events per window
        self._rate_counters: Dict[str, List[datetime]] = defaultdict(list)
        
        # Heartbeat config
        self.heartbeat_interval = heartbeat_interval
        self.stale_timeout = stale_timeout
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Event handlers (for plugins/extensions)
        self._event_handlers: Dict[WebSocketEventType, List[Callable]] = defaultdict(list)
        
        logger.info("TenantEventBroadcaster initialized")
    
    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    
    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
        role: str,
        event_types: Optional[Set[str]] = None
    ) -> TenantConnection:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            tenant_id: Tenant identifier
            user_id: User identifier
            role: User role for permission checking
            event_types: Optional set of event types to subscribe to
        
        Returns:
            TenantConnection object
        """
        connection = TenantConnection(
            websocket=websocket,
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            subscribed_event_types=event_types or set()
        )
        
        async with self._lock:
            self._connections[tenant_id].add(connection)
        
        logger.info(f"WebSocket connected: tenant={tenant_id}, user={user_id}, role={role}")
        
        # Send connection established event
        await self._send_to_connection(connection, WebSocketEvent(
            event_type=WebSocketEventType.CONNECTED,
            tenant_id=tenant_id,
            payload={
                "message": "Connected to AquaWatch real-time events",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "subscribed_events": list(event_types) if event_types else "all"
            }
        ))
        
        return connection
    
    async def disconnect(self, connection: TenantConnection):
        """Remove a WebSocket connection."""
        async with self._lock:
            tenant_id = connection.tenant_id
            if connection in self._connections[tenant_id]:
                self._connections[tenant_id].discard(connection)
                logger.info(f"WebSocket disconnected: tenant={tenant_id}, user={connection.user_id}")
            
            # Clean up empty tenant sets
            if not self._connections[tenant_id]:
                del self._connections[tenant_id]
    
    def get_connection_count(self, tenant_id: Optional[str] = None) -> int:
        """Get number of active connections."""
        if tenant_id:
            return len(self._connections.get(tenant_id, set()))
        return sum(len(conns) for conns in self._connections.values())
    
    def get_tenant_connections(self, tenant_id: str) -> List[Dict]:
        """Get info about connections for a tenant."""
        connections = self._connections.get(tenant_id, set())
        return [
            {
                "user_id": c.user_id,
                "role": c.role,
                "connected_at": c.connected_at.isoformat(),
                "last_heartbeat": c.last_heartbeat.isoformat(),
                "subscribed_events": list(c.subscribed_event_types)
            }
            for c in connections
        ]
    
    # -------------------------------------------------------------------------
    # Broadcasting
    # -------------------------------------------------------------------------
    
    async def broadcast(
        self,
        tenant_id: str,
        event_type: WebSocketEventType,
        payload: Dict[str, Any],
        source: str = "system",
        exclude_user_id: Optional[str] = None
    ) -> int:
        """
        Broadcast an event to all connections for a tenant.
        
        Args:
            tenant_id: Target tenant
            event_type: Type of event
            payload: Event data
            source: Event source identifier
            exclude_user_id: Optional user to exclude (e.g., the originator)
        
        Returns:
            Number of connections that received the event
        """
        event = WebSocketEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
            source=source
        )
        
        # Check rate limit
        if not self._check_rate_limit(tenant_id):
            logger.warning(f"Rate limit exceeded for tenant {tenant_id}")
            return 0
        
        # Store in history
        self._add_to_history(tenant_id, event)
        
        # Run event handlers
        await self._run_handlers(event)
        
        # Broadcast to connections
        connections = self._connections.get(tenant_id, set())
        sent_count = 0
        disconnected = []
        
        for connection in connections:
            # Skip excluded user
            if exclude_user_id and connection.user_id == exclude_user_id:
                continue
            
            # Check event type subscription
            if connection.subscribed_event_types:
                event_type_str = event_type.value if isinstance(event_type, Enum) else event_type
                if event_type_str not in connection.subscribed_event_types:
                    continue
            
            try:
                await self._send_to_connection(connection, event)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            await self.disconnect(conn)
        
        logger.debug(f"Broadcast {event_type.value if isinstance(event_type, Enum) else event_type} to {sent_count} connections in tenant {tenant_id}")
        
        return sent_count
    
    async def broadcast_to_all_tenants(
        self,
        event_type: WebSocketEventType,
        payload: Dict[str, Any],
        source: str = "system"
    ) -> Dict[str, int]:
        """Broadcast an event to all tenants (system-wide announcements)."""
        results = {}
        for tenant_id in list(self._connections.keys()):
            count = await self.broadcast(tenant_id, event_type, payload, source)
            results[tenant_id] = count
        return results
    
    async def send_to_user(
        self,
        tenant_id: str,
        user_id: str,
        event_type: WebSocketEventType,
        payload: Dict[str, Any],
        source: str = "system"
    ) -> bool:
        """Send an event to a specific user within a tenant."""
        event = WebSocketEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
            source=source
        )
        
        connections = self._connections.get(tenant_id, set())
        for connection in connections:
            if connection.user_id == user_id:
                try:
                    await self._send_to_connection(connection, event)
                    return True
                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")
                    await self.disconnect(connection)
                    return False
        
        return False
    
    async def _send_to_connection(self, connection: TenantConnection, event: WebSocketEvent):
        """Send event to a single connection."""
        try:
            await connection.websocket.send_json(event.to_dict())
        except Exception as e:
            raise  # Let caller handle disconnection
    
    # -------------------------------------------------------------------------
    # History & Replay
    # -------------------------------------------------------------------------
    
    def _add_to_history(self, tenant_id: str, event: WebSocketEvent):
        """Add event to history buffer."""
        history = self._event_history[tenant_id]
        history.append(event)
        
        # Trim old events
        if len(history) > self._history_limit:
            self._event_history[tenant_id] = history[-self._history_limit:]
    
    async def replay_history(
        self,
        connection: TenantConnection,
        since: Optional[datetime] = None,
        event_types: Optional[Set[str]] = None,
        limit: int = 50
    ) -> int:
        """
        Replay recent events to a connection (for reconnection scenarios).
        
        Args:
            connection: Target connection
            since: Only replay events after this timestamp
            event_types: Filter by event types
            limit: Maximum events to replay
        
        Returns:
            Number of events replayed
        """
        history = self._event_history.get(connection.tenant_id, [])
        
        # Filter events
        events = []
        for event in reversed(history):
            if since and event.timestamp <= since:
                break
            
            if event_types:
                event_type_str = event.event_type.value if isinstance(event.event_type, Enum) else event.event_type
                if event_type_str not in event_types:
                    continue
            
            events.append(event)
            if len(events) >= limit:
                break
        
        # Send in chronological order
        events.reverse()
        for event in events:
            try:
                await self._send_to_connection(connection, event)
            except Exception:
                break
        
        return len(events)
    
    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------
    
    def _check_rate_limit(self, tenant_id: str) -> bool:
        """Check if tenant is within rate limits."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self._rate_limit_window)
        
        # Clean old timestamps
        self._rate_counters[tenant_id] = [
            ts for ts in self._rate_counters[tenant_id]
            if ts > window_start
        ]
        
        # Check limit
        if len(self._rate_counters[tenant_id]) >= self._rate_limit_max:
            return False
        
        # Record this event
        self._rate_counters[tenant_id].append(now)
        return True
    
    # -------------------------------------------------------------------------
    # Heartbeat & Cleanup
    # -------------------------------------------------------------------------
    
    async def start_background_tasks(self):
        """Start heartbeat and cleanup background tasks."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("Started WebSocket heartbeat task")
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started WebSocket cleanup task")
    
    async def stop_background_tasks(self):
        """Stop background tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat pings to all connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                for tenant_id in list(self._connections.keys()):
                    connections = list(self._connections[tenant_id])
                    for connection in connections:
                        try:
                            await connection.websocket.send_json({
                                "event_type": "connection.heartbeat",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except Exception:
                            await self.disconnect(connection)
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    async def _cleanup_loop(self):
        """Remove stale connections."""
        while True:
            try:
                await asyncio.sleep(self.stale_timeout)
                
                for tenant_id in list(self._connections.keys()):
                    stale = [
                        c for c in self._connections[tenant_id]
                        if c.is_stale(self.stale_timeout)
                    ]
                    for connection in stale:
                        logger.info(f"Removing stale connection: tenant={tenant_id}, user={connection.user_id}")
                        await self.disconnect(connection)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    
    def register_handler(self, event_type: WebSocketEventType, handler: Callable):
        """Register a handler for an event type."""
        self._event_handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: WebSocketEventType, handler: Callable):
        """Unregister an event handler."""
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)
    
    async def _run_handlers(self, event: WebSocketEvent):
        """Run all registered handlers for an event."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

event_broadcaster = TenantEventBroadcaster()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def broadcast_leak_detected(
    tenant_id: str,
    leak_id: str,
    dma_id: str,
    location: str,
    estimated_loss_m3: float,
    confidence: float,
    priority: str = "high",
    detection_method: str = "ai"
) -> int:
    """Convenience function to broadcast leak detection event."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.LEAK_DETECTED,
        payload={
            "leak_id": leak_id,
            "dma_id": dma_id,
            "location": location,
            "estimated_loss_m3_per_day": estimated_loss_m3,
            "confidence": confidence,
            "priority": priority,
            "detection_method": detection_method,
            "requires_immediate_attention": priority == "high"
        },
        source="leak_detection_engine"
    )


async def broadcast_leak_updated(
    tenant_id: str,
    leak_id: str,
    status: str,
    updated_by: str,
    changes: Dict[str, Any]
) -> int:
    """Convenience function to broadcast leak update event."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.LEAK_UPDATED,
        payload={
            "leak_id": leak_id,
            "new_status": status,
            "updated_by": updated_by,
            "changes": changes
        },
        source="leak_management"
    )


async def broadcast_work_order_created(
    tenant_id: str,
    work_order_id: str,
    leak_id: Optional[str],
    title: str,
    priority: str,
    assigned_to: Optional[str] = None
) -> int:
    """Convenience function to broadcast work order creation."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.WORK_ORDER_CREATED,
        payload={
            "work_order_id": work_order_id,
            "leak_id": leak_id,
            "title": title,
            "priority": priority,
            "assigned_to": assigned_to
        },
        source="work_order_system"
    )


async def broadcast_sensor_offline(
    tenant_id: str,
    sensor_id: str,
    sensor_type: str,
    dma_id: str,
    last_seen: datetime,
    reason: Optional[str] = None
) -> int:
    """Convenience function to broadcast sensor offline event."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.SENSOR_OFFLINE,
        payload={
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "dma_id": dma_id,
            "last_seen": last_seen.isoformat(),
            "reason": reason,
            "alert_level": "warning"
        },
        source="sensor_monitoring"
    )


async def broadcast_sensor_online(
    tenant_id: str,
    sensor_id: str,
    sensor_type: str,
    dma_id: str
) -> int:
    """Convenience function to broadcast sensor back online event."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.SENSOR_ONLINE,
        payload={
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "dma_id": dma_id,
            "status": "online"
        },
        source="sensor_monitoring"
    )


async def broadcast_critical_alert(
    tenant_id: str,
    alert_id: str,
    title: str,
    message: str,
    category: str,
    action_required: bool = True
) -> int:
    """Convenience function to broadcast critical alert."""
    return await event_broadcaster.broadcast(
        tenant_id=tenant_id,
        event_type=WebSocketEventType.ALERT_CRITICAL,
        payload={
            "alert_id": alert_id,
            "title": title,
            "message": message,
            "category": category,
            "action_required": action_required,
            "severity": "critical"
        },
        source="alert_system"
    )
