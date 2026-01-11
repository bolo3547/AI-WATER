"""
AquaWatch Dynamic Pressure Management
=====================================
AI-optimized pressure zone management to reduce leakage and improve service.
Inspired by Chinese smart water systems (Huawei/Alibaba).

Features:
- Real-time pressure optimization
- Pressure zone modeling
- Leak-pressure correlation
- Pump scheduling optimization
- PRV (Pressure Reducing Valve) control
- Critical point monitoring
- Energy efficiency optimization
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from collections import defaultdict


class PressureZoneType(Enum):
    """Types of pressure zones"""
    HIGH_LEVEL = "high_level"        # Elevated areas
    LOW_LEVEL = "low_level"          # Low-lying areas
    MIXED = "mixed"                  # Variable elevation
    INDUSTRIAL = "industrial"        # High demand
    RESIDENTIAL = "residential"      # Standard residential
    COMMERCIAL = "commercial"        # Commercial areas


class ControllerType(Enum):
    """Types of pressure controllers"""
    PRV = "pressure_reducing_valve"
    PSV = "pressure_sustaining_valve"
    PUMP = "pump_station"
    BOOSTER = "booster_station"
    BREAK_TANK = "break_tank"


class ControlMode(Enum):
    """Controller operating modes"""
    FIXED = "fixed"                  # Fixed setpoint
    TIME_MODULATED = "time_modulated"  # Time-based pattern
    FLOW_MODULATED = "flow_modulated"  # Flow-responsive
    PRESSURE_MODULATED = "pressure_modulated"  # Critical point based
    AI_OPTIMIZED = "ai_optimized"    # ML-optimized


@dataclass
class PressureZone:
    """Represents a pressure management zone"""
    zone_id: str
    name: str
    zone_type: PressureZoneType
    
    # Geographic bounds
    boundary: List[Tuple[float, float]]  # Polygon coordinates
    centroid: Tuple[float, float]
    
    # Elevation characteristics
    min_elevation: float  # meters
    max_elevation: float
    avg_elevation: float
    
    # Hydraulic characteristics
    design_pressure: float  # bar - target pressure
    min_pressure: float     # bar - minimum acceptable
    max_pressure: float     # bar - maximum acceptable
    
    # Current state
    current_pressure: float = 0.0
    current_flow: float = 0.0  # L/s
    
    # Connections
    inlet_controllers: List[str] = field(default_factory=list)
    outlet_controllers: List[str] = field(default_factory=list)
    critical_points: List[str] = field(default_factory=list)
    
    # Performance metrics
    avg_zone_pressure: float = 0.0
    pressure_variance: float = 0.0
    leakage_index: float = 0.0  # ILI - Infrastructure Leakage Index


@dataclass
class PressureController:
    """Represents a pressure control device (PRV, pump, etc.)"""
    controller_id: str
    name: str
    controller_type: ControllerType
    
    # Location
    latitude: float
    longitude: float
    upstream_zone: str
    downstream_zone: str
    
    # Specifications
    max_flow: float  # L/s
    inlet_size: int  # mm
    outlet_size: int  # mm
    
    # Operating parameters
    setpoint: float = 3.0  # bar
    current_outlet_pressure: float = 0.0
    current_inlet_pressure: float = 0.0
    current_flow: float = 0.0
    
    # Control settings
    control_mode: ControlMode = ControlMode.FIXED
    time_pattern: List[float] = field(default_factory=list)  # 24-hour setpoints
    
    # Status
    is_active: bool = True
    last_adjustment: Optional[datetime] = None
    
    # For pumps
    power_kw: float = 0.0
    efficiency: float = 0.75


@dataclass
class CriticalPoint:
    """Critical pressure monitoring point"""
    point_id: str
    name: str
    zone_id: str
    
    # Location
    latitude: float
    longitude: float
    elevation: float
    
    # Pressure requirements
    min_required_pressure: float  # bar
    target_pressure: float
    
    # Current state
    current_pressure: float = 0.0
    
    # Characteristics
    is_worst_point: bool = False  # Highest elevation in zone
    customer_count: int = 0


class PressureOptimizer:
    """AI-powered pressure optimization engine"""
    
    def __init__(self):
        # Leakage exponent (N1) - typically 0.5-1.5 for different leak types
        self.leakage_exponent = 1.0
        
        # Time-of-day demand patterns
        self.demand_patterns = {
            "residential": [
                0.3, 0.2, 0.2, 0.2, 0.3, 0.5,
                0.9, 1.4, 1.2, 0.8, 0.6, 0.7,
                0.9, 0.7, 0.6, 0.6, 0.7, 1.0,
                1.3, 1.2, 1.0, 0.8, 0.5, 0.4
            ],
            "industrial": [
                0.8, 0.8, 0.8, 0.8, 0.8, 0.9,
                1.0, 1.2, 1.3, 1.3, 1.3, 1.2,
                1.0, 1.2, 1.3, 1.3, 1.2, 1.0,
                0.9, 0.8, 0.8, 0.8, 0.8, 0.8
            ],
            "commercial": [
                0.1, 0.1, 0.1, 0.1, 0.1, 0.2,
                0.5, 1.0, 1.4, 1.5, 1.4, 1.3,
                1.2, 1.3, 1.4, 1.3, 1.2, 1.0,
                0.5, 0.2, 0.1, 0.1, 0.1, 0.1
            ]
        }
    
    def calculate_optimal_pressure(
        self,
        zone: PressureZone,
        critical_points: List[CriticalPoint],
        current_hour: int
    ) -> float:
        """
        Calculate optimal pressure setpoint for a zone.
        
        Balances:
        - Meeting critical point minimum pressure
        - Reducing leakage (pressure-leakage relationship)
        - Energy efficiency
        
        Returns:
            Optimal pressure setpoint in bar
        """
        # Find worst-case critical point
        worst_point = None
        max_head_required = 0
        
        for cp in critical_points:
            # Required head = elevation + min pressure (in meters of head)
            required_head = cp.elevation + cp.min_required_pressure * 10.2
            if required_head > max_head_required:
                max_head_required = required_head
                worst_point = cp
        
        # Calculate minimum zone pressure to satisfy worst point
        # Add margin for head loss
        head_loss_margin = 5  # meters
        min_zone_head = max_head_required + head_loss_margin - zone.avg_elevation
        min_zone_pressure = min_zone_head / 10.2  # Convert to bar
        
        # Adjust for demand pattern
        pattern = self.demand_patterns.get(zone.zone_type.value, self.demand_patterns["residential"])
        demand_factor = pattern[current_hour]
        
        # Lower pressure during low demand periods (night)
        if demand_factor < 0.5:
            # Can reduce pressure by up to 20% during low demand
            pressure_reduction = 0.2 * (0.5 - demand_factor)
            optimal_pressure = min_zone_pressure * (1 - pressure_reduction)
        else:
            # Maintain or slightly increase during peak
            pressure_increase = 0.1 * (demand_factor - 0.5) if demand_factor > 1.0 else 0
            optimal_pressure = min_zone_pressure * (1 + pressure_increase)
        
        # Clamp to zone limits
        optimal_pressure = max(zone.min_pressure, min(zone.max_pressure, optimal_pressure))
        
        return optimal_pressure
    
    def estimate_leakage_reduction(
        self,
        current_pressure: float,
        new_pressure: float,
        current_leakage: float
    ) -> Dict:
        """
        Estimate leakage reduction from pressure change.
        
        Uses the Fixed and Variable Area Discharge (FAVAD) concept:
        Leakage ∝ Pressure^N1
        """
        if current_pressure <= 0:
            return {"error": "Invalid current pressure"}
        
        # Calculate pressure ratio
        pressure_ratio = new_pressure / current_pressure
        
        # Calculate new leakage using FAVAD
        new_leakage = current_leakage * (pressure_ratio ** self.leakage_exponent)
        leakage_reduction = current_leakage - new_leakage
        
        # Calculate savings
        reduction_percent = (leakage_reduction / current_leakage * 100) if current_leakage > 0 else 0
        
        # Annual water savings (m³/year)
        daily_savings = leakage_reduction * 3600 * 24 / 1000  # m³/day
        annual_savings = daily_savings * 365
        
        # Financial savings (ZMW)
        cost_per_m3 = 5.50
        annual_cost_savings = annual_savings * cost_per_m3
        
        return {
            "current_pressure_bar": current_pressure,
            "new_pressure_bar": new_pressure,
            "pressure_reduction_bar": current_pressure - new_pressure,
            "pressure_reduction_percent": (1 - pressure_ratio) * 100,
            "current_leakage_lps": current_leakage,
            "new_leakage_lps": new_leakage,
            "leakage_reduction_lps": leakage_reduction,
            "leakage_reduction_percent": reduction_percent,
            "daily_water_savings_m3": daily_savings,
            "annual_water_savings_m3": annual_savings,
            "annual_cost_savings_zmw": annual_cost_savings
        }
    
    def optimize_pump_schedule(
        self,
        zone: PressureZone,
        pump: PressureController,
        electricity_tariff: Dict[int, float]
    ) -> List[Dict]:
        """
        Optimize pump operating schedule for energy efficiency.
        
        Args:
            zone: Pressure zone served by pump
            pump: Pump controller
            electricity_tariff: Hour -> cost (ZMW/kWh)
        
        Returns:
            24-hour schedule with setpoints and expected costs
        """
        schedule = []
        total_energy_cost = 0
        
        for hour in range(24):
            # Get demand factor
            pattern = self.demand_patterns.get(zone.zone_type.value, self.demand_patterns["residential"])
            demand_factor = pattern[hour]
            
            # Calculate required flow
            base_flow = zone.current_flow if zone.current_flow > 0 else 50  # L/s baseline
            required_flow = base_flow * demand_factor
            
            # Calculate pump power needed
            head_required = zone.design_pressure * 10.2  # Convert bar to meters
            power_needed = (required_flow / 1000 * 9.81 * head_required) / pump.efficiency  # kW
            
            # Get electricity cost
            tariff = electricity_tariff.get(hour, 0.50)  # ZMW/kWh
            
            # Decide pump operation
            if demand_factor < 0.4 and tariff > 0.60:
                # Low demand + high tariff = reduce pumping, use storage
                run_pump = False
                power_used = 0
            else:
                run_pump = True
                power_used = min(power_needed, pump.power_kw)
            
            hourly_cost = power_used * tariff
            total_energy_cost += hourly_cost
            
            schedule.append({
                "hour": hour,
                "run_pump": run_pump,
                "power_kw": power_used,
                "tariff_zmw_kwh": tariff,
                "hourly_cost_zmw": hourly_cost,
                "demand_factor": demand_factor,
                "flow_lps": required_flow if run_pump else 0
            })
        
        return {
            "schedule": schedule,
            "daily_energy_kwh": sum(s["power_kw"] for s in schedule),
            "daily_cost_zmw": total_energy_cost,
            "peak_hours_avoided": len([s for s in schedule if not s["run_pump"] and s["tariff_zmw_kwh"] > 0.60])
        }


class DynamicPressureManager:
    """
    Central manager for dynamic pressure management.
    """
    
    def __init__(self):
        self.zones: Dict[str, PressureZone] = {}
        self.controllers: Dict[str, PressureController] = {}
        self.critical_points: Dict[str, CriticalPoint] = {}
        self.optimizer = PressureOptimizer()
        
        # Historical data
        self.pressure_history: Dict[str, List[Dict]] = defaultdict(list)
        self.control_history: List[Dict] = []
        
        # Electricity tariff (Zambia ZESCO rates)
        self.electricity_tariff = {
            **{h: 0.35 for h in range(0, 6)},    # Off-peak: 00:00-06:00
            **{h: 0.65 for h in range(6, 8)},    # Shoulder: 06:00-08:00
            **{h: 0.85 for h in range(8, 12)},   # Peak: 08:00-12:00
            **{h: 0.65 for h in range(12, 17)},  # Shoulder: 12:00-17:00
            **{h: 0.85 for h in range(17, 21)},  # Peak: 17:00-21:00
            **{h: 0.45 for h in range(21, 24)}   # Off-peak: 21:00-00:00
        }
        
        # Initialize demo configuration
        self._initialize_demo_config()
    
    def _initialize_demo_config(self):
        """Initialize demo pressure zones for Lusaka"""
        # Define pressure zones
        zones_data = [
            {
                "zone_id": "PZ_CBD_HIGH",
                "name": "CBD High Zone",
                "zone_type": PressureZoneType.COMMERCIAL,
                "centroid": (-15.4167, 28.2833),
                "min_elevation": 1230,
                "max_elevation": 1250,
                "avg_elevation": 1240,
                "design_pressure": 3.5,
                "min_pressure": 2.0,
                "max_pressure": 5.0
            },
            {
                "zone_id": "PZ_KABULONGA",
                "name": "Kabulonga Zone",
                "zone_type": PressureZoneType.RESIDENTIAL,
                "centroid": (-15.3958, 28.3208),
                "min_elevation": 1250,
                "max_elevation": 1280,
                "avg_elevation": 1265,
                "design_pressure": 3.0,
                "min_pressure": 2.0,
                "max_pressure": 4.5
            },
            {
                "zone_id": "PZ_WOODLANDS",
                "name": "Woodlands Zone",
                "zone_type": PressureZoneType.RESIDENTIAL,
                "centroid": (-15.4250, 28.3083),
                "min_elevation": 1235,
                "max_elevation": 1260,
                "avg_elevation": 1248,
                "design_pressure": 3.2,
                "min_pressure": 2.0,
                "max_pressure": 4.5
            },
            {
                "zone_id": "PZ_INDUSTRIAL",
                "name": "Industrial Zone",
                "zone_type": PressureZoneType.INDUSTRIAL,
                "centroid": (-15.4417, 28.2625),
                "min_elevation": 1225,
                "max_elevation": 1240,
                "avg_elevation": 1232,
                "design_pressure": 4.0,
                "min_pressure": 2.5,
                "max_pressure": 6.0
            },
            {
                "zone_id": "PZ_MATERO",
                "name": "Matero Zone",
                "zone_type": PressureZoneType.RESIDENTIAL,
                "centroid": (-15.3833, 28.2542),
                "min_elevation": 1260,
                "max_elevation": 1290,
                "avg_elevation": 1275,
                "design_pressure": 2.8,
                "min_pressure": 1.5,
                "max_pressure": 4.0
            }
        ]
        
        for zdata in zones_data:
            zone = PressureZone(
                zone_id=zdata["zone_id"],
                name=zdata["name"],
                zone_type=zdata["zone_type"],
                boundary=[],  # Simplified
                centroid=zdata["centroid"],
                min_elevation=zdata["min_elevation"],
                max_elevation=zdata["max_elevation"],
                avg_elevation=zdata["avg_elevation"],
                design_pressure=zdata["design_pressure"],
                min_pressure=zdata["min_pressure"],
                max_pressure=zdata["max_pressure"],
                current_pressure=zdata["design_pressure"],
                current_flow=np.random.uniform(30, 100)
            )
            self.zones[zone.zone_id] = zone
        
        # Define pressure controllers
        controllers_data = [
            {
                "controller_id": "PRV_CBD_01",
                "name": "CBD Main PRV",
                "controller_type": ControllerType.PRV,
                "coords": (-15.4150, 28.2840),
                "upstream": "PZ_KABULONGA",
                "downstream": "PZ_CBD_HIGH",
                "max_flow": 150,
                "setpoint": 3.5
            },
            {
                "controller_id": "PRV_WOOD_01",
                "name": "Woodlands PRV",
                "controller_type": ControllerType.PRV,
                "coords": (-15.4240, 28.3090),
                "upstream": "PZ_KABULONGA",
                "downstream": "PZ_WOODLANDS",
                "max_flow": 100,
                "setpoint": 3.2
            },
            {
                "controller_id": "PUMP_MATERO",
                "name": "Matero Booster",
                "controller_type": ControllerType.PUMP,
                "coords": (-15.3850, 28.2560),
                "upstream": "PZ_CBD_HIGH",
                "downstream": "PZ_MATERO",
                "max_flow": 80,
                "setpoint": 4.0,
                "power_kw": 45
            },
            {
                "controller_id": "PRV_IND_01",
                "name": "Industrial PRV",
                "controller_type": ControllerType.PRV,
                "coords": (-15.4400, 28.2630),
                "upstream": "PZ_CBD_HIGH",
                "downstream": "PZ_INDUSTRIAL",
                "max_flow": 200,
                "setpoint": 4.0
            }
        ]
        
        for cdata in controllers_data:
            controller = PressureController(
                controller_id=cdata["controller_id"],
                name=cdata["name"],
                controller_type=cdata["controller_type"],
                latitude=cdata["coords"][0],
                longitude=cdata["coords"][1],
                upstream_zone=cdata["upstream"],
                downstream_zone=cdata["downstream"],
                max_flow=cdata["max_flow"],
                inlet_size=150,
                outlet_size=150,
                setpoint=cdata["setpoint"],
                power_kw=cdata.get("power_kw", 0)
            )
            self.controllers[controller.controller_id] = controller
            
            # Link to zones
            if cdata["downstream"] in self.zones:
                self.zones[cdata["downstream"]].inlet_controllers.append(cdata["controller_id"])
            if cdata["upstream"] in self.zones:
                self.zones[cdata["upstream"]].outlet_controllers.append(cdata["controller_id"])
        
        # Define critical points
        critical_points_data = [
            ("CP_KAB_HIGH", "Kabulonga Hilltop", "PZ_KABULONGA", -15.3920, 28.3250, 1280, 1.5, True),
            ("CP_KAB_LOW", "Kabulonga Valley", "PZ_KABULONGA", -15.3990, 28.3180, 1255, 2.0, False),
            ("CP_WOOD_HIGH", "Woodlands Heights", "PZ_WOODLANDS", -15.4220, 28.3100, 1260, 1.8, True),
            ("CP_MAT_HIGH", "Matero Hilltop", "PZ_MATERO", -15.3800, 28.2520, 1290, 1.2, True),
            ("CP_CBD_TOWER", "CBD Tower", "PZ_CBD_HIGH", -15.4180, 28.2820, 1250, 2.5, False),
            ("CP_IND_FACTORY", "Industrial Plant", "PZ_INDUSTRIAL", -15.4430, 28.2610, 1240, 3.0, False),
        ]
        
        for cpdata in critical_points_data:
            cp_id, name, zone, lat, lon, elev, min_press, is_worst = cpdata
            cp = CriticalPoint(
                point_id=cp_id,
                name=name,
                zone_id=zone,
                latitude=lat,
                longitude=lon,
                elevation=elev,
                min_required_pressure=min_press,
                target_pressure=min_press + 0.5,
                current_pressure=min_press + np.random.uniform(0.2, 1.0),
                is_worst_point=is_worst,
                customer_count=np.random.randint(100, 1000)
            )
            self.critical_points[cp_id] = cp
            
            # Link to zone
            if zone in self.zones:
                self.zones[zone].critical_points.append(cp_id)
    
    def update_pressure_reading(
        self,
        zone_id: str,
        pressure: float,
        flow: float = None
    ):
        """Update pressure reading for a zone"""
        if zone_id not in self.zones:
            return
        
        zone = self.zones[zone_id]
        zone.current_pressure = pressure
        if flow is not None:
            zone.current_flow = flow
        
        # Store history
        self.pressure_history[zone_id].append({
            "timestamp": datetime.now().isoformat(),
            "pressure": pressure,
            "flow": flow
        })
        
        # Keep only last 168 hours (7 days)
        if len(self.pressure_history[zone_id]) > 168:
            self.pressure_history[zone_id] = self.pressure_history[zone_id][-168:]
    
    def get_optimal_setpoints(self) -> Dict[str, Dict]:
        """
        Calculate optimal pressure setpoints for all zones.
        
        Returns:
            Dictionary of zone_id -> optimal settings
        """
        current_hour = datetime.now().hour
        results = {}
        
        for zone_id, zone in self.zones.items():
            # Get zone's critical points
            zone_cps = [
                self.critical_points[cp_id]
                for cp_id in zone.critical_points
                if cp_id in self.critical_points
            ]
            
            # Calculate optimal pressure
            optimal_pressure = self.optimizer.calculate_optimal_pressure(
                zone, zone_cps, current_hour
            )
            
            # Calculate potential leakage reduction
            current_leakage = zone.current_flow * 0.15  # Assume 15% leakage
            leakage_impact = self.optimizer.estimate_leakage_reduction(
                zone.current_pressure,
                optimal_pressure,
                current_leakage
            )
            
            results[zone_id] = {
                "zone_name": zone.name,
                "current_pressure": zone.current_pressure,
                "optimal_pressure": optimal_pressure,
                "change_required": optimal_pressure - zone.current_pressure,
                "leakage_impact": leakage_impact,
                "status": "optimal" if abs(zone.current_pressure - optimal_pressure) < 0.2 else "adjustment_needed"
            }
        
        return results
    
    def adjust_controller(
        self,
        controller_id: str,
        new_setpoint: float,
        mode: ControlMode = None
    ) -> Dict:
        """
        Adjust a pressure controller.
        
        Args:
            controller_id: Controller ID
            new_setpoint: New pressure setpoint (bar)
            mode: Optional new control mode
        
        Returns:
            Adjustment result
        """
        if controller_id not in self.controllers:
            return {"error": f"Controller {controller_id} not found"}
        
        controller = self.controllers[controller_id]
        old_setpoint = controller.setpoint
        
        # Apply adjustment
        controller.setpoint = new_setpoint
        if mode:
            controller.control_mode = mode
        controller.last_adjustment = datetime.now()
        
        # Log adjustment
        adjustment = {
            "controller_id": controller_id,
            "controller_name": controller.name,
            "timestamp": datetime.now().isoformat(),
            "old_setpoint": old_setpoint,
            "new_setpoint": new_setpoint,
            "mode": controller.control_mode.value
        }
        self.control_history.append(adjustment)
        
        # Estimate impact on downstream zone
        downstream_zone = self.zones.get(controller.downstream_zone)
        impact = {}
        if downstream_zone:
            leakage = downstream_zone.current_flow * 0.15
            impact = self.optimizer.estimate_leakage_reduction(
                old_setpoint, new_setpoint, leakage
            )
        
        return {
            **adjustment,
            "impact": impact
        }
    
    def get_pump_optimization(self, pump_id: str) -> Dict:
        """
        Get optimized pump schedule.
        
        Args:
            pump_id: Pump controller ID
        
        Returns:
            Optimized schedule with energy costs
        """
        if pump_id not in self.controllers:
            return {"error": f"Pump {pump_id} not found"}
        
        pump = self.controllers[pump_id]
        if pump.controller_type != ControllerType.PUMP:
            return {"error": f"{pump_id} is not a pump"}
        
        zone = self.zones.get(pump.downstream_zone)
        if not zone:
            return {"error": "Downstream zone not found"}
        
        schedule = self.optimizer.optimize_pump_schedule(
            zone, pump, self.electricity_tariff
        )
        
        return {
            "pump_id": pump_id,
            "pump_name": pump.name,
            "zone": zone.name,
            **schedule
        }
    
    def get_zone_dashboard(self, zone_id: str) -> Dict:
        """Get detailed dashboard for a pressure zone"""
        if zone_id not in self.zones:
            return {"error": f"Zone {zone_id} not found"}
        
        zone = self.zones[zone_id]
        
        # Get critical points
        zone_cps = [
            {
                "point_id": cp_id,
                "name": self.critical_points[cp_id].name,
                "elevation": self.critical_points[cp_id].elevation,
                "min_pressure": self.critical_points[cp_id].min_required_pressure,
                "current_pressure": self.critical_points[cp_id].current_pressure,
                "is_worst": self.critical_points[cp_id].is_worst_point,
                "status": "ok" if self.critical_points[cp_id].current_pressure >= self.critical_points[cp_id].min_required_pressure else "low"
            }
            for cp_id in zone.critical_points
            if cp_id in self.critical_points
        ]
        
        # Get controllers
        inlet_controllers = [
            {
                "controller_id": c_id,
                "name": self.controllers[c_id].name,
                "type": self.controllers[c_id].controller_type.value,
                "setpoint": self.controllers[c_id].setpoint,
                "flow": self.controllers[c_id].current_flow
            }
            for c_id in zone.inlet_controllers
            if c_id in self.controllers
        ]
        
        # Calculate optimal pressure
        optimal = self.get_optimal_setpoints().get(zone_id, {})
        
        # Pressure history stats
        history = self.pressure_history.get(zone_id, [])
        if history:
            pressures = [h["pressure"] for h in history if h["pressure"]]
            avg_pressure = np.mean(pressures)
            min_pressure = min(pressures)
            max_pressure = max(pressures)
        else:
            avg_pressure = zone.current_pressure
            min_pressure = zone.current_pressure
            max_pressure = zone.current_pressure
        
        return {
            "zone_id": zone_id,
            "zone_name": zone.name,
            "zone_type": zone.zone_type.value,
            "current_state": {
                "pressure_bar": zone.current_pressure,
                "flow_lps": zone.current_flow,
                "design_pressure": zone.design_pressure
            },
            "elevation": {
                "min": zone.min_elevation,
                "max": zone.max_elevation,
                "avg": zone.avg_elevation
            },
            "pressure_limits": {
                "min": zone.min_pressure,
                "max": zone.max_pressure
            },
            "optimization": optimal,
            "critical_points": zone_cps,
            "inlet_controllers": inlet_controllers,
            "statistics": {
                "avg_pressure_24h": avg_pressure,
                "min_pressure_24h": min_pressure,
                "max_pressure_24h": max_pressure,
                "readings_count": len(history)
            }
        }
    
    def get_system_overview(self) -> Dict:
        """Get system-wide pressure management overview"""
        # Calculate zone statistics
        zones_status = []
        total_leakage_reduction_potential = 0
        
        setpoints = self.get_optimal_setpoints()
        
        for zone_id, zone in self.zones.items():
            opt = setpoints.get(zone_id, {})
            
            status = {
                "zone_id": zone_id,
                "zone_name": zone.name,
                "current_pressure": zone.current_pressure,
                "optimal_pressure": opt.get("optimal_pressure", zone.design_pressure),
                "status": opt.get("status", "unknown"),
                "critical_points_count": len(zone.critical_points),
                "controllers_count": len(zone.inlet_controllers)
            }
            
            if "leakage_impact" in opt:
                status["potential_savings_zmw"] = opt["leakage_impact"].get("annual_cost_savings_zmw", 0)
                total_leakage_reduction_potential += opt["leakage_impact"].get("annual_cost_savings_zmw", 0)
            
            zones_status.append(status)
        
        # Controller status
        controller_status = {
            "total": len(self.controllers),
            "by_type": defaultdict(int),
            "active": 0,
            "needs_adjustment": 0
        }
        
        for controller in self.controllers.values():
            controller_status["by_type"][controller.controller_type.value] += 1
            if controller.is_active:
                controller_status["active"] += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "zones": {
                "total": len(self.zones),
                "status": zones_status,
                "zones_optimal": len([z for z in zones_status if z["status"] == "optimal"]),
                "zones_need_adjustment": len([z for z in zones_status if z["status"] == "adjustment_needed"])
            },
            "controllers": dict(controller_status),
            "critical_points": {
                "total": len(self.critical_points),
                "low_pressure": len([cp for cp in self.critical_points.values() if cp.current_pressure < cp.min_required_pressure])
            },
            "potential_savings": {
                "annual_leakage_reduction_zmw": total_leakage_reduction_potential,
                "optimization_opportunities": len([z for z in zones_status if z["status"] == "adjustment_needed"])
            },
            "electricity_tariff": {
                "current_rate": self.electricity_tariff[datetime.now().hour],
                "period": "peak" if self.electricity_tariff[datetime.now().hour] > 0.70 else "off-peak"
            }
        }


# Global instance
pressure_manager = DynamicPressureManager()


def get_pressure_manager() -> DynamicPressureManager:
    """Get global pressure manager instance"""
    return pressure_manager


if __name__ == "__main__":
    # Demo
    manager = DynamicPressureManager()
    
    print("=" * 60)
    print("AquaWatch Dynamic Pressure Management")
    print("=" * 60)
    
    # System overview
    overview = manager.get_system_overview()
    print(f"\nSystem Overview:")
    print(f"  Total Zones: {overview['zones']['total']}")
    print(f"  Zones Optimal: {overview['zones']['zones_optimal']}")
    print(f"  Zones Need Adjustment: {overview['zones']['zones_need_adjustment']}")
    print(f"  Total Controllers: {overview['controllers']['total']}")
    print(f"  Annual Savings Potential: ZMW {overview['potential_savings']['annual_leakage_reduction_zmw']:,.0f}")
    
    # Get optimal setpoints
    print(f"\nOptimal Pressure Setpoints:")
    setpoints = manager.get_optimal_setpoints()
    for zone_id, data in setpoints.items():
        print(f"  {data['zone_name']}:")
        print(f"    Current: {data['current_pressure']:.2f} bar")
        print(f"    Optimal: {data['optimal_pressure']:.2f} bar")
        print(f"    Status: {data['status']}")
    
    # Zone dashboard
    print(f"\nZone Dashboard (PZ_KABULONGA):")
    dashboard = manager.get_zone_dashboard("PZ_KABULONGA")
    print(f"  Current Pressure: {dashboard['current_state']['pressure_bar']:.2f} bar")
    print(f"  Critical Points: {len(dashboard['critical_points'])}")
    for cp in dashboard['critical_points']:
        print(f"    - {cp['name']}: {cp['current_pressure']:.2f} bar ({cp['status']})")
    
    # Pump optimization
    print(f"\nPump Optimization (PUMP_MATERO):")
    pump_opt = manager.get_pump_optimization("PUMP_MATERO")
    if "error" not in pump_opt:
        print(f"  Daily Energy: {pump_opt['daily_energy_kwh']:.1f} kWh")
        print(f"  Daily Cost: ZMW {pump_opt['daily_cost_zmw']:.2f}")
        print(f"  Peak Hours Avoided: {pump_opt['peak_hours_avoided']}")
