"""
AQUAWATCH NRW - EVENT BUS
=========================

Event-driven architecture for loose coupling between components.

Events:
- New sensor data → triggers feature update
- New anomaly → triggers decision engine
- New work order update → triggers learning loop
- Leak repair confirmed → triggers retraining flag
- System health change → triggers alerts

Ensures:
- Loose coupling
- Clear event contracts
- Idempotent processing

Author: AquaWatch AI Team
Version: 1.0.0
"""

import asyncio
import logging
import threading
import queue
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict
import json
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType(Enum):
    """System event types."""
    # Data events
    SENSOR_DATA_RECEIVED = "sensor_data_received"
    FEATURE_UPDATED = "feature_updated"
    BASELINE_UPDATED = "baseline_updated"
    
    # AI events
    ANOMALY_DETECTED = "anomaly_detected"
    LEAK_PROBABILITY_UPDATED = "leak_probability_updated"
    NRW_CALCULATED = "nrw_calculated"
    
    # Decision events
    DECISION_MADE = "decision_made"
    PRIORITY_CHANGED = "priority_changed"
    
    # Workflow events
    ALERT_CREATED = "alert_created"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"
    WORK_ORDER_CREATED = "work_order_created"
    WORK_ORDER_UPDATED = "work_order_updated"
    WORK_ORDER_COMPLETED = "work_order_completed"
    
    # Feedback events
    FIELD_FEEDBACK_RECEIVED = "field_feedback_received"
    LEAK_CONFIRMED = "leak_confirmed"
    FALSE_POSITIVE_REPORTED = "false_positive_reported"
    
    # Learning events
    RETRAINING_TRIGGERED = "retraining_triggered"
    MODEL_UPDATED = "model_updated"
    DRIFT_DETECTED = "drift_detected"
    
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    COMPONENT_HEALTHY = "component_healthy"
    COMPONENT_UNHEALTHY = "component_unhealthy"
    HEALTH_CHECK_FAILED = "health_check_failed"
    
    # Notification events
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_FAILED = "notification_failed"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# =============================================================================
# EVENT DATA CLASSES
# =============================================================================

