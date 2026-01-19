"""
AquaWatch NRW - Time Series Forecasting
=======================================

Implements time series prediction for flow and pressure:
1. Prophet (baseline, interpretable)
2. LSTM (deep learning, sequence patterns)
3. STL Decomposition + Z-score (statistical anomaly detection)

Purpose:
- Predict expected flow/pressure for anomaly detection
- Forecast NRW trends
- Seasonal pattern analysis

All models output predictions that feed into the anomaly detector.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Check available libraries
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not installed. Run: pip install prophet")

try:
    from statsmodels.tsa.seasonal import STL
    from statsmodels.tsa.stattools import adfuller
    STL_AVAILABLE = True
except ImportError:
    STL_AVAILABLE = False
    logger.warning("statsmodels not installed. Run: pip install statsmodels")

try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ForecastResult:
    """Result from time series forecast."""
    sensor_id: str
    model_name: str
    timestamp: datetime
    
    # Forecast values
    predicted_value: float
    lower_bound: float          # 95% CI lower
    upper_bound: float          # 95% CI upper
    
    # Anomaly detection
    actual_value: Optional[float] = None
    residual: Optional[float] = None
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    
    # Decomposition (if available)
    trend: Optional[float] = None
    seasonal: Optional[float] = None
    residual_component: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "model": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "prediction": {
                "value": round(self.predicted_value, 4),
                "lower_95": round(self.lower_bound, 4),
                "upper_95": round(self.upper_bound, 4)
            },
            "anomaly": {
                "is_anomaly": self.is_anomaly,
                "score": round(self.anomaly_score, 3),
                "residual": round(self.residual, 4) if self.residual else None
            },
            "decomposition": {
                "trend": round(self.trend, 4) if self.trend else None,
                "seasonal": round(self.seasonal, 4) if self.seasonal else None,
                "residual": round(self.residual_component, 4) if self.residual_component else None
            } if self.trend else None
        }


@dataclass
class STLAnomalyResult:
    """Result from STL-based anomaly detection."""
    timestamp: datetime
    original_value: float
    trend: float
    seasonal: float
    residual: float
    
    # Anomaly detection
    residual_zscore: float
    is_anomaly: bool
    anomaly_type: str  # "high", "low", "none"
    
    # Context
    residual_mean: float
    residual_std: float


# =============================================================================
# STL DECOMPOSITION + Z-SCORE ANOMALY DETECTION
# =============================================================================

class STLAnomalyDetector:
    """
    Seasonal-Trend decomposition using Loess (STL) for anomaly detection.
    
    Physical Basis:
    ---------------
    Water network flow/pressure has strong patterns:
    - Daily cycle (demand patterns)
    - Weekly cycle (weekday vs weekend)
    - Seasonal (summer vs winter)
    
    STL decomposes time series into:
    - Trend: Long-term direction
    - Seasonal: Repeating patterns
    - Residual: What's left (including anomalies!)
    
    Large residuals indicate anomalies.
    
    Why STL:
    - No training data required (unsupervised)
    - Physically interpretable
    - Handles missing data
    - Fast computation
    """
    
    def __init__(
        self,
        period: int = 96,              # Samples per day (15-min intervals = 96)
        seasonal: int = 7,              # Seasonal smoother (odd number)
        zscore_threshold: float = 3.0   # Anomaly threshold
    ):
        self.period = period
        self.seasonal = seasonal
        self.zscore_threshold = zscore_threshold
        
        if not STL_AVAILABLE:
            raise ImportError("statsmodels required. Run: pip install statsmodels")
    
    def fit_transform(
        self,
        data: pd.DataFrame,
        value_column: str = 'value'
    ) -> Tuple[pd.DataFrame, List[STLAnomalyResult]]:
        """
        Decompose time series and detect anomalies.
        
        Args:
            data: DataFrame with datetime index and value column
            value_column: Name of column containing values
            
        Returns:
            (decomposition_df, list of anomaly results)
        """
        if len(data) < self.period * 2:
            logger.warning(f"Insufficient data for STL: need {self.period * 2}, got {len(data)}")
            return data, []
        
        # Prepare series
        if isinstance(data.index, pd.DatetimeIndex):
            series = data[value_column]
        else:
            data = data.copy()
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.set_index('timestamp')
            series = data[value_column]
        
        # Handle missing values
        series = series.interpolate(method='linear', limit=4)
        series = series.ffill().bfill()
        
        # Run STL decomposition
        stl = STL(series, period=self.period, seasonal=self.seasonal, robust=True)
        result = stl.fit()
        
        # Create decomposition DataFrame
        decomp_df = pd.DataFrame({
            'original': series,
            'trend': result.trend,
            'seasonal': result.seasonal,
            'residual': result.resid
        })
        
        # Calculate residual statistics
        residual_mean = result.resid.mean()
        residual_std = result.resid.std()
        
        # Detect anomalies using Z-score on residuals
        anomalies = []
        decomp_df['residual_zscore'] = (result.resid - residual_mean) / residual_std
        decomp_df['is_anomaly'] = abs(decomp_df['residual_zscore']) > self.zscore_threshold
        
        for idx, row in decomp_df.iterrows():
            if row['is_anomaly']:
                anomaly_type = "high" if row['residual_zscore'] > 0 else "low"
                
                anomalies.append(STLAnomalyResult(
                    timestamp=idx,
                    original_value=row['original'],
                    trend=row['trend'],
                    seasonal=row['seasonal'],
                    residual=row['residual'],
                    residual_zscore=row['residual_zscore'],
                    is_anomaly=True,
                    anomaly_type=anomaly_type,
                    residual_mean=residual_mean,
                    residual_std=residual_std
                ))
        
        logger.info(f"STL decomposition complete: {len(anomalies)} anomalies detected")
        
        return decomp_df, anomalies
    
    def predict_next(
        self,
        decomp_df: pd.DataFrame,
        steps: int = 96  # Predict next 24 hours
    ) -> pd.DataFrame:
        """
        Simple prediction using trend extrapolation + seasonal pattern.
        
        Note: For production, use Prophet or LSTM for better forecasts.
        """
        # Get recent trend slope
        recent_trend = decomp_df['trend'].tail(self.period)
        trend_slope = (recent_trend.iloc[-1] - recent_trend.iloc[0]) / len(recent_trend)
        
        # Get seasonal pattern (last complete cycle)
        seasonal_pattern = decomp_df['seasonal'].tail(self.period).values
        
        # Extend seasonal pattern for prediction period
        n_cycles = (steps // self.period) + 1
        extended_seasonal = np.tile(seasonal_pattern, n_cycles)[:steps]
        
        # Create predictions
        last_trend = decomp_df['trend'].iloc[-1]
        predictions = []
        
        last_timestamp = decomp_df.index[-1]
        
        for i in range(steps):
            predicted_trend = last_trend + trend_slope * (i + 1)
            predicted_seasonal = extended_seasonal[i]
            predicted_value = predicted_trend + predicted_seasonal
            
            new_timestamp = last_timestamp + timedelta(minutes=15 * (i + 1))
            
            predictions.append({
                'timestamp': new_timestamp,
                'predicted': predicted_value,
                'trend': predicted_trend,
                'seasonal': predicted_seasonal
            })
        
        return pd.DataFrame(predictions).set_index('timestamp')


# =============================================================================
# PROPHET FORECASTER
# =============================================================================

class ProphetForecaster:
    """
    Facebook Prophet for time series forecasting.
    
    Why Prophet:
    - Handles seasonality automatically
    - Robust to missing data
    - Interpretable components
    - Good baseline model
    
    Physical Interpretation:
    - Daily seasonality = demand patterns
    - Weekly seasonality = weekday/weekend differences
    - Trend = long-term changes (network growth/deterioration)
    - Holidays = special events (meter reading days, etc.)
    """
    
    def __init__(
        self,
        daily_seasonality: bool = True,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = False,  # Need >1 year data
        changepoint_prior_scale: float = 0.05,  # Lower = smoother trend
        interval_width: float = 0.95
    ):
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet required. Run: pip install prophet")
        
        self.daily_seasonality = daily_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.yearly_seasonality = yearly_seasonality
        self.changepoint_prior_scale = changepoint_prior_scale
        self.interval_width = interval_width
        
        self.model = None
        self.is_fitted = False
    
    def fit(self, data: pd.DataFrame, value_column: str = 'value') -> 'ProphetForecaster':
        """
        Fit Prophet model.
        
        Args:
            data: DataFrame with 'timestamp' or datetime index
            value_column: Column containing values to forecast
        """
        # Prepare data in Prophet format (ds, y)
        if isinstance(data.index, pd.DatetimeIndex):
            df = pd.DataFrame({
                'ds': data.index,
                'y': data[value_column].values
            })
        else:
            df = pd.DataFrame({
                'ds': pd.to_datetime(data['timestamp']),
                'y': data[value_column].values
            })
        
        # Remove rows with missing values
        df = df.dropna()
        
        if len(df) < 100:
            logger.warning(f"Low data for Prophet: {len(df)} rows")
        
        # Initialize model
        self.model = Prophet(
            daily_seasonality=self.daily_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            yearly_seasonality=self.yearly_seasonality,
            changepoint_prior_scale=self.changepoint_prior_scale,
            interval_width=self.interval_width
        )
        
        # Fit
        self.model.fit(df)
        self.is_fitted = True
        
        logger.info(f"Prophet model fitted on {len(df)} samples")
        
        return self
    
    def predict(
        self,
        periods: int = 96,  # 24 hours at 15-min intervals
        include_history: bool = False
    ) -> pd.DataFrame:
        """
        Generate forecasts.
        
        Args:
            periods: Number of periods to forecast
            include_history: Include historical predictions
            
        Returns:
            DataFrame with predictions and confidence intervals
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(
            periods=periods,
            freq='15min',
            include_history=include_history
        )
        
        # Predict
        forecast = self.model.predict(future)
        
        # Select relevant columns
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend', 
                          'additive_terms', 'daily', 'weekly']].copy()
        result.columns = ['timestamp', 'predicted', 'lower_95', 'upper_95', 
                         'trend', 'seasonality', 'daily_seasonal', 'weekly_seasonal']
        
        return result
    
    def detect_anomalies(
        self,
        actual_data: pd.DataFrame,
        value_column: str = 'value',
        threshold_sigma: float = 2.0
    ) -> List[ForecastResult]:
        """
        Detect anomalies by comparing actual vs predicted.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Prepare data
        if isinstance(actual_data.index, pd.DatetimeIndex):
            df = pd.DataFrame({
                'ds': actual_data.index,
                'y': actual_data[value_column].values
            })
        else:
            df = pd.DataFrame({
                'ds': pd.to_datetime(actual_data['timestamp']),
                'y': actual_data[value_column].values
            })
        
        # Get predictions for same period
        predictions = self.model.predict(df[['ds']])
        
        # Merge actual and predicted
        merged = df.merge(
            predictions[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']],
            on='ds'
        )
        
        # Calculate residuals and anomaly scores
        merged['residual'] = merged['y'] - merged['yhat']
        residual_std = merged['residual'].std()
        merged['anomaly_score'] = abs(merged['residual']) / residual_std
        merged['is_anomaly'] = merged['anomaly_score'] > threshold_sigma
        
        # Create results
        results = []
        for _, row in merged.iterrows():
            results.append(ForecastResult(
                sensor_id="unknown",
                model_name="prophet",
                timestamp=row['ds'],
                predicted_value=row['yhat'],
                lower_bound=row['yhat_lower'],
                upper_bound=row['yhat_upper'],
                actual_value=row['y'],
                residual=row['residual'],
                is_anomaly=row['is_anomaly'],
                anomaly_score=row['anomaly_score'],
                trend=row['trend']
            ))
        
        anomaly_count = len([r for r in results if r.is_anomaly])
        logger.info(f"Prophet anomaly detection: {anomaly_count} anomalies found")
        
        return results
    
    def get_components(self) -> Dict[str, Any]:
        """Get model components for interpretation."""
        if not self.is_fitted:
            return {}
        
        return {
            "trend_changepoints": self.model.changepoints.tolist() if hasattr(self.model, 'changepoints') else [],
            "seasonality_mode": "additive",
            "daily_seasonality": self.daily_seasonality,
            "weekly_seasonality": self.weekly_seasonality
        }


# =============================================================================
# LSTM SEQUENCE FORECASTER
# =============================================================================

class LSTMForecaster:
    """
    LSTM neural network for time series forecasting.
    
    Why LSTM:
    - Captures complex temporal dependencies
    - Can learn non-linear patterns
    - Good for multi-step forecasting
    
    Architecture:
    - Input: Sequence of past values (lookback window)
    - LSTM layers: Learn temporal patterns
    - Dense output: Predict future values
    
    Physical Interpretation:
    - Learns pressure/flow dynamics automatically
    - Captures dependencies that rule-based systems miss
    """
    
    def __init__(
        self,
        lookback: int = 96,           # 24 hours of history
        forecast_horizon: int = 12,    # 3 hours ahead
        lstm_units: int = 64,
        dropout: float = 0.2
    ):
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required. Run: pip install tensorflow")
        
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        self.lstm_units = lstm_units
        self.dropout = dropout
        
        self.model = None
        self.scaler = None
        self.is_fitted = False
    
    def _build_model(self, n_features: int = 1):
        """Build LSTM model architecture."""
        model = keras.Sequential([
            keras.layers.LSTM(
                self.lstm_units,
                activation='relu',
                return_sequences=True,
                input_shape=(self.lookback, n_features)
            ),
            keras.layers.Dropout(self.dropout),
            keras.layers.LSTM(self.lstm_units // 2, activation='relu'),
            keras.layers.Dropout(self.dropout),
            keras.layers.Dense(self.forecast_horizon)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        return model
    
    def _create_sequences(
        self,
        data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create input/output sequences for training."""
        X, y = [], []
        
        for i in range(len(data) - self.lookback - self.forecast_horizon + 1):
            X.append(data[i:i + self.lookback])
            y.append(data[i + self.lookback:i + self.lookback + self.forecast_horizon])
        
        return np.array(X), np.array(y)
    
    def fit(
        self,
        data: pd.DataFrame,
        value_column: str = 'value',
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> 'LSTMForecaster':
        """
        Train LSTM model.
        """
        from sklearn.preprocessing import MinMaxScaler
        
        # Extract values
        if isinstance(data.index, pd.DatetimeIndex):
            values = data[value_column].values
        else:
            values = data[value_column].values
        
        values = values.reshape(-1, 1)
        
        # Scale data
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(values)
        
        # Create sequences
        X, y = self._create_sequences(scaled_data.flatten())
        
        if len(X) < 100:
            logger.warning(f"Low data for LSTM: {len(X)} sequences")
        
        # Reshape for LSTM [samples, timesteps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Build and train model
        self.model = self._build_model(n_features=1)
        
        self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        self.is_fitted = True
        logger.info(f"LSTM model fitted on {len(X)} sequences")
        
        return self
    
    def predict(
        self,
        recent_data: np.ndarray
    ) -> np.ndarray:
        """
        Predict future values.
        
        Args:
            recent_data: Last `lookback` values
            
        Returns:
            Array of `forecast_horizon` predicted values
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Scale input
        scaled = self.scaler.transform(recent_data.reshape(-1, 1)).flatten()
        
        # Ensure correct length
        if len(scaled) < self.lookback:
            # Pad with first value
            scaled = np.pad(scaled, (self.lookback - len(scaled), 0), mode='edge')
        elif len(scaled) > self.lookback:
            scaled = scaled[-self.lookback:]
        
        # Reshape for prediction
        X = scaled.reshape((1, self.lookback, 1))
        
        # Predict
        scaled_pred = self.model.predict(X, verbose=0)[0]
        
        # Inverse scale
        predictions = self.scaler.inverse_transform(scaled_pred.reshape(-1, 1)).flatten()
        
        return predictions


# =============================================================================
# ENSEMBLE FORECASTER
# =============================================================================

class EnsembleForecaster:
    """
    Ensemble of multiple forecasters for robust predictions.
    
    Combines:
    - STL (statistical, interpretable)
    - Prophet (seasonal patterns, robust)
    - LSTM (complex patterns, neural)
    
    Ensemble Strategy:
    - Weight by recent performance
    - Use median for robustness
    - Track individual model accuracy
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.weights: Dict[str, float] = {
            'stl': 0.3,
            'prophet': 0.4,
            'lstm': 0.3
        }
        self.performance: Dict[str, List[float]] = {
            'stl': [],
            'prophet': [],
            'lstm': []
        }
    
    def fit(
        self,
        data: pd.DataFrame,
        value_column: str = 'value'
    ) -> 'EnsembleForecaster':
        """Fit all available models."""
        
        # STL
        if STL_AVAILABLE:
            try:
                self.models['stl'] = STLAnomalyDetector()
                # STL doesn't have a separate fit step
                logger.info("STL model ready")
            except Exception as e:
                logger.error(f"STL fit failed: {e}")
        
        # Prophet
        if PROPHET_AVAILABLE:
            try:
                self.models['prophet'] = ProphetForecaster()
                self.models['prophet'].fit(data, value_column)
                logger.info("Prophet model fitted")
            except Exception as e:
                logger.error(f"Prophet fit failed: {e}")
        
        # LSTM
        if TF_AVAILABLE and len(data) > 500:  # Need substantial data
            try:
                self.models['lstm'] = LSTMForecaster()
                self.models['lstm'].fit(data, value_column)
                logger.info("LSTM model fitted")
            except Exception as e:
                logger.error(f"LSTM fit failed: {e}")
        
        return self
    
    def predict(
        self,
        data: pd.DataFrame,
        value_column: str = 'value',
        steps: int = 96
    ) -> Dict[str, Any]:
        """
        Get predictions from all models.
        """
        results = {}
        
        # STL prediction
        if 'stl' in self.models and STL_AVAILABLE:
            try:
                decomp_df, _ = self.models['stl'].fit_transform(data, value_column)
                stl_pred = self.models['stl'].predict_next(decomp_df, steps)
                results['stl'] = stl_pred['predicted'].values
            except Exception as e:
                logger.error(f"STL prediction failed: {e}")
        
        # Prophet prediction
        if 'prophet' in self.models:
            try:
                prophet_pred = self.models['prophet'].predict(steps, include_history=False)
                results['prophet'] = prophet_pred['predicted'].values[-steps:]
            except Exception as e:
                logger.error(f"Prophet prediction failed: {e}")
        
        # LSTM prediction
        if 'lstm' in self.models:
            try:
                recent = data[value_column].values[-self.models['lstm'].lookback:]
                lstm_pred = self.models['lstm'].predict(recent)
                # LSTM predicts fewer steps, pad with last value
                if len(lstm_pred) < steps:
                    lstm_pred = np.pad(lstm_pred, (0, steps - len(lstm_pred)), mode='edge')
                results['lstm'] = lstm_pred[:steps]
            except Exception as e:
                logger.error(f"LSTM prediction failed: {e}")
        
        # Ensemble (weighted average)
        if results:
            ensemble_pred = np.zeros(steps)
            total_weight = 0
            
            for model_name, pred in results.items():
                weight = self.weights.get(model_name, 0.33)
                if len(pred) == steps:
                    ensemble_pred += weight * pred
                    total_weight += weight
            
            if total_weight > 0:
                ensemble_pred /= total_weight
            
            results['ensemble'] = ensemble_pred
        
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_sample_pressure_data(
    days: int = 30,
    interval_minutes: int = 15,
    base_pressure: float = 3.0,
    daily_amplitude: float = 0.5,
    noise_std: float = 0.1,
    add_anomalies: bool = True
) -> pd.DataFrame:
    """Generate sample pressure data for testing."""
    
    n_samples = days * 24 * 60 // interval_minutes
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=days),
        periods=n_samples,
        freq=f'{interval_minutes}min'
    )
    
    # Base daily pattern (higher at night, lower during peak)
    hours = timestamps.hour + timestamps.minute / 60
    daily_pattern = -daily_amplitude * np.sin(2 * np.pi * hours / 24)
    
    # Weekly pattern (slightly lower on weekends)
    weekly_pattern = 0.1 * (timestamps.dayofweek >= 5).astype(float)
    
    # Trend (slight increase)
    trend = np.linspace(0, 0.1, n_samples)
    
    # Noise
    noise = np.random.normal(0, noise_std, n_samples)
    
    # Combine
    pressure = base_pressure + daily_pattern + weekly_pattern + trend + noise
    
    # Add anomalies
    if add_anomalies:
        n_anomalies = n_samples // 500
        anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
        anomaly_magnitudes = np.random.choice([-0.8, -0.5, 0.5, 0.8], n_anomalies)
        pressure[anomaly_indices] += anomaly_magnitudes
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'value': pressure
    }).set_index('timestamp')


