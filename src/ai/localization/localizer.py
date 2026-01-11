"""
AquaWatch NRW - Layer 3: Leak Localization
==========================================

Localizes probable leak location to pipe segments using network topology
and Bayesian inference.

Design Principles:
1. Network-aware inference (uses pipe topology)
2. Incorporates prior knowledge (pipe age, material, history)
3. Quantifies uncertainty (not just point estimates)
4. Explainable reasoning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


@dataclass
class LocalizationResult:
    """Result from leak localization."""
    dma_id: str
    timestamp: datetime
    ranked_segments: List[Dict[str, Any]]
    confidence: float
    coverage_area_km2: Optional[float]
    recommended_inspection_points: List[Dict[str, Any]]
    reasoning: List[str]
    model_version: str
    inference_time_ms: float


@dataclass
class PipeSegment:
    """Pipe segment with attributes for risk calculation."""
    segment_id: str
    upstream_node: str
    downstream_node: str
    length_m: float
    diameter_mm: float
    material: str
    age_years: int
    failure_count: int
    last_inspection: Optional[datetime]
    street_name: str
    coordinates: Optional[Tuple[float, float]]  # (lat, lon)


@dataclass
class SensorNode:
    """Sensor node in the network."""
    sensor_id: str
    node_id: str
    sensor_type: str
    current_probability: float
    coordinates: Tuple[float, float]


class PipeNetworkGraph:
    """
    Represents the water distribution network as a graph.
    
    Nodes: Junctions, sensors, valves, hydrants
    Edges: Pipe segments
    
    Used for:
    1. Calculating distances between sensors and segments
    2. Tracing flow paths
    3. Identifying which segments are between sensors
    """
    
    def __init__(self):
        if not HAS_NETWORKX:
            raise ImportError("networkx required for network analysis")
        
        self.graph = nx.Graph()
        self.segments: Dict[str, PipeSegment] = {}
        self.sensors: Dict[str, SensorNode] = {}
        
    def add_segment(self, segment: PipeSegment) -> None:
        """Add a pipe segment to the network."""
        
        self.segments[segment.segment_id] = segment
        
        # Add edge with attributes
        self.graph.add_edge(
            segment.upstream_node,
            segment.downstream_node,
            segment_id=segment.segment_id,
            length=segment.length_m,
            material=segment.material,
            age=segment.age_years,
            diameter=segment.diameter_mm
        )
    
    def add_sensor(self, sensor: SensorNode) -> None:
        """Add a sensor to the network."""
        
        self.sensors[sensor.sensor_id] = sensor
        
        # Mark node as sensor location
        if sensor.node_id in self.graph:
            self.graph.nodes[sensor.node_id]['sensor_id'] = sensor.sensor_id
            self.graph.nodes[sensor.node_id]['coordinates'] = sensor.coordinates
    
    def get_distance_to_segment(
        self,
        sensor_id: str,
        segment_id: str
    ) -> float:
        """
        Calculate network distance from sensor to segment.
        
        Returns distance in meters.
        """
        if sensor_id not in self.sensors:
            return float('inf')
        
        if segment_id not in self.segments:
            return float('inf')
        
        sensor = self.sensors[sensor_id]
        segment = self.segments[segment_id]
        
        try:
            # Distance to upstream node
            dist_upstream = nx.shortest_path_length(
                self.graph,
                sensor.node_id,
                segment.upstream_node,
                weight='length'
            )
            
            # Distance to downstream node
            dist_downstream = nx.shortest_path_length(
                self.graph,
                sensor.node_id,
                segment.downstream_node,
                weight='length'
            )
            
            # Return minimum + half segment length
            return min(dist_upstream, dist_downstream) + segment.length_m / 2
            
        except nx.NetworkXNoPath:
            return float('inf')
    
    def get_segments_between_sensors(
        self,
        sensor1_id: str,
        sensor2_id: str
    ) -> List[str]:
        """Get all segments on the shortest path between two sensors."""
        
        if sensor1_id not in self.sensors or sensor2_id not in self.sensors:
            return []
        
        node1 = self.sensors[sensor1_id].node_id
        node2 = self.sensors[sensor2_id].node_id
        
        try:
            path = nx.shortest_path(self.graph, node1, node2, weight='length')
            
            segments = []
            for i in range(len(path) - 1):
                edge_data = self.graph.edges[path[i], path[i+1]]
                segments.append(edge_data['segment_id'])
            
            return segments
            
        except nx.NetworkXNoPath:
            return []
    
    def get_neighboring_sensors(
        self,
        sensor_id: str,
        max_distance: float = 2000
    ) -> List[Tuple[str, float]]:
        """Get sensors within max_distance meters."""
        
        if sensor_id not in self.sensors:
            return []
        
        source_node = self.sensors[sensor_id].node_id
        neighbors = []
        
        for other_id, other_sensor in self.sensors.items():
            if other_id == sensor_id:
                continue
            
            try:
                distance = nx.shortest_path_length(
                    self.graph,
                    source_node,
                    other_sensor.node_id,
                    weight='length'
                )
                
                if distance <= max_distance:
                    neighbors.append((other_id, distance))
                    
            except nx.NetworkXNoPath:
                continue
        
        return sorted(neighbors, key=lambda x: x[1])


class LeakLocalizer:
    """
    Layer 3: Localize leak to pipe segments using Bayesian inference.
    
    Method:
    -------
    1. Start with prior probabilities (based on pipe attributes)
    2. Update with sensor observations (likelihood)
    3. Use network topology to constrain possibilities
    4. Rank segments by posterior probability
    
    Physical Interpretation:
    -----------------------
    - Sensors closer to leak show higher probability
    - Leak effect decreases with distance (roughly exponentially)
    - Pipe attributes affect prior (older pipes more likely to leak)
    - Multiple sensors agreeing increases confidence
    """
    
    def __init__(
        self,
        network: Optional[PipeNetworkGraph] = None,
        decay_constant: float = 500.0  # meters
    ):
        """
        Initialize localizer.
        
        Args:
            network: Pipe network graph
            decay_constant: Distance at which leak signal decays by 63%
        """
        self.network = network
        self.decay_constant = decay_constant
        
        # Prior weights for pipe attributes
        self.material_priors = {
            'pvc': 0.3,
            'hdpe': 0.25,
            'ductile_iron': 0.5,
            'cast_iron': 0.8,
            'steel': 0.6,
            'asbestos_cement': 0.9,
            'concrete': 0.7,
            'unknown': 0.5
        }
        
        self.segment_priors: Dict[str, float] = {}
        
    def set_network(self, network: PipeNetworkGraph) -> None:
        """Set or update the network graph."""
        self.network = network
        self._calculate_priors()
    
    def _calculate_priors(self) -> None:
        """
        Calculate prior leak probability for each segment.
        
        Prior factors:
        1. Material (some materials more prone to failure)
        2. Age (older pipes more likely to fail)
        3. Failure history (past failures predict future)
        4. Diameter (smaller pipes more sensitive)
        """
        if self.network is None:
            return
        
        for segment_id, segment in self.network.segments.items():
            # Base prior: 1% per segment
            prior = 0.01
            
            # Material factor
            material_factor = self.material_priors.get(
                segment.material.lower(), 0.5
            )
            
            # Age factor (linear increase, caps at 50 years)
            age_factor = min(segment.age_years / 50, 1.0) if segment.age_years else 0.5
            
            # Failure history factor
            failure_factor = min(1 + segment.failure_count * 0.2, 2.0)
            
            # Combine factors
            prior *= (1 + material_factor + age_factor) / 3
            prior *= failure_factor
            
            # Cap at reasonable value
            self.segment_priors[segment_id] = min(prior, 0.1)
    
    def localize(
        self,
        sensor_probabilities: Dict[str, float],
        dma_id: str = 'unknown'
    ) -> LocalizationResult:
        """
        Localize leak based on sensor probabilities.
        
        Args:
            sensor_probabilities: {sensor_id: leak_probability} from Layer 2
            dma_id: DMA identifier
            
        Returns:
            LocalizationResult with ranked segments and explanations
        """
        import time
        start_time = time.time()
        
        reasoning = []
        
        if self.network is None or len(self.network.segments) == 0:
            return LocalizationResult(
                dma_id=dma_id,
                timestamp=datetime.utcnow(),
                ranked_segments=[],
                confidence=0.0,
                coverage_area_km2=None,
                recommended_inspection_points=[],
                reasoning=["No network data available"],
                model_version='3.0.0',
                inference_time_ms=0.0
            )
        
        # Update sensor probabilities in network
        for sensor_id, prob in sensor_probabilities.items():
            if sensor_id in self.network.sensors:
                self.network.sensors[sensor_id].current_probability = prob
        
        # Calculate posterior for each segment
        posteriors = {}
        
        for segment_id in self.network.segments:
            posterior = self._calculate_segment_posterior(
                segment_id, sensor_probabilities
            )
            posteriors[segment_id] = posterior
        
        # Normalize posteriors
        total = sum(posteriors.values())
        if total > 0:
            posteriors = {k: v/total for k, v in posteriors.items()}
        
        # Rank segments
        ranked = sorted(posteriors.items(), key=lambda x: x[1], reverse=True)
        
        # Build detailed results for top segments
        ranked_segments = []
        cumulative_prob = 0
        
        for segment_id, prob in ranked[:10]:
            segment = self.network.segments[segment_id]
            
            ranked_segments.append({
                'segment_id': segment_id,
                'probability': float(prob),
                'cumulative_probability': float(cumulative_prob + prob),
                'pipe_info': {
                    'material': segment.material,
                    'age_years': segment.age_years,
                    'length_m': segment.length_m,
                    'diameter_mm': segment.diameter_mm,
                    'street': segment.street_name,
                    'failure_count': segment.failure_count
                },
                'coordinates': segment.coordinates
            })
            
            cumulative_prob += prob
        
        # Calculate overall confidence
        confidence = self._calculate_localization_confidence(
            ranked_segments, sensor_probabilities
        )
        
        # Generate inspection recommendations
        inspection_points = self._generate_inspection_points(ranked_segments)
        
        # Add reasoning
        reasoning = self._generate_reasoning(
            ranked_segments, sensor_probabilities
        )
        
        inference_time = (time.time() - start_time) * 1000
        
        return LocalizationResult(
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            ranked_segments=ranked_segments,
            confidence=float(confidence),
            coverage_area_km2=None,  # Would require GIS calculation
            recommended_inspection_points=inspection_points,
            reasoning=reasoning,
            model_version='3.0.0',
            inference_time_ms=inference_time
        )
    
    def _calculate_segment_posterior(
        self,
        segment_id: str,
        sensor_probabilities: Dict[str, float]
    ) -> float:
        """
        Calculate posterior probability for a segment using Bayes' theorem.
        
        P(leak in segment | sensor observations) ∝ P(observations | leak in segment) × P(leak in segment)
        """
        # Prior probability
        prior = self.segment_priors.get(segment_id, 0.01)
        
        # Likelihood: How well do sensor observations match leak in this segment?
        likelihood = 1.0
        
        for sensor_id, observed_prob in sensor_probabilities.items():
            distance = self.network.get_distance_to_segment(sensor_id, segment_id)
            
            if distance == float('inf'):
                continue
            
            # Expected signal strength based on distance
            # Leak signal decays exponentially with distance
            expected_signal = np.exp(-distance / self.decay_constant)
            
            # Likelihood contribution
            # If sensor shows high probability and it's close, that's consistent
            # If sensor shows low probability and it's far, that's also consistent
            if observed_prob > 0.5:
                # Sensor indicates leak - closer sensors should show higher
                contribution = expected_signal * observed_prob
            else:
                # Sensor indicates no leak - farther sensors should show lower
                contribution = (1 - expected_signal) * (1 - observed_prob)
            
            likelihood *= max(contribution, 0.01)  # Avoid zero
        
        # Posterior ∝ Prior × Likelihood
        posterior = prior * likelihood
        
        return posterior
    
    def _calculate_localization_confidence(
        self,
        ranked_segments: List[Dict],
        sensor_probabilities: Dict[str, float]
    ) -> float:
        """
        Calculate confidence in localization.
        
        Factors:
        1. Concentration (top segments have most probability)
        2. Sensor agreement (multiple sensors with high probability)
        3. Number of sensors
        """
        if not ranked_segments:
            return 0.0
        
        # Factor 1: Concentration in top 3 segments
        top3_prob = sum(s['probability'] for s in ranked_segments[:3])
        concentration = min(top3_prob / 0.5, 1.0)  # 50% in top 3 = full credit
        
        # Factor 2: Sensor agreement
        high_prob_sensors = sum(1 for p in sensor_probabilities.values() if p > 0.5)
        agreement = min(high_prob_sensors / 2, 1.0)  # 2+ sensors agreeing = full credit
        
        # Factor 3: Number of sensors
        sensor_count = len(sensor_probabilities)
        coverage = min(sensor_count / 3, 1.0)  # 3+ sensors = full credit
        
        # Weighted combination
        confidence = 0.5 * concentration + 0.3 * agreement + 0.2 * coverage
        
        return confidence
    
    def _generate_inspection_points(
        self,
        ranked_segments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate recommended inspection points."""
        
        points = []
        
        for i, segment_data in enumerate(ranked_segments[:5]):
            segment_id = segment_data['segment_id']
            segment = self.network.segments.get(segment_id)
            
            if segment is None:
                continue
            
            points.append({
                'priority': i + 1,
                'segment_id': segment_id,
                'type': 'pipe_inspection',
                'location': segment.street_name,
                'coordinates': segment.coordinates,
                'recommended_method': self._recommend_method(segment),
                'probability': segment_data['probability']
            })
        
        return points
    
    def _recommend_method(self, segment: PipeSegment) -> str:
        """Recommend inspection method based on pipe characteristics."""
        
        if segment.diameter_mm < 200:
            return "Acoustic listening stick or correlator"
        elif segment.material in ['cast_iron', 'ductile_iron', 'steel']:
            return "Acoustic correlator or ground microphone"
        else:
            return "Ground microphone or tracer gas"
    
    def _generate_reasoning(
        self,
        ranked_segments: List[Dict],
        sensor_probabilities: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable reasoning for localization."""
        
        reasoning = []
        
        # Count high-probability sensors
        high_prob = sum(1 for p in sensor_probabilities.values() if p > 0.5)
        reasoning.append(
            f"{high_prob} of {len(sensor_probabilities)} sensors show elevated leak probability"
        )
        
        # Top segment reasoning
        if ranked_segments:
            top = ranked_segments[0]
            pipe = top['pipe_info']
            reasoning.append(
                f"Top candidate: {top['segment_id']} on {pipe['street']} "
                f"({pipe['material']}, {pipe['age_years']} years old, "
                f"{pipe['failure_count']} previous failures)"
            )
            
            # Coverage
            top3_prob = sum(s['probability'] for s in ranked_segments[:3])
            reasoning.append(
                f"Top 3 segments account for {top3_prob*100:.0f}% of probability"
            )
        
        return reasoning


class SimpleLocalizer:
    """
    Simplified localizer for deployments without full network model.
    
    Uses only sensor positions and simple distance-based weighting.
    Suitable for initial deployments before network GIS is available.
    """
    
    def __init__(self, decay_constant: float = 500.0):
        self.decay_constant = decay_constant
        self.sensor_positions: Dict[str, Tuple[float, float]] = {}
        self.dma_zones: Dict[str, Dict[str, Any]] = {}
    
    def add_sensor(
        self,
        sensor_id: str,
        lat: float,
        lon: float
    ) -> None:
        """Add sensor position."""
        self.sensor_positions[sensor_id] = (lat, lon)
    
    def add_zone(
        self,
        zone_id: str,
        name: str,
        center_lat: float,
        center_lon: float,
        description: str = ""
    ) -> None:
        """Add a named zone for localization."""
        self.dma_zones[zone_id] = {
            'name': name,
            'center': (center_lat, center_lon),
            'description': description
        }
    
    def localize(
        self,
        sensor_probabilities: Dict[str, float],
        dma_id: str = 'unknown'
    ) -> LocalizationResult:
        """
        Localize using weighted centroid of sensor probabilities.
        """
        import time
        start_time = time.time()
        
        if not sensor_probabilities:
            return LocalizationResult(
                dma_id=dma_id,
                timestamp=datetime.utcnow(),
                ranked_segments=[],
                confidence=0.0,
                coverage_area_km2=None,
                recommended_inspection_points=[],
                reasoning=["No sensor data provided"],
                model_version='simple_3.0.0',
                inference_time_ms=0.0
            )
        
        # Calculate weighted centroid
        total_weight = 0
        lat_sum = 0
        lon_sum = 0
        
        for sensor_id, prob in sensor_probabilities.items():
            if sensor_id in self.sensor_positions and prob > 0:
                lat, lon = self.sensor_positions[sensor_id]
                weight = prob ** 2  # Square to emphasize high-probability sensors
                lat_sum += lat * weight
                lon_sum += lon * weight
                total_weight += weight
        
        if total_weight > 0:
            estimated_lat = lat_sum / total_weight
            estimated_lon = lon_sum / total_weight
        else:
            # Fallback to simple average
            positions = [self.sensor_positions[s] for s in sensor_probabilities 
                        if s in self.sensor_positions]
            if positions:
                estimated_lat = np.mean([p[0] for p in positions])
                estimated_lon = np.mean([p[1] for p in positions])
            else:
                return LocalizationResult(
                    dma_id=dma_id,
                    timestamp=datetime.utcnow(),
                    ranked_segments=[],
                    confidence=0.0,
                    coverage_area_km2=None,
                    recommended_inspection_points=[],
                    reasoning=["No sensor positions available"],
                    model_version='simple_3.0.0',
                    inference_time_ms=0.0
                )
        
        # Find nearest zones
        ranked_zones = []
        for zone_id, zone_data in self.dma_zones.items():
            zone_lat, zone_lon = zone_data['center']
            distance = self._haversine_distance(
                estimated_lat, estimated_lon, zone_lat, zone_lon
            )
            ranked_zones.append({
                'segment_id': zone_id,
                'probability': 1.0 / (1 + distance / 100),  # Simple distance weighting
                'coordinates': zone_data['center'],
                'pipe_info': {
                    'street': zone_data['name'],
                    'description': zone_data['description']
                }
            })
        
        # Sort by probability
        ranked_zones.sort(key=lambda x: x['probability'], reverse=True)
        
        # Calculate confidence
        max_prob = max(sensor_probabilities.values())
        num_high = sum(1 for p in sensor_probabilities.values() if p > 0.5)
        confidence = min(max_prob * (1 + 0.2 * num_high), 1.0)
        
        # Generate inspection point at estimated location
        inspection_points = [{
            'priority': 1,
            'type': 'area_search',
            'coordinates': (estimated_lat, estimated_lon),
            'recommended_method': 'Acoustic survey of area'
        }]
        
        reasoning = [
            f"Estimated leak location based on {len(sensor_probabilities)} sensors",
            f"Highest sensor probability: {max_prob:.2f}",
            f"Estimated coordinates: {estimated_lat:.5f}, {estimated_lon:.5f}"
        ]
        
        inference_time = (time.time() - start_time) * 1000
        
        return LocalizationResult(
            dma_id=dma_id,
            timestamp=datetime.utcnow(),
            ranked_segments=ranked_zones[:5],
            confidence=float(confidence),
            coverage_area_km2=None,
            recommended_inspection_points=inspection_points,
            reasoning=reasoning,
            model_version='simple_3.0.0',
            inference_time_ms=inference_time
        )
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