@dataclass
class Event:
    """Base event class."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    priority: EventPriority = EventPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'priority': self.priority.value,
            'data': self.data,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        return cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            priority=EventPriority(data.get('priority', 1)),
            data=data.get('data', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class EventSubscription:
    """Subscription to events."""
    subscription_id: str
    event_types: Set[EventType]
    handler: Callable[[Event], None]
    filter_func: Optional[Callable[[Event], bool]] = None
    async_handler: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# EVENT BUS
# =============================================================================

class EventBus:
    """
    Central event bus for system-wide event handling.
    
    Provides:
    - Publish/subscribe pattern
    - Event filtering
    - Async and sync handlers
    - Event history for replay
    - Dead letter queue for failed handlers
    """
    
    def __init__(self, max_history: int = 1000, max_queue_size: int = 10000):
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._type_subscriptions: Dict[EventType, Set[str]] = defaultdict(set)
        
        # Event queues
        self._event_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self._dead_letter_queue: List[tuple] = []
        
        # History
        self._event_history: List[Event] = []
        self._max_history = max_history
        
        # Processing
        self._running = False
        self._processor_thread: Optional[threading.Thread] = None
        
        # Metrics
        self.metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_called': 0
        }
        
        logger.info("EventBus initialized")
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable[[Event], None],
        filter_func: Optional[Callable[[Event], bool]] = None,
        async_handler: bool = False
    ) -> str:
        """Subscribe to events."""
        subscription_id = str(uuid.uuid4())[:8]
        
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=set(event_types),
            handler=handler,
            filter_func=filter_func,
            async_handler=async_handler
        )
        
        with self._lock:
            self._subscriptions[subscription_id] = subscription
            for event_type in event_types:
                self._type_subscriptions[event_type].add(subscription_id)
        
        logger.debug(f"Subscription {subscription_id} registered for {event_types}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events."""
        with self._lock:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                for event_type in subscription.event_types:
                    self._type_subscriptions[event_type].discard(subscription_id)
                del self._subscriptions[subscription_id]
                logger.debug(f"Subscription {subscription_id} removed")
    
    def subscribe_all(self, handler: Callable[[Event], None]) -> str:
        """Subscribe to all events."""
        return self.subscribe(list(EventType), handler)
    
    # =========================================================================
    # EVENT PUBLISHING
    # =========================================================================
    
    def publish(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Publish an event."""
        event = Event(
            event_id=str(uuid.uuid4())[:12],
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source=source,
            priority=priority,
            data=data or {},
            metadata=metadata or {}
        )
        
        # Add to queue (priority queue uses negative for high priority first)
        self._event_queue.put((-priority.value, time.time(), event))
        
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        self.metrics['events_published'] += 1
        logger.debug(f"Event published: {event_type.value} from {source}")
        
        return event.event_id
    
    def publish_sync(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> str:
        """Publish and process event synchronously."""
        event = Event(
            event_id=str(uuid.uuid4())[:12],
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source=source,
            priority=priority,
            data=data or {}
        )
        
        self._process_event(event)
        self.metrics['events_published'] += 1
        
        return event.event_id
    
    # =========================================================================
    # EVENT PROCESSING
    # =========================================================================
    
    def start(self):
        """Start event processing."""
        if self._running:
            return
        
        self._running = True
        self._processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._processor_thread.start()
        logger.info("EventBus started")
    
    def stop(self, timeout: float = 5.0):
        """Stop event processing."""
        self._running = False
        if self._processor_thread:
            self._processor_thread.join(timeout=timeout)
        logger.info("EventBus stopped")
    
    def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                # Get event with timeout
                try:
                    _, _, event = self._event_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                self._process_event(event)
                self._event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    def _process_event(self, event: Event):
        """Process a single event."""
        subscription_ids = self._type_subscriptions.get(event.event_type, set())
        
        for sub_id in subscription_ids:
            subscription = self._subscriptions.get(sub_id)
            if not subscription:
                continue
            
            # Apply filter
            if subscription.filter_func:
                try:
                    if not subscription.filter_func(event):
                        continue
                except Exception as e:
                    logger.error(f"Filter error for {sub_id}: {e}")
                    continue
            
            # Call handler
            try:
                if subscription.async_handler:
                    asyncio.create_task(subscription.handler(event))
                else:
                    subscription.handler(event)
                
                self.metrics['handlers_called'] += 1
                
            except Exception as e:
                logger.error(f"Handler error for {sub_id}: {e}")
                self._dead_letter_queue.append((event, sub_id, str(e)))
                self.metrics['events_failed'] += 1
        
        self.metrics['events_processed'] += 1
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    def get_history(
        self,
        event_types: Optional[List[EventType]] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history."""
        with self._lock:
            events = self._event_history.copy()
        
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events[-limit:]
    
    def get_dead_letters(self, limit: int = 100) -> List[tuple]:
        """Get dead letter queue contents."""
        return self._dead_letter_queue[-limit:]
    
    def get_stats(self) -> Dict:
        """Get event bus statistics."""
        return {
            'subscriptions': len(self._subscriptions),
            'queue_size': self._event_queue.qsize(),
            'history_size': len(self._event_history),
            'dead_letters': len(self._dead_letter_queue),
            'metrics': self.metrics
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def publish(event_type: EventType, source: str, data: Dict = None, **kwargs) -> str:
    """Publish an event."""
    return get_event_bus().publish(event_type, source, data, **kwargs)


def subscribe(event_types: List[EventType], handler: Callable) -> str:
    """Subscribe to events."""
    return get_event_bus().subscribe(event_types, handler)


def start_event_bus():
    """Start the event bus."""
    get_event_bus().start()


def stop_event_bus():
    """Stop the event bus."""
    get_event_bus().stop()


# =============================================================================
# EVENT FACTORY FUNCTIONS
# =============================================================================

def emit_sensor_data_received(source: str, dma_id: str, sensor_id: str, readings: Dict):
    """Emit sensor data received event."""
    publish(
        EventType.SENSOR_DATA_RECEIVED,
        source,
        {
            'dma_id': dma_id,
            'sensor_id': sensor_id,
            'readings': readings
        }
    )


def emit_anomaly_detected(source: str, dma_id: str, anomaly_type: str, severity: str, details: Dict):
    """Emit anomaly detected event."""
    publish(
        EventType.ANOMALY_DETECTED,
        source,
        {
            'dma_id': dma_id,
            'anomaly_type': anomaly_type,
            'severity': severity,
            'details': details
        },
        priority=EventPriority.HIGH if severity == 'critical' else EventPriority.NORMAL
    )


def emit_alert_created(source: str, alert_id: str, dma_id: str, severity: str):
    """Emit alert created event."""
    publish(
        EventType.ALERT_CREATED,
        source,
        {
            'alert_id': alert_id,
            'dma_id': dma_id,
            'severity': severity
        },
        priority=EventPriority.HIGH if severity == 'critical' else EventPriority.NORMAL
    )


def emit_leak_confirmed(source: str, alert_id: str, dma_id: str, details: Dict):
    """Emit leak confirmed event."""
    publish(
        EventType.LEAK_CONFIRMED,
        source,
        {
            'alert_id': alert_id,
            'dma_id': dma_id,
            'details': details
        },
        priority=EventPriority.HIGH
    )


def emit_drift_detected(source: str, dma_id: str, drift_severity: str, details: Dict):
    """Emit drift detected event."""
    publish(
        EventType.DRIFT_DETECTED,
        source,
        {
            'dma_id': dma_id,
            'drift_severity': drift_severity,
            'details': details
        }
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("EVENT BUS DEMO")
    print("=" * 60)
    
    bus = EventBus()
    
    # Subscribe to events
    def on_sensor_data(event: Event):
        print(f"  Sensor data received: {event.data}")
    
    def on_anomaly(event: Event):
        print(f"  ⚠️ Anomaly detected: {event.data}")
    
    def on_all_events(event: Event):
        print(f"  [ALL] {event.event_type.value}: {event.source}")
    
    bus.subscribe([EventType.SENSOR_DATA_RECEIVED], on_sensor_data)
    bus.subscribe([EventType.ANOMALY_DETECTED], on_anomaly)
    bus.subscribe_all(on_all_events)
    
    # Start bus
    bus.start()
    
    # Publish events
    print("\nPublishing events...")
    
    bus.publish(
        EventType.SENSOR_DATA_RECEIVED,
        "esp32-001",
        {'pressure': 3.2, 'flow': 45.0}
    )
    
    time.sleep(0.5)
    
    bus.publish(
        EventType.ANOMALY_DETECTED,
        "anomaly_detector",
        {'type': 'pressure_drop', 'severity': 'high'},
        priority=EventPriority.HIGH
    )
    
    time.sleep(1)
    
    # Get stats
    print(f"\nStats: {bus.get_stats()}")
    
    # Stop
    bus.stop()
    print("\nDemo complete")