# =============================================================================
# MAIN EXECUTION (Demo)
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("AQUAWATCH NRW - TIME SERIES FORECASTING DEMO")
    print("="*80)
    
    # Generate sample data
    data = generate_sample_pressure_data(days=30)
    print(f"\nGenerated {len(data)} samples of pressure data")
    
    # Test STL
    if STL_AVAILABLE:
        print("\n--- STL Decomposition ---")
        stl = STLAnomalyDetector()
        decomp_df, anomalies = stl.fit_transform(data, 'value')
        print(f"Anomalies detected: {len(anomalies)}")
        if anomalies:
            print(f"Sample anomaly: {anomalies[0].timestamp} - Z-score: {anomalies[0].residual_zscore:.2f}")
    
    # Test Prophet
    if PROPHET_AVAILABLE:
        print("\n--- Prophet Forecast ---")
        prophet = ProphetForecaster()
        prophet.fit(data.reset_index(), 'value')
        forecast = prophet.predict(periods=24)  # 6 hours ahead
        print(f"Next prediction: {forecast['predicted'].iloc[0]:.3f}")
        print(f"95% CI: [{forecast['lower_95'].iloc[0]:.3f}, {forecast['upper_95'].iloc[0]:.3f}]")
    
    # Test Ensemble
    print("\n--- Ensemble Forecast ---")
    ensemble = EnsembleForecaster()
    ensemble.fit(data.reset_index(), 'value')
    predictions = ensemble.predict(data.reset_index(), 'value', steps=24)
    print(f"Models available: {list(predictions.keys())}")
    if 'ensemble' in predictions:
        print(f"Ensemble mean prediction: {np.mean(predictions['ensemble']):.3f}")
