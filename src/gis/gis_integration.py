"""
AquaWatch NRW - GIS Integration Module
======================================

Geographic Information System integration for pipe network visualization.

Features:
- Pipe network mapping and visualization
- Asset management with location data
- Leak heatmaps
- Zone boundary management
- Distance calculations
- Route optimization for technicians

Designed for Zambia/South Africa water utilities.
"""

import os
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# GIS DATA STRUCTURES
# =============================================================================

class AssetType(Enum):
    PIPE = "pipe"
    VALVE = "valve"
    HYDRANT = "hydrant"
    METER = "meter"
    PUMP_STATION = "pump_station"
    RESERVOIR = "reservoir"
    BOREHOLE = "borehole"
    TREATMENT_PLANT = "treatment_plant"
    PRESSURE_SENSOR = "pressure_sensor"
    FLOW_METER = "flow_meter"
    PRV = "prv"  # Pressure Reducing Valve


class PipeMaterial(Enum):
    PVC = "pvc"
    HDPE = "hdpe"
    STEEL = "steel"
    CAST_IRON = "cast_iron"
    DUCTILE_IRON = "ductile_iron"
    ASBESTOS_CEMENT = "asbestos_cement"
    CONCRETE = "concrete"
    COPPER = "copper"
    GALVANIZED = "galvanized"
    UNKNOWN = "unknown"


class AssetCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class GeoPoint:
    """Geographic point with coordinates."""
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "lat": self.latitude,
            "lng": self.longitude,
            "elevation": self.elevation_m
        }
    
    def to_geojson(self) -> Dict:
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }


@dataclass
class GeoLineString:
    """Geographic line (for pipes, routes)."""
    points: List[GeoPoint]
    
    def to_geojson(self) -> Dict:
        return {
            "type": "LineString",
            "coordinates": [[p.longitude, p.latitude] for p in self.points]
        }
    
    @property
    def length_km(self) -> float:
        """Calculate length in kilometers."""
        total = 0
        for i in range(len(self.points) - 1):
            total += haversine_distance(
                self.points[i].latitude, self.points[i].longitude,
                self.points[i+1].latitude, self.points[i+1].longitude
            )
        return total


@dataclass
class GeoPolygon:
    """Geographic polygon (for zones, DMAs)."""
    exterior: List[GeoPoint]
    holes: List[List[GeoPoint]] = field(default_factory=list)
    
    def to_geojson(self) -> Dict:
        exterior_coords = [[p.longitude, p.latitude] for p in self.exterior]
        # Close the polygon
        if exterior_coords[0] != exterior_coords[-1]:
            exterior_coords.append(exterior_coords[0])
        
        coordinates = [exterior_coords]
        for hole in self.holes:
            hole_coords = [[p.longitude, p.latitude] for p in hole]
            if hole_coords[0] != hole_coords[-1]:
                hole_coords.append(hole_coords[0])
            coordinates.append(hole_coords)
        
        return {
            "type": "Polygon",
            "coordinates": coordinates
        }
    
    def contains_point(self, point: GeoPoint) -> bool:
        """Check if polygon contains a point (ray casting algorithm)."""
        x, y = point.longitude, point.latitude
        n = len(self.exterior)
        inside = False
        
        p1x, p1y = self.exterior[0].longitude, self.exterior[0].latitude
        for i in range(1, n + 1):
            p2x, p2y = self.exterior[i % n].longitude, self.exterior[i % n].latitude
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside


@dataclass
class WaterAsset:
    """Water network asset."""
    asset_id: str
    asset_type: AssetType
    name: str
    location: GeoPoint
    
    # Physical properties
    material: Optional[PipeMaterial] = None
    diameter_mm: Optional[int] = None
    length_m: Optional[float] = None
    
    # For pipes
    geometry: Optional[GeoLineString] = None
    start_node: Optional[str] = None
    end_node: Optional[str] = None
    
    # Operational
    zone_id: str = ""
    dma_id: str = ""
    pressure_zone: str = ""
    
    # Condition
    condition: AssetCondition = AssetCondition.UNKNOWN
    installation_year: Optional[int] = None
    last_inspection: Optional[datetime] = None
    
    # Status
    active: bool = True
    notes: str = ""
    
    @property
    def age_years(self) -> Optional[int]:
        if self.installation_year:
            return datetime.now().year - self.installation_year
        return None
    
    def to_geojson_feature(self) -> Dict:
        """Convert to GeoJSON Feature."""
        if self.geometry:
            geometry = self.geometry.to_geojson()
        else:
            geometry = self.location.to_geojson()
        
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "asset_id": self.asset_id,
                "asset_type": self.asset_type.value,
                "name": self.name,
                "material": self.material.value if self.material else None,
                "diameter_mm": self.diameter_mm,
                "condition": self.condition.value,
                "age_years": self.age_years,
                "zone_id": self.zone_id,
                "dma_id": self.dma_id
            }
        }


