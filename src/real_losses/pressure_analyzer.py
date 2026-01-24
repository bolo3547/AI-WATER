"""
AquaWatch NRW - Pressure Instability Analyzer
=============================================

Advanced pressure monitoring for detecting instability patterns
that may indicate:

- Developing leaks
- Valve problems
- Pump station issues
- PRV malfunctions
- Network hydraulic instability

Alert Types:
1. Sustained Low Pressure - may indicate leak downstream
2. Sustained High Pressure - may cause pipe stress/bursts
3. Pressure Oscillation - waterhammer, pump cycling
4. Pressure Gradient Anomaly - abnormal spatial patterns
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)


class PressureAlertType(Enum):
    """Types of pressure alerts"""
    LOW_PRESSURE = "low_pressure"
    HIGH_PRESSURE = "high_pressure"
    OSCILLATION = "oscillation"
    RAPID_CHANGE = "rapid_change"
    GRADIENT_ANOMALY = "gradient_anomaly"
    SUSTAINED_DEVIATION = "sustained_deviation"


class AlertPriority(Enum):
    """Alert priority levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PressureAlert:
    """Pressure instability alert"""
    alert_id: str
    tenant_id: str
    dma_id: str
    sensor_id: str
    
    # Alert classification
    alert_type: PressureAlertType
    priority: AlertPriority
    
    # Detection details
    detected_at: datetime
    current_pressure_bar: float
    baseline_pressure_bar: float
    deviation_bar: float
    deviation_percent: float
    
    # Duration (for sustained alerts)
    duration_minutes: float = 0
    is_sustained: bool = False
    
    # Additional metrics
    rate_of_change_bar_min: float = 0.0
    oscillation_amplitude_bar: float = 0.0
    oscillation_frequency_hz: float = 0.0
    
    # Location
    sensor_lat: Optional[float] = None
    sensor_lng: Optional[float] = None
    
    # Impact assessment
    affected_customers: int = 0
    service_impact: str = ""  # none, minor, moderate, major
    
    # Status
    status: str = "active"  # active, acknowledged, investigating, resolved
    notes: str = ""
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class PressureZoneStatus:
    """Real-time pressure status for a zone"""
    dma_id: str
    timestamp: datetime
    
    # Aggregate metrics
    avg_pressure_bar: float
    min_pressure_bar: float
    max_pressure_bar: float
    pressure_variance: float
    
    # Sensor count
    sensors_online: int
    sensors_offline: int
    sensors_alert: int
    
    # Zone health
    health_score: float  # 0-100
    status: str  # healthy, warning, critical


