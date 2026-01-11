"""
AquaWatch NRW - Feature Engineering Pipeline
============================================

This module implements the complete feature engineering pipeline for
pressure-based leak detection. Each feature has clear physical justification.

ALIGNED WITH IWA WATER BALANCE FRAMEWORK:
- Real Losses: Physical water loss (leaks, bursts, overflows)
- Apparent Losses: Metering errors, unauthorized consumption

"Most AI systems detect anomalies; ours understands water networks, 
NRW categories, and utility operations."

Design Principles:
1. Every feature must have physical meaning
2. Features should be robust to noise and missing data
3. Pipeline should be efficient for real-time processing
4. All transformations must be reproducible
5. Outputs expressed in WATER UTILITY language
6. Night-time analysis (00:00-04:00) is HIGH CONFIDENCE window
7. Pressure management logic integrated for risk assessment
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import savgol_filter
from enum import Enum
import warnings

warnings.filterwarnings('ignore')


# =============================================================================
# IWA WATER BALANCE FRAMEWORK CLASSIFICATIONS
# =============================================================================

class NRWCategory(Enum):
    """
    IWA Water Balance NRW Categories.
    
    Non-Revenue Water = Unbilled Authorized + Apparent Losses + Real Losses
    
    This system focuses on REAL LOSSES (physical leakage) detection.
    """
    # Real Losses (Physical Losses) - Primary focus
    REAL_LOSS_LEAKAGE = "real_loss_leakage"           # Leaks on transmission/distribution mains
    REAL_LOSS_OVERFLOW = "real_loss_overflow"         # Tank overflows
    REAL_LOSS_SERVICE = "real_loss_service"           # Service connection leaks
    
    # Apparent Losses (Commercial Losses) - Secondary detection
    APPARENT_LOSS_METER = "apparent_loss_meter"       # Meter under-registration
    APPARENT_LOSS_UNAUTHORIZED = "apparent_loss_unauthorized"  # Illegal connections
    
    UNKNOWN = "unknown"


class OperationalPriority(Enum):
    """Water utility operational priority levels."""
    CRITICAL = "critical"  # Immediate response required (burst main)
    HIGH = "high"          # Same-day response
    MEDIUM = "medium"      # 48-hour response
    LOW = "low"            # Scheduled maintenance


class SuggestedAction(Enum):
    """Water utility-specific suggested actions."""
    IMMEDIATE_REPAIR = "immediate_repair"      # Visible burst, immediate fix
    INSPECT_ACOUSTIC = "inspect_acoustic"      # Deploy acoustic logger
    INSPECT_VISUAL = "inspect_visual"          # Visual inspection
    PRESSURE_REVIEW = "pressure_review"        # Review zone pressure settings
    STEP_TEST = "step_test"                    # Isolate and step test
    MONITOR = "monitor"                        # Continue monitoring
    METER_CHECK = "meter_check"                # Check meter accuracy


# =============================================================================
# IWA NIGHT ANALYSIS CONSTANTS (HIGH CONFIDENCE WINDOW)
# =============================================================================

# IWA recommended night analysis window - HIGHEST CONFIDENCE for leak detection
IWA_NIGHT_START_HOUR = 0    # 00:00 (midnight)
IWA_NIGHT_END_HOUR = 4      # 04:00

# Minimum Night Flow (MNF) thresholds per IWA guidelines
MNF_LEGITIMATE_LITRES_PER_PROP_NIGHT = 1.7  # IWA guideline
MNF_BACKGROUND_LEAKAGE_ALLOWANCE = 0.05     # 5% of average day flow


@dataclass
class WaterUtilityDetection:
    """
    Water utility-centric detection result.
    
    This is NOT a generic anomaly score. This is water utility language
    that operators can act upon immediately.
    """
    # Location (DMA-centric)
    dma_id: str
    pipe_segment_id: Optional[str] = None
    
    # IWA Classification
    nrw_category: NRWCategory = NRWCategory.UNKNOWN
    
    # Confidence (water utility terminology)
    leak_confidence: float = 0.0          # 0-1 scale
    confidence_source: str = ""            # What drove the confidence
    operational_priority: OperationalPriority = OperationalPriority.LOW
    
    # NRW Impact Estimate (approximate is acceptable)
    estimated_loss_m3_day: float = 0.0
    estimated_loss_percent_dma_input: float = 0.0
    operational_risk: str = ""
    
    # Suggested Action
    suggested_action: SuggestedAction = SuggestedAction.MONITOR
    action_rationale: str = ""
    
    # Evidence in water utility language
    key_evidence: List[str] = field(default_factory=list)
    
    # Night analysis flag (high confidence indicator)
    night_analysis_triggered: bool = False
    high_pressure_zone: bool = False
    
    def to_utility_report(self) -> str:
        """Generate operator-readable report."""
        priority_emoji = {
            OperationalPriority.CRITICAL: "🔴",
            OperationalPriority.HIGH: "🟠",
            OperationalPriority.MEDIUM: "🟡",
            OperationalPriority.LOW: "🟢"
        }
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║             NRW DETECTION - UTILITY REPORT                  ║
╠══════════════════════════════════════════════════════════════╣
║ DMA: {self.dma_id:<54} ║
║ Pipe Segment: {(self.pipe_segment_id or 'Not localized'):<45} ║
╠══════════════════════════════════════════════════════════════╣
║ NRW CATEGORY: {self.nrw_category.value.replace('_', ' ').upper():<45} ║
║ LEAK CONFIDENCE: {self.leak_confidence:.0%:<42} ║
║ PRIORITY: {priority_emoji.get(self.operational_priority, '')} {self.operational_priority.value.upper():<45} ║
╠══════════════════════════════════════════════════════════════╣
║ ESTIMATED NRW IMPACT:                                        ║
║   Water Loss: ~{self.estimated_loss_m3_day:<6.0f} m³/day                                ║
║   % of DMA Input: ~{self.estimated_loss_percent_dma_input:<5.1f}%                                  ║
║   Risk: {self.operational_risk:<51} ║
╠══════════════════════════════════════════════════════════════╣
║ SUGGESTED ACTION: {self.suggested_action.value.replace('_', ' ').upper():<40} ║
║ Rationale: {self.action_rationale:<47} ║
╠══════════════════════════════════════════════════════════════╣
║ KEY EVIDENCE:                                                ║
{''.join(f'║   • {e:<56} ║{chr(10)}' for e in self.key_evidence[:5])}╠══════════════════════════════════════════════════════════════╣
║ Night Analysis (00:00-04:00): {'HIGH CONFIDENCE' if self.night_analysis_triggered else 'Standard':<29} ║
║ High Pressure Zone: {'Yes - elevated risk' if self.high_pressure_zone else 'No':<39} ║
╚══════════════════════════════════════════════════════════════╝
        """


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    
    # Time windows (in hours)
    short_window: int = 1          # 1 hour for rapid changes
    medium_window: int = 6         # 6 hours for trends
    long_window: int = 24          # 24 hours for daily patterns
    baseline_window: int = 168     # 7 days for baseline
    
    # Night hours for MNF analysis (Minimum Night Flow)
    mnf_start_hour: int = 1        # 1 AM
    mnf_end_hour: int = 4          # 4 AM
    
    # Data quality thresholds
    min_completeness: float = 0.8  # 80% data required
    min_samples_short: int = 4     # Minimum samples for short window
    min_samples_long: int = 80     # Minimum samples for long window
    
    # Smoothing parameters
    savgol_window: int = 5         # Savitzky-Golay filter window
    savgol_order: int = 2          # Polynomial order
    
    # Outlier detection
    zscore_threshold: float = 4.0  # Extreme outlier threshold


