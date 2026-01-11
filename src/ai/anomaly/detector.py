"""
AquaWatch NRW - Layer 1: Anomaly Detection
==========================================

Real-time anomaly detection using unsupervised learning.
Detects abnormal pressure behavior as the first filter.

Design Principles:
1. Fast inference (<100ms per sensor)
2. No labeled data required (unsupervised)
3. Adapts to local DMA behavior
4. Robust to noise and missing data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pickle
import json
import hashlib
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.neighbors import LocalOutlierFactor
import joblib


@dataclass
class AnomalyResult:
    """Result from anomaly detection."""
    sensor_id: str
    timestamp: datetime
    anomaly_score: float  # 0 = normal, 1 = highly anomalous
    is_anomaly: bool
    confidence: float
    contributing_features: List[Dict[str, Any]]
    model_version: str
    inference_time_ms: float


@dataclass
class ModelMetadata:
    """Metadata about a trained model."""
    model_id: str
    dma_id: str
    model_type: str
    version: str
    trained_at: datetime
    training_samples: int
    training_start: datetime
    training_end: datetime
    feature_names: List[str]
    performance_metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]


class IsolationForestDetector:
    """
    Anomaly detection using Isolation Forest algorithm.
    
    Why Isolation Forest:
    ---------------------
    1. Works without labeled data (we don't have many confirmed leak examples)
    2. Efficient for high-dimensional feature space
    3. Good at detecting point anomalies
    4. Fast inference (critical for real-time)
    5. Handles mixed feature types well
    
    Physical Interpretation:
    -----------------------
    Normal pressure behavior forms clusters in feature space.
    Leaks push observations away from these clusters.
    Isolation Forest detects how "isolated" a point is from normal behavior.
    """
    
    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        max_samples: str = 'auto',
        random_state: int = 42
    ):
        """
        Initialize detector.
        
        Args:
            contamination: Expected fraction of anomalies (default 5%)
            n_estimators: Number of trees in the forest
            max_samples: Samples to draw for each tree
            random_state: For reproducibility
        """
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=random_state,
            n_jobs=-1,
            warm_start=False
        )
        self.scaler = RobustScaler()  # Robust to outliers in training data
        self.feature_names: List[str] = []
        self.feature_stats: Dict[str, Dict[str, float]] = {}
        self.is_fitted = False
        self.metadata: Optional[ModelMetadata] = None
        
    def fit(
        self,
        X: np.ndarray,
        feature_names: List[str],
        dma_id: str = 'unknown'
    ) -> 'IsolationForestDetector':
        """
        Train the anomaly detector on historical normal data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Names of each feature
            dma_id: DMA identifier for model versioning
            
        Returns:
            self for method chaining
        """
        self.feature_names = feature_names
        
        # Store feature statistics for explainability
        for i, name in enumerate(feature_names):
            self.feature_stats[name] = {
                'mean': float(np.nanmean(X[:, i])),
                'std': float(np.nanstd(X[:, i])),
                'median': float(np.nanmedian(X[:, i])),
                'q1': float(np.nanpercentile(X[:, i], 25)),
                'q3': float(np.nanpercentile(X[:, i], 75))
            }
        
        # Handle missing values
        X_clean = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        
        # Fit isolation forest
        self.model.fit(X_scaled)
        
        self.is_fitted = True
        
        # Create metadata
        self.metadata = ModelMetadata(
            model_id=self._generate_model_id(dma_id),
            dma_id=dma_id,
            model_type='isolation_forest',
            version='1.0.0',
            trained_at=datetime.utcnow(),
            training_samples=len(X),
            training_start=datetime.utcnow() - timedelta(days=30),  # Placeholder
            training_end=datetime.utcnow(),
            feature_names=feature_names,
            performance_metrics={},
            hyperparameters={
                'contamination': self.contamination,
                'n_estimators': self.model.n_estimators
            }
        )
        
        return self
    
    def predict(self, X: np.ndarray, sensor_id: str = 'unknown') -> AnomalyResult:
        """
        Detect anomalies in new data.
        
        Args:
            X: Feature vector (1, n_features) or (n_features,)
            sensor_id: Sensor identifier
            
        Returns:
            AnomalyResult with score, classification, and explanation
        """
        import time
        start_time = time.time()
        
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        # Ensure 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Handle missing values
        X_clean = np.nan_to_num(X, nan=0.0)
        
        # Scale
        X_scaled = self.scaler.transform(X_clean)
        
        # Get raw anomaly score
        # decision_function returns: negative = anomaly, positive = normal
        raw_score = self.model.decision_function(X_scaled)[0]
        
        # Get prediction
        prediction = self.model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
        
        # Convert to 0-1 scale where 1 = anomaly
        # Raw scores typically range from -0.5 to 0.5
        # We normalize to 0-1 where higher = more anomalous
        anomaly_score = self._normalize_score(raw_score)
        
        # Determine if anomaly based on threshold
        is_anomaly = prediction == -1
        
        # Calculate confidence based on score magnitude
        confidence = self._calculate_confidence(raw_score)
        
        # Get contributing features
        contributing = self._explain_anomaly(X_clean[0], X_scaled[0])
        
        inference_time = (time.time() - start_time) * 1000
        
        return AnomalyResult(
            sensor_id=sensor_id,
            timestamp=datetime.utcnow(),
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            confidence=confidence,
            contributing_features=contributing,
            model_version=self.metadata.version if self.metadata else '0.0.0',
            inference_time_ms=inference_time
        )
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        Normalize raw decision function score to 0-1 range.
        
        Raw scores:
        - Highly positive: Very normal
        - Around 0: Boundary
        - Highly negative: Very anomalous
        """
        # Sigmoid-like transformation
        # Centers around contamination threshold
        normalized = 1 / (1 + np.exp(5 * raw_score))
        return float(np.clip(normalized, 0, 1))
    
    def _calculate_confidence(self, raw_score: float) -> float:
        """
        Calculate confidence in the prediction.
        
        High confidence when score is far from decision boundary.
        Low confidence when score is near boundary.
        """
        # Higher absolute score = higher confidence
        confidence = min(abs(raw_score) * 2, 1.0)
        return float(confidence)
    
    def _explain_anomaly(
        self,
        x_original: np.ndarray,
        x_scaled: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Identify features contributing most to anomaly score.
        
        Method:
        For each feature, compare current value to training distribution.
        Features far from normal range contribute more to anomaly.
        """
        contributions = []
        
        for i, name in enumerate(self.feature_names):
            stats = self.feature_stats.get(name, {})
            value = x_original[i]
            scaled_value = x_scaled[i]
            
            # Calculate deviation from normal
            mean = stats.get('mean', 0)
            std = stats.get('std', 1)
            
            if std > 0:
                zscore = (value - mean) / std
            else:
                zscore = 0
            
            # Contribution based on absolute deviation
            contribution = abs(scaled_value)
            
            # Determine direction
            if zscore < -1:
                direction = 'low'
                description = f"{name} is unusually low ({value:.3f}, z={zscore:.1f})"
            elif zscore > 1:
                direction = 'high'
                description = f"{name} is unusually high ({value:.3f}, z={zscore:.1f})"
            else:
                direction = 'normal'
                description = f"{name} is within normal range ({value:.3f})"
            
            contributions.append({
                'feature': name,
                'value': float(value),
                'zscore': float(zscore),
                'contribution': float(contribution),
                'direction': direction,
                'description': description
            })
        
        # Sort by contribution (highest first)
        contributions.sort(key=lambda x: x['contribution'], reverse=True)
        
        # Return top 5
        return contributions[:5]
    
    def _generate_model_id(self, dma_id: str) -> str:
        """Generate unique model ID."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        content = f"{dma_id}_{timestamp}_{self.contamination}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_stats': self.feature_stats,
            'contamination': self.contamination,
            'metadata': self.metadata
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> 'IsolationForestDetector':
        """Load model from disk."""
        model_data = joblib.load(path)
        
        detector = cls(contamination=model_data['contamination'])
        detector.model = model_data['model']
        detector.scaler = model_data['scaler']
        detector.feature_names = model_data['feature_names']
        detector.feature_stats = model_data['feature_stats']
        detector.metadata = model_data['metadata']
        detector.is_fitted = True
        
        return detector


class EnsembleAnomalyDetector:
    """
    Ensemble of multiple anomaly detection methods for robustness.
    
    Combines:
    1. Isolation Forest (global anomalies)
    2. Statistical thresholds (domain knowledge)
    3. Local Outlier Factor (local anomalies)
    
    Final score is weighted combination.
    """
    
    def __init__(
        self,
        contamination: float = 0.05,
        weights: Optional[Dict[str, float]] = None
    ):
        self.contamination = contamination
        self.weights = weights or {
            'isolation_forest': 0.5,
            'statistical': 0.3,
            'lof': 0.2
        }
        
        self.isolation_forest = IsolationForestDetector(contamination=contamination)
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=True
        )
        self.scaler = RobustScaler()
        
        self.feature_names: List[str] = []
        self.statistical_thresholds: Dict[str, Dict[str, float]] = {}
        self.is_fitted = False
        
    def fit(
        self,
        X: np.ndarray,
        feature_names: List[str],
        dma_id: str = 'unknown'
    ) -> 'EnsembleAnomalyDetector':
        """Train all ensemble components."""
        
        self.feature_names = feature_names
        
        # Handle missing values
        X_clean = np.nan_to_num(X, nan=0.0)
        X_scaled = self.scaler.fit_transform(X_clean)
        
        # Fit Isolation Forest
        self.isolation_forest.fit(X, feature_names, dma_id)
        
        # Fit LOF
        self.lof.fit(X_scaled)
        
        # Calculate statistical thresholds
        self._fit_statistical_thresholds(X, feature_names)
        
        self.is_fitted = True
        return self
    
    def _fit_statistical_thresholds(
        self,
        X: np.ndarray,
        feature_names: List[str]
    ) -> None:
        """Calculate statistical thresholds for each feature."""
        
        for i, name in enumerate(feature_names):
            values = X[:, i]
            values = values[~np.isnan(values)]
            
            if len(values) > 0:
                self.statistical_thresholds[name] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'q1': float(np.percentile(values, 25)),
                    'q3': float(np.percentile(values, 75)),
                    'lower': float(np.percentile(values, 2.5)),
                    'upper': float(np.percentile(values, 97.5))
                }
    
    def predict(self, X: np.ndarray, sensor_id: str = 'unknown') -> AnomalyResult:
        """
        Get ensemble anomaly prediction.
        
        Combines multiple methods for robust detection.
        """
        import time
        start_time = time.time()
        
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        # Ensure 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        X_clean = np.nan_to_num(X, nan=0.0)
        X_scaled = self.scaler.transform(X_clean)
        
        # Get scores from each method
        scores = {}
        
        # 1. Isolation Forest
        if_result = self.isolation_forest.predict(X_clean[0], sensor_id)
        scores['isolation_forest'] = if_result.anomaly_score
        
        # 2. Statistical thresholds
        scores['statistical'] = self._statistical_score(X_clean[0])
        
        # 3. Local Outlier Factor
        lof_score = self.lof.decision_function(X_scaled)[0]
        scores['lof'] = self._normalize_lof_score(lof_score)
        
        # Weighted combination
        ensemble_score = sum(
            self.weights[method] * score 
            for method, score in scores.items()
        )
        
        # Determine anomaly (threshold at contamination level)
        is_anomaly = ensemble_score > (1 - self.contamination)
        
        # Confidence based on agreement
        score_variance = np.var(list(scores.values()))
        confidence = 1 - min(score_variance * 4, 0.5)  # Lower variance = higher confidence
        
        inference_time = (time.time() - start_time) * 1000
        
        return AnomalyResult(
            sensor_id=sensor_id,
            timestamp=datetime.utcnow(),
            anomaly_score=float(ensemble_score),
            is_anomaly=is_anomaly,
            confidence=float(confidence),
            contributing_features=if_result.contributing_features,
            model_version='ensemble_1.0.0',
            inference_time_ms=inference_time
        )
    
    def _statistical_score(self, x: np.ndarray) -> float:
        """Calculate anomaly score based on statistical thresholds."""
        violations = 0
        total_features = len(self.feature_names)
        
        for i, name in enumerate(self.feature_names):
            if name not in self.statistical_thresholds:
                continue
                
            thresholds = self.statistical_thresholds[name]
            value = x[i]
            
            # Check if outside 95% confidence interval
            if value < thresholds['lower'] or value > thresholds['upper']:
                violations += 1
            # Partial credit for being outside IQR
            elif value < thresholds['q1'] or value > thresholds['q3']:
                violations += 0.5
        
        return violations / total_features if total_features > 0 else 0
    
    def _normalize_lof_score(self, raw_score: float) -> float:
        """Normalize LOF score to 0-1 range."""
        # LOF: negative = outlier, positive = inlier
        normalized = 1 / (1 + np.exp(2 * raw_score))
        return float(np.clip(normalized, 0, 1))


