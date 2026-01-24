"""
AquaWatch NRW - Database Models
==============================

This module defines the complete data model for the NRW detection system.
Uses SQLAlchemy ORM with TimescaleDB-specific extensions.

Design Principles:
1. Normalize metadata, denormalize time-series
2. Use TimescaleDB hypertables for sensor data
3. Support millions of records per day
4. Maintain referential integrity for metadata
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Text, Enum as SQLEnum, Numeric, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================

class SensorType(str, Enum):
    PRESSURE = "pressure"
    FLOW = "flow"
    LEVEL = "level"
    QUALITY = "quality"


class SensorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FAULTY = "faulty"
    DECOMMISSIONED = "decommissioned"


class PipeMaterial(str, Enum):
    PVC = "pvc"
    HDPE = "hdpe"
    DUCTILE_IRON = "ductile_iron"
    CAST_IRON = "cast_iron"
    STEEL = "steel"
    ASBESTOS_CEMENT = "asbestos_cement"
    CONCRETE = "concrete"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class WorkOrderStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TenantPlan(str, Enum):
    """Subscription plans for tenants."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantRole(str, Enum):
    """Roles for users within a tenant."""
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class TenantUserStatus(str, Enum):
    """Status of tenant user membership."""
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    REMOVED = "removed"


# =============================================================================
# MULTI-TENANCY MODELS
# =============================================================================

class Tenant(Base):
    """
    Multi-tenant organization.
    
    Each tenant represents a water utility organization that uses the system.
    All data is isolated by tenant_id for security and data separation.
    """
    __tablename__ = "tenants"
    
    id = Column(String(50), primary_key=True)  # e.g., "lwsc-zambia", "default-tenant"
    name = Column(String(200), nullable=False)
    country = Column(String(3))  # ISO 3166-1 alpha-3 code
    timezone = Column(String(50), default="UTC")
    plan = Column(SQLEnum(TenantPlan), default=TenantPlan.FREE)
    
    # Contact
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    
    # Settings
    settings = Column(JSONB, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tenant_users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    dmas = relationship("DMA", back_populates="tenant")
    sensors = relationship("Sensor", back_populates="tenant")
    alerts = relationship("Alert", back_populates="tenant")
    work_orders = relationship("WorkOrder", back_populates="tenant")
    
    __table_args__ = (
        Index("ix_tenants_country", "country"),
        Index("ix_tenants_plan", "plan"),
    )
    
    def __repr__(self):
        return f"<Tenant {self.id}: {self.name}>"


class TenantUser(Base):
    """
    User membership within a tenant.
    
    Links users to tenants with specific roles.
    A user can belong to multiple tenants with different roles.
    """
    __tablename__ = "tenant_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Role within this tenant
    role = Column(SQLEnum(TenantRole), default=TenantRole.VIEWER)
    
    # Status
    status = Column(SQLEnum(TenantUserStatus), default=TenantUserStatus.ACTIVE)
    
    # Invitation
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    invited_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_access_at = Column(DateTime(timezone=True))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="tenant_users")
    user = relationship("User", back_populates="tenant_memberships", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
        Index("ix_tenant_users_tenant", "tenant_id"),
        Index("ix_tenant_users_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<TenantUser {self.tenant_id}/{self.user_id}: {self.role}>"


# =============================================================================
# LOCATION & ORGANIZATION MODELS
# =============================================================================

class Country(Base):
    """Country-level organization."""
    __tablename__ = "countries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(3), unique=True, nullable=False)  # ISO 3166-1 alpha-3
    name = Column(String(100), nullable=False)
    
    # Relationships
    utilities = relationship("Utility", back_populates="country")
    
    def __repr__(self):
        return f"<Country {self.code}: {self.name}>"


class Utility(Base):
    """Water utility organization."""
    __tablename__ = "utilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    city = Column(String(100))
    
    # Contact info
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    
    # Configuration
    timezone = Column(String(50), default="UTC")
    config = Column(JSONB, default={})
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="utilities")
    dmas = relationship("DMA", back_populates="utility")
    users = relationship("User", back_populates="utility")


class DMA(Base):
    """District Metered Area - fundamental management unit."""
    __tablename__ = "dmas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utility_id = Column(UUID(as_uuid=True), ForeignKey("utilities.id"), nullable=False)
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=True)  # Multi-tenancy
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    
    # Geographic bounds (GeoJSON polygon stored as JSONB)
    boundary = Column(JSONB)
    centroid_lat = Column(Numeric(10, 7))
    centroid_lon = Column(Numeric(10, 7))
    area_km2 = Column(Numeric(10, 3))
    
    # Network characteristics
    total_pipe_length_km = Column(Numeric(10, 3))
    total_connections = Column(Integer)
    expected_population = Column(Integer)
    
    # Operational parameters
    inlet_pressure_bar = Column(Numeric(5, 2))  # Normal inlet pressure
    critical_pressure_bar = Column(Numeric(5, 2))  # Minimum acceptable
    
    # NRW baseline
    baseline_nrw_percent = Column(Numeric(5, 2))
    target_nrw_percent = Column(Numeric(5, 2))
    
    # Status
    is_active = Column(Boolean, default=True)
    monitoring_level = Column(String(20), default="standard")  # basic, standard, intensive
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    utility = relationship("Utility", back_populates="dmas")
    tenant = relationship("Tenant", back_populates="dmas")
    sensors = relationship("Sensor", back_populates="dma")
    pipes = relationship("Pipe", back_populates="dma")
    alerts = relationship("Alert", back_populates="dma")
    
    __table_args__ = (
        UniqueConstraint("utility_id", "code", name="uq_dma_utility_code"),
        Index("ix_dmas_tenant_id", "tenant_id"),
    )


