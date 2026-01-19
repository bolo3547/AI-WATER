"""
AquaWatch NRW - Continuous Learning System
==========================================

Component 5️⃣: Continuous Learning Pipeline

Implements the feedback loop for model improvement:
1. Store field confirmation labels
2. Track model performance over time
3. Trigger retraining when performance degrades
4. Transition from unsupervised to supervised learning
5. Integrate with baseline comparison drift detection
6. Auto-retraining triggers based on drift metrics

This is CRITICAL for a production system.
Without feedback, the AI cannot improve.

Key Principle: Every field investigation is a learning opportunity.

LOCKED INTEGRATION:
- Baseline drift triggers auto-retraining
- Field feedback stores feature snapshots for supervised learning
- Performance metrics drive alert threshold adjustments

Author: AquaWatch AI Team
Version: 2.0.0
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import pickle
import logging
import hashlib

# Type checking imports
if TYPE_CHECKING:
    from .baseline_comparison import BaselineComparisonService, DriftMetrics

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class FeedbackType(Enum):
    """Types of field feedback."""
    LEAK_CONFIRMED = "leak_confirmed"           # AI was right - leak found
    LEAK_NEARBY = "leak_nearby"                 # Leak found within 100m
    NO_LEAK_FOUND = "no_leak_found"             # AI false positive
    OPERATIONAL_EVENT = "operational_event"     # Valve operation, flushing
    SENSOR_FAULT = "sensor_fault"               # Sensor malfunction
    INCONCLUSIVE = "inconclusive"               # Could not determine
    APPARENT_LOSS = "apparent_loss"             # Commercial loss (theft/meter)
    BASELINE_DRIFT = "baseline_drift"           # Triggered by baseline comparison drift


class ModelStatus(Enum):
    """Model lifecycle status."""
    INITIAL = "initial"              # Using unsupervised only
    LEARNING = "learning"            # Collecting labels
    READY_TO_TRAIN = "ready_to_train"  # Enough labels for supervised
    SUPERVISED = "supervised"        # Using supervised model
    RETRAINING = "retraining"        # Currently retraining
    DRIFT_DETECTED = "drift_detected"  # Baseline drift detected


class PerformanceMetric(Enum):
    """Model performance metrics to track."""
    PRECISION = "precision"          # TP / (TP + FP)
    RECALL = "recall"                # TP / (TP + FN)
    F1_SCORE = "f1_score"            # Harmonic mean
    FALSE_POSITIVE_RATE = "fpr"      # FP / (FP + TN)
    DETECTION_RATE = "detection_rate"  # % of leaks caught
    MEAN_TIME_TO_DETECT = "mttd"     # Average detection time


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FieldFeedback:
    """
    Field feedback from leak investigation.
    
    This is the GOLD STANDARD LABEL for model training.
    """
    feedback_id: str
    alert_id: str                    # Original AI alert
    dma_id: str
    timestamp: datetime
    
    # The field result
    feedback_type: FeedbackType
    leak_confirmed: bool             # Binary for training
    
    # Location info (if leak found)
    actual_location_lat: Optional[float] = None
    actual_location_lon: Optional[float] = None
    distance_from_prediction_m: Optional[float] = None
    
    # Leak details (if confirmed)
    leak_type: Optional[str] = None  # burst, joint, corrosion
    leak_size: Optional[str] = None  # small, medium, large
    estimated_flow_m3_day: Optional[float] = None
    
    # Investigation details
    investigator_id: Optional[str] = None
    investigation_time_hours: Optional[float] = None
    notes: Optional[str] = None
    
    # Feature snapshot at time of alert (for training)
    feature_snapshot: Optional[Dict[str, float]] = None
    
    # AI prediction that was being evaluated
    ai_probability: Optional[float] = None
    ai_confidence: Optional[float] = None
    
    def to_training_sample(self) -> Tuple[Dict[str, float], int]:
        """Convert to (features, label) for training."""
        if self.feature_snapshot is None:
            return {}, 0
        label = 1 if self.leak_confirmed else 0
        return self.feature_snapshot, label
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "alert_id": self.alert_id,
            "dma_id": self.dma_id,
            "timestamp": self.timestamp.isoformat(),
            "feedback_type": self.feedback_type.value,
            "leak_confirmed": self.leak_confirmed,
            "actual_location": {
                "lat": self.actual_location_lat,
                "lon": self.actual_location_lon
            } if self.actual_location_lat else None,
            "distance_from_prediction_m": self.distance_from_prediction_m,
            "leak_details": {
                "type": self.leak_type,
                "size": self.leak_size,
                "flow_m3_day": self.estimated_flow_m3_day
            } if self.leak_confirmed else None,
            "ai_prediction": {
                "probability": self.ai_probability,
                "confidence": self.ai_confidence
            }
        }


@dataclass
class ModelPerformanceSnapshot:
    """
    Snapshot of model performance at a point in time.
    """
    snapshot_id: str
    model_version: str
    timestamp: datetime
    
    # Performance metrics
    total_alerts: int
    confirmed_leaks: int
    false_positives: int
    missed_leaks: int               # Leaks found without AI alert
    
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    
    # Detection timing
    mean_time_to_detect_hours: float
    
    # Water impact
    total_water_saved_m3: float
    total_revenue_saved_usd: float
    
    # Evaluation period
    period_start: datetime
    period_end: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "model_version": self.model_version,
            "timestamp": self.timestamp.isoformat(),
            "metrics": {
                "precision": round(self.precision, 3),
                "recall": round(self.recall, 3),
                "f1_score": round(self.f1_score, 3),
                "false_positive_rate": round(self.false_positive_rate, 3)
            },
            "counts": {
                "total_alerts": self.total_alerts,
                "confirmed_leaks": self.confirmed_leaks,
                "false_positives": self.false_positives,
                "missed_leaks": self.missed_leaks
            },
            "impact": {
                "water_saved_m3": round(self.total_water_saved_m3, 0),
                "revenue_saved_usd": round(self.total_revenue_saved_usd, 0)
            },
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            }
        }


@dataclass
class RetrainingTrigger:
    """
    Conditions that trigger model retraining.
    """
    trigger_id: str
    triggered_at: datetime
    reason: str
    
    # What triggered it
    metric_name: str
    current_value: float
    threshold_value: float
    
    # Recommended action
    action: str
    priority: str  # low, medium, high, critical


@dataclass
class ContinuousLearningConfig:
    """
    Configuration for the continuous learning system.
    """
    # Label collection thresholds
    min_labels_for_supervised: int = 100      # Minimum labels to train supervised
    min_positive_labels: int = 30             # Minimum confirmed leaks
    
    # Performance thresholds
    min_precision: float = 0.60               # Below this = too many false positives
    min_recall: float = 0.70                  # Below this = missing too many leaks
    max_false_positive_rate: float = 0.30     # Above this = operator fatigue
    
    # Retraining triggers
    performance_check_interval_days: int = 7  # Check every week
    retrain_on_n_new_labels: int = 50         # Retrain after N new labels
    
    # Model storage
    model_storage_path: str = "./models"
    keep_n_versions: int = 5                  # Keep last N model versions
    
    # Water tariff for impact calculation (USD/m³)
    water_tariff_usd_per_m3: float = 0.50
    
    # Baseline drift integration (Component 4 integration)
    drift_retrain_agreement_threshold: float = 0.6   # Retrain if agreement below this
    drift_retrain_delta_threshold: float = 20.0      # Retrain if mean delta exceeds %
    drift_check_interval_hours: int = 6              # Check drift every N hours
    auto_retrain_on_drift: bool = True               # Auto-trigger retraining on drift


# =============================================================================
# LABEL STORAGE
# =============================================================================

class LabelStore:
    """
    Persistent storage for field feedback labels.
    
    This is the source of truth for model training.
    """
    
    def __init__(self, storage_path: str = "./data/labels"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.labels_file = self.storage_path / "field_feedback.json"
        self._labels: List[FieldFeedback] = []
        self._load()
    
    def _load(self):
        """Load existing labels from storage."""
        if self.labels_file.exists():
            try:
                with open(self.labels_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Reconstruct FieldFeedback objects
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        item['feedback_type'] = FeedbackType(item['feedback_type'])
                        self._labels.append(FieldFeedback(**item))
                logger.info(f"Loaded {len(self._labels)} labels from storage")
            except Exception as e:
                logger.error(f"Failed to load labels: {e}")
                self._labels = []
    
    def _save(self):
        """Save labels to storage."""
        data = []
        for label in self._labels:
            item = {
                'feedback_id': label.feedback_id,
                'alert_id': label.alert_id,
                'dma_id': label.dma_id,
                'timestamp': label.timestamp.isoformat(),
                'feedback_type': label.feedback_type.value,
                'leak_confirmed': label.leak_confirmed,
                'actual_location_lat': label.actual_location_lat,
                'actual_location_lon': label.actual_location_lon,
                'distance_from_prediction_m': label.distance_from_prediction_m,
                'leak_type': label.leak_type,
                'leak_size': label.leak_size,
                'estimated_flow_m3_day': label.estimated_flow_m3_day,
                'investigator_id': label.investigator_id,
                'investigation_time_hours': label.investigation_time_hours,
                'notes': label.notes,
                'feature_snapshot': label.feature_snapshot,
                'ai_probability': label.ai_probability,
                'ai_confidence': label.ai_confidence
            }
            data.append(item)
        
        with open(self.labels_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_feedback(self, feedback: FieldFeedback) -> str:
        """Add new field feedback."""
        # Generate ID if not provided
        if not feedback.feedback_id:
            feedback.feedback_id = self._generate_id(feedback)
        
        self._labels.append(feedback)
        self._save()
        
        logger.info(f"Added feedback {feedback.feedback_id}: {feedback.feedback_type.value}")
        return feedback.feedback_id
    
    def _generate_id(self, feedback: FieldFeedback) -> str:
        """Generate unique feedback ID."""
        content = f"{feedback.alert_id}{feedback.timestamp.isoformat()}"
        return f"FB-{hashlib.md5(content.encode()).hexdigest()[:8].upper()}"
    
    def get_all(self) -> List[FieldFeedback]:
        """Get all feedback labels."""
        return self._labels.copy()
    
    def get_by_dma(self, dma_id: str) -> List[FieldFeedback]:
        """Get feedback for specific DMA."""
        return [l for l in self._labels if l.dma_id == dma_id]
    
    def get_confirmed_leaks(self) -> List[FieldFeedback]:
        """Get only confirmed leak labels."""
        return [l for l in self._labels if l.leak_confirmed]
    
    def get_false_positives(self) -> List[FieldFeedback]:
        """Get only false positive labels."""
        return [
            l for l in self._labels 
            if l.feedback_type in [FeedbackType.NO_LEAK_FOUND, 
                                   FeedbackType.OPERATIONAL_EVENT,
                                   FeedbackType.SENSOR_FAULT]
        ]
    
    def get_training_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Get labels formatted for model training.
        
        Returns:
            (features_df, labels_array)
        """
        features_list = []
        labels_list = []
        
        for feedback in self._labels:
            if feedback.feature_snapshot:
                features_list.append(feedback.feature_snapshot)
                labels_list.append(1 if feedback.leak_confirmed else 0)
        
        if not features_list:
            return pd.DataFrame(), np.array([])
        
        features_df = pd.DataFrame(features_list)
        labels_array = np.array(labels_list)
        
        return features_df, labels_array
    
    def get_stats(self) -> Dict[str, Any]:
        """Get label statistics."""
        total = len(self._labels)
        confirmed = len([l for l in self._labels if l.leak_confirmed])
        
        by_type = {}
        for feedback_type in FeedbackType:
            by_type[feedback_type.value] = len(
                [l for l in self._labels if l.feedback_type == feedback_type]
            )
        
        return {
            "total_labels": total,
            "confirmed_leaks": confirmed,
            "false_positives": total - confirmed,
            "positive_rate": confirmed / total if total > 0 else 0,
            "by_type": by_type
        }


