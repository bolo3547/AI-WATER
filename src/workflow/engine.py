"""
AquaWatch NRW - Operations Workflow Engine
==========================================

IWA Water Balance Aligned Operations Workflow
----------------------------------------------

This workflow engine speaks the language of water utility operations,
not generic anomaly detection.

Handles the operational workflow from alert to resolution:
1. Alert Generation - Create IWA-classified alerts from AI detections
2. Work Order Management - Create, assign, track work orders with NRW context
3. Feedback Loop - Capture field results to improve AI and track Real vs Apparent losses
4. Escalation Rules - Time-based escalation with IWA loss category consideration
5. Notification System - Multi-channel notifications with water utility terminology

IWA Water Balance Framework Integration:
- Alerts classified as Real Losses (leakage, overflow, service connection)
- Alerts classified as Apparent Losses (meter error, unauthorized consumption)
- Minimum Night Flow (MNF) analysis for loss estimation
- Pressure-leakage relationship awareness

Physical Basis:
- Leak losses increase linearly with time (cost escalation)
- Response time directly impacts water/revenue loss
- Field feedback essential for model improvement
- Real Losses vs Apparent Losses require different interventions
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# IWA WATER BALANCE ENUMERATIONS
# =============================================================================

class NRWCategory(Enum):
    """
    IWA Water Balance NRW Categories.
    
    Real Losses = Physical water losses
    Apparent Losses = Commercial/administrative losses (water delivered but not paid for)
    """
    # Real Losses (Physical)
    REAL_LOSS_LEAKAGE = "real_loss_leakage"           # Transmission/distribution mains
    REAL_LOSS_OVERFLOW = "real_loss_overflow"         # Tank overflows
    REAL_LOSS_SERVICE = "real_loss_service_connection"  # Service connection leaks
    
    # Apparent Losses (Commercial)
    APPARENT_LOSS_METER = "apparent_loss_meter_error"      # Under-registration
    APPARENT_LOSS_UNAUTHORIZED = "apparent_loss_unauthorized"  # Theft/illegal connections
    
    # Unknown (requires investigation)
    UNKNOWN = "unknown"


class InterventionType(Enum):
    """
    IWA-recommended intervention types by NRW category.
    """
    # For Real Losses
    ACTIVE_LEAK_DETECTION = "active_leak_detection"
    ACOUSTIC_SURVEY = "acoustic_survey"
    PRESSURE_MANAGEMENT = "pressure_management"
    INFRASTRUCTURE_REPAIR = "infrastructure_repair"
    TANK_LEVEL_CONTROL = "tank_level_control"
    
    # For Apparent Losses
    METER_TESTING = "meter_testing"
    METER_REPLACEMENT = "meter_replacement"
    UNAUTHORIZED_USE_SURVEY = "unauthorized_use_survey"
    DATA_VALIDATION = "data_validation"
    
    # Generic
    FIELD_INVESTIGATION = "field_investigation"


# =============================================================================
# ALERT ENUMERATIONS
# =============================================================================

class AlertSeverity(Enum):
    """
    Alert severity levels - aligned with IWA operational guidelines.
    
    Severity considers:
    - Estimated volume loss (m³/day)
    - Infrastructure criticality
    - Time since detection (escalation)
    - Whether Real Loss (immediate) or Apparent Loss (scheduled)
    """
    CRITICAL = "critical"  # >100 m³/day or critical infrastructure - Immediate response
    HIGH = "high"          # 50-100 m³/day Real Loss - Same-day response
    MEDIUM = "medium"      # <50 m³/day or Apparent Loss - 48-hour response
    LOW = "low"            # Monitoring/validation required - Scheduled


class AlertStatus(Enum):
    """Alert lifecycle status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class WorkOrderPriority(Enum):
    """Work order priority levels."""
    EMERGENCY = "emergency"  # Dispatch immediately
    HIGH = "high"           # Today
    NORMAL = "normal"       # This week
    LOW = "low"             # Scheduled


class WorkOrderStatus(Enum):
    """Work order lifecycle status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    DASHBOARD = "dashboard"


class LeakConfirmation(Enum):
    """
    Field confirmation of NRW detection - aligned with IWA feedback requirements.
    
    Critical for AI model improvement and ILI (Infrastructure Leakage Index) tracking.
    """
    CONFIRMED_REAL_LOSS = "confirmed_real_loss"         # Real loss confirmed (leakage)
    CONFIRMED_APPARENT_LOSS = "confirmed_apparent_loss" # Apparent loss confirmed (meter/theft)
    CONFIRMED_NEARBY = "nearby"                         # Loss found within 100m of prediction
    NOT_FOUND = "not_found"                             # No loss detected
    INCONCLUSIVE = "inconclusive"                       # Need more investigation
    FALSE_POSITIVE_NORMAL = "false_positive_normal"     # Normal operation, AI error
    FALSE_POSITIVE_EVENT = "false_positive_event"       # Explained by operational event


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GeoLocation:
    """Geographic location."""
    latitude: float
    longitude: float
    accuracy_m: float = 10.0
    
    def distance_to(self, other: 'GeoLocation') -> float:
        """Calculate approximate distance in meters."""
        # Simplified calculation for demonstration
        from math import radians, cos, sin, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


@dataclass
class Alert:
    """
    IWA-Aligned NRW Detection Alert.
    
    This alert speaks the language of water utilities:
    - NRW Category (Real vs Apparent Loss)
    - DMA context
    - Minimum Night Flow (MNF) based confidence
    - Pressure-related risk assessment
    - Utility-specific suggested actions
    """
    alert_id: str
    dma_id: str
    timestamp: datetime
    severity: AlertSeverity
    status: AlertStatus
    
    # Detection details (required fields before defaults)
    detection_type: str  # "real_loss", "apparent_loss", "mnf_anomaly", "pressure_anomaly"
    probability: float
    confidence: float
    
    # IWA Water Balance Classification
    nrw_category: NRWCategory = NRWCategory.UNKNOWN
    recommended_intervention: Optional[InterventionType] = None
    
    # Night Analysis Context (IWA Standard)
    is_night_detection: bool = False  # True if detected during 00:00-04:00
    mnf_deviation_percent: float = 0.0  # % deviation from expected MNF
    
    # Pressure Context
    pressure_bar: Optional[float] = None
    pressure_risk_zone: str = "unknown"  # "low", "optimal", "elevated", "high", "critical"
    
    # Location (if localized)
    pipe_segment_id: Optional[str] = None
    location: Optional[GeoLocation] = None
    location_confidence: float = 0.0
    
    # Estimated impact (IWA metrics)
    estimated_loss_m3_day: float = 0.0
    estimated_loss_m3_year: float = 0.0
    estimated_revenue_loss_daily: float = 0.0
    estimated_revenue_loss_annual: float = 0.0
    
    # AI explanation in water utility language
    key_evidence: List[str] = field(default_factory=list)
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    utility_summary: str = ""  # Human-readable summary for operators
    
    # Workflow tracking
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    work_order_id: Optional[str] = None
    
    # Resolution (IWA feedback)
    resolution: Optional[LeakConfirmation] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    actual_loss_m3_day: Optional[float] = None  # Field-verified loss rate
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with IWA terminology."""
        return {
            "alert_id": self.alert_id,
            "dma_id": self.dma_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "status": self.status.value,
            "nrw_category": self.nrw_category.value,
            "detection_type": self.detection_type,
            "probability": self.probability,
            "confidence": self.confidence,
            "is_night_detection": self.is_night_detection,
            "mnf_deviation_percent": self.mnf_deviation_percent,
            "pressure_bar": self.pressure_bar,
            "pressure_risk_zone": self.pressure_risk_zone,
            "estimated_loss_m3_day": self.estimated_loss_m3_day,
            "estimated_revenue_loss_daily": self.estimated_revenue_loss_daily,
            "key_evidence": self.key_evidence,
            "utility_summary": self.utility_summary
        }
    
    def to_utility_report(self) -> str:
        """
        Generate a water-utility-focused report for operators.
        
        This differentiates us from generic anomaly detection:
        "Most AI systems detect anomalies; ours understands water networks,
        NRW categories, and utility operations."
        """
        category_labels = {
            NRWCategory.REAL_LOSS_LEAKAGE: "Real Loss - Distribution Main Leakage",
            NRWCategory.REAL_LOSS_OVERFLOW: "Real Loss - Tank Overflow",
            NRWCategory.REAL_LOSS_SERVICE: "Real Loss - Service Connection",
            NRWCategory.APPARENT_LOSS_METER: "Apparent Loss - Meter Under-registration",
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: "Apparent Loss - Unauthorized Use",
            NRWCategory.UNKNOWN: "Under Investigation"
        }
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    NRW DETECTION ALERT                           ║
╠══════════════════════════════════════════════════════════════════╣
║ Alert ID: {self.alert_id:<52} ║
║ DMA: {self.dma_id:<57} ║
║ Time: {self.timestamp.strftime('%Y-%m-%d %H:%M'):<56} ║
╠══════════════════════════════════════════════════════════════════╣
║ IWA CLASSIFICATION                                               ║
╠──────────────────────────────────────────────────────────────────╣
║ Category: {category_labels.get(self.nrw_category, 'Unknown'):<52} ║
║ Confidence: {self.confidence*100:.0f}%{' (HIGH - Night Analysis)' if self.is_night_detection else '':<44} ║
║ Severity: {self.severity.value.upper():<52} ║
╠══════════════════════════════════════════════════════════════════╣
║ ESTIMATED NRW IMPACT                                             ║
╠──────────────────────────────────────────────────────────────────╣
║ Daily Loss: {self.estimated_loss_m3_day:,.1f} m³/day (${self.estimated_revenue_loss_daily:,.2f}/day){' ':<15} ║
║ Annual Loss: {self.estimated_loss_m3_year:,.0f} m³/year (${self.estimated_revenue_loss_annual:,.2f}/year){' ':<10} ║
╠══════════════════════════════════════════════════════════════════╣
║ ANALYSIS CONTEXT                                                 ║
╠──────────────────────────────────────────────────────────────────╣
"""
        if self.is_night_detection:
            report += f"║ ⏰ Night Analysis (00:00-04:00): MNF deviation {self.mnf_deviation_percent:+.1f}%{' ':<12} ║\n"
        
        if self.pressure_bar:
            report += f"║ 📊 Pressure: {self.pressure_bar:.2f} bar ({self.pressure_risk_zone} risk){' ':<30} ║\n"
        
        report += "║ Key Evidence:{' ':<50} ║\n"
        for evidence in self.key_evidence[:4]:
            report += f"║   • {evidence:<57} ║\n"
        
        report += f"""╠══════════════════════════════════════════════════════════════════╣
