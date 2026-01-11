"""
AquaWatch Advanced Acoustic Analysis
====================================
Xylem-inspired acoustic leak detection with spectral analysis, ML classification,
and precise leak localization using time-difference-of-arrival (TDOA).

Features:
- Real-time acoustic signal processing
- Spectral frequency analysis
- Machine learning leak classification
- TDOA-based leak localization
- Background noise filtering
- Leak severity estimation
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq


class LeakType(Enum):
    """Types of leaks based on acoustic signature"""
    PINHOLE = "pinhole"          # Small hole, high frequency
    CRACK = "crack"              # Linear crack, medium frequency
    JOINT = "joint"              # Joint failure, variable
    CORROSION = "corrosion"      # Corrosion hole, low-mid frequency
    BURST = "burst"              # Major rupture, broadband
    FITTING = "fitting"          # Fitting leak, medium-high frequency
    VALVE = "valve"              # Valve leak, characteristic pattern
    SERVICE_LINE = "service"     # Service line leak, high frequency


class LeakSeverity(Enum):
    """Leak severity based on acoustic analysis"""
    MINOR = "minor"           # < 0.5 L/s
    MODERATE = "moderate"     # 0.5-2 L/s
    SIGNIFICANT = "significant"  # 2-10 L/s
    SEVERE = "severe"         # 10-50 L/s
    CATASTROPHIC = "catastrophic"  # > 50 L/s


@dataclass
class AcousticSensor:
    """Represents an acoustic sensor in the network"""
    sensor_id: str
    name: str
    latitude: float
    longitude: float
    pipe_id: str
    pipe_material: str
    pipe_diameter: float  # mm
    installed_at: datetime = field(default_factory=datetime.now)
    
    # Calibration
    sensitivity: float = -30.0  # dB
    frequency_range: Tuple[int, int] = (20, 2000)  # Hz
    sampling_rate: int = 8000  # Hz
    
    # Status
    is_active: bool = True
    last_reading: Optional[datetime] = None
    battery_level: float = 100.0
    
    # Noise baseline
    noise_baseline: Optional[np.ndarray] = None
    noise_floor_db: float = -50.0


@dataclass
class AcousticSignature:
    """Acoustic signature of a detected leak"""
    signature_id: str
    sensor_id: str
    timestamp: datetime
    
    # Raw signal characteristics
    peak_frequency: float  # Hz
    dominant_frequencies: List[float]
    spectral_centroid: float
    spectral_bandwidth: float
    rms_amplitude: float  # dB
    
    # Time-domain features
    zero_crossing_rate: float
    peak_to_peak: float
    crest_factor: float
    
    # Classification
    leak_type: LeakType
    confidence: float
    estimated_flow_rate: float  # L/s
    severity: LeakSeverity
    
    # Raw data reference
    sample_rate: int = 8000
    duration_seconds: float = 10.0


@dataclass
class LocalizationResult:
    """Result of leak localization"""
    leak_id: str
    method: str  # tdoa, correlation, triangulation
    
    # Location
    latitude: float
    longitude: float
    distance_from_sensor: float  # meters
    pipe_id: str
    
    # Accuracy
    confidence: float
    position_error_m: float  # estimated error in meters
    
    # Supporting data
    sensors_used: List[str]
    time_delays: Dict[str, float]  # sensor_id -> delay in seconds


class AcousticSignalProcessor:
    """Processes acoustic signals for leak detection"""
    
    def __init__(self, sample_rate: int = 8000):
        self.sample_rate = sample_rate
        
        # Leak frequency characteristics by pipe material
        self.material_frequencies = {
            "PVC": (300, 800),       # Hz range
            "HDPE": (200, 600),
            "Ductile Iron": (100, 500),
            "Steel": (150, 700),
            "Cast Iron": (100, 400),
            "Asbestos Cement": (80, 350),
            "Concrete": (50, 300)
        }
        
        # Leak type frequency signatures
        self.leak_signatures = {
            LeakType.PINHOLE: {"freq_range": (500, 1500), "pattern": "continuous"},
            LeakType.CRACK: {"freq_range": (200, 800), "pattern": "continuous"},
            LeakType.JOINT: {"freq_range": (150, 600), "pattern": "intermittent"},
            LeakType.CORROSION: {"freq_range": (100, 500), "pattern": "irregular"},
            LeakType.BURST: {"freq_range": (50, 2000), "pattern": "broadband"},
            LeakType.FITTING: {"freq_range": (400, 1000), "pattern": "continuous"},
            LeakType.VALVE: {"freq_range": (200, 700), "pattern": "characteristic"},
            LeakType.SERVICE_LINE: {"freq_range": (600, 1500), "pattern": "continuous"}
        }
    
    def process_signal(self, audio_data: np.ndarray, sensor: AcousticSensor) -> Dict:
        """
        Process raw acoustic signal and extract features.
        
        Args:
            audio_data: Raw audio samples (1D numpy array)
            sensor: Sensor that captured the signal
        
        Returns:
            Dictionary of extracted features
        """
        # Ensure signal is numpy array
        audio_data = np.array(audio_data, dtype=np.float64)
        
        # Normalize
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Apply bandpass filter for pipe material
        freq_range = self.material_frequencies.get(sensor.pipe_material, (100, 1000))
        filtered_signal = self._bandpass_filter(audio_data, freq_range[0], freq_range[1])
        
        # Remove background noise if baseline available
        if sensor.noise_baseline is not None:
            filtered_signal = self._subtract_noise(filtered_signal, sensor.noise_baseline)
        
        # Extract features
        features = {
            "time_domain": self._extract_time_features(filtered_signal),
            "frequency_domain": self._extract_frequency_features(filtered_signal),
            "spectral": self._extract_spectral_features(filtered_signal)
        }
        
        return features
    
    def _bandpass_filter(self, signal: np.ndarray, low_freq: float, high_freq: float) -> np.ndarray:
        """Apply bandpass filter to signal"""
        nyquist = self.sample_rate / 2
        low = max(low_freq / nyquist, 0.01)
        high = min(high_freq / nyquist, 0.99)
        
        try:
            b, a = scipy_signal.butter(4, [low, high], btype='band')
            return scipy_signal.filtfilt(b, a, signal)
        except Exception:
            return signal
    
    def _subtract_noise(self, signal: np.ndarray, noise_baseline: np.ndarray) -> np.ndarray:
        """Subtract noise baseline from signal"""
        # Spectral subtraction
        signal_fft = fft(signal)
        noise_fft = fft(noise_baseline[:len(signal)])
        
        # Subtract noise spectrum (with floor to avoid negative values)
        cleaned_fft = np.maximum(np.abs(signal_fft) - 0.5 * np.abs(noise_fft), 0.1)
        cleaned_signal = np.real(np.fft.ifft(cleaned_fft * np.exp(1j * np.angle(signal_fft))))
        
        return cleaned_signal
    
    def _extract_time_features(self, signal: np.ndarray) -> Dict:
        """Extract time-domain features"""
        return {
            "rms": float(np.sqrt(np.mean(signal ** 2))),
            "peak_to_peak": float(np.max(signal) - np.min(signal)),
            "crest_factor": float(np.max(np.abs(signal)) / np.sqrt(np.mean(signal ** 2)) if np.mean(signal ** 2) > 0 else 0),
            "zero_crossing_rate": float(np.sum(np.diff(np.sign(signal)) != 0) / len(signal)),
            "variance": float(np.var(signal)),
            "skewness": float(self._skewness(signal)),
            "kurtosis": float(self._kurtosis(signal))
        }
    
    def _extract_frequency_features(self, signal: np.ndarray) -> Dict:
        """Extract frequency-domain features"""
        # FFT
        n = len(signal)
        fft_vals = fft(signal)
        fft_magnitude = np.abs(fft_vals[:n // 2])
        frequencies = fftfreq(n, 1 / self.sample_rate)[:n // 2]
        
        # Find peaks
        peak_indices = self._find_peaks(fft_magnitude, min_height=np.mean(fft_magnitude))
        
        if len(peak_indices) > 0:
            peak_frequencies = frequencies[peak_indices]
            peak_magnitudes = fft_magnitude[peak_indices]
            
            # Sort by magnitude
            sorted_indices = np.argsort(peak_magnitudes)[::-1]
            dominant_frequencies = peak_frequencies[sorted_indices[:5]].tolist()
            peak_frequency = float(dominant_frequencies[0]) if dominant_frequencies else 0
        else:
            dominant_frequencies = []
            peak_frequency = 0
        
        return {
            "peak_frequency": peak_frequency,
            "dominant_frequencies": dominant_frequencies,
            "mean_frequency": float(np.sum(frequencies * fft_magnitude) / np.sum(fft_magnitude)) if np.sum(fft_magnitude) > 0 else 0,
            "frequency_std": float(np.sqrt(np.sum(((frequencies - np.mean(frequencies)) ** 2) * fft_magnitude) / np.sum(fft_magnitude))) if np.sum(fft_magnitude) > 0 else 0
        }
    
    def _extract_spectral_features(self, signal: np.ndarray) -> Dict:
        """Extract spectral features"""
        n = len(signal)
        fft_vals = fft(signal)
        fft_magnitude = np.abs(fft_vals[:n // 2])
        frequencies = fftfreq(n, 1 / self.sample_rate)[:n // 2]
        
        # Normalize magnitude
        magnitude_sum = np.sum(fft_magnitude)
        if magnitude_sum > 0:
            normalized_magnitude = fft_magnitude / magnitude_sum
        else:
            normalized_magnitude = fft_magnitude
        
        # Spectral centroid
        spectral_centroid = np.sum(frequencies * normalized_magnitude)
        
        # Spectral bandwidth
        spectral_bandwidth = np.sqrt(np.sum(((frequencies - spectral_centroid) ** 2) * normalized_magnitude))
        
        # Spectral rolloff (frequency below which 85% of energy is contained)
        cumsum = np.cumsum(fft_magnitude)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1]) if len(cumsum) > 0 else 0
        spectral_rolloff = frequencies[min(rolloff_idx, len(frequencies) - 1)]
        
        # Spectral flatness (measure of noisiness)
        geometric_mean = np.exp(np.mean(np.log(fft_magnitude + 1e-10)))
        arithmetic_mean = np.mean(fft_magnitude)
        spectral_flatness = geometric_mean / arithmetic_mean if arithmetic_mean > 0 else 0
        
        return {
            "spectral_centroid": float(spectral_centroid),
            "spectral_bandwidth": float(spectral_bandwidth),
            "spectral_rolloff": float(spectral_rolloff),
            "spectral_flatness": float(spectral_flatness)
        }
    
    def _find_peaks(self, signal: np.ndarray, min_height: float = 0) -> np.ndarray:
        """Find peaks in signal"""
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1] and signal[i] > min_height:
                peaks.append(i)
        return np.array(peaks)
    
    def _skewness(self, signal: np.ndarray) -> float:
        """Calculate skewness of signal"""
        mean = np.mean(signal)
        std = np.std(signal)
        if std == 0:
            return 0
        return np.mean(((signal - mean) / std) ** 3)
    
    def _kurtosis(self, signal: np.ndarray) -> float:
        """Calculate kurtosis of signal"""
        mean = np.mean(signal)
        std = np.std(signal)
        if std == 0:
            return 0
        return np.mean(((signal - mean) / std) ** 4) - 3


class LeakClassifier:
    """Machine learning-based leak classifier"""
    
    def __init__(self):
        # Classification thresholds and patterns
        self.classification_rules = {
            LeakType.PINHOLE: {
                "peak_freq_range": (500, 1500),
                "spectral_centroid_range": (600, 1200),
                "crest_factor_range": (3, 10),
                "severity_multiplier": 0.3
            },
            LeakType.CRACK: {
                "peak_freq_range": (200, 800),
                "spectral_centroid_range": (300, 700),
                "crest_factor_range": (2, 6),
                "severity_multiplier": 0.6
            },
            LeakType.JOINT: {
                "peak_freq_range": (150, 600),
                "spectral_centroid_range": (200, 500),
                "crest_factor_range": (2, 8),
                "severity_multiplier": 0.5
            },
            LeakType.BURST: {
                "peak_freq_range": (50, 2000),
                "spectral_flatness_min": 0.3,
                "rms_min": 0.5,
                "severity_multiplier": 2.0
            },
            LeakType.VALVE: {
                "peak_freq_range": (200, 700),
                "harmonic_pattern": True,
                "severity_multiplier": 0.4
            },
            LeakType.SERVICE_LINE: {
                "peak_freq_range": (600, 1500),
                "spectral_centroid_range": (700, 1300),
                "severity_multiplier": 0.4
            }
        }
        
        # Flow rate estimation based on acoustic amplitude
        self.flow_coefficients = {
            LeakType.PINHOLE: 0.05,      # L/s per dB above threshold
            LeakType.CRACK: 0.15,
            LeakType.JOINT: 0.10,
            LeakType.CORROSION: 0.08,
            LeakType.BURST: 0.50,
            LeakType.FITTING: 0.06,
            LeakType.VALVE: 0.08,
            LeakType.SERVICE_LINE: 0.04
        }
    
    def classify(self, features: Dict, pipe_diameter: float, pressure: float = 3.0) -> Dict:
        """
        Classify leak type and estimate severity.
        
        Args:
            features: Extracted acoustic features
            pipe_diameter: Pipe diameter in mm
            pressure: Operating pressure in bar
        
        Returns:
            Classification result with type, confidence, and severity
        """
        # Score each leak type
        scores = {}
        
        freq_features = features.get("frequency_domain", {})
        spectral_features = features.get("spectral", {})
        time_features = features.get("time_domain", {})
        
        peak_freq = freq_features.get("peak_frequency", 0)
        centroid = spectral_features.get("spectral_centroid", 0)
        flatness = spectral_features.get("spectral_flatness", 0)
        rms = time_features.get("rms", 0)
        crest = time_features.get("crest_factor", 0)
        
        for leak_type, rules in self.classification_rules.items():
            score = 0
            max_score = 0
            
            # Check frequency range
            if "peak_freq_range" in rules:
                max_score += 1
                low, high = rules["peak_freq_range"]
                if low <= peak_freq <= high:
                    score += 1
                elif peak_freq > 0:
                    # Partial match
                    distance = min(abs(peak_freq - low), abs(peak_freq - high))
                    score += max(0, 1 - distance / 500)
            
            # Check spectral centroid
            if "spectral_centroid_range" in rules:
                max_score += 1
                low, high = rules["spectral_centroid_range"]
                if low <= centroid <= high:
                    score += 1
                elif centroid > 0:
                    distance = min(abs(centroid - low), abs(centroid - high))
                    score += max(0, 1 - distance / 500)
            
            # Check crest factor
            if "crest_factor_range" in rules:
                max_score += 1
                low, high = rules["crest_factor_range"]
                if low <= crest <= high:
                    score += 1
            
            # Check spectral flatness (for burst detection)
            if "spectral_flatness_min" in rules:
                max_score += 1
                if flatness >= rules["spectral_flatness_min"]:
                    score += 1
            
            # Check RMS amplitude
            if "rms_min" in rules:
                max_score += 1
                if rms >= rules["rms_min"]:
                    score += 1
            
            scores[leak_type] = score / max_score if max_score > 0 else 0
        
        # Get best classification
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        # Estimate flow rate
        flow_rate = self._estimate_flow_rate(
            best_type, rms, pipe_diameter, pressure
        )
        
        # Determine severity
        severity = self._determine_severity(flow_rate)
        
        return {
            "leak_type": best_type,
            "confidence": confidence,
            "all_scores": {lt.value: s for lt, s in scores.items()},
            "estimated_flow_rate": flow_rate,
            "severity": severity,
            "features_summary": {
                "peak_frequency": peak_freq,
                "spectral_centroid": centroid,
                "rms_amplitude": rms,
                "crest_factor": crest
            }
        }
    
    def _estimate_flow_rate(
        self,
        leak_type: LeakType,
        rms: float,
        diameter: float,
        pressure: float
    ) -> float:
        """Estimate leak flow rate in L/s"""
        # Base coefficient
        coef = self.flow_coefficients.get(leak_type, 0.1)
        
        # Adjust for pipe diameter (larger pipes = potentially larger leaks)
        diameter_factor = (diameter / 100) ** 0.5
        
        # Adjust for pressure (higher pressure = higher flow)
        pressure_factor = (pressure / 3.0) ** 0.5
        
        # Calculate flow rate
        # RMS is normalized 0-1, convert to effective dB above threshold
        effective_amplitude = max(0, rms * 50)  # Assume 50dB range
        
        flow_rate = coef * effective_amplitude * diameter_factor * pressure_factor
        
        return max(0.01, min(flow_rate, 100))  # Clamp between 0.01 and 100 L/s
    
    def _determine_severity(self, flow_rate: float) -> LeakSeverity:
        """Determine leak severity from flow rate"""
        if flow_rate < 0.5:
            return LeakSeverity.MINOR
        elif flow_rate < 2:
            return LeakSeverity.MODERATE
        elif flow_rate < 10:
            return LeakSeverity.SIGNIFICANT
        elif flow_rate < 50:
            return LeakSeverity.SEVERE
        else:
            return LeakSeverity.CATASTROPHIC


class LeakLocalizer:
    """Localize leaks using TDOA and correlation methods"""
    
    def __init__(self):
        # Sound velocity in water-filled pipes by material (m/s)
        self.sound_velocities = {
            "PVC": 400,
            "HDPE": 350,
            "Ductile Iron": 1200,
            "Steel": 1500,
            "Cast Iron": 1100,
            "Asbestos Cement": 900,
            "Concrete": 1000
        }
    
    def localize_tdoa(
        self,
        signals: Dict[str, np.ndarray],
        sensors: Dict[str, AcousticSensor],
        pipe_material: str
    ) -> LocalizationResult:
        """
        Localize leak using Time Difference of Arrival.
        
        Args:
            signals: Dict of sensor_id -> signal array
            sensors: Dict of sensor_id -> AcousticSensor
            pipe_material: Pipe material for sound velocity
        
        Returns:
            LocalizationResult with estimated leak position
        """
        if len(signals) < 2:
            raise ValueError("Need at least 2 sensors for TDOA localization")
        
        sensor_ids = list(signals.keys())
        sound_velocity = self.sound_velocities.get(pipe_material, 500)
        
        # Calculate cross-correlation between sensor pairs
        time_delays = {}
        correlations = []
        
        for i in range(len(sensor_ids)):
            for j in range(i + 1, len(sensor_ids)):
                sensor1 = sensor_ids[i]
                sensor2 = sensor_ids[j]
                
                # Cross-correlation
                corr = np.correlate(signals[sensor1], signals[sensor2], mode='full')
                
                # Find peak (time delay)
                peak_idx = np.argmax(np.abs(corr))
                center_idx = len(signals[sensor1]) - 1
                
                # Convert to time delay
                sample_rate = sensors[sensor1].sampling_rate
                delay_samples = peak_idx - center_idx
                delay_seconds = delay_samples / sample_rate
                
                time_delays[f"{sensor1}_{sensor2}"] = delay_seconds
                correlations.append({
                    "sensors": (sensor1, sensor2),
                    "delay": delay_seconds,
                    "correlation_strength": float(np.max(np.abs(corr)))
                })
        
        # Calculate leak position on pipe between sensors
        # For simplicity, assume linear pipe between first two sensors
        sensor1 = sensors[sensor_ids[0]]
        sensor2 = sensors[sensor_ids[1]]
        
        # Distance between sensors (using coordinates)
        distance = self._calculate_distance(
            (sensor1.latitude, sensor1.longitude),
            (sensor2.latitude, sensor2.longitude)
        ) * 1000  # km to meters
        
        # Time delay
        delay = list(time_delays.values())[0]
        
        # Distance from sensor1 to leak
        # d1 - d2 = v * delay
        # d1 + d2 = total_distance
        # Solving: d1 = (total_distance + v * delay) / 2
        distance_from_s1 = (distance + sound_velocity * delay) / 2
        distance_from_s1 = max(0, min(distance_from_s1, distance))  # Clamp
        
        # Interpolate position
        ratio = distance_from_s1 / distance if distance > 0 else 0.5
        leak_lat = sensor1.latitude + ratio * (sensor2.latitude - sensor1.latitude)
        leak_lon = sensor1.longitude + ratio * (sensor2.longitude - sensor1.longitude)
        
        # Estimate accuracy based on correlation strength
        avg_correlation = np.mean([c["correlation_strength"] for c in correlations])
        position_error = max(1, 20 * (1 - min(avg_correlation / 1000, 1)))  # meters
        
        return LocalizationResult(
            leak_id=f"LEAK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            method="tdoa",
            latitude=leak_lat,
            longitude=leak_lon,
            distance_from_sensor=distance_from_s1,
            pipe_id=sensor1.pipe_id,
            confidence=min(avg_correlation / 1000, 0.95),
            position_error_m=position_error,
            sensors_used=sensor_ids,
            time_delays=time_delays
        )
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between coordinates in km"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Earth radius in km
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c


class AcousticAnalysisSystem:
    """
    Complete acoustic analysis system for leak detection.
    Integrates signal processing, classification, and localization.
    """
    
    def __init__(self):
        self.processor = AcousticSignalProcessor()
        self.classifier = LeakClassifier()
        self.localizer = LeakLocalizer()
        
        self.sensors: Dict[str, AcousticSensor] = {}
        self.detections: List[AcousticSignature] = []
        self.localizations: List[LocalizationResult] = []
        
        # Initialize demo sensors
        self._initialize_demo_sensors()
    
    def _initialize_demo_sensors(self):
        """Initialize demo acoustic sensors for Lusaka network"""
        sensors_data = [
            ("AC_CBD_01", "CBD Main Acoustic", -15.4167, 28.2833, "P_IOLANDA_CBD", "Ductile Iron", 600),
            ("AC_CBD_02", "CBD Secondary", -15.4200, 28.2850, "P_CBD_RHODES", "Ductile Iron", 350),
            ("AC_KAB_01", "Kabulonga Main", -15.3958, 28.3208, "P_CHELSTONE_KAB", "PVC", 400),
            ("AC_KAB_02", "Kabulonga Secondary", -15.4000, 28.3150, "P_KAB_RHODES", "PVC", 300),
            ("AC_KAM_01", "Kamwala Main", -15.4292, 28.2708, "P_CBD_KAMWALA", "Steel", 300),
            ("AC_KAM_02", "Kamwala Industrial", -15.4350, 28.2670, "P_KAMWALA_IND", "Steel", 400),
            ("AC_WOD_01", "Woodlands Main", -15.4250, 28.3083, "P_RHODES_WOOD", "PVC", 250),
            ("AC_CHI_01", "Chilenje Main", -15.4458, 28.2792, "P_KABWATA_CHILENJE", "PVC", 200),
        ]
        
        for sensor_data in sensors_data:
            sid, name, lat, lon, pipe, material, diameter = sensor_data
            self.sensors[sid] = AcousticSensor(
                sensor_id=sid,
                name=name,
                latitude=lat,
                longitude=lon,
                pipe_id=pipe,
                pipe_material=material,
                pipe_diameter=diameter
            )
    
    def analyze_signal(
        self,
        sensor_id: str,
        audio_data: np.ndarray,
        pressure: float = 3.0
    ) -> Optional[AcousticSignature]:
        """
        Analyze acoustic signal for leak detection.
        
        Args:
            sensor_id: ID of the capturing sensor
            audio_data: Raw audio samples
            pressure: Operating pressure in bar
        
        Returns:
            AcousticSignature if leak detected, None otherwise
        """
        if sensor_id not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_id}")
        
        sensor = self.sensors[sensor_id]
        
        # Process signal
        features = self.processor.process_signal(audio_data, sensor)
        
        # Classify
        classification = self.classifier.classify(
            features,
            sensor.pipe_diameter,
            pressure
        )
        
        # Only create signature if confidence is high enough
        if classification["confidence"] < 0.5:
            return None
        
        # Create signature
        signature = AcousticSignature(
            signature_id=f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sensor_id}",
            sensor_id=sensor_id,
            timestamp=datetime.now(),
            peak_frequency=features["frequency_domain"]["peak_frequency"],
            dominant_frequencies=features["frequency_domain"]["dominant_frequencies"],
            spectral_centroid=features["spectral"]["spectral_centroid"],
            spectral_bandwidth=features["spectral"]["spectral_bandwidth"],
            rms_amplitude=features["time_domain"]["rms"],
            zero_crossing_rate=features["time_domain"]["zero_crossing_rate"],
            peak_to_peak=features["time_domain"]["peak_to_peak"],
            crest_factor=features["time_domain"]["crest_factor"],
            leak_type=classification["leak_type"],
            confidence=classification["confidence"],
            estimated_flow_rate=classification["estimated_flow_rate"],
            severity=classification["severity"]
        )
        
        self.detections.append(signature)
        
        return signature
    
    def localize_leak(
        self,
        sensor_ids: List[str],
        signals: Dict[str, np.ndarray]
    ) -> LocalizationResult:
        """
        Localize a detected leak using multiple sensors.
        
        Args:
            sensor_ids: List of sensor IDs to use
            signals: Dict of sensor_id -> audio signal
        
        Returns:
            LocalizationResult with estimated position
        """
        sensors = {sid: self.sensors[sid] for sid in sensor_ids if sid in self.sensors}
        
        # Get pipe material from first sensor
        first_sensor = list(sensors.values())[0]
        pipe_material = first_sensor.pipe_material
        
        result = self.localizer.localize_tdoa(signals, sensors, pipe_material)
        self.localizations.append(result)
        
        return result
    
    def get_detection_summary(self) -> Dict:
        """Get summary of all detections"""
        if not self.detections:
            return {"total_detections": 0}
        
        return {
            "total_detections": len(self.detections),
            "by_type": {
                lt.value: len([d for d in self.detections if d.leak_type == lt])
                for lt in LeakType
            },
            "by_severity": {
                s.value: len([d for d in self.detections if d.severity == s])
                for s in LeakSeverity
            },
            "total_estimated_flow_lps": sum(d.estimated_flow_rate for d in self.detections),
            "avg_confidence": np.mean([d.confidence for d in self.detections]),
            "sensors_active": len([s for s in self.sensors.values() if s.is_active]),
            "recent_detections": [
                {
                    "signature_id": d.signature_id,
                    "sensor_id": d.sensor_id,
                    "leak_type": d.leak_type.value,
                    "severity": d.severity.value,
                    "flow_rate": d.estimated_flow_rate,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in sorted(self.detections, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }
    
    def generate_demo_detection(self) -> AcousticSignature:
        """Generate a demo detection for testing"""
        # Create synthetic leak signal
        duration = 10  # seconds
        sample_rate = 8000
        t = np.linspace(0, duration, duration * sample_rate)
        
        # Simulate leak sound (mix of frequencies)
        leak_freq = np.random.uniform(300, 800)
        signal = (
            0.5 * np.sin(2 * np.pi * leak_freq * t) +
            0.3 * np.sin(2 * np.pi * leak_freq * 2 * t) +  # Harmonic
            0.2 * np.random.randn(len(t))  # Noise
        )
        
        # Pick random sensor
        sensor_id = np.random.choice(list(self.sensors.keys()))
        
        return self.analyze_signal(sensor_id, signal, pressure=3.5)


# Global instance
acoustic_system = AcousticAnalysisSystem()


def get_acoustic_system() -> AcousticAnalysisSystem:
    """Get the global acoustic analysis system"""
    return acoustic_system


if __name__ == "__main__":
    # Demo
    system = AcousticAnalysisSystem()
    
    print("=" * 60)
    print("AquaWatch Advanced Acoustic Analysis")
    print("=" * 60)
    
    # Generate demo detections
    print("\nGenerating demo leak detections...")
    
    for i in range(5):
        detection = system.generate_demo_detection()
        if detection:
            print(f"\nDetection {i+1}:")
            print(f"  Sensor: {detection.sensor_id}")
            print(f"  Leak Type: {detection.leak_type.value}")
            print(f"  Severity: {detection.severity.value}")
            print(f"  Flow Rate: {detection.estimated_flow_rate:.2f} L/s")
            print(f"  Confidence: {detection.confidence:.1%}")
            print(f"  Peak Frequency: {detection.peak_frequency:.0f} Hz")
    
    # Summary
    summary = system.get_detection_summary()
    print(f"\n{'='*60}")
    print("Detection Summary:")
    print(f"  Total Detections: {summary['total_detections']}")
    print(f"  Total Estimated Flow: {summary['total_estimated_flow_lps']:.2f} L/s")
    print(f"  Average Confidence: {summary['avg_confidence']:.1%}")
    print(f"  Active Sensors: {summary['sensors_active']}")
