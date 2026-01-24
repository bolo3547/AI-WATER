"""
AquaWatch NRW v3.0 - Real Loss Data Models
==========================================

Production-grade data models for the Real Losses Module.

Tables:
- sensor_readings: Time-series sensor data (Timescale hypertable)
- dma_baselines: Baseline MNF, flow, pressure per DMA
- real_loss_incidents: Leak events with classification
- work_orders: Field service management
- incident_timeline: Audit trail for incidents
- audit_logs: System-wide audit logging

All tables include tenant_id for multi-tenant isolation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class SensorType(Enum):
    """Types of sensors in the network"""
    FLOW_METER = "flow_meter"
    PRESSURE_SENSOR = "pressure_sensor"
    LEVEL_SENSOR = "level_sensor"
    ACOUSTIC_LOGGER = "acoustic_logger"
    AMI_METER = "ami_meter"


class SensorStatus(Enum):
    """Sensor operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    STALE = "stale"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class LeakType(Enum):
    """IWA Real Loss Classification"""
    MAIN_LEAK = "main_leak"                     # Type A: Transmission/Distribution
    SERVICE_CONNECTION = "service_connection"   # Type B: Service connection leaks
    STORAGE_OVERFLOW = "storage_overflow"       # Type C: Tank/reservoir leaks
    BURST_PIPE = "burst_pipe"                   # Catastrophic burst
    JOINT_FAILURE = "joint_failure"             # Joint/connection failure
    UNKNOWN = "unknown"


class IncidentSeverity(Enum):
    """Incident severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Real loss incident lifecycle"""
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    CONFIRMED = "confirmed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class WorkOrderStatus(Enum):
    """Work order lifecycle"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class WorkOrderPriority(Enum):
    """Work order priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class DetectionMethod(Enum):
    """How the leak was detected"""
    MNF_ANALYSIS = "mnf_analysis"
    PRESSURE_DROP = "pressure_drop"
    FLOW_SPIKE = "flow_spike"
    PRESSURE_OSCILLATION = "pressure_oscillation"
    AI_ANOMALY = "ai_anomaly"
    ACOUSTIC_CORRELATION = "acoustic_correlation"
    SATELLITE_DETECTION = "satellite_detection"
    CUSTOMER_REPORT = "customer_report"
    FIELD_INSPECTION = "field_inspection"
    COMBINED_SIGNALS = "combined_signals"


# =============================================================================
# SENSOR READING MODEL
# =============================================================================

@dataclass
class SensorReading:
    """
    Time-series sensor reading.
    
    Designed for Timescale hypertable with tenant partitioning.
    """
    reading_id: str
    tenant_id: str
    sensor_id: str
    dma_id: str
    
    # Timestamp (partitioning key for Timescale)
    timestamp: datetime
    
    # Sensor type
    sensor_type: SensorType
    
    # Readings (only relevant field populated based on type)
    flow_m3_hour: Optional[float] = None
    pressure_bar: Optional[float] = None
    level_m: Optional[float] = None
    acoustic_db: Optional[float] = None
    
    # Location
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Data quality
    quality_score: float = 1.0  # 0-1
    is_valid: bool = True
    anomaly_flag: bool = False
    
    # Raw value (for debugging)
    raw_value: Optional[float] = None
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        sensor_id: str,
        dma_id: str,
        sensor_type: SensorType,
        timestamp: Optional[datetime] = None,
        **kwargs
    ) -> 'SensorReading':
        """Factory method to create a sensor reading."""
        return cls(
            reading_id=f"sr_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            sensor_id=sensor_id,
            dma_id=dma_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            sensor_type=sensor_type,
            **kwargs
        )


# =============================================================================
# DMA BASELINE MODEL
# =============================================================================

@dataclass
class DMABaseline:
    """
    Baseline metrics for a DMA.
    
    Used for anomaly detection and MNF analysis.
    """
    baseline_id: str
    tenant_id: str
    dma_id: str
    
    # MNF baselines (02:00-04:00 window)
    mnf_baseline_m3_hour: float = 0.0
    mnf_std_dev: float = 0.0
    mnf_warning_threshold: float = 0.0
    mnf_critical_threshold: float = 0.0
    
    # Flow baselines
    flow_baseline_m3_hour: float = 0.0
    flow_std_dev: float = 0.0
    flow_max_normal: float = 0.0
    flow_min_normal: float = 0.0
    
    # Pressure baselines (per zone average)
    pressure_baseline_bar: float = 3.0
    pressure_std_dev: float = 0.2
    pressure_min_acceptable: float = 1.5
    pressure_max_acceptable: float = 6.0
    
    # Legitimate Night Use estimate
    estimated_lnu_m3_hour: float = 0.0
    
    # Background leakage (unavoidable small leaks)
    background_leakage_m3_hour: float = 0.0
    
    # Computation metadata
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sample_count: int = 0
    training_days: int = 14
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
    
    # Quality indicators
    data_completeness_pct: float = 0.0
    is_valid: bool = True
    needs_retraining: bool = False
    
    @classmethod
    def create(cls, tenant_id: str, dma_id: str, **kwargs) -> 'DMABaseline':
        """Factory method to create a DMA baseline."""
        return cls(
            baseline_id=f"bl_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            dma_id=dma_id,
            **kwargs
        )


