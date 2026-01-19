"""
AQUAWATCH NRW - CENTRAL FEATURE STORE
=====================================

SINGLE SOURCE OF TRUTH for all processed features.

This module ensures:
- Raw sensor data is written ONCE
- All AI modules read from the same processed feature store
- No duplicated feature computation
- Versioned features
- Timestamp alignment guarantees

Data Flow:
    ESP32/SCADA → Ingestion → FeatureStore → AI Models → Decision Engine

Author: AquaWatch AI Team
Version: 1.0.0
"""

import logging
import threading
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class FeatureType(Enum):
    """Types of features in the store."""
    RAW_SENSOR = "raw_sensor"           # Raw sensor readings
    STATISTICAL = "statistical"          # Statistical aggregations
    TEMPORAL = "temporal"                # Time-based features
    DERIVED = "derived"                  # Computed features
    BASELINE = "baseline"                # Baseline comparisons
    ANOMALY = "anomaly"                  # Anomaly scores


class DataQuality(Enum):
    """Data quality flags."""
    GOOD = "good"
    SUSPECT = "suspect"
    BAD = "bad"
    STALE = "stale"
    MISSING = "missing"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FeatureRecord:
    """Single feature record with metadata."""
    feature_id: str
    dma_id: str
    sensor_id: str
    feature_type: FeatureType
    timestamp: datetime
    value: float
    unit: str
    quality: DataQuality = DataQuality.GOOD
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'feature_id': self.feature_id,
            'dma_id': self.dma_id,
            'sensor_id': self.sensor_id,
            'feature_type': self.feature_type.value,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'unit': self.unit,
            'quality': self.quality.value,
            'version': self.version,
            'metadata': self.metadata
        }


@dataclass
class FeatureVector:
    """Complete feature vector for a DMA at a point in time."""
    dma_id: str
    timestamp: datetime
    version: int
    
    # Raw sensor features
    pressure_bar: float = 0.0
    flow_m3_h: float = 0.0
    noise_level_db: float = 0.0
    
    # Statistical features (rolling windows)
    pressure_mean_1h: float = 0.0
    pressure_std_1h: float = 0.0
    pressure_min_1h: float = 0.0
    pressure_max_1h: float = 0.0
    flow_mean_1h: float = 0.0
    flow_std_1h: float = 0.0
    
    # Temporal features
    hour_of_day: int = 0
    day_of_week: int = 0
    is_night: bool = False  # 00:00-04:00
    is_weekend: bool = False
    
    # Derived features
    pressure_deviation: float = 0.0
    flow_deviation: float = 0.0
    night_day_ratio: float = 1.0
    mnf_deviation: float = 0.0  # Minimum Night Flow deviation
    
    # Baseline comparison (from STL)
    stl_trend: float = 0.0
    stl_seasonal: float = 0.0
    stl_residual: float = 0.0
    stl_expected: float = 0.0
    
    # Quality metadata
    data_quality: DataQuality = DataQuality.GOOD
    completeness_percent: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_ai_input(self) -> Dict[str, float]:
        """Convert to AI model input format."""
        return {
            'pressure_bar': self.pressure_bar,
            'flow_m3_h': self.flow_m3_h,
            'noise_level_db': self.noise_level_db,
            'pressure_mean_1h': self.pressure_mean_1h,
            'pressure_std_1h': self.pressure_std_1h,
            'pressure_deviation': self.pressure_deviation,
            'flow_deviation': self.flow_deviation,
            'night_day_ratio': self.night_day_ratio,
            'mnf_deviation': self.mnf_deviation,
            'hour_of_day': self.hour_of_day,
            'is_night': 1.0 if self.is_night else 0.0,
            'stl_residual': self.stl_residual
        }


@dataclass
class FeatureStoreConfig:
    """Configuration for the feature store."""
    # Storage
    storage_path: str = "./data/features"
    max_history_hours: int = 168  # 7 days
    
    # Alignment
    timestamp_resolution_minutes: int = 15  # 15-minute buckets
    
    # Quality thresholds
    stale_threshold_minutes: int = 30
    min_completeness_percent: float = 80.0
    
    # Versioning
    current_version: int = 1


# =============================================================================
# FEATURE STORE
# =============================================================================