@dataclass
class Zone:
    """Water distribution zone or DMA."""
    zone_id: str
    name: str
    boundary: GeoPolygon
    zone_type: str = "dma"  # dma, pressure_zone, administrative
    
    # Properties
    population: int = 0
    connections: int = 0
    area_km2: float = 0.0
    
    # Operational
    inlet_points: List[str] = field(default_factory=list)  # Asset IDs
    pressure_target_bar: float = 3.0
    
    # NRW metrics
    nrw_percent: float = 0.0
    water_supplied_m3: float = 0.0
    water_billed_m3: float = 0.0
    
    # Style
    fill_color: str = "#3388ff"
    stroke_color: str = "#2266cc"
    
    def to_geojson_feature(self) -> Dict:
        return {
            "type": "Feature",
            "geometry": self.boundary.to_geojson(),
            "properties": {
                "zone_id": self.zone_id,
                "name": self.name,
                "zone_type": self.zone_type,
                "population": self.population,
                "connections": self.connections,
                "nrw_percent": self.nrw_percent,
                "fill_color": self.fill_color,
                "stroke_color": self.stroke_color
            }
        }


@dataclass
class LeakReport:
    """Leak or incident with location."""
    report_id: str
    location: GeoPoint
    report_type: str  # leak, burst, quality, pressure
    severity: str  # low, medium, high, critical
    
    # Details
    description: str = ""
    source: str = "sensor"  # sensor, community, inspection
    
    # Status
    status: str = "open"  # open, assigned, in_progress, resolved
    work_order_id: Optional[str] = None
    
    # Timestamps
    reported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    
    # Measurements
    estimated_loss_lph: float = 0.0
    
    def to_geojson_feature(self) -> Dict:
        return {
            "type": "Feature",
            "geometry": self.location.to_geojson(),
            "properties": {
                "report_id": self.report_id,
                "report_type": self.report_type,
                "severity": self.severity,
                "status": self.status,
                "estimated_loss_lph": self.estimated_loss_lph,
                "reported_at": self.reported_at.isoformat()
            }
        }


# =============================================================================
# GEOGRAPHIC UTILITIES
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def find_nearest_point(
    target: GeoPoint, 
    points: List[Tuple[str, GeoPoint]]
) -> Tuple[str, GeoPoint, float]:
    """Find nearest point to target. Returns (id, point, distance_km)."""
    nearest = None
    min_distance = float('inf')
    
    for point_id, point in points:
        dist = haversine_distance(
            target.latitude, target.longitude,
            point.latitude, point.longitude
        )
        if dist < min_distance:
            min_distance = dist
            nearest = (point_id, point, dist)
    
    return nearest


def calculate_centroid(points: List[GeoPoint]) -> GeoPoint:
    """Calculate centroid of a set of points."""
    if not points:
        return GeoPoint(0, 0)
    
    lat_sum = sum(p.latitude for p in points)
    lon_sum = sum(p.longitude for p in points)
    n = len(points)
    
    return GeoPoint(lat_sum / n, lon_sum / n)


def create_bounding_box(
    points: List[GeoPoint], 
    padding_km: float = 0
) -> Tuple[GeoPoint, GeoPoint]:
    """Create bounding box around points. Returns (sw_corner, ne_corner)."""
    if not points:
        return (GeoPoint(0, 0), GeoPoint(0, 0))
    
    min_lat = min(p.latitude for p in points)
    max_lat = max(p.latitude for p in points)
    min_lon = min(p.longitude for p in points)
    max_lon = max(p.longitude for p in points)
    
    # Add padding (approximate degrees from km)
    padding_deg = padding_km / 111  # 1 degree ≈ 111 km
    
    return (
        GeoPoint(min_lat - padding_deg, min_lon - padding_deg),
        GeoPoint(max_lat + padding_deg, max_lon + padding_deg)
    )