# =============================================================================
# REAL LOSS INCIDENT MODEL
# =============================================================================

@dataclass
class RealLossIncident:
    """
    Real loss incident representing a detected leak.
    
    Full lifecycle from detection to resolution.
    """
    incident_id: str
    tenant_id: str
    dma_id: str
    
    # Detection info
    detected_at: datetime
    detection_method: DetectionMethod
    
    # Classification
    leak_type: LeakType
    severity: IncidentSeverity
    confidence: float  # 0-1
    
    # Priority scoring (locked formula)
    priority_score: float = 0.0
    
    # Location estimate
    estimated_lat: Optional[float] = None
    estimated_lng: Optional[float] = None
    location_radius_m: float = 100.0  # Uncertainty radius
    zone_hint: str = ""
    address: str = ""
    
    # Detection signals
    mnf_current: Optional[float] = None
    mnf_baseline: Optional[float] = None
    mnf_deviation_pct: Optional[float] = None
    pressure_drop_bar: Optional[float] = None
    flow_increase_m3_hour: Optional[float] = None
    
    # Impact estimation
    estimated_loss_m3_hour: float = 0.0
    estimated_loss_m3_day: float = 0.0
    estimated_cost_zmw_day: float = 0.0
    affected_customers: int = 0
    
    # Status and lifecycle
    status: IncidentStatus = IncidentStatus.DETECTED
    
    # Acknowledgment
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    # Confirmation
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    actual_leak_type: Optional[LeakType] = None  # After field verification
    
    # Resolution
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""
    repair_method: str = ""
    repair_cost_zmw: float = 0.0
    
    # Verification
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    actual_loss_m3: Optional[float] = None  # Measured actual loss
    
    # Closure
    closed_at: Optional[datetime] = None
    
    # Work order link
    work_order_id: Optional[str] = None
    
    # AI explanation
    ai_signals: List[str] = field(default_factory=list)
    ai_explanation: str = ""
    
    # Persistence tracking
    consecutive_nights: int = 0
    is_persistent: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        dma_id: str,
        leak_type: LeakType,
        severity: IncidentSeverity,
        detection_method: DetectionMethod,
        confidence: float,
        **kwargs
    ) -> 'RealLossIncident':
        """Factory method to create an incident."""
        now = datetime.now(timezone.utc)
        return cls(
            incident_id=f"inc_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            dma_id=dma_id,
            detected_at=now,
            detection_method=detection_method,
            leak_type=leak_type,
            severity=severity,
            confidence=confidence,
            created_at=now,
            updated_at=now,
            **kwargs
        )
    
    def calculate_priority_score(
        self,
        leak_probability: float,
        criticality_factor: float = 1.0
    ) -> float:
        """
        Calculate priority using the LOCKED FORMULA.
        
        Priority = (leak_probability × estimated_loss_m3_day) × criticality_factor × confidence_factor
        """
        self.priority_score = (
            leak_probability * self.estimated_loss_m3_day *
            criticality_factor * self.confidence
        )
        return self.priority_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'incident_id': self.incident_id,
            'tenant_id': self.tenant_id,
            'dma_id': self.dma_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'detection_method': self.detection_method.value if self.detection_method else None,
            'leak_type': self.leak_type.value if self.leak_type else None,
            'severity': self.severity.value if self.severity else None,
            'confidence': self.confidence,
            'priority_score': self.priority_score,
            'estimated_lat': self.estimated_lat,
            'estimated_lng': self.estimated_lng,
            'location_radius_m': self.location_radius_m,
            'zone_hint': self.zone_hint,
            'address': self.address,
            'mnf_current': self.mnf_current,
            'mnf_baseline': self.mnf_baseline,
            'mnf_deviation_pct': self.mnf_deviation_pct,
            'pressure_drop_bar': self.pressure_drop_bar,
            'flow_increase_m3_hour': self.flow_increase_m3_hour,
            'estimated_loss_m3_hour': self.estimated_loss_m3_hour,
            'estimated_loss_m3_day': self.estimated_loss_m3_day,
            'estimated_cost_zmw_day': self.estimated_cost_zmw_day,
            'affected_customers': self.affected_customers,
            'status': self.status.value if self.status else None,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'work_order_id': self.work_order_id,
            'ai_signals': self.ai_signals,
            'ai_explanation': self.ai_explanation,
            'consecutive_nights': self.consecutive_nights,
            'is_persistent': self.is_persistent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# WORK ORDER MODEL
