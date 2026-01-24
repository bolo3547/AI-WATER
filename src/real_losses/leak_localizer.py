"""
AquaWatch NRW - Leak Localizer
==============================

Pressure-gradient based leak localization system.

Method:
1. Collect pressure readings from multiple sensors in a DMA
2. Compare against baseline pressures
3. Calculate deviation vectors for each sensor
4. Use weighted centroid method to estimate leak location
5. Provide zone hints and confidence scores

Accuracy depends on:
- Number of sensors
- Sensor placement geometry
- Baseline accuracy
- Network topology
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import math

logger = logging.getLogger(__name__)


@dataclass
class SensorLocation:
    """Sensor with GPS coordinates"""
    sensor_id: str
    name: str
    lat: float
    lng: float
    dma_id: str
    baseline_pressure_bar: float = 3.0
    current_pressure_bar: float = 0.0
    deviation_bar: float = 0.0


@dataclass
class LeakLocationEstimate:
    """Estimated leak location"""
    estimate_id: str
    tenant_id: str
    dma_id: str
    incident_id: Optional[str] = None
    
    # Location estimate
    estimated_lat: float = 0.0
    estimated_lng: float = 0.0
    
    # Confidence and accuracy
    confidence: float = 0.0
    estimated_radius_m: float = 0.0  # Uncertainty radius in meters
    
    # Zone information
    zone_hint: str = ""
    nearest_sensors: List[str] = field(default_factory=list)
    
    # Detection signals
    max_deviation_bar: float = 0.0
    max_deviation_sensor: str = ""
    sensors_affected: int = 0
    
    # Timestamp
    computed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Method used
    method: str = "pressure_gradient"


class LeakLocalizer:
    """
    Production leak localization engine.
    
    Uses pressure gradient analysis to estimate leak locations
    within a DMA network.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize localizer."""
        self.config = config or {}
        
        # Minimum sensors required for localization
        self.min_sensors = self.config.get('min_sensors', 3)
        
        # Minimum pressure deviation to consider (bar)
        self.min_deviation_bar = self.config.get('min_deviation', 0.3)
        
        # Weighting exponent (higher = more weight to larger deviations)
        self.weight_exponent = self.config.get('weight_exponent', 2)
        
        # Sensor registry
        self._sensors: Dict[str, Dict[str, SensorLocation]] = {}  # dma_id -> {sensor_id -> SensorLocation}
        
        # Location estimates
        self._estimates: Dict[str, List[LeakLocationEstimate]] = {}  # tenant_id -> estimates
        
        logger.info("LeakLocalizer initialized")
    
    def register_sensor(
        self,
        dma_id: str,
        sensor_id: str,
        name: str,
        lat: float,
        lng: float,
        baseline_pressure: float = 3.0
    ):
        """Register a sensor for localization."""
        if dma_id not in self._sensors:
            self._sensors[dma_id] = {}
        
        self._sensors[dma_id][sensor_id] = SensorLocation(
            sensor_id=sensor_id,
            name=name,
            lat=lat,
            lng=lng,
            dma_id=dma_id,
            baseline_pressure_bar=baseline_pressure
        )
        
        logger.debug(f"Registered sensor {sensor_id} at ({lat}, {lng}) for DMA {dma_id}")
    
    def update_sensor_reading(
        self,
        dma_id: str,
        sensor_id: str,
        current_pressure: float
    ):
        """Update current pressure reading for a sensor."""
        if dma_id not in self._sensors:
            return
        if sensor_id not in self._sensors[dma_id]:
            return
        
        sensor = self._sensors[dma_id][sensor_id]
        sensor.current_pressure_bar = current_pressure
        sensor.deviation_bar = sensor.baseline_pressure_bar - current_pressure
    
    def update_baseline(
        self,
        dma_id: str,
        sensor_id: str,
        baseline_pressure: float
    ):
        """Update baseline pressure for a sensor."""
        if dma_id in self._sensors and sensor_id in self._sensors[dma_id]:
            self._sensors[dma_id][sensor_id].baseline_pressure_bar = baseline_pressure
    
    def localize_leak(
        self,
        tenant_id: str,
        dma_id: str,
        incident_id: Optional[str] = None
    ) -> Optional[LeakLocationEstimate]:
        """
        Estimate leak location using pressure gradient method.
        
        Args:
            tenant_id: Tenant identifier
            dma_id: DMA where leak is suspected
            incident_id: Optional incident reference
            
        Returns:
            LeakLocationEstimate if localization possible, None otherwise
        """
        sensors = self._sensors.get(dma_id, {})
        
        if len(sensors) < self.min_sensors:
            logger.warning(f"Insufficient sensors for localization in {dma_id}: {len(sensors)} < {self.min_sensors}")
            return None
        
        # Filter sensors with significant deviation (pressure DROP)
        affected_sensors = [
            s for s in sensors.values()
            if s.deviation_bar >= self.min_deviation_bar
        ]
        
        if not affected_sensors:
            logger.info(f"No significant pressure deviations in {dma_id}")
            return None
        
        # Use weighted centroid method
        # Weight = deviation ^ exponent (larger drops = closer to leak)
        total_weight = 0
        weighted_lat = 0
        weighted_lng = 0
        max_deviation = 0
        max_deviation_sensor = ""
        
        for sensor in affected_sensors:
            weight = sensor.deviation_bar ** self.weight_exponent
            weighted_lat += sensor.lat * weight
            weighted_lng += sensor.lng * weight
            total_weight += weight
            
            if sensor.deviation_bar > max_deviation:
                max_deviation = sensor.deviation_bar
                max_deviation_sensor = sensor.sensor_id
        
        if total_weight == 0:
            return None
        
        estimated_lat = weighted_lat / total_weight
        estimated_lng = weighted_lng / total_weight
        
        # Calculate confidence and accuracy
        confidence = self._calculate_confidence(affected_sensors, len(sensors))
        radius = self._estimate_accuracy_radius(affected_sensors, estimated_lat, estimated_lng)
        
        # Generate zone hint
        zone_hint = self._generate_zone_hint(affected_sensors, estimated_lat, estimated_lng)
        
        # Get nearest sensors to estimate
        nearest = self._get_nearest_sensors(
            sensors.values(), estimated_lat, estimated_lng, n=3
        )
        
        estimate = LeakLocationEstimate(
            estimate_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dma_id=dma_id,
            incident_id=incident_id,
            estimated_lat=round(estimated_lat, 6),
            estimated_lng=round(estimated_lng, 6),
            confidence=round(confidence, 2),
            estimated_radius_m=round(radius, 0),
            zone_hint=zone_hint,
            nearest_sensors=[s.sensor_id for s in nearest],
            max_deviation_bar=round(max_deviation, 3),
            max_deviation_sensor=max_deviation_sensor,
            sensors_affected=len(affected_sensors),
            computed_at=datetime.utcnow()
        )
        
        # Store estimate
        if tenant_id not in self._estimates:
            self._estimates[tenant_id] = []
        self._estimates[tenant_id].append(estimate)
        
        logger.info(f"Leak localized in {dma_id}: ({estimated_lat:.5f}, {estimated_lng:.5f}) confidence={confidence:.2f}")
        return estimate
    
    def _calculate_confidence(
        self,
        affected_sensors: List[SensorLocation],
        total_sensors: int
    ) -> float:
        """Calculate localization confidence score."""
        base_confidence = 0.3
        
        # More affected sensors = higher confidence
        if len(affected_sensors) >= 5:
            base_confidence += 0.3
        elif len(affected_sensors) >= 3:
            base_confidence += 0.2
        
        # Higher deviations = higher confidence
        max_dev = max(s.deviation_bar for s in affected_sensors)
        if max_dev > 1.0:
            base_confidence += 0.2
        elif max_dev > 0.5:
            base_confidence += 0.1
        
        # Coverage factor
        coverage = len(affected_sensors) / total_sensors
        base_confidence += coverage * 0.1
        
        return min(0.95, base_confidence)
    
    def _estimate_accuracy_radius(
        self,
        sensors: List[SensorLocation],
        est_lat: float,
        est_lng: float
    ) -> float:
        """Estimate accuracy radius in meters."""
        if not sensors:
            return 500  # Default 500m uncertainty
        
        # Calculate average distance from estimate to affected sensors
        distances = []
        for sensor in sensors:
            dist = self._haversine_distance(
                est_lat, est_lng,
                sensor.lat, sensor.lng
            )
            distances.append(dist)
        
        avg_distance = sum(distances) / len(distances) if distances else 500
        
        # Radius is fraction of average sensor distance
        # More sensors and stronger signals = smaller radius
        confidence_factor = 0.3 + (len(sensors) * 0.05)
        radius = avg_distance * (1 - min(0.7, confidence_factor))
        
        return max(50, min(500, radius))  # Clamp between 50m and 500m
    
    def _generate_zone_hint(
        self,
        sensors: List[SensorLocation],
        est_lat: float,
        est_lng: float
    ) -> str:
        """Generate human-readable zone hint."""
        if not sensors:
            return "Unknown location"
        
        # Find two nearest sensors
        nearest = self._get_nearest_sensors(sensors, est_lat, est_lng, n=2)
        
        if len(nearest) >= 2:
            return f"Between {nearest[0].name} and {nearest[1].name}"
        elif len(nearest) == 1:
            return f"Near {nearest[0].name}"
        else:
            return f"Within DMA {sensors[0].dma_id}"
    
    def _get_nearest_sensors(
        self,
        sensors,
        lat: float,
        lng: float,
        n: int = 3
    ) -> List[SensorLocation]:
        """Get n nearest sensors to a point."""
        sensor_list = list(sensors)
        
        def distance_to_point(sensor):
            return self._haversine_distance(lat, lng, sensor.lat, sensor.lng)
        
        sorted_sensors = sorted(sensor_list, key=distance_to_point)
        return sorted_sensors[:n]
    
    def _haversine_distance(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_estimate(
        self,
        tenant_id: str,
        incident_id: str
    ) -> Optional[LeakLocationEstimate]:
        """Get location estimate for an incident."""
        estimates = self._estimates.get(tenant_id, [])
        for estimate in reversed(estimates):
            if estimate.incident_id == incident_id:
                return estimate
        return None
    
    def get_recent_estimates(
        self,
        tenant_id: str,
        dma_id: Optional[str] = None,
        hours: int = 24
    ) -> List[LeakLocationEstimate]:
        """Get recent location estimates."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        estimates = self._estimates.get(tenant_id, [])
        
        results = []
        for est in estimates:
            if est.computed_at < cutoff:
                continue
            if dma_id and est.dma_id != dma_id:
                continue
            results.append(est)
        
        return sorted(results, key=lambda x: x.computed_at, reverse=True)
    
    def get_sensors_for_dma(self, dma_id: str) -> List[Dict]:
        """Get sensor information for a DMA."""
        sensors = self._sensors.get(dma_id, {})
        return [
            {
                "sensor_id": s.sensor_id,
                "name": s.name,
                "lat": s.lat,
                "lng": s.lng,
                "baseline_pressure": s.baseline_pressure_bar,
                "current_pressure": s.current_pressure_bar,
                "deviation": s.deviation_bar
            }
            for s in sensors.values()
        ]
    
    def get_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get localization summary for dashboard."""
        total_dmas = len(self._sensors)
        total_sensors = sum(len(sensors) for sensors in self._sensors.values())
        
        estimates = self._estimates.get(tenant_id, [])
        recent = self.get_recent_estimates(tenant_id, hours=24)
        
        return {
            "has_data": total_sensors > 0,
            "total_dmas_registered": total_dmas,
            "total_sensors_registered": total_sensors,
            "recent_localizations_24h": len(recent),
            "high_confidence_count": len([e for e in recent if e.confidence >= 0.7]),
            "average_confidence": round(
                sum(e.confidence for e in recent) / len(recent), 2
            ) if recent else 0,
            "last_updated": datetime.utcnow().isoformat()
        }
