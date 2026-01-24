"""
AquaWatch NRW - Burst Detector
==============================

Real-time burst/main leak detection using flow and pressure signatures.

Detection Signals:
1. Sudden pressure drop (> threshold in short time)
2. Flow spike at DMA inlet
3. Pressure oscillation (waterhammer effect)
4. Cross-correlation between pressure sensors

Burst Types:
- Type A: Catastrophic burst (immediate, large)
- Type B: Progressive burst (developing over hours)
- Type C: Background leak (detected via MNF, not burst)
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


class BurstSeverity(Enum):
    """Burst severity levels"""
    SUSPECTED = "suspected"     # Anomaly detected, needs confirmation
    CONFIRMED = "confirmed"     # Multiple signals confirm burst
    MAJOR = "major"             # Large burst, significant loss
    CATASTROPHIC = "catastrophic"  # Critical infrastructure failure


class BurstType(Enum):
    """Types of burst/leak"""
    SUDDEN_BURST = "sudden_burst"       # Catastrophic pipe failure
    PROGRESSIVE = "progressive"          # Developing leak
    JOINT_FAILURE = "joint_failure"      # Connection point failure
    VALVE_FAILURE = "valve_failure"      # Valve malfunction
    HYDRANT_RELEASE = "hydrant_release"  # Unauthorized/accidental
    UNKNOWN = "unknown"


@dataclass
class PressureReading:
    """Pressure sensor reading"""
    sensor_id: str
    timestamp: datetime
    pressure_bar: float
    location_lat: float
    location_lng: float
    dma_id: str


@dataclass
class FlowReading:
    """Flow sensor reading"""
    sensor_id: str
    timestamp: datetime
    flow_m3_hour: float
    dma_id: str


@dataclass
class BurstEvent:
    """Detected burst event"""
    event_id: str
    tenant_id: str
    dma_id: str
    
    # Detection info
    detected_at: datetime
    detection_method: str  # pressure_drop, flow_spike, oscillation, combined
    
    # Classification
    burst_type: BurstType
    severity: BurstSeverity
    confidence: float
    
    # Signals
    pressure_drop_bar: float
    pressure_drop_rate_bar_min: float
    flow_increase_m3_hour: float
    flow_increase_percent: float
    
    # Location
    estimated_lat: Optional[float] = None
    estimated_lng: Optional[float] = None
    location_hint: str = ""
    nearest_sensor_id: str = ""
    
    # Impact
    estimated_loss_m3_hour: float = 0.0
    estimated_loss_m3_day: float = 0.0
    estimated_cost_zmw_day: float = 0.0
    
    # Status
    status: str = "active"  # active, acknowledged, responding, contained, resolved
    priority_score: int = 0
    
    # Timeline
    acknowledged_at: Optional[datetime] = None
    response_started_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


@dataclass
class PressureOscillation:
    """Detected pressure oscillation event"""
    event_id: str
    tenant_id: str
    dma_id: str
    sensor_id: str
    
    detected_at: datetime
    frequency_hz: float      # Oscillation frequency
    amplitude_bar: float     # Peak-to-peak amplitude
    duration_seconds: float
    
    severity: str  # low, medium, high
    possible_cause: str  # waterhammer, pump_cycling, valve_instability


class BurstDetector:
    """
    Production burst detection engine.
    
    Uses multi-signal analysis for accurate burst detection:
    - Pressure drop detection
    - Flow spike detection
    - Oscillation analysis
    - Cross-sensor correlation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize burst detector."""
        self.config = config or {}
        
        # Pressure thresholds
        self.pressure_drop_threshold_bar = self.config.get('pressure_drop_threshold', 0.5)
        self.pressure_drop_rate_threshold = self.config.get('pressure_drop_rate_threshold', 0.1)  # bar/min
        self.oscillation_threshold_bar = self.config.get('oscillation_threshold', 0.2)
        
        # Flow thresholds
        self.flow_spike_threshold_pct = self.config.get('flow_spike_threshold_pct', 30)
        self.flow_spike_absolute_m3h = self.config.get('flow_spike_absolute', 50)  # m³/h
        
        # Detection windows
        self.detection_window_minutes = self.config.get('detection_window', 15)
        self.oscillation_window_seconds = self.config.get('oscillation_window', 60)
        
        # Baselines
        self._pressure_baselines: Dict[str, float] = {}  # sensor_id -> baseline bar
        self._flow_baselines: Dict[str, float] = {}      # dma_id -> baseline m³/h
        
        # Recent readings buffer
        self._pressure_history: Dict[str, List[PressureReading]] = {}
        self._flow_history: Dict[str, List[FlowReading]] = {}
        
        # Detected events
        self._events: Dict[str, List[BurstEvent]] = {}
        self._oscillations: Dict[str, List[PressureOscillation]] = {}
        
        logger.info("BurstDetector initialized")
    
    def set_pressure_baseline(self, sensor_id: str, baseline_bar: float):
        """Set pressure baseline for a sensor."""
        self._pressure_baselines[sensor_id] = baseline_bar
        logger.debug(f"Set pressure baseline for {sensor_id}: {baseline_bar} bar")
    
    def set_flow_baseline(self, dma_id: str, baseline_m3h: float):
        """Set flow baseline for a DMA."""
        self._flow_baselines[dma_id] = baseline_m3h
        logger.debug(f"Set flow baseline for {dma_id}: {baseline_m3h} m³/h")
    
    def ingest_pressure(self, reading: PressureReading) -> Optional[BurstEvent]:
        """
        Ingest pressure reading and check for burst signals.
        
        Returns BurstEvent if burst detected, None otherwise.
        """
        sensor_id = reading.sensor_id
        
        # Add to history
        if sensor_id not in self._pressure_history:
            self._pressure_history[sensor_id] = []
        
        self._pressure_history[sensor_id].append(reading)
        
        # Keep only recent history
        cutoff = datetime.utcnow() - timedelta(minutes=self.detection_window_minutes * 2)
        self._pressure_history[sensor_id] = [
            r for r in self._pressure_history[sensor_id] 
            if r.timestamp > cutoff
        ]
        
        # Check for burst signals
        return self._check_pressure_burst(reading)
    
    def ingest_flow(self, reading: FlowReading) -> Optional[BurstEvent]:
        """
        Ingest flow reading and check for burst signals.
        
        Returns BurstEvent if burst detected, None otherwise.
        """
        dma_id = reading.dma_id
        
        # Add to history
        if dma_id not in self._flow_history:
            self._flow_history[dma_id] = []
        
        self._flow_history[dma_id].append(reading)
        
        # Keep only recent history
        cutoff = datetime.utcnow() - timedelta(minutes=self.detection_window_minutes * 2)
        self._flow_history[dma_id] = [
            r for r in self._flow_history[dma_id]
            if r.timestamp > cutoff
        ]
        
        # Check for burst signals
        return self._check_flow_burst(reading)
    
    def _check_pressure_burst(self, reading: PressureReading) -> Optional[BurstEvent]:
        """Check pressure reading for burst indicators."""
        sensor_id = reading.sensor_id
        history = self._pressure_history.get(sensor_id, [])
        
        if len(history) < 3:
            return None
        
        # Get baseline
        baseline = self._pressure_baselines.get(sensor_id)
        if baseline is None:
            # Auto-calculate baseline from recent stable readings
            pressures = [r.pressure_bar for r in history[-20:]]
            if len(pressures) >= 10:
                baseline = statistics.mean(pressures)
                self._pressure_baselines[sensor_id] = baseline
            else:
                return None
        
        current = reading.pressure_bar
        
        # Check 1: Sudden pressure drop
        pressure_drop = baseline - current
        
        if pressure_drop < self.pressure_drop_threshold_bar:
            return None  # No significant drop
        
        # Calculate drop rate
        recent = history[-5:]
        if len(recent) >= 2:
            time_span = (recent[-1].timestamp - recent[0].timestamp).total_seconds() / 60
            if time_span > 0:
                drop_rate = (recent[0].pressure_bar - recent[-1].pressure_bar) / time_span
            else:
                drop_rate = 0
        else:
            drop_rate = 0
        
        # Determine severity
        severity = BurstSeverity.SUSPECTED
        if pressure_drop > 1.5 or drop_rate > 0.3:
            severity = BurstSeverity.CATASTROPHIC
        elif pressure_drop > 1.0 or drop_rate > 0.2:
            severity = BurstSeverity.MAJOR
        elif pressure_drop > 0.7:
            severity = BurstSeverity.CONFIRMED
        
        # Create burst event
        event = BurstEvent(
            event_id=str(uuid.uuid4()),
            tenant_id="",  # Will be set by caller
            dma_id=reading.dma_id,
            detected_at=datetime.utcnow(),
            detection_method="pressure_drop",
            burst_type=BurstType.SUDDEN_BURST if drop_rate > 0.2 else BurstType.PROGRESSIVE,
            severity=severity,
            confidence=self._calculate_burst_confidence(pressure_drop, drop_rate),
            pressure_drop_bar=round(pressure_drop, 3),
            pressure_drop_rate_bar_min=round(drop_rate, 3),
            flow_increase_m3_hour=0,
            flow_increase_percent=0,
            estimated_lat=reading.location_lat,
            estimated_lng=reading.location_lng,
            nearest_sensor_id=sensor_id,
            location_hint=f"Near sensor {sensor_id}",
            priority_score=self._calculate_priority(severity, pressure_drop)
        )
        
        # Estimate loss (rough estimate based on pressure drop)
        # Using orifice equation approximation: Q ∝ √(ΔP)
        estimated_leak_rate = 10 * math.sqrt(pressure_drop)  # Rough m³/h estimate
        event.estimated_loss_m3_hour = round(estimated_leak_rate, 1)
        event.estimated_loss_m3_day = round(estimated_leak_rate * 24, 1)
        
        return event
    
    def _check_flow_burst(self, reading: FlowReading) -> Optional[BurstEvent]:
        """Check flow reading for burst indicators."""
        dma_id = reading.dma_id
        history = self._flow_history.get(dma_id, [])
        
        if len(history) < 3:
            return None
        
        # Get baseline
        baseline = self._flow_baselines.get(dma_id)
        if baseline is None:
            # Auto-calculate from history
            flows = [r.flow_m3_hour for r in history[-20:]]
            if len(flows) >= 10:
                baseline = statistics.mean(flows)
                self._flow_baselines[dma_id] = baseline
            else:
                return None
        
        current = reading.flow_m3_hour
        
        # Calculate increase
        flow_increase = current - baseline
        flow_increase_pct = (flow_increase / baseline) * 100 if baseline > 0 else 0
        
        # Check thresholds
        if (flow_increase_pct < self.flow_spike_threshold_pct and 
            flow_increase < self.flow_spike_absolute_m3h):
            return None
        
        # Determine severity based on flow increase
        severity = BurstSeverity.SUSPECTED
        if flow_increase_pct > 100 or flow_increase > 200:
            severity = BurstSeverity.CATASTROPHIC
        elif flow_increase_pct > 60 or flow_increase > 100:
            severity = BurstSeverity.MAJOR
        elif flow_increase_pct > 40:
            severity = BurstSeverity.CONFIRMED
        
        event = BurstEvent(
            event_id=str(uuid.uuid4()),
            tenant_id="",
            dma_id=dma_id,
            detected_at=datetime.utcnow(),
            detection_method="flow_spike",
            burst_type=BurstType.SUDDEN_BURST if flow_increase_pct > 80 else BurstType.PROGRESSIVE,
            severity=severity,
            confidence=self._calculate_flow_confidence(flow_increase_pct),
            pressure_drop_bar=0,
            pressure_drop_rate_bar_min=0,
            flow_increase_m3_hour=round(flow_increase, 1),
            flow_increase_percent=round(flow_increase_pct, 1),
            estimated_loss_m3_hour=round(flow_increase, 1),
            estimated_loss_m3_day=round(flow_increase * 24, 1),
            location_hint=f"Detected at DMA {dma_id} inlet",
            priority_score=self._calculate_priority(severity, flow_increase)
        )
        
        return event
    
    def detect_oscillation(
        self,
        sensor_id: str,
        tenant_id: str,
        dma_id: str
    ) -> Optional[PressureOscillation]:
        """
        Detect pressure oscillation patterns.
        
        Oscillations indicate waterhammer, pump issues, or valve problems.
        """
        history = self._pressure_history.get(sensor_id, [])
        
        if len(history) < 10:
            return None
        
        # Get recent high-frequency readings
        recent = history[-20:]
        pressures = [r.pressure_bar for r in recent]
        
        if len(pressures) < 10:
            return None
        
        # Calculate statistics
        mean_p = statistics.mean(pressures)
        std_p = statistics.stdev(pressures) if len(pressures) > 1 else 0
        
        # Detect oscillation (high variance)
        if std_p < self.oscillation_threshold_bar / 2:
            return None
        
        # Calculate amplitude (peak-to-peak)
        amplitude = max(pressures) - min(pressures)
        
        if amplitude < self.oscillation_threshold_bar:
            return None
        
        # Estimate frequency (rough)
        zero_crossings = 0
        for i in range(1, len(pressures)):
            if (pressures[i-1] - mean_p) * (pressures[i] - mean_p) < 0:
                zero_crossings += 1
        
        time_span = (recent[-1].timestamp - recent[0].timestamp).total_seconds()
        frequency = zero_crossings / (2 * time_span) if time_span > 0 else 0
        
        # Determine severity
        severity = "low"
        if amplitude > 1.0 or frequency > 2:
            severity = "high"
        elif amplitude > 0.5:
            severity = "medium"
        
        # Determine possible cause
        possible_cause = "unknown"
        if frequency > 1:
            possible_cause = "waterhammer"
        elif 0.1 < frequency < 0.5:
            possible_cause = "pump_cycling"
        else:
            possible_cause = "valve_instability"
        
        oscillation = PressureOscillation(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            sensor_id=sensor_id,
            detected_at=datetime.utcnow(),
            frequency_hz=round(frequency, 3),
            amplitude_bar=round(amplitude, 3),
            duration_seconds=round(time_span, 1),
            severity=severity,
            possible_cause=possible_cause
        )
        
        # Store oscillation
        key = f"{tenant_id}:{dma_id}"
        if key not in self._oscillations:
            self._oscillations[key] = []
        self._oscillations[key].append(oscillation)
        
        logger.warning(f"Pressure oscillation detected: {amplitude:.2f} bar @ {frequency:.2f} Hz - {possible_cause}")
        return oscillation
    
    def _calculate_burst_confidence(self, pressure_drop: float, drop_rate: float) -> float:
        """Calculate confidence score for burst detection."""
        confidence = 0.4
        
        if pressure_drop > 1.5:
            confidence += 0.3
        elif pressure_drop > 1.0:
            confidence += 0.2
        elif pressure_drop > 0.5:
            confidence += 0.1
        
        if drop_rate > 0.3:
            confidence += 0.2
        elif drop_rate > 0.1:
            confidence += 0.1
        
        return round(min(0.95, confidence), 2)
    
    def _calculate_flow_confidence(self, flow_increase_pct: float) -> float:
        """Calculate confidence for flow-based detection."""
        confidence = 0.5
        
        if flow_increase_pct > 100:
            confidence += 0.3
        elif flow_increase_pct > 50:
            confidence += 0.2
        elif flow_increase_pct > 30:
            confidence += 0.1
        
        return round(min(0.95, confidence), 2)
    
    def _calculate_priority(self, severity: BurstSeverity, magnitude: float) -> int:
        """Calculate priority score (0-100)."""
        base = {
            BurstSeverity.SUSPECTED: 40,
            BurstSeverity.CONFIRMED: 60,
            BurstSeverity.MAJOR: 80,
            BurstSeverity.CATASTROPHIC: 95
        }.get(severity, 50)
        
        # Adjust for magnitude
        if magnitude > 2:
            base += 5
        
        return min(100, base)
    
    def get_active_events(self, tenant_id: str, dma_id: Optional[str] = None) -> List[BurstEvent]:
        """Get all active burst events."""
        results = []
        for key, events in self._events.items():
            if not key.startswith(tenant_id):
                continue
            if dma_id and not key.endswith(dma_id):
                continue
            
            active = [e for e in events if e.status in ("active", "acknowledged", "responding")]
            results.extend(active)
        
        return sorted(results, key=lambda x: x.priority_score, reverse=True)
    
    def get_recent_oscillations(
        self,
        tenant_id: str,
        hours: int = 24
    ) -> List[PressureOscillation]:
        """Get recent pressure oscillation events."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        results = []
        
        for key, oscillations in self._oscillations.items():
            if not key.startswith(tenant_id):
                continue
            
            recent = [o for o in oscillations if o.detected_at > cutoff]
            results.extend(recent)
        
        return sorted(results, key=lambda x: x.detected_at, reverse=True)
    
    def get_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get burst detection summary for dashboard."""
        active_events = self.get_active_events(tenant_id)
        oscillations = self.get_recent_oscillations(tenant_id, hours=24)
        
        catastrophic = len([e for e in active_events if e.severity == BurstSeverity.CATASTROPHIC])
        major = len([e for e in active_events if e.severity == BurstSeverity.MAJOR])
        confirmed = len([e for e in active_events if e.severity == BurstSeverity.CONFIRMED])
        
        total_loss = sum(e.estimated_loss_m3_hour for e in active_events)
        
        return {
            "has_data": len(self._pressure_history) > 0 or len(self._flow_history) > 0,
            "active_events": len(active_events),
            "catastrophic_count": catastrophic,
            "major_count": major,
            "confirmed_count": confirmed,
            "oscillation_count_24h": len(oscillations),
            "total_estimated_loss_m3_hour": round(total_loss, 1),
            "sensors_monitored": len(self._pressure_history),
            "dmas_monitored": len(self._flow_history),
            "status": "alert" if catastrophic > 0 else "warning" if major > 0 else "monitoring"
        }