class PressureInstabilityAnalyzer:
    """
    Production pressure instability analyzer.
    
    Monitors pressure patterns for signs of:
    - Leaks (pressure drops)
    - Infrastructure stress (high pressure)
    - Equipment problems (oscillation)
    - Network instability (gradients)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with configuration."""
        self.config = config or {}
        
        # Pressure thresholds (bar)
        self.min_acceptable_pressure = self.config.get('min_pressure', 1.5)
        self.max_acceptable_pressure = self.config.get('max_pressure', 6.0)
        self.warning_deviation_pct = self.config.get('warning_deviation_pct', 15)
        self.critical_deviation_pct = self.config.get('critical_deviation_pct', 30)
        
        # Time thresholds
        self.sustained_alert_minutes = self.config.get('sustained_minutes', 15)
        self.rapid_change_threshold = self.config.get('rapid_change_bar_min', 0.2)
        
        # Oscillation thresholds
        self.oscillation_min_amplitude = self.config.get('oscillation_amplitude', 0.3)
        
        # Storage
        self._baselines: Dict[str, float] = {}  # sensor_id -> baseline
        self._history: Dict[str, List[Tuple[datetime, float]]] = {}  # sensor_id -> [(ts, pressure)]
        self._alerts: Dict[str, List[PressureAlert]] = {}  # tenant_id:dma_id -> alerts
        self._zone_status: Dict[str, PressureZoneStatus] = {}  # dma_id -> status
        
        logger.info("PressureInstabilityAnalyzer initialized")
    
    def set_baseline(self, sensor_id: str, baseline_bar: float):
        """Set pressure baseline for a sensor."""
        self._baselines[sensor_id] = baseline_bar
    
    def ingest_reading(
        self,
        tenant_id: str,
        sensor_id: str,
        dma_id: str,
        pressure_bar: float,
        timestamp: Optional[datetime] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None
    ) -> Optional[PressureAlert]:
        """
        Ingest pressure reading and check for alerts.
        
        Returns PressureAlert if instability detected.
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Add to history
        if sensor_id not in self._history:
            self._history[sensor_id] = []
        
        self._history[sensor_id].append((timestamp, pressure_bar))
        
        # Keep 1 hour of history
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._history[sensor_id] = [
            (ts, p) for ts, p in self._history[sensor_id]
            if ts > cutoff
        ]
        
        # Get or compute baseline
        baseline = self._baselines.get(sensor_id)
        if baseline is None:
            history = self._history[sensor_id]
            if len(history) >= 10:
                baseline = statistics.mean([p for _, p in history])
                self._baselines[sensor_id] = baseline
            else:
                return None
        
        # Check for various alert conditions
        alert = self._check_pressure_conditions(
            tenant_id, sensor_id, dma_id,
            pressure_bar, baseline, timestamp,
            lat, lng
        )
        
        if alert:
            self._store_alert(tenant_id, dma_id, alert)
        
        return alert
    
    def _check_pressure_conditions(
        self,
        tenant_id: str,
        sensor_id: str,
        dma_id: str,
        pressure: float,
        baseline: float,
        timestamp: datetime,
        lat: Optional[float],
        lng: Optional[float]
    ) -> Optional[PressureAlert]:
        """Check for various pressure instability conditions."""
        
        deviation = pressure - baseline
        deviation_pct = (deviation / baseline) * 100 if baseline > 0 else 0
        
        # Check 1: Low pressure alert
        if pressure < self.min_acceptable_pressure:
            return self._create_alert(
                tenant_id, sensor_id, dma_id, timestamp,
                PressureAlertType.LOW_PRESSURE,
                self._get_priority_for_low_pressure(pressure),
                pressure, baseline, deviation, deviation_pct,
                lat, lng,
                service_impact="major" if pressure < 1.0 else "moderate",
                recommendations=[
                    "Check for nearby leaks or bursts",
                    "Verify upstream supply status",
                    "Check PRV settings if applicable",
                    "Monitor downstream customer complaints"
                ]
            )
        
        # Check 2: High pressure alert
        if pressure > self.max_acceptable_pressure:
            return self._create_alert(
                tenant_id, sensor_id, dma_id, timestamp,
                PressureAlertType.HIGH_PRESSURE,
                self._get_priority_for_high_pressure(pressure),
                pressure, baseline, deviation, deviation_pct,
                lat, lng,
                service_impact="minor",
                recommendations=[
                    "Check PRV operation",
                    "Verify pump station output",
                    "Monitor for pipe stress indicators",
                    "Consider pressure reduction"
                ]
            )
        
        # Check 3: Sustained deviation
        if abs(deviation_pct) >= self.warning_deviation_pct:
            is_sustained, duration = self._check_sustained_deviation(
                sensor_id, self.warning_deviation_pct
            )
            
            if is_sustained:
                priority = AlertPriority.HIGH if abs(deviation_pct) >= self.critical_deviation_pct else AlertPriority.MEDIUM
                alert = self._create_alert(
                    tenant_id, sensor_id, dma_id, timestamp,
                    PressureAlertType.SUSTAINED_DEVIATION,
                    priority,
                    pressure, baseline, deviation, deviation_pct,
                    lat, lng
                )
                alert.duration_minutes = duration
                alert.is_sustained = True
                alert.recommended_actions = [
                    "Investigate network changes",
                    "Check for demand pattern anomalies",
                    "Verify sensor calibration"
                ]
                return alert
        
        # Check 4: Rapid pressure change
        rate_of_change = self._calculate_rate_of_change(sensor_id)
        if abs(rate_of_change) >= self.rapid_change_threshold:
            return self._create_alert(
                tenant_id, sensor_id, dma_id, timestamp,
                PressureAlertType.RAPID_CHANGE,
                AlertPriority.HIGH if abs(rate_of_change) > 0.5 else AlertPriority.MEDIUM,
                pressure, baseline, deviation, deviation_pct,
                lat, lng,
                rate_of_change=rate_of_change,
                recommendations=[
                    "Possible burst or major leak",
                    "Check valve operations",
                    "Verify pump station status",
                    "Immediate field inspection recommended"
                ]
            )
        
        # Check 5: Oscillation detection
        oscillation = self._detect_oscillation(sensor_id)
        if oscillation:
            amplitude, frequency = oscillation
            return self._create_alert(
                tenant_id, sensor_id, dma_id, timestamp,
                PressureAlertType.OSCILLATION,
                AlertPriority.MEDIUM if amplitude < 0.5 else AlertPriority.HIGH,
                pressure, baseline, deviation, deviation_pct,
                lat, lng,
                oscillation_amplitude=amplitude,
                oscillation_frequency=frequency,
                recommendations=[
                    "Check for waterhammer conditions",
                    "Verify pump cycling patterns",
                    "Inspect PRV stability",
                    "Check air in system"
                ]
            )
        
        return None
    
    def _create_alert(
        self,
        tenant_id: str,
        sensor_id: str,
        dma_id: str,
        timestamp: datetime,
        alert_type: PressureAlertType,
        priority: AlertPriority,
        pressure: float,
        baseline: float,
        deviation: float,
        deviation_pct: float,
        lat: Optional[float],
        lng: Optional[float],
        rate_of_change: float = 0,
        oscillation_amplitude: float = 0,
        oscillation_frequency: float = 0,
        service_impact: str = "none",
        recommendations: List[str] = None
    ) -> PressureAlert:
        """Create a pressure alert."""
        return PressureAlert(
            alert_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            sensor_id=sensor_id,
            alert_type=alert_type,
            priority=priority,
            detected_at=timestamp,
            current_pressure_bar=round(pressure, 3),
            baseline_pressure_bar=round(baseline, 3),
            deviation_bar=round(deviation, 3),
            deviation_percent=round(deviation_pct, 1),
            rate_of_change_bar_min=round(rate_of_change, 3),
            oscillation_amplitude_bar=round(oscillation_amplitude, 3),
            oscillation_frequency_hz=round(oscillation_frequency, 3),
            sensor_lat=lat,
            sensor_lng=lng,
            service_impact=service_impact,
            recommended_actions=recommendations or []
        )
    
    def _get_priority_for_low_pressure(self, pressure: float) -> AlertPriority:
        """Determine priority for low pressure."""
        if pressure < 0.5:
            return AlertPriority.CRITICAL
        elif pressure < 1.0:
            return AlertPriority.HIGH
        elif pressure < 1.5:
            return AlertPriority.MEDIUM
        return AlertPriority.LOW
    
    def _get_priority_for_high_pressure(self, pressure: float) -> AlertPriority:
        """Determine priority for high pressure."""
        if pressure > 8.0:
            return AlertPriority.CRITICAL
        elif pressure > 7.0:
            return AlertPriority.HIGH
        elif pressure > 6.0:
            return AlertPriority.MEDIUM
        return AlertPriority.LOW
    
    def _check_sustained_deviation(
        self,
        sensor_id: str,
        threshold_pct: float
    ) -> Tuple[bool, float]:
        """Check if deviation has been sustained."""
        history = self._history.get(sensor_id, [])
        baseline = self._baselines.get(sensor_id, 0)
        
        if not history or baseline == 0:
            return False, 0
        
        # Check last N minutes
        cutoff = datetime.utcnow() - timedelta(minutes=self.sustained_alert_minutes)
        recent = [(ts, p) for ts, p in history if ts > cutoff]
        
        if len(recent) < 3:
            return False, 0
        
        # Check if all readings exceed threshold
        exceeded_count = 0
        for ts, pressure in recent:
            deviation_pct = abs((pressure - baseline) / baseline) * 100
            if deviation_pct >= threshold_pct:
                exceeded_count += 1
        
        is_sustained = exceeded_count / len(recent) >= 0.8  # 80% of readings
        duration = (recent[-1][0] - recent[0][0]).total_seconds() / 60 if len(recent) > 1 else 0
        
        return is_sustained, duration
    
    def _calculate_rate_of_change(self, sensor_id: str) -> float:
        """Calculate pressure rate of change (bar/min)."""
        history = self._history.get(sensor_id, [])
        
        if len(history) < 3:
            return 0
        
        # Use last 5 readings
        recent = history[-5:]
        if len(recent) < 2:
            return 0
        
        time_span = (recent[-1][0] - recent[0][0]).total_seconds() / 60
        if time_span <= 0:
            return 0
        
        pressure_change = recent[-1][1] - recent[0][1]
        return pressure_change / time_span
    
    def _detect_oscillation(self, sensor_id: str) -> Optional[Tuple[float, float]]:
        """Detect pressure oscillation. Returns (amplitude, frequency) if detected."""
        history = self._history.get(sensor_id, [])
        
        if len(history) < 10:
            return None
        
        # Use last 20 readings
        recent = history[-20:]
        pressures = [p for _, p in recent]
        
        if len(pressures) < 10:
            return None
        
        # Calculate amplitude
        amplitude = max(pressures) - min(pressures)
        
        if amplitude < self.oscillation_min_amplitude:
            return None
        
        # Estimate frequency from zero crossings
        mean_p = statistics.mean(pressures)
        zero_crossings = 0
        for i in range(1, len(pressures)):
            if (pressures[i-1] - mean_p) * (pressures[i] - mean_p) < 0:
                zero_crossings += 1
        
        time_span = (recent[-1][0] - recent[0][0]).total_seconds()
        frequency = zero_crossings / (2 * time_span) if time_span > 0 else 0
        
        # Only report if frequency indicates real oscillation
        if frequency > 0.01:  # More than 1 cycle per 100 seconds
            return (amplitude, frequency)
        
        return None
    
    def _store_alert(self, tenant_id: str, dma_id: str, alert: PressureAlert):
        """Store alert in memory."""
        key = f"{tenant_id}:{dma_id}"
        if key not in self._alerts:
            self._alerts[key] = []
        self._alerts[key].append(alert)
        
        # Keep only last 100 alerts per DMA
        self._alerts[key] = self._alerts[key][-100:]
        
        logger.warning(f"Pressure alert: {alert.alert_type.value} at {alert.sensor_id} - {alert.priority.value}")
    
    def update_zone_status(
        self,
        tenant_id: str,
        dma_id: str,
        sensor_data: List[Dict]
    ) -> PressureZoneStatus:
        """
        Update pressure status for a zone.
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA identifier
            sensor_data: List of dicts with sensor_id, pressure_bar, is_online
        """
        if not sensor_data:
            return PressureZoneStatus(
                dma_id=dma_id,
                timestamp=datetime.utcnow(),
                avg_pressure_bar=0,
                min_pressure_bar=0,
                max_pressure_bar=0,
                pressure_variance=0,
                sensors_online=0,
                sensors_offline=0,
                sensors_alert=0,
                health_score=0,
                status="no_data"
            )
        
        online_sensors = [s for s in sensor_data if s.get('is_online', False)]
        pressures = [s['pressure_bar'] for s in online_sensors if 'pressure_bar' in s]
        
        sensors_online = len(online_sensors)
        sensors_offline = len(sensor_data) - sensors_online
        
        # Count sensors in alert state
        sensors_alert = 0
        key = f"{tenant_id}:{dma_id}"
        active_alerts = [a for a in self._alerts.get(key, []) if a.status == "active"]
        sensors_alert = len(set(a.sensor_id for a in active_alerts))
        
        if not pressures:
            avg_p = min_p = max_p = variance = 0
        else:
            avg_p = statistics.mean(pressures)
            min_p = min(pressures)
            max_p = max(pressures)
            variance = statistics.variance(pressures) if len(pressures) > 1 else 0
        
        # Calculate health score
        health = 100
        if sensors_offline > 0:
            health -= (sensors_offline / len(sensor_data)) * 30
        if sensors_alert > 0:
            health -= sensors_alert * 10
        if avg_p < self.min_acceptable_pressure:
            health -= 20
        if avg_p > self.max_acceptable_pressure:
            health -= 15
        if variance > 0.5:
            health -= 10
        
        health = max(0, min(100, health))
        
        # Determine status
        status = "healthy"
        if health < 50:
            status = "critical"
        elif health < 75:
            status = "warning"
        
        zone_status = PressureZoneStatus(
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            avg_pressure_bar=round(avg_p, 2),
            min_pressure_bar=round(min_p, 2),
            max_pressure_bar=round(max_p, 2),
            pressure_variance=round(variance, 3),
            sensors_online=sensors_online,
            sensors_offline=sensors_offline,
            sensors_alert=sensors_alert,
            health_score=round(health, 1),
            status=status
        )
        
        self._zone_status[dma_id] = zone_status
        return zone_status
    
    def get_active_alerts(
        self,
        tenant_id: str,
        dma_id: Optional[str] = None,
        priority: Optional[AlertPriority] = None
    ) -> List[PressureAlert]:
        """Get active pressure alerts."""
        results = []
        
        for key, alerts in self._alerts.items():
            if not key.startswith(tenant_id):
                continue
            if dma_id and not key.endswith(dma_id):
                continue
            
            for alert in alerts:
                if alert.status != "active":
                    continue
                if priority and alert.priority != priority:
                    continue
                results.append(alert)
        
        return sorted(results, key=lambda x: (
            -{"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[x.priority.value],
            x.detected_at
        ), reverse=True)
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge a pressure alert."""
        for alerts in self._alerts.values():
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.status = "acknowledged"
                    alert.notes = f"Acknowledged by {user} at {datetime.utcnow().isoformat()}"
                    return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = "") -> bool:
        """Resolve a pressure alert."""
        for alerts in self._alerts.values():
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.status = "resolved"
                    alert.notes = resolution_notes
                    return True
        return False
    
    def get_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get pressure monitoring summary for dashboard."""
        active_alerts = self.get_active_alerts(tenant_id)
        
        critical = len([a for a in active_alerts if a.priority == AlertPriority.CRITICAL])
        high = len([a for a in active_alerts if a.priority == AlertPriority.HIGH])
        medium = len([a for a in active_alerts if a.priority == AlertPriority.MEDIUM])
        
        # Alert type breakdown
        type_counts = {}
        for alert in active_alerts:
            t = alert.alert_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Get zone statuses
        zones = []
        for dma_id, status in self._zone_status.items():
            zones.append({
                "dma_id": dma_id,
                "status": status.status,
                "health_score": status.health_score,
                "avg_pressure": status.avg_pressure_bar
            })
        
        return {
            "has_data": len(self._history) > 0,
            "sensors_monitored": len(self._history),
            "total_active_alerts": len(active_alerts),
            "critical_alerts": critical,
            "high_alerts": high,
            "medium_alerts": medium,
            "alert_types": type_counts,
            "zones": zones,
            "status": "critical" if critical > 0 else "warning" if high > 0 else "healthy",
            "last_updated": datetime.utcnow().isoformat()
        }
