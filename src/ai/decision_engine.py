"""
AquaWatch NRW - Decision Engine
================================

CRITICAL COMPONENT: Explainable DMA Priority Ranking

MOST IMPORTANT QUESTION THIS ENGINE ANSWERS:
"Where do we send field teams tomorrow morning?"

====================================================================
LOCKED DECISION FORMULA (DO NOT CHANGE):
====================================================================

Priority Score = (leak_probability × estimated_loss_m3_day)
                × criticality_factor
                × confidence_factor

====================================================================

INPUTS:
- Leak probability (0-1 from AI model)
- Estimated loss volume (m³/day)
- Pipe age
- Pipe material
- Population served
- Confidence score

OUTPUTS:
- Priority score (0-100)
- Ranked DMA list
- Human-readable explanation per DMA

NO BLACK BOX DECISIONS - Every score is traceable.

Aligned with IWA Water Balance Framework:
- Focuses on REAL LOSSES (physical leakage)
- DMA-centric analysis
- Minimum Night Flow (MNF) integration
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class InterventionType(Enum):
    """IWA-recommended intervention types."""
    ACTIVE_LEAK_DETECTION = "active_leak_detection"  # Acoustic survey, step testing
    PRESSURE_MANAGEMENT = "pressure_management"       # Reduce pressure to reduce leakage
    INFRASTRUCTURE_REPAIR = "infrastructure_repair"   # Fix identified leaks
    SPEED_OF_REPAIR = "speed_of_repair"              # Reduce repair time
    METER_REPLACEMENT = "meter_replacement"           # For apparent losses
    NO_ACTION = "no_action"                          # Monitor only


class UrgencyLevel(Enum):
    """Operational urgency levels."""
    IMMEDIATE = "immediate"     # Dispatch now (burst main)
    SAME_DAY = "same_day"       # Today's priority
    NEXT_48H = "next_48h"       # Within 2 days
    THIS_WEEK = "this_week"     # Scheduled this week
    SCHEDULED = "scheduled"     # Routine maintenance queue


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DMAPriorityScore:
    """
    Explainable priority score for a single DMA.
    
    EVERY component of the score is transparent and traceable.
    Operators can understand WHY this DMA is ranked where it is.
    """
    dma_id: str
    dma_name: str
    timestamp: datetime
    
    # The final priority score (0-100, higher = more urgent)
    priority_score: float
    rank: int  # Position in priority list (1 = highest)
    
    # LOCKED FORMULA COMPONENTS
    leak_probability: float              # 0-1 from AI model
    estimated_loss_m3_day: float         # m³/day
    criticality_factor: float            # Combined criticality (0-2)
    confidence_factor: float             # AI confidence (0-1)
    
    # Component scores (for transparency)
    leak_probability_score: float
    loss_volume_score: float
    criticality_score: float
    time_decay_score: float
    historical_confidence_score: float
    
    # Economic impact
    estimated_loss_m3_year: float
    estimated_revenue_loss_usd_year: float
    
    # DMA characteristics
    population_served: int
    pipe_length_km: float
    average_pipe_age_years: float
    historical_leak_count: int
    days_since_last_inspection: int
    
    # NRW metrics
    current_nrw_percent: float           # Current NRW %
    target_nrw_percent: float            # Target NRW %
    nrw_gap: float                       # Current - Target
    
    # MNF analysis
    mnf_excess_m3_day: float             # Night flow above expected
    mnf_deviation_percent: float         # % deviation from baseline
    
    # Recommended action
    recommended_intervention: InterventionType
    urgency: UrgencyLevel
    
    # Explanation (human-readable)
    explanation: str
    contributing_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API/JSON."""
        return {
            "dma_id": self.dma_id,
            "dma_name": self.dma_name,
            "timestamp": self.timestamp.isoformat(),
            "priority_score": round(self.priority_score, 1),
            "rank": self.rank,
            "locked_formula": {
                "leak_probability": round(self.leak_probability, 3),
                "estimated_loss_m3_day": round(self.estimated_loss_m3_day, 1),
                "criticality_factor": round(self.criticality_factor, 2),
                "confidence_factor": round(self.confidence_factor, 2),
                "formula": "Priority = (leak_prob × loss_m3_day) × criticality × confidence"
            },
            "scores": {
                "leak_probability": round(self.leak_probability_score, 1),
                "loss_volume": round(self.loss_volume_score, 1),
                "criticality": round(self.criticality_score, 1),
                "time_decay": round(self.time_decay_score, 1),
                "historical": round(self.historical_confidence_score, 1)
            },
            "raw_values": {
                "estimated_loss_m3_year": round(self.estimated_loss_m3_year, 0),
                "revenue_loss_usd_year": round(self.estimated_revenue_loss_usd_year, 0),
                "current_nrw_percent": round(self.current_nrw_percent, 1),
                "nrw_gap": round(self.nrw_gap, 1),
                "mnf_excess_m3_day": round(self.mnf_excess_m3_day, 1)
            },
            "dma_info": {
                "population_served": self.population_served,
                "pipe_length_km": round(self.pipe_length_km, 1),
                "avg_pipe_age_years": round(self.average_pipe_age_years, 1),
                "historical_leaks": self.historical_leak_count,
                "days_since_inspection": self.days_since_last_inspection
            },
            "recommendation": {
                "intervention": self.recommended_intervention.value,
                "urgency": self.urgency.value
            },
            "explanation": self.explanation,
            "contributing_factors": self.contributing_factors
        }
    
    def to_operator_report(self) -> str:
        """Generate human-readable report for operators."""
        urgency_emoji = {
            UrgencyLevel.IMMEDIATE: "🔴",
            UrgencyLevel.SAME_DAY: "🟠", 
            UrgencyLevel.NEXT_48H: "🟡",
            UrgencyLevel.THIS_WEEK: "🟢",
            UrgencyLevel.SCHEDULED: "⚪"
        }
        
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         DMA PRIORITY ASSESSMENT                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DMA: {self.dma_name:<72} ║
║  ID: {self.dma_id:<73} ║
║  Assessment Time: {self.timestamp.strftime('%Y-%m-%d %H:%M'):<60} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PRIORITY SCORE: {self.priority_score:>5.1f} / 100                RANK: #{self.rank:<3}                     ║
║  URGENCY: {urgency_emoji.get(self.urgency, '')} {self.urgency.value.upper():<67} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LOCKED FORMULA: Priority = (leak_prob × loss) × criticality × confidence    ║
║  ├─ Leak Probability:     {self.leak_probability:>5.1%}                                        ║
║  ├─ Estimated Loss:       {self.estimated_loss_m3_day:>5.0f} m³/day                                    ║
║  ├─ Criticality Factor:   {self.criticality_factor:>5.2f}                                          ║
║  └─ Confidence Factor:    {self.confidence_factor:>5.2f}                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  NRW STATUS:                                                                 ║
║  ├─ Current NRW: {self.current_nrw_percent:>5.1f}%    Target: {self.target_nrw_percent:>5.1f}%    Gap: {self.nrw_gap:>+5.1f}%               ║
║  └─ MNF Excess: {self.mnf_excess_m3_day:>6.1f} m³/day ({self.mnf_deviation_percent:>+.1f}% from baseline)             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ESTIMATED ANNUAL IMPACT:                                                    ║
║  ├─ Water Loss: {self.estimated_loss_m3_year:>10,.0f} m³/year                                       ║
║  └─ Revenue Loss: ${self.estimated_revenue_loss_usd_year:>9,.0f} USD/year                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  RECOMMENDED ACTION: {self.recommended_intervention.value.upper():<55} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  WHY THIS RANKING:                                                           ║
{''.join(f'║  • {factor:<74} ║{chr(10)}' for factor in self.contributing_factors[:5])}╚══════════════════════════════════════════════════════════════════════════════╝
"""


@dataclass
class DecisionEngineConfig:
    """Configuration for the decision engine."""
    
    # LOCKED FORMULA PARAMETERS
    # Priority = (leak_prob × loss_m3_day) × criticality × confidence
    
    # Normalization parameters for 0-100 scoring
    max_loss_m3_day: float = 500.0      # Loss volume cap for scoring
    max_population: int = 100000         # Population cap for criticality
    max_pipe_age_years: int = 50         # Pipe age cap for criticality
    max_days_since_inspection: int = 365 # Days cap for time decay
    max_historical_leaks: int = 20       # Historical leaks cap
    
    # Criticality factor weights (population, age, infrastructure)
    criticality_population_weight: float = 0.50
    criticality_pipe_age_weight: float = 0.30
    criticality_nrw_gap_weight: float = 0.20
    
    # Thresholds for urgency classification
    urgency_immediate_threshold: float = 80.0
    urgency_same_day_threshold: float = 60.0
    urgency_48h_threshold: float = 40.0
    urgency_week_threshold: float = 20.0
    
    # Economic parameters (Lusaka, Zambia context)
    water_tariff_usd_per_m3: float = 0.50  # Average water tariff
    days_per_year: int = 365


# =============================================================================
# MAIN DECISION ENGINE
# =============================================================================

class DecisionEngine:
    """
    Central Decision Engine for DMA Prioritization.
    
    ====================================================================
    LOCKED DECISION FORMULA (DO NOT CHANGE):
    ====================================================================
    
    Priority Score = (leak_probability × estimated_loss_m3_day)
                    × criticality_factor
                    × confidence_factor
    
    Normalized to 0-100 scale.
    
    ====================================================================
    
    This is NOT a black box - every score is:
    1. Composed of understandable components
    2. Traceable to raw data
    3. Explainable to operators
    
    SINGLE AUTHORITATIVE SOURCE for DMA prioritization.
    Used by: Alerts, Dashboards, Work Orders.
    """
    
    def __init__(self, config: Optional[DecisionEngineConfig] = None):
        self.config = config or DecisionEngineConfig()
        logger.info("Decision Engine initialized with LOCKED FORMULA")
        logger.info("Priority = (leak_prob × loss) × criticality × confidence")
    
    def score_dma(
        self,
        leak_prob: float,
        loss_m3_day: float,
        criticality: float,
        confidence: float
    ) -> float:
        """
        LOCKED FORMULA IMPLEMENTATION.
        
        Priority Score = (leak_probability × estimated_loss_m3_day)
                        × criticality_factor
                        × confidence_factor
        
        Args:
            leak_prob: AI leak probability (0-1)
            loss_m3_day: Estimated loss in m³/day
            criticality: Criticality factor (0-2, 1.0 = baseline)
            confidence: AI confidence (0-1)
            
        Returns:
            Priority score (0-100)
        """
        # Raw score from formula
        raw_score = leak_prob * loss_m3_day * criticality * confidence
        
        # Normalize to 0-100
        # Max theoretical: 1.0 × 500 × 2.0 × 1.0 = 1000
        max_theoretical = self.config.max_loss_m3_day * 2.0
        normalized = (raw_score / max_theoretical) * 100
        
        return min(max(normalized, 0), 100)
    
    def calculate_criticality_factor(
        self,
        population_served: int,
        avg_pipe_age_years: float,
        nrw_gap_percent: float
    ) -> float:
        """
        Calculate criticality factor (0-2, 1.0 = baseline).
        
        Higher = more critical infrastructure.
        """
        # Population factor (0-1)
        pop_factor = min(population_served / self.config.max_population, 1.0)
        
        # Pipe age factor (0-1)
        age_factor = min(avg_pipe_age_years / self.config.max_pipe_age_years, 1.0)
        
        # NRW gap factor (0-1, higher gap = more critical)
        gap_factor = min(max(nrw_gap_percent, 0) / 50.0, 1.0)  # 50% gap = max
        
        # Weighted combination
        weighted = (
            self.config.criticality_population_weight * pop_factor +
            self.config.criticality_pipe_age_weight * age_factor +
            self.config.criticality_nrw_gap_weight * gap_factor
        )
        
        # Scale to 0-2 range (1.0 = baseline)
        return 0.5 + weighted * 1.5
    
    def rank_dmas(
        self,
        dma_data: List[Dict[str, Any]],
        ai_predictions: Optional[Dict[str, float]] = None
    ) -> List[DMAPriorityScore]:
        """
        Rank all DMAs by priority using LOCKED FORMULA.
        
        Args:
            dma_data: List of DMA information dictionaries containing:
                - dma_id: str
                - dma_name: str
                - population_served: int
                - pipe_length_km: float
                - avg_pipe_age_years: float
                - historical_leak_count: int
                - days_since_inspection: int
                - current_nrw_percent: float
                - target_nrw_percent: float
                - estimated_loss_m3_day: float
                - mnf_excess_m3_day: float
                - mnf_deviation_percent: float
            
            ai_predictions: Optional dict of {dma_id: leak_probability}
            
        Returns:
            List of DMAPriorityScore sorted by priority (highest first)
        """
        scores = []
        
        for dma in dma_data:
            dma_id = dma.get('dma_id', 'unknown')
            
            # Get AI prediction if available
            leak_prob = 0.5  # Default moderate probability
            if ai_predictions and dma_id in ai_predictions:
                leak_prob = ai_predictions[dma_id]
            elif 'leak_probability' in dma:
                leak_prob = dma['leak_probability']
            
            # Calculate priority score using LOCKED FORMULA
            score = self._calculate_priority_score(dma, leak_prob)
            scores.append(score)
        
        # Sort by priority (highest first) and assign ranks
        scores.sort(key=lambda x: x.priority_score, reverse=True)
        for i, score in enumerate(scores, 1):
            score.rank = i
        
        return scores
    
    def _calculate_priority_score(
        self,
        dma: Dict[str, Any],
        leak_probability: float
    ) -> DMAPriorityScore:
        """
        Calculate comprehensive priority score for a single DMA.
        
        LOCKED FORMULA:
        Priority = (leak_prob × loss_m3_day) × criticality × confidence
        """
        # Extract DMA data with defaults
        dma_id = dma.get('dma_id', 'unknown')
        dma_name = dma.get('dma_name', f'DMA {dma_id}')
        population = dma.get('population_served', 10000)
        pipe_length = dma.get('pipe_length_km', 10.0)
        avg_pipe_age = dma.get('avg_pipe_age_years', 25.0)
        historical_leaks = dma.get('historical_leak_count', 0)
        days_since_inspection = dma.get('days_since_inspection', 90)
        current_nrw = dma.get('current_nrw_percent', 35.0)
        target_nrw = dma.get('target_nrw_percent', 20.0)
        estimated_loss = dma.get('estimated_loss_m3_day', 50.0)
        mnf_excess = dma.get('mnf_excess_m3_day', 20.0)
        mnf_deviation = dma.get('mnf_deviation_percent', 10.0)
        confidence = dma.get('confidence', 0.85)  # AI confidence
        
        nrw_gap = current_nrw - target_nrw
        
        # =================================================================
        # LOCKED FORMULA CALCULATION
        # =================================================================
        
        # 1. Leak Probability (0-1)
        leak_prob = min(max(leak_probability, 0), 1)
        
        # 2. Estimated Loss (m³/day)
        loss_m3_day = max(estimated_loss, 0)
        
        # 3. Criticality Factor (0-2)
        criticality_factor = self.calculate_criticality_factor(
            population, avg_pipe_age, nrw_gap
        )
        
        # 4. Confidence Factor (0-1)
        confidence_factor = min(max(confidence, 0), 1)
        
        # APPLY LOCKED FORMULA
        priority_score = self.score_dma(
            leak_prob, loss_m3_day, criticality_factor, confidence_factor
        )
        
        # =================================================================
        # COMPONENT SCORES FOR TRANSPARENCY
        # =================================================================
        leak_prob_score = leak_prob * 100
        loss_volume_score = min(loss_m3_day / self.config.max_loss_m3_day, 1.0) * 100
        criticality_score = (criticality_factor / 2.0) * 100
        time_decay_score = min(days_since_inspection / self.config.max_days_since_inspection, 1.0) * 100
        historical_score = min(historical_leaks / self.config.max_historical_leaks, 1.0) * 100
        
        # =================================================================
        # DETERMINE URGENCY AND INTERVENTION
        # =================================================================
        urgency = self._determine_urgency(priority_score)
        intervention = self._recommend_intervention(
            leak_probability, estimated_loss, current_nrw, target_nrw
        )
        
        # =================================================================
        # GENERATE EXPLANATION
        # =================================================================
        explanation, factors = self._generate_explanation(
            leak_probability, estimated_loss, current_nrw, target_nrw,
            mnf_deviation, days_since_inspection, historical_leaks,
            population, criticality_factor, confidence_factor
        )
        
        # =================================================================
        # ECONOMIC IMPACT
        # =================================================================
        annual_loss_m3 = estimated_loss * self.config.days_per_year
        annual_revenue_loss = annual_loss_m3 * self.config.water_tariff_usd_per_m3
        
        return DMAPriorityScore(
            dma_id=dma_id,
            dma_name=dma_name,
            timestamp=datetime.utcnow(),
            priority_score=priority_score,
            rank=0,  # Will be assigned after sorting
            
            # LOCKED FORMULA COMPONENTS
            leak_probability=leak_prob,
            estimated_loss_m3_day=loss_m3_day,
            criticality_factor=criticality_factor,
            confidence_factor=confidence_factor,
            
            # Component scores
            leak_probability_score=leak_prob_score,
            loss_volume_score=loss_volume_score,
            criticality_score=criticality_score,
            time_decay_score=time_decay_score,
            historical_confidence_score=historical_score,
            
            # Economic impact
            estimated_loss_m3_year=annual_loss_m3,
            estimated_revenue_loss_usd_year=annual_revenue_loss,
            
            # DMA characteristics
            population_served=population,
            pipe_length_km=pipe_length,
            average_pipe_age_years=avg_pipe_age,
            historical_leak_count=historical_leaks,
            days_since_last_inspection=days_since_inspection,
            
            # NRW metrics
            current_nrw_percent=current_nrw,
            target_nrw_percent=target_nrw,
            nrw_gap=nrw_gap,
            
            # MNF
            mnf_excess_m3_day=mnf_excess,
            mnf_deviation_percent=mnf_deviation,
            
            # Recommendations
            recommended_intervention=intervention,
            urgency=urgency,
            
            # Explanation
            explanation=explanation,
            contributing_factors=factors
        )
    
    def _determine_urgency(self, priority_score: float) -> UrgencyLevel:
        """Determine urgency level from priority score."""
        if priority_score >= self.config.urgency_immediate_threshold:
            return UrgencyLevel.IMMEDIATE
        elif priority_score >= self.config.urgency_same_day_threshold:
            return UrgencyLevel.SAME_DAY
        elif priority_score >= self.config.urgency_48h_threshold:
            return UrgencyLevel.NEXT_48H
        elif priority_score >= self.config.urgency_week_threshold:
            return UrgencyLevel.THIS_WEEK
        else:
            return UrgencyLevel.SCHEDULED
    
    def _recommend_intervention(
        self,
        leak_prob: float,
        loss_m3_day: float,
        current_nrw: float,
        target_nrw: float
    ) -> InterventionType:
        """Recommend appropriate intervention based on conditions."""
        
        # High probability, high loss = immediate repair
        if leak_prob > 0.8 and loss_m3_day > 100:
            return InterventionType.INFRASTRUCTURE_REPAIR
        
        # High probability, moderate loss = active detection first
        if leak_prob > 0.6:
            return InterventionType.ACTIVE_LEAK_DETECTION
        
        # Moderate probability with NRW gap = pressure management
        nrw_gap = current_nrw - target_nrw
        if nrw_gap > 15 and leak_prob > 0.4:
            return InterventionType.PRESSURE_MANAGEMENT
        
        # Low probability but high NRW = investigate apparent losses
        if leak_prob < 0.4 and nrw_gap > 20:
            return InterventionType.METER_REPLACEMENT
        
        # Default = active leak detection
        if leak_prob > 0.3:
            return InterventionType.ACTIVE_LEAK_DETECTION
        
        return InterventionType.NO_ACTION
    
    def _generate_explanation(
        self,
        leak_prob: float,
        loss_m3_day: float,
        current_nrw: float,
        target_nrw: float,
        mnf_deviation: float,
        days_since_inspection: int,
        historical_leaks: int,
        population: int,
        criticality_factor: float,
        confidence_factor: float
    ) -> Tuple[str, List[str]]:
        """Generate human-readable explanation for the priority."""
        
        factors = []
        
        # LOCKED FORMULA explanation
        factors.append(f"FORMULA: ({leak_prob:.0%} × {loss_m3_day:.0f}m³) × {criticality_factor:.2f} × {confidence_factor:.2f}")
        
        # AI probability factor
        if leak_prob > 0.7:
            factors.append(f"HIGH leak probability ({leak_prob:.0%}) from AI model")
        elif leak_prob > 0.4:
            factors.append(f"MODERATE leak probability ({leak_prob:.0%}) from AI model")
        
        # Loss volume factor
        if loss_m3_day > 100:
            factors.append(f"SIGNIFICANT estimated loss: {loss_m3_day:.0f} m³/day")
        elif loss_m3_day > 50:
            factors.append(f"Notable estimated loss: {loss_m3_day:.0f} m³/day")
        
        # NRW gap factor
        nrw_gap = current_nrw - target_nrw
        if nrw_gap > 20:
            factors.append(f"LARGE NRW gap: {current_nrw:.0f}% vs {target_nrw:.0f}% target")
        elif nrw_gap > 10:
            factors.append(f"NRW above target: {current_nrw:.0f}% vs {target_nrw:.0f}% target")
        
        # MNF factor
        if mnf_deviation > 20:
            factors.append(f"HIGH MNF deviation: +{mnf_deviation:.0f}% above baseline")
        elif mnf_deviation > 10:
            factors.append(f"Elevated MNF: +{mnf_deviation:.0f}% above baseline")
        
        # Time factor
        if days_since_inspection > 180:
            factors.append(f"OVERDUE for inspection: {days_since_inspection} days")
        elif days_since_inspection > 90:
            factors.append(f"Due for inspection: {days_since_inspection} days")
        
        # Historical factor
        if historical_leaks > 10:
            factors.append(f"HIGH leak history: {historical_leaks} previous events")
        elif historical_leaks > 5:
            factors.append(f"Notable leak history: {historical_leaks} previous events")
        
        # Population factor
        if population > 50000:
            factors.append(f"LARGE population impact: {population:,} people served")
        
        # Generate summary explanation
        if not factors:
            factors.append("Low risk indicators - routine monitoring recommended")
        
        explanation = f"This DMA ranks high because: {'; '.join(factors[:3])}"
        
        return explanation, factors
    
    def get_top_priority_dmas(
        self,
        dma_data: List[Dict[str, Any]],
        ai_predictions: Optional[Dict[str, float]] = None,
        top_n: int = 10
    ) -> List[DMAPriorityScore]:
        """Get top N priority DMAs."""
        all_ranked = self.rank_dmas(dma_data, ai_predictions)
        return all_ranked[:top_n]
    
    def generate_daily_action_plan(
        self,
        ranked_dmas: List[DMAPriorityScore],
        available_teams: int = 3
    ) -> Dict[str, Any]:
        """
        Generate actionable daily plan for field teams.
        
        Returns structured plan with team assignments.
        """
        # Filter immediate/same-day urgency
        urgent_dmas = [
            d for d in ranked_dmas 
            if d.urgency in [UrgencyLevel.IMMEDIATE, UrgencyLevel.SAME_DAY]
        ]
        
        # Assign to teams
        team_assignments = {}
        for i, dma in enumerate(urgent_dmas[:available_teams * 2]):
            team_num = (i % available_teams) + 1
            team_key = f"team_{team_num}"
            if team_key not in team_assignments:
                team_assignments[team_key] = []
            team_assignments[team_key].append({
                "dma_id": dma.dma_id,
                "dma_name": dma.dma_name,
                "priority_score": dma.priority_score,
                "urgency": dma.urgency.value,
                "intervention": dma.recommended_intervention.value,
                "estimated_loss_m3_day": dma.estimated_loss_m3_day
            })
        
        # Calculate total impact if all addressed
        total_daily_loss = sum(d.estimated_loss_m3_day for d in urgent_dmas)
        total_annual_savings = total_daily_loss * 365 * self.config.water_tariff_usd_per_m3
        
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "summary": {
                "total_urgent_dmas": len(urgent_dmas),
                "immediate_priority": len([d for d in urgent_dmas if d.urgency == UrgencyLevel.IMMEDIATE]),
                "same_day_priority": len([d for d in urgent_dmas if d.urgency == UrgencyLevel.SAME_DAY]),
                "total_loss_at_risk_m3_day": round(total_daily_loss, 0),
                "potential_annual_savings_usd": round(total_annual_savings, 0)
            },
            "team_assignments": team_assignments,
            "unassigned_urgent": [
                {"dma_id": d.dma_id, "priority_score": d.priority_score}
                for d in urgent_dmas[available_teams * 2:]
            ]
        }
    
    def compare_intervention_roi(
        self,
        dma_scores: List[DMAPriorityScore]
    ) -> List[Dict[str, Any]]:
        """
        Compare ROI of different interventions.
        
        Returns ranked list of interventions by expected water savings.
        """
        roi_analysis = []
        
        for dma in dma_scores:
            # Estimate recovery rate by intervention type
            recovery_rates = {
                InterventionType.INFRASTRUCTURE_REPAIR: 0.90,      # 90% recovery
                InterventionType.ACTIVE_LEAK_DETECTION: 0.70,     # 70% (need to find first)
                InterventionType.PRESSURE_MANAGEMENT: 0.50,        # 50% reduction
                InterventionType.SPEED_OF_REPAIR: 0.40,           # 40% through faster fixes
                InterventionType.METER_REPLACEMENT: 0.30,         # 30% (apparent only)
                InterventionType.NO_ACTION: 0.0
            }
            
            recovery_rate = recovery_rates.get(dma.recommended_intervention, 0.5)
            expected_recovery_m3_day = dma.estimated_loss_m3_day * recovery_rate
            expected_annual_savings = expected_recovery_m3_day * 365 * self.config.water_tariff_usd_per_m3
            
            roi_analysis.append({
                "dma_id": dma.dma_id,
                "dma_name": dma.dma_name,
                "intervention": dma.recommended_intervention.value,
                "current_loss_m3_day": round(dma.estimated_loss_m3_day, 1),
                "expected_recovery_m3_day": round(expected_recovery_m3_day, 1),
                "recovery_rate_percent": round(recovery_rate * 100, 0),
                "expected_annual_savings_usd": round(expected_annual_savings, 0),
                "priority_score": round(dma.priority_score, 1)
            })
        
        # Sort by expected savings
        roi_analysis.sort(key=lambda x: x['expected_annual_savings_usd'], reverse=True)
        
        return roi_analysis


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global engine instance for convenience functions
_default_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get or create the default decision engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = DecisionEngine()
    return _default_engine


def score_dma(
    leak_prob: float,
    loss_m3_day: float,
    criticality: float = 1.0,
    confidence: float = 0.8
) -> float:
    """
    Module-level convenience function for DMA scoring.
    
    Wraps DecisionEngine.score_dma() for direct import.
    
    LOCKED FORMULA:
    Priority Score = (leak_probability × estimated_loss_m3_day)
                    × criticality_factor
                    × confidence_factor
    
    Args:
        leak_prob: Leak probability (0-1)
        loss_m3_day: Estimated loss in m³/day
        criticality: Criticality factor (0-2, default 1.0)
        confidence: Confidence factor (0-1, default 0.8)
    
    Returns:
        Priority score (0-100)
    """
    return get_decision_engine().score_dma(leak_prob, loss_m3_day, criticality, confidence)


def create_sample_dma_data() -> List[Dict[str, Any]]:
    """Create sample DMA data for testing/demonstration."""
    return [
        {
            "dma_id": "DMA-LUS-001",
            "dma_name": "Kabulonga",
            "population_served": 45000,
            "pipe_length_km": 85.5,
            "avg_pipe_age_years": 32,
            "historical_leak_count": 12,
            "days_since_inspection": 145,
            "current_nrw_percent": 42.5,
            "target_nrw_percent": 20.0,
            "estimated_loss_m3_day": 185.0,
            "mnf_excess_m3_day": 75.0,
            "mnf_deviation_percent": 28.5,
            "leak_probability": 0.78
        },
        {
            "dma_id": "DMA-LUS-002", 
            "dma_name": "Chilenje",
            "population_served": 62000,
            "pipe_length_km": 120.3,
            "avg_pipe_age_years": 45,
            "historical_leak_count": 18,
            "days_since_inspection": 210,
            "current_nrw_percent": 55.2,
            "target_nrw_percent": 20.0,
            "estimated_loss_m3_day": 320.0,
            "mnf_excess_m3_day": 145.0,
            "mnf_deviation_percent": 42.0,
            "leak_probability": 0.92
        },
        {
            "dma_id": "DMA-LUS-003",
            "dma_name": "Roma",
            "population_served": 28000,
            "pipe_length_km": 45.8,
            "avg_pipe_age_years": 18,
            "historical_leak_count": 4,
            "days_since_inspection": 60,
            "current_nrw_percent": 22.0,
            "target_nrw_percent": 20.0,
            "estimated_loss_m3_day": 25.0,
            "mnf_excess_m3_day": 8.0,
            "mnf_deviation_percent": 5.0,
            "leak_probability": 0.25
        }
    ]


# =============================================================================
# MAIN EXECUTION (Demo)
# =============================================================================

if __name__ == "__main__":
    # Initialize engine
    engine = DecisionEngine()
    
    # Get sample data
    dma_data = create_sample_dma_data()
    
    # Rank DMAs
    rankings = engine.rank_dmas(dma_data)
    
    # Print reports
    print("\n" + "="*80)
    print("AQUAWATCH NRW - DMA PRIORITY RANKING")
    print("="*80)
    
    for dma in rankings:
        print(dma.to_operator_report())
    
    # Generate daily action plan
    plan = engine.generate_daily_action_plan(rankings, available_teams=2)
    print("\n" + "="*80)
    print("DAILY ACTION PLAN")
    print("="*80)
    print(json.dumps(plan, indent=2))
    
    # ROI Analysis
    roi = engine.compare_intervention_roi(rankings)
    print("\n" + "="*80)
    print("INTERVENTION ROI ANALYSIS")
    print("="*80)
    for item in roi:
        print(f"{item['dma_name']}: {item['intervention']} → ${item['expected_annual_savings_usd']:,}/year")
