"""
AquaWatch Asset Health Scoring System
=====================================
Comprehensive infrastructure condition assessment and prioritization system.
Uses multi-factor scoring to determine asset health and replacement priority.

Features:
- Multi-dimensional health scoring
- Risk-based prioritization
- Condition assessment protocols
- Rehabilitation planning
- Investment optimization
- Failure consequence analysis
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from collections import defaultdict


class AssetCategory(Enum):
    """Categories of water infrastructure assets"""
    PIPE = "pipe"
    VALVE = "valve"
    HYDRANT = "hydrant"
    PUMP = "pump"
    RESERVOIR = "reservoir"
    TANK = "tank"
    METER = "meter"
    PRV = "pressure_reducing_valve"
    TREATMENT = "treatment_facility"
    BOREHOLE = "borehole"


class ConditionGrade(Enum):
    """Asset condition grades (1-5 scale)"""
    EXCELLENT = 5    # Like new, no defects
    GOOD = 4         # Minor deterioration
    FAIR = 3         # Moderate deterioration
    POOR = 2         # Significant deterioration
    CRITICAL = 1     # Failure imminent/occurred


class CriticalityLevel(Enum):
    """Asset criticality levels"""
    VERY_HIGH = 5    # System-wide impact
    HIGH = 4         # Major area impact
    MEDIUM = 3       # Local area impact
    LOW = 2          # Minimal impact
    VERY_LOW = 1     # Negligible impact


class MaterialType(Enum):
    """Pipe material types"""
    DUCTILE_IRON = "ductile_iron"
    CAST_IRON = "cast_iron"
    PVC = "pvc"
    HDPE = "hdpe"
    STEEL = "steel"
    ASBESTOS_CEMENT = "asbestos_cement"
    CONCRETE = "concrete"
    GALVANIZED_IRON = "galvanized_iron"


@dataclass
class ConditionFactor:
    """Individual condition assessment factor"""
    factor_id: str
    name: str
    weight: float  # 0-1
    
    # Current assessment
    score: float  # 1-5
    confidence: float  # 0-1
    
    # Assessment details
    assessment_date: datetime
    assessed_by: str
    method: str
    notes: str = ""


@dataclass
class AssetRecord:
    """Comprehensive asset record"""
    asset_id: str
    name: str
    category: AssetCategory
    
    # Location
    zone: str
    dma: str
    latitude: float
    longitude: float
    
    # Physical properties
    material: Optional[MaterialType] = None
    diameter_mm: Optional[float] = None
    length_m: Optional[float] = None
    
    # Installation info
    installation_date: datetime = None
    manufacturer: str = ""
    model: str = ""
    
    # Expected life
    expected_life_years: float = 50.0
    
    # Current values
    replacement_cost: float = 0.0  # ZMW
    book_value: float = 0.0
    
    # Condition factors
    condition_factors: List[ConditionFactor] = field(default_factory=list)
    
    # History
    failure_history: List[Dict] = field(default_factory=list)
    maintenance_history: List[Dict] = field(default_factory=list)
    
    # Scores (calculated)
    health_score: float = 100.0
    criticality_score: float = 50.0
    risk_score: float = 50.0
    priority_rank: int = 0


@dataclass
class HealthAssessment:
    """Complete health assessment result"""
    asset_id: str
    assessment_date: datetime
    
    # Scores
    physical_condition: float
    performance_condition: float
    reliability_score: float
    
    # Overall
    health_score: float  # 0-100
    condition_grade: ConditionGrade
    
    # Remaining life
    remaining_useful_life_years: float
    age_factor: float
    
    # Risk
    probability_of_failure: float
    consequence_of_failure: float
    risk_score: float
    
    # Recommendations
    recommended_action: str
    urgency: str
    estimated_cost: float


class ConditionAssessmentProtocol:
    """Protocols for assessing different asset types"""
    
    def __init__(self):
        self.protocols = self._initialize_protocols()
    
    def _initialize_protocols(self) -> Dict[AssetCategory, Dict]:
        """Initialize assessment protocols for each asset type"""
        return {
            AssetCategory.PIPE: {
                "factors": [
                    {"id": "P01", "name": "Internal Corrosion", "weight": 0.25},
                    {"id": "P02", "name": "External Corrosion", "weight": 0.20},
                    {"id": "P03", "name": "Structural Integrity", "weight": 0.25},
                    {"id": "P04", "name": "Joint Condition", "weight": 0.15},
                    {"id": "P05", "name": "Lining Condition", "weight": 0.15}
                ],
                "expected_life": {
                    MaterialType.DUCTILE_IRON: 80,
                    MaterialType.CAST_IRON: 100,
                    MaterialType.PVC: 50,
                    MaterialType.HDPE: 50,
                    MaterialType.STEEL: 60,
                    MaterialType.ASBESTOS_CEMENT: 70,
                    MaterialType.GALVANIZED_IRON: 40
                }
            },
            AssetCategory.PUMP: {
                "factors": [
                    {"id": "PU01", "name": "Motor Condition", "weight": 0.30},
                    {"id": "PU02", "name": "Impeller Wear", "weight": 0.25},
                    {"id": "PU03", "name": "Seal Condition", "weight": 0.20},
                    {"id": "PU04", "name": "Bearing Condition", "weight": 0.15},
                    {"id": "PU05", "name": "Control System", "weight": 0.10}
                ],
                "expected_life": {"default": 15}
            },
            AssetCategory.VALVE: {
                "factors": [
                    {"id": "V01", "name": "Seal Integrity", "weight": 0.30},
                    {"id": "V02", "name": "Actuator Function", "weight": 0.25},
                    {"id": "V03", "name": "Body Corrosion", "weight": 0.25},
                    {"id": "V04", "name": "Operability", "weight": 0.20}
                ],
                "expected_life": {"default": 30}
            },
            AssetCategory.TANK: {
                "factors": [
                    {"id": "T01", "name": "Structural Integrity", "weight": 0.30},
                    {"id": "T02", "name": "Internal Coating", "weight": 0.25},
                    {"id": "T03", "name": "External Coating", "weight": 0.15},
                    {"id": "T04", "name": "Roof Condition", "weight": 0.15},
                    {"id": "T05", "name": "Foundation", "weight": 0.15}
                ],
                "expected_life": {"default": 50}
            },
            AssetCategory.PRV: {
                "factors": [
                    {"id": "PR01", "name": "Pressure Control Accuracy", "weight": 0.35},
                    {"id": "PR02", "name": "Diaphragm Condition", "weight": 0.25},
                    {"id": "PR03", "name": "Pilot System", "weight": 0.20},
                    {"id": "PR04", "name": "Body Condition", "weight": 0.20}
                ],
                "expected_life": {"default": 20}
            }
        }
    
    def get_protocol(self, category: AssetCategory) -> Dict:
        """Get assessment protocol for asset category"""
        return self.protocols.get(category, {
            "factors": [{"id": "GEN01", "name": "General Condition", "weight": 1.0}],
            "expected_life": {"default": 25}
        })


class CriticalityAnalyzer:
    """Analyze asset criticality and failure consequences"""
    
    def __init__(self):
        # Criticality factors with weights
        self.factors = {
            "population_served": {"weight": 0.20, "description": "Number of customers affected"},
            "redundancy": {"weight": 0.15, "description": "Alternative supply availability"},
            "repair_difficulty": {"weight": 0.15, "description": "Complexity of repair"},
            "strategic_importance": {"weight": 0.20, "description": "Critical facilities served"},
            "economic_impact": {"weight": 0.15, "description": "Business/industry impact"},
            "environmental_risk": {"weight": 0.15, "description": "Environmental damage potential"}
        }
    
    def calculate_criticality(self, asset: AssetRecord, network_data: Dict = None) -> Dict:
        """Calculate asset criticality score"""
        scores = {}
        
        # Default assessments based on asset category and zone
        zone_population = {
            "CBD": 50000,
            "Kabulonga": 15000,
            "Woodlands": 20000,
            "Matero": 80000,
            "Kabwata": 35000,
            "Industrial": 5000
        }
        
        zone_importance = {
            "CBD": 0.9,
            "Kabulonga": 0.7,
            "Industrial": 0.8,
            "Woodlands": 0.6,
            "Matero": 0.5,
            "Kabwata": 0.5
        }
        
        # Population served factor
        pop = zone_population.get(asset.zone, 20000)
        scores["population_served"] = min(5, 1 + pop / 20000)
        
        # Redundancy factor (lower redundancy = higher criticality)
        if asset.category == AssetCategory.PIPE and asset.diameter_mm:
            if asset.diameter_mm >= 300:
                scores["redundancy"] = 4.5  # Trunk mains have low redundancy
            elif asset.diameter_mm >= 150:
                scores["redundancy"] = 3.5
            else:
                scores["redundancy"] = 2.5
        else:
            scores["redundancy"] = 3.0
        
        # Repair difficulty
        category_repair_difficulty = {
            AssetCategory.PIPE: 3.5,
            AssetCategory.PUMP: 2.5,
            AssetCategory.VALVE: 2.0,
            AssetCategory.TANK: 4.0,
            AssetCategory.RESERVOIR: 4.5,
            AssetCategory.PRV: 2.5
        }
        scores["repair_difficulty"] = category_repair_difficulty.get(asset.category, 3.0)
        
        # Strategic importance
        scores["strategic_importance"] = zone_importance.get(asset.zone, 0.5) * 5
        
        # Economic impact
        if asset.zone == "Industrial":
            scores["economic_impact"] = 4.5
        elif asset.zone == "CBD":
            scores["economic_impact"] = 4.0
        else:
            scores["economic_impact"] = 2.5
        
        # Environmental risk
        if asset.category in [AssetCategory.TANK, AssetCategory.RESERVOIR]:
            scores["environmental_risk"] = 4.0
        else:
            scores["environmental_risk"] = 2.5
        
        # Calculate weighted score
        total_score = sum(
            scores[factor] * self.factors[factor]["weight"]
            for factor in scores
        )
        
        # Normalize to 0-100
        criticality_score = total_score / 5 * 100
        
        # Determine level
        if criticality_score >= 80:
            level = CriticalityLevel.VERY_HIGH
        elif criticality_score >= 60:
            level = CriticalityLevel.HIGH
        elif criticality_score >= 40:
            level = CriticalityLevel.MEDIUM
        elif criticality_score >= 20:
            level = CriticalityLevel.LOW
        else:
            level = CriticalityLevel.VERY_LOW
        
        return {
            "score": criticality_score,
            "level": level,
            "factor_scores": scores,
            "consequence_of_failure": self._estimate_failure_consequence(asset, scores)
        }
    
    def _estimate_failure_consequence(self, asset: AssetRecord, factor_scores: Dict) -> Dict:
        """Estimate consequences of asset failure"""
        # Service disruption (hours)
        base_disruption = {
            AssetCategory.PIPE: 12,
            AssetCategory.PUMP: 8,
            AssetCategory.VALVE: 4,
            AssetCategory.TANK: 24,
            AssetCategory.PRV: 6
        }
        disruption_hours = base_disruption.get(asset.category, 8) * factor_scores.get("repair_difficulty", 3) / 3
        
        # Customer impact
        customers_affected = int(factor_scores.get("population_served", 3) * 5000)
        
        # Financial impact (ZMW)
        repair_cost = asset.replacement_cost * 0.3  # Assume repair is 30% of replacement
        lost_revenue = customers_affected * 0.5 * disruption_hours / 24  # Assuming K0.5/customer/day
        economic_loss = factor_scores.get("economic_impact", 2.5) * 10000
        
        return {
            "disruption_hours": disruption_hours,
            "customers_affected": customers_affected,
            "estimated_repair_cost_zmw": repair_cost,
            "lost_revenue_zmw": lost_revenue,
            "economic_loss_zmw": economic_loss,
            "total_failure_cost_zmw": repair_cost + lost_revenue + economic_loss
        }


class AssetHealthScoring:
    """Main asset health scoring engine"""
    
    def __init__(self):
        self.assets: Dict[str, AssetRecord] = {}
        self.protocol = ConditionAssessmentProtocol()
        self.criticality_analyzer = CriticalityAnalyzer()
        
        # Initialize demo assets
        self._initialize_demo_assets()
    
    def _initialize_demo_assets(self):
        """Initialize demo asset inventory"""
        demo_assets = [
            # Pipes
            {
                "asset_id": "PIPE_001",
                "name": "Iolanda Main Trunk",
                "category": AssetCategory.PIPE,
                "zone": "CBD",
                "dma": "DMA_CBD_01",
                "lat": -15.4167, "lon": 28.2833,
                "material": MaterialType.DUCTILE_IRON,
                "diameter": 600,
                "length": 2500,
                "installed": datetime(1985, 3, 15),
                "replacement_cost": 8500000,
                "condition_scores": {"P01": 3.5, "P02": 3.0, "P03": 4.0, "P04": 3.5, "P05": 3.0}
            },
            {
                "asset_id": "PIPE_002",
                "name": "Kabulonga Distribution Main",
                "category": AssetCategory.PIPE,
                "zone": "Kabulonga",
                "dma": "DMA_KAB_01",
                "lat": -15.4100, "lon": 28.3100,
                "material": MaterialType.PVC,
                "diameter": 200,
                "length": 1800,
                "installed": datetime(2005, 7, 20),
                "replacement_cost": 1200000,
                "condition_scores": {"P01": 4.5, "P02": 4.0, "P03": 4.5, "P04": 4.0, "P05": 4.5}
            },
            {
                "asset_id": "PIPE_003",
                "name": "Matero Old Cast Iron",
                "category": AssetCategory.PIPE,
                "zone": "Matero",
                "dma": "DMA_MAT_01",
                "lat": -15.3900, "lon": 28.2500,
                "material": MaterialType.CAST_IRON,
                "diameter": 150,
                "length": 3200,
                "installed": datetime(1970, 1, 1),
                "replacement_cost": 2800000,
                "condition_scores": {"P01": 2.0, "P02": 1.5, "P03": 2.5, "P04": 2.0, "P05": 1.5}
            },
            # Pumps
            {
                "asset_id": "PUMP_001",
                "name": "Iolanda Booster Pump 1",
                "category": AssetCategory.PUMP,
                "zone": "CBD",
                "dma": "DMA_CBD_01",
                "lat": -15.4150, "lon": 28.2850,
                "installed": datetime(2015, 6, 1),
                "replacement_cost": 450000,
                "manufacturer": "Grundfos",
                "model": "CR 90-3",
                "condition_scores": {"PU01": 3.5, "PU02": 3.0, "PU03": 3.5, "PU04": 3.0, "PU05": 4.0}
            },
            {
                "asset_id": "PUMP_002",
                "name": "Chelstone Pump Station P2",
                "category": AssetCategory.PUMP,
                "zone": "Chelstone",
                "dma": "DMA_CHE_01",
                "lat": -15.3600, "lon": 28.3500,
                "installed": datetime(2008, 11, 15),
                "replacement_cost": 380000,
                "manufacturer": "KSB",
                "model": "Omega 150-340",
                "condition_scores": {"PU01": 2.5, "PU02": 2.0, "PU03": 2.5, "PU04": 2.0, "PU05": 3.0}
            },
            # Valves
            {
                "asset_id": "VALVE_001",
                "name": "CBD Main Isolation Valve",
                "category": AssetCategory.VALVE,
                "zone": "CBD",
                "dma": "DMA_CBD_01",
                "lat": -15.4160, "lon": 28.2860,
                "diameter": 500,
                "installed": datetime(1995, 4, 10),
                "replacement_cost": 180000,
                "condition_scores": {"V01": 3.0, "V02": 3.5, "V03": 3.0, "V04": 2.5}
            },
            # PRVs
            {
                "asset_id": "PRV_001",
                "name": "Woodlands PRV Station",
                "category": AssetCategory.PRV,
                "zone": "Woodlands",
                "dma": "DMA_WDL_01",
                "lat": -15.4000, "lon": 28.3200,
                "installed": datetime(2018, 2, 28),
                "replacement_cost": 95000,
                "manufacturer": "Bermad",
                "model": "720-ES",
                "condition_scores": {"PR01": 4.5, "PR02": 4.0, "PR03": 4.5, "PR04": 4.5}
            },
            # Tanks
            {
                "asset_id": "TANK_001",
                "name": "Kabulonga Elevated Tank",
                "category": AssetCategory.TANK,
                "zone": "Kabulonga",
                "dma": "DMA_KAB_01",
                "lat": -15.4050, "lon": 28.3150,
                "installed": datetime(1990, 8, 1),
                "replacement_cost": 3500000,
                "condition_scores": {"T01": 3.0, "T02": 2.5, "T03": 3.0, "T04": 3.5, "T05": 4.0}
            },
            {
                "asset_id": "TANK_002",
                "name": "Industrial Zone Ground Tank",
                "category": AssetCategory.TANK,
                "zone": "Industrial",
                "dma": "DMA_IND_01",
                "lat": -15.4500, "lon": 28.3100,
                "installed": datetime(2000, 5, 15),
                "replacement_cost": 2800000,
                "condition_scores": {"T01": 4.0, "T02": 3.5, "T03": 4.0, "T04": 4.0, "T05": 4.0}
            }
        ]
        
        for ad in demo_assets:
            asset = AssetRecord(
                asset_id=ad["asset_id"],
                name=ad["name"],
                category=ad["category"],
                zone=ad["zone"],
                dma=ad["dma"],
                latitude=ad["lat"],
                longitude=ad["lon"],
                material=ad.get("material"),
                diameter_mm=ad.get("diameter"),
                length_m=ad.get("length"),
                installation_date=ad.get("installed"),
                manufacturer=ad.get("manufacturer", ""),
                model=ad.get("model", ""),
                replacement_cost=ad.get("replacement_cost", 0)
            )
            
            # Create condition factors
            protocol = self.protocol.get_protocol(asset.category)
            for factor_def in protocol["factors"]:
                score = ad.get("condition_scores", {}).get(factor_def["id"], 3.0)
                factor = ConditionFactor(
                    factor_id=factor_def["id"],
                    name=factor_def["name"],
                    weight=factor_def["weight"],
                    score=score,
                    confidence=0.85,
                    assessment_date=datetime.now() - timedelta(days=30),
                    assessed_by="System",
                    method="Automated Assessment"
                )
                asset.condition_factors.append(factor)
            
            # Add failure history for old assets
            if asset.installation_date and asset.installation_date.year < 2000:
                asset.failure_history = [
                    {"date": datetime.now() - timedelta(days=365), "type": "leak", "severity": "moderate"},
                    {"date": datetime.now() - timedelta(days=730), "type": "break", "severity": "major"}
                ]
            
            self.assets[asset.asset_id] = asset
    
    def calculate_health_score(self, asset_id: str) -> HealthAssessment:
        """Calculate comprehensive health score for asset"""
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # 1. Physical condition score (from condition factors)
        physical_score = 0.0
        if asset.condition_factors:
            weighted_sum = sum(
                f.score * f.weight * f.confidence 
                for f in asset.condition_factors
            )
            weight_sum = sum(f.weight * f.confidence for f in asset.condition_factors)
            physical_score = weighted_sum / weight_sum if weight_sum > 0 else 3.0
        else:
            physical_score = 3.0
        
        # 2. Age factor
        if asset.installation_date:
            age_years = (datetime.now() - asset.installation_date).days / 365.25
            
            # Get expected life
            protocol = self.protocol.get_protocol(asset.category)
            expected_life = protocol.get("expected_life", {}).get("default", 50)
            if asset.material and isinstance(protocol.get("expected_life"), dict):
                expected_life = protocol["expected_life"].get(asset.material, expected_life)
            
            age_factor = min(1.0, age_years / expected_life)
        else:
            age_years = 25
            age_factor = 0.5
            expected_life = 50
        
        # 3. Performance condition (based on failure history)
        failures_per_year = len(asset.failure_history) / max(1, age_years)
        if failures_per_year == 0:
            performance_score = 5.0
        elif failures_per_year < 0.1:
            performance_score = 4.0
        elif failures_per_year < 0.2:
            performance_score = 3.0
        elif failures_per_year < 0.5:
            performance_score = 2.0
        else:
            performance_score = 1.0
        
        # 4. Reliability score (combination of physical and performance)
        reliability_score = physical_score * 0.6 + performance_score * 0.4
        
        # 5. Overall health score (0-100)
        # Physical: 50%, Age: 30%, Performance: 20%
        health_score = (
            (physical_score / 5) * 50 +
            (1 - age_factor) * 30 +
            (performance_score / 5) * 20
        )
        
        # 6. Condition grade
        if health_score >= 80:
            grade = ConditionGrade.EXCELLENT
        elif health_score >= 60:
            grade = ConditionGrade.GOOD
        elif health_score >= 40:
            grade = ConditionGrade.FAIR
        elif health_score >= 20:
            grade = ConditionGrade.POOR
        else:
            grade = ConditionGrade.CRITICAL
        
        # 7. Remaining useful life
        remaining_life = max(0, expected_life - age_years) * (health_score / 100)
        
        # 8. Probability of failure (Weibull-based)
        beta = 2.5  # Shape parameter
        eta = expected_life * 0.8  # Scale parameter
        pof = 1 - np.exp(-(age_years / eta) ** beta)
        pof = min(0.95, pof * (1 + (1 - health_score/100)))
        
        # 9. Criticality and consequence
        criticality = self.criticality_analyzer.calculate_criticality(asset)
        cof = criticality["consequence_of_failure"]["total_failure_cost_zmw"]
        
        # 10. Risk score
        risk_score = pof * (criticality["score"] / 100) * 100
        
        # 11. Recommended action
        if health_score < 20:
            action = "Immediate replacement required"
            urgency = "critical"
        elif health_score < 40:
            action = "Schedule replacement within 1 year"
            urgency = "high"
        elif health_score < 60:
            action = "Plan rehabilitation or replacement within 3 years"
            urgency = "medium"
        elif health_score < 80:
            action = "Continue monitoring, minor maintenance may be needed"
            urgency = "low"
        else:
            action = "Asset in good condition, routine maintenance only"
            urgency = "routine"
        
        # Update asset scores
        asset.health_score = health_score
        asset.criticality_score = criticality["score"]
        asset.risk_score = risk_score
        
        return HealthAssessment(
            asset_id=asset_id,
            assessment_date=datetime.now(),
            physical_condition=physical_score,
            performance_condition=performance_score,
            reliability_score=reliability_score,
            health_score=health_score,
            condition_grade=grade,
            remaining_useful_life_years=remaining_life,
            age_factor=age_factor,
            probability_of_failure=pof,
            consequence_of_failure=cof,
            risk_score=risk_score,
            recommended_action=action,
            urgency=urgency,
            estimated_cost=asset.replacement_cost
        )
    
    def get_asset_inventory_summary(self) -> Dict:
        """Get summary of asset inventory"""
        summary = {
            "total_assets": len(self.assets),
            "by_category": defaultdict(int),
            "by_condition": defaultdict(int),
            "by_zone": defaultdict(int),
            "total_replacement_value": 0,
            "average_health_score": 0
        }
        
        health_scores = []
        
        for asset in self.assets.values():
            summary["by_category"][asset.category.value] += 1
            summary["by_zone"][asset.zone] += 1
            summary["total_replacement_value"] += asset.replacement_cost
            
            # Calculate health if not done
            assessment = self.calculate_health_score(asset.asset_id)
            health_scores.append(assessment.health_score)
            summary["by_condition"][assessment.condition_grade.name] += 1
        
        summary["average_health_score"] = np.mean(health_scores) if health_scores else 0
        summary["by_category"] = dict(summary["by_category"])
        summary["by_condition"] = dict(summary["by_condition"])
        summary["by_zone"] = dict(summary["by_zone"])
        
        return summary
    
    def get_prioritized_assets(self, top_n: int = 10) -> List[Dict]:
        """Get prioritized list of assets for intervention"""
        assessments = []
        
        for asset_id in self.assets:
            assessment = self.calculate_health_score(asset_id)
            asset = self.assets[asset_id]
            
            assessments.append({
                "asset_id": asset_id,
                "name": asset.name,
                "category": asset.category.value,
                "zone": asset.zone,
                "health_score": assessment.health_score,
                "risk_score": assessment.risk_score,
                "condition_grade": assessment.condition_grade.value,
                "remaining_life_years": assessment.remaining_useful_life_years,
                "probability_of_failure": assessment.probability_of_failure,
                "replacement_cost_zmw": asset.replacement_cost,
                "recommended_action": assessment.recommended_action,
                "urgency": assessment.urgency
            })
        
        # Sort by risk score (descending) then by health score (ascending)
        assessments.sort(key=lambda x: (-x["risk_score"], x["health_score"]))
        
        # Assign priority ranks
        for i, a in enumerate(assessments):
            a["priority_rank"] = i + 1
        
        return assessments[:top_n]
    
    def get_rehabilitation_plan(self, budget_zmw: float, years: int = 5) -> Dict:
        """Generate rehabilitation plan within budget"""
        assessments = self.get_prioritized_assets(top_n=len(self.assets))
        
        plan = {
            "total_budget_zmw": budget_zmw,
            "planning_horizon_years": years,
            "annual_budget_zmw": budget_zmw / years,
            "phases": [],
            "summary": {
                "total_assets_planned": 0,
                "total_investment_zmw": 0,
                "expected_risk_reduction": 0
            }
        }
        
        remaining_budget = budget_zmw
        annual_budget = budget_zmw / years
        
        for year in range(1, years + 1):
            year_budget = min(annual_budget, remaining_budget)
            year_plan = {
                "year": year,
                "budget_zmw": year_budget,
                "assets": [],
                "total_cost_zmw": 0
            }
            
            for asset_data in assessments:
                if asset_data["priority_rank"] <= 0:
                    continue
                    
                cost = asset_data["replacement_cost_zmw"]
                
                # Only include if fits in budget and urgency matches year
                urgency_year_map = {"critical": 1, "high": 2, "medium": 3, "low": 4, "routine": 5}
                target_year = urgency_year_map.get(asset_data["urgency"], 5)
                
                if target_year <= year and cost <= (year_budget - year_plan["total_cost_zmw"]):
                    year_plan["assets"].append({
                        "asset_id": asset_data["asset_id"],
                        "name": asset_data["name"],
                        "cost_zmw": cost,
                        "action": asset_data["recommended_action"]
                    })
                    year_plan["total_cost_zmw"] += cost
                    asset_data["priority_rank"] = -1  # Mark as planned
                    
                    plan["summary"]["total_assets_planned"] += 1
                    plan["summary"]["total_investment_zmw"] += cost
            
            remaining_budget -= year_plan["total_cost_zmw"]
            plan["phases"].append(year_plan)
        
        return plan
    
    def get_asset_dashboard(self, asset_id: str) -> Dict:
        """Get complete dashboard for single asset"""
        asset = self.assets.get(asset_id)
        if not asset:
            return {"error": "Asset not found"}
        
        assessment = self.calculate_health_score(asset_id)
        criticality = self.criticality_analyzer.calculate_criticality(asset)
        
        return {
            "asset": {
                "id": asset.asset_id,
                "name": asset.name,
                "category": asset.category.value,
                "zone": asset.zone,
                "dma": asset.dma,
                "location": {"lat": asset.latitude, "lon": asset.longitude},
                "material": asset.material.value if asset.material else None,
                "diameter_mm": asset.diameter_mm,
                "length_m": asset.length_m,
                "installation_date": asset.installation_date.isoformat() if asset.installation_date else None,
                "manufacturer": asset.manufacturer,
                "model": asset.model
            },
            "health": {
                "score": assessment.health_score,
                "grade": assessment.condition_grade.value,
                "physical_condition": assessment.physical_condition,
                "performance_condition": assessment.performance_condition,
                "reliability": assessment.reliability_score,
                "age_factor": assessment.age_factor * 100,
                "remaining_life_years": assessment.remaining_useful_life_years
            },
            "risk": {
                "score": assessment.risk_score,
                "probability_of_failure": assessment.probability_of_failure * 100,
                "consequence_of_failure_zmw": assessment.consequence_of_failure
            },
            "criticality": {
                "score": criticality["score"],
                "level": criticality["level"].value,
                "factors": criticality["factor_scores"]
            },
            "condition_factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "assessment_date": f.assessment_date.isoformat()
                }
                for f in asset.condition_factors
            ],
            "failure_history": asset.failure_history,
            "financial": {
                "replacement_cost_zmw": asset.replacement_cost,
                "book_value_zmw": asset.book_value
            },
            "recommendation": {
                "action": assessment.recommended_action,
                "urgency": assessment.urgency,
                "estimated_cost_zmw": assessment.estimated_cost
            }
        }


# Global instance
asset_health_system = AssetHealthScoring()


def get_asset_health_system() -> AssetHealthScoring:
    """Get global asset health system"""
    return asset_health_system


if __name__ == "__main__":
    # Demo
    system = AssetHealthScoring()
    
    print("=" * 60)
    print("AquaWatch Asset Health Scoring System")
    print("=" * 60)
    
    # Inventory summary
    summary = system.get_asset_inventory_summary()
    print(f"\nAsset Inventory Summary:")
    print(f"  Total Assets: {summary['total_assets']}")
    print(f"  Total Replacement Value: K{summary['total_replacement_value']:,.0f}")
    print(f"  Average Health Score: {summary['average_health_score']:.1f}/100")
    
    print(f"\n  By Category:")
    for cat, count in summary["by_category"].items():
        print(f"    {cat}: {count}")
    
    print(f"\n  By Condition:")
    for cond, count in summary["by_condition"].items():
        print(f"    {cond}: {count}")
    
    # Priority list
    print(f"\n{'='*60}")
    print("Priority Assets for Intervention")
    print("-" * 60)
    
    priorities = system.get_prioritized_assets(5)
    for p in priorities:
        print(f"\n{p['priority_rank']}. {p['name']}")
        print(f"   Health: {p['health_score']:.0f}/100 | Risk: {p['risk_score']:.0f}")
        print(f"   Grade: {p['condition_grade']} | Urgency: {p['urgency']}")
        print(f"   Cost: K{p['replacement_cost_zmw']:,.0f}")
        print(f"   → {p['recommended_action']}")
    
    # Rehabilitation plan
    print(f"\n{'='*60}")
    print("5-Year Rehabilitation Plan (K20M Budget)")
    plan = system.get_rehabilitation_plan(20000000, 5)
    
    for phase in plan["phases"]:
        print(f"\nYear {phase['year']} - Budget: K{phase['budget_zmw']:,.0f}")
        if phase["assets"]:
            for asset in phase["assets"]:
                print(f"  • {asset['name']}: K{asset['cost_zmw']:,.0f}")
        else:
            print("  • No assets scheduled")
    
    print(f"\nTotal Planned: {plan['summary']['total_assets_planned']} assets")
    print(f"Total Investment: K{plan['summary']['total_investment_zmw']:,.0f}")