# =============================================================================
# INFRASTRUCTURE MODELS
# =============================================================================

class Sensor(Base):
    """Physical sensor device."""
    __tablename__ = "sensors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=True)  # Multi-tenancy
    
    # Identification
    device_id = Column(String(50), unique=True, nullable=False)  # Hardware ID
    serial_number = Column(String(100))
    
    # Type and measurement
    sensor_type = Column(SQLEnum(SensorType), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    
    # Measurement specs
    measurement_unit = Column(String(20), nullable=False)  # bar, m3/h, etc.
    min_value = Column(Numeric(10, 4))
    max_value = Column(Numeric(10, 4))
    accuracy_percent = Column(Numeric(5, 2))
    resolution = Column(Numeric(10, 6))
    
    # Location
    location_description = Column(String(500))
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    elevation_m = Column(Numeric(8, 2))
    
    # Installation
    installed_date = Column(Date)
    last_calibration = Column(Date)
    next_calibration = Column(Date)
    
    # Status
    status = Column(SQLEnum(SensorStatus), default=SensorStatus.ACTIVE)
    last_reading_at = Column(DateTime(timezone=True))
    
    # Communication
    communication_protocol = Column(String(50))  # mqtt, lorawan, cellular
    transmission_interval_sec = Column(Integer, default=900)  # 15 min default
    
    # Edge device association
    edge_device_id = Column(String(50))
    
    # Configuration
    config = Column(JSONB, default={})
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dma = relationship("DMA", back_populates="sensors")
    tenant = relationship("Tenant", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")
    
    __table_args__ = (
        Index("ix_sensors_dma_type", "dma_id", "sensor_type"),
        Index("ix_sensors_status", "status"),
        Index("ix_sensors_tenant_id", "tenant_id"),
    )


class Pipe(Base):
    """Pipe segment in the network."""
    __tablename__ = "pipes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    
    # Identification
    pipe_code = Column(String(50), nullable=False)
    
    # Physical properties
    material = Column(SQLEnum(PipeMaterial), default=PipeMaterial.UNKNOWN)
    diameter_mm = Column(Numeric(6, 1))
    length_m = Column(Numeric(10, 2))
    wall_thickness_mm = Column(Numeric(5, 2))
    
    # Age and condition
    installation_year = Column(Integer)
    age_years = Column(Integer)  # Computed or manual
    condition_score = Column(Integer)  # 1-10 scale
    last_inspection_date = Column(Date)
    
    # Location
    start_lat = Column(Numeric(10, 7))
    start_lon = Column(Numeric(10, 7))
    end_lat = Column(Numeric(10, 7))
    end_lon = Column(Numeric(10, 7))
    street_name = Column(String(200))
    
    # Geometry (GeoJSON LineString)
    geometry = Column(JSONB)
    
    # Network topology
    upstream_node_id = Column(String(50))
    downstream_node_id = Column(String(50))
    
    # Risk factors
    failure_history_count = Column(Integer, default=0)
    soil_type = Column(String(50))
    traffic_load = Column(String(20))  # low, medium, high
    
    # Computed risk score (updated by analytics)
    risk_score = Column(Numeric(5, 3))
    risk_updated_at = Column(DateTime(timezone=True))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dma = relationship("DMA", back_populates="pipes")
    leak_events = relationship("LeakEvent", back_populates="pipe")
    
    __table_args__ = (
        UniqueConstraint("dma_id", "pipe_code", name="uq_pipe_dma_code"),
        Index("ix_pipes_material", "material"),
        Index("ix_pipes_risk_score", "risk_score"),
    )


# =============================================================================
# TIME-SERIES DATA MODELS (TimescaleDB Hypertables)
# =============================================================================

class SensorReading(Base):
    """
    Time-series sensor readings.
    
    This table is converted to a TimescaleDB hypertable for efficient
    time-series operations. Partitioned by time (weekly chunks).
    
    Expected volume: ~10 million rows per day for national deployment
    """
    __tablename__ = "sensor_readings"
    
    # Composite primary key for hypertable
    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id"), primary_key=True, nullable=False)
    
    # Measurement
    value = Column(Numeric(12, 4), nullable=False)
    
    # Quality indicators
    quality_score = Column(Integer, default=100)  # 0-100
    is_interpolated = Column(Boolean, default=False)
    
    # Optional raw value (before calibration)
    raw_value = Column(Numeric(12, 4))
    
    # Edge processing info
    edge_timestamp = Column(DateTime(timezone=True))
    transmission_delay_sec = Column(Integer)
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")
    
    __table_args__ = (
        Index("ix_readings_sensor_time", "sensor_id", "time"),
        # TimescaleDB will add time-based partitioning
    )


class HourlyAggregate(Base):
    """
    Pre-computed hourly aggregates.
    
    Created as a TimescaleDB continuous aggregate for efficient querying.
    Automatically maintained by TimescaleDB.
    """
    __tablename__ = "sensor_readings_hourly"
    
    hour = Column(DateTime(timezone=True), primary_key=True)
    sensor_id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Aggregates
    avg_value = Column(Numeric(12, 4))
    min_value = Column(Numeric(12, 4))
    max_value = Column(Numeric(12, 4))
    stddev_value = Column(Numeric(12, 4))
    sample_count = Column(Integer)
    
    # Quality
    avg_quality = Column(Numeric(5, 2))
    missing_count = Column(Integer)


class DailyAggregate(Base):
    """Daily aggregates for long-term analysis."""
    __tablename__ = "sensor_readings_daily"
    
    date = Column(Date, primary_key=True)
    sensor_id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Daily statistics
    avg_value = Column(Numeric(12, 4))
    min_value = Column(Numeric(12, 4))
    max_value = Column(Numeric(12, 4))
    stddev_value = Column(Numeric(12, 4))
    
    # Time-of-day breakdowns
    avg_night = Column(Numeric(12, 4))  # 00:00-06:00
    avg_morning = Column(Numeric(12, 4))  # 06:00-12:00
    avg_afternoon = Column(Numeric(12, 4))  # 12:00-18:00
    avg_evening = Column(Numeric(12, 4))  # 18:00-24:00
    
    # MNF specific (01:00-04:00)
    mnf_avg = Column(Numeric(12, 4))
    mnf_min = Column(Numeric(12, 4))
    
    # Quality metrics
    completeness_percent = Column(Numeric(5, 2))
    sample_count = Column(Integer)


# =============================================================================
# AI & ANALYTICS MODELS
# =============================================================================

class AnomalyScore(Base):
    """
    Real-time anomaly scores from Layer 1 AI.
    
    Stored for audit trail and model improvement.
    """
    __tablename__ = "anomaly_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time = Column(DateTime(timezone=True), nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id"), nullable=False)
    
    # Anomaly detection output
    anomaly_score = Column(Numeric(5, 4), nullable=False)  # 0.0 to 1.0
    is_anomaly = Column(Boolean, nullable=False)
    
    # Model info
    model_version = Column(String(50))
    model_type = Column(String(50))  # isolation_forest, etc.
    
    # Contributing factors (for explainability)
    contributing_features = Column(JSONB)
    
    # Features used (snapshot for reproducibility)
    feature_values = Column(JSONB)
    
    __table_args__ = (
        Index("ix_anomaly_scores_time", "time"),
        Index("ix_anomaly_scores_sensor", "sensor_id"),
    )


