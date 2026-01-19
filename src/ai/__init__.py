"""
AquaWatch AI Package
====================
AI-powered anomaly detection and leak localization.

Component Exports:
- 3️⃣ Decision Engine (LOCKED FORMULA)
- 4️⃣ Baseline Comparison (STL + Prophet)
- 5️⃣ Continuous Learning Pipeline
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

# Component 3: Decision Engine (LOCKED FORMULA)
from .decision_engine import (
    DecisionEngine,
    DecisionEngineConfig,
    DMAPriorityScore,
    score_dma
)

# Component 4: Baseline Comparison (STL + Prophet)
from .baseline_comparison import (
    BaselineComparisonService,
    BaselineComparisonConfig,
    BaselineResult,
    AIResult,
    ComparisonResult,
    DriftMetrics,
    AnomalySource,
    ComparisonVerdict,
    DriftSeverity,
    create_baseline_api
)

# Component 5: Continuous Learning Pipeline
from .continuous_learning import (
    ContinuousLearningController,
    ContinuousLearningConfig,
    FieldFeedback,
    FeedbackType,
    ModelStatus,
    PerformanceMetric,
    ModelPerformanceSnapshot,
    RetrainingTrigger,
    LabelStore,
    PerformanceTracker,
    create_continuous_learning_api
)

# Time Series Forecasting
from .time_series_forecasting import (
    STLAnomalyDetector,
    ProphetForecaster,
    LSTMForecaster,
    EnsembleForecaster,
    STL_AVAILABLE,
    PROPHET_AVAILABLE,
    TF_AVAILABLE
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
    'PressureWaveAnalyzer',
    
    # Decision Engine (Component 3)
    'DecisionEngine',
    'DecisionEngineConfig',
    'DMAPriorityScore',
    'score_dma',
    
    # Baseline Comparison (Component 4)
    'BaselineComparisonService',
    'BaselineComparisonConfig',
    'BaselineResult',
    'AIResult',
    'ComparisonResult',
    'DriftMetrics',
    'AnomalySource',
    'ComparisonVerdict',
    'DriftSeverity',
    'create_baseline_api',
    
    # Continuous Learning (Component 5)
    'ContinuousLearningController',
    'ContinuousLearningConfig',
    'FieldFeedback',
    'FeedbackType',
    'ModelStatus',
    'PerformanceMetric',
    'ModelPerformanceSnapshot',
    'RetrainingTrigger',
    'LabelStore',
    'PerformanceTracker',
    'create_continuous_learning_api',
    
    # Time Series
    'STLAnomalyDetector',
    'ProphetForecaster',
    'LSTMForecaster',
    'EnsembleForecaster',
    'STL_AVAILABLE',
    'PROPHET_AVAILABLE',
    'TF_AVAILABLE'
]

__version__ = '2.0.0'
