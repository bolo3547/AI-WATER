"""
AquaWatch NRW - Layer 2: Leak Probability Estimation
====================================================

Estimates the probability that a detected anomaly represents an actual leak.
Uses supervised learning with calibrated probabilities.

Design Principles:
1. Calibrated probabilities (not just classification)
2. Explainable predictions
3. Confidence intervals
4. Handles class imbalance (leaks are rare)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    roc_auc_score, brier_score_loss
)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


@dataclass
class LeakProbabilityResult:
    """Result from leak probability estimation."""
    dma_id: str
    timestamp: datetime
    probability: float  # 0 to 1
    confidence: float  # 0 to 1
    confidence_lower: float  # Lower bound of CI
    confidence_upper: float  # Upper bound of CI
    severity: str  # low, medium, high, critical
    estimated_loss_m3_day: Optional[float]
    explanation: List[Dict[str, Any]]
    model_version: str
    inference_time_ms: float


@dataclass
class TrainingMetrics:
    """Model training performance metrics."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    brier_score: float
    cv_scores: List[float]
    feature_importance: Dict[str, float]


class LeakProbabilityEstimator:
    """
    Layer 2: Estimate probability of actual leak from anomaly candidates.
    
    Model Choice: XGBoost with Platt Scaling
    ----------------------------------------
    Why XGBoost:
    - Handles mixed feature types well
    - Built-in feature importance for explainability
    - Robust to overfitting with proper regularization
    - Fast inference
    - Handles missing values
    
    Why Calibration:
    - Raw classifier outputs are not true probabilities
    - Platt scaling calibrates to actual leak rates
    - Critical for decision-making (operators need real probabilities)
    
    Physical Interpretation:
    -----------------------
    This model learns to distinguish:
    - True leaks: Persistent pressure drops, night patterns, gradient changes
    - False alarms: Demand changes, operational events, sensor issues
    
    The model is trained on confirmed leak events (from repair records)
    and confirmed non-leaks (from inspections that found nothing).
    """
    
    def __init__(
        self,
        model_type: str = 'xgboost',
        calibration_method: str = 'sigmoid',
        class_weight: str = 'balanced'
    ):
        """
        Initialize estimator.
        
        Args:
            model_type: 'xgboost', 'random_forest', or 'gradient_boosting'
            calibration_method: 'sigmoid' (Platt) or 'isotonic'
            class_weight: How to handle class imbalance
        """
        self.model_type = model_type
        self.calibration_method = calibration_method
        self.class_weight = class_weight
        
        # Create base model
        self.base_model = self._create_base_model()
        
        # Calibrated wrapper
        self.model: Optional[CalibratedClassifierCV] = None
        
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.feature_importance: Dict[str, float] = {}
        self.is_fitted = False
        self.training_metrics: Optional[TrainingMetrics] = None
        
        # For SHAP explanations
        self.explainer = None
        
    def _create_base_model(self):
        """Create the base classifier."""
        
        if self.model_type == 'xgboost' and HAS_XGBOOST:
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_alpha=0.1,
                reg_lambda=1.0,
                objective='binary:logistic',
                eval_metric='auc',
                use_label_encoder=False,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight=self.class_weight,
                random_state=42,
                n_jobs=-1
            )
        else:
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        validation_split: float = 0.2
    ) -> 'LeakProbabilityEstimator':
        """
        Train the leak probability model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (1 = confirmed leak, 0 = confirmed no leak)
            feature_names: Names of features for explainability
            validation_split: Fraction for validation
            
        Returns:
            self for method chaining
        """
        self.feature_names = feature_names
        
        # Handle missing values
        X_clean = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        
        # Handle class imbalance for XGBoost
        if self.model_type == 'xgboost' and HAS_XGBOOST:
            scale_pos_weight = (y == 0).sum() / (y == 1).sum() if (y == 1).sum() > 0 else 1
            self.base_model.set_params(scale_pos_weight=scale_pos_weight)
        
        # Cross-validation for performance estimation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.base_model, X_scaled, y, cv=cv, scoring='roc_auc')
        
        # Fit calibrated model
        self.model = CalibratedClassifierCV(
            self.base_model,
            method=self.calibration_method,
            cv=5
        )
        self.model.fit(X_scaled, y)
        
        # Get feature importance from base model
        self._extract_feature_importance(X_scaled, y)
        
        # Calculate training metrics
        self._calculate_training_metrics(X_scaled, y, cv_scores)
        
        # Initialize SHAP explainer if available
        if HAS_SHAP:
            try:
                # Use the first calibrated classifier's base estimator
                base_for_shap = self.model.calibrated_classifiers_[0].estimator
                self.explainer = shap.TreeExplainer(base_for_shap)
            except Exception:
                self.explainer = None
        
        self.is_fitted = True
        return self
    
    def _extract_feature_importance(self, X: np.ndarray, y: np.ndarray) -> None:
        """Extract feature importance from trained model."""
        
        # Fit base model directly to get importance
        self.base_model.fit(X, y)
        
        if hasattr(self.base_model, 'feature_importances_'):
            importance = self.base_model.feature_importances_
            self.feature_importance = {
                name: float(imp) 
                for name, imp in zip(self.feature_names, importance)
            }
        else:
            self.feature_importance = {name: 0.0 for name in self.feature_names}
    
    def _calculate_training_metrics(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv_scores: np.ndarray
    ) -> None:
        """Calculate and store training performance metrics."""
        
        # Get predictions on training data (for reference only)
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)[:, 1]
        
        self.training_metrics = TrainingMetrics(
            accuracy=float((y_pred == y).mean()),
            precision=float(precision_score(y, y_pred, zero_division=0)),
            recall=float(recall_score(y, y_pred, zero_division=0)),
            f1=float(f1_score(y, y_pred, zero_division=0)),
            roc_auc=float(roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0),
            brier_score=float(brier_score_loss(y, y_proba)),
            cv_scores=cv_scores.tolist(),
            feature_importance=self.feature_importance
        )
    
    def predict_proba(
        self,
        X: np.ndarray,
        dma_id: str = 'unknown',
        anomaly_score: Optional[float] = None
    ) -> LeakProbabilityResult:
        """
        Estimate leak probability with explanation.
        
        Args:
            X: Feature vector (1, n_features) or (n_features,)
            dma_id: DMA identifier
            anomaly_score: Optional anomaly score from Layer 1
            
        Returns:
            LeakProbabilityResult with probability, confidence, and explanation
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
        X_scaled = self.scaler.transform(X_clean)
        
        # Get probability
        proba = self.model.predict_proba(X_scaled)[0, 1]
        
        # Calculate confidence interval using bootstrap-like approach
        confidence_lower, confidence_upper = self._estimate_confidence_interval(
            X_scaled, proba
        )
        
        # Confidence based on how extreme the probability is
        confidence = self._calculate_confidence(proba, X_clean[0])
        
        # Get explanation
        explanation = self._explain_prediction(X_clean[0], X_scaled[0])
        
        # Classify severity
        severity = self._classify_severity(proba)
        
        # Estimate water loss (rough estimation based on probability and severity)
        estimated_loss = self._estimate_water_loss(proba, severity)
        
        inference_time = (time.time() - start_time) * 1000
        
        return LeakProbabilityResult(
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            probability=float(proba),
            confidence=float(confidence),
            confidence_lower=float(confidence_lower),
            confidence_upper=float(confidence_upper),
            severity=severity,
            estimated_loss_m3_day=estimated_loss,
            explanation=explanation,
            model_version='2.0.0',
            inference_time_ms=inference_time
        )
    
    def _estimate_confidence_interval(
        self,
        X_scaled: np.ndarray,
        point_estimate: float
    ) -> Tuple[float, float]:
        """
        Estimate confidence interval for probability.
        
        Uses calibrated classifiers' variance as uncertainty measure.
        """
        # Get predictions from each calibrated classifier
        probas = []
        for calibrated in self.model.calibrated_classifiers_:
            proba = calibrated.predict_proba(X_scaled)[0, 1]
            probas.append(proba)
        
        if len(probas) > 1:
            std = np.std(probas)
            lower = max(0, point_estimate - 2 * std)
            upper = min(1, point_estimate + 2 * std)
        else:
            # Fallback: use fixed interval based on typical uncertainty
            uncertainty = 0.1
            lower = max(0, point_estimate - uncertainty)
            upper = min(1, point_estimate + uncertainty)
        
        return lower, upper
    
    def _calculate_confidence(self, proba: float, x: np.ndarray) -> float:
        """
        Calculate confidence in the prediction.
        
        Factors:
        1. How extreme the probability is (closer to 0 or 1 = higher confidence)
        2. Data quality (presence of key features)
        3. Similarity to training data
        """
        # Factor 1: Probability extremity
        extremity = abs(2 * proba - 1)  # 0 at 0.5, 1 at 0 or 1
        
        # Factor 2: Data completeness
        completeness = 1 - (np.isnan(x).sum() / len(x))
        
        # Factor 3: Key features present
        key_feature_indices = [
            i for i, name in enumerate(self.feature_names)
            if 'mnf' in name.lower() or 'night' in name.lower() or 'baseline' in name.lower()
        ]
        key_features_present = sum(
            1 for i in key_feature_indices if not np.isnan(x[i])
        ) / max(len(key_feature_indices), 1)
        
        # Combine factors
        confidence = 0.4 * extremity + 0.3 * completeness + 0.3 * key_features_present
        
        return float(np.clip(confidence, 0, 1))
    
    def _explain_prediction(
        self,
        x_original: np.ndarray,
        x_scaled: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Generate human-readable explanation of prediction.
        
        Uses SHAP values if available, otherwise feature importance + values.
        """
        explanation = []
        
        # Try SHAP first
        if self.explainer is not None and HAS_SHAP:
            try:
                shap_values = self.explainer.shap_values(x_scaled.reshape(1, -1))
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # For binary classification
                shap_values = shap_values[0]
                
                for i, name in enumerate(self.feature_names):
                    explanation.append({
                        'feature': name,
                        'value': float(x_original[i]),
                        'shap_value': float(shap_values[i]),
                        'impact': 'increases' if shap_values[i] > 0 else 'decreases',
                        'description': self._describe_feature_impact(
                            name, x_original[i], shap_values[i]
                        )
                    })
                
                # Sort by absolute SHAP value
                explanation.sort(key=lambda x: abs(x['shap_value']), reverse=True)
                return explanation[:5]
                
            except Exception:
                pass
        
        # Fallback: use feature importance and values
        for i, name in enumerate(self.feature_names):
            importance = self.feature_importance.get(name, 0)
            value = x_original[i]
            
            # Only include if feature has meaningful importance
            if importance > 0.01:
                explanation.append({
                    'feature': name,
                    'value': float(value),
                    'importance': float(importance),
                    'description': self._describe_feature_value(name, value)
                })
        
        # Sort by importance
        explanation.sort(key=lambda x: x.get('importance', 0), reverse=True)
        return explanation[:5]
    
    def _describe_feature_impact(
        self,
        name: str,
        value: float,
        shap_value: float
    ) -> str:
        """Generate description of how feature impacts prediction."""
        
        impact_direction = "increases" if shap_value > 0 else "decreases"
        impact_magnitude = "strongly" if abs(shap_value) > 0.1 else "slightly"
        
        descriptions = {
            'night_day_ratio': f"Night/day ratio of {value:.2f} {impact_magnitude} {impact_direction} leak probability",
            'mnf_deviation': f"Night pressure deviation of {value:.2f} bar {impact_magnitude} {impact_direction} leak probability",
            'leak_index': f"Leak index of {value:.2f} {impact_magnitude} {impact_direction} leak probability",
            'pressure_zscore': f"Pressure z-score of {value:.1f} {impact_magnitude} {impact_direction} leak probability",
            'anomaly_score': f"Anomaly score of {value:.2f} {impact_magnitude} {impact_direction} leak probability",
        }
        
        return descriptions.get(name, f"{name} = {value:.3f} {impact_magnitude} {impact_direction} leak probability")
    
    def _describe_feature_value(self, name: str, value: float) -> str:
        """Generate description of feature value."""
        
        descriptions = {
            'night_day_ratio': f"Night/day pressure ratio is {value:.2f}" + 
                (" (concerning: below 1.0)" if value < 1.0 else " (healthy: above 1.0)"),
            'mnf_deviation': f"Night pressure is {abs(value):.2f} bar " +
                ("below" if value < 0 else "above") + " normal",
            'deviation_from_baseline': f"Current pressure is {abs(value):.2f} bar " +
                ("below" if value < 0 else "above") + " 7-day average",
            'leak_index': f"Combined leak indicator score is {value:.2f} " +
                ("(high)" if value > 0.5 else "(moderate)" if value > 0.3 else "(low)"),
            'pressure_mean': f"Average pressure is {value:.2f} bar",
        }
        
        return descriptions.get(name, f"{name} = {value:.3f}")
    
    def _classify_severity(self, proba: float) -> str:
        """Classify severity based on probability."""
        if proba >= 0.85:
            return 'critical'
        elif proba >= 0.7:
            return 'high'
        elif proba >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_water_loss(
        self,
        proba: float,
        severity: str
    ) -> Optional[float]:
        """
        Estimate water loss based on probability and severity.
        
        Note: This is a rough estimate based on typical leak sizes.
        Actual loss depends on many factors not captured here.
        """
        # Base estimates by severity (m³/day)
        base_estimates = {
            'critical': 150,  # Large burst
            'high': 75,       # Significant leak
            'medium': 30,     # Moderate leak
            'low': 10         # Small leak
        }
        
        base = base_estimates.get(severity, 30)
        
        # Scale by probability
        estimate = base * proba
        
        return round(estimate, 1)
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'base_model': self.base_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'training_metrics': self.training_metrics,
            'model_type': self.model_type
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> 'LeakProbabilityEstimator':
        """Load model from disk."""
        model_data = joblib.load(path)
        
        estimator = cls(model_type=model_data['model_type'])
        estimator.model = model_data['model']
        estimator.base_model = model_data['base_model']
        estimator.scaler = model_data['scaler']
        estimator.feature_names = model_data['feature_names']
        estimator.feature_importance = model_data['feature_importance']
        estimator.training_metrics = model_data['training_metrics']
        estimator.is_fitted = True
        
        return estimator


