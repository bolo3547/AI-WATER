"""
AquaWatch NRW - SIV Manager
===========================

System Input Volume (SIV) Management:
- SIV data models linked to date/time
- Multiple SIV sources (treatment plants, reservoirs)
- REST API and CSV batch ingestion
- DMA inlet boundary flow tagging
- Timestamp alignment (SIV ↔ DMA ↔ Pressure ↔ Billing)
- Unit validation (m³/day, m³/hour)
- Timezone consistency

This is the FOUNDATION for NRW calculation.
NO SIV = NO NRW ANALYSIS.
"""

import csv
import io
import uuid
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class SIVSourceType(Enum):
    """Types of SIV sources."""
    TREATMENT_PLANT = "treatment_plant"      # Water treatment plant output
    RESERVOIR = "reservoir"                  # Reservoir/tank output
    BULK_METER = "bulk_meter"                # Bulk flow meter at network entry
    BOREHOLE = "borehole"                    # Groundwater source
    IMPORTED = "imported"                    # Bulk purchase from another utility
    MANUAL_ESTIMATE = "manual_estimate"      # Manual entry (fallback)


class FlowUnit(Enum):
    """Standardized flow measurement units."""
    M3_PER_HOUR = "m3/h"          # Cubic meters per hour
    M3_PER_DAY = "m3/day"         # Cubic meters per day
    L_PER_SEC = "l/s"             # Liters per second
    ML_PER_DAY = "ML/day"         # Megalitres per day


class DataQuality(Enum):
    """Data quality classification."""
    MEASURED = "measured"          # Direct meter reading
    ESTIMATED = "estimated"        # Calculated/estimated value
    INTERPOLATED = "interpolated"  # Gap-filled value
    INVALID = "invalid"            # Failed validation


class TimestampAlignment(Enum):
    """Timestamp alignment method."""
    EXACT = "exact"                # Timestamps match exactly
    INTERPOLATED = "interpolated"  # Values interpolated to align
    AGGREGATED = "aggregated"      # Values aggregated (e.g., daily total)
    ESTIMATED = "estimated"        # Timestamps estimated


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SIVSource:
    """
    A source of System Input Volume (treatment plant, reservoir, bulk meter).
    """
    source_id: str
    source_type: SIVSourceType
    name: str
    
    # Location
    utility_id: Optional[str] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Measurement
    meter_id: Optional[str] = None
    meter_serial: Optional[str] = None
    measurement_unit: FlowUnit = FlowUnit.M3_PER_HOUR
    accuracy_percent: float = 2.0  # Typical bulk meter accuracy
    
    # Connected DMAs (for inlet flow attribution)
    connected_dma_ids: List[str] = field(default_factory=list)
    
    # Capacity
    design_capacity_m3_day: Optional[float] = None
    max_flow_m3_hour: Optional[float] = None
    
    # Status
    is_active: bool = True
    last_reading_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "name": self.name,
            "utility_id": self.utility_id,
            "location": {
                "description": self.location_description,
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "measurement": {
                "meter_id": self.meter_id,
                "unit": self.measurement_unit.value,
                "accuracy_percent": self.accuracy_percent
            },
            "connected_dma_ids": self.connected_dma_ids,
            "capacity": {
                "design_m3_day": self.design_capacity_m3_day,
                "max_flow_m3_hour": self.max_flow_m3_hour
            },
            "is_active": self.is_active,
            "last_reading_at": self.last_reading_at.isoformat() if self.last_reading_at else None
        }


@dataclass
class SIVRecord:
    """
    System Input Volume record at a specific time.
    
    This is the FOUNDATION of NRW calculation.
    SIV represents total water entering the distribution network.
    """
    record_id: str
    source_id: str                           # Foreign key to SIVSource
    timestamp: datetime                       # UTC timestamp
    
    # Volume measurement
    volume_m3: float                          # Volume in cubic meters
    flow_rate_m3_hour: Optional[float] = None  # Instantaneous flow rate
    
    # Time period (for aggregated data)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    aggregation_type: str = "instantaneous"   # instantaneous, hourly, daily
    
    # Data quality
    quality: DataQuality = DataQuality.MEASURED
    quality_score: int = 100                  # 0-100
    is_validated: bool = False
    
    # Raw reading (before conversion)
    raw_value: Optional[float] = None
    raw_unit: Optional[str] = None
    
    # Uncertainty
    uncertainty_m3: Optional[float] = None    # ±m³
    uncertainty_percent: Optional[float] = None  # ±%
    
    # Metadata
    ingestion_method: str = "api"             # api, csv, scada, manual
    ingestion_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "volume_m3": round(self.volume_m3, 3),
            "flow_rate_m3_hour": round(self.flow_rate_m3_hour, 3) if self.flow_rate_m3_hour else None,
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
                "type": self.aggregation_type
            },
            "quality": {
                "status": self.quality.value,
                "score": self.quality_score,
                "is_validated": self.is_validated
            },
            "uncertainty": {
                "m3": self.uncertainty_m3,
                "percent": self.uncertainty_percent
            }
        }


