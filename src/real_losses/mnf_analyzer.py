"""
AquaWatch NRW - Minimum Night Flow (MNF) Analyzer
=================================================

MNF Analysis for Real Loss Detection following IWA best practices.

MNF Window: 02:00 - 04:00 (configurable)
MNF Components:
  - Legitimate Night Use (LNU) - estimated
  - Background Leakage - unavoidable minor leaks
  - Burst/Excess Leakage - detected anomalies

When MNF exceeds baseline for multiple consecutive nights → Real Loss Alert
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class MNFAlertSeverity(Enum):
    """MNF alert severity levels"""
    INFO = "info"           # Slight elevation, monitoring
    WARNING = "warning"     # Persistent elevation, needs attention
    HIGH = "high"           # Significant elevation, likely leak
    CRITICAL = "critical"   # Severe elevation, burst suspected


@dataclass
class MNFReading:
    """Single MNF reading for a DMA"""
    reading_id: str
    tenant_id: str
    dma_id: str
    timestamp: datetime
    
    # Flow readings (m³/hour)
    flow_m3_hour: float
    
    # Time window
    window_start: datetime
    window_end: datetime
    
    # Data quality
    reading_count: int      # Number of 15-min intervals
    completeness_pct: float # % of expected readings received
    
    # Calculated
    is_valid: bool = True
    notes: str = ""


@dataclass
class MNFBaseline:
    """MNF baseline for a DMA"""
    baseline_id: str
    tenant_id: str
    dma_id: str
    
    # Computed baseline values
    baseline_mnf_m3_hour: float
    baseline_std_dev: float
    
    # Components breakdown
    estimated_lnu_m3_hour: float      # Legitimate Night Use
    background_leakage_m3_hour: float # Unavoidable background leakage
    
    # Statistics
    sample_count: int
    computed_at: datetime
    valid_from: datetime
    valid_until: Optional[datetime] = None
    
    # Thresholds
    warning_threshold_m3_hour: float = 0.0
    high_threshold_m3_hour: float = 0.0
    critical_threshold_m3_hour: float = 0.0


@dataclass
class MNFAnomaly:
    """Detected MNF anomaly"""
    anomaly_id: str
    tenant_id: str
    dma_id: str
    
    # Detection
    detected_at: datetime
    severity: MNFAlertSeverity
    
    # MNF values
    current_mnf_m3_hour: float
    baseline_mnf_m3_hour: float
    deviation_m3_hour: float
    deviation_percent: float
    
    # Persistence
    consecutive_nights: int
    is_persistent: bool    # 3+ consecutive nights
    
    # Estimated impact
    estimated_daily_loss_m3: float
    estimated_monthly_loss_m3: float
    estimated_cost_zmw: float
    
    # Status
    status: str = "active"  # active, acknowledged, resolved
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # AI signals
    leak_type_hint: str = ""  # main_leak, service_leak, storage_leak
    confidence: float = 0.0


@dataclass
class MNFTrendPoint:
    """Historical MNF trend data point"""
    date: datetime
    dma_id: str
    mnf_m3_hour: float
    baseline_m3_hour: float
    deviation_pct: float
    has_anomaly: bool
    anomaly_severity: Optional[str] = None


class MNFAnalyzer:
    """
    Production MNF analyzer for real loss detection.
    
    Usage:
        analyzer = MNFAnalyzer(config)
        
        # Ingest MNF reading
        reading = analyzer.record_mnf(tenant_id, dma_id, flow_data)
        
        # Check for anomalies
        anomaly = analyzer.analyze_mnf(tenant_id, dma_id)
        
        # Get trend history
        trends = analyzer.get_mnf_trends(tenant_id, dma_id, days=30)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize MNF analyzer with configuration."""
        self.config = config or {}
        
        # MNF time window (24-hour format)
        self.mnf_start_hour = self.config.get('mnf_start_hour', 2)   # 02:00
        self.mnf_end_hour = self.config.get('mnf_end_hour', 4)       # 04:00
        
        # Alert thresholds
        self.warning_deviation_pct = self.config.get('warning_deviation_pct', 15)
        self.high_deviation_pct = self.config.get('high_deviation_pct', 30)
        self.critical_deviation_pct = self.config.get('critical_deviation_pct', 50)
        
        # Persistence threshold (consecutive nights)
        self.persistence_threshold = self.config.get('persistence_threshold', 3)
        
        # LNU estimation factor (% of total connections assumed active at night)
        self.lnu_factor = self.config.get('lnu_factor', 0.06)  # 6%
        
        # In-memory storage (replace with database in production)
        self._readings: Dict[str, List[MNFReading]] = {}  # key: tenant_id:dma_id
        self._baselines: Dict[str, MNFBaseline] = {}      # key: tenant_id:dma_id
        self._anomalies: Dict[str, List[MNFAnomaly]] = {} # key: tenant_id:dma_id
        
        logger.info(f"MNFAnalyzer initialized - Window: {self.mnf_start_hour:02d}:00-{self.mnf_end_hour:02d}:00")
    
    def _get_key(self, tenant_id: str, dma_id: str) -> str:
        """Get storage key for tenant+DMA combination."""
        return f"{tenant_id}:{dma_id}"
    
    def record_mnf(
        self,
        tenant_id: str,
        dma_id: str,
        flow_readings: List[Tuple[datetime, float]],
        timezone_offset_hours: int = 2  # Default: Africa/Lusaka (CAT)
    ) -> Optional[MNFReading]:
        """
        Record MNF reading from flow sensor data.
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA identifier
            flow_readings: List of (timestamp, flow_m3_hour) tuples
            timezone_offset_hours: Local timezone offset from UTC
            
        Returns:
            MNFReading if valid data in MNF window, None otherwise
        """
        if not flow_readings:
            return None
        
        # Filter readings to MNF window
        mnf_readings = []
        for ts, flow in flow_readings:
            local_hour = (ts.hour + timezone_offset_hours) % 24
            if self.mnf_start_hour <= local_hour < self.mnf_end_hour:
                mnf_readings.append((ts, flow))
        
        if not mnf_readings:
            return None
        
        # Calculate average MNF
        flows = [f for _, f in mnf_readings]
        avg_flow = statistics.mean(flows) if flows else 0
        
        # Determine window times
        window_start = min(ts for ts, _ in mnf_readings)
        window_end = max(ts for ts, _ in mnf_readings)
        
        # Calculate completeness (expecting readings every 15 mins = 8 readings for 2-hour window)
        expected_readings = (self.mnf_end_hour - self.mnf_start_hour) * 4
        completeness_pct = min(100, (len(mnf_readings) / expected_readings) * 100)
        
        reading = MNFReading(
            reading_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            flow_m3_hour=round(avg_flow, 3),
            window_start=window_start,
            window_end=window_end,
            reading_count=len(mnf_readings),
            completeness_pct=round(completeness_pct, 1),
            is_valid=completeness_pct >= 75  # Need at least 75% completeness
        )
        
        # Store reading
        key = self._get_key(tenant_id, dma_id)
        if key not in self._readings:
            self._readings[key] = []
        self._readings[key].append(reading)
        
        # Keep only last 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        self._readings[key] = [r for r in self._readings[key] if r.timestamp > cutoff]
        
        logger.info(f"Recorded MNF for {dma_id}: {avg_flow:.2f} m³/hr ({completeness_pct:.0f}% complete)")
        return reading
    
    def compute_baseline(
        self,
        tenant_id: str,
        dma_id: str,
        connection_count: int = 1000,
        avg_demand_per_connection_m3_day: float = 0.5
    ) -> Optional[MNFBaseline]:
        """
        Compute MNF baseline for a DMA.
        
        Uses last 30 days of valid readings (excluding anomalies).
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA identifier
            connection_count: Number of service connections in DMA
            avg_demand_per_connection_m3_day: Average daily demand per connection
            
        Returns:
            MNFBaseline object
        """
        key = self._get_key(tenant_id, dma_id)
        readings = self._readings.get(key, [])
        
        # Get last 30 days of valid readings
        cutoff = datetime.utcnow() - timedelta(days=30)
        valid_readings = [r for r in readings if r.timestamp > cutoff and r.is_valid]
        
        if len(valid_readings) < 7:
            logger.warning(f"Insufficient data for baseline: {len(valid_readings)} readings (need 7+)")
            return None
        
        # Calculate statistics
        flows = [r.flow_m3_hour for r in valid_readings]
        
        # Remove outliers (> 2 std dev) for baseline calculation
        mean_flow = statistics.mean(flows)
        std_dev = statistics.stdev(flows) if len(flows) > 1 else 0
        
        filtered_flows = [f for f in flows if abs(f - mean_flow) <= 2 * std_dev]
        
        if not filtered_flows:
            filtered_flows = flows
        
        baseline_mnf = statistics.mean(filtered_flows)
        baseline_std = statistics.stdev(filtered_flows) if len(filtered_flows) > 1 else 0
        
        # Estimate LNU (Legitimate Night Use)
        # Typically 6% of connections active at night, using 30% of normal hourly demand
        night_demand_factor = 0.3
        hourly_demand_per_conn = avg_demand_per_connection_m3_day / 24
        estimated_lnu = connection_count * self.lnu_factor * hourly_demand_per_conn * night_demand_factor
        
        # Background leakage = baseline - LNU (capped at 0)
        background_leakage = max(0, baseline_mnf - estimated_lnu)
        
        # Calculate thresholds
        warning_threshold = baseline_mnf * (1 + self.warning_deviation_pct / 100)
        high_threshold = baseline_mnf * (1 + self.high_deviation_pct / 100)
        critical_threshold = baseline_mnf * (1 + self.critical_deviation_pct / 100)
        
        baseline = MNFBaseline(
            baseline_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            baseline_mnf_m3_hour=round(baseline_mnf, 3),
            baseline_std_dev=round(baseline_std, 3),
            estimated_lnu_m3_hour=round(estimated_lnu, 3),
            background_leakage_m3_hour=round(background_leakage, 3),
            sample_count=len(filtered_flows),
            computed_at=datetime.utcnow(),
            valid_from=datetime.utcnow(),
            warning_threshold_m3_hour=round(warning_threshold, 3),
            high_threshold_m3_hour=round(high_threshold, 3),
            critical_threshold_m3_hour=round(critical_threshold, 3)
        )
        
        # Store baseline
        self._baselines[key] = baseline
        
        logger.info(f"Computed MNF baseline for {dma_id}: {baseline_mnf:.2f} m³/hr (σ={baseline_std:.2f})")
        return baseline
    
    def analyze_mnf(
        self,
        tenant_id: str,
        dma_id: str,
        tariff_zmw_per_m3: float = 25.0
    ) -> Optional[MNFAnomaly]:
        """
        Analyze latest MNF reading for anomalies.
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA identifier
            tariff_zmw_per_m3: Water tariff for cost estimation
            
        Returns:
            MNFAnomaly if anomaly detected, None otherwise
        """
        key = self._get_key(tenant_id, dma_id)
        
        # Get baseline
        baseline = self._baselines.get(key)
        if not baseline:
            logger.warning(f"No baseline for {dma_id} - run compute_baseline first")
            return None
        
        # Get latest reading
        readings = self._readings.get(key, [])
        if not readings:
            return None
        
        latest = readings[-1]
        if not latest.is_valid:
            return None
        
        # Calculate deviation
        deviation_m3 = latest.flow_m3_hour - baseline.baseline_mnf_m3_hour
        deviation_pct = (deviation_m3 / baseline.baseline_mnf_m3_hour) * 100 if baseline.baseline_mnf_m3_hour > 0 else 0
        
        # Determine severity
        severity = None
        if latest.flow_m3_hour >= baseline.critical_threshold_m3_hour:
            severity = MNFAlertSeverity.CRITICAL
        elif latest.flow_m3_hour >= baseline.high_threshold_m3_hour:
            severity = MNFAlertSeverity.HIGH
        elif latest.flow_m3_hour >= baseline.warning_threshold_m3_hour:
            severity = MNFAlertSeverity.WARNING
        
        if severity is None:
            return None  # No anomaly
        
        # Check persistence (consecutive nights above warning)
        consecutive = 0
        for reading in reversed(readings[-self.persistence_threshold * 2:]):
            if reading.flow_m3_hour >= baseline.warning_threshold_m3_hour:
                consecutive += 1
            else:
                break
        
        is_persistent = consecutive >= self.persistence_threshold
        
        # Estimate losses
        excess_flow = max(0, deviation_m3)
        mnf_hours = self.mnf_end_hour - self.mnf_start_hour
        daily_loss_from_mnf = excess_flow * mnf_hours
        
        # Extrapolate to full day (leaks persist 24h, but are masked during day)
        # Conservative estimate: use MNF excess as hourly rate
        estimated_daily_loss = excess_flow * 24
        estimated_monthly_loss = estimated_daily_loss * 30
        estimated_cost = estimated_daily_loss * tariff_zmw_per_m3
        
        # Hint at leak type based on patterns
        leak_type = self._classify_leak_type(deviation_pct, is_persistent, severity)
        
        anomaly = MNFAnomaly(
            anomaly_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            detected_at=datetime.utcnow(),
            severity=severity,
            current_mnf_m3_hour=round(latest.flow_m3_hour, 3),
            baseline_mnf_m3_hour=round(baseline.baseline_mnf_m3_hour, 3),
            deviation_m3_hour=round(deviation_m3, 3),
            deviation_percent=round(deviation_pct, 1),
            consecutive_nights=consecutive,
            is_persistent=is_persistent,
            estimated_daily_loss_m3=round(estimated_daily_loss, 1),
            estimated_monthly_loss_m3=round(estimated_monthly_loss, 1),
            estimated_cost_zmw=round(estimated_cost, 2),
            leak_type_hint=leak_type,
            confidence=self._calculate_confidence(deviation_pct, is_persistent, latest.completeness_pct)
        )
        
        # Store anomaly
        if key not in self._anomalies:
            self._anomalies[key] = []
        self._anomalies[key].append(anomaly)
        
        logger.warning(f"MNF anomaly detected for {dma_id}: {severity.value} - {deviation_pct:.1f}% above baseline")
        return anomaly
    
    def _classify_leak_type(
        self,
        deviation_pct: float,
        is_persistent: bool,
        severity: MNFAlertSeverity
    ) -> str:
        """Classify leak type based on MNF patterns."""
        if severity == MNFAlertSeverity.CRITICAL and deviation_pct > 80:
            return "main_leak"  # Large sudden increase suggests burst
        elif is_persistent and deviation_pct < 40:
            return "service_leak"  # Persistent mild increase suggests service leaks
        elif is_persistent:
            return "main_leak"  # Persistent high increase suggests developing main leak
        else:
            return "unknown"
    
    def _calculate_confidence(
        self,
        deviation_pct: float,
        is_persistent: bool,
        completeness_pct: float
    ) -> float:
        """Calculate confidence score for anomaly detection."""
        base_confidence = 0.5
        
        # Higher deviation = higher confidence
        if deviation_pct > 50:
            base_confidence += 0.2
        elif deviation_pct > 30:
            base_confidence += 0.1
        
        # Persistence increases confidence
        if is_persistent:
            base_confidence += 0.2
        
        # Data quality affects confidence
        quality_factor = completeness_pct / 100
        
        return round(min(0.95, base_confidence * quality_factor), 2)
    
    def get_mnf_trends(
        self,
        tenant_id: str,
        dma_id: str,
        days: int = 30
    ) -> List[MNFTrendPoint]:
        """
        Get MNF trend history for visualization.
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA identifier
            days: Number of days of history
            
        Returns:
            List of MNFTrendPoint for charting
        """
        key = self._get_key(tenant_id, dma_id)
        readings = self._readings.get(key, [])
        baseline = self._baselines.get(key)
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered_readings = [r for r in readings if r.timestamp > cutoff and r.is_valid]
        
        trends = []
        baseline_mnf = baseline.baseline_mnf_m3_hour if baseline else 0
        
        for reading in filtered_readings:
            deviation_pct = 0
            if baseline_mnf > 0:
                deviation_pct = ((reading.flow_m3_hour - baseline_mnf) / baseline_mnf) * 100
            
            has_anomaly = False
            severity = None
            
            if baseline:
                if reading.flow_m3_hour >= baseline.critical_threshold_m3_hour:
                    has_anomaly = True
                    severity = "critical"
                elif reading.flow_m3_hour >= baseline.high_threshold_m3_hour:
                    has_anomaly = True
                    severity = "high"
                elif reading.flow_m3_hour >= baseline.warning_threshold_m3_hour:
                    has_anomaly = True
                    severity = "warning"
            
            trends.append(MNFTrendPoint(
                date=reading.timestamp,
                dma_id=dma_id,
                mnf_m3_hour=reading.flow_m3_hour,
                baseline_m3_hour=baseline_mnf,
                deviation_pct=round(deviation_pct, 1),
                has_anomaly=has_anomaly,
                anomaly_severity=severity
            ))
        
        return trends
    
    def get_active_anomalies(
        self,
        tenant_id: str,
        dma_id: Optional[str] = None
    ) -> List[MNFAnomaly]:
        """Get all active MNF anomalies for a tenant."""
        results = []
        
        for key, anomalies in self._anomalies.items():
            if not key.startswith(tenant_id):
                continue
            if dma_id and not key.endswith(dma_id):
                continue
            
            active = [a for a in anomalies if a.status == "active"]
            results.extend(active)
        
        return sorted(results, key=lambda x: x.detected_at, reverse=True)
    
    def acknowledge_anomaly(
        self,
        tenant_id: str,
        anomaly_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge an MNF anomaly."""
        for anomalies in self._anomalies.values():
            for anomaly in anomalies:
                if anomaly.anomaly_id == anomaly_id and anomaly.tenant_id == tenant_id:
                    anomaly.status = "acknowledged"
                    anomaly.acknowledged_by = acknowledged_by
                    anomaly.acknowledged_at = datetime.utcnow()
                    return True
        return False
    
    def resolve_anomaly(
        self,
        tenant_id: str,
        anomaly_id: str
    ) -> bool:
        """Mark an MNF anomaly as resolved."""
        for anomalies in self._anomalies.values():
            for anomaly in anomalies:
                if anomaly.anomaly_id == anomaly_id and anomaly.tenant_id == tenant_id:
                    anomaly.status = "resolved"
                    anomaly.resolved_at = datetime.utcnow()
                    return True
        return False
    
    def get_summary(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get MNF analysis summary for tenant dashboard.
        
        Returns summary with real data or appropriate empty states.
        """
        readings_count = 0
        dmas_with_baseline = 0
        active_anomalies = 0
        persistent_anomalies = 0
        total_estimated_loss = 0
        
        for key, readings in self._readings.items():
            if key.startswith(tenant_id):
                readings_count += len(readings)
        
        for key, baseline in self._baselines.items():
            if key.startswith(tenant_id):
                dmas_with_baseline += 1
        
        for key, anomalies in self._anomalies.items():
            if key.startswith(tenant_id):
                for a in anomalies:
                    if a.status == "active":
                        active_anomalies += 1
                        total_estimated_loss += a.estimated_daily_loss_m3
                        if a.is_persistent:
                            persistent_anomalies += 1
        
        return {
            "has_data": readings_count > 0,
            "total_readings": readings_count,
            "dmas_with_baseline": dmas_with_baseline,
            "active_anomalies": active_anomalies,
            "persistent_anomalies": persistent_anomalies,
            "total_estimated_loss_m3_day": round(total_estimated_loss, 1),
            "data_status": "ready" if readings_count > 0 else "waiting_for_sensors",
            "last_updated": datetime.utcnow().isoformat()
        }