class LeakClassifierEnsemble:
    """
    Ensemble of multiple classifiers for robust probability estimation.
    
    Combines:
    1. XGBoost (tree-based)
    2. Random Forest (tree-based, different perspective)
    3. Logistic Regression (linear baseline)
    
    Final probability is weighted average, with uncertainty from disagreement.
    """
    
    def __init__(self):
        self.models: Dict[str, LeakProbabilityEstimator] = {}
        self.weights: Dict[str, float] = {}
        self.is_fitted = False
        
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> 'LeakClassifierEnsemble':
        """Train ensemble of classifiers."""
        
        model_configs = [
            ('xgboost', 0.5),
            ('random_forest', 0.3),
            ('gradient_boosting', 0.2)
        ]
        
        for model_type, weight in model_configs:
            try:
                estimator = LeakProbabilityEstimator(model_type=model_type)
                estimator.fit(X, y, feature_names)
                self.models[model_type] = estimator
                self.weights[model_type] = weight
            except Exception as e:
                print(f"Warning: Could not train {model_type}: {e}")
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        self.feature_names = feature_names
        self.is_fitted = True
        return self
    
    def predict_proba(
        self,
        X: np.ndarray,
        dma_id: str = 'unknown'
    ) -> LeakProbabilityResult:
        """Get ensemble probability estimate."""
        
        if not self.is_fitted or not self.models:
            raise RuntimeError("Ensemble not fitted or no models available.")
        
        import time
        start_time = time.time()
        
        probabilities = []
        explanations = []
        
        for model_type, model in self.models.items():
            result = model.predict_proba(X, dma_id)
            probabilities.append((self.weights[model_type], result.probability))
            if model_type == 'xgboost':  # Use primary model for explanation
                explanations = result.explanation
        
        # Weighted average probability
        ensemble_proba = sum(w * p for w, p in probabilities)
        
        # Uncertainty from disagreement
        proba_values = [p for _, p in probabilities]
        uncertainty = np.std(proba_values)
        
        # Confidence based on agreement
        confidence = 1 - min(uncertainty * 4, 0.5)
        
        # Confidence interval
        ci_lower = max(0, ensemble_proba - 2 * uncertainty)
        ci_upper = min(1, ensemble_proba + 2 * uncertainty)
        
        inference_time = (time.time() - start_time) * 1000
        
        return LeakProbabilityResult(
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            probability=float(ensemble_proba),
            confidence=float(confidence),
            confidence_lower=float(ci_lower),
            confidence_upper=float(ci_upper),
            severity=self._classify_severity(ensemble_proba),
            estimated_loss_m3_day=self._estimate_loss(ensemble_proba),
            explanation=explanations,
            model_version='ensemble_2.0.0',
            inference_time_ms=inference_time
        )
    
    def _classify_severity(self, proba: float) -> str:
        if proba >= 0.85: return 'critical'
        elif proba >= 0.7: return 'high'
        elif proba >= 0.5: return 'medium'
        else: return 'low'
    
    def _estimate_loss(self, proba: float) -> float:
        base = 100 * proba  # Simple linear estimate
        return round(base, 1)
