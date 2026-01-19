"""
AquaWatch Predictive Maintenance AI
===================================
ML-driven asset degradation prediction, failure forecasting, and optimal
maintenance scheduling for water network infrastructure.

Features:
- Asset failure prediction
- Remaining useful life (RUL) estimation
- Maintenance optimization
- Risk-based prioritization
- Cost-benefit analysis
- Condition-based maintenance triggers
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from collections import defaultdict
import uuid


class AssetCategory(Enum):
    """Categories of water network assets"""
    PIPE = "pipe"
    VALVE = "valve"
    PUMP = "pump"
    MOTOR = "motor"
    PRV = "pressure_reducing_valve"
    METER = "meter"
    TANK = "tank"
    HYDRANT = "hydrant"
    FITTING = "fitting"
    SENSOR = "sensor"


class FailureMode(Enum):
    """Common failure modes"""
    CORROSION = "corrosion"
    FATIGUE = "fatigue"
    WEAR = "mechanical_wear"
    LEAKAGE = "leakage"
    BLOCKAGE = "blockage"
    ELECTRICAL = "electrical_failure"
    SEAL_FAILURE = "seal_failure"
    BEARING_FAILURE = "bearing_failure"
    CAVITATION = "cavitation"
    JOINT_FAILURE = "joint_failure"


class MaintenanceType(Enum):
    """Types of maintenance activities"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    CONDITION_BASED = "condition_based"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"


