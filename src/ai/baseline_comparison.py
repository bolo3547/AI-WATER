"""
AQUAWATCH NRW - BASELINE COMPARISON SERVICE
============================================

Component 4️⃣: STL + Prophet Baseline

This module provides comparison between statistical baselines (STL decomposition)
and AI-based anomaly detection, tracking drift and storing deltas for continuous
improvement and explainability.

Key Features:
- STL statistical baseline vs AI anomaly comparison
- Prophet forecast vs LSTM prediction delta tracking
- Baseline drift detection over time
- Anomaly classification reconciliation
- API exposure for dashboard integration

The comparison enables:
1. Explainability: Show operators why AI flagged something vs statistical baseline
2. Drift Detection: Alert when AI predictions diverge from statistical norms
3. Model Validation: Compare real-time AI accuracy against proven statistical methods
4. Audit Trail: Store all deltas for NRW audit compliance

Author: AquaWatch AI Team
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import statistics

import numpy as np
import pandas as pd

# Import existing forecasting components
from .time_series_forecasting import (
    STLAnomalyDetector,
    ProphetForecaster,
    LSTMForecaster,
    EnsembleForecaster,
    STL_AVAILABLE,
    PROPHET_AVAILABLE,
    TF_AVAILABLE,
    STLAnomalyResult
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class AnomalySource(Enum):
    """Source of anomaly detection."""
    STL_BASELINE = "stl_baseline"
    PROPHET_FORECAST = "prophet_forecast"
    LSTM_AI = "lstm_ai"
    ENSEMBLE = "ensemble"
    RULE_BASED = "rule_based"


class ComparisonVerdict(Enum):
    """Result of comparing baseline vs AI."""
    BOTH_AGREE_NORMAL = "both_agree_normal"       # Both say normal
    BOTH_AGREE_ANOMALY = "both_agree_anomaly"     # Both detect anomaly
    AI_ONLY_ANOMALY = "ai_only_anomaly"           # AI detects, baseline doesn't
    BASELINE_ONLY_ANOMALY = "baseline_only_anomaly"  # Baseline detects, AI doesn't
    CONFLICTING = "conflicting"                   # Different severity assessments


class DriftSeverity(Enum):
    """Severity of model drift."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BaselineResult:
    """Result from statistical baseline analysis."""
    timestamp: datetime
    dma_id: str
    metric_type: str  # 'pressure', 'flow', 'noise_level'
    actual_value: float
    
    # STL decomposition components
    stl_trend: float
    stl_seasonal: float
    stl_residual: float
    stl_expected: float  # trend + seasonal
    stl_deviation: float  # actual - expected
    stl_zscore: float
    stl_is_anomaly: bool
    stl_anomaly_threshold: float = 3.0


@dataclass
class AIResult:
    """Result from AI-based analysis."""
    timestamp: datetime
    dma_id: str
    metric_type: str
    actual_value: float
    
    # AI predictions
    ai_predicted: float
    ai_lower_bound: float
    ai_upper_bound: float
    ai_confidence: float
    ai_deviation: float  # actual - predicted
    ai_deviation_percent: float
    ai_is_anomaly: bool
    ai_model: str  # 'lstm', 'prophet', 'ensemble'


