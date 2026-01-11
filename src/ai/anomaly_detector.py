"""
AquaWatch AI - Anomaly Detection Engine
=======================================
Real-time pressure anomaly detection using multiple ML techniques:
- Statistical methods (Z-score, IQR)
- Isolation Forest for multivariate anomalies
- LSTM Autoencoder for sequence anomalies
- Gradient Boosting for leak probability
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
import pickle
from collections import deque

# ML imports
try:
    from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class AnomalyType(Enum):
    """Types of detected anomalies."""
    NORMAL = "normal"
    PRESSURE_DROP = "pressure_drop"
    PRESSURE_SPIKE = "pressure_spike"
    FLOW_ANOMALY = "flow_anomaly"
    LEAK_SUSPECTED = "leak_suspected"
    BURST_SUSPECTED = "burst_suspected"
    SENSOR_FAULT = "sensor_fault"


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    pipe_id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    confidence: float  # 0-1
    severity: str  # low, medium, high, critical
    pressure: float
    flow: float
    expected_pressure: float
    deviation: float
    details: Dict


class PressureBaseline:
    """Learns and maintains pressure baselines for each pipe."""
    
    def __init__(self, window_size: int = 1440):  # 24 hours at 1-min intervals
        self.window_size = window_size
        self.baselines: Dict[str, deque] = {}
        self.hourly_patterns: Dict[str, Dict[int, List[float]]] = {}
        self.daily_stats: Dict[str, Dict] = {}
    
    def update(self, pipe_id: str, pressure: float, timestamp: datetime):
        """Update baseline with new reading."""
        if pipe_id not in self.baselines:
            self.baselines[pipe_id] = deque(maxlen=self.window_size)
            self.hourly_patterns[pipe_id] = {h: [] for h in range(24)}
        
        self.baselines[pipe_id].append(pressure)
        hour = timestamp.hour
        self.hourly_patterns[pipe_id][hour].append(pressure)
        
        # Keep only last 7 days of hourly patterns
        if len(self.hourly_patterns[pipe_id][hour]) > 7 * 60:
            self.hourly_patterns[pipe_id][hour] = self.hourly_patterns[pipe_id][hour][-7*60:]
        
        # Update daily stats
        if pipe_id not in self.daily_stats or len(self.baselines[pipe_id]) >= 100:
            values = list(self.baselines[pipe_id])
            self.daily_stats[pipe_id] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "q25": np.percentile(values, 25),
                "q75": np.percentile(values, 75),
            }
    
    def get_expected(self, pipe_id: str, timestamp: datetime) -> Tuple[float, float]:
        """Get expected pressure and standard deviation for time of day."""
        if pipe_id not in self.hourly_patterns:
            return 2.5, 0.5  # Default values
        
        hour = timestamp.hour
        hourly_values = self.hourly_patterns[pipe_id][hour]
        
        if len(hourly_values) < 10:
            # Not enough data, use overall baseline
            stats = self.daily_stats.get(pipe_id, {"mean": 2.5, "std": 0.5})
            return stats["mean"], stats["std"]
        
        return np.mean(hourly_values), np.std(hourly_values)
    
    def save(self, filepath: str):
        """Save baselines to file."""
        data = {
            "baselines": {k: list(v) for k, v in self.baselines.items()},
            "hourly_patterns": self.hourly_patterns,
            "daily_stats": self.daily_stats,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    def load(self, filepath: str):
        """Load baselines from file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.baselines = {k: deque(v, maxlen=self.window_size) for k, v in data.get("baselines", {}).items()}
            self.hourly_patterns = data.get("hourly_patterns", {})
            self.daily_stats = data.get("daily_stats", {})


