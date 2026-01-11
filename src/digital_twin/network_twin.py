"""
AquaWatch Digital Twin Engine
=============================
Virtual representation of the water distribution network with real-time simulation,
predictive modeling, and scenario analysis. Inspired by Xylem/Huawei digital twin technology.

Features:
- Real-time network state synchronization
- Hydraulic flow simulation
- Pressure propagation modeling
- Leak impact analysis
- What-if scenario testing
- Infrastructure stress analysis
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import math


class AssetType(Enum):
    """Types of network assets"""
    PIPE = "pipe"
    VALVE = "valve"
    PUMP = "pump"
    TANK = "tank"
    RESERVOIR = "reservoir"
    JUNCTION = "junction"
    METER = "meter"
    PRV = "pressure_reducing_valve"
    HYDRANT = "hydrant"


class AssetCondition(Enum):
    """Asset health conditions"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class NetworkNode:
    """Represents a junction/node in the network"""
    node_id: str
    name: str
    latitude: float
    longitude: float
    elevation: float  # meters above sea level
    base_demand: float  # liters per second
    node_type: str = "junction"  # junction, tank, reservoir
    
    # Real-time state
    pressure: float = 0.0  # bar
    head: float = 0.0  # meters
    actual_demand: float = 0.0
    quality: float = 0.0  # water quality index
    
    # For tanks/reservoirs
    volume: float = 0.0  # current volume (m³)
    max_volume: float = 0.0
    min_volume: float = 0.0
    level: float = 0.0  # water level (m)


@dataclass
class NetworkLink:
    """Represents a pipe/link in the network"""
    link_id: str
    name: str
    start_node: str
    end_node: str
    length: float  # meters
    diameter: float  # mm
    roughness: float  # Hazen-Williams coefficient
    asset_type: AssetType = AssetType.PIPE
    
    # Material and age
    material: str = "PVC"
    install_year: int = 2000
    expected_life: int = 50  # years
    
    # Real-time state
    flow_rate: float = 0.0  # liters per second
    velocity: float = 0.0  # m/s
    head_loss: float = 0.0  # meters
    status: str = "open"  # open, closed, cv (check valve)
    
    # Health metrics
    condition: AssetCondition = AssetCondition.GOOD
    break_history: List[Dict] = field(default_factory=list)
    leak_probability: float = 0.0


@dataclass
class SimulationScenario:
    """Defines a what-if scenario for simulation"""
    scenario_id: str
    name: str
    description: str
    changes: List[Dict]  # List of network changes
    duration_hours: int = 24
    created_at: datetime = field(default_factory=datetime.now)