@dataclass
class DMAInletFlow:
    """
    Water flow entering a specific DMA boundary.
    
    This links SIV to individual DMAs for loss attribution.
    A DMA may have multiple inlet points.
    """
    record_id: str
    dma_id: str                               # Foreign key to DMA
    inlet_point_id: str                        # Specific entry point
    timestamp: datetime                        # UTC timestamp
    
    # Flow measurement
    volume_m3: float                          # Volume for period
    flow_rate_m3_hour: float                  # Flow rate
    
    # Period
    period_start: datetime
    period_end: datetime
    
    # Direction (inlet vs outlet)
    is_inlet: bool = True                      # True = water entering DMA
    
    # Linked SIV source (if applicable)
    siv_source_id: Optional[str] = None
    
    # Data quality
    quality: DataQuality = DataQuality.MEASURED
    quality_score: int = 100
    
    # Meter info
    meter_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "dma_id": self.dma_id,
            "inlet_point_id": self.inlet_point_id,
            "timestamp": self.timestamp.isoformat(),
            "volume_m3": round(self.volume_m3, 3),
            "flow_rate_m3_hour": round(self.flow_rate_m3_hour, 3),
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "is_inlet": self.is_inlet,
            "siv_source_id": self.siv_source_id,
            "quality": {
                "status": self.quality.value,
                "score": self.quality_score
            }
        }


@dataclass
class BillingRecord:
    """
    Billing data for authorized consumption.
    
    Required for NRW calculation:
    NRW = SIV - (Billed + Unbilled Authorized)
    """
    record_id: str
    dma_id: str                               # Foreign key to DMA
    billing_period_start: date
    billing_period_end: date
    
    # Billed Authorized Consumption (m³)
    billed_metered_m3: float = 0.0            # From customer meters
    billed_unmetered_m3: float = 0.0          # Flat-rate customers
    
    # Unbilled Authorized Consumption (m³)
    unbilled_metered_m3: float = 0.0          # Utility own use (metered)
    unbilled_unmetered_m3: float = 0.0        # Firefighting, flushing, etc.
    
    # Customer counts
    metered_customer_count: int = 0
    unmetered_customer_count: int = 0
    
    # Revenue (optional, for financial analysis)
    revenue_usd: Optional[float] = None
    tariff_usd_per_m3: Optional[float] = None
    
    @property
    def total_billed_m3(self) -> float:
        """Total billed consumption."""
        return self.billed_metered_m3 + self.billed_unmetered_m3
    
    @property
    def total_unbilled_m3(self) -> float:
        """Total unbilled authorized consumption."""
        return self.unbilled_metered_m3 + self.unbilled_unmetered_m3
    
    @property
    def total_authorized_m3(self) -> float:
        """Total authorized consumption."""
        return self.total_billed_m3 + self.total_unbilled_m3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "dma_id": self.dma_id,
            "billing_period": {
                "start": self.billing_period_start.isoformat(),
                "end": self.billing_period_end.isoformat()
            },
            "consumption_m3": {
                "billed_metered": round(self.billed_metered_m3, 1),
                "billed_unmetered": round(self.billed_unmetered_m3, 1),
                "unbilled_metered": round(self.unbilled_metered_m3, 1),
                "unbilled_unmetered": round(self.unbilled_unmetered_m3, 1),
                "total_authorized": round(self.total_authorized_m3, 1)
            },
            "customer_counts": {
                "metered": self.metered_customer_count,
                "unmetered": self.unmetered_customer_count
            },
            "revenue": {
                "total_usd": self.revenue_usd,
                "tariff_usd_per_m3": self.tariff_usd_per_m3
            } if self.revenue_usd else None
        }


@dataclass
class SIVAggregation:
    """
    Aggregated SIV data for a time period.
    """
    aggregation_id: str
    utility_id: Optional[str] = None
    dma_id: Optional[str] = None              # None = utility-wide
    
    # Period
    period_start: datetime = None
    period_end: datetime = None
    aggregation_level: str = "daily"          # hourly, daily, monthly, annual
    
    # Volume totals
    total_siv_m3: float = 0.0                  # Total system input
    total_inlet_m3: float = 0.0               # Sum of all DMA inlets
    total_billed_m3: float = 0.0              # Billed authorized
    total_unbilled_m3: float = 0.0            # Unbilled authorized
    
    # NRW (calculated)
    nrw_m3: float = 0.0                        # NRW = SIV - Authorized
    nrw_percent: float = 0.0                   # NRW / SIV * 100
    
    # Data quality
    siv_data_completeness: float = 100.0      # % of expected records present
    estimated_volume_m3: float = 0.0          # Volume estimated due to gaps
    
    # Sources included
    source_count: int = 0
    source_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "aggregation_id": self.aggregation_id,
            "utility_id": self.utility_id,
            "dma_id": self.dma_id,
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
                "level": self.aggregation_level
            },
            "volumes_m3": {
                "total_siv": round(self.total_siv_m3, 1),
                "total_inlet": round(self.total_inlet_m3, 1),
                "total_billed": round(self.total_billed_m3, 1),
                "total_unbilled": round(self.total_unbilled_m3, 1),
                "nrw": round(self.nrw_m3, 1),
                "nrw_percent": round(self.nrw_percent, 1)
            },
            "data_quality": {
                "completeness_percent": round(self.siv_data_completeness, 1),
                "estimated_m3": round(self.estimated_volume_m3, 1)
            },
            "sources": {
                "count": self.source_count,
                "ids": self.source_ids
            }
        }