@dataclass
class SensorFeatures:
    """Container for computed features with metadata."""
    
    sensor_id: str
    timestamp: datetime
    features: Dict[str, float] = field(default_factory=dict)
    quality_score: float = 1.0
    warnings: List[str] = field(default_factory=list)
    computation_time_ms: float = 0.0


class FeatureEngineer:
    """
    Main feature engineering class for pressure-based leak detection.
    
    Physical Basis:
    ---------------
    Water leaks create specific pressure signatures:
    
    1. Local pressure drop: Pressure decreases near leak location
    2. Increased headloss: Pressure gradient steepens
    3. Night visibility: Effects most visible during low demand (1-4 AM)
    4. Temporal changes: Sudden drops indicate bursts; gradual indicate developing leaks
    
    The features capture these phenomena mathematically.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        
    def compute_features(
        self,
        pressure_data: pd.DataFrame,
        neighbor_data: Optional[Dict[str, pd.DataFrame]] = None,
        pipe_metadata: Optional[Dict] = None
    ) -> SensorFeatures:
        """
        Compute all features for a sensor.
        
        Args:
            pressure_data: DataFrame with columns ['timestamp', 'value']
                          Must contain at least baseline_window hours of data
            neighbor_data: Dict of {sensor_id: DataFrame} for relative features
            pipe_metadata: Dict with pipe attributes (length, material, age, etc.)
            
        Returns:
            SensorFeatures object containing all computed features
        """
        import time
        start_time = time.time()
        
        sensor_id = pressure_data.attrs.get('sensor_id', 'unknown')
        result = SensorFeatures(
            sensor_id=sensor_id,
            timestamp=datetime.utcnow()
        )
        
        # Validate input data
        if not self._validate_data(pressure_data, result):
            return result
        
        # Prepare data
        df = self._prepare_data(pressure_data)
        
        # Compute feature categories
        result.features.update(self._compute_absolute_features(df))
        result.features.update(self._compute_temporal_features(df))
        result.features.update(self._compute_contextual_features(df))
        result.features.update(self._compute_statistical_features(df))
        result.features.update(self._compute_night_features(df))
        
        # Relative features (if neighbor data available)
        if neighbor_data:
            result.features.update(
                self._compute_relative_features(df, neighbor_data, pipe_metadata)
            )
        
        # Derived composite features
        result.features.update(self._compute_derived_features(result.features))
        
        # Quality assessment
        result.quality_score = self._assess_quality(df, result.features)
        
        result.computation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _validate_data(self, df: pd.DataFrame, result: SensorFeatures) -> bool:
        """Validate input data quality."""
        
        if df is None or len(df) == 0:
            result.warnings.append("No data provided")
            result.quality_score = 0.0
            return False
            
        required_samples = self.config.baseline_window * 4  # 15-min intervals
        completeness = len(df) / required_samples
        
        if completeness < self.config.min_completeness:
            result.warnings.append(
                f"Insufficient data: {completeness:.1%} of required"
            )
            if completeness < 0.5:
                result.quality_score = 0.0
                return False
                
        return True
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for feature computation."""
        
        df = df.copy()
        
        # Ensure datetime index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        df = df.sort_index()
        
        # Remove extreme outliers (likely sensor errors)
        zscore = np.abs(stats.zscore(df['value'].dropna()))
        df.loc[zscore > self.config.zscore_threshold, 'value'] = np.nan
        
        # Forward fill small gaps (up to 1 hour)
        df['value'] = df['value'].ffill(limit=4)
        
        # Apply smoothing to reduce noise
        if len(df) >= self.config.savgol_window:
            valid_mask = df['value'].notna()
            if valid_mask.sum() >= self.config.savgol_window:
                df.loc[valid_mask, 'value_smooth'] = savgol_filter(
                    df.loc[valid_mask, 'value'],
                    self.config.savgol_window,
                    self.config.savgol_order
                )
        
        if 'value_smooth' not in df.columns:
            df['value_smooth'] = df['value']
            
        return df
    
    # =========================================================================
    # CATEGORY 1: ABSOLUTE FEATURES
    # =========================================================================
    
    def _compute_absolute_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute absolute pressure statistics.
        
        Physical Meaning:
        - Mean pressure indicates normal operating point
        - Min pressure shows stress conditions
        - Range indicates pressure stability
        - Std shows pressure variability
        """
        features = {}
        
        # Current window (last 24 hours)
        current = df['value'].tail(96)  # 96 samples = 24 hours at 15-min intervals
        
        if len(current) >= self.config.min_samples_short:
            features['pressure_mean'] = float(current.mean())
            features['pressure_std'] = float(current.std())
            features['pressure_min'] = float(current.min())
            features['pressure_max'] = float(current.max())
            features['pressure_range'] = features['pressure_max'] - features['pressure_min']
            features['pressure_median'] = float(current.median())
            
            # Coefficient of variation (normalized variability)
            if features['pressure_mean'] > 0:
                features['pressure_cv'] = features['pressure_std'] / features['pressure_mean']
            else:
                features['pressure_cv'] = 0.0
                
        # Latest reading
        if len(df) > 0:
            features['pressure_latest'] = float(df['value'].iloc[-1])
            
        return features
    
    # =========================================================================
    # CATEGORY 2: TEMPORAL FEATURES
    # =========================================================================
    
    def _compute_temporal_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute features related to pressure changes over time.
        
        Physical Meaning:
        - Drop rate indicates burst events (rapid) or developing leaks (gradual)
        - Rolling averages smooth out noise to reveal trends
        - Deviation from baseline shows abnormal conditions
        """
        features = {}
        
        # Current value
        current = df['value_smooth'].iloc[-1] if len(df) > 0 else np.nan
        
        # Short-term change (1 hour)
        if len(df) >= 4:
            p_1h_ago = df['value_smooth'].iloc[-4]
            features['pressure_1h_change'] = float(current - p_1h_ago)
            features['pressure_1h_change_rate'] = features['pressure_1h_change'] / 1.0  # bar/hour
        
        # Medium-term change (6 hours)
        if len(df) >= 24:
            p_6h_ago = df['value_smooth'].iloc[-24]
            features['pressure_6h_change'] = float(current - p_6h_ago)
            features['pressure_6h_change_rate'] = features['pressure_6h_change'] / 6.0
            
        # Daily change (24 hours)
        if len(df) >= 96:
            p_24h_ago = df['value_smooth'].iloc[-96]
            features['pressure_24h_change'] = float(current - p_24h_ago)
            features['pressure_24h_change_rate'] = features['pressure_24h_change'] / 24.0
            
        # Rolling averages
        features['rolling_mean_1h'] = float(df['value'].tail(4).mean())
        features['rolling_mean_6h'] = float(df['value'].tail(24).mean())
        features['rolling_mean_24h'] = float(df['value'].tail(96).mean())
        
        # 7-day baseline comparison
        if len(df) >= 672:  # 7 days
            baseline_mean = df['value'].iloc[:-96].mean()  # Exclude last 24h
            baseline_std = df['value'].iloc[:-96].std()
            
            features['baseline_mean'] = float(baseline_mean)
            features['baseline_std'] = float(baseline_std)
            features['deviation_from_baseline'] = float(current - baseline_mean)
            
            if baseline_std > 0:
                features['zscore_vs_baseline'] = float(
                    (current - baseline_mean) / baseline_std
                )
            else:
                features['zscore_vs_baseline'] = 0.0
                
        # Trend detection using linear regression
        if len(df) >= 24:
            recent = df['value_smooth'].tail(24).dropna()
            if len(recent) >= 12:
                x = np.arange(len(recent))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent)
                features['trend_slope_6h'] = float(slope * 4)  # Convert to bar/hour
                features['trend_r_squared'] = float(r_value ** 2)
                
        return features
    
    # =========================================================================
    # CATEGORY 3: CONTEXTUAL FEATURES
    # =========================================================================
    
    def _compute_contextual_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute time-of-day and calendar features.
        
        Physical Meaning:
        - Pressure patterns vary by time of day (demand-driven)
        - Weekend patterns differ from weekday
        - These help normalize for expected behavior
        """
        features = {}
        
        if len(df) == 0:
            return features
            
        latest_time = df.index[-1]
        
        # Time of day
        features['hour_of_day'] = float(latest_time.hour)
        features['is_night'] = float(1 if latest_time.hour in [1, 2, 3] else 0)
        features['is_morning_peak'] = float(1 if latest_time.hour in [6, 7, 8] else 0)
        features['is_evening_peak'] = float(1 if latest_time.hour in [18, 19, 20] else 0)
        
        # Day of week
        features['day_of_week'] = float(latest_time.dayofweek)
        features['is_weekend'] = float(1 if latest_time.dayofweek >= 5 else 0)
        
        # Cyclical encoding (preserves continuity)
        hour_sin = np.sin(2 * np.pi * latest_time.hour / 24)
        hour_cos = np.cos(2 * np.pi * latest_time.hour / 24)
        features['hour_sin'] = float(hour_sin)
        features['hour_cos'] = float(hour_cos)
        
        dow_sin = np.sin(2 * np.pi * latest_time.dayofweek / 7)
        dow_cos = np.cos(2 * np.pi * latest_time.dayofweek / 7)
        features['dow_sin'] = float(dow_sin)
        features['dow_cos'] = float(dow_cos)
        
        return features
    
    # =========================================================================
    # CATEGORY 4: STATISTICAL FEATURES
    # =========================================================================
    
    def _compute_statistical_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute advanced statistical features.
        
        Physical Meaning:
        - Skewness: Asymmetry in pressure distribution (leaks cause left skew)
        - Kurtosis: Presence of extreme values
        - Percentiles: Distribution shape indicators
        """
        features = {}
        
        recent = df['value'].tail(96).dropna()  # Last 24 hours
        
        if len(recent) >= self.config.min_samples_long:
            # Distribution statistics
            features['pressure_skewness'] = float(stats.skew(recent))
            features['pressure_kurtosis'] = float(stats.kurtosis(recent))
            
            # Percentiles
            features['pressure_p05'] = float(np.percentile(recent, 5))
            features['pressure_p25'] = float(np.percentile(recent, 25))
            features['pressure_p75'] = float(np.percentile(recent, 75))
            features['pressure_p95'] = float(np.percentile(recent, 95))
            
            # Interquartile range (robust variability measure)
            features['pressure_iqr'] = features['pressure_p75'] - features['pressure_p25']
            
            # Robust Z-score using median and IQR
            median = np.median(recent)
            iqr = features['pressure_iqr']
            if iqr > 0:
                features['pressure_robust_zscore'] = float(
                    (recent.iloc[-1] - median) / (iqr / 1.349)  # 1.349 for normal distribution
                )
            else:
                features['pressure_robust_zscore'] = 0.0
                
            # Count of values below typical range
            lower_bound = features['pressure_p25'] - 1.5 * features['pressure_iqr']
            features['low_pressure_count'] = float((recent < lower_bound).sum())
            
        return features
    
    # =========================================================================
    # CATEGORY 5: NIGHT FEATURES (MNF Analysis)
    # =========================================================================
    
    def _compute_night_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute Minimum Night Flow (MNF) related features.
        
        Physical Meaning:
        - Night pressure should be HIGHER than day (lower demand)
        - If night pressure is LOWER, this strongly indicates leakage
        - MNF window (1-4 AM) is when legitimate demand is minimal
        - Leaks "consume" pressure even when no legitimate demand exists
        
        This is one of the most powerful leak indicators.
        """
        features = {}
        
        # Get night hours from config
        mnf_start = self.config.mnf_start_hour
        mnf_end = self.config.mnf_end_hour
        
        # Last 7 days of data
        if len(df) < 96:  # Need at least 24 hours
            return features
            
        df_recent = df.tail(672)  # 7 days
        
        # Identify night periods
        df_recent = df_recent.copy()
        df_recent['hour'] = df_recent.index.hour
        df_recent['is_mnf'] = df_recent['hour'].isin(range(mnf_start, mnf_end))
        df_recent['is_day'] = df_recent['hour'].isin(range(8, 20))  # 8 AM to 8 PM
        
        night_data = df_recent[df_recent['is_mnf']]['value']
        day_data = df_recent[df_recent['is_day']]['value']
        
        if len(night_data) >= 12:  # At least 3 nights of data
            features['mnf_pressure_mean'] = float(night_data.mean())
            features['mnf_pressure_std'] = float(night_data.std())
            features['mnf_pressure_min'] = float(night_data.min())
            
        if len(day_data) >= 48:  # At least 1 day
            features['day_pressure_mean'] = float(day_data.mean())
            
        # Night/Day ratio - KEY LEAK INDICATOR
        # Healthy network: ratio > 1.0 (night pressure higher)
        # Leak present: ratio < 1.0 (night pressure lower)
        if 'mnf_pressure_mean' in features and 'day_pressure_mean' in features:
            if features['day_pressure_mean'] > 0:
                features['night_day_ratio'] = float(
                    features['mnf_pressure_mean'] / features['day_pressure_mean']
                )
            else:
                features['night_day_ratio'] = 1.0
                
        # Compare last night to 7-day night average
        last_24h = df.tail(96)
        last_24h_night = last_24h[last_24h.index.hour.isin(range(mnf_start, mnf_end))]['value']
        
        if len(last_24h_night) >= 3 and 'mnf_pressure_mean' in features:
            last_night_mean = last_24h_night.mean()
            features['mnf_last_night'] = float(last_night_mean)
            features['mnf_deviation'] = float(last_night_mean - features['mnf_pressure_mean'])
            
            if features['mnf_pressure_std'] > 0:
                features['mnf_zscore'] = float(
                    features['mnf_deviation'] / features['mnf_pressure_std']
                )
            else:
                features['mnf_zscore'] = 0.0
                
        # Night pressure stability (high variance indicates problems)
        if len(night_data) >= 12:
            features['mnf_cv'] = float(
                night_data.std() / night_data.mean() if night_data.mean() > 0 else 0
            )
            
        return features
    
    # =========================================================================
    # CATEGORY 6: RELATIVE FEATURES (Multi-sensor)
    # =========================================================================
    
    def _compute_relative_features(
        self,
        df: pd.DataFrame,
        neighbor_data: Dict[str, pd.DataFrame],
        pipe_metadata: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Compute features comparing this sensor to neighbors.
        
        Physical Meaning:
        - Pressure gradient shows headloss between points
        - Gradient increasing without demand change indicates leak between sensors
        - Correlation breaking down indicates anomaly in one sensor
        
        These features help LOCALIZE leaks to pipe segments.
        """
        features = {}
        
        if not neighbor_data:
            return features
            
        current_pressure = df['value'].iloc[-1] if len(df) > 0 else np.nan
        
        gradients = []
        correlations = []
        
        for neighbor_id, neighbor_df in neighbor_data.items():
            if len(neighbor_df) == 0:
                continue
                
            neighbor_pressure = neighbor_df['value'].iloc[-1]
            
            # Get distance between sensors (from metadata or default)
            distance = 500  # Default 500m
            if pipe_metadata and neighbor_id in pipe_metadata.get('distances', {}):
                distance = pipe_metadata['distances'][neighbor_id]
            
            # Pressure gradient (bar/km)
            pressure_diff = current_pressure - neighbor_pressure
            gradient = (pressure_diff / distance) * 1000  # Convert to bar/km
            
            features[f'pressure_diff_{neighbor_id}'] = float(pressure_diff)
            features[f'gradient_to_{neighbor_id}'] = float(gradient)
            
            gradients.append(gradient)
            
            # Correlation with neighbor (should be high for normal operation)
            if len(df) >= 96 and len(neighbor_df) >= 96:
                # Align timestamps
                merged = pd.merge(
                    df[['value']].tail(96),
                    neighbor_df[['value']].tail(96),
                    left_index=True,
                    right_index=True,
                    suffixes=('', '_neighbor')
                )
                
                if len(merged) >= 50:
                    corr = merged['value'].corr(merged['value_neighbor'])
                    features[f'correlation_{neighbor_id}'] = float(corr)
                    correlations.append(corr)
                    
        # Aggregate relative features
        if gradients:
            features['max_gradient'] = float(max(gradients))
            features['mean_gradient'] = float(np.mean(gradients))
            
        if correlations:
            features['min_neighbor_correlation'] = float(min(correlations))
            features['mean_neighbor_correlation'] = float(np.mean(correlations))
            
        return features
    
    # =========================================================================
    # CATEGORY 7: DERIVED COMPOSITE FEATURES
    # =========================================================================
    
    def _compute_derived_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Compute composite features that combine multiple signals.
        
        These are higher-level indicators designed to be:
        1. Robust (multiple signals must agree)
        2. Interpretable (clear physical meaning)
        3. Actionable (directly indicate leak likelihood)
        """
        derived = {}
        
        # Leak Index: Combined score from multiple indicators
        # Each component contributes to overall suspicion
        leak_signals = []
        
        # Signal 1: Night/day ratio below threshold
        if 'night_day_ratio' in features:
            # Ratio < 0.98 is suspicious, < 0.95 is concerning
            ndr = features['night_day_ratio']
            if ndr < 1.0:
                signal = min((1.0 - ndr) / 0.1, 1.0)  # Normalize to 0-1
                leak_signals.append(('night_day_ratio', signal))
                
        # Signal 2: MNF deviation below normal
        if 'mnf_deviation' in features:
            mnf_dev = features['mnf_deviation']
            if mnf_dev < 0:
                signal = min(abs(mnf_dev) / 0.5, 1.0)  # 0.5 bar deviation = max signal
                leak_signals.append(('mnf_deviation', signal))
                
        # Signal 3: Negative pressure trend
        if 'trend_slope_6h' in features:
            slope = features['trend_slope_6h']
            if slope < 0:
                signal = min(abs(slope) / 0.1, 1.0)  # 0.1 bar/hour slope = max signal
                leak_signals.append(('negative_trend', signal))
                
        # Signal 4: High gradient (if relative features available)
        if 'max_gradient' in features:
            gradient = features['max_gradient']
            if gradient > 0.5:  # > 0.5 bar/km is elevated
                signal = min((gradient - 0.5) / 1.0, 1.0)
                leak_signals.append(('high_gradient', signal))
                
        # Signal 5: Statistical anomaly
        if 'zscore_vs_baseline' in features:
            zscore = features['zscore_vs_baseline']
            if zscore < -2:  # More than 2 std below baseline
                signal = min((abs(zscore) - 2) / 2, 1.0)
                leak_signals.append(('statistical_anomaly', signal))
        
        # Combine signals with weights
        if leak_signals:
            weights = {
                'night_day_ratio': 0.30,      # Strongest indicator
                'mnf_deviation': 0.25,         # Also strong
                'negative_trend': 0.15,        # Supporting evidence
                'high_gradient': 0.20,         # Location indicator
                'statistical_anomaly': 0.10    # General anomaly
            }
            
            weighted_sum = sum(
                weights.get(name, 0.1) * signal 
                for name, signal in leak_signals
            )
            total_weight = sum(
                weights.get(name, 0.1) 
                for name, _ in leak_signals
            )
            
            derived['leak_index'] = float(weighted_sum / total_weight if total_weight > 0 else 0)
            derived['leak_signal_count'] = float(len(leak_signals))
            
            # Store contributing factors for explainability
            derived['leak_index_components'] = str(leak_signals)
            
        # Pressure stability index
        if 'pressure_cv' in features and 'pressure_iqr' in features:
            # Low CV and low IQR = stable = good
            cv = features['pressure_cv']
            iqr = features['pressure_iqr']
            stability = 1.0 - min(cv * 10 + iqr, 1.0)
            derived['pressure_stability'] = float(stability)
            
        # Data freshness indicator
        derived['features_computed'] = float(len(features))
        
        return derived
    
    def _assess_quality(self, df: pd.DataFrame, features: Dict[str, float]) -> float:
        """
        Assess overall quality of computed features.
        
        Returns:
            Quality score from 0 to 1
        """
        quality = 1.0
        
        # Penalize for missing data
        expected_samples = self.config.baseline_window * 4
        actual_samples = len(df.dropna())
        completeness = actual_samples / expected_samples
        quality *= min(completeness / 0.8, 1.0)  # No penalty above 80%
        
        # Penalize for missing key features
        key_features = [
            'pressure_mean', 'night_day_ratio', 'mnf_deviation',
            'deviation_from_baseline', 'leak_index'
        ]
        missing_key = sum(1 for f in key_features if f not in features)
        quality *= (1 - 0.1 * missing_key)
        
        # Penalize for extreme values (likely sensor issues)
        if 'pressure_latest' in features:
            p = features['pressure_latest']
            if p < 0 or p > 20:  # Outside reasonable range
                quality *= 0.5
                
        return max(0.0, min(1.0, quality))

    # =========================================================================
    # IWA WATER BALANCE ALIGNED CLASSIFICATION
    # =========================================================================
    
    def classify_for_water_utility(
        self,
        features: Dict[str, float],
        dma_id: str,
        pipe_segment_id: Optional[str] = None,
        dma_input_m3_day: float = 1000.0,
        num_connections: int = 500,
        avg_zone_pressure_bar: float = 4.0
    ) -> WaterUtilityDetection:
        """
        Classify detection using IWA Water Balance framework.
        
        This produces WATER UTILITY-CENTRIC output, not generic anomaly scores.
        
        "Most AI systems detect anomalies; ours understands water networks,
        NRW categories, and utility operations."
        
        Args:
            features: Computed feature dictionary
            dma_id: District Metered Area identifier
            pipe_segment_id: Optional pipe segment for localization
            dma_input_m3_day: Total water entering DMA (for % calculation)
            num_connections: Number of service connections in DMA
            avg_zone_pressure_bar: Average operating pressure
            
        Returns:
            WaterUtilityDetection with actionable utility information
        """
        
        result = WaterUtilityDetection(
            dma_id=dma_id,
            pipe_segment_id=pipe_segment_id
        )
        
        evidence = []
        confidence_components = []
        
        # =====================================================================
        # NIGHT ANALYSIS (00:00-04:00) - HIGHEST CONFIDENCE WINDOW
        # IWA: Night flow analysis is gold standard for leak detection
        # =====================================================================
        
        night_day_ratio = features.get('night_day_ratio', 1.0)
        mnf_deviation = features.get('mnf_deviation', 0)
        
        # Night/day ratio is THE key IWA indicator
        # Healthy network: night pressure > day pressure (ratio > 1.0)
        # Leak present: night pressure drops (ratio < 1.0)
        
        if night_day_ratio < 0.92:
            # STRONG leak signal
            evidence.append(f"Night/day pressure ratio {night_day_ratio:.3f} - STRONG leak indicator (IWA)")
            confidence_components.append(('night_ratio_critical', 0.40))
            result.night_analysis_triggered = True
        elif night_day_ratio < 0.96:
            # Moderate leak signal
            evidence.append(f"Night/day pressure ratio {night_day_ratio:.3f} - Moderate leak indicator")
            confidence_components.append(('night_ratio_moderate', 0.25))
            result.night_analysis_triggered = True
        elif night_day_ratio < 0.99:
            # Mild signal
            evidence.append(f"Night/day pressure ratio {night_day_ratio:.3f} - Mild anomaly")
            confidence_components.append(('night_ratio_mild', 0.10))
            result.night_analysis_triggered = True
        
        # MNF deviation (last night vs baseline)
        if mnf_deviation < -0.15:  # Pressure drop > 0.15 bar
            evidence.append(f"Night pressure {abs(mnf_deviation):.2f} bar below baseline")
            confidence_components.append(('mnf_drop', 0.25))
            result.night_analysis_triggered = True
        elif mnf_deviation < -0.08:
            evidence.append(f"Night pressure {abs(mnf_deviation):.2f} bar below baseline")
            confidence_components.append(('mnf_drop_mild', 0.12))
        
        # =====================================================================
        # PRESSURE MANAGEMENT LOGIC
        # IWA: Leakage rate proportional to pressure (N1 factor typically 0.5-1.5)
        # High pressure zones = higher leakage risk
        # =====================================================================
        
        pressure_risk = self._calculate_pressure_leakage_risk(avg_zone_pressure_bar)
        
        if avg_zone_pressure_bar >= 6.0:
            evidence.append(f"HIGH pressure zone ({avg_zone_pressure_bar:.1f} bar) - elevated leak risk")
            confidence_components.append(('high_pressure_zone', 0.15))
            result.high_pressure_zone = True
            result.operational_risk = "High pressure zone - leakage rates significantly elevated"
        elif avg_zone_pressure_bar >= 5.0:
            evidence.append(f"Elevated pressure ({avg_zone_pressure_bar:.1f} bar) - increased leak risk")
            confidence_components.append(('elevated_pressure', 0.08))
            result.operational_risk = "Elevated pressure - consider pressure management"
        
        # =====================================================================
        # BASELINE DEVIATION (sustained abnormality)
        # =====================================================================
        
        baseline_deviation = features.get('deviation_from_baseline', 0)
        zscore_baseline = features.get('zscore_vs_baseline', 0)
        
        if zscore_baseline < -3.0:
            evidence.append(f"Pressure {abs(baseline_deviation):.2f} bar below baseline (>3σ deviation)")
            confidence_components.append(('baseline_critical', 0.20))
        elif zscore_baseline < -2.0:
            evidence.append(f"Pressure {abs(baseline_deviation):.2f} bar below baseline (>2σ deviation)")
            confidence_components.append(('baseline_significant', 0.12))
        
        # =====================================================================
        # PRESSURE GRADIENT (localization indicator)
        # =====================================================================
        
        max_gradient = features.get('max_gradient', 0)
        if max_gradient > 1.5:  # bar/km
            evidence.append(f"Steep pressure gradient ({max_gradient:.2f} bar/km) - leak between sensors")
            confidence_components.append(('gradient_steep', 0.15))
        elif max_gradient > 0.8:
            evidence.append(f"Elevated gradient ({max_gradient:.2f} bar/km)")
            confidence_components.append(('gradient_elevated', 0.08))
        
        # =====================================================================
        # CALCULATE TOTAL CONFIDENCE
        # =====================================================================
        
        total_confidence = sum(score for _, score in confidence_components)
        result.leak_confidence = min(total_confidence, 1.0)
        
        if result.night_analysis_triggered:
            result.confidence_source = "Night analysis (00:00-04:00) - HIGH CONFIDENCE window"
        else:
            result.confidence_source = "Daytime analysis - standard confidence"
        
        # =====================================================================
        # ESTIMATE NRW IMPACT (approximate values acceptable per requirements)
        # IWA: Real losses are physical water escaping system
        # =====================================================================
        
        # Estimate loss based on pressure drop and zone size
        if result.leak_confidence > 0.3:
            # Rough estimation: each 0.1 bar night pressure deficit ≈ X m³/day loss
            # This is approximate but defensible
            
            pressure_deficit = abs(min(mnf_deviation, 0))
            
            # Loss estimate based on zone characteristics
            # Higher pressure = higher loss rate (IWA N1 factor)
            n1_factor = 1.0 + (avg_zone_pressure_bar - 4.0) * 0.2  # Adjust for pressure
            
            base_loss_estimate = pressure_deficit * 100 * n1_factor  # m³/day rough estimate
            result.estimated_loss_m3_day = max(10, min(500, base_loss_estimate))  # Reasonable bounds
            
            if dma_input_m3_day > 0:
                result.estimated_loss_percent_dma_input = (
                    result.estimated_loss_m3_day / dma_input_m3_day * 100
                )
        
        # =====================================================================
        # CLASSIFY NRW CATEGORY (IWA Water Balance)
        # =====================================================================
        
        if result.leak_confidence >= 0.4:
            # Physical leakage is most common detection
            result.nrw_category = NRWCategory.REAL_LOSS_LEAKAGE
        elif result.leak_confidence >= 0.2:
            result.nrw_category = NRWCategory.UNKNOWN
        
        # =====================================================================
        # DETERMINE OPERATIONAL PRIORITY
        # =====================================================================
        
        if result.leak_confidence >= 0.75:
            result.operational_priority = OperationalPriority.CRITICAL
        elif result.leak_confidence >= 0.55:
            result.operational_priority = OperationalPriority.HIGH
        elif result.leak_confidence >= 0.35:
            result.operational_priority = OperationalPriority.MEDIUM
        else:
            result.operational_priority = OperationalPriority.LOW
        
        # Escalate if high estimated loss regardless of confidence
        if result.estimated_loss_m3_day > 100:
            if result.operational_priority in [OperationalPriority.LOW, OperationalPriority.MEDIUM]:
                result.operational_priority = OperationalPriority.HIGH
                evidence.append("Priority escalated: high estimated loss volume")
        
        # =====================================================================
        # DETERMINE SUGGESTED ACTION (water utility specific)
        # =====================================================================
        
        if result.operational_priority == OperationalPriority.CRITICAL:
            result.suggested_action = SuggestedAction.INSPECT_ACOUSTIC
            result.action_rationale = "Deploy acoustic logger for immediate pinpointing"
        elif result.operational_priority == OperationalPriority.HIGH:
            if result.high_pressure_zone:
                result.suggested_action = SuggestedAction.PRESSURE_REVIEW
                result.action_rationale = "Review zone pressure settings, then acoustic survey"
            else:
                result.suggested_action = SuggestedAction.INSPECT_ACOUSTIC
                result.action_rationale = "Acoustic survey within 24 hours"
        elif result.operational_priority == OperationalPriority.MEDIUM:
            result.suggested_action = SuggestedAction.INSPECT_VISUAL
            result.action_rationale = "Visual inspection within 48 hours"
        else:
            result.suggested_action = SuggestedAction.MONITOR
            result.action_rationale = "Continue monitoring, include in routine survey"
        
        result.key_evidence = evidence
        
        return result
    
    def _calculate_pressure_leakage_risk(self, avg_pressure_bar: float) -> float:
        """
        Calculate leakage risk based on operating pressure.
        
        Physical basis (IWA research):
        - Leakage rate L = C × P^N1
        - N1 typically 0.5-1.5 depending on leak type
        - Higher pressure = exponentially more leakage
        
        Risk categories for African context:
        - < 2.5 bar: Low risk but service issues
        - 2.5-4.0 bar: Normal operating range
        - 4.0-5.0 bar: Elevated risk
        - 5.0-6.0 bar: High risk
        - > 6.0 bar: Very high risk (pressure management critical)
        """
        
        if avg_pressure_bar < 2.5:
            return 0.2  # Low leakage but potential supply issues
        elif avg_pressure_bar < 4.0:
            return 0.3  # Normal
        elif avg_pressure_bar < 5.0:
            return 0.5  # Elevated
        elif avg_pressure_bar < 6.0:
            return 0.7  # High
        else:
            return 0.9  # Very high - pressure reduction recommended


# =============================================================================
# FEATURE DOCUMENTATION (IWA WATER BALANCE ALIGNED)
# =============================================================================

FEATURE_DOCUMENTATION = """
FEATURE REFERENCE GUIDE - IWA WATER BALANCE ALIGNED
====================================================