class LeakProbability(Base):
    """
    Leak probability estimates from Layer 2 AI.
    """
    __tablename__ = "leak_probabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time = Column(DateTime(timezone=True), nullable=False)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    
    # Probability estimate
    probability = Column(Numeric(5, 4), nullable=False)  # 0.0 to 1.0
    confidence = Column(Numeric(5, 4))
    
    # Estimated impact
    estimated_loss_m3_day = Column(Numeric(10, 2))
    estimated_loss_lower = Column(Numeric(10, 2))
    estimated_loss_upper = Column(Numeric(10, 2))
    
    # Localization (from Layer 3)
    probable_segments = Column(JSONB)  # [{segment_id, probability}, ...]
    
    # Explanation
    explanation = Column(JSONB)
    
    # Model info
    model_version = Column(String(50))
    
    # Triggering anomalies
    triggering_anomaly_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    __table_args__ = (
        Index("ix_leak_prob_time", "time"),
        Index("ix_leak_prob_dma", "dma_id"),
    )


# =============================================================================
# ALERT & WORKFLOW MODELS
# =============================================================================

class Alert(Base):
    """
    System-generated alerts for operator attention.
    """
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=True)  # Multi-tenancy
    
    # Alert identification
    alert_number = Column(String(50), unique=True, nullable=False)  # ALT-2026-00001
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Classification
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.NEW)
    alert_type = Column(String(50), nullable=False)  # pressure_anomaly, flow_anomaly, etc.
    
    # Source
    source = Column(String(20), nullable=False)  # ai, baseline, manual
    leak_probability_id = Column(UUID(as_uuid=True), ForeignKey("leak_probabilities.id"))
    
    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # AI output
    probability = Column(Numeric(5, 4))
    confidence = Column(Numeric(5, 4))
    estimated_loss_m3_day = Column(Numeric(10, 2))
    
    # Location
    probable_location = Column(String(500))
    probable_segments = Column(JSONB)
    coordinates = Column(JSONB)  # {lat, lon}
    
    # Explanation for operators
    explanation = Column(JSONB)
    recommended_actions = Column(JSONB)
    
    # Response
    acknowledged_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    actual_cause = Column(String(200))
    
    # Feedback for model improvement
    was_correct = Column(Boolean)  # True = confirmed leak, False = false positive
    feedback_notes = Column(Text)
    
    # Relationships
    dma = relationship("DMA", back_populates="alerts")
    tenant = relationship("Tenant", back_populates="alerts")
    work_orders = relationship("WorkOrder", back_populates="alert")
    
    __table_args__ = (
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_created", "created_at"),
        Index("ix_alerts_tenant_id", "tenant_id"),
    )