class FeatureStore:
    """
    Central Feature Store - SINGLE SOURCE OF TRUTH.
    
    All AI modules read from this store.
    Raw data is processed ONCE and stored here.
    """
    
    def __init__(self, config: Optional[FeatureStoreConfig] = None):
        self.config = config or FeatureStoreConfig()
        self._lock = threading.RLock()
        
        # In-memory stores (would be backed by TimescaleDB in production)
        self._raw_readings: Dict[str, List[FeatureRecord]] = defaultdict(list)
        self._feature_vectors: Dict[str, List[FeatureVector]] = defaultdict(list)
        self._baselines: Dict[str, Dict[str, float]] = {}  # dma_id -> baseline values
        
        # Latest values cache
        self._latest: Dict[str, FeatureVector] = {}
        
        # Subscribers for feature updates
        self._subscribers: List[callable] = []
        
        # Ensure storage directory exists
        Path(self.config.storage_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("FeatureStore initialized")
    
    def _align_timestamp(self, ts: datetime) -> datetime:
        """Align timestamp to configured resolution."""
        resolution = self.config.timestamp_resolution_minutes
        minutes = (ts.minute // resolution) * resolution
        return ts.replace(minute=minutes, second=0, microsecond=0)
    
    def _generate_feature_id(self, dma_id: str, sensor_id: str, 
                              feature_type: str, timestamp: datetime) -> str:
        """Generate unique feature ID."""
        content = f"{dma_id}:{sensor_id}:{feature_type}:{timestamp.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    # =========================================================================
    # RAW DATA INGESTION
    # =========================================================================
    
    def ingest_reading(
        self,
        dma_id: str,
        sensor_id: str,
        timestamp: datetime,
        pressure: Optional[float] = None,
        flow: Optional[float] = None,
        noise_level: Optional[float] = None,
        quality: DataQuality = DataQuality.GOOD,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Ingest raw sensor reading.
        
        This is the ONLY entry point for new sensor data.
        Data is processed and features are computed automatically.
        """
        aligned_ts = self._align_timestamp(timestamp)
        
        with self._lock:
            # Store raw readings
            if pressure is not None:
                record = FeatureRecord(
                    feature_id=self._generate_feature_id(dma_id, sensor_id, 'pressure', aligned_ts),
                    dma_id=dma_id,
                    sensor_id=sensor_id,
                    feature_type=FeatureType.RAW_SENSOR,
                    timestamp=aligned_ts,
                    value=pressure,
                    unit='bar',
                    quality=quality,
                    version=self.config.current_version,
                    metadata=metadata or {}
                )
                self._raw_readings[f"{dma_id}:pressure"].append(record)
            
            if flow is not None:
                record = FeatureRecord(
                    feature_id=self._generate_feature_id(dma_id, sensor_id, 'flow', aligned_ts),
                    dma_id=dma_id,
                    sensor_id=sensor_id,
                    feature_type=FeatureType.RAW_SENSOR,
                    timestamp=aligned_ts,
                    value=flow,
                    unit='m3/h',
                    quality=quality,
                    version=self.config.current_version,
                    metadata=metadata or {}
                )
                self._raw_readings[f"{dma_id}:flow"].append(record)
            
            if noise_level is not None:
                record = FeatureRecord(
                    feature_id=self._generate_feature_id(dma_id, sensor_id, 'noise', aligned_ts),
                    dma_id=dma_id,
                    sensor_id=sensor_id,
                    feature_type=FeatureType.RAW_SENSOR,
                    timestamp=aligned_ts,
                    value=noise_level,
                    unit='dB',
                    quality=quality,
                    version=self.config.current_version,
                    metadata=metadata or {}
                )
                self._raw_readings[f"{dma_id}:noise"].append(record)
            
            # Compute and update feature vector
            feature_vector = self._compute_feature_vector(dma_id, aligned_ts)
            
            # Store feature vector
            self._feature_vectors[dma_id].append(feature_vector)
            self._latest[dma_id] = feature_vector
            
            # Trim old data
            self._trim_history(dma_id)
            
            # Notify subscribers
            self._notify_subscribers(dma_id, feature_vector)
            
            return record.feature_id if pressure is not None else f"{dma_id}:{aligned_ts.isoformat()}"
    
    def _compute_feature_vector(self, dma_id: str, timestamp: datetime) -> FeatureVector:
        """Compute complete feature vector from raw readings."""
        
        # Get recent readings
        pressure_readings = self._get_recent_values(f"{dma_id}:pressure", hours=1)
        flow_readings = self._get_recent_values(f"{dma_id}:flow", hours=1)
        noise_readings = self._get_recent_values(f"{dma_id}:noise", hours=1)
        
        # Get baselines
        baseline = self._baselines.get(dma_id, {})
        baseline_pressure = baseline.get('pressure', 3.0)
        baseline_flow = baseline.get('flow', 50.0)
        baseline_mnf = baseline.get('mnf', 10.0)
        
        # Compute statistics
        pressure_values = [r.value for r in pressure_readings]
        flow_values = [r.value for r in flow_readings]
        
        current_pressure = pressure_values[-1] if pressure_values else 0.0
        current_flow = flow_values[-1] if flow_values else 0.0
        current_noise = noise_readings[-1].value if noise_readings else 0.0
        
        # Statistical features
        import statistics
        pressure_mean = statistics.mean(pressure_values) if pressure_values else 0.0
        pressure_std = statistics.stdev(pressure_values) if len(pressure_values) > 1 else 0.0
        pressure_min = min(pressure_values) if pressure_values else 0.0
        pressure_max = max(pressure_values) if pressure_values else 0.0
        flow_mean = statistics.mean(flow_values) if flow_values else 0.0
        flow_std = statistics.stdev(flow_values) if len(flow_values) > 1 else 0.0
        
        # Temporal features
        hour = timestamp.hour
        day = timestamp.weekday()
        is_night = 0 <= hour < 4
        is_weekend = day >= 5
        
        # Derived features
        pressure_deviation = (current_pressure - baseline_pressure) / baseline_pressure if baseline_pressure else 0.0
        flow_deviation = (current_flow - baseline_flow) / baseline_flow if baseline_flow else 0.0
        
        # Night-day ratio (for leak detection)
        night_flow = self._get_night_flow_avg(dma_id)
        day_flow = self._get_day_flow_avg(dma_id)
        night_day_ratio = night_flow / day_flow if day_flow > 0 else 1.0
        
        # MNF deviation
        mnf_deviation = (night_flow - baseline_mnf) / baseline_mnf if baseline_mnf else 0.0
        
        # Data quality
        total_expected = 4  # pressure, flow, noise readings + baseline
        total_available = sum([
            1 if pressure_values else 0,
            1 if flow_values else 0,
            1 if noise_readings else 0,
            1 if baseline else 0
        ])
        completeness = (total_available / total_expected) * 100
        
        quality = DataQuality.GOOD
        if completeness < 50:
            quality = DataQuality.BAD
        elif completeness < 80:
            quality = DataQuality.SUSPECT
        
        return FeatureVector(
            dma_id=dma_id,
            timestamp=timestamp,
            version=self.config.current_version,
            pressure_bar=current_pressure,
            flow_m3_h=current_flow,
            noise_level_db=current_noise,
            pressure_mean_1h=pressure_mean,
            pressure_std_1h=pressure_std,
            pressure_min_1h=pressure_min,
            pressure_max_1h=pressure_max,
            flow_mean_1h=flow_mean,
            flow_std_1h=flow_std,
            hour_of_day=hour,
            day_of_week=day,
            is_night=is_night,
            is_weekend=is_weekend,
            pressure_deviation=pressure_deviation,
            flow_deviation=flow_deviation,
            night_day_ratio=night_day_ratio,
            mnf_deviation=mnf_deviation,
            data_quality=quality,
            completeness_percent=completeness
        )
    
    def _get_recent_values(self, key: str, hours: int = 1) -> List[FeatureRecord]:
        """Get recent values for a key."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        readings = self._raw_readings.get(key, [])
        return [r for r in readings if r.timestamp > cutoff]
    
    def _get_night_flow_avg(self, dma_id: str) -> float:
        """Get average night flow (00:00-04:00)."""
        readings = self._raw_readings.get(f"{dma_id}:flow", [])
        night_values = [r.value for r in readings if 0 <= r.timestamp.hour < 4]
        return sum(night_values) / len(night_values) if night_values else 0.0
    
    def _get_day_flow_avg(self, dma_id: str) -> float:
        """Get average day flow (06:00-22:00)."""
        readings = self._raw_readings.get(f"{dma_id}:flow", [])
        day_values = [r.value for r in readings if 6 <= r.timestamp.hour < 22]
        return sum(day_values) / len(day_values) if day_values else 0.0
    
    def _trim_history(self, dma_id: str):
        """Trim old history to save memory."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.max_history_hours)
        
        for key in list(self._raw_readings.keys()):
            if key.startswith(dma_id):
                self._raw_readings[key] = [
                    r for r in self._raw_readings[key] if r.timestamp > cutoff
                ]
        
        self._feature_vectors[dma_id] = [
            fv for fv in self._feature_vectors[dma_id] if fv.timestamp > cutoff
        ]
    
    # =========================================================================
    # FEATURE RETRIEVAL (Read by AI modules)
    # =========================================================================
    
    def get_latest(self, dma_id: str) -> Optional[FeatureVector]:
        """Get latest feature vector for a DMA."""
        return self._latest.get(dma_id)
    
    def get_latest_all(self) -> Dict[str, FeatureVector]:
        """Get latest feature vectors for all DMAs."""
        return dict(self._latest)
    
    def get_history(
        self,
        dma_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[FeatureVector]:
        """Get historical feature vectors for a DMA."""
        vectors = self._feature_vectors.get(dma_id, [])
        return [fv for fv in vectors if start_time <= fv.timestamp <= end_time]
    
    def get_feature_series(
        self,
        dma_id: str,
        feature_name: str,
        hours: int = 24
    ) -> List[Tuple[datetime, float]]:
        """Get time series of a specific feature."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        vectors = self._feature_vectors.get(dma_id, [])
        
        series = []
        for fv in vectors:
            if fv.timestamp > cutoff:
                value = getattr(fv, feature_name, None)
                if value is not None:
                    series.append((fv.timestamp, value))
        
        return sorted(series, key=lambda x: x[0])
    
    # =========================================================================
    # BASELINE MANAGEMENT
    # =========================================================================
    
    def set_baseline(self, dma_id: str, baselines: Dict[str, float]):
        """Set baseline values for a DMA."""
        with self._lock:
            self._baselines[dma_id] = baselines
            logger.info(f"Baseline set for {dma_id}: {baselines}")
    
    def update_baseline_from_history(self, dma_id: str, days: int = 7):
        """Update baseline from historical data."""
        with self._lock:
            import statistics
            
            # Get historical data
            cutoff = datetime.utcnow() - timedelta(days=days)
            vectors = [fv for fv in self._feature_vectors.get(dma_id, []) 
                      if fv.timestamp > cutoff and fv.data_quality == DataQuality.GOOD]
            
            if not vectors:
                return
            
            # Calculate baselines
            pressure_values = [fv.pressure_bar for fv in vectors]
            flow_values = [fv.flow_m3_h for fv in vectors]
            mnf_values = [fv.flow_m3_h for fv in vectors if fv.is_night]
            
            self._baselines[dma_id] = {
                'pressure': statistics.mean(pressure_values) if pressure_values else 3.0,
                'flow': statistics.mean(flow_values) if flow_values else 50.0,
                'mnf': statistics.mean(mnf_values) if mnf_values else 10.0
            }
            
            logger.info(f"Baseline updated for {dma_id} from {len(vectors)} samples")
    
    # =========================================================================
    # SUBSCRIPTION MECHANISM
    # =========================================================================
    
    def subscribe(self, callback: callable):
        """Subscribe to feature updates."""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: callable):
        """Unsubscribe from feature updates."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, dma_id: str, feature_vector: FeatureVector):
        """Notify subscribers of new feature vector."""
        for callback in self._subscribers:
            try:
                callback(dma_id, feature_vector)
            except Exception as e:
                logger.error(f"Subscriber notification error: {e}")
    
    # =========================================================================
    # DATA QUALITY & FRESHNESS
    # =========================================================================
    
    def check_freshness(self, dma_id: str) -> Dict[str, Any]:
        """Check data freshness for a DMA."""
        latest = self._latest.get(dma_id)
        
        if not latest:
            return {
                'dma_id': dma_id,
                'status': 'no_data',
                'stale': True,
                'last_update': None,
                'age_minutes': None
            }
        
        age = datetime.utcnow() - latest.timestamp
        age_minutes = age.total_seconds() / 60
        stale = age_minutes > self.config.stale_threshold_minutes
        
        return {
            'dma_id': dma_id,
            'status': 'stale' if stale else 'fresh',
            'stale': stale,
            'last_update': latest.timestamp.isoformat(),
            'age_minutes': age_minutes,
            'data_quality': latest.data_quality.value,
            'completeness_percent': latest.completeness_percent
        }
    
    def check_all_freshness(self) -> Dict[str, Dict]:
        """Check freshness for all DMAs."""
        return {dma_id: self.check_freshness(dma_id) for dma_id in self._latest.keys()}
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def save_to_disk(self):
        """Persist feature store to disk."""
        with self._lock:
            data = {
                'baselines': self._baselines,
                'latest': {k: v.to_dict() for k, v in self._latest.items()},
                'config': {
                    'version': self.config.current_version,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            filepath = Path(self.config.storage_path) / 'feature_store.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Feature store saved to {filepath}")
    
    def load_from_disk(self):
        """Load feature store from disk."""
        filepath = Path(self.config.storage_path) / 'feature_store.json'
        
        if not filepath.exists():
            logger.info("No feature store file found, starting fresh")
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self._baselines = data.get('baselines', {})
            logger.info(f"Feature store loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load feature store: {e}")
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feature store statistics."""
        total_readings = sum(len(v) for v in self._raw_readings.values())
        total_vectors = sum(len(v) for v in self._feature_vectors.values())
        
        return {
            'dmas_tracked': len(self._latest),
            'total_raw_readings': total_readings,
            'total_feature_vectors': total_vectors,
            'baselines_configured': len(self._baselines),
            'subscribers': len(self._subscribers),
            'config': {
                'version': self.config.current_version,
                'max_history_hours': self.config.max_history_hours,
                'timestamp_resolution_minutes': self.config.timestamp_resolution_minutes
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_feature_store: Optional[FeatureStore] = None


def get_feature_store() -> FeatureStore:
    """Get the global feature store instance."""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
        _feature_store.load_from_disk()
    return _feature_store


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def ingest_reading(dma_id: str, sensor_id: str, timestamp: datetime, **kwargs) -> str:
    """Convenience function to ingest a reading."""
    return get_feature_store().ingest_reading(dma_id, sensor_id, timestamp, **kwargs)


def get_latest_features(dma_id: str) -> Optional[FeatureVector]:
    """Convenience function to get latest features."""
    return get_feature_store().get_latest(dma_id)


def get_all_latest_features() -> Dict[str, FeatureVector]:
    """Convenience function to get all latest features."""
    return get_feature_store().get_latest_all()


if __name__ == "__main__":
    # Demo
    print("=" * 60)
    print("FEATURE STORE DEMO")
    print("=" * 60)
    
    store = FeatureStore()
    
    # Set baselines
    store.set_baseline("DMA001", {'pressure': 3.0, 'flow': 50.0, 'mnf': 10.0})
    
    # Ingest readings
    for i in range(10):
        ts = datetime.utcnow() - timedelta(minutes=15*i)
        store.ingest_reading(
            dma_id="DMA001",
            sensor_id="SENSOR001",
            timestamp=ts,
            pressure=3.0 + (i * 0.1),
            flow=50.0 + (i * 2),
            noise_level=35.0 + i
        )
    
    # Get latest
    latest = store.get_latest("DMA001")
    print(f"\nLatest features for DMA001:")
    print(f"  Pressure: {latest.pressure_bar} bar")
    print(f"  Flow: {latest.flow_m3_h} m³/h")
    print(f"  Quality: {latest.data_quality.value}")
    
    # Check freshness
    freshness = store.check_freshness("DMA001")
    print(f"\nFreshness: {freshness}")
    
    # Stats
    stats = store.get_stats()
    print(f"\nStats: {stats}")