# =============================================================================

@dataclass
class WorkOrder:
    """
    Field work order for leak investigation/repair.
    """
    work_order_id: str
    tenant_id: str
    dma_id: str
    
    # Link to incident
    incident_id: Optional[str] = None
    
    # Work order type
    work_type: str = "leak_repair"  # leak_repair, inspection, maintenance, etc.
    
    # Priority and scheduling
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    scheduled_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Location
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    address: str = ""
    zone_hint: str = ""
    
    # Assignment
    assigned_to: Optional[str] = None  # Technician user ID
    assigned_team: Optional[str] = None  # Team/crew name
    assigned_at: Optional[datetime] = None
    
    # Description
    title: str = ""
    description: str = ""
    instructions: str = ""
    
    # Status tracking
    status: WorkOrderStatus = WorkOrderStatus.PENDING
    
    # Timeline
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Results
    completion_notes: str = ""
    repair_method: str = ""
    materials_used: List[str] = field(default_factory=list)
    labor_hours: float = 0.0
    repair_cost_zmw: float = 0.0
    
    # Photos/attachments
    attachments: List[str] = field(default_factory=list)
    
    # Verification
    verified_by: Optional[str] = None
    verification_notes: str = ""
    leak_confirmed: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    
    # SLA tracking
    sla_due_at: Optional[datetime] = None
    sla_breached: bool = False
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        dma_id: str,
        title: str,
        incident_id: Optional[str] = None,
        **kwargs
    ) -> 'WorkOrder':
        """Factory method to create a work order."""
        now = datetime.now(timezone.utc)
        return cls(
            work_order_id=f"wo_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            dma_id=dma_id,
            incident_id=incident_id,
            title=title,
            created_at=now,
            updated_at=now,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'work_order_id': self.work_order_id,
            'tenant_id': self.tenant_id,
            'dma_id': self.dma_id,
            'incident_id': self.incident_id,
            'work_type': self.work_type,
            'priority': self.priority.value if self.priority else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'location_lat': self.location_lat,
            'location_lng': self.location_lng,
            'address': self.address,
            'zone_hint': self.zone_hint,
            'assigned_to': self.assigned_to,
            'assigned_team': self.assigned_team,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'title': self.title,
            'description': self.description,
            'instructions': self.instructions,
            'status': self.status.value if self.status else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'completion_notes': self.completion_notes,
            'repair_method': self.repair_method,
            'materials_used': self.materials_used,
            'labor_hours': self.labor_hours,
            'repair_cost_zmw': self.repair_cost_zmw,
            'leak_confirmed': self.leak_confirmed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sla_due_at': self.sla_due_at.isoformat() if self.sla_due_at else None,
            'sla_breached': self.sla_breached,
        }


# =============================================================================
# INCIDENT TIMELINE MODEL
# =============================================================================

@dataclass
class IncidentTimelineEntry:
    """
    Audit trail entry for incident lifecycle.
    """
    entry_id: str
    tenant_id: str
    incident_id: str
    
    # Event details
    event_type: str  # status_change, note_added, assigned, etc.
    timestamp: datetime
    
    # Actor
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_type: str = "user"  # user, system, ai
    
    # Change details
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        incident_id: str,
        event_type: str,
        description: str,
        actor_id: Optional[str] = None,
        **kwargs
    ) -> 'IncidentTimelineEntry':
        """Factory method to create a timeline entry."""
        return cls(
            entry_id=f"tle_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            incident_id=incident_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            description=description,
            **kwargs
        )


# =============================================================================
# TENANT CONFIGURATION MODEL
# =============================================================================