class WorkOrder(Base):
    """
    Field work orders generated from alerts.
    """
    __tablename__ = "work_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"))
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=True)  # Multi-tenancy
    
    # Identification
    work_order_number = Column(String(50), unique=True, nullable=False)  # WO-2026-00001
    
    # Status
    status = Column(SQLEnum(WorkOrderStatus), default=WorkOrderStatus.CREATED)
    priority = Column(Integer, default=3)  # 1 = highest
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    
    # Assignment
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    team = Column(String(100))
    
    # Task details
    task_type = Column(String(50), nullable=False)  # inspection, repair, investigation
    description = Column(Text)
    location = Column(String(500))
    coordinates = Column(JSONB)
    
    # Instructions
    instructions = Column(JSONB)
    required_equipment = Column(JSONB)
    safety_notes = Column(Text)
    
    # Results
    findings = Column(Text)
    actions_taken = Column(Text)
    
    # Leak confirmation
    leak_confirmed = Column(Boolean)
    leak_size = Column(String(50))  # small, medium, large
    estimated_flow_m3_day = Column(Numeric(10, 2))
    repair_completed = Column(Boolean)
    
    # Documentation
    photos = Column(JSONB)  # [{url, caption, timestamp}, ...]
    
    # Relationships
    alert = relationship("Alert", back_populates="work_orders")
    tenant = relationship("Tenant", back_populates="work_orders")
    
    __table_args__ = (
        Index("ix_work_orders_status", "status"),
        Index("ix_work_orders_assigned", "assigned_to_id"),
        Index("ix_work_orders_tenant_id", "tenant_id"),
    )


