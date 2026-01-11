"""
AquaWatch NRW - Financial & Billing Integration
===============================================

Revenue tracking, loss calculation, and billing system integration.

Features:
- NRW financial impact calculation
- Revenue recovery tracking
- ROI analysis for interventions
- Billing system integration hooks
- Cost-benefit analysis
- Financial reporting for utilities

Currency support: ZMW (Zambia), ZAR (South Africa), USD
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Water tariffs (USD per m³) - simplified
WATER_TARIFFS = {
    "zambia": {
        "domestic": 0.45,
        "commercial": 0.85,
        "industrial": 1.20,
        "government": 0.65,
        "average": 0.55
    },
    "south_africa": {
        "domestic": 0.75,
        "commercial": 1.50,
        "industrial": 2.00,
        "government": 1.00,
        "average": 0.95
    }
}

# Production costs (USD per m³)
PRODUCTION_COSTS = {
    "zambia": {
        "raw_water": 0.05,
        "treatment": 0.12,
        "pumping": 0.08,
        "distribution": 0.05,
        "total": 0.30
    },
    "south_africa": {
        "raw_water": 0.10,
        "treatment": 0.20,
        "pumping": 0.12,
        "distribution": 0.08,
        "total": 0.50
    }
}

# Exchange rates (to USD)
EXCHANGE_RATES = {
    "ZMW": 0.04,   # Zambian Kwacha
    "ZAR": 0.055,  # South African Rand
    "USD": 1.0
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class CustomerCategory(Enum):
    DOMESTIC = "domestic"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    GOVERNMENT = "government"
    INSTITUTIONAL = "institutional"


class LossType(Enum):
    REAL_LOSS = "real_loss"           # Physical leakage
    APPARENT_LOSS = "apparent_loss"   # Metering/billing errors
    UNBILLED = "unbilled"             # Authorized unbilled


@dataclass
class WaterBalance:
    """IWA Standard Water Balance."""
    period_start: datetime
    period_end: datetime
    zone_id: str
    
    # System Input Volume (m³)
    system_input_volume: float = 0.0
    
    # Authorized Consumption (m³)
    billed_metered: float = 0.0
    billed_unmetered: float = 0.0
    unbilled_metered: float = 0.0
    unbilled_unmetered: float = 0.0
    
    # Water Losses (m³)
    apparent_losses_metering: float = 0.0
    apparent_losses_unauthorized: float = 0.0
    real_losses_mains: float = 0.0
    real_losses_service: float = 0.0
    real_losses_reservoirs: float = 0.0
    
    @property
    def authorized_consumption(self) -> float:
        return (self.billed_metered + self.billed_unmetered + 
                self.unbilled_metered + self.unbilled_unmetered)
    
    @property
    def revenue_water(self) -> float:
        return self.billed_metered + self.billed_unmetered
    
    @property
    def non_revenue_water(self) -> float:
        return self.system_input_volume - self.revenue_water
    
    @property
    def nrw_percent(self) -> float:
        if self.system_input_volume > 0:
            return (self.non_revenue_water / self.system_input_volume) * 100
        return 0.0
    
    @property
    def apparent_losses(self) -> float:
        return self.apparent_losses_metering + self.apparent_losses_unauthorized
    
    @property
    def real_losses(self) -> float:
        return self.real_losses_mains + self.real_losses_service + self.real_losses_reservoirs
    
    @property
    def total_losses(self) -> float:
        return self.apparent_losses + self.real_losses


@dataclass
class FinancialImpact:
    """Financial impact of water losses."""
    period: str
    zone_id: str
    currency: str = "USD"
    
    # Volume losses (m³)
    real_losses_m3: float = 0.0
    apparent_losses_m3: float = 0.0
    unbilled_m3: float = 0.0
    
    # Revenue impact
    lost_revenue: float = 0.0           # From apparent losses
    production_cost_wasted: float = 0.0  # From real losses
    total_financial_loss: float = 0.0
    
    # Potential recovery
    recoverable_revenue: float = 0.0
    reduction_target_percent: float = 0.0
    annual_recovery_potential: float = 0.0


@dataclass
class Intervention:
    """NRW reduction intervention with cost-benefit."""
    intervention_id: str
    name: str
    zone_id: str
    intervention_type: str  # leak_repair, meter_replacement, pressure_management, etc.
    
    # Costs
    capital_cost: float = 0.0
    annual_operating_cost: float = 0.0
    
    # Benefits (annual)
    water_saved_m3_year: float = 0.0
    revenue_recovered_year: float = 0.0
    production_cost_saved_year: float = 0.0
    
    # Timeline
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    expected_lifespan_years: int = 10
    
    # Status
    status: str = "planned"  # planned, in_progress, completed, cancelled
    
    @property
    def annual_benefit(self) -> float:
        return self.revenue_recovered_year + self.production_cost_saved_year
    
    @property
    def net_annual_benefit(self) -> float:
        return self.annual_benefit - self.annual_operating_cost
    
    @property
    def simple_payback_years(self) -> float:
        if self.net_annual_benefit > 0:
            return self.capital_cost / self.net_annual_benefit
        return float('inf')
    
    @property
    def npv(self, discount_rate: float = 0.1) -> float:
        """Calculate Net Present Value."""
        npv = -self.capital_cost
        for year in range(1, self.expected_lifespan_years + 1):
            npv += self.net_annual_benefit / ((1 + discount_rate) ** year)
        return round(npv, 2)
    
    @property
    def roi_percent(self) -> float:
        if self.capital_cost > 0:
            total_benefit = self.net_annual_benefit * self.expected_lifespan_years
            return ((total_benefit - self.capital_cost) / self.capital_cost) * 100
        return 0.0


@dataclass
class CustomerAccount:
    """Customer billing account."""
    account_id: str
    customer_name: str
    category: CustomerCategory
    zone_id: str
    meter_id: str
    
    # Billing
    tariff_rate: float = 0.0  # Per m³
    monthly_consumption_m3: float = 0.0
    last_reading: float = 0.0
    last_reading_date: Optional[datetime] = None
    
    # Status
    active: bool = True
    arrears: float = 0.0


# =============================================================================
# FINANCIAL SERVICE
# =============================================================================

class FinancialService:
    """
    Financial management for water utilities.
    
    Features:
    - NRW cost calculation
    - Revenue tracking
    - Intervention ROI analysis
    - Billing integration
    - Financial reporting
    """
    
    def __init__(self, country: str = "zambia", currency: str = "USD"):
        self.country = country.lower()
        self.currency = currency
        
        # Get country-specific rates
        self.tariffs = WATER_TARIFFS.get(self.country, WATER_TARIFFS["zambia"])
        self.production_costs = PRODUCTION_COSTS.get(self.country, PRODUCTION_COSTS["zambia"])
        
        # Data stores
        self.water_balances: Dict[str, WaterBalance] = {}
        self.interventions: Dict[str, Intervention] = {}
        self.customers: Dict[str, CustomerAccount] = {}
        
        # Stats
        self.stats = {
            "total_revenue_loss": 0.0,
            "total_water_saved_m3": 0.0,
            "total_revenue_recovered": 0.0,
            "interventions_completed": 0
        }
        
        logger.info(f"FinancialService initialized for {country}")
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert between currencies."""
        if from_currency == to_currency:
            return amount
        
        # Convert to USD first
        usd_amount = amount * EXCHANGE_RATES.get(from_currency, 1.0)
        # Then to target
        return usd_amount / EXCHANGE_RATES.get(to_currency, 1.0)
    
    # =========================================================================
    # WATER BALANCE & NRW
    # =========================================================================
    
    def create_water_balance(
        self,
        zone_id: str,
        period_start: datetime,
        period_end: datetime,
        system_input: float,
        billed_metered: float,
        billed_unmetered: float = 0,
        unbilled_metered: float = 0,
        unbilled_unmetered: float = 0
    ) -> WaterBalance:
        """Create a water balance record."""
        balance = WaterBalance(
            period_start=period_start,
            period_end=period_end,
            zone_id=zone_id,
            system_input_volume=system_input,
            billed_metered=billed_metered,
            billed_unmetered=billed_unmetered,
            unbilled_metered=unbilled_metered,
            unbilled_unmetered=unbilled_unmetered
        )
        
        # Estimate losses (simplified - in practice, would need more data)
        total_losses = system_input - balance.authorized_consumption
        
        # Typical split: 60% real losses, 40% apparent losses
        balance.real_losses_mains = total_losses * 0.4
        balance.real_losses_service = total_losses * 0.15
        balance.real_losses_reservoirs = total_losses * 0.05
        balance.apparent_losses_metering = total_losses * 0.25
        balance.apparent_losses_unauthorized = total_losses * 0.15
        
        key = f"{zone_id}_{period_start.strftime('%Y%m')}"
        self.water_balances[key] = balance
        
        return balance
    
    def calculate_financial_impact(
        self, 
        water_balance: WaterBalance,
        tariff_rate: float = None,
        production_cost: float = None
    ) -> FinancialImpact:
        """Calculate financial impact of NRW."""
        if tariff_rate is None:
            tariff_rate = self.tariffs["average"]
        if production_cost is None:
            production_cost = self.production_costs["total"]
        
        # Calculate losses in financial terms
        real_losses = water_balance.real_losses
        apparent_losses = water_balance.apparent_losses
        unbilled = water_balance.unbilled_metered + water_balance.unbilled_unmetered
        
        # Lost revenue (from apparent losses - water was consumed but not billed)
        lost_revenue = apparent_losses * tariff_rate
        
        # Production cost wasted (from real losses - water was produced but lost)
        production_wasted = real_losses * production_cost
        
        # Total financial loss
        total_loss = lost_revenue + production_wasted
        
        # Recovery potential (assuming 50% reduction target)
        reduction_target = 0.5
        recoverable = total_loss * reduction_target
        
        # Annualize
        days_in_period = (water_balance.period_end - water_balance.period_start).days
        annual_factor = 365 / days_in_period if days_in_period > 0 else 12
        
        impact = FinancialImpact(
            period=f"{water_balance.period_start.strftime('%Y-%m')}",
            zone_id=water_balance.zone_id,
            currency=self.currency,
            real_losses_m3=real_losses,
            apparent_losses_m3=apparent_losses,
            unbilled_m3=unbilled,
            lost_revenue=round(lost_revenue, 2),
            production_cost_wasted=round(production_wasted, 2),
            total_financial_loss=round(total_loss, 2),
            recoverable_revenue=round(recoverable, 2),
            reduction_target_percent=reduction_target * 100,
            annual_recovery_potential=round(recoverable * annual_factor, 2)
        )
        
        self.stats["total_revenue_loss"] += total_loss
        
        return impact
    
    def get_nrw_cost_per_day(self, zone_id: str) -> Dict:
        """Get daily NRW cost for a zone."""
        # Find most recent water balance
        recent_balance = None
        for key, balance in self.water_balances.items():
            if balance.zone_id == zone_id:
                if recent_balance is None or balance.period_end > recent_balance.period_end:
                    recent_balance = balance
        
        if not recent_balance:
            return {"error": "No water balance data"}
        
        impact = self.calculate_financial_impact(recent_balance)
        
        days = (recent_balance.period_end - recent_balance.period_start).days
        if days <= 0:
            days = 30
        
        return {
            "zone_id": zone_id,
            "nrw_percent": round(recent_balance.nrw_percent, 1),
            "daily_water_loss_m3": round(recent_balance.non_revenue_water / days, 1),
            "daily_financial_loss": round(impact.total_financial_loss / days, 2),
            "daily_lost_revenue": round(impact.lost_revenue / days, 2),
            "daily_production_waste": round(impact.production_cost_wasted / days, 2),
            "currency": self.currency,
            "period": impact.period
        }
    
    # =========================================================================
    # INTERVENTION ROI
    # =========================================================================
    
    def add_intervention(self, intervention: Intervention):
        """Add an intervention."""
        self.interventions[intervention.intervention_id] = intervention
        logger.info(f"Added intervention: {intervention.name}")
    
    def evaluate_intervention(
        self,
        name: str,
        zone_id: str,
        intervention_type: str,
        capital_cost: float,
        water_saved_m3_year: float,
        annual_operating_cost: float = 0,
        lifespan_years: int = 10,
        tariff_rate: float = None,
        production_cost: float = None
    ) -> Intervention:
        """Evaluate a potential intervention."""
        if tariff_rate is None:
            tariff_rate = self.tariffs["average"]
        if production_cost is None:
            production_cost = self.production_costs["total"]
        
        # Calculate annual benefits
        # Revenue recovered (from fixing apparent losses)
        revenue_recovered = water_saved_m3_year * tariff_rate * 0.4  # Assume 40% from apparent
        # Production cost saved (from fixing real losses)
        production_saved = water_saved_m3_year * production_cost * 0.6  # Assume 60% from real
        
        intervention = Intervention(
            intervention_id=f"INT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=name,
            zone_id=zone_id,
            intervention_type=intervention_type,
            capital_cost=capital_cost,
            annual_operating_cost=annual_operating_cost,
            water_saved_m3_year=water_saved_m3_year,
            revenue_recovered_year=round(revenue_recovered, 2),
            production_cost_saved_year=round(production_saved, 2),
            expected_lifespan_years=lifespan_years
        )
        
        return intervention
    
    def compare_interventions(self, interventions: List[Intervention]) -> List[Dict]:
        """Compare multiple interventions by ROI."""
        comparison = []
        
        for inv in interventions:
            comparison.append({
                "name": inv.name,
                "capital_cost": inv.capital_cost,
                "annual_benefit": inv.annual_benefit,
                "net_annual_benefit": inv.net_annual_benefit,
                "payback_years": round(inv.simple_payback_years, 1),
                "roi_percent": round(inv.roi_percent, 1),
                "water_saved_m3_year": inv.water_saved_m3_year,
                "priority_score": self._calculate_priority_score(inv)
            })
        
        # Sort by priority score
        comparison.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return comparison
    
    def _calculate_priority_score(self, intervention: Intervention) -> float:
        """Calculate priority score for intervention ranking."""
        # Weighted scoring
        roi_score = min(intervention.roi_percent / 100, 2) * 30  # Max 60 points
        payback_score = max(0, (5 - intervention.simple_payback_years) / 5) * 30  # Max 30 points
        water_score = min(intervention.water_saved_m3_year / 10000, 1) * 20  # Max 20 points
        cost_score = max(0, (100000 - intervention.capital_cost) / 100000) * 20  # Max 20 points (lower cost = higher score)
        
        return round(roi_score + payback_score + water_score + cost_score, 1)
    
    def record_completed_intervention(
        self,
        intervention_id: str,
        actual_water_saved_m3: float
    ):
        """Record completion of an intervention."""
        if intervention_id not in self.interventions:
            return
        
        inv = self.interventions[intervention_id]
        inv.status = "completed"
        inv.completion_date = datetime.now(timezone.utc)
        
        self.stats["interventions_completed"] += 1
        self.stats["total_water_saved_m3"] += actual_water_saved_m3
        self.stats["total_revenue_recovered"] += actual_water_saved_m3 * self.tariffs["average"]
    
    # =========================================================================
    # CUSTOMER & BILLING
    # =========================================================================
    
    def add_customer(self, customer: CustomerAccount):
        """Add a customer account."""
        self.customers[customer.account_id] = customer
    
    def get_zone_revenue(self, zone_id: str) -> Dict:
        """Get revenue statistics for a zone."""
        zone_customers = [c for c in self.customers.values() if c.zone_id == zone_id]
        
        if not zone_customers:
            return {"error": "No customers in zone"}
        
        total_consumption = sum(c.monthly_consumption_m3 for c in zone_customers)
        total_revenue = sum(c.monthly_consumption_m3 * c.tariff_rate for c in zone_customers)
        total_arrears = sum(c.arrears for c in zone_customers)
        
        by_category = {}
        for category in CustomerCategory:
            cat_customers = [c for c in zone_customers if c.category == category]
            if cat_customers:
                by_category[category.value] = {
                    "count": len(cat_customers),
                    "consumption_m3": sum(c.monthly_consumption_m3 for c in cat_customers),
                    "revenue": sum(c.monthly_consumption_m3 * c.tariff_rate for c in cat_customers)
                }
        
        return {
            "zone_id": zone_id,
            "total_customers": len(zone_customers),
            "active_customers": len([c for c in zone_customers if c.active]),
            "monthly_consumption_m3": round(total_consumption, 1),
            "monthly_revenue": round(total_revenue, 2),
            "total_arrears": round(total_arrears, 2),
            "collection_efficiency": round((total_revenue - total_arrears) / total_revenue * 100, 1) if total_revenue > 0 else 0,
            "by_category": by_category,
            "currency": self.currency
        }
    
    def estimate_unbilled_water(self, zone_id: str, system_input_m3: float) -> Dict:
        """Estimate unbilled water in a zone."""
        zone_customers = [c for c in self.customers.values() if c.zone_id == zone_id]
        
        billed_consumption = sum(c.monthly_consumption_m3 for c in zone_customers)
        unbilled = system_input_m3 - billed_consumption
        unbilled_percent = (unbilled / system_input_m3 * 100) if system_input_m3 > 0 else 0
        
        # Estimate financial loss
        potential_revenue = unbilled * self.tariffs["average"]
        
        return {
            "zone_id": zone_id,
            "system_input_m3": system_input_m3,
            "billed_consumption_m3": round(billed_consumption, 1),
            "unbilled_water_m3": round(unbilled, 1),
            "unbilled_percent": round(unbilled_percent, 1),
            "potential_revenue_loss": round(potential_revenue, 2),
            "currency": self.currency
        }
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def generate_financial_report(self, zone_id: str = None, period: str = None) -> Dict:
        """Generate comprehensive financial report."""
        # Filter data
        balances = list(self.water_balances.values())
        if zone_id:
            balances = [b for b in balances if b.zone_id == zone_id]
        if period:
            balances = [b for b in balances if b.period_start.strftime('%Y-%m') == period]
        
        if not balances:
            return {"error": "No data available"}
        
        # Aggregate metrics
        total_input = sum(b.system_input_volume for b in balances)
        total_nrw = sum(b.non_revenue_water for b in balances)
        total_real_losses = sum(b.real_losses for b in balances)
        total_apparent_losses = sum(b.apparent_losses for b in balances)
        
        # Calculate financial impact
        total_revenue_loss = total_apparent_losses * self.tariffs["average"]
        total_production_waste = total_real_losses * self.production_costs["total"]
        total_financial_loss = total_revenue_loss + total_production_waste
        
        # Intervention ROI
        completed_interventions = [i for i in self.interventions.values() if i.status == "completed"]
        if zone_id:
            completed_interventions = [i for i in completed_interventions if i.zone_id == zone_id]
        
        total_investment = sum(i.capital_cost for i in completed_interventions)
        total_annual_savings = sum(i.net_annual_benefit for i in completed_interventions)
        
        return {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "zone_id": zone_id or "All Zones",
            "period": period or "All Time",
            "currency": self.currency,
            
            "water_balance": {
                "system_input_m3": round(total_input, 0),
                "non_revenue_water_m3": round(total_nrw, 0),
                "nrw_percent": round(total_nrw / total_input * 100, 1) if total_input > 0 else 0,
                "real_losses_m3": round(total_real_losses, 0),
                "apparent_losses_m3": round(total_apparent_losses, 0)
            },
            
            "financial_impact": {
                "lost_revenue": round(total_revenue_loss, 2),
                "production_cost_wasted": round(total_production_waste, 2),
                "total_financial_loss": round(total_financial_loss, 2),
                "daily_loss": round(total_financial_loss / 30, 2),  # Assuming monthly
                "annual_projected_loss": round(total_financial_loss * 12, 2)
            },
            
            "interventions": {
                "total_planned": len([i for i in self.interventions.values() if i.status == "planned"]),
                "total_completed": len(completed_interventions),
                "total_investment": round(total_investment, 2),
                "annual_savings": round(total_annual_savings, 2),
                "overall_roi_percent": round((total_annual_savings / total_investment - 1) * 100, 1) if total_investment > 0 else 0
            },
            
            "recommendations": self._generate_recommendations(total_nrw / total_input * 100 if total_input > 0 else 0)
        }
    
    def _generate_recommendations(self, nrw_percent: float) -> List[str]:
        """Generate recommendations based on NRW level."""
        recommendations = []
        
        if nrw_percent > 50:
            recommendations.append("CRITICAL: NRW exceeds 50%. Prioritize pressure management and active leak detection.")
            recommendations.append("Implement district metering to isolate high-loss areas.")
            recommendations.append("Consider emergency leak repair program.")
        elif nrw_percent > 35:
            recommendations.append("HIGH: NRW above IWA benchmark. Focus on systematic leak detection.")
            recommendations.append("Review meter accuracy and billing processes.")
            recommendations.append("Implement pressure management in critical zones.")
        elif nrw_percent > 20:
            recommendations.append("MODERATE: NRW above target. Continue systematic improvements.")
            recommendations.append("Focus on apparent loss reduction through meter replacement.")
            recommendations.append("Enhance customer meter reading and billing accuracy.")
        else:
            recommendations.append("GOOD: NRW within acceptable range. Focus on maintenance.")
            recommendations.append("Continue proactive pipe replacement program.")
            recommendations.append("Optimize pressure management settings.")
        
        return recommendations
    
    def export_to_csv_data(self, zone_id: str = None) -> List[Dict]:
        """Export financial data for CSV export."""
        data = []
        
        for key, balance in self.water_balances.items():
            if zone_id and balance.zone_id != zone_id:
                continue
            
            impact = self.calculate_financial_impact(balance)
            
            data.append({
                "Period": balance.period_start.strftime("%Y-%m"),
                "Zone": balance.zone_id,
                "System Input (m³)": balance.system_input_volume,
                "Revenue Water (m³)": balance.revenue_water,
                "NRW (m³)": balance.non_revenue_water,
                "NRW (%)": round(balance.nrw_percent, 1),
                "Real Losses (m³)": balance.real_losses,
                "Apparent Losses (m³)": balance.apparent_losses,
                f"Lost Revenue ({self.currency})": impact.lost_revenue,
                f"Production Waste ({self.currency})": impact.production_cost_wasted,
                f"Total Loss ({self.currency})": impact.total_financial_loss
            })
        
        return data


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize for Zambia
    service = FinancialService(country="zambia", currency="USD")
    
    # Create water balance
    balance = service.create_water_balance(
        zone_id="ZONE_KAB",
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 1, 31),
        system_input=150000,  # 150,000 m³
        billed_metered=90000,
        billed_unmetered=5000,
        unbilled_metered=2000,
        unbilled_unmetered=3000
    )
    
    print("Water Balance:")
    print(f"  System Input: {balance.system_input_volume:,.0f} m³")
    print(f"  Revenue Water: {balance.revenue_water:,.0f} m³")
    print(f"  NRW: {balance.non_revenue_water:,.0f} m³ ({balance.nrw_percent:.1f}%)")
    print(f"  Real Losses: {balance.real_losses:,.0f} m³")
    print(f"  Apparent Losses: {balance.apparent_losses:,.0f} m³")
    
    print("\n" + "="*50 + "\n")
    
    # Calculate financial impact
    impact = service.calculate_financial_impact(balance)
    print("Financial Impact:")
    print(f"  Lost Revenue: ${impact.lost_revenue:,.2f}")
    print(f"  Production Waste: ${impact.production_cost_wasted:,.2f}")
    print(f"  Total Financial Loss: ${impact.total_financial_loss:,.2f}")
    print(f"  Annual Recovery Potential: ${impact.annual_recovery_potential:,.2f}")
    
    print("\n" + "="*50 + "\n")
    
    # Daily cost
    daily = service.get_nrw_cost_per_day("ZONE_KAB")
    print("Daily NRW Cost:")
    print(json.dumps(daily, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Evaluate interventions
    interventions = [
        service.evaluate_intervention(
            name="Active Leak Detection Program",
            zone_id="ZONE_KAB",
            intervention_type="leak_detection",
            capital_cost=25000,
            water_saved_m3_year=15000,
            annual_operating_cost=5000,
            lifespan_years=5
        ),
        service.evaluate_intervention(
            name="Pressure Management - PRVs",
            zone_id="ZONE_KAB",
            intervention_type="pressure_management",
            capital_cost=45000,
            water_saved_m3_year=20000,
            annual_operating_cost=2000,
            lifespan_years=15
        ),
        service.evaluate_intervention(
            name="Meter Replacement Program",
            zone_id="ZONE_KAB",
            intervention_type="meter_replacement",
            capital_cost=60000,
            water_saved_m3_year=8000,
            annual_operating_cost=3000,
            lifespan_years=10
        )
    ]
    
    print("Intervention Comparison:")
    comparison = service.compare_interventions(interventions)
    for i, inv in enumerate(comparison, 1):
        print(f"\n  {i}. {inv['name']}")
        print(f"     Capital Cost: ${inv['capital_cost']:,.0f}")
        print(f"     Annual Benefit: ${inv['annual_benefit']:,.0f}")
        print(f"     Payback: {inv['payback_years']:.1f} years")
        print(f"     ROI: {inv['roi_percent']:.0f}%")
        print(f"     Priority Score: {inv['priority_score']:.1f}")
    
    print("\n" + "="*50 + "\n")
    
    # Generate report
    print("Financial Report:")
    report = service.generate_financial_report("ZONE_KAB")
    print(json.dumps(report, indent=2))