class AnomalyDetectorManager:
    """
    Manages anomaly detectors for multiple DMAs.
    
    Responsibilities:
    - Create/load models for each DMA
    - Handle model versioning
    - Coordinate training and deployment
    """
    
    def __init__(self, model_dir: str = './models/anomaly'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.detectors: Dict[str, IsolationForestDetector] = {}
        
    def get_detector(self, dma_id: str) -> Optional[IsolationForestDetector]:
        """Get detector for a DMA, loading from disk if needed."""
        
        if dma_id in self.detectors:
            return self.detectors[dma_id]
        
        # Try to load from disk
        model_path = self.model_dir / f"{dma_id}_latest.joblib"
        if model_path.exists():
            detector = IsolationForestDetector.load(str(model_path))
            self.detectors[dma_id] = detector
            return detector
        
        return None
    
    def train_detector(
        self,
        dma_id: str,
        X: np.ndarray,
        feature_names: List[str],
        contamination: float = 0.05
    ) -> IsolationForestDetector:
        """Train a new detector for a DMA."""
        
        detector = IsolationForestDetector(contamination=contamination)
        detector.fit(X, feature_names, dma_id)
        
        # Save model
        model_path = self.model_dir / f"{dma_id}_latest.joblib"
        detector.save(str(model_path))
        
        # Also save versioned copy
        version = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        versioned_path = self.model_dir / f"{dma_id}_{version}.joblib"
        detector.save(str(versioned_path))
        
        self.detectors[dma_id] = detector
        return detector
    
    def detect_anomaly(
        self,
        dma_id: str,
        sensor_id: str,
        features: np.ndarray
    ) -> Optional[AnomalyResult]:
        """Run anomaly detection for a sensor."""
        
        detector = self.get_detector(dma_id)
        if detector is None:
            return None
        
        return detector.predict(features, sensor_id)
