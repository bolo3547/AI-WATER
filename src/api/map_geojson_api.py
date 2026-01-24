"""
AQUAWATCH NRW - MAP GEOJSON API
================================

Step 7: Map Intelligence Features

This module provides GeoJSON endpoints for the map visualization:
- GET /tenants/{tenant_id}/map/geojson - Full map data
- GET /tenants/{tenant_id}/map/sensors - Sensor locations
- GET /tenants/{tenant_id}/map/leaks - Leak markers
- GET /tenants/{tenant_id}/map/dmas - DMA polygons with NRW heatmap

Author: AquaWatch AI Team
Version: 3.0.0
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SensorType(str, Enum):
    FLOW = "flow"
    PRESSURE = "pressure"
    ACOUSTIC = "acoustic"
    QUALITY = "quality"


class SensorStatus(str, Enum):
    ONLINE = "online"
    WARNING = "warning"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class LeakSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LeakStatus(str, Enum):
    ACTIVE = "active"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in-progress"
    MONITORING = "monitoring"
    REPAIRED = "repaired"
    VERIFIED = "verified"


class DMAStatus(str, Enum):
    GOOD = "good"
    MODERATE = "moderate"
    WARNING = "warning"
    CRITICAL = "critical"


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature model."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    id: Optional[str] = None


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection model."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
    metadata: Optional[Dict[str, Any]] = None


class MapLayerResponse(BaseModel):
    """Response for individual map layers."""
    layer: str
    geojson: GeoJSONFeatureCollection
    lastUpdated: str
    count: int


class FullMapResponse(BaseModel):
    """Response for full map data."""
    tenantId: str
    layers: Dict[str, GeoJSONFeatureCollection]
    metadata: Dict[str, Any]
    generatedAt: str


# =============================================================================
# SAMPLE DATA GENERATOR
# =============================================================================

class SampleGeoJSONGenerator:
    """
    Generates sample GeoJSON data for development and demo purposes.
    
    Creates realistic DMA polygons, sensor locations, and leak markers
    for the Lusaka water distribution network.
    """
    
    # Lusaka center coordinates
    CENTER_LAT = -15.4167
    CENTER_LNG = 28.2833
    
    # DMA definitions with approximate boundaries
    DMA_DEFINITIONS = [
        {
            "id": "dma-woodlands",
            "name": "Woodlands",
            "center": (-15.385, 28.310),
            "radius_km": 1.8,
            "nrw_percent": 18.5,
            "population": 45000,
            "connections": 8500
        },
        {
            "id": "dma-kabulonga", 
            "name": "Kabulonga",
            "center": (-15.408, 28.332),
            "radius_km": 1.5,
            "nrw_percent": 21.2,
            "population": 38000,
            "connections": 7200
        },
        {
            "id": "dma-roma",
            "name": "Roma",
            "center": (-15.422, 28.298),
            "radius_km": 1.2,
            "nrw_percent": 23.1,
            "population": 28000,
            "connections": 5500
        },
        {
            "id": "dma-matero",
            "name": "Matero",
            "center": (-15.362, 28.278),
            "radius_km": 2.0,
            "nrw_percent": 48.2,
            "population": 85000,
            "connections": 12000
        },
        {
            "id": "dma-chilenje",
            "name": "Chilenje",
            "center": (-15.445, 28.268),
            "radius_km": 1.6,
            "nrw_percent": 45.8,
            "population": 62000,
            "connections": 9800
        },
        {
            "id": "dma-garden",
            "name": "Garden",
            "center": (-15.398, 28.285),
            "radius_km": 1.0,
            "nrw_percent": 42.1,
            "population": 22000,
            "connections": 4200
        },
        {
            "id": "dma-rhodes-park",
            "name": "Rhodes Park",
            "center": (-15.412, 28.305),
            "radius_km": 0.9,
            "nrw_percent": 28.5,
            "population": 18000,
            "connections": 3500
        },
        {
            "id": "dma-olympia",
            "name": "Olympia",
            "center": (-15.438, 28.312),
            "radius_km": 1.1,
            "nrw_percent": 35.2,
            "population": 25000,
            "connections": 4800
        },
        {
            "id": "dma-kabwata",
            "name": "Kabwata",
            "center": (-15.455, 28.285),
            "radius_km": 1.4,
            "nrw_percent": 39.8,
            "population": 48000,
            "connections": 7500
        },
        {
            "id": "dma-mtendere",
            "name": "Mtendere",
            "center": (-15.448, 28.342),
            "radius_km": 1.7,
            "nrw_percent": 52.3,
            "population": 72000,
            "connections": 10500
        },
        {
            "id": "dma-kalingalinga",
            "name": "Kalingalinga",
            "center": (-15.432, 28.355),
            "radius_km": 1.3,
            "nrw_percent": 55.1,
            "population": 58000,
            "connections": 8200
        },
        {
            "id": "dma-chelstone",
            "name": "Chelstone",
            "center": (-15.395, 28.365),
            "radius_km": 2.2,
            "nrw_percent": 41.5,
            "population": 95000,
            "connections": 14000
        }
    ]
    
    # Sensor types distribution per DMA
    SENSORS_PER_DMA = {
        "flow": 2,
        "pressure": 2,
        "acoustic": 1
    }
    
    @classmethod
    def generate_polygon_from_center(
        cls, 
        center: Tuple[float, float], 
        radius_km: float,
        num_points: int = 8,
        irregularity: float = 0.3
    ) -> List[List[float]]:
        """
        Generate an irregular polygon around a center point.
        
        Args:
            center: (lat, lng) tuple
            radius_km: Approximate radius in kilometers
            num_points: Number of polygon vertices
            irregularity: Randomness factor (0-1)
            
        Returns:
            List of [lng, lat] coordinates (GeoJSON format)
        """
        lat, lng = center
        # Convert km to degrees (approximately)
        lat_degree = radius_km / 111.0
        lng_degree = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        coords = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            # Add irregularity
            r_factor = 1 + (random.random() - 0.5) * 2 * irregularity
            
            point_lat = lat + lat_degree * r_factor * math.sin(angle)
            point_lng = lng + lng_degree * r_factor * math.cos(angle)
            
            coords.append([point_lng, point_lat])
        
        # Close the polygon
        coords.append(coords[0])
        
        return coords
    
    @classmethod
    def get_nrw_status(cls, nrw_percent: float) -> str:
        """Determine DMA status based on NRW percentage."""
        if nrw_percent >= 45:
            return "critical"
        elif nrw_percent >= 35:
            return "warning"
        elif nrw_percent >= 25:
            return "moderate"
        return "good"
    
    @classmethod
    def get_nrw_color(cls, nrw_percent: float) -> str:
        """Get color for NRW heatmap visualization."""
        if nrw_percent >= 50:
            return "#dc2626"  # red-600
        elif nrw_percent >= 45:
            return "#ef4444"  # red-500
        elif nrw_percent >= 40:
            return "#f97316"  # orange-500
        elif nrw_percent >= 35:
            return "#f59e0b"  # amber-500
        elif nrw_percent >= 30:
            return "#eab308"  # yellow-500
        elif nrw_percent >= 25:
            return "#84cc16"  # lime-500
        elif nrw_percent >= 20:
            return "#22c55e"  # green-500
        return "#10b981"  # emerald-500
    
    @classmethod
    def get_fill_opacity(cls, nrw_percent: float) -> float:
        """Get fill opacity based on NRW severity."""
        # Higher NRW = more opaque
        return min(0.7, 0.2 + (nrw_percent / 100) * 0.6)
    
    @classmethod
    def generate_dma_features(cls, tenant_id: str) -> List[GeoJSONFeature]:
        """Generate DMA polygon features with NRW data."""
        features = []
        
        for dma in cls.DMA_DEFINITIONS:
            # Generate polygon
            polygon_coords = cls.generate_polygon_from_center(
                dma["center"],
                dma["radius_km"],
                num_points=random.randint(6, 10),
                irregularity=0.25
            )
            
            # Add some real-time variation
            current_nrw = dma["nrw_percent"] + (random.random() - 0.5) * 4
            current_nrw = max(10, min(65, current_nrw))
            
            feature = GeoJSONFeature(
                id=dma["id"],
                geometry={
                    "type": "Polygon",
                    "coordinates": [polygon_coords]
                },
                properties={
                    "id": dma["id"],
                    "name": dma["name"],
                    "type": "dma",
                    "tenant_id": tenant_id,
                    
                    # NRW metrics
                    "nrw_percent": round(current_nrw, 1),
                    "nrw_target": 20.0,
                    "nrw_trend": random.choice(["improving", "stable", "worsening"]),
                    "status": cls.get_nrw_status(current_nrw),
                    
                    # Styling
                    "fill_color": cls.get_nrw_color(current_nrw),
                    "fill_opacity": cls.get_fill_opacity(current_nrw),
                    "stroke_color": "#1e293b",
                    "stroke_width": 2,
                    
                    # Statistics
                    "population": dma["population"],
                    "connections": dma["connections"],
                    "area_km2": round(math.pi * dma["radius_km"] ** 2, 2),
                    
                    # Real-time metrics
                    "flow_rate_m3h": round(random.uniform(50, 200) * (dma["connections"] / 5000), 1),
                    "pressure_bar": round(random.uniform(2.0, 4.0), 2),
                    "active_leaks": random.randint(0, 8) if current_nrw > 30 else random.randint(0, 3),
                    "sensors_online": random.randint(3, 5),
                    "sensors_total": 5,
                    
                    # Timestamps
                    "last_updated": datetime.utcnow().isoformat(),
                    "data_quality": random.choice(["excellent", "good", "fair"])
                }
            )
            features.append(feature)
        
        return features
    
    @classmethod
    def generate_sensor_features(cls, tenant_id: str) -> List[GeoJSONFeature]:
        """Generate sensor point features."""
        features = []
        sensor_idx = 1
        
        for dma in cls.DMA_DEFINITIONS:
            center_lat, center_lng = dma["center"]
            radius_km = dma["radius_km"]
            
            # Convert km to degrees
            lat_spread = radius_km / 111.0 * 0.7
            lng_spread = radius_km / (111.0 * math.cos(math.radians(center_lat))) * 0.7
            
            for sensor_type, count in cls.SENSORS_PER_DMA.items():
                for i in range(count):
                    # Random position within DMA
                    lat = center_lat + (random.random() - 0.5) * 2 * lat_spread
                    lng = center_lng + (random.random() - 0.5) * 2 * lng_spread
                    
                    # Determine status (mostly online)
                    status_roll = random.random()
                    if status_roll > 0.95:
                        status = "offline"
                        battery = random.randint(0, 10)
                    elif status_roll > 0.85:
                        status = "warning"
                        battery = random.randint(15, 35)
                    else:
                        status = "online"
                        battery = random.randint(50, 100)
                    
                    # Generate sensor value based on type
                    if sensor_type == "flow":
                        value = round(random.uniform(100, 1500), 1)
                        unit = "L/hr"
                    elif sensor_type == "pressure":
                        value = round(random.uniform(1.5, 4.5), 2)
                        unit = "bar"
                    else:  # acoustic
                        value = round(random.uniform(15, 85), 0)
                        unit = "dB"
                    
                    sensor_id = f"ESP32-{sensor_idx:03d}"
                    
                    feature = GeoJSONFeature(
                        id=sensor_id,
                        geometry={
                            "type": "Point",
                            "coordinates": [lng, lat]
                        },
                        properties={
                            "id": sensor_id,
                            "name": f"{dma['name']} {sensor_type.capitalize()} {i+1}",
                            "type": "sensor",
                            "sensor_type": sensor_type,
                            "tenant_id": tenant_id,
                            "dma_id": dma["id"],
                            "dma_name": dma["name"],
                            
                            # Status
                            "status": status,
                            "battery_percent": battery,
                            "signal_strength": random.randint(60, 100) if status != "offline" else 0,
                            
                            # Reading
                            "value": value if status != "offline" else None,
                            "unit": unit,
                            "last_reading": datetime.utcnow().isoformat() if status != "offline" else (
                                datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                            ).isoformat(),
                            
                            # Styling
                            "icon": f"sensor-{sensor_type}",
                            "marker_color": {
                                "online": "#10b981",
                                "warning": "#f59e0b",
                                "offline": "#ef4444",
                                "maintenance": "#6366f1"
                            }.get(status, "#64748b"),
                            "marker_size": 12,
                            
                            # Alerts
                            "has_alert": status == "warning" or (sensor_type == "acoustic" and value > 60),
                            "alert_type": "high_acoustic" if (sensor_type == "acoustic" and value > 60) else (
                                "low_battery" if battery < 20 else None
                            )
                        }
                    )
                    features.append(feature)
                    sensor_idx += 1
        
        return features
    
    @classmethod
    def generate_leak_features(cls, tenant_id: str) -> List[GeoJSONFeature]:
        """Generate leak marker features."""
        features = []
        
        # Sample leak locations
        leak_data = [
            {"dma": "dma-matero", "loc": "Great East Rd & Lumumba Rd", "severity": "critical", "status": "active", "flow": 67.3},
            {"dma": "dma-matero", "loc": "Matero Main Market", "severity": "high", "status": "assigned", "flow": 45.2},
            {"dma": "dma-chilenje", "loc": "Kafue Rd Junction", "severity": "high", "status": "active", "flow": 52.1},
            {"dma": "dma-chilenje", "loc": "Chilenje South", "severity": "medium", "status": "in-progress", "flow": 28.4},
            {"dma": "dma-mtendere", "loc": "Chelstone Market Area", "severity": "high", "status": "assigned", "flow": 41.5},
            {"dma": "dma-mtendere", "loc": "Mtendere Clinic Road", "severity": "medium", "status": "monitoring", "flow": 22.8},
            {"dma": "dma-kalingalinga", "loc": "Kalingalinga Main St", "severity": "critical", "status": "active", "flow": 78.2},
            {"dma": "dma-kabwata", "loc": "Chawama Rd Junction", "severity": "high", "status": "active", "flow": 38.9},
            {"dma": "dma-garden", "loc": "Cairo Rd South", "severity": "medium", "status": "repaired", "flow": 0},
            {"dma": "dma-rhodes-park", "loc": "Independence Ave", "severity": "low", "status": "verified", "flow": 5.2},
            {"dma": "dma-kabulonga", "loc": "Los Angeles Blvd", "severity": "medium", "status": "assigned", "flow": 18.4},
            {"dma": "dma-woodlands", "loc": "Manda Hill Area", "severity": "low", "status": "monitoring", "flow": 8.1},
            {"dma": "dma-olympia", "loc": "Olympia Park Rd", "severity": "medium", "status": "in-progress", "flow": 24.6},
            {"dma": "dma-chelstone", "loc": "Chelstone Mall Area", "severity": "high", "status": "assigned", "flow": 35.7},
        ]
        
        # Find DMA centers for positioning leaks
        dma_centers = {d["id"]: d["center"] for d in cls.DMA_DEFINITIONS}
        dma_radii = {d["id"]: d["radius_km"] for d in cls.DMA_DEFINITIONS}
        
        for idx, leak in enumerate(leak_data, 1):
            dma_id = leak["dma"]
            center = dma_centers.get(dma_id, (cls.CENTER_LAT, cls.CENTER_LNG))
            radius = dma_radii.get(dma_id, 1.0)
            
            # Position leak within DMA
            lat_spread = radius / 111.0 * 0.6
            lng_spread = radius / (111.0 * math.cos(math.radians(center[0]))) * 0.6
            
            lat = center[0] + (random.random() - 0.5) * 2 * lat_spread
            lng = center[1] + (random.random() - 0.5) * 2 * lng_spread
            
            leak_id = f"LEAK-{tenant_id[:3].upper()}-{idx:04d}"
            
            # Determine marker styling
            severity_colors = {
                "critical": "#dc2626",
                "high": "#f97316",
                "medium": "#eab308",
                "low": "#3b82f6"
            }
            
            status_icons = {
                "active": "leak-active",
                "assigned": "leak-assigned",
                "in-progress": "leak-progress",
                "monitoring": "leak-monitor",
                "repaired": "leak-repaired",
                "verified": "leak-verified"
            }
            
            detected_days_ago = random.randint(0, 14)
            
            feature = GeoJSONFeature(
                id=leak_id,
                geometry={
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                properties={
                    "id": leak_id,
                    "type": "leak",
                    "tenant_id": tenant_id,
                    "dma_id": dma_id,
                    "dma_name": dma_id.replace("dma-", "").replace("-", " ").title(),
                    
                    # Leak details
                    "location": leak["loc"],
                    "severity": leak["severity"],
                    "status": leak["status"],
                    "flow_rate_lph": leak["flow"] if leak["status"] not in ["repaired", "verified"] else 0,
                    "estimated_loss_m3_day": round(leak["flow"] * 24 / 1000, 2) if leak["flow"] > 0 else 0,
                    
                    # Detection info
                    "detected_at": (datetime.utcnow() - timedelta(days=detected_days_ago)).isoformat(),
                    "detection_method": random.choice(["acoustic", "pressure_anomaly", "flow_analysis", "customer_report"]),
                    "confidence_percent": random.randint(75, 98) if leak["status"] != "verified" else 100,
                    "ai_probability": round(random.uniform(0.7, 0.98), 2),
                    
                    # Assignment
                    "assigned_to": f"TECH-{random.randint(1,20):03d}" if leak["status"] in ["assigned", "in-progress"] else None,
                    "work_order_id": f"WO-{random.randint(1000,9999)}" if leak["status"] in ["assigned", "in-progress", "repaired"] else None,
                    
                    # Styling
                    "marker_color": severity_colors.get(leak["severity"], "#64748b"),
                    "marker_size": {"critical": 18, "high": 16, "medium": 14, "low": 12}.get(leak["severity"], 14),
                    "icon": status_icons.get(leak["status"], "leak-active"),
                    "pulse": leak["status"] == "active" and leak["severity"] in ["critical", "high"],
                    
                    # Priority score (for sorting)
                    "priority_score": cls._calculate_leak_priority(leak)
                }
            )
            features.append(feature)
        
        return features
    
    @classmethod
    def _calculate_leak_priority(cls, leak: dict) -> float:
        """Calculate leak priority score using the LOCKED FORMULA."""
        severity_weights = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
        status_weights = {"active": 1.0, "assigned": 0.8, "in-progress": 0.6, "monitoring": 0.4, "repaired": 0.1, "verified": 0.05}
        
        severity_factor = severity_weights.get(leak["severity"], 0.5)
        status_factor = status_weights.get(leak["status"], 0.5)
        flow_factor = min(1.0, leak["flow"] / 100)
        
        # Priority Score = leak_probability × estimated_loss × criticality × confidence
        priority = severity_factor * flow_factor * status_factor * 0.9
        return round(priority * 100, 1)
    
    @classmethod
    def generate_full_geojson(cls, tenant_id: str) -> Dict[str, GeoJSONFeatureCollection]:
        """Generate complete map data for a tenant."""
        return {
            "dmas": GeoJSONFeatureCollection(
                features=cls.generate_dma_features(tenant_id),
                metadata={
                    "layer": "dmas",
                    "description": "District Metered Areas with NRW heatmap",
                    "total_count": len(cls.DMA_DEFINITIONS)
                }
            ),
            "sensors": GeoJSONFeatureCollection(
                features=cls.generate_sensor_features(tenant_id),
                metadata={
                    "layer": "sensors",
                    "description": "IoT sensors (flow, pressure, acoustic)",
                    "types": ["flow", "pressure", "acoustic"]
                }
            ),
            "leaks": GeoJSONFeatureCollection(
                features=cls.generate_leak_features(tenant_id),
                metadata={
                    "layer": "leaks",
                    "description": "Detected and tracked leaks",
                    "severities": ["critical", "high", "medium", "low"]
                }
            )
        }


# =============================================================================
# FASTAPI ROUTER
# =============================================================================

router = APIRouter(prefix="/tenants/{tenant_id}/map", tags=["Map GeoJSON"])


@router.get("/geojson", response_model=FullMapResponse)
async def get_full_map_geojson(
    tenant_id: str,
    include_layers: Optional[str] = Query(
        default="dmas,sensors,leaks",
        description="Comma-separated list of layers to include"
    ),
    dma_filter: Optional[str] = Query(
        default=None,
        description="Filter by specific DMA ID"
    ),
    sensor_status: Optional[SensorStatus] = Query(
        default=None,
        description="Filter sensors by status"
    ),
    leak_status: Optional[LeakStatus] = Query(
        default=None,
        description="Filter leaks by status"
    ),
    leak_severity: Optional[LeakSeverity] = Query(
        default=None,
        description="Filter leaks by severity"
    ),
    min_nrw: Optional[float] = Query(
        default=None,
        description="Filter DMAs with NRW >= this value"
    )
):
    """
    Get full map GeoJSON data for a tenant.
    
    Returns GeoJSON FeatureCollections for:
    - DMAs: Polygon features with NRW heatmap styling
    - Sensors: Point features with status colors
    - Leaks: Point features with severity markers
    
    Use query parameters to filter and customize the response.
    """
    try:
        # Generate sample data
        layers_to_include = [l.strip() for l in include_layers.split(",")]
        all_layers = SampleGeoJSONGenerator.generate_full_geojson(tenant_id)
        
        result_layers = {}
        
        # Filter DMA layer
        if "dmas" in layers_to_include:
            dma_layer = all_layers["dmas"]
            if dma_filter:
                dma_layer.features = [f for f in dma_layer.features if f.properties.get("id") == dma_filter]
            if min_nrw is not None:
                dma_layer.features = [f for f in dma_layer.features if f.properties.get("nrw_percent", 0) >= min_nrw]
            result_layers["dmas"] = dma_layer
        
        # Filter sensor layer
        if "sensors" in layers_to_include:
            sensor_layer = all_layers["sensors"]
            if dma_filter:
                sensor_layer.features = [f for f in sensor_layer.features if f.properties.get("dma_id") == dma_filter]
            if sensor_status:
                sensor_layer.features = [f for f in sensor_layer.features if f.properties.get("status") == sensor_status.value]
            result_layers["sensors"] = sensor_layer
        
        # Filter leak layer
        if "leaks" in layers_to_include:
            leak_layer = all_layers["leaks"]
            if dma_filter:
                leak_layer.features = [f for f in leak_layer.features if f.properties.get("dma_id") == dma_filter]
            if leak_status:
                leak_layer.features = [f for f in leak_layer.features if f.properties.get("status") == leak_status.value]
            if leak_severity:
                leak_layer.features = [f for f in leak_layer.features if f.properties.get("severity") == leak_severity.value]
            result_layers["leaks"] = leak_layer
        
        # Calculate metadata
        total_sensors = len(result_layers.get("sensors", GeoJSONFeatureCollection(features=[])).features)
        online_sensors = len([
            f for f in result_layers.get("sensors", GeoJSONFeatureCollection(features=[])).features
            if f.properties.get("status") == "online"
        ])
        active_leaks = len([
            f for f in result_layers.get("leaks", GeoJSONFeatureCollection(features=[])).features
            if f.properties.get("status") == "active"
        ])
        
        return FullMapResponse(
            tenantId=tenant_id,
            layers=result_layers,
            metadata={
                "total_dmas": len(result_layers.get("dmas", GeoJSONFeatureCollection(features=[])).features),
                "total_sensors": total_sensors,
                "sensors_online": online_sensors,
                "total_leaks": len(result_layers.get("leaks", GeoJSONFeatureCollection(features=[])).features),
                "active_leaks": active_leaks,
                "filters_applied": {
                    "dma": dma_filter,
                    "sensor_status": sensor_status.value if sensor_status else None,
                    "leak_status": leak_status.value if leak_status else None,
                    "leak_severity": leak_severity.value if leak_severity else None,
                    "min_nrw": min_nrw
                },
                "center": [SampleGeoJSONGenerator.CENTER_LNG, SampleGeoJSONGenerator.CENTER_LAT],
                "zoom": 12
            },
            generatedAt=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating map GeoJSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors", response_model=MapLayerResponse)
async def get_sensors_geojson(
    tenant_id: str,
    dma_id: Optional[str] = None,
    sensor_type: Optional[SensorType] = None,
    status: Optional[SensorStatus] = None
):
    """Get GeoJSON for sensors only."""
    features = SampleGeoJSONGenerator.generate_sensor_features(tenant_id)
    
    if dma_id:
        features = [f for f in features if f.properties.get("dma_id") == dma_id]
    if sensor_type:
        features = [f for f in features if f.properties.get("sensor_type") == sensor_type.value]
    if status:
        features = [f for f in features if f.properties.get("status") == status.value]
    
    return MapLayerResponse(
        layer="sensors",
        geojson=GeoJSONFeatureCollection(features=features),
        lastUpdated=datetime.utcnow().isoformat(),
        count=len(features)
    )


@router.get("/leaks", response_model=MapLayerResponse)
async def get_leaks_geojson(
    tenant_id: str,
    dma_id: Optional[str] = None,
    severity: Optional[LeakSeverity] = None,
    status: Optional[LeakStatus] = None,
    active_only: bool = False
):
    """Get GeoJSON for leaks only."""
    features = SampleGeoJSONGenerator.generate_leak_features(tenant_id)
    
    if dma_id:
        features = [f for f in features if f.properties.get("dma_id") == dma_id]
    if severity:
        features = [f for f in features if f.properties.get("severity") == severity.value]
    if status:
        features = [f for f in features if f.properties.get("status") == status.value]
    if active_only:
        features = [f for f in features if f.properties.get("status") == "active"]
    
    # Sort by priority
    features.sort(key=lambda f: f.properties.get("priority_score", 0), reverse=True)
    
    return MapLayerResponse(
        layer="leaks",
        geojson=GeoJSONFeatureCollection(features=features),
        lastUpdated=datetime.utcnow().isoformat(),
        count=len(features)
    )


@router.get("/dmas", response_model=MapLayerResponse)
async def get_dmas_geojson(
    tenant_id: str,
    dma_id: Optional[str] = None,
    status: Optional[DMAStatus] = None,
    min_nrw: Optional[float] = None,
    max_nrw: Optional[float] = None
):
    """Get GeoJSON for DMAs with NRW heatmap data."""
    features = SampleGeoJSONGenerator.generate_dma_features(tenant_id)
    
    if dma_id:
        features = [f for f in features if f.properties.get("id") == dma_id]
    if status:
        features = [f for f in features if f.properties.get("status") == status.value]
    if min_nrw is not None:
        features = [f for f in features if f.properties.get("nrw_percent", 0) >= min_nrw]
    if max_nrw is not None:
        features = [f for f in features if f.properties.get("nrw_percent", 100) <= max_nrw]
    
    # Sort by NRW (highest first)
    features.sort(key=lambda f: f.properties.get("nrw_percent", 0), reverse=True)
    
    return MapLayerResponse(
        layer="dmas",
        geojson=GeoJSONFeatureCollection(features=features),
        lastUpdated=datetime.utcnow().isoformat(),
        count=len(features)
    )


@router.get("/bounds")
async def get_map_bounds(tenant_id: str):
    """Get the bounding box for the tenant's network."""
    features = SampleGeoJSONGenerator.generate_dma_features(tenant_id)
    
    all_coords = []
    for feature in features:
        if feature.geometry["type"] == "Polygon":
            for coord in feature.geometry["coordinates"][0]:
                all_coords.append(coord)
    
    if not all_coords:
        return {
            "bounds": [
                [SampleGeoJSONGenerator.CENTER_LNG - 0.1, SampleGeoJSONGenerator.CENTER_LAT - 0.1],
                [SampleGeoJSONGenerator.CENTER_LNG + 0.1, SampleGeoJSONGenerator.CENTER_LAT + 0.1]
            ],
            "center": [SampleGeoJSONGenerator.CENTER_LNG, SampleGeoJSONGenerator.CENTER_LAT],
            "zoom": 12
        }
    
    lngs = [c[0] for c in all_coords]
    lats = [c[1] for c in all_coords]
    
    return {
        "bounds": [
            [min(lngs), min(lats)],  # Southwest
            [max(lngs), max(lats)]   # Northeast
        ],
        "center": [
            (min(lngs) + max(lngs)) / 2,
            (min(lats) + max(lats)) / 2
        ],
        "zoom": 12
    }


# =============================================================================
# INTEGRATION WITH MAIN API
# =============================================================================

def register_map_routes(app):
    """Register map routes with the main FastAPI app."""
    app.include_router(router)
    logger.info("Map GeoJSON routes registered")


# For standalone testing
if __name__ == "__main__":
    import json
    
    # Generate sample data
    tenant = "lusaka-water"
    data = SampleGeoJSONGenerator.generate_full_geojson(tenant)
    
    print("=== SAMPLE GEOJSON DATA ===\n")
    
    for layer_name, layer_data in data.items():
        print(f"\n--- {layer_name.upper()} ---")
        print(f"Total features: {len(layer_data.features)}")
        if layer_data.features:
            print(f"Sample feature: {json.dumps(layer_data.features[0].model_dump(), indent=2, default=str)[:500]}...")