class MaintenancePriority(Enum):
    """Maintenance priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ROUTINE = "routine"


@dataclass
class Asset:
    """Represents a network asset"""
    asset_id: str
    name: str
    category: AssetCategory
    
    # Location
    latitude: float
    longitude: float
    zone_id: str
    
    # Installation details
    manufacturer: str
    model: str
    serial_number: str
    install_date: datetime
    expected_life_years: int
    
    # Current condition
    condition_score: float = 1.0  # 0-1 (1 = perfect)
    health_index: float = 100.0  # 0-100
    
    # Operating parameters
    operating_hours: float = 0.0
    cycles_count: int = 0
    
    # Material (for pipes)
    material: str = ""
    size_mm: int = 0
    
    # Failure history
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    mtbf_hours: float = 0.0  # Mean Time Between Failures
    
    # Maintenance history
    last_maintenance: Optional[datetime] = None
    maintenance_count: int = 0
    
    # Cost information
    replacement_cost: float = 0.0
    maintenance_cost_ytd: float = 0.0


@dataclass
class FailurePrediction:
    """Failure prediction result"""
    asset_id: str
    prediction_date: datetime
    
    # Probability
    failure_probability_30d: float  # Probability of failure in 30 days
    failure_probability_90d: float
    failure_probability_1yr: float
    
    # Remaining useful life
    rul_days: float
    rul_confidence: float
    
    # Likely failure modes
    failure_modes: List[Dict]  # mode, probability
    
    # Risk score
    risk_score: float  # 0-100
    risk_factors: List[str]
    
    # Recommendation
    recommended_action: str
    recommended_date: datetime
    urgency: MaintenancePriority


@dataclass
class MaintenanceTask:
    """Scheduled maintenance task"""
    task_id: str
    asset_id: str
    task_type: MaintenanceType
    priority: MaintenancePriority
    
    # Scheduling
    scheduled_date: datetime
    estimated_duration: float  # hours
    
    # Details
    description: str
    procedures: List[str]
    required_parts: List[Dict]
    required_skills: List[str]
    
    # Costs
    estimated_labor_cost: float
    estimated_parts_cost: float
    
    # Status
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    assigned_to: Optional[str] = None
    
    # Outcome
    completed_date: Optional[datetime] = None
    actual_cost: float = 0.0
    findings: str = ""


class DegradationModel:
    """Models asset degradation over time"""
    
    def __init__(self):
        # Degradation parameters by asset category
        self.degradation_params = {
            AssetCategory.PIPE: {
                "base_rate": 0.02,  # 2% per year base degradation
                "material_factors": {
                    "PVC": 0.8,
                    "HDPE": 0.7,
                    "Ductile Iron": 1.0,
                    "Steel": 1.3,
                    "Cast Iron": 1.5,
                    "Asbestos Cement": 1.8
                },
                "soil_factors": {
                    "sandy": 0.9,
                    "clay": 1.2,
                    "corrosive": 1.5,
                    "rocky": 1.1
                }
            },
            AssetCategory.PUMP: {
                "base_rate": 0.05,
                "operating_hours_factor": 0.00001,  # Per operating hour
                "cycles_factor": 0.000005  # Per start/stop cycle
            },
            AssetCategory.VALVE: {
                "base_rate": 0.03,
                "cycles_factor": 0.0001
            },
            AssetCategory.METER: {
                "base_rate": 0.04,
                "accuracy_degradation": 0.005  # Per year
            }
        }
        
        # Weibull parameters for failure probability
        self.weibull_params = {
            AssetCategory.PIPE: {"shape": 2.5, "scale": 50},  # years
            AssetCategory.PUMP: {"shape": 2.0, "scale": 15},
            AssetCategory.VALVE: {"shape": 2.2, "scale": 25},
            AssetCategory.METER: {"shape": 3.0, "scale": 12},
            AssetCategory.PRV: {"shape": 2.0, "scale": 20}
        }
    
    def calculate_degradation(
        self,
        asset: Asset,
        environmental_factors: Dict = None
    ) -> Dict:
        """
        Calculate asset degradation state.
        
        Returns:
            Degradation analysis including current state and projections
        """
        params = self.degradation_params.get(asset.category, {"base_rate": 0.03})
        base_rate = params["base_rate"]
        
        # Calculate age-based degradation
        age_years = (datetime.now() - asset.install_date).days / 365.25
        
        # Adjust for material (pipes)
        material_factor = 1.0
        if asset.category == AssetCategory.PIPE and "material_factors" in params:
            material_factor = params["material_factors"].get(asset.material, 1.2)
        
        # Adjust for environmental factors
        env_factor = 1.0
        if environmental_factors:
            if "soil_type" in environmental_factors and "soil_factors" in params:
                env_factor *= params["soil_factors"].get(
                    environmental_factors["soil_type"], 1.0
                )
            if "water_quality" in environmental_factors:
                # Aggressive water increases degradation
                env_factor *= environmental_factors.get("water_quality_factor", 1.0)
        
        # Calculate operating stress (pumps, valves)
        stress_factor = 1.0
        if "operating_hours_factor" in params and asset.operating_hours > 0:
            stress_factor += params["operating_hours_factor"] * asset.operating_hours
        if "cycles_factor" in params and asset.cycles_count > 0:
            stress_factor += params["cycles_factor"] * asset.cycles_count
        
        # Calculate degradation
        annual_degradation = base_rate * material_factor * env_factor * stress_factor
        cumulative_degradation = annual_degradation * age_years
        
        # Calculate condition score (1 = new, 0 = failed)
        condition_score = max(0, 1 - cumulative_degradation)
        
        # Health index (0-100)
        health_index = condition_score * 100
        
        # Project future degradation
        years_to_50_percent = (0.5 / annual_degradation) if annual_degradation > 0 else 100
        years_to_failure = (1.0 / annual_degradation) if annual_degradation > 0 else 100
        
        return {
            "asset_id": asset.asset_id,
            "age_years": age_years,
            "annual_degradation_rate": annual_degradation,
            "cumulative_degradation": cumulative_degradation,
            "condition_score": condition_score,
            "health_index": health_index,
            "factors": {
                "base_rate": base_rate,
                "material_factor": material_factor,
                "environmental_factor": env_factor,
                "stress_factor": stress_factor
            },
            "projections": {
                "years_to_50_percent": years_to_50_percent - age_years,
                "years_to_failure": years_to_failure - age_years,
                "end_of_life_date": (
                    asset.install_date + timedelta(days=years_to_failure * 365)
                ).isoformat()
            }
        }
    
    def calculate_failure_probability(
        self,
        asset: Asset,
        time_horizon_days: int
    ) -> float:
        """
        Calculate probability of failure within time horizon.
        Uses Weibull distribution.
        """
        params = self.weibull_params.get(
            asset.category,
            {"shape": 2.0, "scale": 20}
        )
        
        shape = params["shape"]
        scale = params["scale"] * 365  # Convert to days
        
        # Current age in days
        age_days = (datetime.now() - asset.install_date).days
        
        # Adjust scale based on condition
        if asset.condition_score < 1.0:
            # Lower condition = higher failure probability
            scale *= asset.condition_score
        
        # Calculate cumulative failure probability
        # P(T <= t) = 1 - exp(-(t/scale)^shape)
        current_survival = np.exp(-((age_days / scale) ** shape))
        future_survival = np.exp(-(((age_days + time_horizon_days) / scale) ** shape))
        
        # Conditional probability of failure
        failure_prob = 1 - (future_survival / current_survival) if current_survival > 0 else 1.0
        
        return min(max(failure_prob, 0), 1)


class MaintenanceOptimizer:
    """Optimizes maintenance scheduling"""
    
    def __init__(self):
        # Labor costs (ZMW per hour)
        self.labor_rates = {
            "technician": 150,
            "senior_technician": 200,
            "engineer": 350,
            "specialist": 500
        }
        
        # Maintenance interval guidelines (days)
        self.maintenance_intervals = {
            AssetCategory.PUMP: {
                "inspection": 30,
                "minor_service": 90,
                "major_service": 365
            },
            AssetCategory.VALVE: {
                "inspection": 90,
                "exercise": 180,
                "rebuild": 730
            },
            AssetCategory.PRV: {
                "inspection": 30,
                "calibration": 180,
                "overhaul": 730
            },
            AssetCategory.METER: {
                "inspection": 365,
                "calibration": 730,
                "replacement": 3650
            }
        }
    
    def calculate_optimal_interval(
        self,
        asset: Asset,
        failure_cost: float
    ) -> Dict:
        """
        Calculate optimal maintenance interval using cost optimization.
        
        Minimizes total cost = maintenance cost + expected failure cost
        """
        # Get base interval
        intervals = self.maintenance_intervals.get(
            asset.category,
            {"inspection": 180, "service": 365}
        )
        
        base_interval = intervals.get("minor_service", intervals.get("inspection", 180))
        
        # Adjust based on condition
        condition_factor = 2 - asset.condition_score  # 1-2x depending on condition
        
        # Calculate optimal interval
        # Optimal interval ∝ sqrt(maintenance_cost / failure_cost)
        maintenance_cost = self._estimate_maintenance_cost(asset, "preventive")
        
        if failure_cost > 0:
            cost_ratio = maintenance_cost / failure_cost
            interval_factor = np.sqrt(cost_ratio) if cost_ratio > 0 else 1
        else:
            interval_factor = 1
        
        optimal_days = int(base_interval * interval_factor / condition_factor)
        optimal_days = max(7, min(optimal_days, 730))  # Clamp 7 days to 2 years
        
        # Calculate expected costs
        annual_maintenance_cost = (365 / optimal_days) * maintenance_cost
        annual_failure_cost = failure_cost * (1 - asset.condition_score) * 0.5
        total_annual_cost = annual_maintenance_cost + annual_failure_cost
        
        return {
            "asset_id": asset.asset_id,
            "optimal_interval_days": optimal_days,
            "current_condition": asset.condition_score,
            "maintenance_cost_per_event": maintenance_cost,
            "failure_cost": failure_cost,
            "annual_costs": {
                "maintenance": annual_maintenance_cost,
                "expected_failure": annual_failure_cost,
                "total": total_annual_cost
            },
            "next_maintenance": (
                datetime.now() + timedelta(days=optimal_days)
            ).isoformat()
        }
    
    def _estimate_maintenance_cost(self, asset: Asset, maintenance_type: str) -> float:
        """Estimate maintenance cost"""
        base_costs = {
            AssetCategory.PUMP: {"preventive": 2500, "corrective": 15000},
            AssetCategory.VALVE: {"preventive": 500, "corrective": 3000},
            AssetCategory.PRV: {"preventive": 800, "corrective": 5000},
            AssetCategory.METER: {"preventive": 200, "corrective": 1500},
            AssetCategory.PIPE: {"preventive": 1000, "corrective": 25000}
        }
        
        costs = base_costs.get(asset.category, {"preventive": 1000, "corrective": 5000})
        return costs.get(maintenance_type, 1000)
    
    def prioritize_maintenance(
        self,
        predictions: List[FailurePrediction]
    ) -> List[Dict]:
        """
        Prioritize maintenance based on risk and cost.
        
        Returns ranked list of assets requiring attention.
        """
        priority_list = []
        
        for pred in predictions:
            # Calculate priority score
            # Higher score = more urgent
            risk_weight = pred.risk_score / 100
            prob_weight = pred.failure_probability_30d
            
            # Combine factors
            priority_score = (
                risk_weight * 0.4 +
                prob_weight * 0.3 +
                (1 - pred.rul_days / 365) * 0.3  # Shorter RUL = higher priority
            )
            
            priority_list.append({
                "asset_id": pred.asset_id,
                "priority_score": priority_score,
                "failure_probability_30d": pred.failure_probability_30d,
                "rul_days": pred.rul_days,
                "risk_score": pred.risk_score,
                "urgency": pred.urgency.value,
                "recommended_action": pred.recommended_action,
                "recommended_date": pred.recommended_date.isoformat()
            })
        
        # Sort by priority score (descending)
        priority_list.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return priority_list


class PredictiveMaintenanceEngine:
    """
    Main engine for predictive maintenance.
    """
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.predictions: Dict[str, FailurePrediction] = {}
        self.tasks: Dict[str, MaintenanceTask] = {}
        
        self.degradation_model = DegradationModel()
        self.optimizer = MaintenanceOptimizer()
        
        # Historical data
        self.maintenance_history: List[Dict] = []
        self.failure_history: List[Dict] = []
        
        # Initialize demo assets
        self._initialize_demo_assets()
    
    def _initialize_demo_assets(self):
        """Initialize demo assets for Lusaka network"""
        assets_data = [
            # Pumps
            {
                "asset_id": "PUMP_IOLANDA_01",
                "name": "Iolanda Main Pump 1",
                "category": AssetCategory.PUMP,
                "coords": (-15.3875, 28.3228),
                "zone": "ZONE_CBD",
                "manufacturer": "Grundfos",
                "model": "SP 125-3",
                "install_date": datetime(2015, 3, 15),
                "expected_life": 15,
                "operating_hours": 45000,
                "replacement_cost": 250000
            },
            {
                "asset_id": "PUMP_MATERO_01",
                "name": "Matero Booster Pump",
                "category": AssetCategory.PUMP,
                "coords": (-15.3850, 28.2560),
                "zone": "ZONE_MATERO",
                "manufacturer": "KSB",
                "model": "Etanorm",
                "install_date": datetime(2018, 7, 20),
                "expected_life": 15,
                "operating_hours": 28000,
                "replacement_cost": 180000
            },
            # PRVs
            {
                "asset_id": "PRV_CBD_01",
                "name": "CBD Main PRV",
                "category": AssetCategory.PRV,
                "coords": (-15.4150, 28.2840),
                "zone": "ZONE_CBD",
                "manufacturer": "Cla-Val",
                "model": "90-01",
                "install_date": datetime(2012, 5, 10),
                "expected_life": 20,
                "cycles_count": 15000,
                "replacement_cost": 85000
            },
            # Valves
            {
                "asset_id": "VALVE_KAB_01",
                "name": "Kabulonga Gate Valve",
                "category": AssetCategory.VALVE,
                "coords": (-15.3958, 28.3208),
                "zone": "ZONE_KABULONGA",
                "manufacturer": "AVK",
                "model": "Series 56",
                "install_date": datetime(2010, 2, 1),
                "expected_life": 30,
                "cycles_count": 5000,
                "replacement_cost": 25000
            },
            # Pipes
            {
                "asset_id": "PIPE_CBD_MAIN",
                "name": "CBD Main Transmission",
                "category": AssetCategory.PIPE,
                "coords": (-15.4167, 28.2833),
                "zone": "ZONE_CBD",
                "manufacturer": "Saint-Gobain",
                "model": "DN600",
                "install_date": datetime(1985, 1, 1),
                "expected_life": 50,
                "material": "Ductile Iron",
                "size_mm": 600,
                "replacement_cost": 2500000
            },
            {
                "asset_id": "PIPE_WOOD_DIST",
                "name": "Woodlands Distribution",
                "category": AssetCategory.PIPE,
                "coords": (-15.4250, 28.3083),
                "zone": "ZONE_WOODLANDS",
                "manufacturer": "JM Eagle",
                "model": "DN200",
                "install_date": datetime(2008, 6, 15),
                "expected_life": 50,
                "material": "PVC",
                "size_mm": 200,
                "replacement_cost": 450000
            }
        ]
        
        for adata in assets_data:
            asset = Asset(
                asset_id=adata["asset_id"],
                name=adata["name"],
                category=adata["category"],
                latitude=adata["coords"][0],
                longitude=adata["coords"][1],
                zone_id=adata["zone"],
                manufacturer=adata["manufacturer"],
                model=adata["model"],
                serial_number=f"SN{adata['asset_id'][-6:]}",
                install_date=adata["install_date"],
                expected_life_years=adata["expected_life"],
                operating_hours=adata.get("operating_hours", 0),
                cycles_count=adata.get("cycles_count", 0),
                material=adata.get("material", ""),
                size_mm=adata.get("size_mm", 0),
                replacement_cost=adata["replacement_cost"]
            )
            
            # Calculate initial condition
            degradation = self.degradation_model.calculate_degradation(asset)
            asset.condition_score = degradation["condition_score"]
            asset.health_index = degradation["health_index"]
            
            self.assets[asset.asset_id] = asset
    
    def predict_failure(self, asset_id: str) -> FailurePrediction:
        """
        Generate failure prediction for an asset.
        
        Args:
            asset_id: Asset ID
        
        Returns:
            FailurePrediction with probabilities and recommendations
        """
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset = self.assets[asset_id]
        
        # Calculate degradation
        degradation = self.degradation_model.calculate_degradation(asset)
        
        # Calculate failure probabilities
        prob_30d = self.degradation_model.calculate_failure_probability(asset, 30)
        prob_90d = self.degradation_model.calculate_failure_probability(asset, 90)
        prob_1yr = self.degradation_model.calculate_failure_probability(asset, 365)
        
        # Estimate remaining useful life
        rul_days = degradation["projections"]["years_to_failure"] * 365
        rul_days = max(0, min(rul_days, 3650))  # Cap at 10 years
        
        # Identify failure modes
        failure_modes = self._identify_failure_modes(asset)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(asset, prob_90d)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(asset, degradation)
        
        # Determine recommendation
        recommendation, urgency, recommended_date = self._generate_recommendation(
            asset, prob_30d, rul_days, risk_score
        )
        
        prediction = FailurePrediction(
            asset_id=asset_id,
            prediction_date=datetime.now(),
            failure_probability_30d=prob_30d,
            failure_probability_90d=prob_90d,
            failure_probability_1yr=prob_1yr,
            rul_days=rul_days,
            rul_confidence=0.85 if asset.failure_count > 0 else 0.70,
            failure_modes=failure_modes,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommended_action=recommendation,
            recommended_date=recommended_date,
            urgency=urgency
        )
        
        self.predictions[asset_id] = prediction
        
        return prediction
    
    def _identify_failure_modes(self, asset: Asset) -> List[Dict]:
        """Identify likely failure modes for asset"""
        modes = []
        
        if asset.category == AssetCategory.PUMP:
            modes = [
                {"mode": FailureMode.BEARING_FAILURE.value, "probability": 0.35},
                {"mode": FailureMode.SEAL_FAILURE.value, "probability": 0.25},
                {"mode": FailureMode.CAVITATION.value, "probability": 0.20},
                {"mode": FailureMode.ELECTRICAL.value, "probability": 0.20}
            ]
        elif asset.category == AssetCategory.PIPE:
            modes = [
                {"mode": FailureMode.CORROSION.value, "probability": 0.40},
                {"mode": FailureMode.JOINT_FAILURE.value, "probability": 0.30},
                {"mode": FailureMode.FATIGUE.value, "probability": 0.20},
                {"mode": FailureMode.LEAKAGE.value, "probability": 0.10}
            ]
        elif asset.category == AssetCategory.VALVE:
            modes = [
                {"mode": FailureMode.WEAR.value, "probability": 0.40},
                {"mode": FailureMode.CORROSION.value, "probability": 0.30},
                {"mode": FailureMode.SEAL_FAILURE.value, "probability": 0.30}
            ]
        elif asset.category == AssetCategory.PRV:
            modes = [
                {"mode": FailureMode.WEAR.value, "probability": 0.35},
                {"mode": FailureMode.SEAL_FAILURE.value, "probability": 0.35},
                {"mode": FailureMode.BLOCKAGE.value, "probability": 0.30}
            ]
        
        return modes
    
    def _calculate_risk_score(self, asset: Asset, failure_prob: float) -> float:
        """Calculate risk score (0-100)"""
        # Risk = Probability × Consequence
        
        # Consequence based on replacement cost (normalized)
        max_cost = 3000000  # ZMW
        cost_factor = min(asset.replacement_cost / max_cost, 1.0)
        
        # Criticality factor (pipes and pumps are more critical)
        criticality = {
            AssetCategory.PIPE: 1.0,
            AssetCategory.PUMP: 0.9,
            AssetCategory.PRV: 0.7,
            AssetCategory.VALVE: 0.6,
            AssetCategory.METER: 0.4
        }
        crit_factor = criticality.get(asset.category, 0.5)
        
        # Calculate risk
        consequence = cost_factor * 0.6 + crit_factor * 0.4
        risk_score = failure_prob * consequence * 100
        
        return min(risk_score, 100)
    
    def _identify_risk_factors(self, asset: Asset, degradation: Dict) -> List[str]:
        """Identify risk factors for asset"""
        factors = []
        
        age_years = (datetime.now() - asset.install_date).days / 365.25
        
        if age_years > asset.expected_life_years * 0.8:
            factors.append("Approaching end of expected life")
        
        if asset.condition_score < 0.5:
            factors.append("Poor condition score")
        
        if degradation["factors"]["material_factor"] > 1.2:
            factors.append("Material susceptible to degradation")
        
        if asset.failure_count > 2:
            factors.append("History of multiple failures")
        
        if asset.category == AssetCategory.PUMP and asset.operating_hours > 40000:
            factors.append("High operating hours")
        
        if not factors:
            factors.append("No significant risk factors identified")
        
        return factors
    
    def _generate_recommendation(
        self,
        asset: Asset,
        prob_30d: float,
        rul_days: float,
        risk_score: float
    ) -> Tuple[str, MaintenancePriority, datetime]:
        """Generate maintenance recommendation"""
        
        if prob_30d > 0.5 or rul_days < 30:
            return (
                "Immediate inspection and preventive maintenance required",
                MaintenancePriority.CRITICAL,
                datetime.now() + timedelta(days=7)
            )
        elif prob_30d > 0.3 or rul_days < 90:
            return (
                "Schedule preventive maintenance within 30 days",
                MaintenancePriority.HIGH,
                datetime.now() + timedelta(days=30)
            )
        elif prob_30d > 0.1 or rul_days < 180:
            return (
                "Plan maintenance during next scheduled window",
                MaintenancePriority.MEDIUM,
                datetime.now() + timedelta(days=90)
            )
        elif risk_score > 50:
            return (
                "Monitor condition and schedule routine maintenance",
                MaintenancePriority.LOW,
                datetime.now() + timedelta(days=180)
            )
        else:
            return (
                "Continue normal monitoring",
                MaintenancePriority.ROUTINE,
                datetime.now() + timedelta(days=365)
            )
    
    def create_maintenance_task(
        self,
        asset_id: str,
        task_type: MaintenanceType,
        scheduled_date: datetime,
        description: str = ""
    ) -> MaintenanceTask:
        """Create a new maintenance task"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset = self.assets[asset_id]
        
        # Get prediction for priority
        prediction = self.predictions.get(asset_id)
        priority = prediction.urgency if prediction else MaintenancePriority.MEDIUM
        
        # Estimate costs
        labor_cost = 8 * self.optimizer.labor_rates["technician"]  # 8 hours
        parts_cost = self.optimizer._estimate_maintenance_cost(asset, task_type.value) * 0.4
        
        task = MaintenanceTask(
            task_id=f"MT_{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            task_type=task_type,
            priority=priority,
            scheduled_date=scheduled_date,
            estimated_duration=8.0,
            description=description or f"{task_type.value.title()} maintenance for {asset.name}",
            procedures=self._get_maintenance_procedures(asset, task_type),
            required_parts=[],
            required_skills=["technician"],
            estimated_labor_cost=labor_cost,
            estimated_parts_cost=parts_cost
        )
        
        self.tasks[task.task_id] = task
        
        return task
    
    def _get_maintenance_procedures(
        self,
        asset: Asset,
        task_type: MaintenanceType
    ) -> List[str]:
        """Get maintenance procedures for asset type"""
        procedures = {
            AssetCategory.PUMP: [
                "Check and record motor current and voltage",
                "Inspect mechanical seal for leaks",
                "Check bearing temperature and vibration",
                "Inspect impeller and volute for wear",
                "Verify alignment",
                "Test pressure and flow performance"
            ],
            AssetCategory.VALVE: [
                "Operate valve through full stroke",
                "Check for leaks at stem and body",
                "Inspect handwheel and gearing",
                "Lubricate stem threads",
                "Verify position indicator accuracy"
            ],
            AssetCategory.PRV: [
                "Test inlet and outlet pressures",
                "Verify setpoint accuracy",
                "Inspect diaphragm condition",
                "Check pilot system operation",
                "Clean strainer",
                "Calibrate if necessary"
            ],
            AssetCategory.METER: [
                "Compare reading with test meter",
                "Check for register damage",
                "Inspect housing for leaks",
                "Verify accuracy within tolerance",
                "Clean sensor if applicable"
            ]
        }
        
        return procedures.get(asset.category, ["Perform standard inspection"])
    
    def get_maintenance_dashboard(self) -> Dict:
        """Get maintenance system dashboard"""
        # Generate predictions for all assets
        all_predictions = []
        for asset_id in self.assets:
            if asset_id not in self.predictions:
                self.predict_failure(asset_id)
            all_predictions.append(self.predictions[asset_id])
        
        # Prioritize
        priority_list = self.optimizer.prioritize_maintenance(all_predictions)
        
        # Count by urgency
        by_urgency = defaultdict(int)
        for pred in all_predictions:
            by_urgency[pred.urgency.value] += 1
        
        # Assets needing immediate attention
        critical_assets = [
            p for p in priority_list
            if p["urgency"] in ["critical", "high"]
        ]
        
        # Upcoming tasks
        upcoming_tasks = [
            {
                "task_id": t.task_id,
                "asset_id": t.asset_id,
                "type": t.task_type.value,
                "priority": t.priority.value,
                "scheduled": t.scheduled_date.isoformat(),
                "status": t.status
            }
            for t in sorted(self.tasks.values(), key=lambda x: x.scheduled_date)[:10]
        ]
        
        # Calculate costs
        scheduled_costs = sum(
            t.estimated_labor_cost + t.estimated_parts_cost
            for t in self.tasks.values()
            if t.status == "scheduled"
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "assets": {
                "total": len(self.assets),
                "by_category": dict(defaultdict(
                    int,
                    {cat.value: len([a for a in self.assets.values() if a.category == cat])
                     for cat in AssetCategory}
                )),
                "avg_health_index": np.mean([a.health_index for a in self.assets.values()])
            },
            "predictions": {
                "total": len(all_predictions),
                "by_urgency": dict(by_urgency),
                "critical_assets": len(critical_assets),
                "high_risk_count": len([p for p in all_predictions if p.risk_score > 50])
            },
            "priority_list": priority_list[:10],
            "tasks": {
                "total": len(self.tasks),
                "scheduled": len([t for t in self.tasks.values() if t.status == "scheduled"]),
                "upcoming": upcoming_tasks,
                "estimated_cost_zmw": scheduled_costs
            },
            "recommendations": [
                f"Schedule maintenance for {critical_assets[0]['asset_id']}" if critical_assets else "All assets within acceptable parameters"
            ]
        }


