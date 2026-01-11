"""
AquaWatch Enterprise - Smart Building & Campus Water Management
================================================================

"Every drop counts in your building."

Solutions for:
1. Commercial real estate
2. Corporate campuses
3. Hotels & hospitality
4. Hospitals & healthcare
5. Universities
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# BUILDING TYPES
# =============================================================================

class BuildingType(Enum):
    OFFICE = "office"
    HOTEL = "hotel"
    HOSPITAL = "hospital"
    UNIVERSITY = "university"
    RETAIL = "retail"
    MIXED_USE = "mixed_use"
    MANUFACTURING = "manufacturing"
    DATA_CENTER = "data_center"


class WaterFixtureType(Enum):
    TOILET = "toilet"
    URINAL = "urinal"
    FAUCET = "faucet"
    SHOWER = "shower"
    COOLING_TOWER = "cooling_tower"
    IRRIGATION = "irrigation"
    KITCHEN = "kitchen"
    LAUNDRY = "laundry"
    PROCESS = "process"


# Building benchmarks (liters per person per day or per unit)
BUILDING_BENCHMARKS = {
    BuildingType.OFFICE: {
        "unit": "L/person/day",
        "excellent": 30,
        "good": 50,
        "average": 75,
        "poor": 100
    },
    BuildingType.HOTEL: {
        "unit": "L/guest-night",
        "excellent": 200,
        "good": 350,
        "average": 500,
        "poor": 800
    },
    BuildingType.HOSPITAL: {
        "unit": "L/bed/day",
        "excellent": 400,
        "good": 600,
        "average": 800,
        "poor": 1200
    },
    BuildingType.UNIVERSITY: {
        "unit": "L/student/day",
        "excellent": 40,
        "good": 60,
        "average": 80,
        "poor": 120
    }
}


# =============================================================================
# BUILDING MODEL
# =============================================================================

@dataclass
class WaterZone:
    """Water zone within building."""
    zone_id: str
    name: str
    floor: int
    zone_type: str  # restroom, kitchen, mechanical, etc.
    
    # Fixtures
    fixtures: Dict[WaterFixtureType, int] = field(default_factory=dict)
    
    # Metering
    has_submeter: bool = False
    meter_id: str = ""
    
    # Usage
    daily_usage_liters: float = 0
    baseline_liters: float = 0


@dataclass
class SmartBuilding:
    """Smart building water profile."""
    building_id: str
    name: str
    building_type: BuildingType
    address: str
    
    # Size
    floors: int
    gross_area_sqm: float
    occupancy: int  # Average daily occupancy
    
    # Zones
    zones: List[WaterZone] = field(default_factory=list)
    
    # Water sources
    municipal_connection: bool = True
    rainwater_harvesting: bool = False
    rainwater_tank_liters: float = 0
    greywater_recycling: bool = False
    blackwater_treatment: bool = False
    
    # Cooling
    cooling_tower_count: int = 0
    cooling_tower_cycles: float = 5.0  # Cycles of concentration
    
    # Landscaping
    landscape_area_sqm: float = 0
    smart_irrigation: bool = False
    
    # Certifications
    leed_certified: bool = False
    leed_level: str = ""  # Certified, Silver, Gold, Platinum
    wels_rating: int = 0  # Water Efficiency Labeling
    
    # Usage
    annual_usage_kl: float = 0
    annual_cost_usd: float = 0


# =============================================================================
# FIXTURE-LEVEL MONITORING
# =============================================================================

@dataclass
class FixtureReading:
    """Individual fixture reading."""
    fixture_id: str
    fixture_type: WaterFixtureType
    zone_id: str
    
    timestamp: datetime
    flow_rate_lpm: float
    duration_seconds: float
    volume_liters: float
    
    # Anomaly
    is_anomaly: bool = False
    anomaly_type: str = ""


class FixtureLevelMonitor:
    """
    Fixture-level water monitoring.
    
    "Know exactly where every drop goes."
    """
    
    def __init__(self):
        self.readings: List[FixtureReading] = []
        self.fixture_baselines: Dict[str, Dict] = {}
    
    def set_baseline(self, 
                     fixture_id: str,
                     fixture_type: WaterFixtureType,
                     expected_flow_lpm: float,
                     expected_duration: float,
                     expected_daily_uses: int):
        """Set baseline for fixture."""
        
        self.fixture_baselines[fixture_id] = {
            "fixture_type": fixture_type,
            "expected_flow_lpm": expected_flow_lpm,
            "expected_duration": expected_duration,
            "expected_daily_uses": expected_daily_uses,
            "expected_daily_volume": expected_flow_lpm * expected_duration / 60 * expected_daily_uses
        }
    
    def process_reading(self, reading: FixtureReading) -> Dict:
        """Process fixture reading for anomalies."""
        
        baseline = self.fixture_baselines.get(reading.fixture_id)
        if not baseline:
            return {"status": "no_baseline"}
        
        anomalies = []
        
        # Check flow rate
        if reading.flow_rate_lpm > baseline["expected_flow_lpm"] * 1.5:
            anomalies.append({
                "type": "high_flow",
                "expected": baseline["expected_flow_lpm"],
                "actual": reading.flow_rate_lpm,
                "severity": "medium"
            })
        
        # Check duration
        if reading.duration_seconds > baseline["expected_duration"] * 3:
            anomalies.append({
                "type": "long_duration",
                "expected": baseline["expected_duration"],
                "actual": reading.duration_seconds,
                "severity": "high"  # Possible running fixture
            })
        
        # Check for continuous flow (leak)
        if reading.duration_seconds > 3600:  # 1 hour continuous
            anomalies.append({
                "type": "continuous_flow",
                "duration_hours": reading.duration_seconds / 3600,
                "severity": "critical"
            })
        
        reading.is_anomaly = len(anomalies) > 0
        self.readings.append(reading)
        
        return {
            "fixture_id": reading.fixture_id,
            "is_anomaly": reading.is_anomaly,
            "anomalies": anomalies
        }
    
    def get_fixture_analytics(self, 
                               fixture_id: str,
                               period_days: int = 30) -> Dict:
        """Get analytics for specific fixture."""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        fixture_readings = [r for r in self.readings 
                          if r.fixture_id == fixture_id and r.timestamp > cutoff]
        
        if not fixture_readings:
            return {"error": "No readings found"}
        
        total_volume = sum(r.volume_liters for r in fixture_readings)
        total_uses = len(fixture_readings)
        anomaly_count = sum(1 for r in fixture_readings if r.is_anomaly)
        
        baseline = self.fixture_baselines.get(fixture_id, {})
        expected_volume = baseline.get("expected_daily_volume", 0) * period_days
        
        return {
            "fixture_id": fixture_id,
            "period_days": period_days,
            "total_volume_liters": total_volume,
            "total_uses": total_uses,
            "avg_per_use_liters": total_volume / total_uses if total_uses > 0 else 0,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_count / total_uses if total_uses > 0 else 0,
            "vs_baseline": {
                "expected_volume": expected_volume,
                "variance_percent": ((total_volume - expected_volume) / expected_volume * 100) if expected_volume > 0 else 0
            }
        }


# =============================================================================
# COOLING TOWER OPTIMIZER
# =============================================================================

class CoolingTowerOptimizer:
    """
    Cooling tower water optimization.
    
    Cooling towers are often 30-50% of building water use.
    """
    
    def __init__(self):
        # Water quality limits
        self.chemistry_limits = {
            "conductivity_us": {"min": 500, "max": 2500},
            "ph": {"min": 7.0, "max": 9.0},
            "alkalinity_ppm": {"min": 100, "max": 500},
            "hardness_ppm": {"min": 200, "max": 800},
            "chlorides_ppm": {"min": 0, "max": 250}
        }
    
    def calculate_water_balance(self,
                                 tons_cooling: float,
                                 delta_t_f: float,
                                 cycles_of_concentration: float,
                                 hours_operation: float = 12) -> Dict:
        """Calculate cooling tower water balance."""
        
        # Evaporation (simplified formula)
        evaporation_gph = 0.0008 * tons_cooling * delta_t_f * 3  # gallons per hour
        evaporation_liters_day = evaporation_gph * hours_operation * 3.785
        
        # Blowdown
        blowdown_liters_day = evaporation_liters_day / (cycles_of_concentration - 1)
        
        # Drift (typically 0.02% of circulation)
        circulation_gph = 3 * tons_cooling  # Rule of thumb
        drift_liters_day = circulation_gph * hours_operation * 3.785 * 0.0002
        
        # Makeup = Evaporation + Blowdown + Drift
        makeup_liters_day = evaporation_liters_day + blowdown_liters_day + drift_liters_day
        
        return {
            "cooling_tons": tons_cooling,
            "delta_t": delta_t_f,
            "cycles_of_concentration": cycles_of_concentration,
            "hours_per_day": hours_operation,
            "water_balance": {
                "evaporation_L_day": round(evaporation_liters_day, 0),
                "blowdown_L_day": round(blowdown_liters_day, 0),
                "drift_L_day": round(drift_liters_day, 0),
                "total_makeup_L_day": round(makeup_liters_day, 0),
                "annual_consumption_kL": round(makeup_liters_day * 365 / 1000, 0)
            }
        }
    
    def optimize_cycles(self,
                        current_cycles: float,
                        makeup_water_quality: Dict,
                        cooling_tons: float,
                        delta_t_f: float) -> Dict:
        """Find optimal cycles of concentration."""
        
        # Simulate different cycles
        scenarios = []
        
        for cycles in [3, 4, 5, 6, 7, 8]:
            balance = self.calculate_water_balance(
                cooling_tons, delta_t_f, cycles
            )
            
            # Check if chemistry would exceed limits
            chemistry_ok = True
            makeup_conductivity = makeup_water_quality.get("conductivity_us", 500)
            tower_conductivity = makeup_conductivity * cycles
            
            if tower_conductivity > self.chemistry_limits["conductivity_us"]["max"]:
                chemistry_ok = False
            
            scenarios.append({
                "cycles": cycles,
                "makeup_L_day": balance["water_balance"]["total_makeup_L_day"],
                "annual_kL": balance["water_balance"]["annual_consumption_kL"],
                "chemistry_feasible": chemistry_ok
            })
        
        # Find optimal (highest cycles with good chemistry)
        feasible = [s for s in scenarios if s["chemistry_feasible"]]
        optimal = max(feasible, key=lambda s: s["cycles"]) if feasible else scenarios[0]
        
        # Calculate savings vs current
        current = next((s for s in scenarios if s["cycles"] == current_cycles), scenarios[0])
        
        return {
            "current_cycles": current_cycles,
            "optimal_cycles": optimal["cycles"],
            "current_annual_kL": current["annual_kL"],
            "optimal_annual_kL": optimal["annual_kL"],
            "annual_savings_kL": current["annual_kL"] - optimal["annual_kL"],
            "savings_percent": round((current["annual_kL"] - optimal["annual_kL"]) / current["annual_kL"] * 100, 1),
            "all_scenarios": scenarios
        }


# =============================================================================
# SMART IRRIGATION
# =============================================================================

class SmartIrrigationController:
    """
    AI-powered irrigation for building landscapes.
    
    "Water when plants need it, not on a schedule."
    """
    
    def __init__(self):
        self.zones: Dict[str, Dict] = {}
        self.weather_forecast: List[Dict] = []
    
    def configure_zone(self,
                       zone_id: str,
                       area_sqm: float,
                       plant_type: str,  # turf, shrubs, natives, etc.
                       soil_type: str,
                       sun_exposure: str,
                       sprinkler_type: str):
        """Configure irrigation zone."""
        
        # Base water needs (mm/week)
        plant_needs = {
            "turf": 25,
            "shrubs": 15,
            "flowers": 20,
            "natives": 8,
            "trees": 10
        }
        
        # Soil adjustment
        soil_adjustment = {
            "sand": 1.2,
            "loam": 1.0,
            "clay": 0.8
        }
        
        # Sun adjustment
        sun_adjustment = {
            "full_sun": 1.2,
            "partial": 1.0,
            "shade": 0.7
        }
        
        base_need = plant_needs.get(plant_type, 15)
        adjusted_need = base_need * soil_adjustment.get(soil_type, 1.0) * sun_adjustment.get(sun_exposure, 1.0)
        
        self.zones[zone_id] = {
            "area_sqm": area_sqm,
            "plant_type": plant_type,
            "weekly_need_mm": adjusted_need,
            "weekly_need_liters": adjusted_need * area_sqm,  # 1mm = 1L/sqm
            "sprinkler_type": sprinkler_type
        }
        
        return self.zones[zone_id]
    
    def calculate_schedule(self,
                          zone_id: str,
                          forecast: List[Dict],
                          soil_moisture: float) -> Dict:
        """Calculate optimal irrigation schedule."""
        
        zone = self.zones.get(zone_id)
        if not zone:
            return {"error": "Zone not found"}
        
        # Get rainfall from forecast
        rain_next_7days = sum(f.get("precipitation_mm", 0) for f in forecast[:7])
        
        # Calculate deficit
        weekly_need = zone["weekly_need_mm"]
        effective_rain = rain_next_7days * 0.7  # 70% effective
        
        deficit = weekly_need - effective_rain
        
        # Soil moisture adjustment
        if soil_moisture > 70:
            deficit *= 0.5  # Reduce if soil already moist
        elif soil_moisture < 30:
            deficit *= 1.2  # Increase if soil dry
        
        # If no deficit, skip irrigation
        if deficit <= 0:
            return {
                "zone_id": zone_id,
                "recommendation": "Skip irrigation",
                "reason": f"Forecast rain ({rain_next_7days}mm) exceeds needs",
                "irrigation_liters": 0,
                "schedule": []
            }
        
        # Calculate irrigation
        irrigation_liters = deficit * zone["area_sqm"]
        
        # Determine best days (avoid rainy days)
        schedule = []
        remaining = irrigation_liters
        
        for i, day in enumerate(forecast[:7]):
            if remaining <= 0:
                break
            
            if day.get("precipitation_mm", 0) < 5:  # Low rain expected
                daily_max = zone["weekly_need_liters"] / 3  # Max 3 days/week
                today_amount = min(remaining, daily_max)
                
                if today_amount > 0:
                    schedule.append({
                        "day": i,
                        "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "liters": round(today_amount, 0),
                        "duration_minutes": round(today_amount / 20, 0)  # Assume 20 L/min
                    })
                    remaining -= today_amount
        
        return {
            "zone_id": zone_id,
            "weekly_need_mm": weekly_need,
            "forecast_rain_mm": rain_next_7days,
            "deficit_mm": max(0, deficit),
            "irrigation_liters": round(irrigation_liters, 0),
            "schedule": schedule,
            "water_savings_vs_schedule": f"{round((1 - deficit/weekly_need) * 100)}%"
        }


# =============================================================================
# BUILDING WATER MANAGER
# =============================================================================

class BuildingWaterManager:
    """
    Complete building water management system.
    
    "Your building's water brain."
    """
    
    def __init__(self):
        self.buildings: Dict[str, SmartBuilding] = {}
        self.fixture_monitor = FixtureLevelMonitor()
        self.cooling_optimizer = CoolingTowerOptimizer()
        self.irrigation_controller = SmartIrrigationController()
    
    def register_building(self, building: SmartBuilding) -> Dict:
        """Register building for management."""
        
        self.buildings[building.building_id] = building
        
        # Calculate baseline metrics
        benchmark = BUILDING_BENCHMARKS.get(building.building_type, {})
        
        return {
            "building_id": building.building_id,
            "name": building.name,
            "type": building.building_type.value,
            "benchmark": benchmark,
            "zones_registered": len(building.zones),
            "features": {
                "rainwater_harvesting": building.rainwater_harvesting,
                "greywater_recycling": building.greywater_recycling,
                "smart_irrigation": building.smart_irrigation
            }
        }
    
    def get_building_dashboard(self, building_id: str) -> Dict:
        """Get building water dashboard."""
        
        building = self.buildings.get(building_id)
        if not building:
            return {"error": "Building not found"}
        
        benchmark = BUILDING_BENCHMARKS.get(building.building_type, {})
        
        # Calculate intensity
        daily_usage = building.annual_usage_kl * 1000 / 365
        intensity = daily_usage / building.occupancy if building.occupancy > 0 else 0
        
        # Determine rating
        if intensity <= benchmark.get("excellent", 0):
            rating = "Excellent ⭐⭐⭐⭐⭐"
        elif intensity <= benchmark.get("good", 0):
            rating = "Good ⭐⭐⭐⭐"
        elif intensity <= benchmark.get("average", 0):
            rating = "Average ⭐⭐⭐"
        else:
            rating = "Needs Improvement ⭐⭐"
        
        return {
            "building": building.name,
            "type": building.building_type.value,
            "overview": {
                "annual_usage_kL": building.annual_usage_kl,
                "annual_cost_USD": building.annual_cost_usd,
                "daily_usage_liters": round(daily_usage, 0),
                "intensity": round(intensity, 1),
                "intensity_unit": benchmark.get("unit", "L/unit"),
                "rating": rating
            },
            "benchmarks": benchmark,
            "infrastructure": {
                "floors": building.floors,
                "zones": len(building.zones),
                "cooling_towers": building.cooling_tower_count,
                "landscape_sqm": building.landscape_area_sqm
            },
            "sustainability": {
                "rainwater_harvesting": building.rainwater_harvesting,
                "greywater_recycling": building.greywater_recycling,
                "leed_certified": building.leed_certified
            }
        }
    
    def get_savings_opportunities(self, building_id: str) -> List[Dict]:
        """Identify water savings opportunities."""
        
        building = self.buildings.get(building_id)
        if not building:
            return []
        
        opportunities = []
        
        # Fixture efficiency
        opportunities.append({
            "category": "Fixtures",
            "opportunity": "Upgrade to WaterSense fixtures",
            "current": "Standard 6 LPF toilets",
            "proposed": "Dual-flush 4.5/3 LPF toilets",
            "annual_savings_kL": building.occupancy * 5 * 250 / 1000,  # 5L saved per person per day
            "implementation_cost_usd": 15000,
            "payback_years": 2.5
        })
        
        # Cooling towers
        if building.cooling_tower_count > 0:
            current_cycles = building.cooling_tower_cycles
            if current_cycles < 6:
                opportunities.append({
                    "category": "Cooling Towers",
                    "opportunity": "Increase cycles of concentration",
                    "current": f"{current_cycles} cycles",
                    "proposed": "6 cycles with improved treatment",
                    "annual_savings_kL": 500 * building.cooling_tower_count,
                    "implementation_cost_usd": 8000 * building.cooling_tower_count,
                    "payback_years": 1.8
                })
        
        # Rainwater
        if not building.rainwater_harvesting and building.landscape_area_sqm > 0:
            roof_area = building.gross_area_sqm / building.floors
            annual_rain_mm = 800  # Assumed
            collection_potential = roof_area * annual_rain_mm * 0.8 / 1000  # 80% capture
            
            opportunities.append({
                "category": "Rainwater Harvesting",
                "opportunity": "Install rainwater collection system",
                "potential_collection_kL": round(collection_potential, 0),
                "use_cases": ["Irrigation", "Cooling tower makeup", "Toilet flushing"],
                "implementation_cost_usd": 25000,
                "payback_years": 4.0
            })
        
        # Greywater
        if not building.greywater_recycling and building.building_type in [BuildingType.HOTEL, BuildingType.HOSPITAL]:
            opportunities.append({
                "category": "Greywater Recycling",
                "opportunity": "Implement greywater treatment system",
                "source": "Showers, basins, laundry",
                "use": "Toilet flushing, irrigation",
                "annual_savings_kL": building.annual_usage_kl * 0.25,
                "implementation_cost_usd": 75000,
                "payback_years": 5.0
            })
        
        # Smart irrigation
        if building.landscape_area_sqm > 500 and not building.smart_irrigation:
            opportunities.append({
                "category": "Smart Irrigation",
                "opportunity": "Weather-based irrigation controller",
                "current": "Timer-based schedule",
                "proposed": "AI-powered with soil sensors",
                "annual_savings_kL": building.landscape_area_sqm * 0.5,
                "implementation_cost_usd": 5000,
                "payback_years": 1.5
            })
        
        return sorted(opportunities, key=lambda x: x.get("payback_years", 99))


# =============================================================================
# DEMO
# =============================================================================

def demo_smart_building():
    """Demo smart building water management."""
    
    print("=" * 70)
    print("🏢 AQUAWATCH ENTERPRISE - SMART BUILDING WATER MANAGEMENT")
    print("=" * 70)
    
    manager = BuildingWaterManager()
    
    # Create sample hotel
    hotel = SmartBuilding(
        building_id="BLD_001",
        name="Cape Town Waterfront Hotel",
        building_type=BuildingType.HOTEL,
        address="V&A Waterfront, Cape Town",
        floors=12,
        gross_area_sqm=15000,
        occupancy=450,  # Average guests per day
        cooling_tower_count=2,
        cooling_tower_cycles=4.5,
        landscape_area_sqm=2000,
        rainwater_harvesting=False,
        greywater_recycling=False,
        smart_irrigation=False,
        leed_certified=False,
        annual_usage_kl=45000,
        annual_cost_usd=180000
    )
    
    # Register building
    manager.register_building(hotel)
    
    # Dashboard
    print("\n📊 BUILDING DASHBOARD:")
    print("-" * 50)
    
    dashboard = manager.get_building_dashboard("BLD_001")
    print(f"Building: {dashboard['building']}")
    print(f"Type: {dashboard['type']}")
    print(f"Annual Usage: {dashboard['overview']['annual_usage_kL']:,} kL")
    print(f"Annual Cost: ${dashboard['overview']['annual_cost_USD']:,}")
    print(f"Water Intensity: {dashboard['overview']['intensity']} {dashboard['overview']['intensity_unit']}")
    print(f"Rating: {dashboard['overview']['rating']}")
    
    # Benchmarks
    print("\n📏 BENCHMARKS:")
    for level, value in dashboard['benchmarks'].items():
        if level != 'unit':
            print(f"  {level}: {value} {dashboard['benchmarks']['unit']}")
    
    # Savings opportunities
    print("\n\n💡 SAVINGS OPPORTUNITIES:")
    print("-" * 50)
    
    opportunities = manager.get_savings_opportunities("BLD_001")
    for opp in opportunities:
        print(f"\n{opp['category']}: {opp['opportunity']}")
        if 'annual_savings_kL' in opp:
            print(f"  Annual Savings: {opp['annual_savings_kL']:,.0f} kL")
        print(f"  Cost: ${opp['implementation_cost_usd']:,}")
        print(f"  Payback: {opp['payback_years']} years")
    
    # Cooling tower optimization
    print("\n\n❄️ COOLING TOWER ANALYSIS:")
    print("-" * 50)
    
    optimizer = CoolingTowerOptimizer()
    balance = optimizer.calculate_water_balance(
        tons_cooling=300,
        delta_t_f=10,
        cycles_of_concentration=4.5,
        hours_operation=14
    )
    
    print(f"Cooling Capacity: {balance['cooling_tons']} tons")
    print(f"Current Cycles: {balance['cycles_of_concentration']}")
    print(f"Daily Water Balance:")
    for key, value in balance['water_balance'].items():
        print(f"  {key}: {value:,}")
    
    # Optimize
    optimization = optimizer.optimize_cycles(
        current_cycles=4.5,
        makeup_water_quality={"conductivity_us": 400},
        cooling_tons=300,
        delta_t_f=10
    )
    
    print(f"\n📈 OPTIMIZATION:")
    print(f"  Optimal Cycles: {optimization['optimal_cycles']}")
    print(f"  Annual Savings: {optimization['annual_savings_kL']:,} kL")
    print(f"  Savings: {optimization['savings_percent']}%")
    
    # Smart irrigation
    print("\n\n🌱 SMART IRRIGATION:")
    print("-" * 50)
    
    irrigation = SmartIrrigationController()
    irrigation.configure_zone(
        zone_id="LAWN_01",
        area_sqm=1500,
        plant_type="turf",
        soil_type="loam",
        sun_exposure="full_sun",
        sprinkler_type="rotary"
    )
    
    # Simulate weather forecast
    forecast = [
        {"day": 0, "precipitation_mm": 0, "temp_c": 28},
        {"day": 1, "precipitation_mm": 0, "temp_c": 30},
        {"day": 2, "precipitation_mm": 15, "temp_c": 24},
        {"day": 3, "precipitation_mm": 5, "temp_c": 22},
        {"day": 4, "precipitation_mm": 0, "temp_c": 25},
        {"day": 5, "precipitation_mm": 0, "temp_c": 27},
        {"day": 6, "precipitation_mm": 0, "temp_c": 29},
    ]
    
    schedule = irrigation.calculate_schedule("LAWN_01", forecast, soil_moisture=45)
    print(f"Zone: LAWN_01")
    print(f"Weekly Need: {schedule['weekly_need_mm']} mm")
    print(f"Forecast Rain: {schedule['forecast_rain_mm']} mm")
    print(f"Deficit: {schedule['deficit_mm']:.1f} mm")
    print(f"Total Irrigation: {schedule['irrigation_liters']:,} L")
    print(f"Water Savings vs Timer: {schedule['water_savings_vs_schedule']}")
    print(f"\nSchedule:")
    for s in schedule['schedule']:
        print(f"  {s['date']}: {s['liters']:,} L ({s['duration_minutes']} min)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_smart_building()