class LeakEvent(Base):
    """
    Confirmed leak events (historical record).
    """
    __tablename__ = "leak_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipe_id = Column(UUID(as_uuid=True), ForeignKey("pipes.id"))
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"))
    
    # Detection
    detected_at = Column(DateTime(timezone=True), nullable=False)
    detection_method = Column(String(50))  # ai, acoustic, visual, reported
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"))
    
    # Confirmation
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Location
    location_description = Column(String(500))
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    
    # Leak characteristics
    leak_type = Column(String(50))  # burst, joint_failure, corrosion, crack
    leak_size = Column(String(20))  # small, medium, large
    estimated_flow_m3_day = Column(Numeric(10, 2))
    estimated_duration_days = Column(Integer)
    estimated_total_loss_m3 = Column(Numeric(12, 2))
    
    # Repair
    repaired_at = Column(DateTime(timezone=True))
    repair_type = Column(String(100))
    repair_cost = Column(Numeric(12, 2))
    repair_notes = Column(Text)
    
    # Cause analysis
    root_cause = Column(String(200))
    contributing_factors = Column(JSONB)
    
    # Pressure before/after repair
    pressure_before_repair = Column(Numeric(6, 3))
    pressure_after_repair = Column(Numeric(6, 3))
    pressure_improvement = Column(Numeric(6, 3))
    
    # For model training
    feature_snapshot = Column(JSONB)  # Features at time of detection
    
    # =========================================================================
    # STEP 8: EXPLAINABLE AI INSIGHTS
    # =========================================================================
    # AI Reason stores structured explainability data:
    # - pressure_drop: {value, threshold, deviation, contribution, description}
    # - flow_rise: {value, threshold, deviation, contribution, description}
    # - multi_sensor_agreement: {sensors_triggered, agreement_score, contribution}
    # - night_flow_deviation: {value, expected, deviation_percent, contribution}
    # - confidence: {statistical, ml, temporal, spatial, acoustic, overall, weights}
    # - top_signals: ["pressure_drop", "multi_sensor_agreement", ...]
    # - evidence_timeline: [{timestamp, signal_type, value, anomaly_score, is_key_event}]
    # - explanation: Human-readable description of why leak was detected
    # - recommendations: ["Dispatch team...", "Monitor closely..."]
    ai_reason = Column(JSONB)  # Explainable AI insights
    
    # Relationships
    pipe = relationship("Pipe", back_populates="leak_events")
    
    __table_args__ = (
        Index("ix_leak_events_dma", "dma_id"),
        Index("ix_leak_events_detected", "detected_at"),
    )


# =============================================================================
# USER & ACCESS MODELS
# =============================================================================

class User(Base):
    """System users."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utility_id = Column(UUID(as_uuid=True), ForeignKey("utilities.id"))
    
    # Authentication
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200))  # bcrypt hash
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    
    # Role
    role = Column(String(50), nullable=False)  # admin, manager, operator, technician
    permissions = Column(JSONB, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    
    # Preferences
    preferences = Column(JSONB, default={})
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    utility = relationship("Utility", back_populates="users")
    tenant_memberships = relationship("TenantUser", back_populates="user", foreign_keys="TenantUser.user_id")


# =============================================================================
# AUDIT & LOGGING
# =============================================================================

class AuditLog(Base):
    """System audit trail."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=True)  # Multi-tenancy
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Who
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_email = Column(String(200))
    
    # What
    action = Column(String(50), nullable=False)  # create, update, delete, login, etc.
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    
    # Details
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    # Context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    __table_args__ = (
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_tenant_id", "tenant_id"),
    )


# =============================================================================
# MODEL MANAGEMENT
# =============================================================================

class ModelVersion(Base):
    """Track deployed AI models."""
    __tablename__ = "model_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    model_name = Column(String(100), nullable=False)  # anomaly_detector, leak_classifier, etc.
    version = Column(String(50), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=False)
    deployed_at = Column(DateTime(timezone=True))
    retired_at = Column(DateTime(timezone=True))
    
    # Storage
    artifact_path = Column(String(500))  # S3 path or local path
    checksum = Column(String(64))  # SHA256
    
    # Training info
    trained_at = Column(DateTime(timezone=True))
    training_data_start = Column(Date)
    training_data_end = Column(Date)
    training_samples = Column(Integer)
    
    # Performance metrics
    metrics = Column(JSONB)  # {accuracy, precision, recall, f1, etc.}
    
    # Configuration
    hyperparameters = Column(JSONB)
    feature_names = Column(JSONB)
    
    # Notes
    description = Column(Text)
    
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
    )


# =============================================================================
# SYSTEM INPUT VOLUME (SIV) MODELS - FOUNDATION FOR NRW
# =============================================================================

class SIVSourceType(str, Enum):
    """Types of SIV sources."""
    TREATMENT_PLANT = "treatment_plant"
    RESERVOIR = "reservoir"
    BULK_METER = "bulk_meter"
    BOREHOLE = "borehole"
    IMPORTED = "imported"