class StatisticalDetector:
    """Statistical anomaly detection using Z-score and IQR methods."""
    
    def __init__(self, z_threshold: float = 3.0, iqr_multiplier: float = 1.5):
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
    
    def detect(self, value: float, mean: float, std: float, q25: float = None, q75: float = None) -> Tuple[bool, float]:
        """
        Detect if value is anomalous.
        Returns: (is_anomaly, anomaly_score)
        """
        # Z-score method
        if std > 0:
            z_score = abs(value - mean) / std
        else:
            z_score = 0
        
        z_anomaly = z_score > self.z_threshold
        
        # IQR method (if quartiles provided)
        iqr_anomaly = False
        if q25 is not None and q75 is not None:
            iqr = q75 - q25
            lower_bound = q25 - self.iqr_multiplier * iqr
            upper_bound = q75 + self.iqr_multiplier * iqr
            iqr_anomaly = value < lower_bound or value > upper_bound
        
        is_anomaly = z_anomaly or iqr_anomaly
        
        # Anomaly score (0-1)
        score = min(z_score / (self.z_threshold * 2), 1.0)
        
        return is_anomaly, score


class IsolationForestDetector:
    """Multivariate anomaly detection using Isolation Forest."""
    
    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model = None
        self.scaler = None
        self.is_fitted = False
    
    def fit(self, data: pd.DataFrame):
        """Train the Isolation Forest model."""
        if not SKLEARN_AVAILABLE:
            return
        
        features = ['pressure', 'flow', 'pressure_change', 'flow_change']
        available_features = [f for f in features if f in data.columns]
        
        if len(available_features) < 2:
            return
        
        X = data[available_features].dropna()
        
        if len(X) < 100:
            return
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        self.is_fitted = True
        self.features = available_features
    
    def predict(self, pressure: float, flow: float, pressure_change: float = 0, flow_change: float = 0) -> Tuple[bool, float]:
        """Predict if reading is anomalous."""
        if not self.is_fitted or not SKLEARN_AVAILABLE:
            return False, 0.0
        
        X = np.array([[pressure, flow, pressure_change, flow_change]])
        X_scaled = self.scaler.transform(X[:, :len(self.features)])
        
        prediction = self.model.predict(X_scaled)[0]
        score = -self.model.score_samples(X_scaled)[0]
        
        # Normalize score to 0-1
        score = min(max(score, 0), 1)
        
        return prediction == -1, score


