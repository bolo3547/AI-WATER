"""
AquaWatch AI Package
====================
AI-powered anomaly detection and leak localization.
"""

from .anomaly_detector import (
    AnomalyDetectionEngine,
    AnomalyType,
    AnomalyResult,
    PressureBaseline,
    StatisticalDetector,
    IsolationForestDetector,
    LeakProbabilityModel
)

from .leak_localizer import (
    LeakLocalizer,
    LeakLocation,
    NetworkTopology,
    PipeSegment,
    PressureWaveAnalyzer
)

__all__ = [
    # Anomaly Detection
    'AnomalyDetectionEngine',
    'AnomalyType',
    'AnomalyResult',
    'PressureBaseline',
    'StatisticalDetector',
    'IsolationForestDetector',
    'LeakProbabilityModel',
    
    # Leak Localization
    'LeakLocalizer',
    'LeakLocation',
    'NetworkTopology',
    'PipeSegment',
    'PressureWaveAnalyzer'
]

__version__ = '1.0.0'
