"""
AquaWatch NRW - IWA Water Balance Calculator
============================================

Implements the IWA Standard Water Balance for NRW calculation.

IWA WATER BALANCE FRAMEWORK:
============================

System Input Volume (SIV)
├── Authorized Consumption
│   ├── Billed Authorized Consumption
│   │   ├── Billed Metered (revenue water)
│   │   └── Billed Unmetered
│   └── Unbilled Authorized Consumption
│       ├── Unbilled Metered (own use)
│       └── Unbilled Unmetered (firefighting, flushing)
│
└── Water Losses (Non-Revenue Water)
    ├── Apparent Losses
    │   ├── Unauthorized Consumption (theft)
    │   └── Metering Inaccuracies
    │
    └── Real Losses
        ├── Leakage on Transmission Mains
        ├── Leakage on Distribution Mains
        ├── Leakage on Service Connections
        └── Overflows at Storage

This calculator focuses on DMA-level analysis with:
- System Input Volume from bulk meters
- Billed consumption aggregation
- MNF-based real loss estimation
- Performance indicators (ILI, ELL, UARL)

References:
- IWA Manual of Best Practice: Performance Indicators for Water Supply Services
- AWWA M36 Manual: Water Audits and Loss Control Programs
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# IWA WATER BALANCE COMPONENTS
# =============================================================================

@dataclass
class SystemInputVolume:
    """
    System Input Volume (SIV) for a DMA.
    
    Source: Bulk flow meters at DMA inlet(s).
    Period: Typically daily or monthly totals.
    """
    dma_id: str
    period_start: datetime
    period_end: datetime
    
    # Total volume entering the DMA (m³)
    total_volume_m3: float
    
    # Data quality
    data_completeness_percent: float = 100.0
    estimated_volume_m3: float = 0.0  # Volume estimated due to gaps
    measurement_uncertainty_percent: float = 2.0


@dataclass
class AuthorizedConsumption:
    """
    Authorized Consumption components.
    """
    dma_id: str
    period_start: datetime
    period_end: datetime
    
    # Billed Authorized
    billed_metered_m3: float = 0.0      # From customer meters
    billed_unmetered_m3: float = 0.0    # Flat-rate customers
    
    # Unbilled Authorized
    unbilled_metered_m3: float = 0.0    # Utility own use
    unbilled_unmetered_m3: float = 0.0  # Firefighting, flushing, etc.
    
    @property
    def total_authorized_m3(self) -> float:
        return (self.billed_metered_m3 + self.billed_unmetered_m3 +
                self.unbilled_metered_m3 + self.unbilled_unmetered_m3)
    
    @property
    def total_billed_m3(self) -> float:
        return self.billed_metered_m3 + self.billed_unmetered_m3
    
    @property
    def revenue_water_m3(self) -> float:
        """Water that generates revenue."""
        return self.total_billed_m3


@dataclass
class WaterLosses:
    """
    Water Losses (NRW components).
    """
    dma_id: str
    period_start: datetime
    period_end: datetime
    
    # Apparent Losses (Commercial)
    unauthorized_consumption_m3: float = 0.0  # Theft, illegal connections
    metering_inaccuracies_m3: float = 0.0     # Meter under-registration
    data_handling_errors_m3: float = 0.0      # Billing errors
    
    # Real Losses (Physical)
    leakage_transmission_m3: float = 0.0      # Transmission mains
    leakage_distribution_m3: float = 0.0      # Distribution mains
    leakage_service_connections_m3: float = 0.0  # Service connections
    storage_overflows_m3: float = 0.0         # Tank overflows
    
    @property
    def total_apparent_losses_m3(self) -> float:
        return (self.unauthorized_consumption_m3 + 
                self.metering_inaccuracies_m3 +
                self.data_handling_errors_m3)
    
    @property
    def total_real_losses_m3(self) -> float:
        return (self.leakage_transmission_m3 + 
                self.leakage_distribution_m3 +
                self.leakage_service_connections_m3 +
                self.storage_overflows_m3)
    
    @property
    def total_losses_m3(self) -> float:
        return self.total_apparent_losses_m3 + self.total_real_losses_m3


@dataclass
class DMAInfrastructure:
    """
    DMA infrastructure parameters for IWA calculations.
    """
    dma_id: str
    
    # Network length
    mains_length_km: float              # Distribution mains length
    
    # Service connections
    number_of_connections: int
    
    # Pressure
    average_operating_pressure_m: float  # Meters head (1 bar ≈ 10 m)
    
    # Optional fields with defaults
    transmission_length_km: float = 0.0  # Transmission mains in DMA
    avg_connection_length_m: float = 15.0  # From main to property boundary
    
    # Other
    connection_density_per_km: float = 0.0  # Calculated
    
    def __post_init__(self):
        if self.mains_length_km > 0:
            self.connection_density_per_km = self.number_of_connections / self.mains_length_km


# =============================================================================
# IWA PERFORMANCE INDICATORS
# =============================================================================

@dataclass
class IWAPerformanceIndicators:
    """
    IWA/AWWA Performance Indicators for NRW.
    
    These are internationally standardized metrics that allow
    comparison between utilities worldwide.
    """
    dma_id: str
    calculation_date: datetime
    period_days: int
    
    # =========================================================================
    # LEVEL 1: Basic NRW Indicators
    # =========================================================================
    
    # NRW as percentage of SIV (most common metric)
    nrw_percent: float
    
    # NRW volume (m³/day)
    nrw_m3_per_day: float
    
    # Real Losses as percentage of SIV
    real_losses_percent: float
    
    # Apparent Losses as percentage of SIV
    apparent_losses_percent: float
    
    # =========================================================================
    # LEVEL 2: Operational Indicators
    # =========================================================================
    
    # Real losses per connection per day (L/conn/day)
    # Common benchmark: <100 L/conn/day = good, >250 = poor
    real_losses_l_per_conn_day: float
    
    # Real losses per km of mains per day (m³/km/day)
    real_losses_m3_per_km_day: float
    
    # Real losses per service connection per meter of pressure per day
    # (L/conn/day/m) - pressure normalized
    real_losses_per_conn_per_m_pressure: float
    
    # =========================================================================
    # LEVEL 3: IWA Advanced Indicators
    # =========================================================================
    
    # Infrastructure Leakage Index (ILI)
    # ILI = Current Annual Real Losses / Unavoidable Annual Real Losses
    # ILI = 1.0 means operating at technical minimum
    # ILI = 2.0 means losing twice the unavoidable minimum
    # Good: <2.0, Acceptable: 2-4, Poor: 4-8, Very Poor: >8
    ili: float
    
    # Unavoidable Annual Real Losses (UARL) - theoretical minimum
    # Based on Lambert's formula
    uarl_l_per_conn_day: float
    uarl_m3_per_year: float
    
    # Current Annual Real Losses (CARL)
    carl_m3_per_year: float
    
    # Economic Level of Leakage (ELL)
    # The point where cost of reducing leakage = value of water saved
    ell_l_per_conn_day: float
    
    # =========================================================================
    # MNF-Based Indicators
    # =========================================================================
    
    # Minimum Night Flow (average, typically 01:00-04:00)
    mnf_m3_per_hour: float
    
    # MNF as percentage of average daily flow
    mnf_percent_of_average: float
    
    # MNF excess (potential leakage indicator)
    mnf_excess_m3_per_hour: float
    mnf_excess_m3_per_day: float
    
    # Estimated night legitimate use (L/conn/hour)
    night_legitimate_use_l_per_conn_hour: float = 1.7  # IWA default
    
    def get_ili_rating(self) -> str:
        """Get ILI performance rating."""
        if self.ili < 2.0:
            return "GOOD - Well-managed infrastructure"
        elif self.ili < 4.0:
            return "ACCEPTABLE - Room for improvement"
        elif self.ili < 8.0:
            return "POOR - Significant losses, action needed"
        else:
            return "VERY POOR - Urgent intervention required"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dma_id": self.dma_id,
            "calculation_date": self.calculation_date.isoformat(),
            "period_days": self.period_days,
            "level_1_basic": {
                "nrw_percent": round(self.nrw_percent, 1),
                "nrw_m3_per_day": round(self.nrw_m3_per_day, 1),
                "real_losses_percent": round(self.real_losses_percent, 1),
                "apparent_losses_percent": round(self.apparent_losses_percent, 1)
            },
            "level_2_operational": {
                "real_losses_l_per_conn_day": round(self.real_losses_l_per_conn_day, 1),
                "real_losses_m3_per_km_day": round(self.real_losses_m3_per_km_day, 2),
                "real_losses_per_conn_per_m_pressure": round(self.real_losses_per_conn_per_m_pressure, 2)
            },
            "level_3_iwa": {
                "ili": round(self.ili, 2),
                "ili_rating": self.get_ili_rating(),
                "uarl_l_per_conn_day": round(self.uarl_l_per_conn_day, 1),
                "carl_m3_per_year": round(self.carl_m3_per_year, 0),
                "ell_l_per_conn_day": round(self.ell_l_per_conn_day, 1)
            },
            "mnf_analysis": {
                "mnf_m3_per_hour": round(self.mnf_m3_per_hour, 2),
                "mnf_percent_of_average": round(self.mnf_percent_of_average, 1),
                "mnf_excess_m3_per_day": round(self.mnf_excess_m3_per_day, 1)
            }
        }
    
    def to_report(self) -> str:
        """Generate formatted report."""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    IWA WATER BALANCE PERFORMANCE INDICATORS                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DMA: {self.dma_id:<72} ║
║  Period: {self.period_days} days ending {self.calculation_date.strftime('%Y-%m-%d'):<52} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LEVEL 1 - BASIC NRW INDICATORS                                              ║
╠──────────────────────────────────────────────────────────────────────────────╣
║  NRW as % of System Input:     {self.nrw_percent:>6.1f}%                                       ║
║  NRW Volume:                   {self.nrw_m3_per_day:>6.0f} m³/day                                   ║
║  Real Losses:                  {self.real_losses_percent:>6.1f}% of SIV                                ║
║  Apparent Losses:              {self.apparent_losses_percent:>6.1f}% of SIV                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LEVEL 2 - OPERATIONAL INDICATORS                                            ║
╠──────────────────────────────────────────────────────────────────────────────╣
║  Real Losses per Connection:   {self.real_losses_l_per_conn_day:>6.0f} L/conn/day                           ║
║  Real Losses per km Mains:     {self.real_losses_m3_per_km_day:>6.1f} m³/km/day                            ║
║  Pressure-normalized:          {self.real_losses_per_conn_per_m_pressure:>6.2f} L/conn/day/m                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LEVEL 3 - IWA ADVANCED INDICATORS                                           ║
╠──────────────────────────────────────────────────────────────────────────────╣
║  Infrastructure Leakage Index: {self.ili:>6.2f}                                            ║
║  Rating: {self.get_ili_rating():<68} ║
║  UARL (Unavoidable):           {self.uarl_l_per_conn_day:>6.0f} L/conn/day                           ║
║  CARL (Current):               {self.carl_m3_per_year:>10,.0f} m³/year                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  MNF ANALYSIS (Night Leakage Indicator)                                      ║
╠──────────────────────────────────────────────────────────────────────────────╣
║  Minimum Night Flow:           {self.mnf_m3_per_hour:>6.1f} m³/hour                                ║
║  MNF as % of Average:          {self.mnf_percent_of_average:>6.1f}%                                       ║
║  MNF Excess (Est. Leakage):    {self.mnf_excess_m3_per_day:>6.0f} m³/day                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# IWA WATER BALANCE CALCULATOR
# =============================================================================

class IWAWaterBalanceCalculator:
    """
    Implements IWA Standard Water Balance calculations.
    
    This is the authoritative method for calculating NRW
    according to international water industry standards.
    """
    
    def __init__(self):
        # IWA coefficients for UARL calculation (Lambert's formula)
        # UARL = (18 × Lm + 0.8 × Nc + 25 × Lp) × P
        # Where:
        #   Lm = Mains length (km)
        #   Nc = Number of connections
        #   Lp = Total length of private pipes (km)
        #   P = Average pressure (m)
        self.uarl_coefficient_mains = 18.0       # L/km mains/day/m pressure
        self.uarl_coefficient_connections = 0.80  # L/connection/day/m pressure
        self.uarl_coefficient_private = 25.0      # L/km private pipe/day/m pressure
        
        # Default night legitimate use per connection (IWA guideline)
        self.night_use_l_per_conn_hour = 1.7
        
        logger.info("IWA Water Balance Calculator initialized")
    
    def calculate_water_balance(
        self,
        siv: SystemInputVolume,
        consumption: AuthorizedConsumption,
        infrastructure: DMAInfrastructure,
        mnf_data: Optional[Dict[str, float]] = None
    ) -> Tuple[WaterLosses, IWAPerformanceIndicators]:
        """
        Calculate complete IWA water balance and performance indicators.
        
        Args:
            siv: System Input Volume data
            consumption: Authorized consumption data
            infrastructure: DMA infrastructure parameters
            mnf_data: Optional MNF analysis results
            
        Returns:
            Tuple of (WaterLosses, IWAPerformanceIndicators)
        """
        # Calculate period in days
        period_days = (siv.period_end - siv.period_start).days
        if period_days <= 0:
            period_days = 1
        
        # =================================================================
        # STEP 1: Calculate Total Water Losses
        # NRW = SIV - Authorized Consumption
        # =================================================================
        total_losses_m3 = siv.total_volume_m3 - consumption.total_authorized_m3
        total_losses_m3 = max(total_losses_m3, 0)  # Cannot be negative
        
        # =================================================================
        # STEP 2: Estimate Real vs Apparent Losses
        # 
        # Without detailed data, use industry assumptions:
        # - Apparent losses typically 20-30% of NRW
        # - Real losses typically 70-80% of NRW
        # 
        # Better estimate using MNF if available
        # =================================================================
        
        if mnf_data and 'mnf_excess_m3_day' in mnf_data:
            # MNF-based estimation (more accurate)
            # Night excess flow × 24 hours = estimated real losses
            estimated_real_losses_m3_day = mnf_data['mnf_excess_m3_day']
            estimated_real_losses_m3 = estimated_real_losses_m3_day * period_days
            estimated_apparent_losses_m3 = total_losses_m3 - estimated_real_losses_m3
            estimated_apparent_losses_m3 = max(estimated_apparent_losses_m3, 0)
        else:
            # Default assumption: 75% real, 25% apparent
            estimated_real_losses_m3 = total_losses_m3 * 0.75
            estimated_apparent_losses_m3 = total_losses_m3 * 0.25
        
        # Create WaterLosses object
        losses = WaterLosses(
            dma_id=siv.dma_id,
            period_start=siv.period_start,
            period_end=siv.period_end,
            # Apparent losses (split assumption)
            unauthorized_consumption_m3=estimated_apparent_losses_m3 * 0.4,
            metering_inaccuracies_m3=estimated_apparent_losses_m3 * 0.5,
            data_handling_errors_m3=estimated_apparent_losses_m3 * 0.1,
            # Real losses (split assumption based on typical distribution)
            leakage_transmission_m3=estimated_real_losses_m3 * 0.1,
            leakage_distribution_m3=estimated_real_losses_m3 * 0.5,
            leakage_service_connections_m3=estimated_real_losses_m3 * 0.35,
            storage_overflows_m3=estimated_real_losses_m3 * 0.05
        )
        
        # =================================================================
        # STEP 3: Calculate Performance Indicators
        # =================================================================
        indicators = self._calculate_indicators(
            siv, consumption, losses, infrastructure, mnf_data, period_days
        )
        
        return losses, indicators
    
    def _calculate_indicators(
        self,
        siv: SystemInputVolume,
        consumption: AuthorizedConsumption,
        losses: WaterLosses,
        infrastructure: DMAInfrastructure,
        mnf_data: Optional[Dict[str, float]],
        period_days: int
    ) -> IWAPerformanceIndicators:
        """Calculate IWA performance indicators."""
        
        # Basic volumes
        total_nrw_m3 = losses.total_losses_m3
        real_losses_m3 = losses.total_real_losses_m3
        apparent_losses_m3 = losses.total_apparent_losses_m3
        
        # Daily averages
        siv_per_day = siv.total_volume_m3 / period_days
        nrw_per_day = total_nrw_m3 / period_days
        real_losses_per_day = real_losses_m3 / period_days
        
        # =================================================================
        # Level 1: Basic percentages
        # =================================================================
        nrw_percent = (total_nrw_m3 / siv.total_volume_m3 * 100) if siv.total_volume_m3 > 0 else 0
        real_losses_percent = (real_losses_m3 / siv.total_volume_m3 * 100) if siv.total_volume_m3 > 0 else 0
        apparent_losses_percent = (apparent_losses_m3 / siv.total_volume_m3 * 100) if siv.total_volume_m3 > 0 else 0
        
        # =================================================================
        # Level 2: Operational indicators
        # =================================================================
        
        # Real losses per connection (L/conn/day)
        real_losses_l_per_day = real_losses_per_day * 1000  # Convert m³ to L
        real_losses_per_conn = (
            real_losses_l_per_day / infrastructure.number_of_connections
            if infrastructure.number_of_connections > 0 else 0
        )
        
        # Real losses per km of mains (m³/km/day)
        real_losses_per_km = (
            real_losses_per_day / infrastructure.mains_length_km
            if infrastructure.mains_length_km > 0 else 0
        )
        
        # Pressure-normalized (L/conn/day/m)
        real_losses_per_conn_per_m = (
            real_losses_per_conn / infrastructure.average_operating_pressure_m
            if infrastructure.average_operating_pressure_m > 0 else 0
        )
        
        # =================================================================
        # Level 3: IWA Advanced - UARL and ILI
        # =================================================================
        
        # UARL (Unavoidable Annual Real Losses) using Lambert's formula
        # UARL (L/day) = (18 × Lm + 0.8 × Nc + 25 × Lp) × P
        
        total_private_pipe_km = (
            infrastructure.number_of_connections * 
            infrastructure.avg_connection_length_m / 1000
        )
        
        uarl_l_per_day = (
            self.uarl_coefficient_mains * infrastructure.mains_length_km +
            self.uarl_coefficient_connections * infrastructure.number_of_connections +
            self.uarl_coefficient_private * total_private_pipe_km
        ) * infrastructure.average_operating_pressure_m
        
        uarl_l_per_conn_day = (
            uarl_l_per_day / infrastructure.number_of_connections
            if infrastructure.number_of_connections > 0 else 0
        )
        
        uarl_m3_per_year = uarl_l_per_day * 365 / 1000
        
        # CARL (Current Annual Real Losses)
        carl_m3_per_year = real_losses_per_day * 365
        
        # ILI = CARL / UARL
        ili = carl_m3_per_year / uarl_m3_per_year if uarl_m3_per_year > 0 else 0
        
        # ELL (Economic Level of Leakage) - simplified estimate
        # ELL = UARL × economic factor (typically 1.5-3.0)
        ell_factor = 2.0  # Default for developing countries
        ell_l_per_conn_day = uarl_l_per_conn_day * ell_factor
        
        # =================================================================
        # MNF Analysis
        # =================================================================
        if mnf_data:
            mnf_m3_per_hour = mnf_data.get('mnf_m3_hour', 0)
            mnf_excess_m3_per_hour = mnf_data.get('mnf_excess_m3_hour', 0)
            mnf_excess_m3_per_day = mnf_data.get('mnf_excess_m3_day', 0)
        else:
            # Estimate MNF as percentage of daily flow
            avg_flow_per_hour = siv_per_day / 24
            mnf_m3_per_hour = avg_flow_per_hour * 0.35  # MNF typically 25-45% of average
            
            # Expected legitimate night use
            expected_night_use = (
                self.night_use_l_per_conn_hour * 
                infrastructure.number_of_connections / 1000  # Convert to m³
            )
            
            mnf_excess_m3_per_hour = max(mnf_m3_per_hour - expected_night_use, 0)
            mnf_excess_m3_per_day = mnf_excess_m3_per_hour * 24
        
        mnf_percent_of_average = (
            mnf_m3_per_hour / (siv_per_day / 24) * 100
            if siv_per_day > 0 else 0
        )
        
        return IWAPerformanceIndicators(
            dma_id=siv.dma_id,
            calculation_date=datetime.utcnow(),
            period_days=period_days,
            
            # Level 1
            nrw_percent=nrw_percent,
            nrw_m3_per_day=nrw_per_day,
            real_losses_percent=real_losses_percent,
            apparent_losses_percent=apparent_losses_percent,
            
            # Level 2
            real_losses_l_per_conn_day=real_losses_per_conn,
            real_losses_m3_per_km_day=real_losses_per_km,
            real_losses_per_conn_per_m_pressure=real_losses_per_conn_per_m,
            
            # Level 3
            ili=ili,
            uarl_l_per_conn_day=uarl_l_per_conn_day,
            uarl_m3_per_year=uarl_m3_per_year,
            carl_m3_per_year=carl_m3_per_year,
            ell_l_per_conn_day=ell_l_per_conn_day,
            
            # MNF
            mnf_m3_per_hour=mnf_m3_per_hour,
            mnf_percent_of_average=mnf_percent_of_average,
            mnf_excess_m3_per_hour=mnf_excess_m3_per_hour,
            mnf_excess_m3_per_day=mnf_excess_m3_per_day
        )
    
    def calculate_mnf_from_flow_data(
        self,
        flow_data: pd.DataFrame,
        infrastructure: DMAInfrastructure,
        mnf_start_hour: int = 1,
        mnf_end_hour: int = 4
    ) -> Dict[str, float]:
        """
        Calculate MNF metrics from flow time series data.
        
        Args:
            flow_data: DataFrame with 'timestamp' and 'flow_m3_hour' columns
            infrastructure: DMA infrastructure for legitimate use calculation
            mnf_start_hour: Start of MNF window (default 01:00)
            mnf_end_hour: End of MNF window (default 04:00)
            
        Returns:
            Dictionary with MNF metrics
        """
        if flow_data is None or len(flow_data) == 0:
            return {}
        
        df = flow_data.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
        elif isinstance(df.index, pd.DatetimeIndex):
            df['hour'] = df.index.hour
        else:
            return {}
        
        # Filter to MNF window
        mnf_mask = df['hour'].isin(range(mnf_start_hour, mnf_end_hour))
        mnf_df = df[mnf_mask]
        
        if len(mnf_df) == 0:
            return {}
        
        # Calculate MNF statistics
        mnf_m3_hour = mnf_df['flow_m3_hour'].mean()
        mnf_min_m3_hour = mnf_df['flow_m3_hour'].min()
        mnf_max_m3_hour = mnf_df['flow_m3_hour'].max()
        
        # Calculate expected legitimate night use
        expected_night_use_m3_hour = (
            self.night_use_l_per_conn_hour * 
            infrastructure.number_of_connections / 1000
        )
        
        # MNF excess (potential leakage)
        mnf_excess_m3_hour = max(mnf_m3_hour - expected_night_use_m3_hour, 0)
        mnf_excess_m3_day = mnf_excess_m3_hour * 24
        
        # Average daily flow for comparison
        avg_daily_flow = df['flow_m3_hour'].mean() * 24
        mnf_percent = (mnf_m3_hour * 24 / avg_daily_flow * 100) if avg_daily_flow > 0 else 0
        
        return {
            'mnf_m3_hour': mnf_m3_hour,
            'mnf_min_m3_hour': mnf_min_m3_hour,
            'mnf_max_m3_hour': mnf_max_m3_hour,
            'expected_night_use_m3_hour': expected_night_use_m3_hour,
            'mnf_excess_m3_hour': mnf_excess_m3_hour,
            'mnf_excess_m3_day': mnf_excess_m3_day,
            'mnf_percent_of_daily': mnf_percent,
            'avg_daily_flow_m3': avg_daily_flow
        }
    
    def estimate_real_losses_from_mnf(
        self,
        mnf_excess_m3_day: float,
        infrastructure: DMAInfrastructure
    ) -> Dict[str, float]:
        """
        Estimate real loss components from MNF excess.
        
        Uses typical distribution ratios for sub-Saharan Africa.
        """
        # Typical distribution of real losses (can be calibrated per utility)
        # Based on IWA studies in developing countries
        distribution = {
            'transmission': 0.10,       # 10% - larger, easier to detect
            'distribution': 0.50,       # 50% - most of network
            'service_connections': 0.35, # 35% - many small leaks
            'overflows': 0.05           # 5% - tank overflows
        }
        
        # Apply pressure correction
        # N1 exponent for pressure-leakage relationship (typical 1.0-1.5)
        n1 = 1.15  # Average for mixed networks
        
        return {
            'transmission_m3_day': mnf_excess_m3_day * distribution['transmission'],
            'distribution_m3_day': mnf_excess_m3_day * distribution['distribution'],
            'service_connections_m3_day': mnf_excess_m3_day * distribution['service_connections'],
            'overflows_m3_day': mnf_excess_m3_day * distribution['overflows'],
            'total_real_losses_m3_day': mnf_excess_m3_day,
            'n1_exponent_used': n1,
            'pressure_m': infrastructure.average_operating_pressure_m
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_sample_data() -> Tuple[SystemInputVolume, AuthorizedConsumption, DMAInfrastructure]:
    """Create sample data for testing (Lusaka DMA example)."""
    
    period_start = datetime(2026, 1, 1)
    period_end = datetime(2026, 1, 31)
    
    siv = SystemInputVolume(
        dma_id="DMA-LUS-001",
        period_start=period_start,
        period_end=period_end,
        total_volume_m3=450000,  # 450,000 m³ in January
        data_completeness_percent=98.5
    )
    
    consumption = AuthorizedConsumption(
        dma_id="DMA-LUS-001",
        period_start=period_start,
        period_end=period_end,
        billed_metered_m3=240000,      # 53% of SIV
        billed_unmetered_m3=15000,     # Flat-rate customers
        unbilled_metered_m3=5000,      # Utility use
        unbilled_unmetered_m3=10000    # Firefighting, flushing
    )
    
    infrastructure = DMAInfrastructure(
        dma_id="DMA-LUS-001",
        mains_length_km=85.5,
        transmission_length_km=5.2,
        number_of_connections=12500,
        avg_connection_length_m=12.0,
        average_operating_pressure_m=35.0  # 3.5 bar
    )
    
    return siv, consumption, infrastructure


# =============================================================================
# MAIN EXECUTION (Demo)
# =============================================================================

if __name__ == "__main__":
    # Initialize calculator
    calculator = IWAWaterBalanceCalculator()
    
    # Get sample data
    siv, consumption, infrastructure = create_sample_data()
    
    # MNF data from sensor analysis
    mnf_data = {
        'mnf_m3_hour': 185.0,         # 185 m³/hour during night
        'mnf_excess_m3_hour': 160.0,  # After subtracting legitimate use
        'mnf_excess_m3_day': 3840.0   # 160 × 24
    }
    
    # Calculate water balance
    losses, indicators = calculator.calculate_water_balance(
        siv, consumption, infrastructure, mnf_data
    )
    
    # Print results
    print("\n" + "="*80)
    print("IWA WATER BALANCE CALCULATION")
    print("="*80)
    
    print(f"\nSYSTEM INPUT VOLUME: {siv.total_volume_m3:,.0f} m³")
    print(f"AUTHORIZED CONSUMPTION: {consumption.total_authorized_m3:,.0f} m³")
    print(f"  - Billed: {consumption.total_billed_m3:,.0f} m³")
    print(f"WATER LOSSES: {losses.total_losses_m3:,.0f} m³")
    print(f"  - Real Losses: {losses.total_real_losses_m3:,.0f} m³")
    print(f"  - Apparent Losses: {losses.total_apparent_losses_m3:,.0f} m³")
    
    print(indicators.to_report())
    
    # Print JSON output
    print("\nJSON OUTPUT:")
    print("="*80)
    import json
    print(json.dumps(indicators.to_dict(), indent=2))