"Most AI systems detect anomalies; ours understands water networks,
NRW categories, and utility operations."


IWA NRW CATEGORIES DETECTED
---------------------------
REAL LOSSES (Physical Losses) - Primary Detection Target:
  - Leaks on transmission and distribution mains
  - Leaks on service connections
  - Tank overflows

APPARENT LOSSES (Commercial Losses) - Secondary:
  - Meter under-registration
  - Unauthorized consumption


NIGHT ANALYSIS FEATURES (00:00-04:00) - HIGHEST CONFIDENCE
----------------------------------------------------------
Why night analysis is the IWA gold standard:
  1. Legitimate demand is minimal and predictable
  2. Industrial demand typically zero
  3. Pressure should be at MAXIMUM (no demand headloss)
  4. Any excess flow/pressure drop = REAL LOSS (physical leakage)

night_day_ratio     : Night pressure / Day pressure (ratio)
                      Physical: Should be >1.0 (higher at night)
                      Leak effect: <1.0 indicates leak consuming pressure
                      
                      INTERPRETATION (IWA-aligned):
                      >1.02 : Healthy network
                      0.98-1.02 : Normal variation
                      0.96-0.98 : Mild anomaly, monitor
                      0.92-0.96 : Moderate leak indicator, investigate
                      <0.92 : STRONG leak indicator, prioritize

