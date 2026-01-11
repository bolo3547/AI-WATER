"""
AquaWatch Central Event Management (CEM)
========================================
TaKaDu-inspired intelligent event detection, correlation, and management system.
Provides automated event classification, root cause analysis, and workflow automation.

Key Features:
- Multi-source event correlation
- AI-powered event classification
- Automatic alert prioritization
- Event lifecycle management
- Root cause analysis
- Impact assessment
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import uuid
import json
import numpy as np
from collections import defaultdict


class EventType(Enum):
    """Types of water network events"""
    LEAK = "leak"
    BURST = "burst"
    PRESSURE_ANOMALY = "pressure_anomaly"
    FLOW_ANOMALY = "flow_anomaly"
    WATER_QUALITY = "water_quality"
    METER_ANOMALY = "meter_anomaly"
    EQUIPMENT_FAILURE = "equipment_failure"
    THEFT = "water_theft"
    DEMAND_ANOMALY = "demand_anomaly"
    COMMUNICATION_LOSS = "communication_loss"
    POWER_FAILURE = "power_failure"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"


class EventSeverity(Enum):
    """Event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventStatus(Enum):
    """Event lifecycle status"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_ALARM = "false_alarm"


@dataclass
class EventSource:
    """Source of an event detection"""
    source_type: str  # sensor, algorithm, manual, smart_meter
    source_id: str
    location: Optional[Tuple[float, float]] = None
    confidence: float = 0.8
    raw_data: Dict = field(default_factory=dict)


@dataclass
class Event:
    """Represents a water network event"""
    event_id: str
    event_type: EventType
    severity: EventSeverity
    status: EventStatus
    
    # Location
    zone_id: str
    asset_id: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Details
    title: str = ""
    description: str = ""
    sources: List[EventSource] = field(default_factory=list)
    
    # Impact assessment
    estimated_water_loss: float = 0.0  # m³/hour
    affected_customers: int = 0
    financial_impact: float = 0.0  # ZMW
    
    # Assignment
    assigned_to: Optional[str] = None
    team: Optional[str] = None
    
    # Related events
    parent_event_id: Optional[str] = None
    child_event_ids: List[str] = field(default_factory=list)
    correlated_events: List[str] = field(default_factory=list)
    
    # Actions and notes
    actions: List[Dict] = field(default_factory=list)
    notes: List[Dict] = field(default_factory=list)
    
    # Classification
    ai_classification: Optional[Dict] = None
    root_cause: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class EventRule:
    """Rule for automatic event classification and routing"""
    rule_id: str
    name: str
    description: str
    conditions: List[Dict]  # Conditions to match
    actions: List[Dict]  # Actions to take
    priority: int = 100  # Lower = higher priority
    enabled: bool = True


class EventClassifier:
    """AI-powered event classification engine"""
    
    def __init__(self):
        # Classification patterns
        self.patterns = {
            EventType.LEAK: {
                "pressure_drop": (0.2, 2.0),  # bar
                "flow_increase": (5, 50),  # %
                "duration_min": 30,  # minutes
                "night_flow_anomaly": True
            },
            EventType.BURST: {
                "pressure_drop": (2.0, 10.0),  # bar
                "flow_increase": (50, 500),  # %
                "duration_min": 5,
                "rapid_onset": True
            },
            EventType.PRESSURE_ANOMALY: {
                "pressure_deviation": (0.5, 5.0),  # bar from normal
                "duration_min": 15,
                "multiple_sensors": True
            },
            EventType.WATER_QUALITY: {
                "turbidity_increase": (1.0, 100.0),  # NTU
                "chlorine_deviation": (0.2, 2.0),  # mg/L
                "ph_deviation": (0.5, 3.0)
            },
            EventType.THEFT: {
                "unaccounted_flow": (10, 100),  # %
                "meter_bypass_pattern": True,
                "night_consumption_anomaly": True
            }
        }
        
        # Historical classification accuracy
        self.accuracy_by_type = defaultdict(lambda: {"correct": 0, "total": 0})
    
    def classify_event(self, sensor_data: Dict, historical_baseline: Dict) -> Dict:
        """
        Classify an event based on sensor data and historical patterns.
        
        Returns classification with confidence scores for each event type.
        """
        scores = {}
        
        for event_type, patterns in self.patterns.items():
            score = self._calculate_pattern_match(sensor_data, historical_baseline, patterns)
            scores[event_type.value] = score
        
        # Get best classification
        best_match = max(scores, key=scores.get)
        confidence = scores[best_match]
        
        # Determine severity based on magnitude and impact
        severity = self._determine_severity(sensor_data, best_match)
        
        return {
            "classification": best_match,
            "confidence": confidence,
            "severity": severity,
            "all_scores": scores,
            "features_used": list(sensor_data.keys()),
            "classification_time": datetime.now().isoformat()
        }
    
    def _calculate_pattern_match(self, sensor_data: Dict, baseline: Dict, patterns: Dict) -> float:
        """Calculate how well sensor data matches event patterns"""
        match_score = 0.0
        total_patterns = len(patterns)
        
        for pattern_key, pattern_value in patterns.items():
            if isinstance(pattern_value, tuple):
                # Range pattern
                min_val, max_val = pattern_value
                sensor_key = pattern_key.replace("_drop", "").replace("_increase", "").replace("_deviation", "")
                
                if sensor_key in sensor_data:
                    value = sensor_data[sensor_key]
                    if min_val <= abs(value) <= max_val:
                        match_score += 1.0
                    elif abs(value) < min_val:
                        match_score += abs(value) / min_val
            elif isinstance(pattern_value, bool):
                # Boolean pattern
                if pattern_key in sensor_data and sensor_data[pattern_key] == pattern_value:
                    match_score += 1.0
            elif isinstance(pattern_value, (int, float)):
                # Threshold pattern
                if pattern_key in sensor_data:
                    if sensor_data[pattern_key] >= pattern_value:
                        match_score += 1.0
        
        return match_score / total_patterns if total_patterns > 0 else 0.0
    
    def _determine_severity(self, sensor_data: Dict, event_type: str) -> EventSeverity:
        """Determine event severity based on data magnitude"""
        # Severity scoring factors
        severity_score = 0
        
        # Pressure drop severity
        if "pressure" in sensor_data:
            pressure_drop = sensor_data.get("pressure_drop", 0)
            if pressure_drop > 3.0:
                severity_score += 4
            elif pressure_drop > 1.5:
                severity_score += 3
            elif pressure_drop > 0.5:
                severity_score += 2
            else:
                severity_score += 1
        
        # Flow anomaly severity
        if "flow_increase" in sensor_data:
            flow_increase = sensor_data["flow_increase"]
            if flow_increase > 100:
                severity_score += 4
            elif flow_increase > 50:
                severity_score += 3
            elif flow_increase > 20:
                severity_score += 2
        
        # Water quality severity
        if event_type == "water_quality":
            severity_score += 3  # Always at least medium for quality issues
        
        # Determine final severity
        if severity_score >= 7:
            return EventSeverity.CRITICAL
        elif severity_score >= 5:
            return EventSeverity.HIGH
        elif severity_score >= 3:
            return EventSeverity.MEDIUM
        elif severity_score >= 1:
            return EventSeverity.LOW
        else:
            return EventSeverity.INFO
    
    def update_accuracy(self, event_type: str, was_correct: bool):
        """Update classification accuracy metrics"""
        self.accuracy_by_type[event_type]["total"] += 1
        if was_correct:
            self.accuracy_by_type[event_type]["correct"] += 1
    
    def get_accuracy_report(self) -> Dict:
        """Get classification accuracy report"""
        report = {}
        for event_type, stats in self.accuracy_by_type.items():
            if stats["total"] > 0:
                report[event_type] = {
                    "accuracy": stats["correct"] / stats["total"],
                    "total_events": stats["total"],
                    "correct_classifications": stats["correct"]
                }
        return report


class EventCorrelationEngine:
    """Correlates related events to identify root causes"""
    
    def __init__(self, time_window_minutes: int = 60, distance_threshold_km: float = 2.0):
        self.time_window = timedelta(minutes=time_window_minutes)
        self.distance_threshold = distance_threshold_km
        self.correlation_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[Dict]:
        """Initialize correlation rules"""
        return [
            {
                "name": "cascade_pressure_drop",
                "description": "Multiple pressure drops indicating main break",
                "event_types": [EventType.PRESSURE_ANOMALY],
                "min_events": 3,
                "max_time_spread": 15,  # minutes
                "result_type": EventType.BURST
            },
            {
                "name": "leak_cluster",
                "description": "Multiple leaks in same zone",
                "event_types": [EventType.LEAK],
                "min_events": 2,
                "max_distance": 0.5,  # km
                "result_type": EventType.BURST
            },
            {
                "name": "quality_contamination",
                "description": "Water quality issues spreading downstream",
                "event_types": [EventType.WATER_QUALITY],
                "min_events": 2,
                "pattern": "downstream_spread",
                "result_type": EventType.WATER_QUALITY
            },
            {
                "name": "meter_tampering_pattern",
                "description": "Multiple meter anomalies suggesting theft",
                "event_types": [EventType.METER_ANOMALY],
                "min_events": 3,
                "time_pattern": "night_hours",
                "result_type": EventType.THEFT
            }
        ]
    
    def find_correlations(self, new_event: Event, existing_events: List[Event]) -> List[Dict]:
        """Find events correlated with a new event"""
        correlations = []
        
        # Time-based correlation
        time_correlated = self._find_time_correlated(new_event, existing_events)
        if time_correlated:
            correlations.extend(time_correlated)
        
        # Location-based correlation
        if new_event.coordinates:
            location_correlated = self._find_location_correlated(new_event, existing_events)
            if location_correlated:
                correlations.extend(location_correlated)
        
        # Rule-based correlation
        rule_correlations = self._apply_correlation_rules(new_event, existing_events)
        if rule_correlations:
            correlations.extend(rule_correlations)
        
        return correlations
    
    def _find_time_correlated(self, new_event: Event, events: List[Event]) -> List[Dict]:
        """Find events within time window"""
        correlations = []
        
        for event in events:
            if event.event_id == new_event.event_id:
                continue
            
            time_diff = abs((new_event.detected_at - event.detected_at).total_seconds())
            
            if time_diff <= self.time_window.total_seconds():
                correlation_strength = 1 - (time_diff / self.time_window.total_seconds())
                
                if correlation_strength > 0.3:  # Threshold
                    correlations.append({
                        "event_id": event.event_id,
                        "correlation_type": "temporal",
                        "strength": correlation_strength,
                        "time_difference_seconds": time_diff
                    })
        
        return correlations
    
    def _find_location_correlated(self, new_event: Event, events: List[Event]) -> List[Dict]:
        """Find events within distance threshold"""
        correlations = []
        
        if not new_event.coordinates:
            return correlations
        
        for event in events:
            if event.event_id == new_event.event_id or not event.coordinates:
                continue
            
            distance = self._calculate_distance(new_event.coordinates, event.coordinates)
            
            if distance <= self.distance_threshold:
                correlation_strength = 1 - (distance / self.distance_threshold)
                
                if correlation_strength > 0.3:
                    correlations.append({
                        "event_id": event.event_id,
                        "correlation_type": "spatial",
                        "strength": correlation_strength,
                        "distance_km": distance
                    })
        
        return correlations
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in km"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _apply_correlation_rules(self, new_event: Event, events: List[Event]) -> List[Dict]:
        """Apply correlation rules to find patterns"""
        correlations = []
        
        for rule in self.correlation_rules:
            # Check if new event matches rule event types
            if new_event.event_type not in rule["event_types"]:
                continue
            
            # Find matching events
            matching_events = [
                e for e in events
                if e.event_type in rule["event_types"]
                and e.event_id != new_event.event_id
                and e.status != EventStatus.CLOSED
            ]
            
            if len(matching_events) + 1 >= rule.get("min_events", 2):
                correlations.append({
                    "rule_name": rule["name"],
                    "correlation_type": "rule_based",
                    "description": rule["description"],
                    "event_ids": [e.event_id for e in matching_events],
                    "suggested_type": rule["result_type"].value,
                    "strength": min(len(matching_events) / rule.get("min_events", 2), 1.0)
                })
        
        return correlations


class CentralEventManager:
    """
    Central Event Management (CEM) system.
    Manages the complete lifecycle of water network events.
    """
    
    def __init__(self):
        self.events: Dict[str, Event] = {}
        self.classifier = EventClassifier()
        self.correlation_engine = EventCorrelationEngine()
        self.rules: List[EventRule] = []
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_status": defaultdict(int),
            "avg_resolution_time": timedelta(0),
            "false_alarm_rate": 0.0
        }
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default event routing rules"""
        self.rules = [
            EventRule(
                rule_id="R001",
                name="Critical Alert Escalation",
                description="Escalate critical events immediately",
                conditions=[{"severity": "critical"}],
                actions=[
                    {"type": "notify", "channels": ["sms", "call", "email"]},
                    {"type": "assign", "team": "emergency_response"},
                    {"type": "escalate", "to": "operations_manager"}
                ],
                priority=1
            ),
            EventRule(
                rule_id="R002",
                name="Burst Pipe Response",
                description="Auto-assign burst pipe events",
                conditions=[{"event_type": "burst"}],
                actions=[
                    {"type": "notify", "channels": ["sms", "push"]},
                    {"type": "assign", "team": "repair_crew"},
                    {"type": "create_work_order", "priority": "urgent"}
                ],
                priority=2
            ),
            EventRule(
                rule_id="R003",
                name="Water Quality Alert",
                description="Handle water quality events",
                conditions=[{"event_type": "water_quality"}],
                actions=[
                    {"type": "notify", "channels": ["sms", "email"]},
                    {"type": "assign", "team": "quality_team"},
                    {"type": "notify_regulators", "if_severity": ["critical", "high"]}
                ],
                priority=3
            ),
            EventRule(
                rule_id="R004",
                name="Night Hour Events",
                description="Handle events detected during night",
                conditions=[{"time_range": "22:00-06:00"}],
                actions=[
                    {"type": "notify", "channels": ["sms", "call"]},
                    {"type": "assign", "team": "on_call_team"}
                ],
                priority=10
            )
        ]
    
    def create_event(
        self,
        event_type: EventType,
        zone_id: str,
        sensor_data: Dict,
        source: EventSource,
        auto_classify: bool = True
    ) -> Event:
        """
        Create a new event from sensor data or manual input.
        
        Args:
            event_type: Type of event (can be auto-classified)
            zone_id: Zone where event occurred
            sensor_data: Raw sensor readings
            source: Source of the event detection
            auto_classify: Whether to use AI classification
        
        Returns:
            Created Event object
        """
        event_id = f"EVT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # Auto-classify if requested
        if auto_classify:
            classification = self.classifier.classify_event(sensor_data, {})
            event_type = EventType(classification["classification"])
            severity = classification["severity"]
            ai_classification = classification
        else:
            severity = EventSeverity.MEDIUM
            ai_classification = None
        
        # Extract location if available
        coordinates = None
        if "latitude" in sensor_data and "longitude" in sensor_data:
            coordinates = (sensor_data["latitude"], sensor_data["longitude"])
        
        # Estimate impact
        water_loss = self._estimate_water_loss(event_type, sensor_data)
        affected_customers = self._estimate_affected_customers(zone_id, event_type)
        financial_impact = water_loss * 24 * 5.50  # Daily cost in ZMW
        
        # Create event
        event = Event(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            status=EventStatus.NEW,
            zone_id=zone_id,
            coordinates=coordinates,
            title=self._generate_title(event_type, zone_id),
            description=self._generate_description(event_type, sensor_data),
            sources=[source],
            estimated_water_loss=water_loss,
            affected_customers=affected_customers,
            financial_impact=financial_impact,
            ai_classification=ai_classification
        )
        
        # Find correlations with existing events
        correlations = self.correlation_engine.find_correlations(
            event, list(self.events.values())
        )
        
        for corr in correlations:
            if "event_id" in corr:
                event.correlated_events.append(corr["event_id"])
        
        # Store event
        self.events[event_id] = event
        
        # Update statistics
        self._update_stats(event)
        
        # Apply rules
        self._apply_rules(event)
        
        # Notify subscribers
        self._notify_subscribers("new_event", event)
        
        return event
    
    def _generate_title(self, event_type: EventType, zone_id: str) -> str:
        """Generate event title"""
        type_titles = {
            EventType.LEAK: "Leak Detected",
            EventType.BURST: "Pipe Burst",
            EventType.PRESSURE_ANOMALY: "Pressure Anomaly",
            EventType.FLOW_ANOMALY: "Flow Anomaly",
            EventType.WATER_QUALITY: "Water Quality Alert",
            EventType.METER_ANOMALY: "Meter Anomaly",
            EventType.EQUIPMENT_FAILURE: "Equipment Failure",
            EventType.THEFT: "Suspected Water Theft",
            EventType.DEMAND_ANOMALY: "Unusual Demand Pattern",
            EventType.COMMUNICATION_LOSS: "Sensor Communication Loss",
            EventType.POWER_FAILURE: "Power Failure Detected"
        }
        return f"{type_titles.get(event_type, 'Event')} in {zone_id}"
    
    def _generate_description(self, event_type: EventType, sensor_data: Dict) -> str:
        """Generate event description from sensor data"""
        descriptions = []
        
        if "pressure" in sensor_data:
            descriptions.append(f"Pressure: {sensor_data['pressure']:.2f} bar")
        if "pressure_drop" in sensor_data:
            descriptions.append(f"Pressure drop: {sensor_data['pressure_drop']:.2f} bar")
        if "flow_rate" in sensor_data:
            descriptions.append(f"Flow rate: {sensor_data['flow_rate']:.1f} L/s")
        if "flow_increase" in sensor_data:
            descriptions.append(f"Flow increase: {sensor_data['flow_increase']:.1f}%")
        if "turbidity" in sensor_data:
            descriptions.append(f"Turbidity: {sensor_data['turbidity']:.2f} NTU")
        
        return ". ".join(descriptions) if descriptions else "Event detected by monitoring system."
    
    def _estimate_water_loss(self, event_type: EventType, sensor_data: Dict) -> float:
        """Estimate water loss in m³/hour"""
        base_losses = {
            EventType.LEAK: 2.0,
            EventType.BURST: 20.0,
            EventType.THEFT: 1.0,
            EventType.METER_ANOMALY: 0.5
        }
        
        base = base_losses.get(event_type, 0.0)
        
        # Adjust based on flow data
        if "flow_increase" in sensor_data:
            base *= (1 + sensor_data["flow_increase"] / 100)
        
        return base
    
    def _estimate_affected_customers(self, zone_id: str, event_type: EventType) -> int:
        """Estimate number of affected customers"""
        # Simplified estimation - in production, this would query customer database
        zone_customers = {
            "ZONE_CBD": 5000,
            "ZONE_KABULONGA": 3500,
            "ZONE_WOODLANDS": 4000,
            "ZONE_KABWATA": 6000,
            "ZONE_MATERO": 8000,
            "ZONE_INDUSTRIAL": 200
        }
        
        base_customers = zone_customers.get(zone_id, 2000)
        
        # Impact factor by event type
        impact_factors = {
            EventType.BURST: 0.5,
            EventType.PRESSURE_ANOMALY: 0.3,
            EventType.WATER_QUALITY: 0.8,
            EventType.LEAK: 0.1
        }
        
        factor = impact_factors.get(event_type, 0.2)
        
        return int(base_customers * factor)
    
    def _apply_rules(self, event: Event):
        """Apply routing rules to event"""
        applicable_rules = []
        
        for rule in sorted(self.rules, key=lambda r: r.priority):
            if not rule.enabled:
                continue
            
            if self._matches_conditions(event, rule.conditions):
                applicable_rules.append(rule)
        
        # Execute actions for matching rules
        for rule in applicable_rules:
            for action in rule.actions:
                self._execute_action(event, action)
            
            event.actions.append({
                "type": "rule_applied",
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "timestamp": datetime.now().isoformat()
            })
    
    def _matches_conditions(self, event: Event, conditions: List[Dict]) -> bool:
        """Check if event matches rule conditions"""
        for condition in conditions:
            for key, value in condition.items():
                if key == "severity" and event.severity.value != value:
                    return False
                if key == "event_type" and event.event_type.value != value:
                    return False
                if key == "zone_id" and event.zone_id != value:
                    return False
                if key == "time_range":
                    start, end = value.split("-")
                    current_hour = datetime.now().hour
                    start_hour = int(start.split(":")[0])
                    end_hour = int(end.split(":")[0])
                    
                    if start_hour > end_hour:  # Overnight range
                        if not (current_hour >= start_hour or current_hour < end_hour):
                            return False
                    else:
                        if not (start_hour <= current_hour < end_hour):
                            return False
        
        return True
    
    def _execute_action(self, event: Event, action: Dict):
        """Execute rule action"""
        action_type = action.get("type")
        
        if action_type == "notify":
            channels = action.get("channels", [])
            event.actions.append({
                "type": "notification_sent",
                "channels": channels,
                "timestamp": datetime.now().isoformat()
            })
        
        elif action_type == "assign":
            event.team = action.get("team")
            event.actions.append({
                "type": "assigned",
                "team": event.team,
                "timestamp": datetime.now().isoformat()
            })
        
        elif action_type == "escalate":
            event.actions.append({
                "type": "escalated",
                "to": action.get("to"),
                "timestamp": datetime.now().isoformat()
            })
        
        elif action_type == "create_work_order":
            event.actions.append({
                "type": "work_order_created",
                "priority": action.get("priority", "normal"),
                "timestamp": datetime.now().isoformat()
            })
    
    def _update_stats(self, event: Event):
        """Update event statistics"""
        self.stats["total_events"] += 1
        self.stats["events_by_type"][event.event_type.value] += 1
        self.stats["events_by_severity"][event.severity.value] += 1
        self.stats["events_by_status"][event.status.value] += 1
    
    def _notify_subscribers(self, event_name: str, data: Any):
        """Notify event subscribers"""
        for callback in self.subscribers.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Subscriber notification failed: {e}")
    
    def subscribe(self, event_name: str, callback: Callable):
        """Subscribe to event notifications"""
        self.subscribers[event_name].append(callback)
    
    def acknowledge_event(self, event_id: str, user_id: str, notes: str = "") -> Event:
        """Acknowledge an event"""
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        event.status = EventStatus.ACKNOWLEDGED
        event.acknowledged_at = datetime.now()
        event.assigned_to = user_id
        
        if notes:
            event.notes.append({
                "user": user_id,
                "text": notes,
                "timestamp": datetime.now().isoformat()
            })
        
        event.actions.append({
            "type": "acknowledged",
            "user": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        self._notify_subscribers("event_acknowledged", event)
        
        return event
    
    def update_event_status(self, event_id: str, status: EventStatus, user_id: str, notes: str = "") -> Event:
        """Update event status"""
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        old_status = event.status
        event.status = status
        
        if status == EventStatus.RESOLVED:
            event.resolved_at = datetime.now()
        
        if notes:
            event.notes.append({
                "user": user_id,
                "text": notes,
                "timestamp": datetime.now().isoformat()
            })
        
        event.actions.append({
            "type": "status_change",
            "from": old_status.value,
            "to": status.value,
            "user": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update stats
        self.stats["events_by_status"][old_status.value] -= 1
        self.stats["events_by_status"][status.value] += 1
        
        self._notify_subscribers("event_status_changed", event)
        
        return event
    
    def get_active_events(self, zone_id: Optional[str] = None) -> List[Event]:
        """Get all active (non-closed) events"""
        active_statuses = [
            EventStatus.NEW,
            EventStatus.ACKNOWLEDGED,
            EventStatus.INVESTIGATING,
            EventStatus.IN_PROGRESS
        ]
        
        events = [
            e for e in self.events.values()
            if e.status in active_statuses
        ]
        
        if zone_id:
            events = [e for e in events if e.zone_id == zone_id]
        
        return sorted(events, key=lambda e: (
            -["critical", "high", "medium", "low", "info"].index(e.severity.value),
            e.detected_at
        ))
    
    def get_event_timeline(self, event_id: str) -> List[Dict]:
        """Get complete timeline for an event"""
        if event_id not in self.events:
            return []
        
        event = self.events[event_id]
        timeline = []
        
        # Add detection
        timeline.append({
            "timestamp": event.detected_at.isoformat(),
            "type": "detected",
            "description": f"Event detected: {event.title}"
        })
        
        # Add all actions
        for action in event.actions:
            timeline.append({
                "timestamp": action.get("timestamp"),
                "type": action.get("type"),
                "description": self._format_action(action)
            })
        
        # Add notes
        for note in event.notes:
            timeline.append({
                "timestamp": note.get("timestamp"),
                "type": "note",
                "description": f"Note by {note.get('user')}: {note.get('text')}"
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
    
    def _format_action(self, action: Dict) -> str:
        """Format action for display"""
        action_type = action.get("type")
        
        if action_type == "acknowledged":
            return f"Acknowledged by {action.get('user')}"
        elif action_type == "status_change":
            return f"Status changed from {action.get('from')} to {action.get('to')}"
        elif action_type == "assigned":
            return f"Assigned to {action.get('team')}"
        elif action_type == "escalated":
            return f"Escalated to {action.get('to')}"
        elif action_type == "notification_sent":
            return f"Notifications sent via {', '.join(action.get('channels', []))}"
        elif action_type == "work_order_created":
            return f"Work order created with {action.get('priority')} priority"
        else:
            return action_type
    
    def get_dashboard_metrics(self) -> Dict:
        """Get metrics for dashboard display"""
        active_events = self.get_active_events()
        
        # Calculate response times
        response_times = []
        for event in self.events.values():
            if event.acknowledged_at and event.detected_at:
                response_time = (event.acknowledged_at - event.detected_at).total_seconds() / 60
                response_times.append(response_time)
        
        # Calculate resolution times
        resolution_times = []
        for event in self.events.values():
            if event.resolved_at and event.detected_at:
                resolution_time = (event.resolved_at - event.detected_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
        
        return {
            "active_events": len(active_events),
            "critical_events": len([e for e in active_events if e.severity == EventSeverity.CRITICAL]),
            "events_today": len([
                e for e in self.events.values()
                if e.detected_at.date() == datetime.now().date()
            ]),
            "total_water_loss_m3_hour": sum(e.estimated_water_loss for e in active_events),
            "total_affected_customers": sum(e.affected_customers for e in active_events),
            "avg_response_time_min": np.mean(response_times) if response_times else 0,
            "avg_resolution_time_hours": np.mean(resolution_times) if resolution_times else 0,
            "events_by_type": dict(self.stats["events_by_type"]),
            "events_by_severity": dict(self.stats["events_by_severity"]),
            "classification_accuracy": self.classifier.get_accuracy_report()
        }


# Global instance
event_manager = CentralEventManager()


def get_event_manager() -> CentralEventManager:
    """Get the global event manager instance"""
    return event_manager


if __name__ == "__main__":
    # Demo
    cem = CentralEventManager()
    
    print("=" * 60)
    print("AquaWatch Central Event Management")
    print("=" * 60)
    
    # Create sample events
    source = EventSource(
        source_type="sensor",
        source_id="SENSOR_CBD_001",
        location=(-15.4167, 28.2833),
        confidence=0.85
    )
    
    # Simulate leak detection
    leak_data = {
        "pressure": 2.8,
        "pressure_drop": 0.7,
        "flow_rate": 45.0,
        "flow_increase": 25.0,
        "latitude": -15.4167,
        "longitude": 28.2833
    }
    
    event1 = cem.create_event(
        event_type=EventType.LEAK,
        zone_id="ZONE_CBD",
        sensor_data=leak_data,
        source=source,
        auto_classify=True
    )
    
    print(f"\nEvent Created:")
    print(f"  ID: {event1.event_id}")
    print(f"  Type: {event1.event_type.value}")
    print(f"  Severity: {event1.severity.value}")
    print(f"  Title: {event1.title}")
    print(f"  Estimated Water Loss: {event1.estimated_water_loss:.1f} m³/hour")
    print(f"  Affected Customers: {event1.affected_customers}")
    
    # Simulate burst
    burst_data = {
        "pressure": 0.5,
        "pressure_drop": 3.5,
        "flow_rate": 150.0,
        "flow_increase": 200.0,
        "latitude": -15.4292,
        "longitude": 28.2708
    }
    
    event2 = cem.create_event(
        event_type=EventType.BURST,
        zone_id="ZONE_KAMWALA",
        sensor_data=burst_data,
        source=source,
        auto_classify=True
    )
    
    print(f"\nBurst Event Created:")
    print(f"  ID: {event2.event_id}")
    print(f"  Severity: {event2.severity.value}")
    print(f"  Financial Impact: ZMW {event2.financial_impact:,.2f}/day")
    
    # Get dashboard metrics
    metrics = cem.get_dashboard_metrics()
    print(f"\nDashboard Metrics:")
    print(f"  Active Events: {metrics['active_events']}")
    print(f"  Critical Events: {metrics['critical_events']}")
    print(f"  Total Water Loss: {metrics['total_water_loss_m3_hour']:.1f} m³/hour")
    print(f"  Affected Customers: {metrics['total_affected_customers']}")
