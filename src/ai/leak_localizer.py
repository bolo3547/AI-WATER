"""
AquaWatch AI - Leak Localization Engine
=======================================
Localizes leaks to pipe segments using:
- Pressure wave analysis
- Network topology
- Multi-sensor correlation
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


@dataclass
class PipeSegment:
    """Represents a pipe segment in the network."""
    segment_id: str
    pipe_id: str
    start_node: str
    end_node: str
    length_m: float
    diameter_mm: float
    material: str
    age_years: int
    sensors: List[str]


@dataclass
class LeakLocation:
    """Result of leak localization."""
    segment_id: str
    pipe_id: str
    estimated_distance_m: float
    confidence: float
    probability_map: Dict[str, float]
    contributing_sensors: List[str]
    timestamp: datetime


class NetworkTopology:
    """Manages the pipe network topology."""
    
    def __init__(self):
        self.segments: Dict[str, PipeSegment] = {}
        self.nodes: Dict[str, List[str]] = {}  # node_id -> connected segment_ids
        self.sensor_locations: Dict[str, str] = {}  # sensor_id -> segment_id
    
    def add_segment(self, segment: PipeSegment):
        """Add a pipe segment to the network."""
        self.segments[segment.segment_id] = segment
        
        # Update node connections
        for node in [segment.start_node, segment.end_node]:
            if node not in self.nodes:
                self.nodes[node] = []
            self.nodes[node].append(segment.segment_id)
        
        # Register sensors
        for sensor_id in segment.sensors:
            self.sensor_locations[sensor_id] = segment.segment_id
    
    def get_adjacent_segments(self, segment_id: str) -> List[str]:
        """Get segments adjacent to the given segment."""
        if segment_id not in self.segments:
            return []
        
        segment = self.segments[segment_id]
        adjacent = []
        
        for node in [segment.start_node, segment.end_node]:
            for adj_segment_id in self.nodes.get(node, []):
                if adj_segment_id != segment_id and adj_segment_id not in adjacent:
                    adjacent.append(adj_segment_id)
        
        return adjacent
    
    def get_path_between_sensors(self, sensor1: str, sensor2: str) -> List[str]:
        """Find path between two sensors using BFS."""
        if sensor1 not in self.sensor_locations or sensor2 not in self.sensor_locations:
            return []
        
        start_segment = self.sensor_locations[sensor1]
        end_segment = self.sensor_locations[sensor2]
        
        if start_segment == end_segment:
            return [start_segment]
        
        # BFS
        visited = {start_segment}
        queue = [[start_segment]]
        
        while queue:
            path = queue.pop(0)
            current = path[-1]
            
            for adjacent in self.get_adjacent_segments(current):
                if adjacent == end_segment:
                    return path + [adjacent]
                
                if adjacent not in visited:
                    visited.add(adjacent)
                    queue.append(path + [adjacent])
        
        return []
    
    def save(self, filepath: str):
        """Save topology to file."""
        data = {
            "segments": {
                k: {
                    "segment_id": v.segment_id,
                    "pipe_id": v.pipe_id,
                    "start_node": v.start_node,
                    "end_node": v.end_node,
                    "length_m": v.length_m,
                    "diameter_mm": v.diameter_mm,
                    "material": v.material,
                    "age_years": v.age_years,
                    "sensors": v.sensors
                }
                for k, v in self.segments.items()
            }
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """Load topology from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for seg_data in data.get("segments", {}).values():
            segment = PipeSegment(**seg_data)
            self.add_segment(segment)


class PressureWaveAnalyzer:
    """Analyzes pressure waves for leak localization."""
    
    def __init__(self, wave_speed_ms: float = 1200):
        """
        Args:
            wave_speed_ms: Speed of pressure wave in m/s (typical: 1000-1400)
        """
        self.wave_speed = wave_speed_ms
    
    def estimate_distance(self, sensor1_time: datetime, sensor2_time: datetime,
                         sensor1_distance: float, sensor2_distance: float) -> float:
        """
        Estimate leak distance using pressure wave arrival times.
        
        Uses the formula:
        d = (L + v*Δt) / 2
        
        Where:
        - L = distance between sensors
        - v = wave speed
        - Δt = time difference between sensor detections
        """
        total_distance = sensor1_distance + sensor2_distance
        time_diff = (sensor2_time - sensor1_time).total_seconds()
        
        # Distance from sensor1
        distance = (total_distance + self.wave_speed * time_diff) / 2
        
        # Clamp to valid range
        distance = max(0, min(distance, total_distance))
        
        return distance
    
    def calculate_confidence(self, time_diff: float, expected_diff: float) -> float:
        """Calculate confidence based on time difference consistency."""
        if expected_diff == 0:
            return 0.5
        
        ratio = abs(time_diff - expected_diff) / expected_diff
        confidence = max(0, 1 - ratio)
        
        return confidence


