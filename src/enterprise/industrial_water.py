"""
AquaWatch Enterprise - Industrial Water Intelligence
====================================================

"Water is the new oil. Manage it like one."

Solutions for water-intensive industries:
- Manufacturing (beverages, semiconductors, pharma, textiles)
- Data Centers (cooling optimization)
- Mining (water recycling, compliance)
- Food & Agriculture (irrigation, processing)
- Commercial Real Estate (building efficiency)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# INDUSTRY TYPES
# =============================================================================

class Industry(Enum):
    BEVERAGE = "beverage"
    SEMICONDUCTOR = "semiconductor"
    PHARMACEUTICAL = "pharmaceutical"
    TEXTILE = "textile"
    DATA_CENTER = "data_center"
    MINING = "mining"
    FOOD_PROCESSING = "food_processing"
    AGRICULTURE = "agriculture"
    COMMERCIAL_REAL_ESTATE = "commercial_real_estate"
    HOSPITALITY = "hospitality"
    HEALTHCARE = "healthcare"


# Industry-specific water metrics
INDUSTRY_BENCHMARKS = {
    Industry.BEVERAGE: {
        "unit": "liters_per_liter_product",
        "benchmark": 2.5,  # 2.5L water per 1L beverage
        "best_in_class": 1.5,
        "typical_range": (2.0, 4.0)
    },
    Industry.SEMICONDUCTOR: {
        "unit": "liters_per_wafer",
        "benchmark": 8000,
        "best_in_class": 5000,
        "typical_range": (6000, 12000)
    },
    Industry.DATA_CENTER: {
        "unit": "liters_per_kwh",  # WUE - Water Usage Effectiveness
        "benchmark": 1.8,
        "best_in_class": 0.5,
        "typical_range": (1.0, 3.0)
    },
    Industry.MINING: {
        "unit": "liters_per_ton_ore",
        "benchmark": 1000,
        "best_in_class": 500,
        "typical_range": (500, 3000)
    },
    Industry.TEXTILE: {
        "unit": "liters_per_kg_fabric",
        "benchmark": 100,
        "best_in_class": 50,
        "typical_range": (50, 200)
    },
    Industry.FOOD_PROCESSING: {
        "unit": "liters_per_kg_product",
        "benchmark": 10,
        "best_in_class": 5,
        "typical_range": (5, 25)
    }
}


# =============================================================================
# FACILITY MODEL
# =============================================================================

@dataclass
class WaterSource:
    """Water supply source."""
    source_id: str
    source_type: str  # municipal, groundwell, surface, recycled, rainwater
    capacity_m3_day: float
    cost_per_m3: float
    reliability_score: float  # 0-1
    quality_grade: str  # A, B, C
    is_primary: bool = True


@dataclass
class WaterProcess:
    """Industrial water process/use case."""
    process_id: str
    name: str
    water_type_required: str  # raw, filtered, DI, ultrapure
    consumption_m3_day: float
    criticality: str  # critical, important, optional
    can_use_recycled: bool = False
    recycling_potential_pct: float = 0.0


@dataclass
class IndustrialFacility:
    """Large industrial facility with water needs."""
    facility_id: str
    name: str
    industry: Industry
    location: Tuple[float, float]
    country: str
    
    # Water sources
    water_sources: List[WaterSource] = field(default_factory=list)
    
    # Processes
    processes: List[WaterProcess] = field(default_factory=list)
    
    # Metrics
    total_intake_m3_day: float = 0.0
    total_discharge_m3_day: float = 0.0
    total_consumption_m3_day: float = 0.0  # Intake - Discharge
    recycling_rate_pct: float = 0.0
    
    # Compliance
    discharge_permit_m3_day: float = 0.0
    discharge_quality_limits: Dict = field(default_factory=dict)
    
    # Targets
    water_reduction_target_pct: float = 20.0
    net_zero_water_target_year: int = 2030


# =============================================================================
# WATER EFFICIENCY AI
# =============================================================================

class WaterEfficiencyAI:
    """
    AI engine for industrial water optimization.
    
    "Every drop counts. Every drop is measured. Every drop is optimized."
    """
    
    def __init__(self):
        self.facilities: Dict[str, IndustrialFacility] = {}
        self.optimization_history: List[Dict] = []
    
    def analyze_facility(self, facility: IndustrialFacility) -> Dict:
        """Comprehensive facility water analysis."""
        
        benchmark = INDUSTRY_BENCHMARKS.get(facility.industry, {})
        
        # Calculate current efficiency
        if facility.total_intake_m3_day > 0:
            efficiency_ratio = facility.total_consumption_m3_day / facility.total_intake_m3_day
        else:
            efficiency_ratio = 1.0
        
        # Identify opportunities
        opportunities = []
        
        # 1. Check recycling potential
        total_recyclable = sum(
            p.consumption_m3_day * p.recycling_potential_pct / 100
            for p in facility.processes
            if p.can_use_recycled
        )
        
        if total_recyclable > 0:
            opportunities.append({
                "type": "recycling_expansion",
                "title": "Expand Water Recycling",
                "potential_savings_m3_day": total_recyclable,
                "potential_cost_savings_usd_year": total_recyclable * 365 * 2.5,
                "investment_required_usd": total_recyclable * 1000,
                "payback_months": 12,
                "priority": "high"
            })
        
        # 2. Check for cooling tower optimization
        cooling_processes = [p for p in facility.processes if "cooling" in p.name.lower()]
        if cooling_processes:
            cooling_savings = sum(p.consumption_m3_day * 0.15 for p in cooling_processes)
            opportunities.append({
                "type": "cooling_optimization",
                "title": "Cooling Tower Efficiency",
                "description": "Increase cycles of concentration, add side-stream filtration",
                "potential_savings_m3_day": cooling_savings,
                "potential_cost_savings_usd_year": cooling_savings * 365 * 2.5,
                "priority": "medium"
            })
        
        # 3. Check for rainwater harvesting
        opportunities.append({
            "type": "rainwater_harvesting",
            "title": "Rainwater Collection",
            "description": f"Install collection on {facility.name} roof area",
            "potential_savings_m3_day": 50,  # Estimate
            "potential_cost_savings_usd_year": 50 * 365 * 2.0,
            "priority": "low"
        })
        
        # 4. Smart leak detection
        estimated_losses = facility.total_intake_m3_day * 0.05  # Assume 5% losses
        opportunities.append({
            "type": "leak_detection",
            "title": "AI-Powered Leak Detection",
            "description": "Install AquaWatch sensors throughout facility",
            "potential_savings_m3_day": estimated_losses,
            "potential_cost_savings_usd_year": estimated_losses * 365 * 2.5,
            "priority": "high"
        })
        
        return {
            "facility_id": facility.facility_id,
            "facility_name": facility.name,
            "industry": facility.industry.value,
            "current_metrics": {
                "intake_m3_day": facility.total_intake_m3_day,
                "discharge_m3_day": facility.total_discharge_m3_day,
                "consumption_m3_day": facility.total_consumption_m3_day,
                "recycling_rate_pct": facility.recycling_rate_pct,
                "efficiency_ratio": efficiency_ratio
            },
            "benchmark_comparison": {
                "industry_benchmark": benchmark.get("benchmark", "N/A"),
                "best_in_class": benchmark.get("best_in_class", "N/A"),
                "your_position": "Above average" if efficiency_ratio < 0.8 else "Below average"
            },
            "opportunities": opportunities,
            "total_potential_savings": {
                "water_m3_year": sum(o.get("potential_savings_m3_day", 0) * 365 for o in opportunities),
                "cost_usd_year": sum(o.get("potential_cost_savings_usd_year", 0) for o in opportunities)
            }
        }
    
    def optimize_water_allocation(self, 
                                   facility: IndustrialFacility,
                                   constraint: str = "cost") -> Dict:
        """
        Optimize water allocation across sources and processes.
        
        Constraints:
        - cost: Minimize total water cost
        - reliability: Maximize supply reliability
        - sustainability: Maximize recycled water usage
        """
        
        # Simple optimization logic (would use linear programming in production)
        
        if constraint == "cost":
            # Sort sources by cost
            sorted_sources = sorted(facility.water_sources, key=lambda s: s.cost_per_m3)
            allocation = []
            remaining_demand = facility.total_consumption_m3_day
            
            for source in sorted_sources:
                allocated = min(remaining_demand, source.capacity_m3_day)
                if allocated > 0:
                    allocation.append({
                        "source": source.source_id,
                        "type": source.source_type,
                        "allocated_m3_day": allocated,
                        "cost_per_m3": source.cost_per_m3,
                        "daily_cost": allocated * source.cost_per_m3
                    })
                    remaining_demand -= allocated
            
            return {
                "optimization_type": "cost_minimization",
                "allocation": allocation,
                "total_daily_cost": sum(a["daily_cost"] for a in allocation),
                "unmet_demand": remaining_demand
            }
        
        elif constraint == "reliability":
            # Diversify across reliable sources
            allocation = []
            for source in facility.water_sources:
                if source.reliability_score > 0.8:
                    allocation.append({
                        "source": source.source_id,
                        "allocated_m3_day": source.capacity_m3_day * 0.7,
                        "reliability": source.reliability_score
                    })
            
            return {
                "optimization_type": "reliability_maximization",
                "allocation": allocation,
                "overall_reliability": sum(a["reliability"] for a in allocation) / len(allocation) if allocation else 0
            }
        
        return {"error": "Unknown constraint"}


# =============================================================================
# DATA CENTER COOLING OPTIMIZER
# =============================================================================

class DataCenterWaterOptimizer:
    """
    Specialized optimizer for data center cooling.
    
    "Microsoft, Google, and Amazon spend billions on cooling.
     We help them spend less."
    """
    
    def __init__(self):
        self.wue_target = 1.0  # Water Usage Effectiveness target (L/kWh)
    
    def analyze_cooling_system(self, 
                               it_load_kw: float,
                               cooling_type: str,
                               current_wue: float,
                               location_climate: str) -> Dict:
        """Analyze data center cooling efficiency."""
        
        # Climate-based recommendations
        climate_factors = {
            "hot_humid": {"free_cooling_hours": 1000, "evaporative_efficiency": 0.7},
            "hot_dry": {"free_cooling_hours": 2000, "evaporative_efficiency": 0.9},
            "temperate": {"free_cooling_hours": 4000, "evaporative_efficiency": 0.8},
            "cold": {"free_cooling_hours": 6000, "evaporative_efficiency": 0.6}
        }
        
        climate = climate_factors.get(location_climate, climate_factors["temperate"])
        
        # Current water usage
        current_water_m3_year = it_load_kw * current_wue * 8760 / 1000
        
        recommendations = []
        
        # 1. Increase free cooling hours
        if climate["free_cooling_hours"] > 2000:
            savings = current_water_m3_year * 0.3  # 30% reduction potential
            recommendations.append({
                "type": "free_cooling_expansion",
                "title": "Expand Free Cooling",
                "description": f"Your climate supports {climate['free_cooling_hours']} free cooling hours/year",
                "water_savings_m3_year": savings,
                "cost_savings_usd_year": savings * 3.0,
                "implementation_cost": 500000,
                "payback_years": 500000 / (savings * 3.0) if savings > 0 else 999
            })
        
        # 2. Improve cooling tower cycles
        recommendations.append({
            "type": "cycles_of_concentration",
            "title": "Increase Cycles of Concentration",
            "description": "Increase from 3 to 8 cycles with better water treatment",
            "water_savings_m3_year": current_water_m3_year * 0.25,
            "cost_savings_usd_year": current_water_m3_year * 0.25 * 3.0,
            "implementation_cost": 100000
        })
        
        # 3. Alternative cooling
        if location_climate in ["temperate", "cold"]:
            recommendations.append({
                "type": "indirect_evaporative",
                "title": "Switch to Indirect Evaporative Cooling",
                "description": "Uses 90% less water than traditional cooling towers",
                "water_savings_m3_year": current_water_m3_year * 0.9,
                "cost_savings_usd_year": current_water_m3_year * 0.9 * 3.0,
                "implementation_cost": 2000000
            })
        
        # 4. AI-based predictive cooling
        recommendations.append({
            "type": "ai_cooling_prediction",
            "title": "AI Predictive Cooling",
            "description": "ML model predicts cooling needs 24h ahead, pre-positions resources",
            "water_savings_m3_year": current_water_m3_year * 0.15,
            "efficiency_improvement_pct": 15,
            "implementation_cost": 200000
        })
        
        # Calculate optimal WUE
        optimal_wue = current_wue * 0.5  # 50% improvement potential
        
        return {
            "current_state": {
                "it_load_kw": it_load_kw,
                "cooling_type": cooling_type,
                "current_wue": current_wue,
                "water_usage_m3_year": current_water_m3_year,
                "water_cost_usd_year": current_water_m3_year * 3.0
            },
            "target_state": {
                "optimal_wue": optimal_wue,
                "target_water_m3_year": it_load_kw * optimal_wue * 8760 / 1000,
                "potential_savings_usd_year": (current_water_m3_year - it_load_kw * optimal_wue * 8760 / 1000) * 3.0
            },
            "recommendations": recommendations,
            "benchmark": {
                "industry_average_wue": 1.8,
                "best_in_class_wue": 0.2,  # Google's best
                "your_percentile": 75 if current_wue < 1.5 else 50 if current_wue < 2.0 else 25
            }
        }


# =============================================================================
# MINING WATER MANAGEMENT
# =============================================================================

class MiningWaterManager:
    """
    Water management for mining operations.
    
    Handles:
    - Process water recycling
    - Tailings water recovery
    - Dewatering optimization
    - Compliance monitoring
    """
    
    def __init__(self):
        self.water_quality_limits = {
            "pH": (6.5, 8.5),
            "TSS_mg_L": 50,
            "heavy_metals_mg_L": 0.1,
            "sulfate_mg_L": 500
        }
    
    def analyze_mining_operation(self,
                                  ore_processed_tons_day: float,
                                  current_water_intensity: float,
                                  tailings_volume_m3_day: float,
                                  recycling_rate_pct: float) -> Dict:
        """Analyze mining water efficiency."""
        
        # Current usage
        fresh_water_m3_day = ore_processed_tons_day * current_water_intensity * (1 - recycling_rate_pct/100)
        
        opportunities = []
        
        # 1. Tailings water recovery
        recoverable = tailings_volume_m3_day * 0.7  # 70% recoverable
        opportunities.append({
            "type": "tailings_recovery",
            "title": "Enhanced Tailings Water Recovery",
            "description": "Install paste thickeners and advanced dewatering",
            "water_recovery_m3_day": recoverable,
            "cost_savings_usd_year": recoverable * 365 * 4.0,  # Water expensive in mining
            "investment_usd": 5000000,
            "payback_years": 5000000 / (recoverable * 365 * 4.0)
        })
        
        # 2. Dry processing
        if ore_processed_tons_day > 10000:
            opportunities.append({
                "type": "dry_processing",
                "title": "Partial Dry Processing",
                "description": "Convert some wet processes to dry alternatives",
                "water_reduction_pct": 30,
                "investment_usd": 10000000
            })
        
        # 3. Real-time water quality monitoring
        opportunities.append({
            "type": "quality_monitoring",
            "title": "AI Water Quality Monitoring",
            "description": "Real-time sensors with ML anomaly detection",
            "benefit": "Prevent discharge violations, early contamination detection",
            "investment_usd": 500000
        })
        
        return {
            "current_metrics": {
                "ore_processed_tons_day": ore_processed_tons_day,
                "water_intensity_m3_ton": current_water_intensity,
                "fresh_water_m3_day": fresh_water_m3_day,
                "recycling_rate_pct": recycling_rate_pct,
                "tailings_m3_day": tailings_volume_m3_day
            },
            "benchmark": {
                "industry_average_intensity": 1.0,
                "best_practice_intensity": 0.5,
                "best_practice_recycling": 85
            },
            "opportunities": opportunities,
            "compliance_status": {
                "discharge_within_limits": True,
                "monitoring_frequency": "continuous",
                "last_violation": None
            }
        }


# =============================================================================
# WATER RISK ASSESSMENT
# =============================================================================

class WaterRiskAssessment:
    """
    Enterprise water risk assessment.
    
    Analyzes:
    - Physical risk (scarcity, floods)
    - Regulatory risk (permits, pricing)
    - Reputational risk (community, ESG)
    - Supply chain water risk
    """
    
    def __init__(self):
        # Water stress by region (simplified)
        self.regional_stress = {
            "Southern Africa": 0.7,  # High stress
            "East Africa": 0.5,
            "West Africa": 0.4,
            "North Africa": 0.9,  # Extreme stress
            "India": 0.8,
            "China_North": 0.8,
            "China_South": 0.4,
            "USA_Southwest": 0.7,
            "USA_Midwest": 0.3,
            "Europe": 0.3,
            "Southeast_Asia": 0.4
        }
    
    def assess_facility_risk(self, 
                            facility: IndustrialFacility,
                            region: str) -> Dict:
        """Comprehensive water risk assessment."""
        
        base_stress = self.regional_stress.get(region, 0.5)
        
        # Physical Risk
        physical_risk = {
            "baseline_water_stress": base_stress,
            "drought_frequency": "High" if base_stress > 0.6 else "Medium" if base_stress > 0.4 else "Low",
            "flood_risk": random.choice(["Low", "Medium", "High"]),
            "groundwater_depletion": base_stress > 0.5,
            "climate_change_projection": f"+{int(base_stress * 30)}% stress by 2040",
            "risk_score": base_stress * 100
        }
        
        # Regulatory Risk
        regulatory_risk = {
            "discharge_permit_status": "Compliant",
            "upcoming_regulations": [
                "Stricter discharge limits (2027)",
                "Mandatory water recycling targets (2028)",
                "Water pricing reform (2026)"
            ],
            "carbon_water_nexus": "Water treatment linked to carbon accounting",
            "risk_score": 45 if base_stress > 0.5 else 30
        }
        
        # Reputational Risk
        reputational_risk = {
            "community_water_conflicts": base_stress > 0.6,
            "esg_investor_scrutiny": "High",
            "brand_exposure": "Medium",
            "social_license_risk": "Elevated" if base_stress > 0.5 else "Low",
            "risk_score": 60 if base_stress > 0.6 else 35
        }
        
        # Financial Risk
        daily_water_cost = facility.total_intake_m3_day * 2.5
        financial_risk = {
            "current_water_cost_usd_year": daily_water_cost * 365,
            "projected_cost_increase_pct": 50 if base_stress > 0.6 else 25,
            "business_interruption_exposure_usd": facility.total_intake_m3_day * 1000 * 30,  # 30 days outage
            "stranded_asset_risk": base_stress > 0.7,
            "risk_score": 70 if base_stress > 0.6 else 40
        }
        
        # Overall risk score
        overall_score = (
            physical_risk["risk_score"] * 0.35 +
            regulatory_risk["risk_score"] * 0.25 +
            reputational_risk["risk_score"] * 0.20 +
            financial_risk["risk_score"] * 0.20
        )
        
        return {
            "facility": facility.name,
            "region": region,
            "overall_risk_score": round(overall_score, 1),
            "risk_category": "Critical" if overall_score > 70 else "High" if overall_score > 50 else "Medium" if overall_score > 30 else "Low",
            "physical_risk": physical_risk,
            "regulatory_risk": regulatory_risk,
            "reputational_risk": reputational_risk,
            "financial_risk": financial_risk,
            "mitigation_recommendations": [
                "Diversify water sources",
                "Invest in on-site recycling",
                "Engage with local water stewardship initiatives",
                "Set science-based water targets",
                "Install AquaWatch monitoring across facility"
            ]
        }
    
    def assess_supply_chain(self, 
                           suppliers: List[Dict],
                           product: str) -> Dict:
        """Assess water risk across supply chain."""
        
        supplier_risks = []
        total_water_footprint = 0
        
        for supplier in suppliers:
            region = supplier.get("region", "Unknown")
            water_use = supplier.get("water_m3_per_unit", 100)
            volume = supplier.get("volume_units", 1000)
            
            stress = self.regional_stress.get(region, 0.5)
            risk_score = stress * 100
            
            footprint = water_use * volume
            total_water_footprint += footprint
            
            supplier_risks.append({
                "supplier": supplier.get("name"),
                "region": region,
                "water_stress": stress,
                "risk_score": risk_score,
                "water_footprint_m3": footprint,
                "risk_level": "Critical" if risk_score > 70 else "High" if risk_score > 50 else "Medium"
            })
        
        # Sort by risk
        supplier_risks.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "product": product,
            "total_water_footprint_m3": total_water_footprint,
            "supplier_count": len(suppliers),
            "high_risk_suppliers": len([s for s in supplier_risks if s["risk_score"] > 50]),
            "supplier_analysis": supplier_risks,
            "recommendations": [
                f"Engage with {supplier_risks[0]['supplier']} on water efficiency" if supplier_risks else "",
                "Require water disclosure from all Tier 1 suppliers",
                "Set water reduction targets in supplier contracts",
                "Develop alternative suppliers in lower-risk regions"
            ]
        }


# =============================================================================
# DEMO
# =============================================================================

def demo_enterprise():
    """Demo enterprise water solutions."""
    
    print("=" * 70)
    print("🏭 AQUAWATCH ENTERPRISE - INDUSTRIAL WATER INTELLIGENCE")
    print("=" * 70)
    
    # Create sample facility
    facility = IndustrialFacility(
        facility_id="FAC_001",
        name="Coca-Cola Lusaka Bottling Plant",
        industry=Industry.BEVERAGE,
        location=(-15.4167, 28.2833),
        country="Zambia",
        water_sources=[
            WaterSource("WS_MUNICIPAL", "municipal", 2000, 1.5, 0.9, "A"),
            WaterSource("WS_BOREHOLE", "groundwell", 500, 0.8, 0.95, "A"),
            WaterSource("WS_RECYCLED", "recycled", 300, 0.5, 1.0, "B", False)
        ],
        processes=[
            WaterProcess("P_PRODUCTION", "Beverage Production", "ultrapure", 1500, "critical", False, 0),
            WaterProcess("P_CLEANING", "CIP Cleaning", "filtered", 300, "important", True, 60),
            WaterProcess("P_COOLING", "Cooling Towers", "raw", 400, "important", True, 80),
            WaterProcess("P_SANITARY", "Sanitary/Domestic", "filtered", 100, "optional", False, 0)
        ],
        total_intake_m3_day=2300,
        total_discharge_m3_day=800,
        total_consumption_m3_day=1500,
        recycling_rate_pct=25
    )
    
    # Water Efficiency Analysis
    print("\n📊 WATER EFFICIENCY ANALYSIS:")
    print("-" * 50)
    
    ai = WaterEfficiencyAI()
    analysis = ai.analyze_facility(facility)
    
    print(f"Facility: {analysis['facility_name']}")
    print(f"Industry: {analysis['industry'].title()}")
    print(f"\nCurrent Metrics:")
    print(f"  Intake: {analysis['current_metrics']['intake_m3_day']:,.0f} m³/day")
    print(f"  Consumption: {analysis['current_metrics']['consumption_m3_day']:,.0f} m³/day")
    print(f"  Recycling: {analysis['current_metrics']['recycling_rate_pct']}%")
    
    print(f"\n💡 OPTIMIZATION OPPORTUNITIES:")
    for opp in analysis['opportunities'][:3]:
        print(f"  • {opp['title']}")
        if 'potential_savings_m3_day' in opp:
            print(f"    Savings: {opp['potential_savings_m3_day']:.0f} m³/day")
    
    print(f"\nTotal Potential Savings:")
    print(f"  Water: {analysis['total_potential_savings']['water_m3_year']:,.0f} m³/year")
    print(f"  Cost: ${analysis['total_potential_savings']['cost_usd_year']:,.0f}/year")
    
    # Data Center Optimization
    print("\n\n🖥️ DATA CENTER COOLING OPTIMIZATION:")
    print("-" * 50)
    
    dc_optimizer = DataCenterWaterOptimizer()
    dc_analysis = dc_optimizer.analyze_cooling_system(
        it_load_kw=10000,  # 10 MW data center
        cooling_type="evaporative",
        current_wue=1.8,
        location_climate="hot_dry"
    )
    
    print(f"IT Load: {dc_analysis['current_state']['it_load_kw']:,} kW")
    print(f"Current WUE: {dc_analysis['current_state']['current_wue']} L/kWh")
    print(f"Water Usage: {dc_analysis['current_state']['water_usage_m3_year']:,.0f} m³/year")
    print(f"\nTarget WUE: {dc_analysis['target_state']['optimal_wue']} L/kWh")
    print(f"Potential Savings: ${dc_analysis['target_state']['potential_savings_usd_year']:,.0f}/year")
    
    # Risk Assessment
    print("\n\n⚠️ WATER RISK ASSESSMENT:")
    print("-" * 50)
    
    risk_assessor = WaterRiskAssessment()
    risk = risk_assessor.assess_facility_risk(facility, "Southern Africa")
    
    print(f"Overall Risk Score: {risk['overall_risk_score']}/100 ({risk['risk_category']})")
    print(f"\nRisk Breakdown:")
    print(f"  Physical Risk: {risk['physical_risk']['risk_score']:.0f}/100")
    print(f"  Regulatory Risk: {risk['regulatory_risk']['risk_score']:.0f}/100")
    print(f"  Reputational Risk: {risk['reputational_risk']['risk_score']:.0f}/100")
    print(f"  Financial Risk: {risk['financial_risk']['risk_score']:.0f}/100")
    
    print(f"\n🎯 TOP RECOMMENDATIONS:")
    for rec in risk['mitigation_recommendations'][:3]:
        print(f"  • {rec}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_enterprise()