# Global instance
maintenance_engine = PredictiveMaintenanceEngine()


def get_maintenance_engine() -> PredictiveMaintenanceEngine:
    """Get global maintenance engine instance"""
    return maintenance_engine


# Alias for compatibility
def get_maintenance_system() -> PredictiveMaintenanceEngine:
    """Get global maintenance system instance (alias for get_maintenance_engine)"""
    return maintenance_engine


if __name__ == "__main__":
    # Demo
    engine = PredictiveMaintenanceEngine()
    
    print("=" * 60)
    print("AquaWatch Predictive Maintenance AI")
    print("=" * 60)
    
    # Get predictions for all assets
    print("\nAsset Predictions:")
    for asset_id in engine.assets:
        prediction = engine.predict_failure(asset_id)
        asset = engine.assets[asset_id]
        print(f"\n  {asset.name}:")
        print(f"    Category: {asset.category.value}")
        print(f"    Health Index: {asset.health_index:.1f}")
        print(f"    Failure Prob (30d): {prediction.failure_probability_30d:.1%}")
        print(f"    RUL: {prediction.rul_days:.0f} days")
        print(f"    Risk Score: {prediction.risk_score:.1f}")
        print(f"    Urgency: {prediction.urgency.value}")
    
    # Dashboard
    print("\nMaintenance Dashboard:")
    dashboard = engine.get_maintenance_dashboard()
    print(f"  Total Assets: {dashboard['assets']['total']}")
    print(f"  Avg Health Index: {dashboard['assets']['avg_health_index']:.1f}")
    print(f"  Critical Assets: {dashboard['predictions']['critical_assets']}")
    print(f"  High Risk: {dashboard['predictions']['high_risk_count']}")
    
    print("\nTop Priority Assets:")
    for item in dashboard["priority_list"][:5]:
        print(f"    - {item['asset_id']}: Score {item['priority_score']:.2f}, "
              f"RUL {item['rul_days']:.0f} days, {item['urgency']}")