@dataclass
class ComparisonResult:
    """Result of comparing baseline vs AI detection."""
    timestamp: datetime
    dma_id: str
    metric_type: str
    actual_value: float
    
    # Baseline assessment
    baseline: BaselineResult
    
    # AI assessment
    ai: AIResult
    
    # Comparison metrics
    verdict: ComparisonVerdict
    prediction_delta: float  # AI predicted - STL expected
    prediction_delta_percent: float
    agreement_score: float  # 0-1, how much baseline and AI agree
    
    # Explainability
    explanation: str
    
    # Metadata
    comparison_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage."""
        return {
            'comparison_id': self.comparison_id,
            'timestamp': self.timestamp.isoformat(),
            'dma_id': self.dma_id,
            'metric_type': self.metric_type,
            'actual_value': self.actual_value,
            'baseline': {
                'stl_expected': self.baseline.stl_expected,
                'stl_deviation': self.baseline.stl_deviation,
                'stl_zscore': self.baseline.stl_zscore,
                'stl_is_anomaly': self.baseline.stl_is_anomaly
            },
            'ai': {
                'predicted': self.ai.ai_predicted,
                'lower_bound': self.ai.ai_lower_bound,
                'upper_bound': self.ai.ai_upper_bound,
                'confidence': self.ai.ai_confidence,
                'is_anomaly': self.ai.ai_is_anomaly,
                'model': self.ai.ai_model
            },
            'verdict': self.verdict.value,
            'prediction_delta': self.prediction_delta,
            'prediction_delta_percent': self.prediction_delta_percent,
            'agreement_score': self.agreement_score,
            'explanation': self.explanation,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class DriftMetrics:
    """Metrics for tracking model drift over time."""
    dma_id: str
    metric_type: str
    period_start: datetime
    period_end: datetime
    
    # Delta statistics
    mean_prediction_delta: float
    std_prediction_delta: float
    max_prediction_delta: float
    min_prediction_delta: float
    
    # Agreement statistics
    agreement_rate: float  # % of time baseline and AI agree
    ai_only_anomaly_rate: float
    baseline_only_anomaly_rate: float
    
    # Drift assessment
    drift_severity: DriftSeverity
    drift_direction: str  # 'ai_higher', 'ai_lower', 'oscillating'
    drift_trend: float  # Slope of delta over time
    
    # Recommendations
    retrain_recommended: bool
    retrain_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'dma_id': self.dma_id,
            'metric_type': self.metric_type,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'mean_prediction_delta': self.mean_prediction_delta,
            'std_prediction_delta': self.std_prediction_delta,
            'max_prediction_delta': self.max_prediction_delta,
            'min_prediction_delta': self.min_prediction_delta,
            'agreement_rate': self.agreement_rate,
            'ai_only_anomaly_rate': self.ai_only_anomaly_rate,
            'baseline_only_anomaly_rate': self.baseline_only_anomaly_rate,
            'drift_severity': self.drift_severity.value,
            'drift_direction': self.drift_direction,
            'drift_trend': self.drift_trend,
            'retrain_recommended': self.retrain_recommended,
            'retrain_reason': self.retrain_reason
        }


@dataclass
class BaselineComparisonConfig:
    """Configuration for baseline comparison service."""
    # STL configuration
    stl_period: int = 96  # 15-min intervals per day
    stl_zscore_threshold: float = 3.0
    
    # AI configuration
    ai_confidence_threshold: float = 0.7
    ai_deviation_threshold_percent: float = 15.0
    
    # Comparison thresholds
    agreement_threshold: float = 0.8  # Consider agreeing if within this
    delta_warning_threshold: float = 10.0  # % delta to warn
    delta_critical_threshold: float = 25.0  # % delta for critical
    
    # Drift detection
    drift_window_hours: int = 24
    drift_samples_min: int = 48  # Minimum samples for drift calculation
    drift_trend_threshold: float = 0.05  # Slope threshold for drift
    
    # Retraining triggers
    retrain_agreement_threshold: float = 0.6  # Retrain if agreement below this
    retrain_drift_threshold: float = 0.1  # Retrain if drift slope exceeds


# =============================================================================
# BASELINE COMPARISON SERVICE
# =============================================================================

class BaselineComparisonService:
    """
    Service for comparing statistical baselines with AI predictions.
    
    This is the core of Component 4: STL + Prophet Baseline.
    
    The service:
    1. Runs STL decomposition for statistical baseline
    2. Runs AI models (Prophet/LSTM/Ensemble) for predictions
    3. Compares results and classifies verdict
    4. Tracks drift over time
    5. Triggers retraining recommendations
    """
    
    def __init__(self, config: Optional[BaselineComparisonConfig] = None):
        """Initialize the comparison service."""
        self.config = config or BaselineComparisonConfig()
        
        # Initialize detectors
        self.stl_detector = STLAnomalyDetector(
            period=self.config.stl_period,
            zscore_threshold=self.config.stl_zscore_threshold
        ) if STL_AVAILABLE else None
        
        self.prophet_forecaster = ProphetForecaster() if PROPHET_AVAILABLE else None
        self.lstm_forecaster = LSTMForecaster() if TF_AVAILABLE else None
        self.ensemble_forecaster = EnsembleForecaster()
        
        # Storage for comparison history (in-memory, should be persisted)
        self.comparison_history: Dict[str, List[ComparisonResult]] = {}  # dma_id -> results
        self.drift_history: Dict[str, List[DriftMetrics]] = {}  # dma_id -> metrics
        
        # Model fit status per DMA
        self.fitted_dmas: Dict[str, Dict[str, bool]] = {}  # dma_id -> {model: fitted}
        
        logger.info(
            f"BaselineComparisonService initialized - "
            f"STL: {STL_AVAILABLE}, Prophet: {PROPHET_AVAILABLE}, LSTM: {TF_AVAILABLE}"
        )
    
    def fit_models(
        self,
        dma_id: str,
        data: pd.DataFrame,
        value_column: str = 'value',
        timestamp_column: str = 'timestamp'
    ) -> Dict[str, bool]:
        """
        Fit all models for a specific DMA.
        
        Args:
            dma_id: District Metered Area identifier
            data: Historical data with timestamp and value columns
            value_column: Name of the value column
            timestamp_column: Name of the timestamp column
            
        Returns:
            Dictionary of model_name -> fit_success
        """
        fit_status = {}
        
        # Ensure data is properly formatted
        if timestamp_column in data.columns:
            df = data.copy()
            if not isinstance(df.index, pd.DatetimeIndex):
                df = df.set_index(timestamp_column)
        else:
            df = data.copy()
        
        # Fit Prophet
        if self.prophet_forecaster:
            try:
                prophet_df = df.reset_index()
                prophet_df.columns = ['ds', 'y'] if len(prophet_df.columns) == 2 else prophet_df.columns
                if 'ds' not in prophet_df.columns:
                    prophet_df = prophet_df.rename(columns={timestamp_column: 'ds', value_column: 'y'})
                self.prophet_forecaster.fit(prophet_df.reset_index(drop=True), 'y' if 'y' in prophet_df.columns else value_column)
                fit_status['prophet'] = True
                logger.info(f"Prophet fitted for DMA {dma_id}")
            except Exception as e:
                fit_status['prophet'] = False
                logger.error(f"Prophet fit failed for DMA {dma_id}: {e}")
        
        # Fit LSTM (needs more data)
        if self.lstm_forecaster and len(df) > 500:
            try:
                self.lstm_forecaster.fit(df.reset_index(), value_column)
                fit_status['lstm'] = True
                logger.info(f"LSTM fitted for DMA {dma_id}")
            except Exception as e:
                fit_status['lstm'] = False
                logger.error(f"LSTM fit failed for DMA {dma_id}: {e}")
        else:
            fit_status['lstm'] = False
        
        # Fit Ensemble
        try:
            self.ensemble_forecaster.fit(df.reset_index(), value_column)
            fit_status['ensemble'] = True
            logger.info(f"Ensemble fitted for DMA {dma_id}")
        except Exception as e:
            fit_status['ensemble'] = False
            logger.error(f"Ensemble fit failed for DMA {dma_id}: {e}")
        
        # STL doesn't need pre-fitting
        fit_status['stl'] = STL_AVAILABLE
        
        self.fitted_dmas[dma_id] = fit_status
        return fit_status
    
    def analyze_point(
        self,
        dma_id: str,
        timestamp: datetime,
        actual_value: float,
        metric_type: str,
        historical_data: pd.DataFrame,
        value_column: str = 'value'
    ) -> ComparisonResult:
        """
        Analyze a single data point comparing baseline vs AI.
        
        Args:
            dma_id: District Metered Area identifier
            timestamp: Timestamp of the data point
            actual_value: Actual observed value
            metric_type: Type of metric ('pressure', 'flow', 'noise_level')
            historical_data: Recent historical data for context
            value_column: Name of the value column
            
        Returns:
            ComparisonResult with baseline vs AI analysis
        """
        # Run STL baseline analysis
        baseline_result = self._run_stl_baseline(
            dma_id, timestamp, actual_value, metric_type,
            historical_data, value_column
        )
        
        # Run AI analysis
        ai_result = self._run_ai_analysis(
            dma_id, timestamp, actual_value, metric_type,
            historical_data, value_column
        )
        
        # Compare and determine verdict
        comparison = self._compare_results(
            timestamp, dma_id, metric_type, actual_value,
            baseline_result, ai_result
        )
        
        # Store in history
        if dma_id not in self.comparison_history:
            self.comparison_history[dma_id] = []
        self.comparison_history[dma_id].append(comparison)
        
        # Trim history to last 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        self.comparison_history[dma_id] = [
            c for c in self.comparison_history[dma_id]
            if c.timestamp > cutoff
        ]
        
        return comparison
    
    def _run_stl_baseline(
        self,
        dma_id: str,
        timestamp: datetime,
        actual_value: float,
        metric_type: str,
        historical_data: pd.DataFrame,
        value_column: str
    ) -> BaselineResult:
        """Run STL decomposition baseline analysis."""
        
        stl_trend = actual_value
        stl_seasonal = 0.0
        stl_residual = 0.0
        stl_expected = actual_value
        stl_deviation = 0.0
        stl_zscore = 0.0
        stl_is_anomaly = False
        
        if self.stl_detector and len(historical_data) >= self.config.stl_period:
            try:
                # Ensure proper index
                df = historical_data.copy()
                if value_column not in df.columns:
                    df.columns = ['timestamp', value_column] if len(df.columns) == 2 else df.columns
                
                decomp_df, anomalies = self.stl_detector.fit_transform(df, value_column)
                
                if len(decomp_df) > 0:
                    # Get the latest decomposition values
                    last_row = decomp_df.iloc[-1]
                    stl_trend = last_row.get('trend', actual_value)
                    stl_seasonal = last_row.get('seasonal', 0.0)
                    stl_residual = last_row.get('residual', 0.0)
                    stl_expected = stl_trend + stl_seasonal
                    stl_deviation = actual_value - stl_expected
                    
                    # Calculate z-score from residuals
                    residuals = decomp_df['residual'].dropna()
                    if len(residuals) > 0 and residuals.std() > 0:
                        stl_zscore = (actual_value - stl_expected) / residuals.std()
                    
                    stl_is_anomaly = abs(stl_zscore) > self.config.stl_zscore_threshold
                    
            except Exception as e:
                logger.warning(f"STL analysis failed for {dma_id}: {e}")
        
        return BaselineResult(
            timestamp=timestamp,
            dma_id=dma_id,
            metric_type=metric_type,
            actual_value=actual_value,
            stl_trend=stl_trend,
            stl_seasonal=stl_seasonal,
            stl_residual=stl_residual,
            stl_expected=stl_expected,
            stl_deviation=stl_deviation,
            stl_zscore=stl_zscore,
            stl_is_anomaly=stl_is_anomaly,
            stl_anomaly_threshold=self.config.stl_zscore_threshold
        )
    
    def _run_ai_analysis(
        self,
        dma_id: str,
        timestamp: datetime,
        actual_value: float,
        metric_type: str,
        historical_data: pd.DataFrame,
        value_column: str
    ) -> AIResult:
        """Run AI-based analysis (Prophet/LSTM/Ensemble)."""
        
        ai_predicted = actual_value
        ai_lower_bound = actual_value * 0.85
        ai_upper_bound = actual_value * 1.15
        ai_confidence = 0.5
        ai_model = 'fallback'
        
        # Try ensemble first
        if hasattr(self.ensemble_forecaster, 'models') and self.ensemble_forecaster.models:
            try:
                df = historical_data.copy()
                predictions = self.ensemble_forecaster.predict(df.reset_index(), value_column, steps=1)
                
                if 'ensemble' in predictions and len(predictions['ensemble']) > 0:
                    ai_predicted = float(predictions['ensemble'][0])
                    ai_model = 'ensemble'
                    ai_confidence = 0.85
                    
                    # Estimate bounds from individual model variance
                    model_preds = [predictions[m][0] for m in predictions if m != 'ensemble' and len(predictions[m]) > 0]
                    if model_preds:
                        pred_std = statistics.stdev(model_preds) if len(model_preds) > 1 else ai_predicted * 0.1
                        ai_lower_bound = ai_predicted - 2 * pred_std
                        ai_upper_bound = ai_predicted + 2 * pred_std
                        
            except Exception as e:
                logger.warning(f"Ensemble prediction failed for {dma_id}: {e}")
        
        # Fallback to Prophet
        elif self.prophet_forecaster and self.fitted_dmas.get(dma_id, {}).get('prophet'):
            try:
                forecast = self.prophet_forecaster.predict(periods=1, include_history=False)
                if len(forecast) > 0:
                    ai_predicted = float(forecast['predicted'].iloc[0])
                    ai_lower_bound = float(forecast['lower_95'].iloc[0])
                    ai_upper_bound = float(forecast['upper_95'].iloc[0])
                    ai_model = 'prophet'
                    ai_confidence = 0.8
            except Exception as e:
                logger.warning(f"Prophet prediction failed for {dma_id}: {e}")
        
        # Calculate deviation
        ai_deviation = actual_value - ai_predicted
        ai_deviation_percent = (ai_deviation / ai_predicted * 100) if ai_predicted != 0 else 0
        
        # Determine if anomaly
        ai_is_anomaly = (
            actual_value < ai_lower_bound or 
            actual_value > ai_upper_bound or
            abs(ai_deviation_percent) > self.config.ai_deviation_threshold_percent
        )
        
        return AIResult(
            timestamp=timestamp,
            dma_id=dma_id,
            metric_type=metric_type,
            actual_value=actual_value,
            ai_predicted=ai_predicted,
            ai_lower_bound=ai_lower_bound,
            ai_upper_bound=ai_upper_bound,
            ai_confidence=ai_confidence,
            ai_deviation=ai_deviation,
            ai_deviation_percent=ai_deviation_percent,
            ai_is_anomaly=ai_is_anomaly,
            ai_model=ai_model
        )
    
    def _compare_results(
        self,
        timestamp: datetime,
        dma_id: str,
        metric_type: str,
        actual_value: float,
        baseline: BaselineResult,
        ai: AIResult
    ) -> ComparisonResult:
        """Compare baseline and AI results to determine verdict."""
        
        # Determine verdict
        if baseline.stl_is_anomaly and ai.ai_is_anomaly:
            verdict = ComparisonVerdict.BOTH_AGREE_ANOMALY
        elif not baseline.stl_is_anomaly and not ai.ai_is_anomaly:
            verdict = ComparisonVerdict.BOTH_AGREE_NORMAL
        elif ai.ai_is_anomaly and not baseline.stl_is_anomaly:
            verdict = ComparisonVerdict.AI_ONLY_ANOMALY
        elif baseline.stl_is_anomaly and not ai.ai_is_anomaly:
            verdict = ComparisonVerdict.BASELINE_ONLY_ANOMALY
        else:
            verdict = ComparisonVerdict.CONFLICTING
        
        # Calculate prediction delta
        prediction_delta = ai.ai_predicted - baseline.stl_expected
        prediction_delta_percent = (
            (prediction_delta / baseline.stl_expected * 100) 
            if baseline.stl_expected != 0 else 0
        )
        
        # Calculate agreement score (0-1)
        # Based on how close the predictions are and anomaly classification agreement
        pred_agreement = max(0, 1 - abs(prediction_delta_percent) / 100)
        class_agreement = 1.0 if (baseline.stl_is_anomaly == ai.ai_is_anomaly) else 0.0
        agreement_score = 0.7 * pred_agreement + 0.3 * class_agreement
        
        # Generate explanation
        explanation = self._generate_explanation(baseline, ai, verdict, prediction_delta_percent)
        
        # Generate comparison ID
        comparison_id = f"{dma_id}_{timestamp.strftime('%Y%m%d%H%M%S')}_{metric_type}"
        
        return ComparisonResult(
            timestamp=timestamp,
            dma_id=dma_id,
            metric_type=metric_type,
            actual_value=actual_value,
            baseline=baseline,
            ai=ai,
            verdict=verdict,
            prediction_delta=prediction_delta,
            prediction_delta_percent=prediction_delta_percent,
            agreement_score=agreement_score,
            explanation=explanation,
            comparison_id=comparison_id
        )
    
    def _generate_explanation(
        self,
        baseline: BaselineResult,
        ai: AIResult,
        verdict: ComparisonVerdict,
        delta_percent: float
    ) -> str:
        """Generate human-readable explanation of comparison."""
        
        explanations = {
            ComparisonVerdict.BOTH_AGREE_NORMAL: (
                f"Both statistical baseline (STL z-score: {baseline.stl_zscore:.2f}) and "
                f"AI model ({ai.ai_model}, confidence: {ai.ai_confidence:.0%}) agree this reading is normal. "
                f"Prediction delta: {delta_percent:.1f}%."
            ),
            ComparisonVerdict.BOTH_AGREE_ANOMALY: (
                f"ALERT: Both methods detect an anomaly. "
                f"STL baseline shows z-score of {baseline.stl_zscore:.2f} (threshold: {baseline.stl_anomaly_threshold}). "
                f"AI model ({ai.ai_model}) predicted {ai.ai_predicted:.2f} but actual is {ai.actual_value:.2f} "
                f"({ai.ai_deviation_percent:+.1f}% deviation). High confidence anomaly."
            ),
            ComparisonVerdict.AI_ONLY_ANOMALY: (
                f"AI model ({ai.ai_model}) flags anomaly but statistical baseline shows normal. "
                f"STL z-score: {baseline.stl_zscore:.2f} (within normal range). "
                f"AI deviation: {ai.ai_deviation_percent:+.1f}%. "
                f"This may indicate a subtle pattern the AI learned that statistics don't capture."
            ),
            ComparisonVerdict.BASELINE_ONLY_ANOMALY: (
                f"Statistical baseline flags anomaly (z-score: {baseline.stl_zscore:.2f}) but AI model says normal. "
                f"AI predicted {ai.ai_predicted:.2f}, actual {ai.actual_value:.2f}. "
                f"The AI may have learned this pattern as acceptable, or the baseline is overly sensitive."
            ),
            ComparisonVerdict.CONFLICTING: (
                f"Conflicting assessments between baseline and AI. "
                f"Baseline z-score: {baseline.stl_zscore:.2f}, AI deviation: {ai.ai_deviation_percent:.1f}%. "
                f"Prediction delta: {delta_percent:.1f}%. Recommend manual review."
            )
        }
        
        return explanations.get(verdict, "Unknown comparison state.")
    
    def calculate_drift(
        self,
        dma_id: str,
        metric_type: str,
        window_hours: Optional[int] = None
    ) -> Optional[DriftMetrics]:
        """
        Calculate drift metrics between baseline and AI over a time window.
        
        Args:
            dma_id: District Metered Area identifier
            metric_type: Type of metric to analyze
            window_hours: Hours of history to analyze (default from config)
            
        Returns:
            DriftMetrics or None if insufficient data
        """
        window_hours = window_hours or self.config.drift_window_hours
        
        if dma_id not in self.comparison_history:
            return None
        
        # Filter relevant comparisons
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        relevant = [
            c for c in self.comparison_history[dma_id]
            if c.timestamp > cutoff and c.metric_type == metric_type
        ]
        
        if len(relevant) < self.config.drift_samples_min:
            logger.info(
                f"Insufficient data for drift calculation: "
                f"{len(relevant)} < {self.config.drift_samples_min}"
            )
            return None
        
        # Calculate delta statistics
        deltas = [c.prediction_delta_percent for c in relevant]
        mean_delta = statistics.mean(deltas)
        std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0
        max_delta = max(deltas)
        min_delta = min(deltas)
        
        # Calculate agreement statistics
        total = len(relevant)
        both_agree = sum(
            1 for c in relevant 
            if c.verdict in [ComparisonVerdict.BOTH_AGREE_NORMAL, ComparisonVerdict.BOTH_AGREE_ANOMALY]
        )
        ai_only = sum(1 for c in relevant if c.verdict == ComparisonVerdict.AI_ONLY_ANOMALY)
        baseline_only = sum(1 for c in relevant if c.verdict == ComparisonVerdict.BASELINE_ONLY_ANOMALY)
        
        agreement_rate = both_agree / total
        ai_only_rate = ai_only / total
        baseline_only_rate = baseline_only / total
        
        # Calculate drift trend (linear regression on deltas over time)
        timestamps = [(c.timestamp - relevant[0].timestamp).total_seconds() for c in relevant]
        if len(set(timestamps)) > 1:
            # Simple linear regression
            n = len(timestamps)
            sum_x = sum(timestamps)
            sum_y = sum(deltas)
            sum_xy = sum(t * d for t, d in zip(timestamps, deltas))
            sum_x2 = sum(t * t for t in timestamps)
            
            denominator = n * sum_x2 - sum_x * sum_x
            drift_trend = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0
        else:
            drift_trend = 0
        
        # Determine drift direction
        if abs(drift_trend) < 0.001:
            drift_direction = 'stable'
        elif drift_trend > 0:
            drift_direction = 'ai_higher'
        else:
            drift_direction = 'ai_lower'
        
        # Determine drift severity
        if abs(mean_delta) < 5 and agreement_rate > 0.9:
            drift_severity = DriftSeverity.NONE
        elif abs(mean_delta) < 10 and agreement_rate > 0.8:
            drift_severity = DriftSeverity.LOW
        elif abs(mean_delta) < 20 and agreement_rate > 0.7:
            drift_severity = DriftSeverity.MEDIUM
        elif abs(mean_delta) < 30 and agreement_rate > 0.6:
            drift_severity = DriftSeverity.HIGH
        else:
            drift_severity = DriftSeverity.CRITICAL
        
        # Determine if retraining is recommended
        retrain_recommended = (
            agreement_rate < self.config.retrain_agreement_threshold or
            abs(drift_trend) > self.config.retrain_drift_threshold or
            drift_severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]
        )
        
        retrain_reasons = []
        if agreement_rate < self.config.retrain_agreement_threshold:
            retrain_reasons.append(f"Low agreement rate ({agreement_rate:.0%})")
        if abs(drift_trend) > self.config.retrain_drift_threshold:
            retrain_reasons.append(f"High drift trend ({drift_trend:.4f})")
        if drift_severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
            retrain_reasons.append(f"Drift severity: {drift_severity.value}")
        
        retrain_reason = "; ".join(retrain_reasons) if retrain_reasons else "No retraining needed"
        
        drift_metrics = DriftMetrics(
            dma_id=dma_id,
            metric_type=metric_type,
            period_start=relevant[0].timestamp,
            period_end=relevant[-1].timestamp,
            mean_prediction_delta=mean_delta,
            std_prediction_delta=std_delta,
            max_prediction_delta=max_delta,
            min_prediction_delta=min_delta,
            agreement_rate=agreement_rate,
            ai_only_anomaly_rate=ai_only_rate,
            baseline_only_anomaly_rate=baseline_only_rate,
            drift_severity=drift_severity,
            drift_direction=drift_direction,
            drift_trend=drift_trend,
            retrain_recommended=retrain_recommended,
            retrain_reason=retrain_reason
        )
        
        # Store drift history
        if dma_id not in self.drift_history:
            self.drift_history[dma_id] = []
        self.drift_history[dma_id].append(drift_metrics)
        
        return drift_metrics
    
    def get_comparison_summary(
        self,
        dma_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary of comparisons for a DMA over specified hours.
        
        Args:
            dma_id: District Metered Area identifier
            hours: Hours of history to summarize
            
        Returns:
            Summary dictionary with statistics and recent comparisons
        """
        if dma_id not in self.comparison_history:
            return {
                'dma_id': dma_id,
                'period_hours': hours,
                'total_comparisons': 0,
                'message': 'No comparison data available'
            }
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        relevant = [c for c in self.comparison_history[dma_id] if c.timestamp > cutoff]
        
        if not relevant:
            return {
                'dma_id': dma_id,
                'period_hours': hours,
                'total_comparisons': 0,
                'message': f'No comparisons in the last {hours} hours'
            }
        
        # Count verdicts
        verdict_counts = {}
        for verdict in ComparisonVerdict:
            verdict_counts[verdict.value] = sum(1 for c in relevant if c.verdict == verdict)
        
        # Calculate statistics
        agreement_scores = [c.agreement_score for c in relevant]
        deltas = [c.prediction_delta_percent for c in relevant]
        
        return {
            'dma_id': dma_id,
            'period_hours': hours,
            'period_start': relevant[0].timestamp.isoformat(),
            'period_end': relevant[-1].timestamp.isoformat(),
            'total_comparisons': len(relevant),
            'verdict_distribution': verdict_counts,
            'statistics': {
                'mean_agreement_score': statistics.mean(agreement_scores),
                'min_agreement_score': min(agreement_scores),
                'max_agreement_score': max(agreement_scores),
                'mean_prediction_delta_percent': statistics.mean(deltas),
                'std_prediction_delta_percent': statistics.stdev(deltas) if len(deltas) > 1 else 0
            },
            'recent_anomalies': [
                c.to_dict() for c in relevant[-10:]
                if c.verdict in [
                    ComparisonVerdict.BOTH_AGREE_ANOMALY,
                    ComparisonVerdict.AI_ONLY_ANOMALY,
                    ComparisonVerdict.BASELINE_ONLY_ANOMALY
                ]
            ],
            'models_used': list(set(c.ai.ai_model for c in relevant))
        }
    
    def get_api_response(
        self,
        dma_id: str,
        include_drift: bool = True,
        include_history: bool = False,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive API response for dashboard integration.
        
        Args:
            dma_id: District Metered Area identifier
            include_drift: Include drift metrics
            include_history: Include full comparison history
            hours: Hours of history to include
            
        Returns:
            API response dictionary
        """
        response = {
            'dma_id': dma_id,
            'timestamp': datetime.utcnow().isoformat(),
            'summary': self.get_comparison_summary(dma_id, hours),
            'models_available': {
                'stl': STL_AVAILABLE,
                'prophet': PROPHET_AVAILABLE,
                'lstm': TF_AVAILABLE,
                'fitted': self.fitted_dmas.get(dma_id, {})
            }
        }
        
        if include_drift:
            for metric_type in ['pressure', 'flow', 'noise_level']:
                drift = self.calculate_drift(dma_id, metric_type)
                if drift:
                    response[f'drift_{metric_type}'] = drift.to_dict()
        
        if include_history and dma_id in self.comparison_history:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            response['history'] = [
                c.to_dict() for c in self.comparison_history[dma_id]
                if c.timestamp > cutoff
            ]
        
        return response


# =============================================================================
# API ENDPOINTS (Flask Integration)
# =============================================================================

def create_baseline_api(service: BaselineComparisonService):
    """
    Create Flask Blueprint for baseline comparison API.
    
    Usage:
        from flask import Flask
        from baseline_comparison import BaselineComparisonService, create_baseline_api
        
        app = Flask(__name__)
        service = BaselineComparisonService()
        app.register_blueprint(create_baseline_api(service), url_prefix='/api/v1/baseline')
    """
    from flask import Blueprint, jsonify, request
    
    bp = Blueprint('baseline_comparison', __name__)
    
    @bp.route('/compare/<dma_id>', methods=['POST'])
    def compare_point(dma_id: str):
        """
        Compare a single data point.
        
        POST /api/v1/baseline/compare/DMA001
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "value": 3.45,
            "metric_type": "pressure",
            "historical_data": [...]  // Optional, recent 24h data
        }
        """
        data = request.get_json()
        
        try:
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            value = float(data['value'])
            metric_type = data.get('metric_type', 'pressure')
            
            # Get historical data from request or fetch from storage
            if 'historical_data' in data:
                historical = pd.DataFrame(data['historical_data'])
            else:
                # Would fetch from database in production
                historical = pd.DataFrame({
                    'timestamp': pd.date_range(end=timestamp, periods=96, freq='15min'),
                    'value': np.random.normal(value, 0.1, 96)
                })
            
            result = service.analyze_point(
                dma_id=dma_id,
                timestamp=timestamp,
                actual_value=value,
                metric_type=metric_type,
                historical_data=historical
            )
            
            return jsonify(result.to_dict())
            
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return jsonify({'error': str(e)}), 400
    
    @bp.route('/summary/<dma_id>', methods=['GET'])
    def get_summary(dma_id: str):
        """
        Get comparison summary for a DMA.
        
        GET /api/v1/baseline/summary/DMA001?hours=24
        """
        hours = request.args.get('hours', 24, type=int)
        return jsonify(service.get_comparison_summary(dma_id, hours))
    
    @bp.route('/drift/<dma_id>/<metric_type>', methods=['GET'])
    def get_drift(dma_id: str, metric_type: str):
        """
        Get drift metrics for a DMA and metric type.
        
        GET /api/v1/baseline/drift/DMA001/pressure?window_hours=24
        """
        window_hours = request.args.get('window_hours', 24, type=int)
        drift = service.calculate_drift(dma_id, metric_type, window_hours)
        
        if drift:
            return jsonify(drift.to_dict())
        else:
            return jsonify({
                'error': 'Insufficient data for drift calculation',
                'dma_id': dma_id,
                'metric_type': metric_type
            }), 404
    
    @bp.route('/dashboard/<dma_id>', methods=['GET'])
    def get_dashboard_data(dma_id: str):
        """
        Get comprehensive dashboard data for a DMA.
        
        GET /api/v1/baseline/dashboard/DMA001?hours=24&include_history=true
        """
        hours = request.args.get('hours', 24, type=int)
        include_history = request.args.get('include_history', 'false').lower() == 'true'
        
        return jsonify(service.get_api_response(
            dma_id=dma_id,
            include_drift=True,
            include_history=include_history,
            hours=hours
        ))
    
    @bp.route('/fit/<dma_id>', methods=['POST'])
    def fit_models(dma_id: str):
        """
        Fit models for a DMA using provided historical data.
        
        POST /api/v1/baseline/fit/DMA001
        {
            "data": [...],  // Historical data array
            "value_column": "pressure"
        }
        """
        data = request.get_json()
        
        try:
            historical = pd.DataFrame(data['data'])
            value_column = data.get('value_column', 'value')
            
            fit_status = service.fit_models(dma_id, historical, value_column)
            
            return jsonify({
                'dma_id': dma_id,
                'fit_status': fit_status,
                'message': 'Models fitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Model fitting failed: {e}")
            return jsonify({'error': str(e)}), 400
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'models_available': {
                'stl': STL_AVAILABLE,
                'prophet': PROPHET_AVAILABLE,
                'lstm': TF_AVAILABLE
            },
            'fitted_dmas': list(service.fitted_dmas.keys()),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return bp


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("AQUAWATCH NRW - BASELINE COMPARISON SERVICE DEMO")
    print("Component 4: STL + Prophet Baseline")
    print("=" * 80)
    
    # Initialize service
    config = BaselineComparisonConfig(
        stl_period=96,
        stl_zscore_threshold=3.0,
        ai_deviation_threshold_percent=15.0
    )
    service = BaselineComparisonService(config)
    
    print(f"\nService initialized:")
    print(f"  STL Available: {STL_AVAILABLE}")
    print(f"  Prophet Available: {PROPHET_AVAILABLE}")
    print(f"  LSTM Available: {TF_AVAILABLE}")
    
    # Generate sample data
    print("\n--- Generating Sample Data ---")
    from .time_series_forecasting import generate_sample_pressure_data
    sample_data = generate_sample_pressure_data(days=7)
    print(f"Generated {len(sample_data)} samples")
    
    # Fit models
    print("\n--- Fitting Models for DMA001 ---")
    fit_status = service.fit_models('DMA001', sample_data.reset_index(), 'value', 'timestamp')
    for model, status in fit_status.items():
        print(f"  {model}: {'✓' if status else '✗'}")
    
    # Analyze some points
    print("\n--- Analyzing Data Points ---")
    recent_data = sample_data.iloc[-96:]  # Last 24 hours (96 x 15min)
    
    for i in range(5):
        idx = len(sample_data) - 5 + i
        timestamp = sample_data.index[idx]
        value = sample_data['value'].iloc[idx]
        
        result = service.analyze_point(
            dma_id='DMA001',
            timestamp=timestamp,
            actual_value=value,
            metric_type='pressure',
            historical_data=sample_data.iloc[:idx].reset_index()
        )
        
        print(f"\n  Point {i+1}: {timestamp}")
        print(f"    Actual: {value:.3f}")
        print(f"    STL Expected: {result.baseline.stl_expected:.3f} (z-score: {result.baseline.stl_zscore:.2f})")
        print(f"    AI Predicted: {result.ai.ai_predicted:.3f} ({result.ai.ai_model})")
        print(f"    Verdict: {result.verdict.value}")
        print(f"    Agreement: {result.agreement_score:.0%}")
    
    # Get summary
    print("\n--- DMA001 Summary ---")
    summary = service.get_comparison_summary('DMA001', hours=24)
    print(f"  Total comparisons: {summary['total_comparisons']}")
    print(f"  Verdict distribution: {summary.get('verdict_distribution', {})}")
    
    # Get drift metrics
    print("\n--- Drift Analysis ---")
    drift = service.calculate_drift('DMA001', 'pressure', window_hours=24)
    if drift:
        print(f"  Mean delta: {drift.mean_prediction_delta:.2f}%")
        print(f"  Agreement rate: {drift.agreement_rate:.0%}")
        print(f"  Drift severity: {drift.drift_severity.value}")
        print(f"  Retrain recommended: {drift.retrain_recommended}")
        if drift.retrain_recommended:
            print(f"  Reason: {drift.retrain_reason}")
    else:
        print("  Insufficient data for drift calculation")
    
    print("\n" + "=" * 80)
    print("Demo complete. Use create_baseline_api() for Flask integration.")
    print("=" * 80)