class LeakLocalizer:
    """
    Main leak localization engine.
    
    Combines multiple techniques:
    1. Pressure wave timing analysis
    2. Pressure gradient analysis
    3. Network topology constraints
    4. Historical leak data
    """
    
    def __init__(self, topology: NetworkTopology = None):
        self.topology = topology or NetworkTopology()
        self.wave_analyzer = PressureWaveAnalyzer()
        
        # Store recent pressure drops for correlation
        self.pressure_drops: Dict[str, List[Tuple[datetime, float]]] = {}
        
        # Historical leak locations for Bayesian prior
        self.leak_history: Dict[str, int] = {}  # segment_id -> leak count
    
    def record_pressure_drop(self, sensor_id: str, timestamp: datetime, magnitude: float):
        """Record a pressure drop event from a sensor."""
        if sensor_id not in self.pressure_drops:
            self.pressure_drops[sensor_id] = []
        
        self.pressure_drops[sensor_id].append((timestamp, magnitude))
        
        # Keep only last hour
        cutoff = timestamp - timedelta(hours=1)
        self.pressure_drops[sensor_id] = [
            (t, m) for t, m in self.pressure_drops[sensor_id] if t > cutoff
        ]
    
    def localize(self, primary_sensor: str, timestamp: datetime,
                pressure_drop: float) -> Optional[LeakLocation]:
        """
        Localize a suspected leak.
        
        Args:
            primary_sensor: Sensor that detected the main anomaly
            timestamp: Time of detection
            pressure_drop: Magnitude of pressure drop
        
        Returns:
            LeakLocation with probability map
        """
        # Get segment where primary sensor is located
        if primary_sensor not in self.topology.sensor_locations:
            return None
        
        primary_segment = self.topology.sensor_locations[primary_sensor]
        
        # Find correlated pressure drops from nearby sensors
        correlated_drops = self._find_correlated_drops(primary_sensor, timestamp)
        
        # Calculate probability for each segment
        probability_map = {}
        contributing_sensors = [primary_sensor]
        
        # Start with primary segment having highest probability
        probability_map[primary_segment] = 0.5
        
        # Adjust based on correlated sensors
        for sensor_id, (drop_time, drop_magnitude) in correlated_drops.items():
            contributing_sensors.append(sensor_id)
            sensor_segment = self.topology.sensor_locations.get(sensor_id)
            
            if sensor_segment:
                # Path between sensors
                path = self.topology.get_path_between_sensors(primary_sensor, sensor_id)
                
                if path:
                    # Distribute probability along path based on timing
                    time_diff = (drop_time - timestamp).total_seconds()
                    
                    for i, seg_id in enumerate(path):
                        # Earlier segments get higher probability
                        position_factor = 1 - (i / len(path))
                        
                        # Magnitude correlation
                        magnitude_factor = min(drop_magnitude / pressure_drop, 1) if pressure_drop > 0 else 0.5
                        
                        seg_prob = position_factor * magnitude_factor * 0.3
                        
                        if seg_id in probability_map:
                            probability_map[seg_id] = min(probability_map[seg_id] + seg_prob, 1.0)
                        else:
                            probability_map[seg_id] = seg_prob
        
        # Add adjacent segments with lower probability
        for seg_id in self.topology.get_adjacent_segments(primary_segment):
            if seg_id not in probability_map:
                probability_map[seg_id] = 0.15
        
        # Apply historical prior
        probability_map = self._apply_historical_prior(probability_map)
        
        # Normalize probabilities
        total = sum(probability_map.values())
        if total > 0:
            probability_map = {k: v/total for k, v in probability_map.items()}
        
        # Find most likely segment
        if not probability_map:
            return None
        
        best_segment = max(probability_map, key=probability_map.get)
        confidence = probability_map[best_segment]
        
        # Estimate distance within segment
        segment = self.topology.segments.get(best_segment)
        estimated_distance = segment.length_m / 2 if segment else 0
        
        # Refine with wave analysis if multiple sensors
        if len(contributing_sensors) >= 2:
            estimated_distance = self._refine_distance(
                best_segment, contributing_sensors, timestamp
            )
        
        return LeakLocation(
            segment_id=best_segment,
            pipe_id=segment.pipe_id if segment else "unknown",
            estimated_distance_m=estimated_distance,
            confidence=confidence,
            probability_map=probability_map,
            contributing_sensors=contributing_sensors,
            timestamp=timestamp
        )
    
    def _find_correlated_drops(self, primary_sensor: str, timestamp: datetime,
                               window_seconds: float = 30) -> Dict[str, Tuple[datetime, float]]:
        """Find pressure drops from other sensors within time window."""
        correlated = {}
        
        for sensor_id, drops in self.pressure_drops.items():
            if sensor_id == primary_sensor:
                continue
            
            for drop_time, magnitude in drops:
                time_diff = abs((drop_time - timestamp).total_seconds())
                if time_diff <= window_seconds:
                    # Keep the drop closest in time
                    if sensor_id not in correlated:
                        correlated[sensor_id] = (drop_time, magnitude)
                    else:
                        existing_diff = abs((correlated[sensor_id][0] - timestamp).total_seconds())
                        if time_diff < existing_diff:
                            correlated[sensor_id] = (drop_time, magnitude)
        
        return correlated
    
    def _apply_historical_prior(self, probability_map: Dict[str, float]) -> Dict[str, float]:
        """Apply Bayesian prior based on historical leak locations."""
        if not self.leak_history:
            return probability_map
        
        total_leaks = sum(self.leak_history.values())
        
        for seg_id in probability_map:
            historical_count = self.leak_history.get(seg_id, 0)
            prior = (historical_count + 1) / (total_leaks + len(self.topology.segments))
            
            # Combine prior with current probability (weighted average)
            probability_map[seg_id] = 0.7 * probability_map[seg_id] + 0.3 * prior
        
        return probability_map
    
    def _refine_distance(self, segment_id: str, sensors: List[str],
                        timestamp: datetime) -> float:
        """Refine distance estimate using wave analysis."""
        segment = self.topology.segments.get(segment_id)
        if not segment:
            return 0
        
        # Find sensors on this segment
        segment_sensors = [s for s in sensors if s in segment.sensors]
        
        if len(segment_sensors) < 2:
            return segment.length_m / 2
        
        # Get drop times for these sensors
        drop_times = []
        for sensor_id in segment_sensors[:2]:
            if sensor_id in self.pressure_drops and self.pressure_drops[sensor_id]:
                # Find closest drop to timestamp
                closest = min(self.pressure_drops[sensor_id],
                            key=lambda x: abs((x[0] - timestamp).total_seconds()))
                drop_times.append(closest[0])
        
        if len(drop_times) < 2:
            return segment.length_m / 2
        
        # Use wave analyzer
        distance = self.wave_analyzer.estimate_distance(
            drop_times[0], drop_times[1],
            0, segment.length_m  # Assume sensors at segment ends
        )
        
        return distance
    
    def record_confirmed_leak(self, segment_id: str):
        """Record a confirmed leak for historical prior."""
        if segment_id not in self.leak_history:
            self.leak_history[segment_id] = 0
        self.leak_history[segment_id] += 1


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("\n🎯 AquaWatch Leak Localization Engine")
    print("=" * 50)
    
    # Create network topology
    topology = NetworkTopology()
    
    # Add pipe segments (example network)
    segments = [
        PipeSegment("SEG-001", "Pipe_A1", "N1", "N2", 500, 200, "PVC", 10, ["S1", "S2"]),
        PipeSegment("SEG-002", "Pipe_A1", "N2", "N3", 300, 200, "PVC", 10, ["S3"]),
        PipeSegment("SEG-003", "Pipe_A2", "N2", "N4", 400, 150, "HDPE", 5, ["S4", "S5"]),
        PipeSegment("SEG-004", "Pipe_A2", "N4", "N5", 350, 150, "HDPE", 5, ["S6"]),
    ]
    
    for seg in segments:
        topology.add_segment(seg)
    
    print(f"✅ Network loaded: {len(topology.segments)} segments, {len(topology.nodes)} nodes")
    
    # Create localizer
    localizer = LeakLocalizer(topology)
    
    # Simulate pressure drop events
    now = datetime.now()
    
    localizer.record_pressure_drop("S1", now, 0.5)
    localizer.record_pressure_drop("S2", now + timedelta(seconds=0.5), 0.4)
    localizer.record_pressure_drop("S3", now + timedelta(seconds=1.2), 0.3)
    
    # Localize the leak
    result = localizer.localize("S1", now, 0.5)
    
    if result:
        print(f"\n📍 Leak Localization Result:")
        print(f"   Segment: {result.segment_id}")
        print(f"   Pipe: {result.pipe_id}")
        print(f"   Estimated Distance: {result.estimated_distance_m:.0f} m from start")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Contributing Sensors: {', '.join(result.contributing_sensors)}")
        print(f"\n   Probability Map:")
        for seg_id, prob in sorted(result.probability_map.items(), key=lambda x: -x[1]):
            print(f"      {seg_id}: {prob:.1%}")
    
    print("\n✅ Leak Localization Engine ready!")