║ RECOMMENDED ACTION                                               ║
╠──────────────────────────────────────────────────────────────────╣
║ {self.utility_summary:<63} ║
╚══════════════════════════════════════════════════════════════════╝
"""
        return report


@dataclass
class WorkOrder:
    """Field work order for leak investigation/repair."""
    order_id: str
    alert_id: str
    dma_id: str
    
    # Assignment
    priority: WorkOrderPriority
    status: WorkOrderStatus
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # Task details
    title: str = ""
    description: str = ""
    location: Optional[GeoLocation] = None
    pipe_segment_id: Optional[str] = None
    
    # AI guidance
    investigation_steps: List[str] = field(default_factory=list)
    equipment_needed: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    due_by: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Field results
    leak_confirmed: Optional[LeakConfirmation] = None
    actual_location: Optional[GeoLocation] = None
    photos: List[str] = field(default_factory=list)
    technician_notes: str = ""
    
    # Repair details
    repair_type: Optional[str] = None
    repair_cost: float = 0.0
    repair_duration_hours: float = 0.0


@dataclass 
class EscalationRule:
    """Time-based escalation rule."""
    rule_id: str
    name: str
    severity: AlertSeverity
    initial_status: AlertStatus
    escalate_after_minutes: int
    escalate_to_status: AlertStatus
    notify_roles: List[str]
    notify_channels: List[NotificationChannel]


@dataclass
class Notification:
    """Notification to send."""
    notification_id: str
    recipient_id: str
    channel: NotificationChannel
    subject: str
    message: str
    priority: str = "normal"
    sent_at: Optional[datetime] = None
    delivered: bool = False


# =============================================================================
# ALERT GENERATOR - IWA Water Balance Aligned
# =============================================================================

class AlertGenerator:
    """
    IWA-Aligned Alert Generator for Water Utilities.
    
    "Most AI systems detect anomalies; ours understands water networks,
    NRW categories, and utility operations."
    
    Key differentiators:
    - Classifies detections by IWA NRW category (Real vs Apparent Loss)
    - Emphasizes night analysis (00:00-04:00) per IWA guidelines
    - Incorporates pressure-leakage relationship
    - Outputs in water utility language
    - Recommends IWA-standard interventions
    """
    
    # IWA Night Analysis Window (Minimum Night Flow)
    IWA_NIGHT_START_HOUR = 0   # 00:00
    IWA_NIGHT_END_HOUR = 4     # 04:00
    
    # Thresholds for alert generation
    PROBABILITY_THRESHOLD = 0.5
    HIGH_PROBABILITY_THRESHOLD = 0.75
    CRITICAL_PROBABILITY_THRESHOLD = 0.9
    
    # IWA Pressure Risk Zones (bar) - African context
    PRESSURE_ZONES = {
        "low": (0, 2.5),        # Under-pressure risk
        "optimal": (2.5, 4.0),  # Target zone
        "elevated": (4.0, 5.0), # Increased leakage risk
        "high": (5.0, 6.0),     # High leakage risk
        "critical": (6.0, 15.0) # Very high leakage risk
    }
    
    # Cost parameters (configurable per utility - Zambia/SA context)
    WATER_COST_PER_M3 = 2.50  # USD - regional average
    REVENUE_LOSS_MULTIPLIER = 1.5  # Include treatment, pumping costs
    
    def __init__(self, min_probability: float = 0.5, water_cost_per_m3: float = 2.50):
        self.min_probability = min_probability
        self.water_cost_per_m3 = water_cost_per_m3
        self.alert_count = 0
    
    def generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        year = datetime.now().year
        self.alert_count += 1
        return f"NRW-{year}-{self.alert_count:06d}"  # NRW prefix for water utility context
    
    def _is_night_window(self, timestamp: datetime) -> bool:
        """Check if timestamp is within IWA night analysis window (00:00-04:00)."""
        return self.IWA_NIGHT_START_HOUR <= timestamp.hour < self.IWA_NIGHT_END_HOUR
    
    def _get_pressure_risk_zone(self, pressure_bar: float) -> str:
        """Classify pressure into risk zone."""
        for zone, (low, high) in self.PRESSURE_ZONES.items():
            if low <= pressure_bar < high:
                return zone
        return "unknown"
    
    def _classify_nrw_category(
        self,
        feature_contributions: Dict[str, float],
        detection_type: str,
        is_night: bool,
        pressure_bar: Optional[float] = None
    ) -> tuple[NRWCategory, InterventionType, str]:
        """
        Classify detection into IWA NRW category.
        
        Returns: (category, recommended_intervention, utility_summary)
        """
        # Analyze feature contributions to determine category
        night_features = sum(
            abs(v) for k, v in feature_contributions.items() 
            if 'night' in k.lower() or 'mnf' in k.lower()
        )
        pressure_features = sum(
            abs(v) for k, v in feature_contributions.items()
            if 'pressure' in k.lower() or 'gradient' in k.lower()
        )
        flow_features = sum(
            abs(v) for k, v in feature_contributions.items()
            if 'flow' in k.lower()
        )
        meter_features = sum(
            abs(v) for k, v in feature_contributions.items()
            if 'meter' in k.lower() or 'consumption' in k.lower()
        )
        
        total = night_features + pressure_features + flow_features + meter_features + 0.001
        
        # Decision logic based on feature patterns
        if night_features / total > 0.4 and is_night:
            # Strong night signal during MNF window = likely Real Loss (leakage)
            if pressure_features / total > 0.3:
                return (
                    NRWCategory.REAL_LOSS_LEAKAGE,
                    InterventionType.ACOUSTIC_SURVEY,
                    "Suspected distribution main leakage. MNF anomaly with pressure drop pattern. "
                    "Recommend acoustic survey in affected zone."
                )
            else:
                return (
                    NRWCategory.REAL_LOSS_SERVICE,
                    InterventionType.ACTIVE_LEAK_DETECTION,
                    "Suspected service connection leak. MNF elevated without main pressure impact. "
                    "Recommend step-testing to isolate affected connections."
                )
        
        elif pressure_features / total > 0.5:
            # Dominant pressure signal
            if pressure_bar and pressure_bar < 2.0:
                return (
                    NRWCategory.REAL_LOSS_LEAKAGE,
                    InterventionType.INFRASTRUCTURE_REPAIR,
                    "Significant pressure loss detected. Possible main break or major leak. "
                    "Recommend immediate visual inspection of pipeline route."
                )
            else:
                return (
                    NRWCategory.REAL_LOSS_LEAKAGE,
                    InterventionType.PRESSURE_MANAGEMENT,
                    "Pressure anomaly detected. Consider pressure management intervention "
                    "and acoustic survey for leak detection."
                )
        
        elif meter_features / total > 0.3:
            # Meter-related patterns
            if flow_features / total > 0.2:
                return (
                    NRWCategory.APPARENT_LOSS_METER,
                    InterventionType.METER_TESTING,
                    "Suspected meter under-registration. Flow-consumption mismatch detected. "
                    "Recommend meter accuracy testing and calibration check."
                )
            else:
                return (
                    NRWCategory.APPARENT_LOSS_UNAUTHORIZED,
                    InterventionType.UNAUTHORIZED_USE_SURVEY,
                    "Suspected unauthorized consumption. Consumption pattern anomaly. "
                    "Recommend customer audit and connection survey."
                )
        
        elif 'overflow' in detection_type.lower() or 'tank' in str(feature_contributions.keys()).lower():
            return (
                NRWCategory.REAL_LOSS_OVERFLOW,
                InterventionType.TANK_LEVEL_CONTROL,
                "Suspected reservoir/tank overflow. Check level sensors and inlet valve controls. "
                "Verify SCADA alerts and telemetry."
            )
        
        else:
            # Default - requires investigation
            return (
                NRWCategory.UNKNOWN,
                InterventionType.FIELD_INVESTIGATION,
                "NRW detection requires field investigation. Pattern does not clearly indicate "
                "Real or Apparent Loss category. Recommend combined acoustic and meter survey."
            )
    
    def should_generate_alert(
        self,
        probability: float,
        confidence: float,
        estimated_loss: float,
        is_night_detection: bool = False
    ) -> bool:
        """
        Determine if detection warrants an alert.
        
        IWA Consideration: Night detections have higher confidence.
        """
        # Night detection bonus - MNF analysis is more reliable
        effective_confidence = confidence * 1.2 if is_night_detection else confidence
        effective_confidence = min(effective_confidence, 1.0)
        
        # High probability always generates alert
        if probability >= self.HIGH_PROBABILITY_THRESHOLD:
            return True
        
        # Medium probability requires high confidence
        if probability >= self.min_probability and effective_confidence >= 0.7:
            return True
        
        # Large estimated loss generates alert
        if estimated_loss > 100 and probability >= 0.4:  # >100 m³/day
            return True
        
        # Night detection with moderate probability
        if is_night_detection and probability >= 0.45 and confidence >= 0.6:
            return True
        
        return False
    
    def determine_severity(
        self,
        probability: float,
        estimated_loss: float,
        nrw_category: NRWCategory,
        pipe_criticality: str = "normal",
        pressure_risk: str = "optimal"
    ) -> AlertSeverity:
        """
        Determine alert severity based on IWA-aligned criteria.
        
        Real Losses generally more urgent than Apparent Losses.
        """
        # Critical pipe always high priority
        if pipe_criticality == "critical":
            if probability >= self.HIGH_PROBABILITY_THRESHOLD:
                return AlertSeverity.CRITICAL
            return AlertSeverity.HIGH
        
        # Real losses are more urgent
        is_real_loss = nrw_category in [
            NRWCategory.REAL_LOSS_LEAKAGE,
            NRWCategory.REAL_LOSS_OVERFLOW,
            NRWCategory.REAL_LOSS_SERVICE
        ]
        
        # Pressure in critical zone increases severity
        pressure_severity_boost = pressure_risk in ["high", "critical"]
        
        # Based on probability, loss, and category
        if probability >= self.CRITICAL_PROBABILITY_THRESHOLD:
            return AlertSeverity.CRITICAL
        elif probability >= self.HIGH_PROBABILITY_THRESHOLD and is_real_loss:
            return AlertSeverity.CRITICAL if pressure_severity_boost else AlertSeverity.HIGH
        elif estimated_loss > 100:
            return AlertSeverity.CRITICAL
        elif estimated_loss > 50 or (is_real_loss and probability >= 0.6):
            return AlertSeverity.HIGH
        elif probability >= 0.5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def estimate_loss_iwa(
        self,
        probability: float,
        pipe_diameter_mm: float,
        nrw_category: NRWCategory,
        pressure_bar: float = 4.0,
        leak_type: str = "unknown"
    ) -> tuple[float, float]:
        """
        Estimate water loss using IWA methodology.
        
        Returns: (daily_loss_m3, annual_loss_m3)
        
        IWA Pressure-Leakage Relationship: L = C × P^N1
        Where N1 typically 0.5 (fixed) to 1.5 (flexible pipes)
        """
        # Base loss estimates by NRW category (m³/day)
        base_loss_by_category = {
            NRWCategory.REAL_LOSS_LEAKAGE: 50.0,      # Main leakage
            NRWCategory.REAL_LOSS_OVERFLOW: 100.0,    # Tank overflow can be significant
            NRWCategory.REAL_LOSS_SERVICE: 15.0,      # Service connection - smaller
            NRWCategory.APPARENT_LOSS_METER: 20.0,    # Meter error - varies
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: 10.0,  # Theft - varies
            NRWCategory.UNKNOWN: 30.0
        }
        
        base_loss = base_loss_by_category.get(nrw_category, 30.0)
        
        # Scale by pipe diameter (larger pipes = larger potential loss)
        diameter_factor = (pipe_diameter_mm / 150.0) ** 0.5  # Normalized to 150mm
        
        # IWA Pressure adjustment (N1 factor)
        # L = C × P^N1, using N1 = 1.0 for moderate estimate
        pressure_factor = (pressure_bar / 4.0) ** 1.0  # Normalized to 4 bar
        
        # Scale by probability
        daily_loss = base_loss * diameter_factor * pressure_factor * probability
        annual_loss = daily_loss * 365
        
        return daily_loss, annual_loss
    
    def estimate_revenue_loss(self, water_loss_m3_day: float) -> tuple[float, float]:
        """
        Estimate revenue loss (daily and annual).
        
        Returns: (daily_revenue_loss, annual_revenue_loss)
        """
        daily = water_loss_m3_day * self.water_cost_per_m3 * self.REVENUE_LOSS_MULTIPLIER
        annual = daily * 365
        return daily, annual
    
    def create_alert(
        self,
        dma_id: str,
        detection_type: str,
        probability: float,
        confidence: float,
        feature_contributions: Dict[str, float],
        pipe_segment_id: Optional[str] = None,
        location: Optional[GeoLocation] = None,
        pipe_diameter_mm: float = 150.0,
        pipe_criticality: str = "normal",
        pressure_bar: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[Alert]:
        """
        Create an IWA-aligned NRW alert.
        
        Outputs in water utility language with NRW categorization.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Determine if night detection (high confidence window)
        is_night = self._is_night_window(timestamp)
        
        # Get pressure risk zone
        pressure_risk = self._get_pressure_risk_zone(pressure_bar) if pressure_bar else "unknown"
        
        # Classify into IWA NRW category
        nrw_category, intervention, utility_summary = self._classify_nrw_category(
            feature_contributions, detection_type, is_night, pressure_bar
        )
        
        # Estimate loss using IWA methodology
        daily_loss, annual_loss = self.estimate_loss_iwa(
            probability, pipe_diameter_mm, nrw_category, 
            pressure_bar or 4.0
        )
        
        # Check if alert warranted
        if not self.should_generate_alert(probability, confidence, daily_loss, is_night):
            logger.debug(f"Detection below threshold, no alert generated")
            return None
        
        # Determine severity with IWA context
        severity = self.determine_severity(
            probability, daily_loss, nrw_category, 
            pipe_criticality, pressure_risk
        )
        
        # Estimate revenue impact
        daily_revenue, annual_revenue = self.estimate_revenue_loss(daily_loss)
        
        # Generate key evidence in water utility language
        key_evidence = self._generate_evidence_iwa(feature_contributions, is_night)
        
        # Calculate MNF deviation if night detection
        mnf_deviation = 0.0
        if is_night and 'mnf_deviation' in feature_contributions:
            mnf_deviation = feature_contributions['mnf_deviation'] * 100
        
        # Create IWA-aligned alert
        alert = Alert(
            alert_id=self.generate_alert_id(),
            dma_id=dma_id,
            timestamp=timestamp,
            severity=severity,
            status=AlertStatus.NEW,
            nrw_category=nrw_category,
            recommended_intervention=intervention,
            detection_type=detection_type,
            probability=probability,
            confidence=confidence,
            is_night_detection=is_night,
            mnf_deviation_percent=mnf_deviation,
            pressure_bar=pressure_bar,
            pressure_risk_zone=pressure_risk,
            pipe_segment_id=pipe_segment_id,
            location=location,
            estimated_loss_m3_day=daily_loss,
            estimated_loss_m3_year=annual_loss,
            estimated_revenue_loss_daily=daily_revenue,
            estimated_revenue_loss_annual=annual_revenue,
            key_evidence=key_evidence,
            feature_contributions=feature_contributions,
            utility_summary=utility_summary
        )
        
        logger.info(
            f"Generated {severity.value} NRW alert: {alert.alert_id} | "
            f"Category: {nrw_category.value} | DMA: {dma_id} | "
            f"Est. Loss: {daily_loss:.1f} m³/day"
        )
        
        return alert
    
    def _generate_evidence_iwa(
        self, 
        contributions: Dict[str, float],
        is_night: bool
    ) -> List[str]:
        """Generate water-utility-focused evidence from feature contributions."""
        
        evidence = []
        
        # Sort by absolute contribution
        sorted_features = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]  # Top 5
        
        # Map feature names to IWA/utility-focused descriptions
        feature_descriptions = {
            # Pressure features
            "night_pressure_avg": "Night pressure {} than baseline (MNF period)",
            "day_pressure_avg": "Day pressure {} than baseline",
            "night_day_ratio": "Night/day pressure ratio indicates possible night leakage",
            "gradient_downstream": "Downstream pressure gradient increased (headloss)",
            "pressure_variance_24h": "Pressure instability detected (24h variance elevated)",
            
            # Flow/MNF features
            "mnf_deviation": "Minimum Night Flow (MNF) deviation from expected",
            "flow_rate_deviation": "Flow rate deviation from normal pattern",
            "night_flow_elevated": "Night flow elevated above legitimate demand",
            
            # Consumption features
            "consumption_pattern": "Customer consumption pattern anomaly",
            "meter_reading_variance": "Meter reading variance detected",
            
            # Baseline features
            "baseline_deviation": "Sustained deviation from historical baseline",
            "seasonal_deviation": "Deviation from seasonal normal"
        }
        
        for feature, value in sorted_features:
            if abs(value) > 0.1:  # Only significant contributions
                desc = feature_descriptions.get(feature, f"{feature} anomaly detected")
                if "than baseline" in desc or "than expected" in desc:
                    direction = "lower" if value > 0 else "higher"
                    desc = desc.format(direction)
                evidence.append(desc)
        
        # Add night context if applicable
        if is_night:
            evidence.insert(0, "⏰ Detected during MNF window (00:00-04:00) - HIGH CONFIDENCE")
        
        return evidence