class LeakProbabilityModel:
    """Gradient Boosting model to estimate leak probability."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_fitted = False
    
    def fit(self, data: pd.DataFrame, labels: np.ndarray):
        """Train the leak probability model."""
        if not SKLEARN_AVAILABLE:
            return
        
        features = [
            'pressure', 'flow', 'pressure_change', 'flow_change',
            'pressure_deviation', 'hour', 'day_of_week'
        ]
        available_features = [f for f in features if f in data.columns]
        
        X = data[available_features].dropna()
        y = labels[:len(X)]
        
        if len(X) < 50:
            return
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        self.features = available_features
    
    def predict_probability(self, features: Dict) -> float:
        """Predict leak probability (0-1)."""
        if not self.is_fitted or not SKLEARN_AVAILABLE:
            # Fallback heuristic
            pressure_drop = features.get('pressure_deviation', 0)
            if pressure_drop < -0.5:
                return min(abs(pressure_drop) / 2, 0.9)
            return 0.1
        
        X = np.array([[features.get(f, 0) for f in self.features]])
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict_proba(X_scaled)[0][1]


class LSTMAutoencoder:
    """LSTM Autoencoder for sequence anomaly detection."""
    
    def __init__(self, sequence_length: int = 60, latent_dim: int = 16):
        self.sequence_length = sequence_length
        self.latent_dim = latent_dim
        self.model = None
        self.scaler = None
        self.threshold = None
        self.is_fitted = False
    
    def build_model(self, n_features: int):
        """Build LSTM Autoencoder architecture."""
        if not TF_AVAILABLE:
            return None
        
        # Encoder
        inputs = keras.Input(shape=(self.sequence_length, n_features))
        encoded = keras.layers.LSTM(64, activation='relu', return_sequences=True)(inputs)
        encoded = keras.layers.LSTM(self.latent_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = keras.layers.RepeatVector(self.sequence_length)(encoded)
        decoded = keras.layers.LSTM(self.latent_dim, activation='relu', return_sequences=True)(decoded)
        decoded = keras.layers.LSTM(64, activation='relu', return_sequences=True)(decoded)
        outputs = keras.layers.TimeDistributed(keras.layers.Dense(n_features))(decoded)
        
        model = keras.Model(inputs, outputs)
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    def fit(self, sequences: np.ndarray, epochs: int = 50):
        """Train the autoencoder."""
        if not TF_AVAILABLE:
            return
        
        self.scaler = MinMaxScaler()
        n_samples, seq_len, n_features = sequences.shape
        
        # Reshape for scaling
        sequences_flat = sequences.reshape(-1, n_features)
        sequences_scaled = self.scaler.fit_transform(sequences_flat)
        sequences_scaled = sequences_scaled.reshape(n_samples, seq_len, n_features)
        
        self.model = self.build_model(n_features)
        
        self.model.fit(
            sequences_scaled, sequences_scaled,
            epochs=epochs,
            batch_size=32,
            validation_split=0.1,
            verbose=0
        )
        
        # Calculate threshold from training data
        reconstructions = self.model.predict(sequences_scaled, verbose=0)
        mse = np.mean(np.power(sequences_scaled - reconstructions, 2), axis=(1, 2))
        self.threshold = np.percentile(mse, 95)
        self.is_fitted = True
    
    def detect(self, sequence: np.ndarray) -> Tuple[bool, float]:
        """Detect anomaly in sequence."""
        if not self.is_fitted or not TF_AVAILABLE:
            return False, 0.0
        
        # Scale and reshape
        sequence_flat = sequence.reshape(-1, sequence.shape[-1])
        sequence_scaled = self.scaler.transform(sequence_flat)
        sequence_scaled = sequence_scaled.reshape(1, *sequence.shape)
        
        # Reconstruct
        reconstruction = self.model.predict(sequence_scaled, verbose=0)
        mse = np.mean(np.power(sequence_scaled - reconstruction, 2))
        
        # Anomaly score
        score = mse / self.threshold if self.threshold > 0 else 0
        is_anomaly = mse > self.threshold
        
        return is_anomaly, min(score, 1.0)


class AnomalyDetectionEngine:
    """
    Main anomaly detection engine combining multiple methods.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Initialize components
        self.baseline = PressureBaseline()
        self.statistical = StatisticalDetector(
            z_threshold=self.config.get('z_threshold', 3.0)
        )
        self.isolation_forest = IsolationForestDetector(
            contamination=self.config.get('contamination', 0.05)
        )
        self.leak_model = LeakProbabilityModel()
        self.lstm = LSTMAutoencoder()
        
        # Reading history for each pipe
        self.history: Dict[str, deque] = {}
        self.history_size = 60  # Keep last 60 readings
        
        # Previous readings for change calculation
        self.previous: Dict[str, Dict] = {}
        
        # Alert cooldown to prevent spam
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_minutes = 5
    
    def process_reading(self, pipe_id: str, pressure: float, flow: float, 
                       timestamp: datetime = None) -> AnomalyResult:
        """
        Process a sensor reading and detect anomalies.
        
        Args:
            pipe_id: Identifier for the pipe
            pressure: Pressure reading in bar
            flow: Flow reading in L/min
            timestamp: Reading timestamp (defaults to now)
        
        Returns:
            AnomalyResult with detection details
        """
        timestamp = timestamp or datetime.now()
        
        # Update baseline
        self.baseline.update(pipe_id, pressure, timestamp)
        
        # Get expected values
        expected_pressure, expected_std = self.baseline.get_expected(pipe_id, timestamp)
        deviation = pressure - expected_pressure
        
        # Calculate changes from previous reading
        prev = self.previous.get(pipe_id, {'pressure': pressure, 'flow': flow})
        pressure_change = pressure - prev['pressure']
        flow_change = flow - prev['flow']
        self.previous[pipe_id] = {'pressure': pressure, 'flow': flow, 'timestamp': timestamp}
        
        # Update history
        if pipe_id not in self.history:
            self.history[pipe_id] = deque(maxlen=self.history_size)
        self.history[pipe_id].append({
            'pressure': pressure,
            'flow': flow,
            'timestamp': timestamp
        })
        
        # Get baseline stats
        stats = self.baseline.daily_stats.get(pipe_id, {
            'mean': expected_pressure,
            'std': expected_std,
            'q25': expected_pressure - expected_std,
            'q75': expected_pressure + expected_std
        })
        
        # === Run Detection Methods ===
        
        # 1. Statistical detection
        stat_anomaly, stat_score = self.statistical.detect(
            pressure, stats['mean'], stats['std'], stats.get('q25'), stats.get('q75')
        )
        
        # 2. Isolation Forest detection
        iso_anomaly, iso_score = self.isolation_forest.predict(
            pressure, flow, pressure_change, flow_change
        )
        
        # 3. Leak probability
        leak_features = {
            'pressure': pressure,
            'flow': flow,
            'pressure_change': pressure_change,
            'flow_change': flow_change,
            'pressure_deviation': deviation,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday()
        }
        leak_probability = self.leak_model.predict_probability(leak_features)
        
        # === Determine Anomaly Type ===
        anomaly_type = AnomalyType.NORMAL
        confidence = 0.0
        
        # Check for sensor fault (readings out of physical range)
        if pressure < 0 or pressure > 20 or flow < 0 or flow > 1000:
            anomaly_type = AnomalyType.SENSOR_FAULT
            confidence = 0.95
        
        # Check for burst (sudden large pressure drop with high flow)
        elif pressure_change < -1.0 and flow_change > 50:
            anomaly_type = AnomalyType.BURST_SUSPECTED
            confidence = min(abs(pressure_change) / 2, 0.95)
        
        # Check for leak (gradual pressure drop)
        elif deviation < -0.3 and leak_probability > 0.5:
            anomaly_type = AnomalyType.LEAK_SUSPECTED
            confidence = leak_probability
        
        # Check for pressure drop
        elif stat_anomaly and deviation < 0:
            anomaly_type = AnomalyType.PRESSURE_DROP
            confidence = stat_score
        
        # Check for pressure spike
        elif stat_anomaly and deviation > 0:
            anomaly_type = AnomalyType.PRESSURE_SPIKE
            confidence = stat_score
        
        # Check for flow anomaly
        elif iso_anomaly and abs(flow_change) > 20:
            anomaly_type = AnomalyType.FLOW_ANOMALY
            confidence = iso_score
        
        # Combined anomaly score
        combined_score = max(stat_score, iso_score, leak_probability)
        if anomaly_type == AnomalyType.NORMAL:
            confidence = 1 - combined_score  # Confidence it's normal
        
        # Determine severity
        severity = self._calculate_severity(anomaly_type, confidence, deviation)
        
        return AnomalyResult(
            pipe_id=pipe_id,
            timestamp=timestamp,
            anomaly_type=anomaly_type,
            confidence=confidence,
            severity=severity,
            pressure=pressure,
            flow=flow,
            expected_pressure=expected_pressure,
            deviation=deviation,
            details={
                'statistical_score': stat_score,
                'isolation_score': iso_score,
                'leak_probability': leak_probability,
                'pressure_change': pressure_change,
                'flow_change': flow_change,
                'baseline_mean': stats['mean'],
                'baseline_std': stats['std']
            }
        )
    
    def _calculate_severity(self, anomaly_type: AnomalyType, confidence: float, 
                           deviation: float) -> str:
        """Calculate severity level."""
        if anomaly_type == AnomalyType.NORMAL:
            return "none"
        
        if anomaly_type == AnomalyType.BURST_SUSPECTED:
            return "critical"
        
        if anomaly_type == AnomalyType.SENSOR_FAULT:
            return "medium"
        
        # Based on confidence and deviation
        if confidence > 0.8 or abs(deviation) > 1.0:
            return "high"
        elif confidence > 0.6 or abs(deviation) > 0.5:
            return "medium"
        else:
            return "low"
    
    def should_alert(self, pipe_id: str, anomaly_type: AnomalyType) -> bool:
        """Check if we should send an alert (respecting cooldown)."""
        if anomaly_type == AnomalyType.NORMAL:
            return False
        
        key = f"{pipe_id}_{anomaly_type.value}"
        now = datetime.now()
        
        if key in self.alert_cooldown:
            last_alert = self.alert_cooldown[key]
            if (now - last_alert).total_seconds() < self.cooldown_minutes * 60:
                return False
        
        self.alert_cooldown[key] = now
        return True
    
    def train_models(self, historical_data: pd.DataFrame):
        """Train ML models on historical data."""
        print("Training Isolation Forest...")
        self.isolation_forest.fit(historical_data)
        
        # For leak model, we need labels (simulated here)
        if 'is_leak' in historical_data.columns:
            print("Training Leak Probability Model...")
            self.leak_model.fit(historical_data, historical_data['is_leak'].values)
        
        print("Models trained successfully!")
    
    def save_models(self, directory: str):
        """Save trained models to directory."""
        os.makedirs(directory, exist_ok=True)
        
        # Save baseline
        self.baseline.save(os.path.join(directory, 'baseline.json'))
        
        # Save sklearn models
        if SKLEARN_AVAILABLE and self.isolation_forest.is_fitted:
            with open(os.path.join(directory, 'isolation_forest.pkl'), 'wb') as f:
                pickle.dump({
                    'model': self.isolation_forest.model,
                    'scaler': self.isolation_forest.scaler,
                    'features': self.isolation_forest.features
                }, f)
        
        if SKLEARN_AVAILABLE and self.leak_model.is_fitted:
            with open(os.path.join(directory, 'leak_model.pkl'), 'wb') as f:
                pickle.dump({
                    'model': self.leak_model.model,
                    'scaler': self.leak_model.scaler,
                    'features': self.leak_model.features
                }, f)
    
    def load_models(self, directory: str):
        """Load trained models from directory."""
        # Load baseline
        baseline_path = os.path.join(directory, 'baseline.json')
        if os.path.exists(baseline_path):
            self.baseline.load(baseline_path)
        
        # Load sklearn models
        iso_path = os.path.join(directory, 'isolation_forest.pkl')
        if SKLEARN_AVAILABLE and os.path.exists(iso_path):
            with open(iso_path, 'rb') as f:
                data = pickle.load(f)
                self.isolation_forest.model = data['model']
                self.isolation_forest.scaler = data['scaler']
                self.isolation_forest.features = data['features']
                self.isolation_forest.is_fitted = True
        
        leak_path = os.path.join(directory, 'leak_model.pkl')
        if SKLEARN_AVAILABLE and os.path.exists(leak_path):
            with open(leak_path, 'rb') as f:
                data = pickle.load(f)
                self.leak_model.model = data['model']
                self.leak_model.scaler = data['scaler']
                self.leak_model.features = data['features']
                self.leak_model.is_fitted = True


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Create engine
    engine = AnomalyDetectionEngine({
        'z_threshold': 2.5,
        'contamination': 0.05
    })
    
    # Simulate some readings
    import random
    
    print("\n🔍 AquaWatch Anomaly Detection Engine")
    print("=" * 50)
    
    # Normal readings
    print("\n📊 Processing normal readings...")
    for i in range(100):
        pressure = 2.5 + random.gauss(0, 0.1)
        flow = 50 + random.gauss(0, 5)
        result = engine.process_reading("Pipe_A1", pressure, flow)
    
    print(f"   Baseline established: mean={engine.baseline.daily_stats['Pipe_A1']['mean']:.2f} bar")
    
    # Simulate a leak (pressure drop)
    print("\n🚨 Simulating leak condition...")
    leak_pressure = 1.8  # Significant drop
    leak_flow = 65  # Increased flow
    result = engine.process_reading("Pipe_A1", leak_pressure, leak_flow)
    
    print(f"   Anomaly Type: {result.anomaly_type.value}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Severity: {result.severity}")
    print(f"   Deviation: {result.deviation:.2f} bar")
    print(f"   Leak Probability: {result.details['leak_probability']:.2%}")
    
    # Simulate a burst
    print("\n💥 Simulating burst condition...")
    burst_pressure = 0.5  # Severe drop
    burst_flow = 150  # Very high flow
    result = engine.process_reading("Pipe_A1", burst_pressure, burst_flow)
    
    print(f"   Anomaly Type: {result.anomaly_type.value}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Severity: {result.severity}")
    
    print("\n✅ Anomaly Detection Engine ready!")
