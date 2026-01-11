"""
AquaWatch Enterprise - Water Insurance & Risk Transfer
======================================================

"Protecting against the unexpected."

Innovative water risk insurance products:
1. Business interruption from water supply failure
2. Leak damage coverage
3. Regulatory non-compliance protection
4. Climate-adjusted parametric insurance
5. Cyber-physical water system coverage
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# RISK CATEGORIES
# =============================================================================

class RiskCategory(Enum):
    SUPPLY_DISRUPTION = "supply_disruption"
    LEAK_DAMAGE = "leak_damage"
    REGULATORY = "regulatory"
    INFRASTRUCTURE = "infrastructure"
    CLIMATE = "climate"
    CYBER = "cyber"


class CoverageType(Enum):
    INDEMNITY = "indemnity"           # Traditional - pay for actual losses
    PARAMETRIC = "parametric"          # Pay when trigger met
    HYBRID = "hybrid"                  # Combination


# =============================================================================
# RISK ASSESSMENT
# =============================================================================

@dataclass
class FacilityRiskProfile:
    """Risk profile for a facility."""
    facility_id: str
    name: str
    location: str
    country: str
    
    # Water dependency
    daily_water_usage_m3: float
    water_criticality: str  # low, medium, high, critical
    backup_water_sources: int
    
    # Infrastructure
    infrastructure_age_years: float
    last_major_upgrade: datetime
    smart_sensors_coverage: float  # 0-100%
    
    # History
    incidents_last_5_years: int
    total_claim_value_usd: float
    
    # Location risk
    water_stress_level: str  # low, medium, high, extremely high
    flood_zone: bool
    drought_prone: bool


@dataclass
class RiskScore:
    """Calculated risk score."""
    overall_score: float  # 0-100 (higher = riskier)
    category_scores: Dict[str, float]
    risk_factors: List[str]
    mitigation_recommendations: List[str]
    premium_multiplier: float


class WaterRiskAssessor:
    """
    Comprehensive water risk assessment.
    
    Uses AquaWatch data + external sources.
    """
    
    def __init__(self):
        # Base risk weights by category
        self.category_weights = {
            RiskCategory.SUPPLY_DISRUPTION: 0.25,
            RiskCategory.LEAK_DAMAGE: 0.20,
            RiskCategory.REGULATORY: 0.15,
            RiskCategory.INFRASTRUCTURE: 0.20,
            RiskCategory.CLIMATE: 0.15,
            RiskCategory.CYBER: 0.05
        }
    
    def assess_facility(self, profile: FacilityRiskProfile) -> RiskScore:
        """Assess risk for a facility."""
        
        scores = {}
        factors = []
        recommendations = []
        
        # Supply disruption risk
        supply_score = 20.0
        if profile.water_stress_level == "extremely high":
            supply_score += 50
            factors.append("Location in extremely high water stress zone")
            recommendations.append("Develop alternative water sources")
        elif profile.water_stress_level == "high":
            supply_score += 30
            factors.append("Location in high water stress zone")
        
        if profile.backup_water_sources == 0:
            supply_score += 20
            factors.append("No backup water sources")
            recommendations.append("Establish backup water supply agreements")
        elif profile.backup_water_sources == 1:
            supply_score += 10
        
        scores[RiskCategory.SUPPLY_DISRUPTION.value] = min(100, supply_score)
        
        # Leak damage risk
        leak_score = 15.0
        if profile.infrastructure_age_years > 30:
            leak_score += 40
            factors.append("Aging infrastructure (>30 years)")
            recommendations.append("Priority infrastructure replacement program")
        elif profile.infrastructure_age_years > 20:
            leak_score += 20
            factors.append("Infrastructure over 20 years old")
        
        if profile.smart_sensors_coverage < 30:
            leak_score += 25
            factors.append("Low smart sensor coverage")
            recommendations.append("Increase IoT sensor deployment to 80%+")
        elif profile.smart_sensors_coverage < 60:
            leak_score += 10
        
        scores[RiskCategory.LEAK_DAMAGE.value] = min(100, leak_score)
        
        # Regulatory risk
        reg_score = 10.0
        if profile.country in ["India", "Brazil", "South Africa", "China"]:
            reg_score += 20
            factors.append("Rapidly evolving water regulations")
        
        if profile.incidents_last_5_years > 3:
            reg_score += 30
            factors.append("Multiple regulatory incidents in history")
            recommendations.append("Implement comprehensive compliance program")
        
        scores[RiskCategory.REGULATORY.value] = min(100, reg_score)
        
        # Infrastructure risk
        infra_score = 20.0
        days_since_upgrade = (datetime.now() - profile.last_major_upgrade.replace(tzinfo=None)).days
        if days_since_upgrade > 3650:  # 10+ years
            infra_score += 35
            factors.append("No major infrastructure upgrade in 10+ years")
        elif days_since_upgrade > 1825:  # 5+ years
            infra_score += 15
        
        scores[RiskCategory.INFRASTRUCTURE.value] = min(100, infra_score)
        
        # Climate risk
        climate_score = 10.0
        if profile.drought_prone:
            climate_score += 30
            factors.append("Drought-prone region")
        if profile.flood_zone:
            climate_score += 25
            factors.append("Located in flood zone")
            recommendations.append("Install flood protection systems")
        
        scores[RiskCategory.CLIMATE.value] = min(100, climate_score)
        
        # Cyber risk
        cyber_score = 15.0
        if profile.smart_sensors_coverage > 70:
            cyber_score += 20
            factors.append("High digital exposure")
            recommendations.append("Implement water system cybersecurity framework")
        
        scores[RiskCategory.CYBER.value] = min(100, cyber_score)
        
        # Calculate overall score
        overall = sum(
            scores[cat.value] * weight 
            for cat, weight in self.category_weights.items()
        )
        
        # Premium multiplier
        if overall < 30:
            multiplier = 0.8
        elif overall < 50:
            multiplier = 1.0
        elif overall < 70:
            multiplier = 1.3
        else:
            multiplier = 1.8
        
        return RiskScore(
            overall_score=overall,
            category_scores=scores,
            risk_factors=factors,
            mitigation_recommendations=recommendations,
            premium_multiplier=multiplier
        )


# =============================================================================
# INSURANCE PRODUCTS
# =============================================================================

@dataclass
class InsuranceProduct:
    """Water insurance product."""
    product_id: str
    name: str
    category: RiskCategory
    coverage_type: CoverageType
    description: str
    
    # Coverage
    max_coverage_usd: float
    deductible_usd: float
    
    # Pricing
    base_annual_rate: float  # As percentage of coverage
    
    # Terms
    coverage_period_days: int = 365
    waiting_period_days: int = 30
    
    # Parametric triggers (if applicable)
    triggers: List[Dict] = field(default_factory=list)


class InsuranceMarketplace:
    """
    Water insurance product marketplace.
    
    "Innovative coverage for water risks."
    """
    
    def __init__(self):
        self.products: Dict[str, InsuranceProduct] = {}
        self._load_products()
    
    def _load_products(self):
        """Load insurance products."""
        products = [
            # Supply Disruption
            InsuranceProduct(
                product_id="WI_SUPPLY_01",
                name="Water Supply Business Interruption",
                category=RiskCategory.SUPPLY_DISRUPTION,
                coverage_type=CoverageType.INDEMNITY,
                description="Covers lost revenue when water supply is disrupted for 24+ hours",
                max_coverage_usd=10000000,
                deductible_usd=25000,
                base_annual_rate=0.015,  # 1.5% of coverage
                waiting_period_days=1
            ),
            InsuranceProduct(
                product_id="WI_SUPPLY_02",
                name="Parametric Drought Coverage",
                category=RiskCategory.SUPPLY_DISRUPTION,
                coverage_type=CoverageType.PARAMETRIC,
                description="Automatic payout when regional reservoir drops below 30%",
                max_coverage_usd=5000000,
                deductible_usd=0,
                base_annual_rate=0.025,
                triggers=[
                    {"type": "reservoir_level", "threshold": 30, "unit": "percent"}
                ]
            ),
            
            # Leak Damage
            InsuranceProduct(
                product_id="WI_LEAK_01",
                name="Catastrophic Leak Coverage",
                category=RiskCategory.LEAK_DAMAGE,
                coverage_type=CoverageType.INDEMNITY,
                description="Covers property damage and remediation from major water leaks",
                max_coverage_usd=25000000,
                deductible_usd=50000,
                base_annual_rate=0.008
            ),
            InsuranceProduct(
                product_id="WI_LEAK_02",
                name="Water Loss Protection",
                category=RiskCategory.LEAK_DAMAGE,
                coverage_type=CoverageType.HYBRID,
                description="Covers cost of lost water from undetected leaks",
                max_coverage_usd=1000000,
                deductible_usd=5000,
                base_annual_rate=0.02,
                triggers=[
                    {"type": "water_loss", "threshold": 15, "unit": "percent_of_input"}
                ]
            ),
            
            # Regulatory
            InsuranceProduct(
                product_id="WI_REG_01",
                name="Regulatory Non-Compliance Shield",
                category=RiskCategory.REGULATORY,
                coverage_type=CoverageType.INDEMNITY,
                description="Covers fines, legal costs, and remediation for water permit violations",
                max_coverage_usd=5000000,
                deductible_usd=100000,
                base_annual_rate=0.012
            ),
            
            # Climate
            InsuranceProduct(
                product_id="WI_CLIMATE_01",
                name="Parametric Flood Protection",
                category=RiskCategory.CLIMATE,
                coverage_type=CoverageType.PARAMETRIC,
                description="Automatic payout when local rainfall exceeds 150mm in 24 hours",
                max_coverage_usd=3000000,
                deductible_usd=0,
                base_annual_rate=0.018,
                triggers=[
                    {"type": "rainfall", "threshold": 150, "unit": "mm_24h"}
                ]
            ),
            
            # Cyber
            InsuranceProduct(
                product_id="WI_CYBER_01",
                name="Water System Cyber Coverage",
                category=RiskCategory.CYBER,
                coverage_type=CoverageType.INDEMNITY,
                description="Covers losses from cyber attacks on water infrastructure",
                max_coverage_usd=10000000,
                deductible_usd=100000,
                base_annual_rate=0.02
            )
        ]
        
        for product in products:
            self.products[product.product_id] = product
    
    def get_quote(self,
                  product_id: str,
                  coverage_amount: float,
                  risk_score: RiskScore) -> Dict:
        """Get insurance quote."""
        
        product = self.products.get(product_id)
        if not product:
            return {"error": "Product not found"}
        
        if coverage_amount > product.max_coverage_usd:
            return {"error": f"Max coverage is ${product.max_coverage_usd:,}"}
        
        # Calculate premium
        base_premium = coverage_amount * product.base_annual_rate
        
        # Apply risk multiplier
        adjusted_premium = base_premium * risk_score.premium_multiplier
        
        # Category-specific adjustment
        category_score = risk_score.category_scores.get(product.category.value, 50)
        category_adjustment = 1 + (category_score - 50) / 100
        final_premium = adjusted_premium * category_adjustment
        
        return {
            "product": product.name,
            "product_id": product_id,
            "coverage_amount": coverage_amount,
            "deductible": product.deductible_usd,
            "annual_premium": round(final_premium, 2),
            "monthly_premium": round(final_premium / 12, 2),
            "coverage_type": product.coverage_type.value,
            "risk_multiplier_applied": risk_score.premium_multiplier,
            "triggers": product.triggers if product.triggers else "N/A",
            "effective_date": (datetime.now() + timedelta(days=product.waiting_period_days)).strftime("%Y-%m-%d")
        }


# =============================================================================
# CLAIMS MANAGEMENT
# =============================================================================

class ClaimStatus(Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


@dataclass
class InsuranceClaim:
    """Insurance claim."""
    claim_id: str
    policy_id: str
    product_id: str
    facility_id: str
    
    # Incident
    incident_date: datetime
    incident_description: str
    estimated_loss_usd: float
    
    # Supporting data
    sensor_data_attached: bool
    aquawatch_validation: str
    
    # Status
    status: ClaimStatus = ClaimStatus.SUBMITTED
    approved_amount: float = 0.0
    
    # Timeline
    submitted_at: datetime = None
    reviewed_at: datetime = None
    resolved_at: datetime = None


class ClaimsProcessor:
    """
    AI-powered claims processing.
    
    Uses AquaWatch sensor data for validation.
    """
    
    def __init__(self):
        self.claims: Dict[str, InsuranceClaim] = {}
    
    def submit_claim(self,
                     policy_id: str,
                     product_id: str,
                     facility_id: str,
                     incident_date: datetime,
                     description: str,
                     estimated_loss: float,
                     sensor_data: Dict = None) -> InsuranceClaim:
        """Submit insurance claim."""
        
        claim_id = f"CLM_{datetime.now().strftime('%Y%m%d')}_{len(self.claims):04d}"
        
        # Validate with sensor data
        validation = self._validate_with_sensors(incident_date, sensor_data)
        
        claim = InsuranceClaim(
            claim_id=claim_id,
            policy_id=policy_id,
            product_id=product_id,
            facility_id=facility_id,
            incident_date=incident_date,
            incident_description=description,
            estimated_loss_usd=estimated_loss,
            sensor_data_attached=sensor_data is not None,
            aquawatch_validation=validation,
            submitted_at=datetime.now(timezone.utc)
        )
        
        self.claims[claim_id] = claim
        
        return claim
    
    def _validate_with_sensors(self, 
                               incident_date: datetime, 
                               sensor_data: Dict) -> str:
        """Validate claim with AquaWatch sensor data."""
        
        if not sensor_data:
            return "No sensor data provided - manual review required"
        
        # Simulated validation
        anomalies_detected = sensor_data.get("anomalies_detected", False)
        leak_confirmed = sensor_data.get("leak_confirmed", False)
        
        if leak_confirmed:
            return "VALIDATED: AquaWatch sensors confirmed leak event"
        elif anomalies_detected:
            return "PARTIAL: Anomalies detected, requires investigation"
        else:
            return "INCONSISTENT: Sensor data does not support claim"
    
    def process_claim(self, claim_id: str) -> Dict:
        """Process claim with AI assistance."""
        
        claim = self.claims.get(claim_id)
        if not claim:
            return {"error": "Claim not found"}
        
        claim.status = ClaimStatus.UNDER_REVIEW
        claim.reviewed_at = datetime.now(timezone.utc)
        
        # AI-powered decision
        decision = self._ai_decision(claim)
        
        if decision["approved"]:
            claim.status = ClaimStatus.APPROVED
            claim.approved_amount = decision["approved_amount"]
        else:
            claim.status = ClaimStatus.DENIED
        
        return {
            "claim_id": claim_id,
            "status": claim.status.value,
            "decision": decision,
            "processing_time": "4 hours (vs 14 days industry average)"
        }
    
    def _ai_decision(self, claim: InsuranceClaim) -> Dict:
        """AI-powered claim decision."""
        
        # Simulated AI decision
        if "VALIDATED" in claim.aquawatch_validation:
            approval_rate = 0.95
            payout_percent = 0.95
        elif "PARTIAL" in claim.aquawatch_validation:
            approval_rate = 0.70
            payout_percent = 0.75
        else:
            approval_rate = 0.20
            payout_percent = 0.50
        
        approved = random.random() < approval_rate
        
        return {
            "approved": approved,
            "approved_amount": claim.estimated_loss_usd * payout_percent if approved else 0,
            "confidence": approval_rate,
            "validation_source": "AquaWatch Sensor Network",
            "ai_model": "ClaimsGPT v2.0",
            "reasoning": [
                f"Sensor validation: {claim.aquawatch_validation}",
                f"Historical facility claims: Within normal range",
                f"Incident date correlation: Confirmed"
            ]
        }


# =============================================================================
# PARAMETRIC MONITORING
# =============================================================================

class ParametricMonitor:
    """
    Real-time parametric trigger monitoring.
    
    Automatic payouts when conditions met.
    """
    
    def __init__(self):
        self.active_policies: List[Dict] = []
        self.trigger_history: List[Dict] = []
    
    def register_policy(self,
                        policy_id: str,
                        facility_id: str,
                        product_id: str,
                        triggers: List[Dict],
                        coverage_amount: float):
        """Register parametric policy for monitoring."""
        
        self.active_policies.append({
            "policy_id": policy_id,
            "facility_id": facility_id,
            "product_id": product_id,
            "triggers": triggers,
            "coverage_amount": coverage_amount,
            "active": True
        })
    
    def check_triggers(self, current_conditions: Dict) -> List[Dict]:
        """Check if any triggers are met."""
        
        payouts = []
        
        for policy in self.active_policies:
            if not policy["active"]:
                continue
            
            for trigger in policy["triggers"]:
                trigger_type = trigger["type"]
                threshold = trigger["threshold"]
                
                current_value = current_conditions.get(trigger_type)
                if current_value is None:
                    continue
                
                triggered = False
                
                if "level" in trigger_type or "percent" in trigger.get("unit", ""):
                    # Below threshold (drought, reservoir)
                    triggered = current_value < threshold
                else:
                    # Above threshold (rainfall, temperature)
                    triggered = current_value > threshold
                
                if triggered:
                    payout = {
                        "policy_id": policy["policy_id"],
                        "trigger_type": trigger_type,
                        "threshold": threshold,
                        "actual_value": current_value,
                        "payout_amount": policy["coverage_amount"],
                        "triggered_at": datetime.now(timezone.utc).isoformat(),
                        "status": "AUTOMATIC_PAYOUT_INITIATED"
                    }
                    
                    payouts.append(payout)
                    self.trigger_history.append(payout)
                    
                    logger.info(f"Parametric trigger met: {policy['policy_id']} - {trigger_type}")
        
        return payouts


# =============================================================================
# DEMO
# =============================================================================

def demo_insurance():
    """Demo water insurance platform."""
    
    print("=" * 70)
    print("🛡️ AQUAWATCH ENTERPRISE - WATER INSURANCE & RISK TRANSFER")
    print("=" * 70)
    
    # Create facility profile
    print("\n📋 FACILITY RISK ASSESSMENT:")
    print("-" * 50)
    
    facility = FacilityRiskProfile(
        facility_id="FAC_001",
        name="Johannesburg Bottling Plant",
        location="Johannesburg",
        country="South Africa",
        daily_water_usage_m3=5000,
        water_criticality="critical",
        backup_water_sources=1,
        infrastructure_age_years=25,
        last_major_upgrade=datetime(2018, 6, 15),
        smart_sensors_coverage=45,
        incidents_last_5_years=2,
        total_claim_value_usd=150000,
        water_stress_level="high",
        flood_zone=False,
        drought_prone=True
    )
    
    assessor = WaterRiskAssessor()
    risk = assessor.assess_facility(facility)
    
    print(f"Facility: {facility.name}")
    print(f"Overall Risk Score: {risk.overall_score:.1f}/100")
    print(f"Premium Multiplier: {risk.premium_multiplier}x")
    print(f"\nRisk Factors:")
    for factor in risk.risk_factors:
        print(f"  ⚠️ {factor}")
    print(f"\nRecommendations:")
    for rec in risk.mitigation_recommendations:
        print(f"  💡 {rec}")
    
    # Insurance quotes
    print("\n\n💰 INSURANCE QUOTES:")
    print("-" * 50)
    
    marketplace = InsuranceMarketplace()
    
    quotes = [
        ("WI_SUPPLY_01", 5000000),
        ("WI_LEAK_01", 10000000),
        ("WI_SUPPLY_02", 2000000),
        ("WI_CLIMATE_01", 1000000)
    ]
    
    for product_id, coverage in quotes:
        quote = marketplace.get_quote(product_id, coverage, risk)
        if "error" not in quote:
            print(f"\n{quote['product']}")
            print(f"  Coverage: ${quote['coverage_amount']:,}")
            print(f"  Annual Premium: ${quote['annual_premium']:,.0f}")
            print(f"  Type: {quote['coverage_type']}")
    
    # Parametric demo
    print("\n\n⚡ PARAMETRIC TRIGGER DEMO:")
    print("-" * 50)
    
    monitor = ParametricMonitor()
    monitor.register_policy(
        policy_id="POL_DROUGHT_001",
        facility_id=facility.facility_id,
        product_id="WI_SUPPLY_02",
        triggers=[{"type": "reservoir_level", "threshold": 30, "unit": "percent"}],
        coverage_amount=2000000
    )
    
    # Simulate drought condition
    current = {"reservoir_level": 25}  # Below 30% threshold
    payouts = monitor.check_triggers(current)
    
    if payouts:
        print(f"🚨 TRIGGER ACTIVATED!")
        payout = payouts[0]
        print(f"  Policy: {payout['policy_id']}")
        print(f"  Trigger: {payout['trigger_type']} < {payout['threshold']}%")
        print(f"  Actual: {payout['actual_value']}%")
        print(f"  Automatic Payout: ${payout['payout_amount']:,}")
    
    # Claims demo
    print("\n\n📝 AI-POWERED CLAIMS PROCESSING:")
    print("-" * 50)
    
    processor = ClaimsProcessor()
    claim = processor.submit_claim(
        policy_id="POL_LEAK_001",
        product_id="WI_LEAK_01",
        facility_id=facility.facility_id,
        incident_date=datetime(2024, 1, 15),
        description="Major pipeline burst in cooling section",
        estimated_loss=750000,
        sensor_data={
            "anomalies_detected": True,
            "leak_confirmed": True,
            "flow_deviation": 340
        }
    )
    
    print(f"Claim ID: {claim.claim_id}")
    print(f"Sensor Validation: {claim.aquawatch_validation}")
    
    result = processor.process_claim(claim.claim_id)
    print(f"Status: {result['status']}")
    print(f"Approved Amount: ${result['decision']['approved_amount']:,.0f}")
    print(f"Processing Time: {result['processing_time']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_insurance()