# =============================================================================
# WORK ORDER MANAGER - IWA Aligned
# =============================================================================

class WorkOrderManager:
    """
    IWA-Aligned Work Order Management.
    
    Creates work orders that speak water utility language:
    - NRW category context
    - IWA-recommended interventions
    - Equipment for Real vs Apparent Loss investigation
    """
    
    def __init__(self):
        self.work_orders: Dict[str, WorkOrder] = {}
        self.order_count = 0
    
    def generate_order_id(self) -> str:
        """Generate unique work order ID."""
        year = datetime.now().year
        self.order_count += 1
        return f"NRW-WO-{year}-{self.order_count:05d}"  # NRW-prefixed for utility context
    
    def create_from_alert(self, alert: Alert) -> WorkOrder:
        """Create an IWA-aligned work order from an NRW alert."""
        
        # Map alert severity to work order priority
        priority_map = {
            AlertSeverity.CRITICAL: WorkOrderPriority.EMERGENCY,
            AlertSeverity.HIGH: WorkOrderPriority.HIGH,
            AlertSeverity.MEDIUM: WorkOrderPriority.NORMAL,
            AlertSeverity.LOW: WorkOrderPriority.LOW
        }
        
        # IWA-adjusted due dates based on NRW category
        # Real losses generally need faster response
        due_hours_real = {
            WorkOrderPriority.EMERGENCY: 4,
            WorkOrderPriority.HIGH: 12,
            WorkOrderPriority.NORMAL: 48,
            WorkOrderPriority.LOW: 120  # 5 days
        }
        due_hours_apparent = {
            WorkOrderPriority.EMERGENCY: 8,
            WorkOrderPriority.HIGH: 24,
            WorkOrderPriority.NORMAL: 72,
            WorkOrderPriority.LOW: 168  # 1 week
        }
        
        priority = priority_map.get(alert.severity, WorkOrderPriority.NORMAL)
        
        # Select due hours based on NRW category
        is_real_loss = alert.nrw_category in [
            NRWCategory.REAL_LOSS_LEAKAGE,
            NRWCategory.REAL_LOSS_OVERFLOW,
            NRWCategory.REAL_LOSS_SERVICE
        ]
        due_hours = due_hours_real if is_real_loss else due_hours_apparent
        
        # Generate IWA-aligned investigation steps
        steps = self._generate_investigation_steps_iwa(alert)
        equipment = self._recommend_equipment_iwa(alert)
        
        # Generate IWA-aligned title
        title = self._generate_title_iwa(alert)
        
        work_order = WorkOrder(
            order_id=self.generate_order_id(),
            alert_id=alert.alert_id,
            dma_id=alert.dma_id,
            priority=priority,
            status=WorkOrderStatus.PENDING,
            title=title,
            description=self._generate_description_iwa(alert),
            location=alert.location,
            pipe_segment_id=alert.pipe_segment_id,
            investigation_steps=steps,
            equipment_needed=equipment,
            due_by=datetime.now() + timedelta(hours=due_hours[priority])
        )
        
        # Update alert
        alert.work_order_id = work_order.order_id
        alert.status = AlertStatus.ASSIGNED
        
        # Store
        self.work_orders[work_order.order_id] = work_order
        
        logger.info(
            f"Created work order {work_order.order_id} | "
            f"NRW Category: {alert.nrw_category.value} | "
            f"Alert: {alert.alert_id}"
        )
        
        return work_order
    
    def _generate_title_iwa(self, alert: Alert) -> str:
        """Generate IWA-aligned work order title."""
        
        category_titles = {
            NRWCategory.REAL_LOSS_LEAKAGE: "Real Loss Investigation - Distribution Leakage",
            NRWCategory.REAL_LOSS_OVERFLOW: "Real Loss Investigation - Tank/Reservoir Overflow",
            NRWCategory.REAL_LOSS_SERVICE: "Real Loss Investigation - Service Connection",
            NRWCategory.APPARENT_LOSS_METER: "Apparent Loss Investigation - Meter Accuracy",
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: "Apparent Loss Investigation - Unauthorized Use",
            NRWCategory.UNKNOWN: "NRW Investigation - Category TBD"
        }
        
        return category_titles.get(alert.nrw_category, f"NRW Investigation - {alert.dma_id}")
    
    def _generate_description_iwa(self, alert: Alert) -> str:
        """Generate IWA-aligned work order description."""
        
        category_labels = {
            NRWCategory.REAL_LOSS_LEAKAGE: "Real Loss - Distribution Main Leakage",
            NRWCategory.REAL_LOSS_OVERFLOW: "Real Loss - Tank/Reservoir Overflow",
            NRWCategory.REAL_LOSS_SERVICE: "Real Loss - Service Connection Leak",
            NRWCategory.APPARENT_LOSS_METER: "Apparent Loss - Meter Under-registration",
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: "Apparent Loss - Unauthorized Consumption",
            NRWCategory.UNKNOWN: "Under Investigation"
        }
        
        intervention_labels = {
            InterventionType.ACTIVE_LEAK_DETECTION: "Active Leak Detection Survey",
            InterventionType.ACOUSTIC_SURVEY: "Acoustic Leak Survey",
            InterventionType.PRESSURE_MANAGEMENT: "Pressure Management Review",
            InterventionType.INFRASTRUCTURE_REPAIR: "Infrastructure Inspection/Repair",
            InterventionType.TANK_LEVEL_CONTROL: "Tank Level Control Check",
            InterventionType.METER_TESTING: "Meter Accuracy Testing",
            InterventionType.METER_REPLACEMENT: "Meter Replacement Assessment",
            InterventionType.UNAUTHORIZED_USE_SURVEY: "Unauthorized Use Survey",
            InterventionType.DATA_VALIDATION: "Data Validation Check",
            InterventionType.FIELD_INVESTIGATION: "General Field Investigation"
        }
        
        night_context = ""
        if alert.is_night_detection:
            night_context = f"""
🌙 NIGHT DETECTION (MNF Analysis)
   Detection occurred during 00:00-04:00 MNF window
   MNF Deviation: {alert.mnf_deviation_percent:+.1f}%
   Confidence: HIGH (reduced legitimate demand during night)
"""
        
        pressure_context = ""
        if alert.pressure_bar:
            pressure_context = f"""
📊 PRESSURE CONTEXT
   Current Pressure: {alert.pressure_bar:.2f} bar
   Risk Zone: {alert.pressure_risk_zone.upper()}
   Note: Higher pressure increases Real Loss rate (IWA N1 factor)
"""
        
        desc = f"""
════════════════════════════════════════════════════════════════════
                      NRW WORK ORDER
════════════════════════════════════════════════════════════════════

ALERT REFERENCE: {alert.alert_id}
DMA: {alert.dma_id}
DETECTION TIME: {alert.timestamp.strftime('%Y-%m-%d %H:%M')}

────────────────────────────────────────────────────────────────────
IWA WATER BALANCE CLASSIFICATION
────────────────────────────────────────────────────────────────────
NRW Category: {category_labels.get(alert.nrw_category, 'Unknown')}
Recommended Intervention: {intervention_labels.get(alert.recommended_intervention, 'Field Investigation')}

Detection Confidence: {alert.probability:.0%} probability, {alert.confidence:.0%} confidence
{night_context}
{pressure_context}
────────────────────────────────────────────────────────────────────
ESTIMATED NRW IMPACT
────────────────────────────────────────────────────────────────────
Daily Water Loss: {alert.estimated_loss_m3_day:,.1f} m³/day
Annual Water Loss: {alert.estimated_loss_m3_year:,.0f} m³/year
Daily Revenue Loss: ${alert.estimated_revenue_loss_daily:,.2f}/day
Annual Revenue Loss: ${alert.estimated_revenue_loss_annual:,.2f}/year

────────────────────────────────────────────────────────────────────
KEY EVIDENCE (AI Analysis)
────────────────────────────────────────────────────────────────────
{chr(10).join('• ' + e for e in alert.key_evidence)}

────────────────────────────────────────────────────────────────────
ACTION SUMMARY
────────────────────────────────────────────────────────────────────
{alert.utility_summary}

════════════════════════════════════════════════════════════════════
FIELD TEAM INSTRUCTIONS: See investigation steps and required equipment.
Confirm or deny detection and document all findings.
════════════════════════════════════════════════════════════════════
        """.strip()
        
        return desc
    
    def _generate_investigation_steps_iwa(self, alert: Alert) -> List[str]:
        """Generate IWA-aligned investigation steps based on NRW category."""
        
        # Base steps by NRW category
        category_steps = {
            NRWCategory.REAL_LOSS_LEAKAGE: [
                "Navigate to DMA sector indicated in alert",
                "Perform visual inspection for: wet spots, road settlement, vegetation changes",
                "Deploy acoustic equipment (ground microphone/correlator)",
                "Sound valves and fittings along suspected pipeline section",
                "Check pressure at hydrants upstream and downstream of suspected area",
                "If leak located: Mark position with GPS coordinates",
                "Estimate leak severity (seeping/running/spraying)",
                "Document with photos and submit field confirmation"
            ],
            NRWCategory.REAL_LOSS_OVERFLOW: [
                "Proceed to reservoir/tank identified in alert",
                "Check current water level vs. setpoint",
                "Verify level sensor readings match physical level",
                "Inspect inlet valve operation (automatic shutoff)",
                "Check overflow pipe for recent discharge evidence",
                "Review SCADA alarm history for past 7 days",
                "Verify telemetry communication status",
                "Document findings and recommend control adjustments"
            ],
            NRWCategory.REAL_LOSS_SERVICE: [
                "Navigate to service connection area",
                "Perform step-test to isolate affected section",
                "Visual inspection of service connections and meter boxes",
                "Listen at stop taps and ferrules with acoustic stick",
                "Check for wet areas around connection points",
                "Verify meter readings match consumption records",
                "If leak found: Mark for repair and estimate loss rate",
                "Document location and severity"
            ],
            NRWCategory.APPARENT_LOSS_METER: [
                "Locate customer meter(s) identified in alert",
                "Record current meter reading",
                "Perform visual inspection for damage or tampering",
                "Check meter installation (bypass, positioning)",
                "Conduct accuracy test with portable test meter",
                "Check for air in pipes (over-registration) or low flow issues",
                "Review customer consumption history for anomalies",
                "Recommend replacement if accuracy <98%"
            ],
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: [
                "Survey area for illegal connections",
                "Check meter seals and installation integrity",
                "Look for bypass pipes or direct connections",
                "Verify all connected properties have registered meters",
                "Interview property owners if suspicious findings",
                "Document evidence with photos and GPS coordinates",
                "Report to revenue protection team if confirmed",
                "Coordinate with enforcement if needed"
            ],
            NRWCategory.UNKNOWN: [
                "Conduct general area survey",
                "Perform both acoustic and visual inspection",
                "Check nearby meters for anomalies",
                "Review pressure readings at zone entry point",
                "Document all observations for AI feedback",
                "Recommend follow-up investigation type based on findings"
            ]
        }
        
        steps = category_steps.get(alert.nrw_category, category_steps[NRWCategory.UNKNOWN])
        
        # Add priority-specific steps
        if alert.severity == AlertSeverity.CRITICAL:
            steps.insert(0, "⚠️ CRITICAL: Immediate response required - potential major loss")
        
        if alert.estimated_loss_m3_day > 100:
            steps.append("Prepare for potential excavation if Real Loss confirmed")
            steps.append("Notify repair crew to be on standby")
        
        return steps
    
    def _recommend_equipment_iwa(self, alert: Alert) -> List[str]:
        """Recommend equipment based on IWA NRW category."""
        
        # Base equipment by category
        category_equipment = {
            NRWCategory.REAL_LOSS_LEAKAGE: [
                "Ground microphone",
                "Acoustic correlator (if available)",
                "Listening stick",
                "Pressure gauge (0-10 bar)",
                "GPS device",
                "Camera/smartphone for documentation",
                "Hi-vis vest and safety equipment",
                "Valve key for hydrant access"
            ],
            NRWCategory.REAL_LOSS_OVERFLOW: [
                "Portable level measurement device",
                "Camera for visual documentation",
                "SCADA access credentials",
                "Valve operating key",
                "Safety harness (if tank access required)",
                "Radio/phone for control room communication"
            ],
            NRWCategory.REAL_LOSS_SERVICE: [
                "Listening stick",
                "Stop tap key",
                "Small acoustic equipment",
                "Meter reading device",
                "Pressure gauge",
                "Camera for documentation",
                "Excavation marking spray"
            ],
            NRWCategory.APPARENT_LOSS_METER: [
                "Portable test meter",
                "Meter reading device",
                "Seal kit for resealing",
                "Customer database access",
                "Calculator for accuracy calculation",
                "Camera for documentation",
                "Meter replacement forms"
            ],
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: [
                "Pipe and cable locator",
                "Camera for evidence documentation",
                "GPS device",
                "Customer database access",
                "Official ID/authorization documents",
                "Report forms",
                "Phone for coordination"
            ],
            NRWCategory.UNKNOWN: [
                "Listening stick",
                "Pressure gauge",
                "GPS device",
                "Camera",
                "Meter reading device",
                "General hand tools"
            ]
        }
        
        return category_equipment.get(alert.nrw_category, category_equipment[NRWCategory.UNKNOWN])
    
    def assign_work_order(
        self,
        order_id: str,
        technician_id: str
    ) -> bool:
        """Assign work order to technician."""
        
        if order_id not in self.work_orders:
            return False
        
        work_order = self.work_orders[order_id]
        work_order.assigned_to = technician_id
        work_order.assigned_at = datetime.now()
        work_order.status = WorkOrderStatus.ASSIGNED
        
        logger.info(f"Assigned {order_id} to technician {technician_id}")
        
        return True
    
    def update_status(
        self,
        order_id: str,
        status: WorkOrderStatus
    ) -> bool:
        """Update work order status."""
        
        if order_id not in self.work_orders:
            return False
        
        work_order = self.work_orders[order_id]
        old_status = work_order.status
        work_order.status = status
        
        # Track timing
        if status == WorkOrderStatus.ON_SITE:
            work_order.started_at = datetime.now()
        elif status == WorkOrderStatus.COMPLETED:
            work_order.completed_at = datetime.now()
        
        logger.info(f"Updated {order_id} status: {old_status.value} -> {status.value}")
        
        return True
    
    def complete_work_order(
        self,
        order_id: str,
        leak_confirmed: LeakConfirmation,
        actual_location: Optional[GeoLocation] = None,
        technician_notes: str = "",
        photos: List[str] = None
    ) -> bool:
        """Complete a work order with field results."""
        
        if order_id not in self.work_orders:
            return False
        
        work_order = self.work_orders[order_id]
        work_order.status = WorkOrderStatus.COMPLETED
        work_order.completed_at = datetime.now()
        work_order.leak_confirmed = leak_confirmed
        work_order.actual_location = actual_location
        work_order.technician_notes = technician_notes
        work_order.photos = photos or []
        
        logger.info(f"Completed {order_id} with result: {leak_confirmed.value}")
        
        return True