mnf_pressure_mean   : Average pressure during MNF window (bar)
                      Physical: Pressure when demand minimal
                      Leak effect: Lower than expected

mnf_deviation       : Last night vs 7-day night average (bar)
                      Physical: Night pressure trend
                      Leak effect: Negative = dropping night pressure = leak


PRESSURE MANAGEMENT FEATURES (IWA Leakage-Pressure Relationship)
----------------------------------------------------------------
Physical basis: Leakage rate L = C × P^N1 (N1 = 0.5 to 1.5)
Higher pressure = exponentially higher leakage

pressure_mean       : Average operating pressure (bar)
                      Risk zones:
                      <2.5 bar: Low leak risk but service issues
                      2.5-4.0 bar: Normal operating range
                      4.0-5.0 bar: Elevated leak risk
                      5.0-6.0 bar: High leak risk
                      >6.0 bar: Very high risk - pressure management critical

pressure_leakage_risk : Calculated risk factor (0-1)
                        Based on IWA pressure-leakage relationship


ABSOLUTE FEATURES
-----------------
pressure_mean       : Average pressure over 24 hours (bar)
                      Physical: Normal operating point
                      Leak effect: Decreases near leak

pressure_min        : Minimum pressure in window (bar)
                      Physical: Worst-case pressure
                      Leak effect: Decreases significantly (service impact)