class SIVSource(Base):
    """
    System Input Volume source (treatment plant, reservoir, bulk meter).
    
    This is CRITICAL - without SIV sources, NRW cannot be calculated.
    """
    __tablename__ = "siv_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utility_id = Column(UUID(as_uuid=True), ForeignKey("utilities.id"))
    
    # Identification
    source_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    source_type = Column(SQLEnum(SIVSourceType), nullable=False)
    
    # Location
    location_description = Column(String(500))
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    
    # Meter info
    meter_id = Column(String(100))
    meter_serial = Column(String(100))
    measurement_unit = Column(String(20), default="m3/h")
    accuracy_percent = Column(Numeric(5, 2), default=2.0)
    
    # Capacity
    design_capacity_m3_day = Column(Numeric(12, 2))
    max_flow_m3_hour = Column(Numeric(10, 2))
    
    # Connected DMAs
    connected_dma_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    # Status
    is_active = Column(Boolean, default=True)
    commissioned_date = Column(Date)
    last_reading_at = Column(DateTime(timezone=True))
    
    # Config
    config = Column(JSONB, default={})
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    siv_records = relationship("SIVRecord", back_populates="source")
    
    __table_args__ = (
        Index("ix_siv_sources_type", "source_type"),
        Index("ix_siv_sources_utility", "utility_id"),
    )


class SIVRecord(Base):
    """
    System Input Volume time-series record.
    
    This table stores all water entering the distribution system.
    Converted to TimescaleDB hypertable for efficient queries.
    """
    __tablename__ = "siv_records"
    
    # Composite primary key for hypertable
    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("siv_sources.id"), primary_key=True, nullable=False)
    
    # Volume measurement
    volume_m3 = Column(Numeric(12, 3), nullable=False)
    flow_rate_m3_hour = Column(Numeric(10, 3))
    
    # Period (for aggregated data)
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    aggregation_type = Column(String(20), default="instantaneous")
    
    # Data quality
    quality = Column(String(20), default="measured")  # measured, estimated, interpolated
    quality_score = Column(Integer, default=100)
    is_validated = Column(Boolean, default=False)
    
    # Raw reading
    raw_value = Column(Numeric(12, 4))
    raw_unit = Column(String(20))
    
    # Uncertainty
    uncertainty_m3 = Column(Numeric(10, 3))
    uncertainty_percent = Column(Numeric(5, 2))
    
    # Ingestion
    ingestion_method = Column(String(20), default="api")  # api, csv, scada, manual
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    
    # Relationships
    source = relationship("SIVSource", back_populates="siv_records")
    
    __table_args__ = (
        Index("ix_siv_records_source_time", "source_id", "time"),
    )


class DMAInletFlow(Base):
    """
    Water flow at DMA boundary meters.
    
    Links SIV to individual DMAs for loss attribution.
    """
    __tablename__ = "dma_inlet_flows"
    
    # Composite primary key for hypertable
    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), primary_key=True, nullable=False)
    inlet_point_id = Column(String(50), primary_key=True, nullable=False)
    
    # Flow measurement
    volume_m3 = Column(Numeric(12, 3), nullable=False)
    flow_rate_m3_hour = Column(Numeric(10, 3), nullable=False)
    
    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Direction
    is_inlet = Column(Boolean, default=True)  # True = entering, False = leaving
    
    # Link to SIV source
    siv_source_id = Column(UUID(as_uuid=True), ForeignKey("siv_sources.id"))
    
    # Meter
    meter_id = Column(String(100))
    
    # Quality
    quality = Column(String(20), default="measured")
    quality_score = Column(Integer, default=100)
    
    __table_args__ = (
        Index("ix_dma_inlet_dma_time", "dma_id", "time"),
    )


class BillingRecord(Base):
    """
    Billing/consumption data for NRW calculation.
    
    NRW = SIV - (Billed + Unbilled Authorized)
    """
    __tablename__ = "billing_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=False)
    
    # Billing period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Billed Authorized Consumption (m³)
    billed_metered_m3 = Column(Numeric(12, 2), default=0)
    billed_unmetered_m3 = Column(Numeric(12, 2), default=0)
    
    # Unbilled Authorized Consumption (m³)
    unbilled_metered_m3 = Column(Numeric(12, 2), default=0)
    unbilled_unmetered_m3 = Column(Numeric(12, 2), default=0)
    
    # Customer counts
    metered_customer_count = Column(Integer, default=0)
    unmetered_customer_count = Column(Integer, default=0)
    
    # Revenue (optional)
    revenue_usd = Column(Numeric(14, 2))
    tariff_usd_per_m3 = Column(Numeric(8, 4))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source_system = Column(String(50))  # billing_system, manual, etc.
    
    __table_args__ = (
        Index("ix_billing_dma_period", "dma_id", "period_start"),
        UniqueConstraint("dma_id", "period_start", "period_end", name="uq_billing_dma_period"),
    )


