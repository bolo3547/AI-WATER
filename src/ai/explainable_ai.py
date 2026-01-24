"""
AQUAWATCH NRW - EXPLAINABLE AI INSIGHTS
========================================

Step 8: Explainable AI for Leak Detection

This module provides:
1. AI Reason structure for leak explainability
2. Evidence aggregation for detection signals
3. Confidence breakdown calculation

LOCKED DECISION FORMULA:
    Priority Score = (leak_probability × estimated_loss_m3_day) × criticality_factor × confidence_factor

AI Reason Components:
- pressure_drop: Sustained pressure decrease below baseline
- flow_rise: Unexpected flow increase without demand correlation
- multi_sensor_agreement: Multiple sensors corroborating detection
- night_flow_deviation: Anomalous minimum night flow
- confidence: Overall detection confidence with breakdown

Author: AquaWatch AI Team
Version: 3.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class DetectionSignal(str, Enum):
    """Types of detection signals that contribute to leak detection."""
    PRESSURE_DROP = "pressure_drop"
    FLOW_RISE = "flow_rise"
    MULTI_SENSOR_AGREEMENT = "multi_sensor_agreement"
    NIGHT_FLOW_DEVIATION = "night_flow_deviation"
    ACOUSTIC_ANOMALY = "acoustic_anomaly"
    TEMPERATURE_CHANGE = "temperature_change"
    PRESSURE_TRANSIENT = "pressure_transient"
    CORRELATION_BREAK = "correlation_break"
    HISTORICAL_PATTERN = "historical_pattern"
    CUSTOMER_REPORT = "customer_report"


@dataclass
class SignalEvidence:
    """Evidence for a single detection signal."""
    signal_type: str
    contribution: float  # 0-1, how much this signal contributed
    value: float  # The measured value
    threshold: float  # The threshold that was exceeded
    deviation: float  # How much the value deviated from normal
    description: str  # Human-readable explanation
    timestamp: str
    sensor_id: Optional[str] = None
    raw_data: Optional[Dict] = None


@dataclass
class ConfidenceBreakdown:
    """Breakdown of confidence scores by method."""
    statistical_confidence: float  # Z-score / IQR methods
    ml_confidence: float  # Isolation Forest / GB
    temporal_confidence: float  # Time-series patterns
    spatial_confidence: float  # Multi-sensor agreement
    acoustic_confidence: float  # Acoustic sensor data
    overall_confidence: float  # Weighted combination
    
    # Method weights (how much each contributed)
    weights: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.weights:
            self.weights = {
                "statistical": 0.20,
                "ml": 0.25,
                "temporal": 0.20,
                "spatial": 0.25,
                "acoustic": 0.10
            }


@dataclass
class EvidenceTimelinePoint:
    """A point in the evidence timeline."""
    timestamp: str
    signal_type: str
    value: float
    anomaly_score: float
    description: str
    is_key_event: bool = False


@dataclass
class AIReason:
    """
    Explainable AI reason for leak detection.
    
    This is the main structure stored in the ai_reason JSONB field.
    """
    # Primary detection signals
    pressure_drop: Optional[SignalEvidence] = None
    flow_rise: Optional[SignalEvidence] = None
    multi_sensor_agreement: Optional[SignalEvidence] = None
    night_flow_deviation: Optional[SignalEvidence] = None
    acoustic_anomaly: Optional[SignalEvidence] = None
    
    # Confidence breakdown
    confidence: Optional[ConfidenceBreakdown] = None
    
    # Top contributing signals (sorted by contribution)
    top_signals: List[str] = field(default_factory=list)
    
    # Evidence timeline
    evidence_timeline: List[EvidenceTimelinePoint] = field(default_factory=list)
    
    # Detection summary
    detection_method: str = "multi_signal"  # primary method that triggered
    detection_timestamp: str = ""
    analysis_duration_seconds: float = 0.0
    
    # Human-readable explanation
    explanation: str = ""
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Model metadata
    model_version: str = "3.0.0"
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        # Handle signal evidences
        for signal_name in ['pressure_drop', 'flow_rise', 'multi_sensor_agreement', 
                           'night_flow_deviation', 'acoustic_anomaly']:
            signal = getattr(self, signal_name)
            if signal:
                result[signal_name] = asdict(signal)
        
        # Handle confidence
        if self.confidence:
            result['confidence'] = asdict(self.confidence)
        
        # Simple fields
        result['top_signals'] = self.top_signals
        result['evidence_timeline'] = [asdict(e) for e in self.evidence_timeline]
        result['detection_method'] = self.detection_method
        result['detection_timestamp'] = self.detection_timestamp
        result['analysis_duration_seconds'] = self.analysis_duration_seconds
        result['explanation'] = self.explanation
        result['recommendations'] = self.recommendations
        result['model_version'] = self.model_version
        result['feature_importance'] = self.feature_importance
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIReason':
        """Create from dictionary."""
        reason = cls()
        
        # Parse signal evidences
        for signal_name in ['pressure_drop', 'flow_rise', 'multi_sensor_agreement',
                           'night_flow_deviation', 'acoustic_anomaly']:
            if signal_name in data and data[signal_name]:
                setattr(reason, signal_name, SignalEvidence(**data[signal_name]))
        
        # Parse confidence
        if 'confidence' in data and data['confidence']:
            reason.confidence = ConfidenceBreakdown(**data['confidence'])
        
        # Parse timeline
        if 'evidence_timeline' in data:
            reason.evidence_timeline = [
                EvidenceTimelinePoint(**e) for e in data['evidence_timeline']
            ]
        
        # Simple fields
        reason.top_signals = data.get('top_signals', [])
        reason.detection_method = data.get('detection_method', 'unknown')
        reason.detection_timestamp = data.get('detection_timestamp', '')
        reason.analysis_duration_seconds = data.get('analysis_duration_seconds', 0)
        reason.explanation = data.get('explanation', '')
        reason.recommendations = data.get('recommendations', [])
        reason.model_version = data.get('model_version', '3.0.0')
        reason.feature_importance = data.get('feature_importance', {})
        
        return reason


# =============================================================================
# EXPLAINABLE AI ENGINE
# =============================================================================

class ExplainableLeakDetector:
    """
    Leak detection engine with explainable AI capabilities.
    
    Produces human-readable explanations for each detection.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.pressure_drop_threshold = self.config.get('pressure_drop_threshold', 0.3)  # bar
        self.flow_rise_threshold = self.config.get('flow_rise_threshold', 15)  # %
        self.night_flow_baseline = self.config.get('night_flow_baseline', 10)  # L/min
        self.acoustic_threshold = self.config.get('acoustic_threshold', 60)  # dB
        self.multi_sensor_min = self.config.get('multi_sensor_min', 2)
        
        # Confidence weights
        self.signal_weights = {
            DetectionSignal.PRESSURE_DROP: 0.25,
            DetectionSignal.FLOW_RISE: 0.20,
            DetectionSignal.MULTI_SENSOR_AGREEMENT: 0.25,
            DetectionSignal.NIGHT_FLOW_DEVIATION: 0.15,
            DetectionSignal.ACOUSTIC_ANOMALY: 0.15,
        }
    
    def analyze_leak(
        self,
        pressure_data: List[Dict],
        flow_data: List[Dict],
        acoustic_data: Optional[List[Dict]] = None,
        night_flow_data: Optional[List[Dict]] = None,
        correlated_sensors: Optional[List[str]] = None,
        baseline_pressure: float = 3.0,
        baseline_flow: float = 100.0,
        dma_id: Optional[str] = None
    ) -> AIReason:
        """
        Analyze sensor data and produce explainable leak detection.
        
        Args:
            pressure_data: List of {timestamp, value, sensor_id}
            flow_data: List of {timestamp, value, sensor_id}
            acoustic_data: Optional acoustic readings
            night_flow_data: Minimum night flow data
            correlated_sensors: List of sensor IDs showing correlation
            baseline_pressure: Expected baseline pressure
            baseline_flow: Expected baseline flow
            dma_id: District Metered Area identifier
            
        Returns:
            AIReason with full explainability data
        """
        start_time = datetime.utcnow()
        reason = AIReason()
        reason.detection_timestamp = start_time.isoformat()
        
        signals_detected: List[Tuple[str, float]] = []  # (signal_name, contribution)
        timeline_events: List[EvidenceTimelinePoint] = []
        
        # === 1. Analyze Pressure Drop ===
        pressure_evidence = self._analyze_pressure_drop(
            pressure_data, baseline_pressure
        )
        if pressure_evidence:
            reason.pressure_drop = pressure_evidence
            signals_detected.append(('pressure_drop', pressure_evidence.contribution))
            timeline_events.append(EvidenceTimelinePoint(
                timestamp=pressure_evidence.timestamp,
                signal_type='pressure_drop',
                value=pressure_evidence.value,
                anomaly_score=pressure_evidence.contribution,
                description=pressure_evidence.description,
                is_key_event=pressure_evidence.contribution > 0.7
            ))
        
        # === 2. Analyze Flow Rise ===
        flow_evidence = self._analyze_flow_rise(
            flow_data, baseline_flow
        )
        if flow_evidence:
            reason.flow_rise = flow_evidence
            signals_detected.append(('flow_rise', flow_evidence.contribution))
            timeline_events.append(EvidenceTimelinePoint(
                timestamp=flow_evidence.timestamp,
                signal_type='flow_rise',
                value=flow_evidence.value,
                anomaly_score=flow_evidence.contribution,
                description=flow_evidence.description,
                is_key_event=flow_evidence.contribution > 0.7
            ))
        
        # === 3. Multi-Sensor Agreement ===
        if correlated_sensors and len(correlated_sensors) >= self.multi_sensor_min:
            multi_evidence = self._analyze_multi_sensor(
                correlated_sensors, pressure_data, flow_data
            )
            if multi_evidence:
                reason.multi_sensor_agreement = multi_evidence
                signals_detected.append(('multi_sensor_agreement', multi_evidence.contribution))
                timeline_events.append(EvidenceTimelinePoint(
                    timestamp=multi_evidence.timestamp,
                    signal_type='multi_sensor_agreement',
                    value=len(correlated_sensors),
                    anomaly_score=multi_evidence.contribution,
                    description=multi_evidence.description,
                    is_key_event=True
                ))
        
        # === 4. Night Flow Deviation ===
        if night_flow_data:
            night_evidence = self._analyze_night_flow(
                night_flow_data, self.night_flow_baseline
            )
            if night_evidence:
                reason.night_flow_deviation = night_evidence
                signals_detected.append(('night_flow_deviation', night_evidence.contribution))
                timeline_events.append(EvidenceTimelinePoint(
                    timestamp=night_evidence.timestamp,
                    signal_type='night_flow_deviation',
                    value=night_evidence.value,
                    anomaly_score=night_evidence.contribution,
                    description=night_evidence.description,
                    is_key_event=night_evidence.contribution > 0.6
                ))
        
        # === 5. Acoustic Anomaly ===
        if acoustic_data:
            acoustic_evidence = self._analyze_acoustic(acoustic_data)
            if acoustic_evidence:
                reason.acoustic_anomaly = acoustic_evidence
                signals_detected.append(('acoustic_anomaly', acoustic_evidence.contribution))
                timeline_events.append(EvidenceTimelinePoint(
                    timestamp=acoustic_evidence.timestamp,
                    signal_type='acoustic_anomaly',
                    value=acoustic_evidence.value,
                    anomaly_score=acoustic_evidence.contribution,
                    description=acoustic_evidence.description,
                    is_key_event=acoustic_evidence.contribution > 0.8
                ))
        
        # === Calculate Confidence Breakdown ===
        reason.confidence = self._calculate_confidence(signals_detected)
        
        # === Sort signals by contribution ===
        signals_detected.sort(key=lambda x: x[1], reverse=True)
        reason.top_signals = [s[0] for s in signals_detected]
        
        # === Build timeline ===
        timeline_events.sort(key=lambda x: x.timestamp)
        reason.evidence_timeline = timeline_events
        
        # === Determine detection method ===
        if signals_detected:
            reason.detection_method = signals_detected[0][0]
        
        # === Generate explanation ===
        reason.explanation = self._generate_explanation(reason)
        
        # === Generate recommendations ===
        reason.recommendations = self._generate_recommendations(reason)
        
        # === Calculate feature importance ===
        reason.feature_importance = {
            s[0]: s[1] for s in signals_detected
        }
        
        # === Record timing ===
        reason.analysis_duration_seconds = (
            datetime.utcnow() - start_time
        ).total_seconds()
        
        return reason
    
    def _analyze_pressure_drop(
        self, 
        data: List[Dict], 
        baseline: float
    ) -> Optional[SignalEvidence]:
        """Analyze pressure data for sustained drops."""
        if not data or len(data) < 3:
            return None
        
        # Get recent values
        recent_values = [d['value'] for d in data[-10:]]
        avg_pressure = sum(recent_values) / len(recent_values)
        min_pressure = min(recent_values)
        
        # Calculate deviation
        deviation = baseline - avg_pressure
        
        if deviation < self.pressure_drop_threshold:
            return None
        
        # Calculate contribution (0-1)
        contribution = min(deviation / (baseline * 0.3), 1.0)
        
        return SignalEvidence(
            signal_type=DetectionSignal.PRESSURE_DROP.value,
            contribution=round(contribution, 3),
            value=round(avg_pressure, 2),
            threshold=round(baseline - self.pressure_drop_threshold, 2),
            deviation=round(-deviation, 2),
            description=f"Sustained pressure drop of {deviation:.2f} bar detected. "
                       f"Current: {avg_pressure:.2f} bar, Expected: {baseline:.2f} bar",
            timestamp=data[-1].get('timestamp', datetime.utcnow().isoformat()),
            sensor_id=data[-1].get('sensor_id'),
            raw_data={'values': recent_values[-5:], 'baseline': baseline}
        )
    
    def _analyze_flow_rise(
        self, 
        data: List[Dict], 
        baseline: float
    ) -> Optional[SignalEvidence]:
        """Analyze flow data for unexpected increases."""
        if not data or len(data) < 3:
            return None
        
        recent_values = [d['value'] for d in data[-10:]]
        avg_flow = sum(recent_values) / len(recent_values)
        
        # Calculate percentage increase
        pct_increase = ((avg_flow - baseline) / baseline) * 100 if baseline > 0 else 0
        
        if pct_increase < self.flow_rise_threshold:
            return None
        
        contribution = min(pct_increase / 50, 1.0)  # 50% increase = full contribution
        
        return SignalEvidence(
            signal_type=DetectionSignal.FLOW_RISE.value,
            contribution=round(contribution, 3),
            value=round(avg_flow, 2),
            threshold=round(baseline * (1 + self.flow_rise_threshold/100), 2),
            deviation=round(avg_flow - baseline, 2),
            description=f"Flow increased by {pct_increase:.1f}% above baseline. "
                       f"Current: {avg_flow:.1f} L/min, Expected: {baseline:.1f} L/min",
            timestamp=data[-1].get('timestamp', datetime.utcnow().isoformat()),
            sensor_id=data[-1].get('sensor_id'),
            raw_data={'values': recent_values[-5:], 'baseline': baseline}
        )
    
    def _analyze_multi_sensor(
        self, 
        sensors: List[str],
        pressure_data: List[Dict],
        flow_data: List[Dict]
    ) -> Optional[SignalEvidence]:
        """Analyze multi-sensor correlation."""
        n_sensors = len(sensors)
        
        if n_sensors < self.multi_sensor_min:
            return None
        
        # More sensors agreeing = higher contribution
        contribution = min((n_sensors - 1) / 4, 1.0)  # 5 sensors = full contribution
        
        return SignalEvidence(
            signal_type=DetectionSignal.MULTI_SENSOR_AGREEMENT.value,
            contribution=round(contribution, 3),
            value=n_sensors,
            threshold=self.multi_sensor_min,
            deviation=n_sensors - self.multi_sensor_min,
            description=f"{n_sensors} sensors showing correlated anomalies, "
                       f"strongly indicating leak presence in the area.",
            timestamp=datetime.utcnow().isoformat(),
            sensor_id=None,
            raw_data={'sensors': sensors}
        )
    
    def _analyze_night_flow(
        self, 
        data: List[Dict], 
        baseline: float
    ) -> Optional[SignalEvidence]:
        """Analyze minimum night flow deviation."""
        if not data:
            return None
        
        # Get minimum night flow
        night_values = [d['value'] for d in data]
        min_night_flow = min(night_values)
        avg_night_flow = sum(night_values) / len(night_values)
        
        # Deviation from expected
        deviation = avg_night_flow - baseline
        
        if deviation < baseline * 0.2:  # Less than 20% increase
            return None
        
        contribution = min(deviation / (baseline * 2), 1.0)
        
        return SignalEvidence(
            signal_type=DetectionSignal.NIGHT_FLOW_DEVIATION.value,
            contribution=round(contribution, 3),
            value=round(avg_night_flow, 2),
            threshold=round(baseline * 1.2, 2),
            deviation=round(deviation, 2),
            description=f"Minimum night flow elevated at {avg_night_flow:.1f} L/min "
                       f"(expected: {baseline:.1f} L/min). Suggests background leakage.",
            timestamp=data[-1].get('timestamp', datetime.utcnow().isoformat()),
            sensor_id=data[-1].get('sensor_id'),
            raw_data={'values': night_values[-5:], 'baseline': baseline}
        )
    
    def _analyze_acoustic(
        self, 
        data: List[Dict]
    ) -> Optional[SignalEvidence]:
        """Analyze acoustic sensor data for leak signatures."""
        if not data:
            return None
        
        recent_values = [d['value'] for d in data[-5:]]
        max_acoustic = max(recent_values)
        avg_acoustic = sum(recent_values) / len(recent_values)
        
        if max_acoustic < self.acoustic_threshold:
            return None
        
        contribution = min((max_acoustic - self.acoustic_threshold) / 40, 1.0)
        
        return SignalEvidence(
            signal_type=DetectionSignal.ACOUSTIC_ANOMALY.value,
            contribution=round(contribution, 3),
            value=round(max_acoustic, 1),
            threshold=self.acoustic_threshold,
            deviation=round(max_acoustic - self.acoustic_threshold, 1),
            description=f"Acoustic signature detected at {max_acoustic:.0f} dB "
                       f"(threshold: {self.acoustic_threshold} dB). "
                       f"Sound pattern consistent with water leak.",
            timestamp=data[-1].get('timestamp', datetime.utcnow().isoformat()),
            sensor_id=data[-1].get('sensor_id'),
            raw_data={'values': recent_values}
        )
    
    def _calculate_confidence(
        self, 
        signals: List[Tuple[str, float]]
    ) -> ConfidenceBreakdown:
        """Calculate confidence breakdown from detected signals."""
        # Initialize scores
        statistical = 0.0
        ml = 0.0
        temporal = 0.0
        spatial = 0.0
        acoustic = 0.0
        
        for signal_name, contribution in signals:
            if signal_name == 'pressure_drop':
                statistical = max(statistical, contribution * 0.8)
                ml = max(ml, contribution * 0.6)
            elif signal_name == 'flow_rise':
                statistical = max(statistical, contribution * 0.7)
                ml = max(ml, contribution * 0.7)
            elif signal_name == 'multi_sensor_agreement':
                spatial = max(spatial, contribution)
                ml = max(ml, contribution * 0.8)
            elif signal_name == 'night_flow_deviation':
                temporal = max(temporal, contribution)
            elif signal_name == 'acoustic_anomaly':
                acoustic = max(acoustic, contribution)
        
        # Calculate weighted overall confidence
        weights = {
            "statistical": 0.20,
            "ml": 0.25,
            "temporal": 0.20,
            "spatial": 0.25,
            "acoustic": 0.10
        }
        
        overall = (
            statistical * weights["statistical"] +
            ml * weights["ml"] +
            temporal * weights["temporal"] +
            spatial * weights["spatial"] +
            acoustic * weights["acoustic"]
        )
        
        # Boost if multiple signals agree
        n_signals = len([s for s in signals if s[1] > 0.3])
        if n_signals >= 3:
            overall = min(overall * 1.2, 0.98)
        elif n_signals >= 2:
            overall = min(overall * 1.1, 0.95)
        
        return ConfidenceBreakdown(
            statistical_confidence=round(statistical, 3),
            ml_confidence=round(ml, 3),
            temporal_confidence=round(temporal, 3),
            spatial_confidence=round(spatial, 3),
            acoustic_confidence=round(acoustic, 3),
            overall_confidence=round(overall, 3),
            weights=weights
        )
    
    def _generate_explanation(self, reason: AIReason) -> str:
        """Generate human-readable explanation."""
        parts = []
        
        if reason.confidence and reason.confidence.overall_confidence > 0.7:
            parts.append(f"High confidence leak detection ({reason.confidence.overall_confidence:.0%}).")
        elif reason.confidence and reason.confidence.overall_confidence > 0.4:
            parts.append(f"Moderate confidence leak indication ({reason.confidence.overall_confidence:.0%}).")
        else:
            parts.append("Low confidence anomaly detected.")
        
        # Add top signal explanations
        if reason.pressure_drop and reason.pressure_drop.contribution > 0.5:
            parts.append(f"Primary indicator: {reason.pressure_drop.description}")
        
        if reason.flow_rise and reason.flow_rise.contribution > 0.5:
            parts.append(f"Supporting evidence: {reason.flow_rise.description}")
        
        if reason.multi_sensor_agreement and reason.multi_sensor_agreement.contribution > 0.5:
            parts.append(f"Spatial confirmation: {reason.multi_sensor_agreement.description}")
        
        if reason.acoustic_anomaly and reason.acoustic_anomaly.contribution > 0.5:
            parts.append(f"Acoustic confirmation: {reason.acoustic_anomaly.description}")
        
        return " ".join(parts)
    
    def _generate_recommendations(self, reason: AIReason) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        confidence = reason.confidence.overall_confidence if reason.confidence else 0
        
        if confidence > 0.8:
            recs.append("URGENT: Dispatch field team immediately for visual inspection.")
            recs.append("Isolate affected area if possible to minimize water loss.")
        elif confidence > 0.6:
            recs.append("Schedule field inspection within 24 hours.")
            recs.append("Monitor pressure trends closely for next 6 hours.")
        else:
            recs.append("Continue monitoring - possible leak developing.")
            recs.append("Review sensor calibration if anomalies persist.")
        
        if reason.acoustic_anomaly and reason.acoustic_anomaly.contribution > 0.7:
            recs.append("Deploy acoustic localization equipment for precise positioning.")
        
        if reason.night_flow_deviation and reason.night_flow_deviation.contribution > 0.6:
            recs.append("Conduct step-testing during low demand period to isolate leak section.")
        
        if reason.multi_sensor_agreement:
            recs.append("Use sensor triangulation data to narrow search area.")
        
        return recs


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_ai_reason_from_detection(
    anomaly_result: Dict,
    sensor_data: Dict,
    correlated_sensors: Optional[List[str]] = None
) -> AIReason:
    """
    Create an AIReason from anomaly detection output.
    
    This function bridges the existing anomaly detector with the 
    explainability module.
    """
    detector = ExplainableLeakDetector()
    
    # Convert anomaly result to our format
    pressure_data = sensor_data.get('pressure_history', [])
    flow_data = sensor_data.get('flow_history', [])
    acoustic_data = sensor_data.get('acoustic_history', [])
    night_flow_data = sensor_data.get('night_flow', [])
    
    # Get baselines from anomaly result
    details = anomaly_result.get('details', {})
    baseline_pressure = details.get('baseline_mean', 3.0)
    baseline_flow = details.get('flow_baseline', 100.0)
    
    return detector.analyze_leak(
        pressure_data=pressure_data,
        flow_data=flow_data,
        acoustic_data=acoustic_data,
        night_flow_data=night_flow_data,
        correlated_sensors=correlated_sensors,
        baseline_pressure=baseline_pressure,
        baseline_flow=baseline_flow
    )


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test the explainable detector
    detector = ExplainableLeakDetector()
    
    # Sample data
    now = datetime.utcnow()
    pressure_data = [
        {'timestamp': (now - timedelta(minutes=i)).isoformat(), 'value': 3.0 - (i * 0.02), 'sensor_id': 'P001'}
        for i in range(20, 0, -1)
    ]
    
    flow_data = [
        {'timestamp': (now - timedelta(minutes=i)).isoformat(), 'value': 100 + (i * 2), 'sensor_id': 'F001'}
        for i in range(20, 0, -1)
    ]
    
    acoustic_data = [
        {'timestamp': (now - timedelta(minutes=i)).isoformat(), 'value': 55 + (i * 1.5), 'sensor_id': 'A001'}
        for i in range(10, 0, -1)
    ]
    
    result = detector.analyze_leak(
        pressure_data=pressure_data,
        flow_data=flow_data,
        acoustic_data=acoustic_data,
        correlated_sensors=['P001', 'P002', 'F001'],
        baseline_pressure=3.0,
        baseline_flow=100.0
    )
    
    print("\n" + "=" * 60)
    print("EXPLAINABLE AI - LEAK DETECTION RESULT")
    print("=" * 60)
    
    if result.confidence:
        print(f"\nOverall Confidence: {result.confidence.overall_confidence:.1%}")
    print(f"Detection Method: {result.detection_method}")
    print(f"\nTop Signals: {result.top_signals}")
    print(f"\nExplanation:\n{result.explanation}")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")
    
    if result.confidence:
        print(f"\nConfidence Breakdown:")
        print(f"  Statistical: {result.confidence.statistical_confidence:.1%}")
        print(f"  ML Model: {result.confidence.ml_confidence:.1%}")
        print(f"  Temporal: {result.confidence.temporal_confidence:.1%}")
        print(f"  Spatial: {result.confidence.spatial_confidence:.1%}")
        print(f"  Acoustic: {result.confidence.acoustic_confidence:.1%}")
    
    print(f"\nJSON Output (ai_reason field):")
    import json
    print(json.dumps(result.to_dict(), indent=2, default=str)[:1000] + "...")