# =============================================================================
# FEEDBACK PROCESSOR
# =============================================================================

class FeedbackProcessor:
    """
    Processes field feedback to improve AI models.
    
    Key feedback types:
    1. True Positive - Leak confirmed at predicted location
    2. Near Miss - Leak found nearby (within 100m)
    3. False Positive - No leak found
    4. Inconclusive - Need more investigation
    """
    
    def __init__(self):
        self.feedback_records: List[Dict] = []
    
    def process_work_order_completion(
        self,
        work_order: WorkOrder,
        alert: Alert
    ) -> Dict:
        """Process completed work order to generate feedback record."""
        
        # Calculate localization accuracy
        localization_accuracy = None
        if work_order.actual_location and alert.location:
            distance = alert.location.distance_to(work_order.actual_location)
            localization_accuracy = distance
        
        # Create feedback record
        feedback = {
            "feedback_id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "alert_id": alert.alert_id,
            "work_order_id": work_order.order_id,
            "dma_id": alert.dma_id,
            
            # Original prediction
            "predicted_probability": alert.probability,
            "predicted_confidence": alert.confidence,
            "predicted_location": {
                "lat": alert.location.latitude,
                "lon": alert.location.longitude
            } if alert.location else None,
            
            # Actual result
            "leak_confirmed": work_order.leak_confirmed.value,
            "actual_location": {
                "lat": work_order.actual_location.latitude,
                "lon": work_order.actual_location.longitude
            } if work_order.actual_location else None,
            
            # Performance metrics
            "localization_accuracy_m": localization_accuracy,
            "response_time_hours": (
                (work_order.started_at - alert.timestamp).total_seconds() / 3600
                if work_order.started_at else None
            ),
            "resolution_time_hours": (
                (work_order.completed_at - alert.timestamp).total_seconds() / 3600
                if work_order.completed_at else None
            ),
            
            # Classification
            "classification": self._classify_result(work_order.leak_confirmed),
            
            # Feature contributions (for model retraining)
            "feature_contributions": alert.feature_contributions,
            
            # Notes
            "technician_notes": work_order.technician_notes
        }
        
        self.feedback_records.append(feedback)
        
        logger.info(
            f"Processed feedback for {alert.alert_id}: "
            f"{feedback['classification']}"
        )
        
        return feedback
    
    def _classify_result(self, confirmation: LeakConfirmation) -> str:
        """Classify the result for model training."""
        
        classification_map = {
            LeakConfirmation.CONFIRMED: "true_positive",
            LeakConfirmation.CONFIRMED_NEARBY: "true_positive_offset",
            LeakConfirmation.NOT_FOUND: "false_positive",
            LeakConfirmation.INCONCLUSIVE: "inconclusive"
        }
        
        return classification_map.get(confirmation, "unknown")
    
    def get_performance_metrics(self) -> Dict:
        """Calculate model performance metrics from feedback."""
        
        if not self.feedback_records:
            return {}
        
        # Count classifications
        total = len(self.feedback_records)
        true_positives = sum(
            1 for f in self.feedback_records 
            if f['classification'] in ('true_positive', 'true_positive_offset')
        )
        false_positives = sum(
            1 for f in self.feedback_records 
            if f['classification'] == 'false_positive'
        )
        inconclusive = sum(
            1 for f in self.feedback_records 
            if f['classification'] == 'inconclusive'
        )
        
        # Calculate precision
        precision = true_positives / max(true_positives + false_positives, 1)
        
        # Localization accuracy
        accuracies = [
            f['localization_accuracy_m'] 
            for f in self.feedback_records 
            if f['localization_accuracy_m'] is not None
        ]
        
        avg_localization = sum(accuracies) / len(accuracies) if accuracies else None
        
        return {
            "total_feedback": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "inconclusive": inconclusive,
            "precision": precision,
            "avg_localization_accuracy_m": avg_localization,
            "within_50m_rate": (
                sum(1 for a in accuracies if a <= 50) / len(accuracies)
                if accuracies else None
            )
        }
    
    def export_for_retraining(self) -> List[Dict]:
        """Export feedback records for model retraining."""
        
        # Filter to confirmed results only (exclude inconclusive)
        training_records = [
            f for f in self.feedback_records
            if f['classification'] in ('true_positive', 'true_positive_offset', 'false_positive')
        ]
        
        return training_records