# =============================================================================
# PERFORMANCE TRACKER
# =============================================================================

class PerformanceTracker:
    """
    Tracks model performance over time.
    
    Key metrics:
    - Precision: How often alerts are real leaks
    - Recall: How many real leaks we catch
    - F1: Balance between precision and recall
    - Water saved: Business impact metric
    """
    
    def __init__(self, config: ContinuousLearningConfig):
        self.config = config
        self.snapshots: List[ModelPerformanceSnapshot] = []
        self.storage_path = Path(config.model_storage_path) / "performance"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def calculate_performance(
        self,
        label_store: LabelStore,
        period_start: datetime,
        period_end: datetime,
        model_version: str = "current"
    ) -> ModelPerformanceSnapshot:
        """
        Calculate performance metrics for a time period.
        """
        # Get labels in period
        labels = [
            l for l in label_store.get_all()
            if period_start <= l.timestamp <= period_end
        ]
        
        if not labels:
            return self._empty_snapshot(model_version, period_start, period_end)
        
        # Count outcomes
        total_alerts = len(labels)
        confirmed_leaks = len([l for l in labels if l.leak_confirmed])
        false_positives = total_alerts - confirmed_leaks
        
        # Precision and recall
        # Note: True negatives and missed leaks require additional data
        precision = confirmed_leaks / total_alerts if total_alerts > 0 else 0
        
        # For recall, we need to know total actual leaks (including those we missed)
        # Use proxy: alerts + missed leaks reported separately
        missed_leaks = 0  # Would come from separate tracking
        total_actual_leaks = confirmed_leaks + missed_leaks
        recall = confirmed_leaks / total_actual_leaks if total_actual_leaks > 0 else 0
        
        # F1 score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0
        
        # False positive rate (needs total negatives estimate)
        # Proxy: FP / total alerts
        fpr = false_positives / total_alerts if total_alerts > 0 else 0
        
        # Water impact
        total_water_saved = sum(
            l.estimated_flow_m3_day or 0 
            for l in labels 
            if l.leak_confirmed
        )
        
        # Assume average repair time reduces ongoing loss
        avg_days_saved = 30  # Assume leak would run 30 more days without detection
        total_water_saved_m3 = total_water_saved * avg_days_saved
        total_revenue_saved = total_water_saved_m3 * self.config.water_tariff_usd_per_m3
        
        # Mean time to detect
        detection_times = [
            l.investigation_time_hours 
            for l in labels 
            if l.investigation_time_hours
        ]
        mttd = float(np.mean(detection_times)) if detection_times else 0.0
        
        snapshot = ModelPerformanceSnapshot(
            snapshot_id=self._generate_snapshot_id(model_version, period_end),
            model_version=model_version,
            timestamp=datetime.utcnow(),
            total_alerts=total_alerts,
            confirmed_leaks=confirmed_leaks,
            false_positives=false_positives,
            missed_leaks=missed_leaks,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            false_positive_rate=fpr,
            mean_time_to_detect_hours=mttd,
            total_water_saved_m3=total_water_saved_m3,
            total_revenue_saved_usd=total_revenue_saved,
            period_start=period_start,
            period_end=period_end
        )
        
        self.snapshots.append(snapshot)
        self._save_snapshot(snapshot)
        
        return snapshot
    
    def _empty_snapshot(
        self, 
        model_version: str, 
        period_start: datetime, 
        period_end: datetime
    ) -> ModelPerformanceSnapshot:
        """Return empty snapshot when no data available."""
        return ModelPerformanceSnapshot(
            snapshot_id=self._generate_snapshot_id(model_version, period_end),
            model_version=model_version,
            timestamp=datetime.utcnow(),
            total_alerts=0,
            confirmed_leaks=0,
            false_positives=0,
            missed_leaks=0,
            precision=0,
            recall=0,
            f1_score=0,
            false_positive_rate=0,
            mean_time_to_detect_hours=0,
            total_water_saved_m3=0,
            total_revenue_saved_usd=0,
            period_start=period_start,
            period_end=period_end
        )
    
    def _generate_snapshot_id(self, model_version: str, period_end: datetime) -> str:
        content = f"{model_version}{period_end.isoformat()}"
        return f"PERF-{hashlib.md5(content.encode()).hexdigest()[:8].upper()}"
    
    def _save_snapshot(self, snapshot: ModelPerformanceSnapshot):
        """Save snapshot to file."""
        filepath = self.storage_path / f"{snapshot.snapshot_id}.json"
        with open(filepath, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    def check_retraining_triggers(
        self,
        latest_snapshot: ModelPerformanceSnapshot
    ) -> Optional[RetrainingTrigger]:
        """
        Check if model retraining is needed.
        """
        # Check precision
        if latest_snapshot.precision < self.config.min_precision:
            return RetrainingTrigger(
                trigger_id=f"TRIG-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                triggered_at=datetime.utcnow(),
                reason="Precision below threshold",
                metric_name="precision",
                current_value=latest_snapshot.precision,
                threshold_value=self.config.min_precision,
                action="Retrain model to reduce false positives",
                priority="high"
            )
        
        # Check recall
        if latest_snapshot.recall < self.config.min_recall:
            return RetrainingTrigger(
                trigger_id=f"TRIG-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                triggered_at=datetime.utcnow(),
                reason="Recall below threshold",
                metric_name="recall",
                current_value=latest_snapshot.recall,
                threshold_value=self.config.min_recall,
                action="Retrain model to catch more leaks",
                priority="critical"
            )
        
        # Check false positive rate
        if latest_snapshot.false_positive_rate > self.config.max_false_positive_rate:
            return RetrainingTrigger(
                trigger_id=f"TRIG-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                triggered_at=datetime.utcnow(),
                reason="False positive rate too high",
                metric_name="false_positive_rate",
                current_value=latest_snapshot.false_positive_rate,
                threshold_value=self.config.max_false_positive_rate,
                action="Retrain model to reduce operator fatigue",
                priority="high"
            )
        
        return None
    
    def get_performance_trend(
        self,
        metric: PerformanceMetric,
        n_periods: int = 12
    ) -> List[Tuple[datetime, float]]:
        """Get trend of a metric over time."""
        recent = sorted(self.snapshots, key=lambda x: x.timestamp)[-n_periods:]
        
        trend = []
        for snapshot in recent:
            if metric == PerformanceMetric.PRECISION:
                value = snapshot.precision
            elif metric == PerformanceMetric.RECALL:
                value = snapshot.recall
            elif metric == PerformanceMetric.F1_SCORE:
                value = snapshot.f1_score
            elif metric == PerformanceMetric.FALSE_POSITIVE_RATE:
                value = snapshot.false_positive_rate
            else:
                value = 0
            
            trend.append((snapshot.timestamp, value))
        
        return trend


# =============================================================================
# MODEL RETRAINING PIPELINE
# =============================================================================

class ModelRetrainingPipeline:
    """
    Handles automatic model retraining.
    
    Workflow:
    1. Collect sufficient labels
    2. Evaluate current performance
    3. Retrain if needed
    4. Validate new model
    5. Deploy if improved
    """
    
    def __init__(
        self,
        config: ContinuousLearningConfig,
        label_store: LabelStore,
        performance_tracker: PerformanceTracker
    ):
        self.config = config
        self.label_store = label_store
        self.performance_tracker = performance_tracker
        self.model_status = ModelStatus.INITIAL
        self.current_model_version = "v0.1.0"
        
        self.model_path = Path(config.model_storage_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    def check_readiness(self) -> Dict[str, Any]:
        """
        Check if system is ready for supervised learning.
        """
        stats = self.label_store.get_stats()
        
        ready = (
            stats['total_labels'] >= self.config.min_labels_for_supervised and
            stats['confirmed_leaks'] >= self.config.min_positive_labels
        )
        
        return {
            "ready_for_supervised": ready,
            "total_labels": stats['total_labels'],
            "required_labels": self.config.min_labels_for_supervised,
            "confirmed_leaks": stats['confirmed_leaks'],
            "required_positive": self.config.min_positive_labels,
            "current_status": self.model_status.value,
            "progress_percent": min(100, (stats['total_labels'] / self.config.min_labels_for_supervised) * 100)
        }
    
    def retrain_model(
        self,
        model_class: Any,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Retrain the leak probability model with new labels.
        
        Args:
            model_class: The model class to instantiate and train
            feature_columns: List of feature column names to use
            
        Returns:
            Training results including metrics
        """
        # Get training data
        features_df, labels = self.label_store.get_training_data()
        
        if len(features_df) < self.config.min_labels_for_supervised:
            return {
                "success": False,
                "error": "Insufficient training data",
                "samples": len(features_df),
                "required": self.config.min_labels_for_supervised
            }
        
        # Align features
        available_features = [c for c in feature_columns if c in features_df.columns]
        X = features_df[available_features].fillna(0)
        y = labels
        
        # Train model
        from sklearn.model_selection import train_test_split, cross_val_score
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Initialize and train
        model = model_class()
        model.fit(X_train, y_train)
        
        # Evaluate
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        y_pred = model.predict(X_test)
        
        metrics = {
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred)
        }
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1')
        metrics["cv_f1_mean"] = cv_scores.mean()
        metrics["cv_f1_std"] = cv_scores.std()
        
        # Generate new version
        new_version = self._increment_version()
        
        # Save model
        model_file = self.model_path / f"leak_model_{new_version}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # Update status
        self.model_status = ModelStatus.SUPERVISED
        self.current_model_version = new_version
        
        logger.info(f"Model retrained: version {new_version}, F1={metrics['f1']:.3f}")
        
        return {
            "success": True,
            "model_version": new_version,
            "model_file": str(model_file),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": metrics,
            "features_used": available_features
        }
    
    def _increment_version(self) -> str:
        """Increment model version number."""
        parts = self.current_model_version.replace('v', '').split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return 'v' + '.'.join(parts)
    
    def get_model_history(self) -> List[Dict[str, Any]]:
        """Get history of model versions."""
        history = []
        
        for model_file in sorted(self.model_path.glob("leak_model_v*.pkl")):
            version = model_file.stem.replace("leak_model_", "")
            stat = model_file.stat()
            history.append({
                "version": version,
                "file": str(model_file),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size_kb": stat.st_size / 1024
            })
        
        return history


# =============================================================================
# MAIN CONTINUOUS LEARNING CONTROLLER
# =============================================================================

class ContinuousLearningController:
    """
    Main controller for the continuous learning system.
    
    This is the interface for the rest of the application.
    """
    
    def __init__(self, config: Optional[ContinuousLearningConfig] = None):
        self.config = config or ContinuousLearningConfig()
        self.label_store = LabelStore()
        self.performance_tracker = PerformanceTracker(self.config)
        self.retraining_pipeline = ModelRetrainingPipeline(
            self.config, self.label_store, self.performance_tracker
        )
        
        logger.info("Continuous Learning Controller initialized")
    
    def record_feedback(
        self,
        alert_id: str,
        dma_id: str,
        feedback_type: FeedbackType,
        feature_snapshot: Optional[Dict[str, float]] = None,
        ai_probability: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Record field feedback for an alert.
        
        This is the main entry point for the feedback loop.
        """
        leak_confirmed = feedback_type in [
            FeedbackType.LEAK_CONFIRMED,
            FeedbackType.LEAK_NEARBY,
            FeedbackType.APPARENT_LOSS
        ]
        
        feedback = FieldFeedback(
            feedback_id="",  # Will be generated
            alert_id=alert_id,
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            feedback_type=feedback_type,
            leak_confirmed=leak_confirmed,
            feature_snapshot=feature_snapshot,
            ai_probability=ai_probability,
            **kwargs
        )
        
        feedback_id = self.label_store.add_feedback(feedback)
        
        # Check if we should transition to supervised learning
        self._check_transition()
        
        return feedback_id
    
    def _check_transition(self):
        """Check if ready to transition to supervised learning."""
        readiness = self.retraining_pipeline.check_readiness()
        
        if readiness['ready_for_supervised']:
            if self.retraining_pipeline.model_status == ModelStatus.INITIAL:
                self.retraining_pipeline.model_status = ModelStatus.READY_TO_TRAIN
                logger.info("System ready for supervised learning!")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall continuous learning status."""
        readiness = self.retraining_pipeline.check_readiness()
        label_stats = self.label_store.get_stats()
        
        return {
            "model_status": self.retraining_pipeline.model_status.value,
            "model_version": self.retraining_pipeline.current_model_version,
            "readiness": readiness,
            "label_stats": label_stats,
            "last_performance_check": self.performance_tracker.snapshots[-1].to_dict() 
                if self.performance_tracker.snapshots else None
        }
    
    def run_performance_evaluation(
        self,
        period_days: int = 30
    ) -> ModelPerformanceSnapshot:
        """Run performance evaluation for recent period."""
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        snapshot = self.performance_tracker.calculate_performance(
            self.label_store,
            period_start,
            period_end,
            self.retraining_pipeline.current_model_version
        )
        
        # Check for retraining triggers
        trigger = self.performance_tracker.check_retraining_triggers(snapshot)
        
        if trigger:
            logger.warning(f"Retraining trigger: {trigger.reason}")
        
        return snapshot
    
    def trigger_retraining(
        self,
        model_class: Any,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Manually trigger model retraining."""
        return self.retraining_pipeline.retrain_model(model_class, feature_columns)
    
    def get_improvement_summary(self) -> str:
        """Get human-readable improvement summary."""
        stats = self.label_store.get_stats()
        readiness = self.retraining_pipeline.check_readiness()
        
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONTINUOUS LEARNING STATUS                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Model Status: {self.retraining_pipeline.model_status.value.upper():<62} ║
║  Current Version: {self.retraining_pipeline.current_model_version:<59} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LABEL COLLECTION:                                                           ║
║  ├─ Total Labels: {stats['total_labels']:<5} / {self.config.min_labels_for_supervised:<5} required                               ║
║  ├─ Confirmed Leaks: {stats['confirmed_leaks']:<5} / {self.config.min_positive_labels:<5} required                            ║
║  └─ Progress: {readiness['progress_percent']:>5.1f}%                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  READY FOR SUPERVISED: {'YES ✓' if readiness['ready_for_supervised'] else 'NO - Need more labels':<55} ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    def check_drift_retraining(
        self,
        baseline_service: 'BaselineComparisonService',
        dma_id: str,
        metric_type: str = 'pressure'
    ) -> Optional[RetrainingTrigger]:
        """
        Check if baseline drift warrants retraining.
        
        This integrates with Component 4 (STL + Prophet Baseline).
        
        Args:
            baseline_service: The BaselineComparisonService instance
            dma_id: DMA to check drift for
            metric_type: Metric type to analyze
            
        Returns:
            RetrainingTrigger if drift warrants retraining, None otherwise
        """
        try:
            drift = baseline_service.calculate_drift(dma_id, metric_type)
            
            if drift is None:
                return None
            
            # Check if drift exceeds thresholds
            should_retrain = False
            reasons = []
            
            if drift.agreement_rate < self.config.drift_retrain_agreement_threshold:
                should_retrain = True
                reasons.append(
                    f"Agreement rate ({drift.agreement_rate:.0%}) below threshold "
                    f"({self.config.drift_retrain_agreement_threshold:.0%})"
                )
            
            if abs(drift.mean_prediction_delta) > self.config.drift_retrain_delta_threshold:
                should_retrain = True
                reasons.append(
                    f"Mean prediction delta ({drift.mean_prediction_delta:.1f}%) exceeds "
                    f"threshold ({self.config.drift_retrain_delta_threshold}%)"
                )
            
            if drift.retrain_recommended:
                should_retrain = True
                reasons.append(f"Drift service recommends retraining: {drift.retrain_reason}")
            
            if should_retrain:
                trigger = RetrainingTrigger(
                    trigger_id=f"DRIFT-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                    triggered_at=datetime.utcnow(),
                    reason="; ".join(reasons),
                    metric_name="baseline_drift",
                    current_value=drift.mean_prediction_delta,
                    threshold_value=self.config.drift_retrain_delta_threshold,
                    action="Retrain model due to baseline drift",
                    priority="high" if drift.drift_severity.value in ['high', 'critical'] else "medium"
                )
                
                # Update model status
                self.retraining_pipeline.model_status = ModelStatus.DRIFT_DETECTED
                
                logger.warning(f"Drift-triggered retraining for {dma_id}: {trigger.reason}")
                return trigger
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking drift retraining: {e}")
            return None
    
    def auto_check_all_dmas(
        self,
        baseline_service: 'BaselineComparisonService',
        dma_ids: List[str],
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Automatically check all DMAs for drift-triggered retraining.
        
        Args:
            baseline_service: The BaselineComparisonService instance
            dma_ids: List of DMA IDs to check
            metric_types: List of metric types to check (default: pressure, flow)
            
        Returns:
            Summary of drift checks and any triggered retraining
        """
        metric_types = metric_types or ['pressure', 'flow']
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'dmas_checked': len(dma_ids),
            'metrics_checked': metric_types,
            'triggers': [],
            'summary': {
                'total_checks': 0,
                'drift_detected': 0,
                'retrain_triggered': 0
            }
        }
        
        for dma_id in dma_ids:
            for metric_type in metric_types:
                results['summary']['total_checks'] += 1
                
                trigger = self.check_drift_retraining(
                    baseline_service, dma_id, metric_type
                )
                
                if trigger:
                    results['summary']['drift_detected'] += 1
                    results['triggers'].append({
                        'dma_id': dma_id,
                        'metric_type': metric_type,
                        'trigger_id': trigger.trigger_id,
                        'reason': trigger.reason,
                        'priority': trigger.priority
                    })
                    
                    if self.config.auto_retrain_on_drift:
                        results['summary']['retrain_triggered'] += 1
        
        return results


# =============================================================================
# FLASK API ENDPOINTS
# =============================================================================

def create_continuous_learning_api(controller: ContinuousLearningController):
    """
    Create Flask Blueprint for continuous learning API.
    
    Usage:
        from flask import Flask
        from continuous_learning import ContinuousLearningController, create_continuous_learning_api
        
        app = Flask(__name__)
        controller = ContinuousLearningController()
        app.register_blueprint(create_continuous_learning_api(controller), url_prefix='/api/v1/learning')
    """
    from flask import Blueprint, jsonify, request
    
    bp = Blueprint('continuous_learning', __name__)
    
    @bp.route('/feedback', methods=['POST'])
    def submit_feedback():
        """
        Submit field feedback for an alert.
        
        POST /api/v1/learning/feedback
        {
            "alert_id": "ALT-2026-001234",
            "dma_id": "DMA001",
            "feedback_type": "leak_confirmed",
            "feature_snapshot": {...},
            "ai_probability": 0.85,
            "leak_type": "joint_failure",
            "estimated_flow_m3_day": 45.5,
            "actual_location": {"lat": -15.4, "lon": 28.3},
            "investigator_id": "INV-001",
            "notes": "Leak found at service connection"
        }
        """
        data = request.get_json()
        
        try:
            feedback_type = FeedbackType(data['feedback_type'])
            
            feedback_id = controller.record_feedback(
                alert_id=data['alert_id'],
                dma_id=data['dma_id'],
                feedback_type=feedback_type,
                feature_snapshot=data.get('feature_snapshot'),
                ai_probability=data.get('ai_probability'),
                actual_location_lat=data.get('actual_location', {}).get('lat'),
                actual_location_lon=data.get('actual_location', {}).get('lon'),
                leak_type=data.get('leak_type'),
                leak_size=data.get('leak_size'),
                estimated_flow_m3_day=data.get('estimated_flow_m3_day'),
                investigator_id=data.get('investigator_id'),
                notes=data.get('notes')
            )
            
            return jsonify({
                'success': True,
                'feedback_id': feedback_id,
                'message': 'Feedback recorded successfully'
            })
            
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            return jsonify({'error': str(e)}), 400
    
    @bp.route('/feedback/<dma_id>', methods=['GET'])
    def get_dma_feedback(dma_id: str):
        """
        Get all feedback for a specific DMA.
        
        GET /api/v1/learning/feedback/DMA001?limit=50
        """
        limit = request.args.get('limit', 50, type=int)
        
        feedback = controller.label_store.get_by_dma(dma_id)
        feedback = sorted(feedback, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return jsonify({
            'dma_id': dma_id,
            'total_feedback': len(feedback),
            'feedback': [f.to_dict() for f in feedback]
        })
    
    @bp.route('/status', methods=['GET'])
    def get_status():
        """
        Get continuous learning system status.
        
        GET /api/v1/learning/status
        """
        return jsonify(controller.get_status())
    
    @bp.route('/performance', methods=['GET'])
    def get_performance():
        """
        Get model performance evaluation.
        
        GET /api/v1/learning/performance?days=30
        """
        days = request.args.get('days', 30, type=int)
        
        snapshot = controller.run_performance_evaluation(period_days=days)
        
        return jsonify(snapshot.to_dict())
    
    @bp.route('/performance/trend/<metric>', methods=['GET'])
    def get_performance_trend(metric: str):
        """
        Get performance trend for a specific metric.
        
        GET /api/v1/learning/performance/trend/precision?periods=12
        """
        periods = request.args.get('periods', 12, type=int)
        
        try:
            metric_enum = PerformanceMetric(metric)
            trend = controller.performance_tracker.get_performance_trend(metric_enum, periods)
            
            return jsonify({
                'metric': metric,
                'periods': periods,
                'trend': [
                    {'timestamp': t.isoformat(), 'value': v}
                    for t, v in trend
                ]
            })
            
        except ValueError:
            return jsonify({
                'error': f'Invalid metric: {metric}',
                'valid_metrics': [m.value for m in PerformanceMetric]
            }), 400
    
    @bp.route('/retrain', methods=['POST'])
    def trigger_retrain():
        """
        Manually trigger model retraining.
        
        POST /api/v1/learning/retrain
        {
            "feature_columns": ["pressure_mean", "mnf_deviation", "night_day_ratio"]
        }
        """
        data = request.get_json()
        
        feature_columns = data.get('feature_columns', [
            'pressure_mean', 'pressure_std', 'pressure_min', 'pressure_max',
            'flow_mean', 'mnf_value', 'mnf_deviation',
            'night_day_ratio', 'noise_level'
        ])
        
        # Use RandomForest as default model
        try:
            from sklearn.ensemble import RandomForestClassifier
            model_class = RandomForestClassifier
        except ImportError:
            return jsonify({
                'error': 'sklearn not available for retraining'
            }), 500
        
        result = controller.trigger_retraining(model_class, feature_columns)
        
        return jsonify(result)
    
    @bp.route('/readiness', methods=['GET'])
    def check_readiness():
        """
        Check readiness for supervised learning.
        
        GET /api/v1/learning/readiness
        """
        return jsonify(controller.retraining_pipeline.check_readiness())
    
    @bp.route('/labels/stats', methods=['GET'])
    def get_label_stats():
        """
        Get label collection statistics.
        
        GET /api/v1/learning/labels/stats
        """
        return jsonify(controller.label_store.get_stats())
    
    @bp.route('/models/history', methods=['GET'])
    def get_model_history():
        """
        Get model version history.
        
        GET /api/v1/learning/models/history
        """
        return jsonify(controller.retraining_pipeline.get_model_history())
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'model_status': controller.retraining_pipeline.model_status.value,
            'model_version': controller.retraining_pipeline.current_model_version,
            'total_labels': len(controller.label_store.get_all()),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return bp


# =============================================================================
# MAIN EXECUTION (Demo)
# =============================================================================

if __name__ == "__main__":
    # Initialize controller
    controller = ContinuousLearningController()
    
    # Simulate some feedback
    print("\n" + "="*80)
    print("SIMULATING FIELD FEEDBACK")
    print("="*80)
    
    # Simulate confirmed leaks
    for i in range(5):
        controller.record_feedback(
            alert_id=f"ALT-2026-{1000+i}",
            dma_id="DMA-LUS-001",
            feedback_type=FeedbackType.LEAK_CONFIRMED,
            feature_snapshot={
                "pressure_mean": 2.5 + np.random.randn() * 0.3,
                "mnf_deviation": -0.3 + np.random.randn() * 0.1,
                "night_day_ratio": 0.92 + np.random.randn() * 0.05
            },
            ai_probability=0.75 + np.random.randn() * 0.1,
            leak_type="joint_failure",
            estimated_flow_m3_day=50 + np.random.randn() * 20
        )
    
    # Simulate false positives
    for i in range(3):
        controller.record_feedback(
            alert_id=f"ALT-2026-{2000+i}",
            dma_id="DMA-LUS-002",
            feedback_type=FeedbackType.NO_LEAK_FOUND,
            feature_snapshot={
                "pressure_mean": 3.0 + np.random.randn() * 0.2,
                "mnf_deviation": -0.1 + np.random.randn() * 0.05,
                "night_day_ratio": 1.02 + np.random.randn() * 0.03
            },
            ai_probability=0.55 + np.random.randn() * 0.1
        )
    
    # Print status
    print(controller.get_improvement_summary())
    
    # Print detailed status
    status = controller.get_status()
    print("\nDetailed Status:")
    print(json.dumps(status, indent=2, default=str))