# =============================================================================
# SIV MANAGER - CORE SERVICE
# =============================================================================

class SIVManager:
    """
    Central service for managing System Input Volume data.
    
    Responsibilities:
    - Ingest SIV data via REST API or CSV
    - Manage SIV sources (treatment plants, reservoirs)
    - Track DMA inlet flows
    - Align timestamps across data streams
    - Validate units and data quality
    - Provide aggregated SIV for NRW calculation
    
    Usage:
        manager = SIVManager()
        
        # Register a source
        source = manager.register_source(
            source_type=SIVSourceType.TREATMENT_PLANT,
            name="Kafue Treatment Plant",
            connected_dma_ids=["DMA-01", "DMA-02"]
        )
        
        # Ingest SIV data
        manager.ingest_siv(source_id, timestamp, volume_m3)
        
        # Get SIV for NRW calculation
        siv = manager.get_siv(start_date, end_date, dma_id="DMA-01")
    """
    
    def __init__(self, storage_path: Optional[str] = None, utility_timezone: str = "UTC"):
        """
        Initialize SIV Manager.
        
        Args:
            storage_path: Path for JSON storage (optional, for persistence)
            utility_timezone: Default timezone for the utility
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.utility_timezone = utility_timezone
        
        # In-memory storage (replace with database in production)
        self._sources: Dict[str, SIVSource] = {}
        self._siv_records: List[SIVRecord] = []
        self._inlet_records: List[DMAInletFlow] = []
        self._billing_records: List[BillingRecord] = []
        
        # Unit conversion factors to m³
        self._unit_conversions = {
            FlowUnit.M3_PER_HOUR: 1.0,          # Base unit
            FlowUnit.M3_PER_DAY: 1.0 / 24.0,    # Per day to per hour
            FlowUnit.L_PER_SEC: 3.6,            # L/s to m³/h (1 L/s = 3.6 m³/h)
            FlowUnit.ML_PER_DAY: 1000.0 / 24.0  # ML/day to m³/h
        }
        
        # Load existing data if storage path exists
        if self.storage_path and self.storage_path.exists():
            self._load_from_storage()
        
        logger.info(f"SIV Manager initialized (timezone: {utility_timezone})")
    
    # =========================================================================
    # SOURCE MANAGEMENT
    # =========================================================================
    
    def register_source(
        self,
        source_type: SIVSourceType,
        name: str,
        connected_dma_ids: Optional[List[str]] = None,
        meter_id: Optional[str] = None,
        measurement_unit: FlowUnit = FlowUnit.M3_PER_HOUR,
        design_capacity_m3_day: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        utility_id: Optional[str] = None,
        **kwargs
    ) -> SIVSource:
        """
        Register a new SIV source (treatment plant, reservoir, bulk meter).
        
        Args:
            source_type: Type of source
            name: Human-readable name
            connected_dma_ids: DMAs that receive water from this source
            meter_id: Meter identifier
            measurement_unit: Unit of measurement
            design_capacity_m3_day: Design capacity
            latitude, longitude: Location
            utility_id: Owning utility
            
        Returns:
            Registered SIVSource
        """
        source_id = f"SIV-{source_type.value[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
        
        source = SIVSource(
            source_id=source_id,
            source_type=source_type,
            name=name,
            utility_id=utility_id,
            latitude=latitude,
            longitude=longitude,
            meter_id=meter_id,
            measurement_unit=measurement_unit,
            connected_dma_ids=connected_dma_ids or [],
            design_capacity_m3_day=design_capacity_m3_day,
            **kwargs
        )
        
        self._sources[source_id] = source
        self._save_to_storage()
        
        logger.info(f"Registered SIV source: {name} ({source_id})")
        return source
    
    def get_source(self, source_id: str) -> Optional[SIVSource]:
        """Get a SIV source by ID."""
        return self._sources.get(source_id)
    
    def list_sources(
        self,
        source_type: Optional[SIVSourceType] = None,
        utility_id: Optional[str] = None,
        dma_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[SIVSource]:
        """
        List SIV sources with optional filtering.
        """
        sources = list(self._sources.values())
        
        if active_only:
            sources = [s for s in sources if s.is_active]
        
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        
        if utility_id:
            sources = [s for s in sources if s.utility_id == utility_id]
        
        if dma_id:
            sources = [s for s in sources if dma_id in s.connected_dma_ids]
        
        return sources
    
    # =========================================================================
    # SIV DATA INGESTION
    # =========================================================================
    
    def ingest_siv(
        self,
        source_id: str,
        timestamp: datetime,
        value: float,
        unit: Optional[FlowUnit] = None,
        is_volume: bool = False,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        quality: DataQuality = DataQuality.MEASURED,
        quality_score: int = 100,
        notes: Optional[str] = None,
        ingestion_method: str = "api"
    ) -> SIVRecord:
        """
        Ingest a single SIV data point.
        
        Args:
            source_id: SIV source ID
            timestamp: UTC timestamp of reading
            value: The measurement value
            unit: Unit of measurement (default: source's configured unit)
            is_volume: If True, value is total volume; if False, value is flow rate
            period_start/end: For aggregated data, the time period covered
            quality: Data quality classification
            quality_score: Quality score (0-100)
            notes: Optional notes
            ingestion_method: How data was ingested (api, csv, scada, manual)
            
        Returns:
            Created SIVRecord
        """
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Unknown SIV source: {source_id}")
        
        # Ensure timezone-aware timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Use source's unit if not specified
        if unit is None:
            unit = source.measurement_unit
        
        # Convert to standard units (m³, m³/h)
        raw_value = value
        if is_volume:
            # Value is total volume in m³
            volume_m3 = value
            # Calculate flow rate if period is known
            if period_start and period_end:
                hours = (period_end - period_start).total_seconds() / 3600
                flow_rate = volume_m3 / hours if hours > 0 else 0
            else:
                flow_rate = None
        else:
            # Value is flow rate - convert to m³/h
            conversion_factor = self._unit_conversions.get(unit, 1.0)
            flow_rate = value * conversion_factor
            
            # Calculate volume if period is known
            if period_start and period_end:
                hours = (period_end - period_start).total_seconds() / 3600
                volume_m3 = flow_rate * hours
            else:
                # Assume 1 hour period for instantaneous readings
                volume_m3 = flow_rate
        
        # Create record
        record_id = f"SIV-REC-{uuid.uuid4().hex[:12].upper()}"
        
        record = SIVRecord(
            record_id=record_id,
            source_id=source_id,
            timestamp=timestamp,
            volume_m3=volume_m3,
            flow_rate_m3_hour=flow_rate,
            period_start=period_start,
            period_end=period_end,
            aggregation_type="instantaneous" if not period_start else "aggregated",
            quality=quality,
            quality_score=quality_score,
            is_validated=False,
            raw_value=raw_value,
            raw_unit=unit.value if unit else None,
            ingestion_method=ingestion_method,
            notes=notes
        )
        
        # Add uncertainty based on source accuracy
        record.uncertainty_percent = source.accuracy_percent
        record.uncertainty_m3 = volume_m3 * (source.accuracy_percent / 100)
        
        self._siv_records.append(record)
        
        # Update source last reading
        source.last_reading_at = timestamp
        
        self._save_to_storage()
        
        logger.debug(f"Ingested SIV: {source_id} @ {timestamp} = {volume_m3:.2f} m³")
        return record
    
    def ingest_siv_batch(
        self,
        records: List[Dict[str, Any]],
        default_source_id: Optional[str] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest multiple SIV records at once.
        
        Args:
            records: List of record dictionaries
            default_source_id: Default source if not specified in record
            
        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        success_count = 0
        error_count = 0
        errors = []
        
        for i, rec in enumerate(records):
            try:
                source_id = rec.get('source_id', default_source_id)
                if not source_id:
                    raise ValueError("No source_id provided")
                
                timestamp = rec.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                value = float(rec.get('value', rec.get('volume_m3', rec.get('flow_rate', 0))))
                
                self.ingest_siv(
                    source_id=source_id,
                    timestamp=timestamp,
                    value=value,
                    is_volume=rec.get('is_volume', False),
                    period_start=rec.get('period_start'),
                    period_end=rec.get('period_end'),
                    quality=DataQuality(rec.get('quality', 'measured')),
                    quality_score=int(rec.get('quality_score', 100)),
                    notes=rec.get('notes'),
                    ingestion_method="batch"
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Record {i}: {str(e)}")
                logger.error(f"Batch ingest error at record {i}: {e}")
        
        logger.info(f"Batch ingest: {success_count} success, {error_count} errors")
        return success_count, error_count, errors
    
    def ingest_csv(
        self,
        csv_content: str,
        source_id: str,
        timestamp_column: str = "timestamp",
        value_column: str = "value",
        timestamp_format: Optional[str] = None,
        unit: Optional[FlowUnit] = None,
        is_volume: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest SIV data from CSV content.
        
        Expected CSV format:
            timestamp,value[,quality][,notes]
            2026-01-15T00:00:00Z,125.5
            2026-01-15T01:00:00Z,128.3
            
        Args:
            csv_content: CSV string content
            source_id: SIV source ID
            timestamp_column: Name of timestamp column
            value_column: Name of value column
            timestamp_format: strptime format (auto-detect if None)
            unit: Flow unit (default: source's unit)
            is_volume: If True, values are volumes; if False, flow rates
            
        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Unknown SIV source: {source_id}")
        
        success_count = 0
        error_count = 0
        errors = []
        
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for i, row in enumerate(reader, start=1):
            try:
                # Parse timestamp
                ts_str = row.get(timestamp_column, '').strip()
                if timestamp_format:
                    timestamp = datetime.strptime(ts_str, timestamp_format)
                else:
                    timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                # Parse value
                value = float(row.get(value_column, 0))
                
                # Optional quality
                quality_str = row.get('quality', 'measured').lower()
                quality = DataQuality(quality_str) if quality_str else DataQuality.MEASURED
                
                quality_score = int(row.get('quality_score', 100))
                notes = row.get('notes')
                
                self.ingest_siv(
                    source_id=source_id,
                    timestamp=timestamp,
                    value=value,
                    unit=unit,
                    is_volume=is_volume,
                    quality=quality,
                    quality_score=quality_score,
                    notes=notes,
                    ingestion_method="csv"
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {i}: {str(e)}")
                logger.error(f"CSV ingest error at row {i}: {e}")
        
        logger.info(f"CSV ingest from {source_id}: {success_count} success, {error_count} errors")
        return success_count, error_count, errors
    
    # =========================================================================
    # DMA INLET FLOW
    # =========================================================================
    
    def record_dma_inlet(
        self,
        dma_id: str,
        inlet_point_id: str,
        timestamp: datetime,
        flow_rate_m3_hour: float,
        period_start: datetime,
        period_end: datetime,
        is_inlet: bool = True,
        siv_source_id: Optional[str] = None,
        meter_id: Optional[str] = None,
        quality: DataQuality = DataQuality.MEASURED,
        quality_score: int = 100
    ) -> DMAInletFlow:
        """
        Record flow entering (or leaving) a DMA boundary.
        
        Args:
            dma_id: DMA identifier
            inlet_point_id: Specific entry/exit point
            timestamp: UTC timestamp
            flow_rate_m3_hour: Flow rate in m³/h
            period_start/end: Time period for volume calculation
            is_inlet: True if water entering, False if leaving
            siv_source_id: Link to SIV source (if applicable)
            meter_id: Boundary meter ID
            quality: Data quality
            quality_score: Quality score (0-100)
            
        Returns:
            Created DMAInletFlow record
        """
        # Ensure timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        
        # Calculate volume
        hours = (period_end - period_start).total_seconds() / 3600
        volume_m3 = flow_rate_m3_hour * hours
        
        record_id = f"INLET-{uuid.uuid4().hex[:12].upper()}"
        
        record = DMAInletFlow(
            record_id=record_id,
            dma_id=dma_id,
            inlet_point_id=inlet_point_id,
            timestamp=timestamp,
            volume_m3=volume_m3,
            flow_rate_m3_hour=flow_rate_m3_hour,
            period_start=period_start,
            period_end=period_end,
            is_inlet=is_inlet,
            siv_source_id=siv_source_id,
            meter_id=meter_id,
            quality=quality,
            quality_score=quality_score
        )
        
        self._inlet_records.append(record)
        self._save_to_storage()
        
        logger.debug(f"Recorded DMA inlet: {dma_id}/{inlet_point_id} = {volume_m3:.2f} m³")
        return record
    
    # =========================================================================
    # BILLING DATA
    # =========================================================================
    
    def record_billing(
        self,
        dma_id: str,
        billing_period_start: date,
        billing_period_end: date,
        billed_metered_m3: float = 0.0,
        billed_unmetered_m3: float = 0.0,
        unbilled_metered_m3: float = 0.0,
        unbilled_unmetered_m3: float = 0.0,
        metered_customer_count: int = 0,
        unmetered_customer_count: int = 0,
        revenue_usd: Optional[float] = None,
        tariff_usd_per_m3: Optional[float] = None
    ) -> BillingRecord:
        """
        Record billing/consumption data for a DMA.
        
        Args:
            dma_id: DMA identifier
            billing_period_start/end: Billing period dates
            billed_metered_m3: Billed metered consumption
            billed_unmetered_m3: Billed unmetered (flat-rate) consumption
            unbilled_metered_m3: Unbilled metered (utility use)
            unbilled_unmetered_m3: Unbilled unmetered (firefighting, etc.)
            metered_customer_count: Number of metered customers
            unmetered_customer_count: Number of unmetered customers
            revenue_usd: Total revenue (optional)
            tariff_usd_per_m3: Average tariff (optional)
            
        Returns:
            Created BillingRecord
        """
        record_id = f"BILL-{uuid.uuid4().hex[:12].upper()}"
        
        record = BillingRecord(
            record_id=record_id,
            dma_id=dma_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            billed_metered_m3=billed_metered_m3,
            billed_unmetered_m3=billed_unmetered_m3,
            unbilled_metered_m3=unbilled_metered_m3,
            unbilled_unmetered_m3=unbilled_unmetered_m3,
            metered_customer_count=metered_customer_count,
            unmetered_customer_count=unmetered_customer_count,
            revenue_usd=revenue_usd,
            tariff_usd_per_m3=tariff_usd_per_m3
        )
        
        self._billing_records.append(record)
        self._save_to_storage()
        
        logger.info(f"Recorded billing for {dma_id}: {record.total_authorized_m3:.1f} m³")
        return record
    
    # =========================================================================
    # DATA RETRIEVAL - CORE FUNCTIONS FOR NRW CALCULATION
    # =========================================================================
    
    def get_siv(
        self,
        start_date: datetime,
        end_date: datetime,
        source_id: Optional[str] = None,
        utility_id: Optional[str] = None,
        aggregation: str = "daily"
    ) -> SIVAggregation:
        """
        Get System Input Volume for a time period.
        
        This is the primary function for NRW calculation.
        
        Args:
            start_date: Start of period (UTC)
            end_date: End of period (UTC)
            source_id: Specific source (optional, defaults to all)
            utility_id: Filter by utility
            aggregation: 'hourly', 'daily', 'monthly', 'total'
            
        Returns:
            SIVAggregation with total volumes
        """
        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Filter records
        records = [
            r for r in self._siv_records
            if start_date <= r.timestamp <= end_date
        ]
        
        if source_id:
            records = [r for r in records if r.source_id == source_id]
        
        if utility_id:
            source_ids = [s.source_id for s in self._sources.values() 
                         if s.utility_id == utility_id]
            records = [r for r in records if r.source_id in source_ids]
        
        # Calculate totals
        total_volume = sum(r.volume_m3 for r in records)
        estimated_volume = sum(
            r.volume_m3 for r in records 
            if r.quality in [DataQuality.ESTIMATED, DataQuality.INTERPOLATED]
        )
        
        # Calculate data completeness
        expected_hours = (end_date - start_date).total_seconds() / 3600
        actual_records = len(records)
        completeness = min(100.0, (actual_records / max(expected_hours, 1)) * 100)
        
        # Get unique sources
        source_ids = list(set(r.source_id for r in records))
        
        aggregation_result = SIVAggregation(
            aggregation_id=f"SIV-AGG-{uuid.uuid4().hex[:8]}",
            utility_id=utility_id,
            period_start=start_date,
            period_end=end_date,
            aggregation_level=aggregation,
            total_siv_m3=total_volume,
            siv_data_completeness=completeness,
            estimated_volume_m3=estimated_volume,
            source_count=len(source_ids),
            source_ids=source_ids
        )
        
        return aggregation_result
    
    def get_dma_inlet_flow(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get DMA inlet flow for a time period.
        
        This is used for DMA-level NRW calculation.
        
        Args:
            dma_id: DMA identifier
            start_date: Start of period (UTC)
            end_date: End of period (UTC)
            
        Returns:
            Dictionary with inlet flow totals and details
        """
        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Filter records
        records = [
            r for r in self._inlet_records
            if r.dma_id == dma_id and start_date <= r.timestamp <= end_date
        ]
        
        # Separate inlets and outlets
        inlet_records = [r for r in records if r.is_inlet]
        outlet_records = [r for r in records if not r.is_inlet]
        
        total_inlet_m3 = sum(r.volume_m3 for r in inlet_records)
        total_outlet_m3 = sum(r.volume_m3 for r in outlet_records)
        net_input_m3 = total_inlet_m3 - total_outlet_m3
        
        # Group by inlet point
        inlet_points = {}
        for r in inlet_records:
            if r.inlet_point_id not in inlet_points:
                inlet_points[r.inlet_point_id] = {
                    "total_m3": 0,
                    "record_count": 0,
                    "avg_flow_m3_h": 0
                }
            inlet_points[r.inlet_point_id]["total_m3"] += r.volume_m3
            inlet_points[r.inlet_point_id]["record_count"] += 1
        
        # Calculate averages
        for point_id, data in inlet_points.items():
            if data["record_count"] > 0:
                hours = (end_date - start_date).total_seconds() / 3600
                data["avg_flow_m3_h"] = data["total_m3"] / hours if hours > 0 else 0
        
        return {
            "dma_id": dma_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_inlet_m3": round(total_inlet_m3, 2),
            "total_outlet_m3": round(total_outlet_m3, 2),
            "net_input_m3": round(net_input_m3, 2),
            "inlet_record_count": len(inlet_records),
            "inlet_points": inlet_points
        }
    
    def get_billing(
        self,
        dma_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get billing/consumption data for a DMA and period.
        
        Args:
            dma_id: DMA identifier
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with billing totals
        """
        records = [
            r for r in self._billing_records
            if r.dma_id == dma_id
            and r.billing_period_start >= start_date
            and r.billing_period_end <= end_date
        ]
        
        total_billed_metered = sum(r.billed_metered_m3 for r in records)
        total_billed_unmetered = sum(r.billed_unmetered_m3 for r in records)
        total_unbilled_metered = sum(r.unbilled_metered_m3 for r in records)
        total_unbilled_unmetered = sum(r.unbilled_unmetered_m3 for r in records)
        
        return {
            "dma_id": dma_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "record_count": len(records),
            "billed_m3": {
                "metered": round(total_billed_metered, 1),
                "unmetered": round(total_billed_unmetered, 1),
                "total": round(total_billed_metered + total_billed_unmetered, 1)
            },
            "unbilled_m3": {
                "metered": round(total_unbilled_metered, 1),
                "unmetered": round(total_unbilled_unmetered, 1),
                "total": round(total_unbilled_metered + total_unbilled_unmetered, 1)
            },
            "total_authorized_m3": round(
                total_billed_metered + total_billed_unmetered + 
                total_unbilled_metered + total_unbilled_unmetered, 1
            )
        }
    
    # =========================================================================
    # TIMESTAMP ALIGNMENT
    # =========================================================================
    
    def align_timestamps(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        interval_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Align timestamps across SIV, DMA inlet, and pressure data.
        
        This ensures that all data sources are on the same time grid
        for accurate NRW calculation.
        
        Args:
            dma_id: DMA identifier
            start_date: Start of alignment period
            end_date: End of alignment period
            interval_minutes: Target time interval (default: 60 min)
            
        Returns:
            Aligned time series data
        """
        # Create time grid
        interval = timedelta(minutes=interval_minutes)
        timestamps = []
        current = start_date
        while current <= end_date:
            timestamps.append(current)
            current += interval
        
        # Get SIV data for connected sources
        connected_sources = self.list_sources(dma_id=dma_id)
        
        aligned_data = {
            "dma_id": dma_id,
            "interval_minutes": interval_minutes,
            "timestamps": [t.isoformat() for t in timestamps],
            "siv_m3": [],
            "inlet_m3": [],
            "alignment_method": TimestampAlignment.INTERPOLATED.value,
            "data_quality": {
                "siv_completeness": 0.0,
                "inlet_completeness": 0.0
            }
        }
        
        # TODO: Implement interpolation/aggregation to align data
        # For now, return placeholder structure
        
        logger.info(f"Aligned {len(timestamps)} timestamps for DMA {dma_id}")
        return aligned_data
    
    # =========================================================================
    # DATA VALIDATION
    # =========================================================================
    
    def validate_siv_record(self, record: SIVRecord) -> Tuple[bool, List[str]]:
        """
        Validate a SIV record for data quality.
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check source exists
        if record.source_id not in self._sources:
            issues.append(f"Unknown source: {record.source_id}")
        
        # Check value ranges
        if record.volume_m3 < 0:
            issues.append(f"Negative volume: {record.volume_m3}")
        
        source = self._sources.get(record.source_id)
        if source and source.max_flow_m3_hour:
            if record.flow_rate_m3_hour and record.flow_rate_m3_hour > source.max_flow_m3_hour * 1.5:
                issues.append(f"Flow rate exceeds 150% of max capacity")
        
        # Check timestamp is reasonable
        now = datetime.now(timezone.utc)
        if record.timestamp > now + timedelta(hours=1):
            issues.append(f"Timestamp in future: {record.timestamp}")
        
        if record.timestamp < now - timedelta(days=365):
            issues.append(f"Timestamp very old: {record.timestamp}")
        
        record.is_validated = len(issues) == 0
        return len(issues) == 0, issues
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def _save_to_storage(self):
        """Save data to JSON storage."""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Save sources
        sources_file = self.storage_path / "siv_sources.json"
        with open(sources_file, 'w') as f:
            json.dump(
                {sid: s.to_dict() for sid, s in self._sources.items()},
                f, indent=2, default=str
            )
        
        # Save records (limit to recent for performance)
        records_file = self.storage_path / "siv_records.json"
        recent_records = sorted(
            self._siv_records, 
            key=lambda r: r.timestamp, 
            reverse=True
        )[:10000]  # Keep last 10k records
        
        with open(records_file, 'w') as f:
            json.dump(
                [r.to_dict() for r in recent_records],
                f, indent=2, default=str
            )
    
    def _load_from_storage(self):
        """Load data from JSON storage."""
        if not self.storage_path:
            return
        
        # Load sources
        sources_file = self.storage_path / "siv_sources.json"
        if sources_file.exists():
            with open(sources_file, 'r') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    self._sources[sid] = SIVSource(
                        source_id=sdata['source_id'],
                        source_type=SIVSourceType(sdata['source_type']),
                        name=sdata['name'],
                        utility_id=sdata.get('utility_id'),
                        connected_dma_ids=sdata.get('connected_dma_ids', []),
                        is_active=sdata.get('is_active', True)
                    )
        
        logger.info(f"Loaded {len(self._sources)} SIV sources from storage")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def convert_flow_unit(value: float, from_unit: FlowUnit, to_unit: FlowUnit) -> float:
    """
    Convert between flow units.
    
    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit
        
    Returns:
        Converted value
    """
    # Convert to m³/h first
    to_m3_h = {
        FlowUnit.M3_PER_HOUR: 1.0,
        FlowUnit.M3_PER_DAY: 1.0 / 24.0,
        FlowUnit.L_PER_SEC: 3.6,
        FlowUnit.ML_PER_DAY: 1000.0 / 24.0
    }
    
    # Convert from m³/h to target
    from_m3_h = {
        FlowUnit.M3_PER_HOUR: 1.0,
        FlowUnit.M3_PER_DAY: 24.0,
        FlowUnit.L_PER_SEC: 1.0 / 3.6,
        FlowUnit.ML_PER_DAY: 24.0 / 1000.0
    }
    
    m3_h_value = value * to_m3_h[from_unit]
    return m3_h_value * from_m3_h[to_unit]


def estimate_unbilled_unmetered(
    population: int,
    firefighting_events: int = 0,
    flushing_hours: float = 0,
    days: int = 30
) -> float:
    """
    Estimate unbilled unmetered consumption.
    
    Based on IWA guidelines for typical unbilled uses:
    - Firefighting: ~500 m³ per event average
    - Main flushing: ~50 m³/hour
    - Street cleaning: ~5 L/capita/month
    - Public fountains: varies
    
    Args:
        population: Population served
        firefighting_events: Number of firefighting events
        flushing_hours: Hours of main flushing
        days: Number of days in period
        
    Returns:
        Estimated unbilled unmetered consumption (m³)
    """
    firefighting_m3 = firefighting_events * 500  # 500 m³/event average
    flushing_m3 = flushing_hours * 50  # 50 m³/hour
    street_cleaning_m3 = population * 0.005 * (days / 30)  # 5 L/capita/month
    
    return firefighting_m3 + flushing_m3 + street_cleaning_m3


# =============================================================================
# EXAMPLE USAGE / TESTING
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create SIV Manager
    manager = SIVManager(utility_timezone="Africa/Lusaka")
    
    # Register a treatment plant
    source = manager.register_source(
        source_type=SIVSourceType.TREATMENT_PLANT,
        name="Kafue Treatment Works",
        connected_dma_ids=["DMA-MATERO", "DMA-CHILENJE"],
        design_capacity_m3_day=120000,
        latitude=-15.4178,
        longitude=28.3228,
        utility_id="LWSC"
    )
    print(f"Registered source: {source.source_id}")
    
    # Ingest some SIV data
    now = datetime.now(timezone.utc)
    for hour in range(24):
        timestamp = now - timedelta(hours=24-hour)
        flow_rate = 4500 + 500 * (1 + 0.3 * abs(hour - 12) / 12)  # Varies by time of day
        
        manager.ingest_siv(
            source_id=source.source_id,
            timestamp=timestamp,
            value=flow_rate,
            unit=FlowUnit.M3_PER_HOUR,
            is_volume=False
        )
    
    # Get SIV for period
    start = now - timedelta(hours=24)
    end = now
    
    siv_data = manager.get_siv(start, end)
    print(f"\nSIV Summary:")
    print(f"  Period: {siv_data.period_start} to {siv_data.period_end}")
    print(f"  Total Volume: {siv_data.total_siv_m3:,.0f} m³")
    print(f"  Data Completeness: {siv_data.siv_data_completeness:.1f}%")
    
    # Record billing data
    billing = manager.record_billing(
        dma_id="DMA-MATERO",
        billing_period_start=date(2026, 1, 1),
        billing_period_end=date(2026, 1, 31),
        billed_metered_m3=45000,
        billed_unmetered_m3=5000,
        unbilled_metered_m3=500,
        unbilled_unmetered_m3=1000,
        metered_customer_count=8500,
        unmetered_customer_count=1500
    )
    
    print(f"\nBilling Record:")
    print(f"  Total Authorized: {billing.total_authorized_m3:,.0f} m³")
    print(f"  Billed: {billing.total_billed_m3:,.0f} m³")
    print(f"  Unbilled: {billing.total_unbilled_m3:,.0f} m³")