# =============================================================================
# GIS SERVICE
# =============================================================================

class GISService:
    """
    Main GIS service for AquaWatch NRW.
    
    Features:
    - Asset management with spatial queries
    - Zone management
    - Leak mapping and heatmaps
    - Route optimization
    - GeoJSON export for mapping
    """
    
    def __init__(self):
        # In-memory stores (replace with PostGIS in production)
        self.assets: Dict[str, WaterAsset] = {}
        self.zones: Dict[str, Zone] = {}
        self.leak_reports: Dict[str, LeakReport] = {}
        
        # Spatial index (simplified - use R-tree in production)
        self._asset_locations: List[Tuple[str, GeoPoint]] = []
        
        logger.info("GISService initialized")
    
    # =========================================================================
    # ASSET MANAGEMENT
    # =========================================================================
    
    def add_asset(self, asset: WaterAsset):
        """Add a water network asset."""
        self.assets[asset.asset_id] = asset
        self._asset_locations.append((asset.asset_id, asset.location))
        logger.info(f"Added asset: {asset.asset_id} ({asset.asset_type.value})")
    
    def get_asset(self, asset_id: str) -> Optional[WaterAsset]:
        """Get asset by ID."""
        return self.assets.get(asset_id)
    
    def get_assets_by_type(self, asset_type: AssetType) -> List[WaterAsset]:
        """Get all assets of a specific type."""
        return [a for a in self.assets.values() if a.asset_type == asset_type]
    
    def get_assets_in_zone(self, zone_id: str) -> List[WaterAsset]:
        """Get all assets in a zone."""
        return [a for a in self.assets.values() if a.zone_id == zone_id]
    
    def get_assets_in_radius(
        self, 
        center: GeoPoint, 
        radius_km: float
    ) -> List[Tuple[WaterAsset, float]]:
        """Get assets within radius of a point. Returns (asset, distance_km)."""
        results = []
        for asset in self.assets.values():
            dist = haversine_distance(
                center.latitude, center.longitude,
                asset.location.latitude, asset.location.longitude
            )
            if dist <= radius_km:
                results.append((asset, dist))
        
        results.sort(key=lambda x: x[1])
        return results
    
    def find_nearest_asset(
        self, 
        location: GeoPoint, 
        asset_type: AssetType = None
    ) -> Optional[Tuple[WaterAsset, float]]:
        """Find nearest asset to a location."""
        candidates = self._asset_locations
        
        if asset_type:
            candidates = [(aid, loc) for aid, loc in candidates 
                         if self.assets[aid].asset_type == asset_type]
        
        if not candidates:
            return None
        
        nearest = find_nearest_point(location, candidates)
        if nearest:
            asset_id, _, distance = nearest
            return (self.assets[asset_id], distance)
        
        return None
    
    def get_aging_assets(
        self, 
        min_age_years: int = 30,
        asset_type: AssetType = None
    ) -> List[WaterAsset]:
        """Get assets older than specified age."""
        results = []
        for asset in self.assets.values():
            if asset.age_years and asset.age_years >= min_age_years:
                if asset_type is None or asset.asset_type == asset_type:
                    results.append(asset)
        
        results.sort(key=lambda x: x.age_years or 0, reverse=True)
        return results
    
    def get_critical_condition_assets(self) -> List[WaterAsset]:
        """Get assets in poor or critical condition."""
        return [a for a in self.assets.values() 
                if a.condition in [AssetCondition.POOR, AssetCondition.CRITICAL]]
    
    # =========================================================================
    # ZONE MANAGEMENT
    # =========================================================================
    
    def add_zone(self, zone: Zone):
        """Add a zone/DMA."""
        self.zones[zone.zone_id] = zone
        logger.info(f"Added zone: {zone.zone_id} ({zone.name})")
    
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID."""
        return self.zones.get(zone_id)
    
    def find_zone_for_point(self, point: GeoPoint) -> Optional[Zone]:
        """Find which zone contains a point."""
        for zone in self.zones.values():
            if zone.boundary.contains_point(point):
                return zone
        return None
    
    def get_zone_statistics(self, zone_id: str) -> Dict:
        """Get statistics for a zone."""
        zone = self.zones.get(zone_id)
        if not zone:
            return {}
        
        assets = self.get_assets_in_zone(zone_id)
        pipes = [a for a in assets if a.asset_type == AssetType.PIPE]
        leaks = [l for l in self.leak_reports.values() 
                if self.find_zone_for_point(l.location) and 
                self.find_zone_for_point(l.location).zone_id == zone_id]
        
        return {
            "zone_id": zone_id,
            "name": zone.name,
            "area_km2": zone.area_km2,
            "population": zone.population,
            "connections": zone.connections,
            "total_assets": len(assets),
            "total_pipes": len(pipes),
            "total_pipe_length_km": sum(
                (p.length_m or 0) / 1000 for p in pipes
            ),
            "nrw_percent": zone.nrw_percent,
            "active_leaks": len([l for l in leaks if l.status != "resolved"]),
            "assets_by_type": self._count_assets_by_type(assets),
            "pipe_materials": self._count_pipe_materials(pipes),
            "average_pipe_age": self._average_pipe_age(pipes)
        }
    
    def _count_assets_by_type(self, assets: List[WaterAsset]) -> Dict:
        counts = {}
        for asset in assets:
            t = asset.asset_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    def _count_pipe_materials(self, pipes: List[WaterAsset]) -> Dict:
        counts = {}
        for pipe in pipes:
            m = pipe.material.value if pipe.material else "unknown"
            counts[m] = counts.get(m, 0) + 1
        return counts
    
    def _average_pipe_age(self, pipes: List[WaterAsset]) -> float:
        ages = [p.age_years for p in pipes if p.age_years]
        return round(sum(ages) / len(ages), 1) if ages else 0
    
    # =========================================================================
    # LEAK REPORTS
    # =========================================================================
    
    def add_leak_report(self, report: LeakReport):
        """Add a leak report."""
        self.leak_reports[report.report_id] = report
        logger.info(f"Added leak report: {report.report_id}")
    
    def get_leak_report(self, report_id: str) -> Optional[LeakReport]:
        """Get leak report by ID."""
        return self.leak_reports.get(report_id)
    
    def get_active_leaks(self) -> List[LeakReport]:
        """Get all active (unresolved) leak reports."""
        return [l for l in self.leak_reports.values() if l.status != "resolved"]
    
    def get_leaks_in_radius(
        self, 
        center: GeoPoint, 
        radius_km: float
    ) -> List[Tuple[LeakReport, float]]:
        """Get leak reports within radius."""
        results = []
        for leak in self.leak_reports.values():
            dist = haversine_distance(
                center.latitude, center.longitude,
                leak.location.latitude, leak.location.longitude
            )
            if dist <= radius_km:
                results.append((leak, dist))
        
        results.sort(key=lambda x: x[1])
        return results
    
    def generate_leak_heatmap_data(
        self, 
        grid_size_km: float = 0.5,
        days: int = 90
    ) -> List[Dict]:
        """Generate heatmap data for leaks."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent_leaks = [l for l in self.leak_reports.values() 
                       if l.reported_at > cutoff]
        
        if not recent_leaks:
            return []
        
        # Get bounding box
        points = [l.location for l in recent_leaks]
        sw, ne = create_bounding_box(points, padding_km=1)
        
        # Create grid
        lat_step = grid_size_km / 111  # Convert km to degrees
        lon_step = grid_size_km / (111 * math.cos(math.radians(sw.latitude)))
        
        heatmap_data = []
        lat = sw.latitude
        while lat <= ne.latitude:
            lon = sw.longitude
            while lon <= ne.longitude:
                # Count leaks in this cell
                count = 0
                total_loss = 0
                for leak in recent_leaks:
                    if (lat <= leak.location.latitude < lat + lat_step and
                        lon <= leak.location.longitude < lon + lon_step):
                        count += 1
                        total_loss += leak.estimated_loss_lph
                
                if count > 0:
                    heatmap_data.append({
                        "lat": lat + lat_step/2,
                        "lng": lon + lon_step/2,
                        "count": count,
                        "intensity": min(count / 5, 1.0),  # Normalize
                        "total_loss_lph": total_loss
                    })
                
                lon += lon_step
            lat += lat_step
        
        return heatmap_data
    
    # =========================================================================
    # ROUTE OPTIMIZATION
    # =========================================================================
    
    def optimize_technician_route(
        self, 
        start: GeoPoint,
        work_order_locations: List[GeoPoint],
        return_to_start: bool = True
    ) -> List[int]:
        """
        Optimize route for a technician to visit multiple locations.
        Uses nearest neighbor heuristic (simple but effective for small sets).
        Returns indices in optimized order.
        """
        if not work_order_locations:
            return []
        
        n = len(work_order_locations)
        if n == 1:
            return [0]
        
        # Nearest neighbor algorithm
        unvisited = set(range(n))
        route = []
        current = start
        
        while unvisited:
            nearest_idx = None
            min_dist = float('inf')
            
            for idx in unvisited:
                dist = haversine_distance(
                    current.latitude, current.longitude,
                    work_order_locations[idx].latitude, 
                    work_order_locations[idx].longitude
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
            
            route.append(nearest_idx)
            current = work_order_locations[nearest_idx]
            unvisited.remove(nearest_idx)
        
        return route
    
    def calculate_route_distance(
        self, 
        start: GeoPoint,
        locations: List[GeoPoint],
        order: List[int] = None
    ) -> float:
        """Calculate total route distance in km."""
        if not locations:
            return 0
        
        if order is None:
            order = list(range(len(locations)))
        
        total = 0
        current = start
        
        for idx in order:
            total += haversine_distance(
                current.latitude, current.longitude,
                locations[idx].latitude, locations[idx].longitude
            )
            current = locations[idx]
        
        return round(total, 2)
    
    # =========================================================================
    # GEOJSON EXPORT
    # =========================================================================
    
    def export_assets_geojson(
        self, 
        zone_id: str = None,
        asset_type: AssetType = None
    ) -> Dict:
        """Export assets as GeoJSON FeatureCollection."""
        assets = self.assets.values()
        
        if zone_id:
            assets = [a for a in assets if a.zone_id == zone_id]
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        
        return {
            "type": "FeatureCollection",
            "features": [a.to_geojson_feature() for a in assets]
        }
    
    def export_zones_geojson(self) -> Dict:
        """Export zones as GeoJSON FeatureCollection."""
        return {
            "type": "FeatureCollection",
            "features": [z.to_geojson_feature() for z in self.zones.values()]
        }
    
    def export_leaks_geojson(self, active_only: bool = True) -> Dict:
        """Export leak reports as GeoJSON FeatureCollection."""
        leaks = self.leak_reports.values()
        if active_only:
            leaks = [l for l in leaks if l.status != "resolved"]
        
        return {
            "type": "FeatureCollection",
            "features": [l.to_geojson_feature() for l in leaks]
        }
    
    def export_full_network_geojson(self) -> Dict:
        """Export complete network as GeoJSON."""
        features = []
        
        # Add zones
        for zone in self.zones.values():
            feature = zone.to_geojson_feature()
            feature["properties"]["layer"] = "zones"
            features.append(feature)
        
        # Add assets
        for asset in self.assets.values():
            feature = asset.to_geojson_feature()
            feature["properties"]["layer"] = "assets"
            features.append(feature)
        
        # Add active leaks
        for leak in self.leak_reports.values():
            if leak.status != "resolved":
                feature = leak.to_geojson_feature()
                feature["properties"]["layer"] = "leaks"
                features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }


# =============================================================================
# SAMPLE DATA FOR ZAMBIA
# =============================================================================

def create_sample_lusaka_data(service: GISService):
    """Create sample GIS data for Lusaka, Zambia."""
    
    # Define sample zone (simplified Kabulonga area)
    kabulonga_boundary = GeoPolygon(exterior=[
        GeoPoint(-15.38, 28.30),
        GeoPoint(-15.38, 28.34),
        GeoPoint(-15.42, 28.34),
        GeoPoint(-15.42, 28.30)
    ])
    
    service.add_zone(Zone(
        zone_id="ZONE_KAB",
        name="Kabulonga DMA",
        boundary=kabulonga_boundary,
        zone_type="dma",
        population=45000,
        connections=8500,
        area_km2=12.5,
        nrw_percent=28.5,
        fill_color="#3388ff",
        stroke_color="#2266cc"
    ))
    
    # Add sample pipes
    service.add_asset(WaterAsset(
        asset_id="PIPE_001",
        asset_type=AssetType.PIPE,
        name="Great East Rd Main",
        location=GeoPoint(-15.40, 28.32),
        material=PipeMaterial.DUCTILE_IRON,
        diameter_mm=300,
        length_m=1500,
        geometry=GeoLineString([
            GeoPoint(-15.39, 28.31),
            GeoPoint(-15.40, 28.32),
            GeoPoint(-15.41, 28.33)
        ]),
        zone_id="ZONE_KAB",
        condition=AssetCondition.GOOD,
        installation_year=2005
    ))
    
    service.add_asset(WaterAsset(
        asset_id="PIPE_002",
        asset_type=AssetType.PIPE,
        name="Leopards Hill Branch",
        location=GeoPoint(-15.405, 28.325),
        material=PipeMaterial.PVC,
        diameter_mm=150,
        length_m=800,
        zone_id="ZONE_KAB",
        condition=AssetCondition.FAIR,
        installation_year=1998
    ))
    
    # Add valves
    service.add_asset(WaterAsset(
        asset_id="VALVE_001",
        asset_type=AssetType.VALVE,
        name="Kabulonga Main Valve",
        location=GeoPoint(-15.40, 28.32),
        zone_id="ZONE_KAB",
        condition=AssetCondition.GOOD,
        installation_year=2005
    ))
    
    # Add sensors
    service.add_asset(WaterAsset(
        asset_id="SENSOR_001",
        asset_type=AssetType.PRESSURE_SENSOR,
        name="Kabulonga Pressure Monitor",
        location=GeoPoint(-15.402, 28.322),
        zone_id="ZONE_KAB",
        installation_year=2023
    ))
    
    # Add sample leak
    service.add_leak_report(LeakReport(
        report_id="LEAK_001",
        location=GeoPoint(-15.403, 28.323),
        report_type="leak",
        severity="medium",
        description="Underground leak detected by pressure drop",
        source="sensor",
        status="assigned",
        estimated_loss_lph=150.0
    ))
    
    logger.info("Created sample Lusaka GIS data")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    service = GISService()
    
    # Create sample data
    create_sample_lusaka_data(service)
    
    # Get zone statistics
    print("Zone Statistics:")
    stats = service.get_zone_statistics("ZONE_KAB")
    print(json.dumps(stats, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Export GeoJSON
    print("GeoJSON Export (first 500 chars):")
    geojson = service.export_full_network_geojson()
    print(json.dumps(geojson, indent=2)[:500] + "...")
    
    print("\n" + "="*50 + "\n")
    
    # Find nearest asset
    test_point = GeoPoint(-15.405, 28.324)
    nearest = service.find_nearest_asset(test_point)
    if nearest:
        asset, dist = nearest
        print(f"Nearest asset to test point: {asset.name} ({dist:.2f} km away)")
    
    print("\n" + "="*50 + "\n")
    
    # Generate heatmap data
    print("Leak Heatmap Data:")
    heatmap = service.generate_leak_heatmap_data()
    print(json.dumps(heatmap, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Route optimization
    start = GeoPoint(-15.39, 28.31)
    work_locations = [
        GeoPoint(-15.41, 28.33),
        GeoPoint(-15.40, 28.32),
        GeoPoint(-15.405, 28.325)
    ]
    
    optimized_route = service.optimize_technician_route(start, work_locations)
    original_dist = service.calculate_route_distance(start, work_locations)
    optimized_dist = service.calculate_route_distance(start, work_locations, optimized_route)
    
    print(f"Route Optimization:")
    print(f"  Original order: {list(range(len(work_locations)))}")
    print(f"  Optimized order: {optimized_route}")
    print(f"  Original distance: {original_dist} km")
    print(f"  Optimized distance: {optimized_dist} km")
    print(f"  Savings: {original_dist - optimized_dist:.2f} km")