@dataclass
class TenantConfig:
    """
    Per-tenant configuration for real loss calculations.
    """
    tenant_id: str
    
    # Water tariff
    tariff_zmw_per_m3: float = 15.0  # Zambian Kwacha per cubic meter
    
    # Detection thresholds
    mnf_warning_deviation_pct: float = 20.0
    mnf_critical_deviation_pct: float = 50.0
    pressure_drop_warning_bar: float = 0.5
    pressure_drop_critical_bar: float = 1.0
    flow_spike_warning_pct: float = 30.0
    flow_spike_critical_pct: float = 100.0
    
    # Data freshness
    data_stale_minutes: int = 3
    sensor_offline_minutes: int = 15
    
    # Work order automation
    auto_create_work_order: bool = True
    auto_create_threshold: str = "high"  # Severity threshold for auto-creation
    
    # SLA targets
    sla_critical_hours: int = 4
    sla_high_hours: int = 12
    sla_medium_hours: int = 48
    sla_low_hours: int = 168  # 7 days
    
    # Notification settings
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_email_list: List[str] = field(default_factory=list)
    notify_sms_list: List[str] = field(default_factory=list)
    
    # MNF window (local time)
    mnf_window_start_hour: int = 2  # 02:00
    mnf_window_end_hour: int = 4    # 04:00
    
    # Timezone
    timezone: str = "Africa/Lusaka"
    
    @classmethod
    def default(cls, tenant_id: str) -> 'TenantConfig':
        """Create default configuration for a tenant."""
        return cls(tenant_id=tenant_id)


# =============================================================================
# MNF TREND POINT MODEL
# =============================================================================

@dataclass
class MNFTrendPoint:
    """Historical MNF data point for trend charts."""
    date: datetime
    tenant_id: str
    dma_id: str
    
    mnf_m3_hour: float
    baseline_m3_hour: float
    deviation_pct: float
    deviation_m3_hour: float
    
    has_anomaly: bool = False
    anomaly_severity: Optional[str] = None
    incident_id: Optional[str] = None
    
    # Components
    estimated_lnu: float = 0.0
    background_leakage: float = 0.0
    excess_leakage: float = 0.0


# =============================================================================
# SYSTEM LIVE STATUS MODEL
# =============================================================================

@dataclass
class SystemLiveStatus:
    """
    Real-time system status for a tenant.
    
    Endpoint: GET /tenants/{tenant_id}/system/live-status
    """
    tenant_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Connection status
    mqtt_connected: bool = False
    api_healthy: bool = True
    database_connected: bool = True
    
    # Sensor counts
    active_sensors: int = 0
    offline_sensors: int = 0
    stale_sensors: int = 0
    total_sensors: int = 0
    
    # Last data received
    last_sensor_seen_at: Optional[datetime] = None
    last_flow_reading_at: Optional[datetime] = None
    last_pressure_reading_at: Optional[datetime] = None
    
    # Data freshness
    data_fresh: bool = False
    data_age_seconds: Optional[int] = None
    
    # Processing status
    anomaly_detection_running: bool = False
    last_mnf_analysis_at: Optional[datetime] = None
    
    # Active issues
    active_incidents: int = 0
    pending_work_orders: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'tenant_id': self.tenant_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'mqtt_connected': self.mqtt_connected,
            'api_healthy': self.api_healthy,
            'database_connected': self.database_connected,
            'active_sensors': self.active_sensors,
            'offline_sensors': self.offline_sensors,
            'stale_sensors': self.stale_sensors,
            'total_sensors': self.total_sensors,
            'last_sensor_seen_at': self.last_sensor_seen_at.isoformat() if self.last_sensor_seen_at else None,
            'last_flow_reading_at': self.last_flow_reading_at.isoformat() if self.last_flow_reading_at else None,
            'last_pressure_reading_at': self.last_pressure_reading_at.isoformat() if self.last_pressure_reading_at else None,
            'data_fresh': self.data_fresh,
            'data_age_seconds': self.data_age_seconds,
            'anomaly_detection_running': self.anomaly_detection_running,
            'last_mnf_analysis_at': self.last_mnf_analysis_at.isoformat() if self.last_mnf_analysis_at else None,
            'active_incidents': self.active_incidents,
            'pending_work_orders': self.pending_work_orders,
        }


# =============================================================================
# DISPATCH SUGGESTION MODEL
# =============================================================================

@dataclass
class DispatchSuggestion:
    """
    AI-generated dispatch suggestion.
    """
    suggestion_id: str
    tenant_id: str
    incident_id: str
    
    # Suggested team/technician
    suggested_team: str = ""
    suggested_technician_id: Optional[str] = None
    suggested_technician_name: str = ""
    
    # Reasoning
    reason: str = ""
    factors: List[str] = field(default_factory=list)
    
    # Estimated response
    estimated_travel_minutes: int = 0
    estimated_repair_hours: float = 0.0
    
    # Priority
    urgency_score: float = 0.0
    
    # Equipment needed
    equipment_needed: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.0
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        incident_id: str,
        **kwargs
    ) -> 'DispatchSuggestion':
        """Factory method to create a dispatch suggestion."""
        return cls(
            suggestion_id=f"ds_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            incident_id=incident_id,
            **kwargs
        )