# =============================================================================
# ESCALATION ENGINE
# =============================================================================

class EscalationEngine:
    """
    Handles time-based escalation of alerts.
    
    Rules:
    - Critical alerts escalate to emergency after 1 hour
    - High alerts escalate after 4 hours
    - Unacknowledged alerts notify supervisors
    """
    
    def __init__(self):
        self.rules: List[EscalationRule] = self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> List[EscalationRule]:
        """Initialize default escalation rules."""
        
        return [
            # Critical alerts
            EscalationRule(
                rule_id="ESC-001",
                name="Critical Unacknowledged",
                severity=AlertSeverity.CRITICAL,
                initial_status=AlertStatus.NEW,
                escalate_after_minutes=30,
                escalate_to_status=AlertStatus.NEW,  # Remains new but escalates
                notify_roles=["supervisor", "manager"],
                notify_channels=[NotificationChannel.SMS, NotificationChannel.PUSH]
            ),
            
            # High alerts
            EscalationRule(
                rule_id="ESC-002",
                name="High Unacknowledged",
                severity=AlertSeverity.HIGH,
                initial_status=AlertStatus.NEW,
                escalate_after_minutes=120,  # 2 hours
                escalate_to_status=AlertStatus.NEW,
                notify_roles=["supervisor"],
                notify_channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH]
            ),
            
            # Acknowledged but not assigned
            EscalationRule(
                rule_id="ESC-003",
                name="Acknowledged Not Assigned",
                severity=AlertSeverity.CRITICAL,
                initial_status=AlertStatus.ACKNOWLEDGED,
                escalate_after_minutes=60,
                escalate_to_status=AlertStatus.ACKNOWLEDGED,
                notify_roles=["dispatcher", "supervisor"],
                notify_channels=[NotificationChannel.PUSH]
            )
        ]
    
    def check_escalations(self, alerts: List[Alert]) -> List[Notification]:
        """Check alerts against escalation rules and generate notifications."""
        
        notifications = []
        now = datetime.now()
        
        for alert in alerts:
            for rule in self.rules:
                if self._rule_applies(alert, rule, now):
                    # Generate notifications
                    for role in rule.notify_roles:
                        for channel in rule.notify_channels:
                            notification = self._create_notification(
                                alert, rule, role, channel
                            )
                            notifications.append(notification)
        
        return notifications
    
    def _rule_applies(self, alert: Alert, rule: EscalationRule, now: datetime) -> bool:
        """Check if escalation rule applies to alert."""
        
        # Check severity match
        if alert.severity != rule.severity:
            return False
        
        # Check status match
        if alert.status != rule.initial_status:
            return False
        
        # Check time threshold
        age_minutes = (now - alert.timestamp).total_seconds() / 60
        if age_minutes < rule.escalate_after_minutes:
            return False
        
        return True
    
    def _create_notification(
        self,
        alert: Alert,
        rule: EscalationRule,
        role: str,
        channel: NotificationChannel
    ) -> Notification:
        """Create escalation notification."""
        
        return Notification(
            notification_id=str(uuid4()),
            recipient_id=role,  # In production, resolve to actual user
            channel=channel,
            subject=f"ESCALATION: {alert.severity.value.upper()} Alert {alert.alert_id}",
            message=(
                f"Alert {alert.alert_id} requires attention.\n"
                f"DMA: {alert.dma_id}\n"
                f"Probability: {alert.probability:.0%}\n"
                f"Age: {(datetime.now() - alert.timestamp).total_seconds() / 60:.0f} minutes\n"
                f"Rule: {rule.name}"
            ),
            priority="high"
        )


