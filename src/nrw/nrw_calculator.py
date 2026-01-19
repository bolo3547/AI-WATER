"""
AquaWatch NRW - NRW Calculator Service
======================================

CRITICAL EXECUTIVE KPI — NON-NEGOTIABLE FORMULA:

    NRW = System Input Volume - Billed Authorized - Unbilled Authorized
    NRW = Real Losses + Apparent Losses

This module:
1. Integrates SIV module with IWA Water Balance calculator
2. Provides DMA-level NRW attribution
3. Supports daily, monthly, annual aggregation
4. Exposes NRW calculation service and API endpoints
5. Documents all assumptions clearly

FOCUS: REAL LOSSES (physical leakage)
"""

import uuid
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NRWResult:
    """
    Complete NRW calculation result.
    
    This is the AUTHORITATIVE output for NRW metrics.
    """
    calculation_id: str
    calculation_timestamp: datetime
    
    # Scope
    dma_id: Optional[str]              # None = utility-wide
    utility_id: Optional[str]
    
    # Period
    period_start: datetime
    period_end: datetime
    period_days: int
    aggregation_level: str             # daily, monthly, annual
    
    # IWA Water Balance Components (m³)
    system_input_volume_m3: float
    billed_authorized_m3: float
    unbilled_authorized_m3: float
    water_losses_m3: float
    
    # NRW KPIs
    nrw_m3: float                       # Same as water_losses_m3
    nrw_percent: float                  # NRW / SIV × 100
    nrw_m3_per_day: float
    
    # Loss breakdown (estimated)
    real_losses_m3: float
    apparent_losses_m3: float
    real_losses_percent: float          # Real Losses / SIV × 100
    apparent_losses_percent: float
    
    # IWA Level 2 Operational Indicators
    real_losses_l_conn_day: Optional[float] = None    # L/connection/day
    real_losses_m3_km_day: Optional[float] = None     # m³/km mains/day
    
    # IWA Level 3 Advanced Indicators
    ili: Optional[float] = None                        # Infrastructure Leakage Index
    uarl_m3_year: Optional[float] = None              # Unavoidable Annual Real Losses
    carl_m3_year: Optional[float] = None              # Current Annual Real Losses
    
    # MNF Analysis
    mnf_m3_hour: Optional[float] = None
    mnf_excess_m3_day: Optional[float] = None
    
    # Data Quality
    siv_data_completeness_percent: float = 100.0
    billing_data_completeness_percent: float = 100.0
    calculation_confidence_percent: float = 100.0
    
    # Assumptions (CRITICAL for transparency)
    assumptions: Dict[str, Any] = field(default_factory=dict)
    
    # Revenue impact (optional)
    tariff_usd_per_m3: Optional[float] = None
    revenue_loss_usd: Optional[float] = None
    revenue_loss_usd_per_year: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/JSON."""
        return {
            "calculation_id": self.calculation_id,
            "calculation_timestamp": self.calculation_timestamp.isoformat(),
            "scope": {
                "dma_id": self.dma_id,
                "utility_id": self.utility_id
            },
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
                "days": self.period_days,
                "aggregation": self.aggregation_level
            },
            "iwa_water_balance_m3": {
                "system_input_volume": round(self.system_input_volume_m3, 1),
                "billed_authorized": round(self.billed_authorized_m3, 1),
                "unbilled_authorized": round(self.unbilled_authorized_m3, 1),
                "water_losses": round(self.water_losses_m3, 1)
            },
            "nrw_metrics": {
                "nrw_m3": round(self.nrw_m3, 1),
                "nrw_percent": round(self.nrw_percent, 1),
                "nrw_m3_per_day": round(self.nrw_m3_per_day, 1)
            },
            "loss_breakdown_m3": {
                "real_losses": round(self.real_losses_m3, 1),
                "apparent_losses": round(self.apparent_losses_m3, 1),
                "real_losses_percent": round(self.real_losses_percent, 1),
                "apparent_losses_percent": round(self.apparent_losses_percent, 1)
            },
            "iwa_level_2": {
                "real_losses_l_conn_day": round(self.real_losses_l_conn_day, 1) if self.real_losses_l_conn_day else None,
                "real_losses_m3_km_day": round(self.real_losses_m3_km_day, 2) if self.real_losses_m3_km_day else None
            },
            "iwa_level_3": {
                "ili": round(self.ili, 2) if self.ili else None,
                "uarl_m3_year": round(self.uarl_m3_year, 0) if self.uarl_m3_year else None,
                "carl_m3_year": round(self.carl_m3_year, 0) if self.carl_m3_year else None
            },
            "mnf_analysis": {
                "mnf_m3_hour": round(self.mnf_m3_hour, 2) if self.mnf_m3_hour else None,
                "mnf_excess_m3_day": round(self.mnf_excess_m3_day, 1) if self.mnf_excess_m3_day else None
            },
            "data_quality": {
                "siv_completeness_percent": round(self.siv_data_completeness_percent, 1),
                "billing_completeness_percent": round(self.billing_data_completeness_percent, 1),
                "calculation_confidence_percent": round(self.calculation_confidence_percent, 1)
            },
            "assumptions": self.assumptions,
            "revenue_impact": {
                "tariff_usd_per_m3": self.tariff_usd_per_m3,
                "revenue_loss_usd": round(self.revenue_loss_usd, 2) if self.revenue_loss_usd else None,
                "revenue_loss_usd_per_year": round(self.revenue_loss_usd_per_year, 0) if self.revenue_loss_usd_per_year else None
            } if self.revenue_loss_usd else None
        }
    
    def to_executive_summary(self) -> str:
        """Generate executive summary report."""
        rating = self._get_nrw_rating()
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         NRW EXECUTIVE SUMMARY                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DMA: {(self.dma_id or 'UTILITY-WIDE'):<72} ║
║  Period: {self.period_start.strftime('%Y-%m-%d')} to {self.period_end.strftime('%Y-%m-%d')} ({self.period_days} days)                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                    IWA WATER BALANCE                                    │ ║
║  ├─────────────────────────────────────────────────────────────────────────┤ ║
║  │  System Input Volume:         {self.system_input_volume_m3:>12,.0f} m³                         │ ║
║  │  ─ Billed Authorized:         {self.billed_authorized_m3:>12,.0f} m³                         │ ║
║  │  ─ Unbilled Authorized:       {self.unbilled_authorized_m3:>12,.0f} m³                         │ ║
║  │  ═══════════════════════════════════════════════════════════════════    │ ║
║  │  WATER LOSSES (NRW):          {self.nrw_m3:>12,.0f} m³  ({self.nrw_percent:>5.1f}%)          │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  NRW RATING: {rating['status']:<15}  {rating['emoji']}                                           ║
║  {rating['recommendation']:<76} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LOSS BREAKDOWN:                                                             ║
║  ├─ Real Losses (Physical):      {self.real_losses_m3:>10,.0f} m³  ({self.real_losses_percent:>5.1f}% of SIV)       ║
║  └─ Apparent Losses (Commercial):{self.apparent_losses_m3:>10,.0f} m³  ({self.apparent_losses_percent:>5.1f}% of SIV)       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DAILY IMPACT:                                                               ║
║  ├─ Water Lost:                  {self.nrw_m3_per_day:>10,.0f} m³/day                            ║
║  └─ Revenue Lost:                ${(self.revenue_loss_usd / self.period_days) if self.revenue_loss_usd else 0:>9,.0f} USD/day                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ANNUAL PROJECTION (if unchanged):                                           ║
║  ├─ Water Lost:                  {self.nrw_m3_per_day * 365:>10,.0f} m³/year                         ║
║  └─ Revenue Lost:                ${self.revenue_loss_usd_per_year or 0:>9,.0f} USD/year                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DATA QUALITY:                                                               ║
║  ├─ SIV Data Completeness:       {self.siv_data_completeness_percent:>5.1f}%                                      ║
║  ├─ Billing Data Completeness:   {self.billing_data_completeness_percent:>5.1f}%                                      ║
║  └─ Calculation Confidence:      {self.calculation_confidence_percent:>5.1f}%                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    def _get_nrw_rating(self) -> Dict[str, str]:
        """Get NRW performance rating."""
        if self.nrw_percent < 20:
            return {
                "status": "EXCELLENT",
                "emoji": "🟢",
                "recommendation": "Maintain current practices. Consider advanced optimization."
            }
        elif self.nrw_percent < 30:
            return {
                "status": "GOOD",
                "emoji": "🟡",
                "recommendation": "Target pressure management and active leak detection."
            }
        elif self.nrw_percent < 40:
            return {
                "status": "ACCEPTABLE",
                "emoji": "🟠",
                "recommendation": "Implement DMA-level leak detection program."
            }
        elif self.nrw_percent < 50:
            return {
                "status": "POOR",
                "emoji": "🔴",
                "recommendation": "URGENT: Deploy comprehensive NRW reduction strategy."
            }
        else:
            return {
                "status": "CRITICAL",
                "emoji": "⛔",
                "recommendation": "EMERGENCY: Immediate infrastructure assessment required."
            }


@dataclass 
class DMANRWSummary:
    """Summary of NRW for multiple DMAs."""
    utility_id: str
    period_start: datetime
    period_end: datetime
    calculation_timestamp: datetime
    
    # Aggregated totals
    total_siv_m3: float
    total_nrw_m3: float
    total_nrw_percent: float
    
    # Per-DMA breakdown
    dma_results: List[NRWResult]
    
    # Rankings
    worst_dma_by_volume: Optional[str] = None
    worst_dma_by_percent: Optional[str] = None
    best_dma_by_percent: Optional[str] = None


# =============================================================================
# NRW CALCULATOR SERVICE
# =============================================================================

class NRWCalculator:
    """
    Central NRW Calculation Service.
    
    This is the AUTHORITATIVE source for NRW calculations.
    All NRW metrics should come through this service.
    
    NON-NEGOTIABLE FORMULA:
        NRW = SIV - Billed - Unbilled
    
    Usage:
        calculator = NRWCalculator(siv_manager)
        
        # Calculate NRW for a DMA
        result = calculator.calculate(
            dma_id="DMA-001",
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31)
        )
        
        # Get utility-wide NRW
        result = calculator.calculate_utility_wide(utility_id, start_date, end_date)
    """
    
    def __init__(
        self,
        siv_manager=None,
        default_tariff_usd_per_m3: float = 0.50,
        default_real_loss_ratio: float = 0.75,
        default_apparent_loss_ratio: float = 0.25
    ):
        """
        Initialize NRW Calculator.
        
        Args:
            siv_manager: SIVManager instance for data access
            default_tariff_usd_per_m3: Default water tariff for revenue calculations
            default_real_loss_ratio: Default ratio of real losses (used when MNF unavailable)
            default_apparent_loss_ratio: Default ratio of apparent losses
        """
        self.siv_manager = siv_manager
        self.default_tariff = default_tariff_usd_per_m3
        self.default_real_loss_ratio = default_real_loss_ratio
        self.default_apparent_loss_ratio = default_apparent_loss_ratio
        
        # UARL coefficients (Lambert's formula)
        self.uarl_mains = 18.0        # L/km mains/day/m pressure
        self.uarl_connections = 0.80  # L/connection/day/m pressure
        self.uarl_private = 25.0      # L/km private pipe/day/m pressure
        
        # Night legitimate use (IWA default)
        self.night_use_l_conn_hour = 1.7
        
        logger.info("NRW Calculator initialized")
    
    def calculate(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        siv_m3: Optional[float] = None,
        billed_m3: Optional[float] = None,
        unbilled_m3: Optional[float] = None,
        infrastructure: Optional[Dict[str, Any]] = None,
        mnf_data: Optional[Dict[str, float]] = None,
        tariff_usd_per_m3: Optional[float] = None,
        assumptions: Optional[Dict[str, Any]] = None
    ) -> NRWResult:
        """
        Calculate NRW for a single DMA.
        
        Args:
            dma_id: DMA identifier
            start_date: Start of period
            end_date: End of period
            siv_m3: System Input Volume (if not using SIV manager)
            billed_m3: Billed authorized consumption
            unbilled_m3: Unbilled authorized consumption
            infrastructure: DMA infrastructure data (connections, pipe length, pressure)
            mnf_data: Minimum Night Flow analysis data
            tariff_usd_per_m3: Water tariff for revenue calculation
            assumptions: Dictionary of assumptions to document
            
        Returns:
            NRWResult with complete calculation
        """
        # Ensure timezone-aware dates
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        period_days = (end_date - start_date).days
        if period_days <= 0:
            period_days = 1
        
        # Build assumptions record
        calc_assumptions = assumptions.copy() if assumptions else {}
        
        # =====================================================================
        # STEP 1: Get System Input Volume
        # =====================================================================
        siv_data_completeness = 100.0
        
        if siv_m3 is not None:
            system_input_volume = siv_m3
            calc_assumptions["siv_source"] = "provided"
        elif self.siv_manager:
            siv_result = self.siv_manager.get_siv(start_date, end_date, dma_id=dma_id)
            system_input_volume = siv_result.total_siv_m3
            siv_data_completeness = siv_result.siv_data_completeness
            calc_assumptions["siv_source"] = "siv_manager"
        else:
            raise ValueError("Either siv_m3 or siv_manager must be provided")
        
        if system_input_volume <= 0:
            raise ValueError(f"Invalid SIV: {system_input_volume}. SIV must be > 0")
        
        # =====================================================================
        # STEP 2: Get Authorized Consumption
        # =====================================================================
        billing_data_completeness = 100.0
        
        if billed_m3 is not None:
            billed_authorized = billed_m3
            calc_assumptions["billed_source"] = "provided"
        elif self.siv_manager:
            billing_data = self.siv_manager.get_billing(
                dma_id, 
                start_date.date() if isinstance(start_date, datetime) else start_date,
                end_date.date() if isinstance(end_date, datetime) else end_date
            )
            billed_authorized = billing_data.get("billed_m3", {}).get("total", 0)
            calc_assumptions["billed_source"] = "siv_manager"
        else:
            billed_authorized = 0
            billing_data_completeness = 0
            calc_assumptions["billed_source"] = "not_available"
        
        if unbilled_m3 is not None:
            unbilled_authorized = unbilled_m3
            calc_assumptions["unbilled_source"] = "provided"
        elif self.siv_manager:
            billing_data = self.siv_manager.get_billing(
                dma_id,
                start_date.date() if isinstance(start_date, datetime) else start_date,
                end_date.date() if isinstance(end_date, datetime) else end_date
            )
            unbilled_authorized = billing_data.get("unbilled_m3", {}).get("total", 0)
            calc_assumptions["unbilled_source"] = "siv_manager"
        else:
            # Estimate unbilled as 3-5% of SIV (IWA typical)
            unbilled_authorized = system_input_volume * 0.04
            calc_assumptions["unbilled_source"] = "estimated_4_percent_of_siv"
            billing_data_completeness = max(billing_data_completeness - 20, 0)
        
        # =====================================================================
        # STEP 3: Calculate NRW (THE FORMULA)
        # =====================================================================
        # NRW = SIV - Billed - Unbilled
        water_losses = system_input_volume - billed_authorized - unbilled_authorized
        water_losses = max(water_losses, 0)  # Cannot be negative
        
        nrw_percent = (water_losses / system_input_volume * 100) if system_input_volume > 0 else 0
        nrw_per_day = water_losses / period_days
        
        # =====================================================================
        # STEP 4: Estimate Real vs Apparent Losses
        # =====================================================================
        if mnf_data and "mnf_excess_m3_day" in mnf_data:
            # MNF-based estimation (more accurate)
            mnf_excess_per_day = mnf_data["mnf_excess_m3_day"]
            real_losses = min(mnf_excess_per_day * period_days, water_losses)
            apparent_losses = water_losses - real_losses
            calc_assumptions["loss_split_method"] = "mnf_based"
        else:
            # Use default ratios
            real_losses = water_losses * self.default_real_loss_ratio
            apparent_losses = water_losses * self.default_apparent_loss_ratio
            calc_assumptions["loss_split_method"] = "default_ratios"
            calc_assumptions["real_loss_ratio"] = self.default_real_loss_ratio
            calc_assumptions["apparent_loss_ratio"] = self.default_apparent_loss_ratio
        
        real_losses_percent = (real_losses / system_input_volume * 100) if system_input_volume > 0 else 0
        apparent_losses_percent = (apparent_losses / system_input_volume * 100) if system_input_volume > 0 else 0
        
        # =====================================================================
        # STEP 5: Calculate IWA Level 2 & 3 Indicators (if infrastructure data available)
        # =====================================================================
        real_losses_l_conn_day = None
        real_losses_m3_km_day = None
        ili = None
        uarl_m3_year = None
        carl_m3_year = None
        
        if infrastructure:
            connections = infrastructure.get("number_of_connections", 0)
            mains_km = infrastructure.get("mains_length_km", 0)
            pressure_m = infrastructure.get("average_pressure_m", 30)  # Default 3 bar
            avg_conn_length_m = infrastructure.get("avg_connection_length_m", 15)
            
            real_losses_per_day = real_losses / period_days
            
            # Level 2: Per connection and per km
            if connections > 0:
                real_losses_l_conn_day = (real_losses_per_day * 1000) / connections
            
            if mains_km > 0:
                real_losses_m3_km_day = real_losses_per_day / mains_km
            
            # Level 3: ILI (Infrastructure Leakage Index)
            if connections > 0 and mains_km > 0 and pressure_m > 0:
                # UARL (Lambert's formula)
                private_pipe_km = connections * avg_conn_length_m / 1000
                
                uarl_l_per_day = (
                    self.uarl_mains * mains_km +
                    self.uarl_connections * connections +
                    self.uarl_private * private_pipe_km
                ) * pressure_m
                
                uarl_m3_year = uarl_l_per_day * 365 / 1000
                carl_m3_year = real_losses_per_day * 365
                
                ili = carl_m3_year / uarl_m3_year if uarl_m3_year > 0 else None
                
                calc_assumptions["uarl_coefficients"] = {
                    "mains": self.uarl_mains,
                    "connections": self.uarl_connections,
                    "private": self.uarl_private
                }
        
        # =====================================================================
        # STEP 6: Revenue Impact
        # =====================================================================
        tariff = tariff_usd_per_m3 or self.default_tariff
        revenue_loss = water_losses * tariff
        revenue_loss_per_year = nrw_per_day * 365 * tariff
        
        # =====================================================================
        # STEP 7: Calculate Confidence Score
        # =====================================================================
        confidence = min(siv_data_completeness, billing_data_completeness)
        if calc_assumptions.get("loss_split_method") == "default_ratios":
            confidence *= 0.8  # Lower confidence for estimated loss split
        if calc_assumptions.get("unbilled_source") == "estimated_4_percent_of_siv":
            confidence *= 0.9  # Lower confidence for estimated unbilled
        
        # =====================================================================
        # STEP 8: Determine Aggregation Level
        # =====================================================================
        if period_days <= 1:
            aggregation = "daily"
        elif period_days <= 31:
            aggregation = "monthly"
        else:
            aggregation = "annual" if period_days >= 365 else "custom"
        
        # =====================================================================
        # CREATE RESULT
        # =====================================================================
        result = NRWResult(
            calculation_id=f"NRW-{uuid.uuid4().hex[:12].upper()}",
            calculation_timestamp=datetime.now(timezone.utc),
            dma_id=dma_id,
            utility_id=None,
            period_start=start_date,
            period_end=end_date,
            period_days=period_days,
            aggregation_level=aggregation,
            
            # IWA Water Balance
            system_input_volume_m3=system_input_volume,
            billed_authorized_m3=billed_authorized,
            unbilled_authorized_m3=unbilled_authorized,
            water_losses_m3=water_losses,
            
            # NRW metrics
            nrw_m3=water_losses,
            nrw_percent=nrw_percent,
            nrw_m3_per_day=nrw_per_day,
            
            # Loss breakdown
            real_losses_m3=real_losses,
            apparent_losses_m3=apparent_losses,
            real_losses_percent=real_losses_percent,
            apparent_losses_percent=apparent_losses_percent,
            
            # IWA indicators
            real_losses_l_conn_day=real_losses_l_conn_day,
            real_losses_m3_km_day=real_losses_m3_km_day,
            ili=ili,
            uarl_m3_year=uarl_m3_year,
            carl_m3_year=carl_m3_year,
            
            # MNF
            mnf_m3_hour=mnf_data.get("mnf_m3_hour") if mnf_data else None,
            mnf_excess_m3_day=mnf_data.get("mnf_excess_m3_day") if mnf_data else None,
            
            # Data quality
            siv_data_completeness_percent=siv_data_completeness,
            billing_data_completeness_percent=billing_data_completeness,
            calculation_confidence_percent=confidence,
            
            # Assumptions
            assumptions=calc_assumptions,
            
            # Revenue
            tariff_usd_per_m3=tariff,
            revenue_loss_usd=revenue_loss,
            revenue_loss_usd_per_year=revenue_loss_per_year
        )
        
        logger.info(f"NRW calculated for {dma_id}: {nrw_percent:.1f}%")
        return result
    
    def calculate_utility_wide(
        self,
        utility_id: str,
        start_date: datetime,
        end_date: datetime,
        dma_ids: Optional[List[str]] = None
    ) -> DMANRWSummary:
        """
        Calculate NRW for all DMAs in a utility.
        
        Args:
            utility_id: Utility identifier
            start_date: Start of period
            end_date: End of period
            dma_ids: Specific DMAs to include (optional, defaults to all)
            
        Returns:
            DMANRWSummary with utility-wide aggregation
        """
        if not self.siv_manager:
            raise ValueError("SIV manager required for utility-wide calculation")
        
        # Get all DMAs if not specified
        if not dma_ids:
            sources = self.siv_manager.list_sources(utility_id=utility_id)
            dma_ids = list(set(
                dma_id 
                for source in sources 
                for dma_id in source.connected_dma_ids
            ))
        
        # Calculate NRW for each DMA
        dma_results = []
        for dma_id in dma_ids:
            try:
                result = self.calculate(dma_id, start_date, end_date)
                result.utility_id = utility_id
                dma_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to calculate NRW for {dma_id}: {e}")
        
        if not dma_results:
            raise ValueError("No DMA results calculated")
        
        # Aggregate totals
        total_siv = sum(r.system_input_volume_m3 for r in dma_results)
        total_nrw = sum(r.nrw_m3 for r in dma_results)
        total_nrw_percent = (total_nrw / total_siv * 100) if total_siv > 0 else 0
        
        # Find best/worst DMAs
        by_volume = sorted(dma_results, key=lambda r: r.nrw_m3, reverse=True)
        by_percent = sorted(dma_results, key=lambda r: r.nrw_percent, reverse=True)
        
        return DMANRWSummary(
            utility_id=utility_id,
            period_start=start_date,
            period_end=end_date,
            calculation_timestamp=datetime.now(timezone.utc),
            total_siv_m3=total_siv,
            total_nrw_m3=total_nrw,
            total_nrw_percent=total_nrw_percent,
            dma_results=dma_results,
            worst_dma_by_volume=by_volume[0].dma_id if by_volume else None,
            worst_dma_by_percent=by_percent[0].dma_id if by_percent else None,
            best_dma_by_percent=by_percent[-1].dma_id if by_percent else None
        )
    
    def calculate_daily(
        self,
        dma_id: str,
        date_value: date
    ) -> NRWResult:
        """Calculate NRW for a single day."""
        start = datetime.combine(date_value, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(date_value, datetime.max.time()).replace(tzinfo=timezone.utc)
        return self.calculate(dma_id, start, end)
    
    def calculate_monthly(
        self,
        dma_id: str,
        year: int,
        month: int
    ) -> NRWResult:
        """Calculate NRW for a calendar month."""
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        return self.calculate(dma_id, start, end)
    
    def calculate_annual(
        self,
        dma_id: str,
        year: int
    ) -> NRWResult:
        """Calculate NRW for a calendar year."""
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        return self.calculate(dma_id, start, end)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def calculate_simple_nrw(
    siv_m3: float,
    billed_m3: float,
    unbilled_m3: float = 0
) -> Tuple[float, float]:
    """
    Simple NRW calculation without infrastructure data.
    
    Args:
        siv_m3: System Input Volume (m³)
        billed_m3: Billed authorized consumption (m³)
        unbilled_m3: Unbilled authorized consumption (m³)
        
    Returns:
        Tuple of (NRW volume m³, NRW percent)
    """
    nrw_m3 = siv_m3 - billed_m3 - unbilled_m3
    nrw_m3 = max(nrw_m3, 0)
    nrw_percent = (nrw_m3 / siv_m3 * 100) if siv_m3 > 0 else 0
    return nrw_m3, nrw_percent


def get_nrw_rating(nrw_percent: float) -> str:
    """
    Get NRW performance rating.
    
    Based on typical industry benchmarks:
    - < 20%: Excellent
    - 20-30%: Good
    - 30-40%: Acceptable
    - 40-50%: Poor
    - > 50%: Critical
    """
    if nrw_percent < 20:
        return "EXCELLENT"
    elif nrw_percent < 30:
        return "GOOD"
    elif nrw_percent < 40:
        return "ACCEPTABLE"
    elif nrw_percent < 50:
        return "POOR"
    else:
        return "CRITICAL"


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create calculator (without SIV manager for demo)
    calculator = NRWCalculator(default_tariff_usd_per_m3=0.45)
    
    # Example calculation with provided data
    result = calculator.calculate(
        dma_id="DMA-MATERO-001",
        start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 1, 31, tzinfo=timezone.utc),
        siv_m3=450000,           # 450,000 m³ SIV
        billed_m3=255000,        # 255,000 m³ billed
        unbilled_m3=15000,       # 15,000 m³ unbilled
        infrastructure={
            "number_of_connections": 12500,
            "mains_length_km": 85.5,
            "average_pressure_m": 35,
            "avg_connection_length_m": 12
        },
        mnf_data={
            "mnf_m3_hour": 185,
            "mnf_excess_m3_day": 3840
        },
        assumptions={
            "note": "Example calculation for demonstration"
        }
    )
    
    # Print results
    print(result.to_executive_summary())
    
    # Print JSON
    import json
    print("\nJSON OUTPUT:")
    print(json.dumps(result.to_dict(), indent=2))