class DigitalTwinEngine:
    """
    Core Digital Twin engine for water network simulation and analysis.
    Provides real-time network state, predictive modeling, and scenario analysis.
    """
    
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.links: Dict[str, NetworkLink] = {}
        self.sensors: Dict[str, Dict] = {}
        self.simulation_time = datetime.now()
        self.time_step = 3600  # seconds (1 hour default)
        
        # Hydraulic parameters
        self.gravity = 9.81  # m/s²
        self.water_density = 1000  # kg/m³
        
        # Simulation state
        self.is_running = False
        self.simulation_history: List[Dict] = []
        
        # Initialize sample network for Zambia
        self._initialize_sample_network()
    
    def _initialize_sample_network(self):
        """Initialize a sample water network for demonstration"""
        # Lusaka Water Network (simplified)
        nodes_data = [
            ("RES_IOLANDA", "Iolanda Reservoir", -15.3875, 28.3228, 1280, 0, "reservoir"),
            ("RES_CHELSTONE", "Chelstone Reservoir", -15.3542, 28.3667, 1260, 0, "reservoir"),
            ("TANK_MTENDERE", "Mtendere Tank", -15.4125, 28.3125, 1245, 0, "tank"),
            ("TANK_GARDEN", "Garden Tank", -15.4042, 28.2833, 1250, 0, "tank"),
            ("J_CBD", "CBD Junction", -15.4167, 28.2833, 1235, 45.0, "junction"),
            ("J_KABULONGA", "Kabulonga Junction", -15.3958, 28.3208, 1255, 35.0, "junction"),
            ("J_RHODES", "Rhodes Park Junction", -15.4083, 28.2958, 1245, 28.0, "junction"),
            ("J_WOODLANDS", "Woodlands Junction", -15.4250, 28.3083, 1240, 32.0, "junction"),
            ("J_KABWATA", "Kabwata Junction", -15.4375, 28.2917, 1238, 40.0, "junction"),
            ("J_CHILENJE", "Chilenje Junction", -15.4458, 28.2792, 1235, 38.0, "junction"),
            ("J_KAMWALA", "Kamwala Junction", -15.4292, 28.2708, 1232, 42.0, "junction"),
            ("J_INDUSTRIAL", "Industrial Area", -15.4417, 28.2625, 1230, 85.0, "junction"),
            ("J_MATERO", "Matero Junction", -15.3833, 28.2542, 1265, 55.0, "junction"),
            ("J_CHAWAMA", "Chawama Junction", -15.4583, 28.2833, 1228, 48.0, "junction"),
        ]
        
        for node_data in nodes_data:
            node_id, name, lat, lon, elev, demand, ntype = node_data
            node = NetworkNode(
                node_id=node_id,
                name=name,
                latitude=lat,
                longitude=lon,
                elevation=elev,
                base_demand=demand,
                node_type=ntype
            )
            if ntype == "tank":
                node.max_volume = 5000  # m³
                node.min_volume = 500
                node.volume = 3500
            elif ntype == "reservoir":
                node.max_volume = 50000  # m³
                node.volume = 45000
            self.nodes[node_id] = node
        
        # Define pipes/links
        pipes_data = [
            ("P_IOLANDA_CBD", "Iolanda Main", "RES_IOLANDA", "J_CBD", 4500, 600, 130, "Ductile Iron", 1985),
            ("P_IOLANDA_MATERO", "Iolanda-Matero", "RES_IOLANDA", "J_MATERO", 3200, 450, 120, "Steel", 1990),
            ("P_CHELSTONE_KAB", "Chelstone-Kabulonga", "RES_CHELSTONE", "J_KABULONGA", 2800, 400, 140, "PVC", 2010),
            ("P_CBD_RHODES", "CBD-Rhodes", "J_CBD", "J_RHODES", 1200, 350, 135, "Ductile Iron", 1988),
            ("P_CBD_KAMWALA", "CBD-Kamwala", "J_CBD", "J_KAMWALA", 1500, 300, 130, "Steel", 1975),
            ("P_RHODES_WOOD", "Rhodes-Woodlands", "J_RHODES", "J_WOODLANDS", 1800, 250, 140, "PVC", 2005),
            ("P_WOOD_KABWATA", "Woodlands-Kabwata", "J_WOODLANDS", "J_KABWATA", 1400, 200, 145, "HDPE", 2015),
            ("P_KABWATA_CHILENJE", "Kabwata-Chilenje", "J_KABWATA", "J_CHILENJE", 1100, 200, 140, "PVC", 2008),
            ("P_KAMWALA_IND", "Kamwala-Industrial", "J_KAMWALA", "J_INDUSTRIAL", 2200, 400, 125, "Steel", 1980),
            ("P_CHILENJE_CHAWAMA", "Chilenje-Chawama", "J_CHILENJE", "J_CHAWAMA", 1600, 250, 135, "PVC", 2012),
            ("P_KAB_RHODES", "Kabulonga-Rhodes", "J_KABULONGA", "J_RHODES", 2100, 300, 140, "PVC", 2008),
            ("P_TANK_MTD", "Mtendere Supply", "TANK_MTENDERE", "J_WOODLANDS", 1900, 350, 145, "HDPE", 2018),
            ("P_TANK_GARDEN", "Garden Supply", "TANK_GARDEN", "J_CBD", 800, 400, 140, "Ductile Iron", 1995),
        ]
        
        for pipe_data in pipes_data:
            pipe_id, name, start, end, length, dia, rough, material, year = pipe_data
            age = datetime.now().year - year
            condition = self._calculate_condition(age, 50, material)
            
            link = NetworkLink(
                link_id=pipe_id,
                name=name,
                start_node=start,
                end_node=end,
                length=length,
                diameter=dia,
                roughness=rough,
                material=material,
                install_year=year,
                condition=condition,
                leak_probability=self._estimate_leak_probability(age, material, condition)
            )
            self.links[pipe_id] = link
    
    def _calculate_condition(self, age: int, expected_life: int, material: str) -> AssetCondition:
        """Calculate asset condition based on age and material"""
        life_ratio = age / expected_life
        
        # Material degradation factors
        material_factors = {
            "PVC": 1.0,
            "HDPE": 0.9,
            "Ductile Iron": 1.1,
            "Steel": 1.3,
            "Asbestos Cement": 1.5,
            "Cast Iron": 1.4
        }
        factor = material_factors.get(material, 1.2)
        adjusted_ratio = life_ratio * factor
        
        if adjusted_ratio < 0.3:
            return AssetCondition.EXCELLENT
        elif adjusted_ratio < 0.5:
            return AssetCondition.GOOD
        elif adjusted_ratio < 0.7:
            return AssetCondition.FAIR
        elif adjusted_ratio < 0.9:
            return AssetCondition.POOR
        else:
            return AssetCondition.CRITICAL
    
    def _estimate_leak_probability(self, age: int, material: str, condition: AssetCondition) -> float:
        """Estimate probability of leak based on asset characteristics"""
        # Base probability by condition
        base_prob = {
            AssetCondition.EXCELLENT: 0.01,
            AssetCondition.GOOD: 0.03,
            AssetCondition.FAIR: 0.08,
            AssetCondition.POOR: 0.15,
            AssetCondition.CRITICAL: 0.30
        }
        
        # Material factors
        material_factor = {
            "PVC": 0.8,
            "HDPE": 0.7,
            "Ductile Iron": 1.0,
            "Steel": 1.3,
            "Cast Iron": 1.5,
            "Asbestos Cement": 1.8
        }
        
        prob = base_prob[condition] * material_factor.get(material, 1.2)
        # Age factor
        prob *= (1 + age / 100)
        
        return min(prob, 0.95)  # Cap at 95%
    
    def sync_sensor_data(self, sensor_id: str, readings: Dict):
        """
        Synchronize real sensor data with digital twin.
        Updates the virtual network state based on actual measurements.
        """
        self.sensors[sensor_id] = {
            "last_reading": readings,
            "timestamp": datetime.now(),
            "synced": True
        }
        
        # Update corresponding network element
        if "node_id" in readings:
            node_id = readings["node_id"]
            if node_id in self.nodes:
                if "pressure" in readings:
                    self.nodes[node_id].pressure = readings["pressure"]
                if "flow" in readings:
                    self.nodes[node_id].actual_demand = readings["flow"]
                if "quality" in readings:
                    self.nodes[node_id].quality = readings["quality"]
        
        if "link_id" in readings:
            link_id = readings["link_id"]
            if link_id in self.links:
                if "flow_rate" in readings:
                    self.links[link_id].flow_rate = readings["flow_rate"]
                if "velocity" in readings:
                    self.links[link_id].velocity = readings["velocity"]
    
    def run_hydraulic_simulation(self, duration_hours: int = 24) -> Dict:
        """
        Run hydraulic simulation for the network.
        Calculates pressures, flows, and head losses throughout the network.
        """
        self.is_running = True
        results = {
            "simulation_id": f"SIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": self.simulation_time.isoformat(),
            "duration_hours": duration_hours,
            "timesteps": [],
            "warnings": [],
            "summary": {}
        }
        
        for hour in range(duration_hours):
            timestep_result = self._simulate_timestep(hour)
            results["timesteps"].append(timestep_result)
            
            # Check for warnings
            for node_id, node in self.nodes.items():
                if node.node_type == "junction" and node.pressure < 1.5:
                    results["warnings"].append({
                        "time": hour,
                        "type": "low_pressure",
                        "node": node_id,
                        "value": node.pressure,
                        "message": f"Low pressure at {node.name}: {node.pressure:.2f} bar"
                    })
        
        # Calculate summary statistics
        results["summary"] = self._calculate_simulation_summary(results["timesteps"])
        
        self.is_running = False
        self.simulation_history.append(results)
        
        return results
    
    def _simulate_timestep(self, hour: int) -> Dict:
        """Simulate a single timestep"""
        # Demand pattern (typical daily pattern for Zambia)
        demand_multipliers = [
            0.6, 0.5, 0.4, 0.4, 0.5, 0.7,  # 00:00-05:00
            0.9, 1.2, 1.4, 1.3, 1.1, 1.0,  # 06:00-11:00
            1.1, 1.0, 0.9, 0.9, 1.0, 1.3,  # 12:00-17:00
            1.4, 1.3, 1.1, 0.9, 0.8, 0.7   # 18:00-23:00
        ]
        
        multiplier = demand_multipliers[hour % 24]
        
        # Update demands
        for node in self.nodes.values():
            if node.node_type == "junction":
                node.actual_demand = node.base_demand * multiplier * np.random.uniform(0.9, 1.1)
        
        # Simple pressure propagation (simplified hydraulic calculation)
        for link in self.links.values():
            start_node = self.nodes.get(link.start_node)
            end_node = self.nodes.get(link.end_node)
            
            if start_node and end_node:
                # Hazen-Williams head loss calculation
                if link.diameter > 0 and link.length > 0:
                    # Estimate flow based on demands
                    link.flow_rate = end_node.actual_demand * 1.2  # Account for downstream
                    
                    # Head loss (Hazen-Williams)
                    Q = link.flow_rate / 1000  # m³/s
                    D = link.diameter / 1000  # m
                    L = link.length
                    C = link.roughness
                    
                    if Q > 0 and D > 0:
                        link.head_loss = 10.67 * L * (Q ** 1.852) / ((C ** 1.852) * (D ** 4.87))
                        link.velocity = Q / (math.pi * (D/2)**2)
                    
                    # Update end node pressure
                    if start_node.node_type in ["reservoir", "tank"]:
                        head_available = start_node.elevation + 10  # Assume 10m head at source
                    else:
                        head_available = start_node.elevation + start_node.pressure * 10.2
                    
                    end_head = head_available - link.head_loss - (end_node.elevation - start_node.elevation)
                    end_node.pressure = max(0, end_head / 10.2)  # Convert to bar
        
        # Collect timestep results
        return {
            "hour": hour,
            "node_pressures": {n.node_id: n.pressure for n in self.nodes.values()},
            "node_demands": {n.node_id: n.actual_demand for n in self.nodes.values()},
            "link_flows": {l.link_id: l.flow_rate for l in self.links.values()},
            "link_velocities": {l.link_id: l.velocity for l in self.links.values()}
        }
    
    def _calculate_simulation_summary(self, timesteps: List[Dict]) -> Dict:
        """Calculate summary statistics from simulation"""
        all_pressures = []
        all_flows = []
        
        for ts in timesteps:
            all_pressures.extend(ts["node_pressures"].values())
            all_flows.extend(ts["link_flows"].values())
        
        return {
            "min_pressure": min(all_pressures) if all_pressures else 0,
            "max_pressure": max(all_pressures) if all_pressures else 0,
            "avg_pressure": np.mean(all_pressures) if all_pressures else 0,
            "total_demand": sum(all_flows),
            "timesteps_analyzed": len(timesteps)
        }
    
    def simulate_leak_scenario(self, link_id: str, leak_rate: float) -> Dict:
        """
        Simulate the impact of a leak on the network.
        
        Args:
            link_id: ID of the pipe with leak
            leak_rate: Leak rate in liters per second
        
        Returns:
            Impact analysis including affected nodes and pressure changes
        """
        if link_id not in self.links:
            return {"error": f"Link {link_id} not found"}
        
        link = self.links[link_id]
        
        # Store original state
        original_state = {
            node_id: node.pressure for node_id, node in self.nodes.items()
        }
        
        # Apply leak as additional demand at end node
        end_node = self.nodes.get(link.end_node)
        if end_node:
            original_demand = end_node.actual_demand
            end_node.actual_demand += leak_rate
        
        # Run quick simulation
        self._simulate_timestep(12)  # Peak hour
        
        # Calculate impacts
        impacts = []
        for node_id, node in self.nodes.items():
            if node.node_type == "junction":
                pressure_drop = original_state[node_id] - node.pressure
                if pressure_drop > 0.1:  # Significant drop
                    impacts.append({
                        "node_id": node_id,
                        "node_name": node.name,
                        "original_pressure": original_state[node_id],
                        "new_pressure": node.pressure,
                        "pressure_drop": pressure_drop,
                        "severity": "high" if pressure_drop > 0.5 else "medium"
                    })
        
        # Restore original state
        if end_node:
            end_node.actual_demand = original_demand
        
        # Estimate water loss
        daily_loss = leak_rate * 3600 * 24 / 1000  # m³/day
        annual_loss = daily_loss * 365
        cost_per_m3 = 5.50  # ZMW per m³
        
        return {
            "scenario": "leak_simulation",
            "link_id": link_id,
            "link_name": link.name,
            "leak_rate_lps": leak_rate,
            "affected_nodes": sorted(impacts, key=lambda x: x["pressure_drop"], reverse=True),
            "water_loss": {
                "daily_m3": daily_loss,
                "annual_m3": annual_loss,
                "daily_cost_zmw": daily_loss * cost_per_m3,
                "annual_cost_zmw": annual_loss * cost_per_m3
            },
            "recommendation": self._get_leak_recommendation(leak_rate, len(impacts))
        }
    
    def _get_leak_recommendation(self, leak_rate: float, affected_count: int) -> str:
        """Generate recommendation based on leak severity"""
        if leak_rate > 10:
            return "CRITICAL: Immediate repair required. Consider emergency isolation."
        elif leak_rate > 5:
            return "HIGH PRIORITY: Schedule repair within 24 hours."
        elif leak_rate > 2:
            return "MEDIUM PRIORITY: Schedule repair within 1 week."
        else:
            return "LOW PRIORITY: Monitor and schedule during routine maintenance."
    
    def run_scenario_analysis(self, scenario: SimulationScenario) -> Dict:
        """
        Run a what-if scenario analysis.
        
        Scenarios can include:
        - Pipe closures for maintenance
        - New infrastructure additions
        - Demand changes
        - Pump failures
        """
        results = {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.name,
            "description": scenario.description,
            "changes_applied": [],
            "impacts": [],
            "before_state": {},
            "after_state": {}
        }
        
        # Store before state
        results["before_state"] = {
            "node_pressures": {n.node_id: n.pressure for n in self.nodes.values()},
            "link_flows": {l.link_id: l.flow_rate for l in self.links.values()}
        }
        
        # Apply changes
        for change in scenario.changes:
            change_type = change.get("type")
            
            if change_type == "close_pipe":
                link_id = change.get("link_id")
                if link_id in self.links:
                    self.links[link_id].status = "closed"
                    results["changes_applied"].append(f"Closed pipe: {link_id}")
            
            elif change_type == "increase_demand":
                node_id = change.get("node_id")
                increase = change.get("increase", 0)
                if node_id in self.nodes:
                    self.nodes[node_id].base_demand += increase
                    results["changes_applied"].append(
                        f"Increased demand at {node_id} by {increase} L/s"
                    )
            
            elif change_type == "add_pump":
                # Simulate pump addition by increasing available head
                node_id = change.get("node_id")
                head_increase = change.get("head", 20)  # meters
                if node_id in self.nodes:
                    self.nodes[node_id].head += head_increase
                    results["changes_applied"].append(
                        f"Added pump at {node_id} with {head_increase}m head"
                    )
        
        # Run simulation with changes
        sim_results = self.run_hydraulic_simulation(scenario.duration_hours)
        
        # Store after state
        results["after_state"] = {
            "node_pressures": {n.node_id: n.pressure for n in self.nodes.values()},
            "link_flows": {l.link_id: l.flow_rate for l in self.links.values()}
        }
        
        # Analyze impacts
        for node_id in self.nodes:
            before = results["before_state"]["node_pressures"].get(node_id, 0)
            after = results["after_state"]["node_pressures"].get(node_id, 0)
            change_pct = ((after - before) / before * 100) if before > 0 else 0
            
            if abs(change_pct) > 5:  # Significant change
                results["impacts"].append({
                    "node_id": node_id,
                    "metric": "pressure",
                    "before": before,
                    "after": after,
                    "change_percent": change_pct
                })
        
        results["simulation_summary"] = sim_results["summary"]
        results["warnings"] = sim_results["warnings"]
        
        return results
    
    def get_network_state(self) -> Dict:
        """Get current state of the entire network"""
        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                node_id: {
                    "name": node.name,
                    "type": node.node_type,
                    "coordinates": [node.latitude, node.longitude],
                    "elevation": node.elevation,
                    "pressure": node.pressure,
                    "demand": node.actual_demand,
                    "quality": node.quality
                }
                for node_id, node in self.nodes.items()
            },
            "links": {
                link_id: {
                    "name": link.name,
                    "type": link.asset_type.value,
                    "start": link.start_node,
                    "end": link.end_node,
                    "length": link.length,
                    "diameter": link.diameter,
                    "material": link.material,
                    "age": datetime.now().year - link.install_year,
                    "condition": link.condition.value,
                    "flow_rate": link.flow_rate,
                    "velocity": link.velocity,
                    "leak_probability": link.leak_probability,
                    "status": link.status
                }
                for link_id, link in self.links.items()
            },
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_links": len(self.links),
                "total_pipe_length_km": sum(l.length for l in self.links.values()) / 1000,
                "avg_pipe_age": np.mean([datetime.now().year - l.install_year for l in self.links.values()]),
                "critical_assets": sum(1 for l in self.links.values() if l.condition == AssetCondition.CRITICAL)
            }
        }
    
    def export_to_geojson(self) -> Dict:
        """Export network to GeoJSON format for mapping"""
        features = []
        
        # Export nodes as points
        for node_id, node in self.nodes.items():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [node.longitude, node.latitude]
                },
                "properties": {
                    "id": node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "elevation": node.elevation,
                    "pressure": node.pressure,
                    "demand": node.actual_demand
                }
            })
        
        # Export links as lines
        for link_id, link in self.links.items():
            start_node = self.nodes.get(link.start_node)
            end_node = self.nodes.get(link.end_node)
            
            if start_node and end_node:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [start_node.longitude, start_node.latitude],
                            [end_node.longitude, end_node.latitude]
                        ]
                    },
                    "properties": {
                        "id": link_id,
                        "name": link.name,
                        "type": link.asset_type.value,
                        "diameter": link.diameter,
                        "material": link.material,
                        "condition": link.condition.value,
                        "flow_rate": link.flow_rate,
                        "leak_probability": link.leak_probability
                    }
                })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }


# Initialize global digital twin instance
digital_twin = DigitalTwinEngine()


def get_digital_twin() -> DigitalTwinEngine:
    """Get the global digital twin instance"""
    return digital_twin


if __name__ == "__main__":
    # Demo
    twin = DigitalTwinEngine()
    
    print("=" * 60)
    print("AquaWatch Digital Twin Engine")
    print("=" * 60)
    
    # Get network state
    state = twin.get_network_state()
    print(f"\nNetwork Statistics:")
    print(f"  Total Nodes: {state['statistics']['total_nodes']}")
    print(f"  Total Links: {state['statistics']['total_links']}")
    print(f"  Total Pipe Length: {state['statistics']['total_pipe_length_km']:.1f} km")
    print(f"  Average Pipe Age: {state['statistics']['avg_pipe_age']:.1f} years")
    print(f"  Critical Assets: {state['statistics']['critical_assets']}")
    
    # Run simulation
    print("\nRunning 24-hour hydraulic simulation...")
    results = twin.run_hydraulic_simulation(24)
    print(f"  Simulation ID: {results['simulation_id']}")
    print(f"  Min Pressure: {results['summary']['min_pressure']:.2f} bar")
    print(f"  Max Pressure: {results['summary']['max_pressure']:.2f} bar")
    print(f"  Warnings: {len(results['warnings'])}")
    
    # Simulate leak
    print("\nSimulating leak scenario...")
    leak_impact = twin.simulate_leak_scenario("P_CBD_KAMWALA", 5.0)
    print(f"  Leak Rate: {leak_impact['leak_rate_lps']} L/s")
    print(f"  Daily Water Loss: {leak_impact['water_loss']['daily_m3']:.1f} m³")
    print(f"  Annual Cost: ZMW {leak_impact['water_loss']['annual_cost_zmw']:,.0f}")
    print(f"  Affected Nodes: {len(leak_impact['affected_nodes'])}")
    print(f"  Recommendation: {leak_impact['recommendation']}")