# =============================================================================
# WORKFLOW ENGINE (MAIN ORCHESTRATOR)
# =============================================================================

class WorkflowEngine:
    """
    Main orchestrator for the operations workflow.
    
    Coordinates:
    - Alert generation
    - Work order creation
    - Escalations
    - Feedback processing
    - Notifications
    """
    
    def __init__(self):
        self.alert_generator = AlertGenerator()
        self.work_order_manager = WorkOrderManager()
        self.feedback_processor = FeedbackProcessor()
        self.escalation_engine = EscalationEngine()
        
        self.alerts: Dict[str, Alert] = {}
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
    
    def register_notification_handler(
        self,
        channel: NotificationChannel,
        handler: Callable[[Notification], bool]
    ):
        """Register a notification handler for a channel."""
        self.notification_handlers[channel] = handler
    
    def process_detection(
        self,
        dma_id: str,
        detection_type: str,
        probability: float,
        confidence: float,
        feature_contributions: Dict[str, float],
        pipe_segment_id: Optional[str] = None,
        location: Optional[GeoLocation] = None,
        pipe_diameter_mm: float = 150.0,
        pipe_criticality: str = "normal",
        pressure_bar: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        auto_create_work_order: bool = True
    ) -> Optional[str]:
        """
        Process a detection result from the AI layer.
        
        IWA-aligned processing:
        - Classifies into NRW category (Real vs Apparent Loss)
        - Considers night analysis for confidence boost
        - Incorporates pressure-leakage relationship
        
        Returns alert_id if alert was generated.
        """
        
        # Generate IWA-aligned alert
        alert = self.alert_generator.create_alert(
            dma_id=dma_id,
            detection_type=detection_type,
            probability=probability,
            confidence=confidence,
            feature_contributions=feature_contributions,
            pipe_segment_id=pipe_segment_id,
            location=location,
            pipe_diameter_mm=pipe_diameter_mm,
            pipe_criticality=pipe_criticality,
            pressure_bar=pressure_bar,
            timestamp=timestamp
        )
        
        if alert is None:
            return None
        
        # Store alert
        self.alerts[alert.alert_id] = alert
        
        # Auto-create work order for high-priority alerts
        if auto_create_work_order and alert.severity in (
            AlertSeverity.CRITICAL, AlertSeverity.HIGH
        ):
            self.work_order_manager.create_from_alert(alert)
        
        # Send notifications
        self._send_alert_notification(alert)
        
        return alert.alert_id
    
    def _send_alert_notification(self, alert: Alert):
        """Send IWA-aligned notifications for new alert."""
        
        # Determine channels based on severity
        if alert.severity == AlertSeverity.CRITICAL:
            channels = [NotificationChannel.SMS, NotificationChannel.PUSH]
        elif alert.severity == AlertSeverity.HIGH:
            channels = [NotificationChannel.PUSH, NotificationChannel.EMAIL]
        else:
            channels = [NotificationChannel.DASHBOARD]
        
        # IWA category label for notifications
        category_short = {
            NRWCategory.REAL_LOSS_LEAKAGE: "Real Loss - Leakage",
            NRWCategory.REAL_LOSS_OVERFLOW: "Real Loss - Overflow",
            NRWCategory.REAL_LOSS_SERVICE: "Real Loss - Service",
            NRWCategory.APPARENT_LOSS_METER: "Apparent Loss - Meter",
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: "Apparent Loss - Unauthorized",
            NRWCategory.UNKNOWN: "Under Investigation"
        }.get(alert.nrw_category, "Unknown")
        
        for channel in channels:
            notification = Notification(
                notification_id=str(uuid4()),
                recipient_id="operations_team",
                channel=channel,
                subject=f"NRW Alert [{alert.severity.value.upper()}] - {category_short}",
                message=(
                    f"NRW Category: {category_short}\n"
                    f"DMA: {alert.dma_id}\n"
                    f"Probability: {alert.probability:.0%}\n"
                    f"Est. Loss: {alert.estimated_loss_m3_day:.0f} m³/day (${alert.estimated_revenue_loss_daily:.0f}/day)\n"
                    f"{'🌙 Night Detection (HIGH confidence)' if alert.is_night_detection else ''}"
                ),
                priority="high" if alert.severity == AlertSeverity.CRITICAL else "normal"
            )
            
            # Send via registered handler
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    handler(notification)
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert."""
        
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now()
        
        return True
    
    def create_work_order_for_alert(self, alert_id: str) -> Optional[WorkOrder]:
        """Create a work order for an existing alert."""
        
        if alert_id not in self.alerts:
            return None
        
        return self.work_order_manager.create_from_alert(self.alerts[alert_id])
    
    def complete_investigation(
        self,
        order_id: str,
        leak_confirmed: LeakConfirmation,
        actual_location: Optional[GeoLocation] = None,
        technician_notes: str = ""
    ):
        """Complete a work order and process feedback."""
        
        # Complete work order
        self.work_order_manager.complete_work_order(
            order_id,
            leak_confirmed,
            actual_location,
            technician_notes
        )
        
        # Get work order and associated alert
        work_order = self.work_order_manager.work_orders.get(order_id)
        if work_order and work_order.alert_id in self.alerts:
            alert = self.alerts[work_order.alert_id]
            
            # Update alert status
            if leak_confirmed == LeakConfirmation.CONFIRMED:
                alert.status = AlertStatus.RESOLVED
            elif leak_confirmed == LeakConfirmation.NOT_FOUND:
                alert.status = AlertStatus.FALSE_POSITIVE
            else:
                alert.status = AlertStatus.CLOSED
            
            alert.resolution = leak_confirmed
            alert.resolution_notes = technician_notes
            alert.resolved_at = datetime.now()
            
            # Process feedback for model improvement
            self.feedback_processor.process_work_order_completion(work_order, alert)
    
    def run_escalation_check(self):
        """Run escalation check on all active alerts."""
        
        active_alerts = [
            a for a in self.alerts.values()
            if a.status in (AlertStatus.NEW, AlertStatus.ACKNOWLEDGED)
        ]
        
        notifications = self.escalation_engine.check_escalations(active_alerts)
        
        for notification in notifications:
            handler = self.notification_handlers.get(notification.channel)
            if handler:
                try:
                    handler(notification)
                except Exception as e:
                    logger.error(f"Failed to send escalation notification: {e}")
        
        return len(notifications)
    
    def get_performance_report(self) -> Dict:
        """Generate performance report from feedback."""
        return self.feedback_processor.get_performance_metrics()


# =============================================================================
# DEMO FUNCTIONS
# =============================================================================

def demo_workflow():
    """Demonstrate the workflow engine."""
    
    print("=" * 60)
    print("AquaWatch NRW - Workflow Engine Demo")
    print("=" * 60)
    
    # Initialize engine
    engine = WorkflowEngine()
    
    # Register a simple notification handler
    def print_notification(notification: Notification) -> bool:
        print(f"\n📱 NOTIFICATION [{notification.channel.value.upper()}]")
        print(f"   Subject: {notification.subject}")
        print(f"   Message: {notification.message[:100]}...")
        return True
    
    for channel in NotificationChannel:
        engine.register_notification_handler(channel, print_notification)
    
    # Simulate a detection
    print("\n1. Processing AI detection result...")
    
    alert_id = engine.process_detection(
        dma_id="DMA-KIT-015",
        detection_type="leak_probability",
        probability=0.82,
        confidence=0.88,
        feature_contributions={
            "night_pressure_avg": 0.35,
            "night_day_ratio": 0.25,
            "gradient_downstream": 0.20,
            "baseline_deviation": 0.15
        },
        pipe_segment_id="PIPE-1234",
        location=GeoLocation(latitude=-15.4123, longitude=28.2876),
        pipe_diameter_mm=200
    )
    
    if alert_id:
        print(f"\n✓ Alert generated: {alert_id}")
        alert = engine.alerts[alert_id]
        print(f"  Severity: {alert.severity.value}")
        print(f"  Estimated loss: {alert.estimated_loss_m3_day:.0f} m³/day")
        print(f"  Work Order: {alert.work_order_id}")
    
    # Simulate field completion
    print("\n2. Simulating field investigation...")
    
    if alert_id:
        work_order_id = engine.alerts[alert_id].work_order_id
        
        # Technician starts work
        engine.work_order_manager.update_status(work_order_id, WorkOrderStatus.EN_ROUTE)
        engine.work_order_manager.update_status(work_order_id, WorkOrderStatus.ON_SITE)
        
        # Complete investigation
        engine.complete_investigation(
            order_id=work_order_id,
            leak_confirmed=LeakConfirmation.CONFIRMED,
            actual_location=GeoLocation(latitude=-15.4125, longitude=28.2880),
            technician_notes="Leak found at pipe joint. Visible water on surface."
        )
        
        print(f"✓ Investigation completed")
        print(f"  Result: Leak confirmed")
        print(f"  Alert status: {engine.alerts[alert_id].status.value}")
    
    # Show performance metrics
    print("\n3. Performance metrics:")
    metrics = engine.get_performance_report()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    demo_workflow()