class NRWCalculation(Base):
    """
    Stored NRW calculation results.
    
    Provides audit trail of all NRW calculations.
    """
    __tablename__ = "nrw_calculations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope
    utility_id = Column(UUID(as_uuid=True), ForeignKey("utilities.id"))
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"))  # NULL = utility-wide
    
    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_days = Column(Integer, nullable=False)
    
    # IWA Water Balance Components (m³)
    system_input_volume_m3 = Column(Numeric(14, 2), nullable=False)
    billed_authorized_m3 = Column(Numeric(14, 2), nullable=False)
    unbilled_authorized_m3 = Column(Numeric(14, 2), nullable=False)
    water_losses_m3 = Column(Numeric(14, 2), nullable=False)
    
    # Loss breakdown
    apparent_losses_m3 = Column(Numeric(14, 2))
    real_losses_m3 = Column(Numeric(14, 2))
    
    # KPIs
    nrw_percent = Column(Numeric(5, 2), nullable=False)
    real_losses_percent = Column(Numeric(5, 2))
    apparent_losses_percent = Column(Numeric(5, 2))
    
    # IWA Level 2 indicators
    real_losses_l_per_conn_day = Column(Numeric(8, 2))
    real_losses_m3_per_km_day = Column(Numeric(8, 3))
    
    # IWA Level 3 indicators
    ili = Column(Numeric(6, 2))  # Infrastructure Leakage Index
    uarl_m3_year = Column(Numeric(14, 2))  # Unavoidable Annual Real Losses
    carl_m3_year = Column(Numeric(14, 2))  # Current Annual Real Losses
    
    # MNF analysis
    mnf_m3_hour = Column(Numeric(10, 2))
    mnf_excess_m3_day = Column(Numeric(10, 2))
    
    # Data quality
    siv_data_completeness = Column(Numeric(5, 2))
    billing_data_completeness = Column(Numeric(5, 2))
    calculation_confidence = Column(Numeric(5, 2))
    
    # Metadata
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    calculated_by = Column(String(100))  # user or "system"
    assumptions = Column(JSONB)
    notes = Column(Text)
    
    __table_args__ = (
        Index("ix_nrw_calc_dma_period", "dma_id", "period_start"),
        Index("ix_nrw_calc_utility_period", "utility_id", "period_start"),
    )


# =============================================================================
# NOTIFICATION SYSTEM MODELS
# =============================================================================

class NotificationChannel(str, Enum):
    """Available notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationSeverity(str, Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class NotificationRule(Base):
    """
    Notification rules defining when and how to send notifications.
    
    Configures:
    - Which events trigger notifications
    - Which channels to use based on severity
    - Escalation paths and timing
    """
    __tablename__ = "notification_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Trigger conditions
    event_type = Column(String(50), nullable=False)  # leak.detected, sensor.offline, etc.
    severity = Column(SQLEnum(NotificationSeverity), nullable=False)
    
    # Target roles (JSON array of roles to notify)
    target_roles = Column(JSONB, default=["operator"])  # e.g., ["operator", "engineer"]
    
    # Channels configuration (JSON object mapping channel to config)
    # e.g., {"in_app": {"enabled": true}, "email": {"enabled": true, "template": "leak_alert"}}
    channels = Column(JSONB, nullable=False, default={
        "in_app": {"enabled": True},
        "email": {"enabled": False}
    })
    
    # Escalation configuration (JSON array of escalation steps)
    # e.g., [{"delay_minutes": 5, "roles": ["engineer"], "channels": ["sms"]}]
    escalation = Column(JSONB, default=[])
    
    # Conditions (optional JSON filter)
    # e.g., {"dma_id": "DMA-01", "min_loss_m3": 100}
    conditions = Column(JSONB, default={})
    
    # Throttling
    cooldown_minutes = Column(Integer, default=15)  # Don't re-notify within this period
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    __table_args__ = (
        Index("ix_notification_rules_tenant", "tenant_id"),
        Index("ix_notification_rules_event", "event_type"),
        Index("ix_notification_rules_severity", "severity"),
        UniqueConstraint("tenant_id", "name", name="uq_notification_rule_name"),
    )
    
    def __repr__(self):
        return f"<NotificationRule {self.name}: {self.event_type}/{self.severity}>"


class Notification(Base):
    """
    Individual notifications sent to users.
    
    Tracks:
    - Notification content and metadata
    - Delivery status per channel
    - Read status for in-app notifications
    """
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Classification
    severity = Column(SQLEnum(NotificationSeverity), nullable=False, default=NotificationSeverity.INFO)
    category = Column(String(50))  # leak, sensor, work_order, system, etc.
    
    # Source reference
    source_type = Column(String(50))  # alert, work_order, system, etc.
    source_id = Column(String(100))  # ID of the source entity
    
    # Delivery
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # For in-app notifications
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Action URL (for clickable notifications)
    action_url = Column(String(500))
    
    # Metadata
    metadata = Column(JSONB, default={})  # Additional context data
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    
    # Delivery tracking
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Link to rule that triggered this
    rule_id = Column(UUID(as_uuid=True), ForeignKey("notification_rules.id", ondelete="SET NULL"))
    
    __table_args__ = (
        Index("ix_notifications_tenant_user", "tenant_id", "user_id"),
        Index("ix_notifications_user_read", "user_id", "read"),
        Index("ix_notifications_created", "created_at"),
        Index("ix_notifications_status", "status"),
    )
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.title[:30]}...>"


class EscalationTracker(Base):
    """
    Tracks escalation state for alerts requiring time-based escalation.
    
    Used by the escalation scheduler to determine when to escalate.
    """
    __tablename__ = "escalation_trackers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Source reference
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    
    # Escalation state
    current_level = Column(Integer, default=0)  # 0 = initial notification
    max_level = Column(Integer, default=2)  # Maximum escalation level
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_escalated_at = Column(DateTime(timezone=True))
    next_escalation_at = Column(DateTime(timezone=True))
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_type = Column(String(50))  # acknowledged, resolved, timeout, manual
    
    # Notification history
    notifications_sent = Column(JSONB, default=[])  # Array of notification IDs sent
    
    __table_args__ = (
        Index("ix_escalation_tenant", "tenant_id"),
        Index("ix_escalation_alert", "alert_id"),
        Index("ix_escalation_next", "next_escalation_at"),
        UniqueConstraint("alert_id", name="uq_escalation_alert"),
    )
    
    def __repr__(self):
        return f"<EscalationTracker alert={self.alert_id} level={self.current_level}>"


# =============================================================================
# TIMESCALEDB INITIALIZATION SQL
# =============================================================================

TIMESCALEDB_INIT_SQL = """
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert sensor_readings to hypertable
SELECT create_hypertable(
    'sensor_readings', 
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- Enable compression
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_id'
);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