TEMPORAL FEATURES
-----------------
pressure_1h_change  : Pressure change over 1 hour (bar)
                      Physical: Short-term dynamics
                      Leak effect: Negative for burst events

trend_slope_6h      : Linear trend over 6 hours (bar/hour)
                      Physical: Pressure trajectory
                      Leak effect: Negative slope = pressure loss

deviation_from_baseline : Current vs 7-day average (bar)
                          Physical: Abnormal vs normal operation
                          Leak effect: Negative (below normal)


RELATIVE FEATURES (LOCALIZATION)
--------------------------------
gradient_to_{neighbor}   : Pressure gradient (bar/km)
                           Physical: Headloss per unit distance
                           Leak effect: Steepens between sensors
                           Helps LOCALIZE leak to pipe segment


DERIVED FEATURES
----------------
leak_index          : Combined leak probability indicator (0-1)
                      Aggregates multiple IWA-aligned signals

pressure_stability  : Overall pressure stability (0-1)
                      System health indicator


WATER UTILITY OUTPUT FORMAT
---------------------------
All detections expressed in utility language:

1. Affected DMA or pipe segment
2. NRW Category (Real Loss - Leakage)
3. Leak confidence level (%)
4. Operational priority (Critical/High/Medium/Low)
5. Suggested action:
   - Inspect (Acoustic survey)
   - Monitor (Continue observation)
   - Pressure review (Zone pressure management)

This is NOT generic anomaly detection.
This is water network intelligence for utility operations.
"""


def get_feature_documentation() -> str:
    """Return IWA-aligned feature documentation string."""
    return FEATURE_DOCUMENTATION