-- Retention policy (keep raw data for 90 days)
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');

-- Create continuous aggregate for hourly data
CREATE MATERIALIZED VIEW sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    sensor_id,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value,
    COUNT(*) as sample_count,
    AVG(quality_score) as avg_quality,
    SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as missing_count
FROM sensor_readings
GROUP BY hour, sensor_id
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('sensor_readings_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Anomaly scores hypertable
SELECT create_hypertable(
    'anomaly_scores',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Leak probabilities hypertable  
SELECT create_hypertable(
    'leak_probabilities',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- =============================================================================
-- SIV (SYSTEM INPUT VOLUME) HYPERTABLES - FOUNDATION FOR NRW
-- =============================================================================

-- SIV Records hypertable
SELECT create_hypertable(
    'siv_records',
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- Enable compression for SIV records
ALTER TABLE siv_records SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'source_id'
);

SELECT add_compression_policy('siv_records', INTERVAL '30 days');

-- Continuous aggregate for daily SIV totals
CREATE MATERIALIZED VIEW siv_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    source_id,
    SUM(volume_m3) as total_volume_m3,
    AVG(flow_rate_m3_hour) as avg_flow_m3_h,
    MAX(flow_rate_m3_hour) as max_flow_m3_h,
    MIN(flow_rate_m3_hour) as min_flow_m3_h,
    COUNT(*) as record_count,
    AVG(quality_score) as avg_quality
FROM siv_records
GROUP BY day, source_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('siv_daily',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- DMA Inlet Flow hypertable
SELECT create_hypertable(
    'dma_inlet_flows',
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE dma_inlet_flows SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dma_id'
);

SELECT add_compression_policy('dma_inlet_flows', INTERVAL '30 days');

-- Continuous aggregate for daily DMA inlet totals
CREATE MATERIALIZED VIEW dma_inlet_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    dma_id,
    SUM(CASE WHEN is_inlet THEN volume_m3 ELSE 0 END) as total_inlet_m3,
    SUM(CASE WHEN NOT is_inlet THEN volume_m3 ELSE 0 END) as total_outlet_m3,
    SUM(volume_m3 * CASE WHEN is_inlet THEN 1 ELSE -1 END) as net_input_m3,
    AVG(flow_rate_m3_hour) as avg_flow_m3_h,
    COUNT(*) as record_count
FROM dma_inlet_flows
GROUP BY day, dma_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('dma_inlet_daily',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');
"""
