"""
AquaWatch Smart Meter Integration (AMI)
=======================================
Advanced Metering Infrastructure integration for consumption analytics,
leak detection at customer level, and revenue protection.

Features:
- Smart meter data collection and processing
- Consumption pattern analysis
- Customer-level leak detection
- Demand forecasting
- Revenue protection (theft detection)
- Real-time billing integration
- District Metered Area (DMA) analytics
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from collections import defaultdict
import uuid


class MeterType(Enum):
    """Types of smart meters"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    BULK = "bulk"
    DMA_INLET = "dma_inlet"
    DMA_OUTLET = "dma_outlet"
    FIRE_SERVICE = "fire_service"


class MeterStatus(Enum):
    """Meter operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAULTY = "faulty"
    TAMPERED = "tampered"
    MAINTENANCE = "maintenance"
    DISCONNECTED = "disconnected"


class AlertType(Enum):
    """Types of meter alerts"""
    HIGH_CONSUMPTION = "high_consumption"
    LOW_CONSUMPTION = "low_consumption"
    CONTINUOUS_FLOW = "continuous_flow"
    REVERSE_FLOW = "reverse_flow"
    METER_STOPPED = "meter_stopped"
    TAMPER_DETECTED = "tamper_detected"
    LEAK_SUSPECTED = "leak_suspected"
    BURST_SUSPECTED = "burst_suspected"
    BATTERY_LOW = "battery_low"
    COMMUNICATION_LOSS = "communication_loss"


@dataclass
class SmartMeter:
    """Represents a smart water meter"""
    meter_id: str
    serial_number: str
    meter_type: MeterType
    customer_id: str
    
    # Location
    latitude: float
    longitude: float
    zone_id: str
    dma_id: str
    address: str
    
    # Technical specs
    size_mm: int = 15  # DN15 typical residential
    max_flow_lph: float = 3000  # liters per hour
    min_flow_lph: float = 10
    accuracy_class: str = "B"  # ISO 4064
    
    # Communication
    protocol: str = "NB-IoT"  # NB-IoT, LoRa, GSM
    transmission_interval: int = 15  # minutes
    last_transmission: Optional[datetime] = None
    signal_strength: int = -70  # dBm
    
    # Status
    status: MeterStatus = MeterStatus.ACTIVE
    installed_date: datetime = field(default_factory=datetime.now)
    battery_level: float = 100.0
    
    # Readings
    current_reading: float = 0.0  # m³
    previous_reading: float = 0.0
    monthly_consumption: float = 0.0
    
    # Billing
    tariff_category: str = "domestic"
    account_balance: float = 0.0


@dataclass
class MeterReading:
    """Individual meter reading"""
    reading_id: str
    meter_id: str
    timestamp: datetime
    
    # Reading values
    cumulative_volume: float  # m³
    flow_rate: float  # L/hour (instantaneous)
    
    # Quality indicators
    signal_quality: int  # 0-100
    battery_level: float
    
    # Flags
    reverse_flow: bool = False
    tamper_detected: bool = False
    leak_flag: bool = False
    
    # Calculated
    consumption_since_last: float = 0.0  # m³


@dataclass
class ConsumptionProfile:
    """Customer consumption profile"""
    customer_id: str
    meter_id: str
    profile_type: str  # residential, commercial, industrial
    
    # Usage patterns
    avg_daily_consumption: float  # m³
    avg_monthly_consumption: float
    peak_hour: int  # 0-23
    peak_day: int  # 0-6 (Monday=0)
    
    # Baseline
    weekday_pattern: List[float] = field(default_factory=list)  # 24 hourly values
    weekend_pattern: List[float] = field(default_factory=list)
    seasonal_factors: Dict[str, float] = field(default_factory=dict)
    
    # Anomaly thresholds
    high_threshold: float = 0.0  # m³/day
    low_threshold: float = 0.0
    night_flow_threshold: float = 0.0  # L/hour


class SmartMeterAnalytics:
    """Analytics engine for smart meter data"""
    
    def __init__(self):
        # Typical consumption patterns by customer type (hourly multipliers)
        self.typical_patterns = {
            "residential": [
                0.3, 0.2, 0.2, 0.2, 0.3, 0.5,  # 00-05
                0.9, 1.4, 1.2, 0.8, 0.6, 0.7,  # 06-11
                0.9, 0.7, 0.6, 0.6, 0.7, 1.0,  # 12-17
                1.3, 1.2, 1.0, 0.8, 0.5, 0.4   # 18-23
            ],
            "commercial": [
                0.1, 0.1, 0.1, 0.1, 0.1, 0.2,  # 00-05
                0.5, 1.0, 1.4, 1.5, 1.4, 1.3,  # 06-11
                1.2, 1.3, 1.4, 1.3, 1.2, 1.0,  # 12-17
                0.5, 0.2, 0.1, 0.1, 0.1, 0.1   # 18-23
            ],
            "industrial": [
                0.8, 0.8, 0.8, 0.8, 0.8, 0.9,  # 00-05
                1.0, 1.2, 1.3, 1.3, 1.3, 1.2,  # 06-11
                1.0, 1.2, 1.3, 1.3, 1.2, 1.0,  # 12-17
                0.9, 0.8, 0.8, 0.8, 0.8, 0.8   # 18-23
            ]
        }
        
        # Seasonal factors for Zambia
        self.seasonal_factors = {
            "hot_dry": 1.3,      # September-November
            "rainy": 0.9,        # December-March
            "cold_dry": 1.0,     # April-May
            "cool_dry": 1.1      # June-August
        }
    
    def create_consumption_profile(
        self,
        meter: SmartMeter,
        historical_readings: List[MeterReading]
    ) -> ConsumptionProfile:
        """
        Create consumption profile from historical data.
        
        Args:
            meter: Smart meter object
            historical_readings: List of historical readings
        
        Returns:
            ConsumptionProfile for the customer
        """
        if len(historical_readings) < 24:  # Need at least 24 hours of data
            # Use typical patterns
            profile_type = meter.meter_type.value
            if profile_type not in self.typical_patterns:
                profile_type = "residential"
            
            avg_daily = 0.5 if meter.meter_type == MeterType.RESIDENTIAL else 5.0
            
            return ConsumptionProfile(
                customer_id=meter.customer_id,
                meter_id=meter.meter_id,
                profile_type=profile_type,
                avg_daily_consumption=avg_daily,
                avg_monthly_consumption=avg_daily * 30,
                peak_hour=7,
                peak_day=6,  # Saturday
                weekday_pattern=self.typical_patterns[profile_type],
                weekend_pattern=[p * 1.2 for p in self.typical_patterns[profile_type]],
                seasonal_factors=self.seasonal_factors,
                high_threshold=avg_daily * 2.0,
                low_threshold=avg_daily * 0.1,
                night_flow_threshold=20.0  # L/hour
            )
        
        # Calculate from actual data
        hourly_consumption = defaultdict(list)
        daily_consumption = defaultdict(float)
        
        for reading in sorted(historical_readings, key=lambda r: r.timestamp):
            hour = reading.timestamp.hour
            date = reading.timestamp.date()
            
            hourly_consumption[hour].append(reading.flow_rate)
            daily_consumption[date] += reading.consumption_since_last * 1000  # m³ to L
        
        # Calculate averages
        weekday_pattern = []
        for hour in range(24):
            if hourly_consumption[hour]:
                weekday_pattern.append(np.mean(hourly_consumption[hour]))
            else:
                weekday_pattern.append(self.typical_patterns["residential"][hour] * 100)
        
        # Normalize
        pattern_sum = sum(weekday_pattern)
        if pattern_sum > 0:
            weekday_pattern = [p / pattern_sum * 24 for p in weekday_pattern]
        
        # Find peak hour
        peak_hour = int(np.argmax(weekday_pattern))
        
        # Calculate daily average
        daily_values = list(daily_consumption.values())
        avg_daily = np.mean(daily_values) / 1000 if daily_values else 0.5  # Convert to m³
        
        return ConsumptionProfile(
            customer_id=meter.customer_id,
            meter_id=meter.meter_id,
            profile_type=meter.meter_type.value,
            avg_daily_consumption=avg_daily,
            avg_monthly_consumption=avg_daily * 30,
            peak_hour=peak_hour,
            peak_day=5,  # Friday typically
            weekday_pattern=weekday_pattern,
            weekend_pattern=[p * 1.15 for p in weekday_pattern],
            seasonal_factors=self.seasonal_factors,
            high_threshold=avg_daily * 2.5,
            low_threshold=avg_daily * 0.05,
            night_flow_threshold=max(10, avg_daily * 50)  # L/hour
        )
    
    def detect_anomalies(
        self,
        reading: MeterReading,
        profile: ConsumptionProfile
    ) -> List[Dict]:
        """
        Detect consumption anomalies.
        
        Args:
            reading: Current meter reading
            profile: Customer's consumption profile
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        hour = reading.timestamp.hour
        is_weekend = reading.timestamp.weekday() >= 5
        
        # Get expected consumption
        pattern = profile.weekend_pattern if is_weekend else profile.weekday_pattern
        expected_flow = pattern[hour] * profile.avg_daily_consumption * 1000 / 24  # L/hour
        
        # High consumption check
        if reading.flow_rate > expected_flow * 3:
            anomalies.append({
                "type": AlertType.HIGH_CONSUMPTION.value,
                "severity": "high" if reading.flow_rate > expected_flow * 5 else "medium",
                "message": f"High consumption: {reading.flow_rate:.1f} L/hr (expected: {expected_flow:.1f})",
                "value": reading.flow_rate,
                "expected": expected_flow
            })
        
        # Continuous night flow (potential leak)
        if 0 <= hour <= 5 and reading.flow_rate > profile.night_flow_threshold:
            anomalies.append({
                "type": AlertType.CONTINUOUS_FLOW.value,
                "severity": "high",
                "message": f"Continuous night flow: {reading.flow_rate:.1f} L/hr",
                "value": reading.flow_rate,
                "threshold": profile.night_flow_threshold
            })
        
        # Reverse flow
        if reading.reverse_flow:
            anomalies.append({
                "type": AlertType.REVERSE_FLOW.value,
                "severity": "critical",
                "message": "Reverse flow detected - possible illegal connection",
                "value": reading.flow_rate
            })
        
        # Tamper detection
        if reading.tamper_detected:
            anomalies.append({
                "type": AlertType.TAMPER_DETECTED.value,
                "severity": "critical",
                "message": "Meter tampering detected",
                "value": None
            })
        
        # Zero flow for extended period (meter stopped)
        if reading.flow_rate == 0 and expected_flow > 10:
            anomalies.append({
                "type": AlertType.METER_STOPPED.value,
                "severity": "medium",
                "message": "No flow detected during expected usage period",
                "value": 0,
                "expected": expected_flow
            })
        
        # Low battery
        if reading.battery_level < 20:
            anomalies.append({
                "type": AlertType.BATTERY_LOW.value,
                "severity": "low",
                "message": f"Low battery: {reading.battery_level:.0f}%",
                "value": reading.battery_level
            })
        
        return anomalies
    
    def calculate_dma_balance(
        self,
        dma_id: str,
        inlet_readings: List[MeterReading],
        outlet_readings: List[MeterReading],
        customer_readings: List[MeterReading]
    ) -> Dict:
        """
        Calculate DMA water balance.
        
        Args:
            dma_id: District Metered Area ID
            inlet_readings: Readings from DMA inlet meters
            outlet_readings: Readings from DMA outlet meters
            customer_readings: Readings from customer meters in DMA
        
        Returns:
            Water balance analysis
        """
        # Calculate total input
        total_input = sum(r.consumption_since_last for r in inlet_readings)
        
        # Calculate total output (to other DMAs)
        total_output = sum(r.consumption_since_last for r in outlet_readings)
        
        # Calculate total consumption
        total_consumption = sum(r.consumption_since_last for r in customer_readings)
        
        # Net input
        net_input = total_input - total_output
        
        # Unaccounted for water (NRW)
        unaccounted = net_input - total_consumption
        nrw_percentage = (unaccounted / net_input * 100) if net_input > 0 else 0
        
        # Calculate Minimum Night Flow (MNF)
        night_readings = [r for r in inlet_readings if 2 <= r.timestamp.hour <= 4]
        if night_readings:
            mnf = min(r.flow_rate for r in night_readings)
        else:
            mnf = 0
        
        # Estimate leakage from MNF
        # Typical legitimate night use is 6-10% of average day flow
        avg_day_flow = net_input / 24 if net_input > 0 else 0
        legitimate_night_use = avg_day_flow * 0.08
        estimated_leakage_flow = max(0, mnf - legitimate_night_use)
        estimated_daily_leakage = estimated_leakage_flow * 24  # m³/day
        
        return {
            "dma_id": dma_id,
            "period": {
                "start": min(r.timestamp for r in inlet_readings).isoformat() if inlet_readings else None,
                "end": max(r.timestamp for r in inlet_readings).isoformat() if inlet_readings else None
            },
            "water_balance": {
                "total_input_m3": total_input,
                "total_output_m3": total_output,
                "net_input_m3": net_input,
                "billed_consumption_m3": total_consumption,
                "unaccounted_m3": unaccounted,
                "nrw_percentage": nrw_percentage
            },
            "minimum_night_flow": {
                "mnf_lph": mnf,
                "legitimate_night_use_lph": legitimate_night_use,
                "estimated_leakage_lph": estimated_leakage_flow,
                "estimated_daily_leakage_m3": estimated_daily_leakage
            },
            "performance": {
                "status": "good" if nrw_percentage < 20 else "concern" if nrw_percentage < 35 else "poor",
                "nrw_target": 20,  # Target NRW percentage
                "improvement_needed": max(0, nrw_percentage - 20)
            }
        }


class SmartMeterManager:
    """
    Central manager for smart meter infrastructure.
    """
    
    def __init__(self):
        self.meters: Dict[str, SmartMeter] = {}
        self.readings: Dict[str, List[MeterReading]] = defaultdict(list)
        self.profiles: Dict[str, ConsumptionProfile] = {}
        self.alerts: List[Dict] = []
        self.analytics = SmartMeterAnalytics()
        
        # DMA tracking
        self.dmas: Dict[str, Dict] = {}
        
        # Initialize demo data
        self._initialize_demo_meters()
    
    def _initialize_demo_meters(self):
        """Initialize demo smart meters"""
        # Define DMAs for Lusaka
        dma_definitions = {
            "DMA_CBD": {"name": "CBD District", "zone": "ZONE_CBD", "customers": 1200},
            "DMA_KABULONGA": {"name": "Kabulonga District", "zone": "ZONE_KABULONGA", "customers": 800},
            "DMA_WOODLANDS": {"name": "Woodlands District", "zone": "ZONE_WOODLANDS", "customers": 1500},
            "DMA_KABWATA": {"name": "Kabwata District", "zone": "ZONE_KABWATA", "customers": 2000},
            "DMA_MATERO": {"name": "Matero District", "zone": "ZONE_MATERO", "customers": 3000},
            "DMA_INDUSTRIAL": {"name": "Industrial Area", "zone": "ZONE_INDUSTRIAL", "customers": 150}
        }
        
        self.dmas = dma_definitions
        
        # Create sample meters for each DMA
        meter_configs = [
            # DMA Inlet/Outlet meters
            ("DMA_IN_CBD", "CBD Inlet", MeterType.DMA_INLET, "DMA_CBD", -15.4167, 28.2833, 150),
            ("DMA_OUT_CBD", "CBD Outlet", MeterType.DMA_OUTLET, "DMA_CBD", -15.4200, 28.2800, 100),
            ("DMA_IN_KAB", "Kabulonga Inlet", MeterType.DMA_INLET, "DMA_KABULONGA", -15.3958, 28.3208, 150),
            ("DMA_IN_WOOD", "Woodlands Inlet", MeterType.DMA_INLET, "DMA_WOODLANDS", -15.4250, 28.3083, 150),
            
            # Sample residential meters
            ("MTR_RES_001", "Plot 123 Kabulonga", MeterType.RESIDENTIAL, "DMA_KABULONGA", -15.3970, 28.3190, 15),
            ("MTR_RES_002", "Plot 45 Woodlands", MeterType.RESIDENTIAL, "DMA_WOODLANDS", -15.4260, 28.3070, 15),
            ("MTR_RES_003", "House 78 Kabwata", MeterType.RESIDENTIAL, "DMA_KABWATA", -15.4380, 28.2910, 15),
            ("MTR_RES_004", "Stand 234 Matero", MeterType.RESIDENTIAL, "DMA_MATERO", -15.3840, 28.2550, 15),
            
            # Commercial meters
            ("MTR_COM_001", "Manda Hill Shopping", MeterType.COMMERCIAL, "DMA_KABULONGA", -15.4000, 28.3150, 50),
            ("MTR_COM_002", "Levy Junction", MeterType.COMMERCIAL, "DMA_CBD", -15.4150, 28.2850, 50),
            ("MTR_COM_003", "EastPark Mall", MeterType.COMMERCIAL, "DMA_CBD", -15.4100, 28.2900, 50),
            
            # Industrial meters
            ("MTR_IND_001", "Zambia Breweries", MeterType.INDUSTRIAL, "DMA_INDUSTRIAL", -15.4400, 28.2620, 200),
            ("MTR_IND_002", "Trade Kings", MeterType.INDUSTRIAL, "DMA_INDUSTRIAL", -15.4420, 28.2640, 150),
        ]
        
        for config in meter_configs:
            meter_id, name, mtype, dma, lat, lon, size = config
            
            meter = SmartMeter(
                meter_id=meter_id,
                serial_number=f"ZM{meter_id[-6:].replace('_', '')}",
                meter_type=mtype,
                customer_id=f"CUST_{meter_id}",
                latitude=lat,
                longitude=lon,
                zone_id=self.dmas[dma]["zone"],
                dma_id=dma,
                address=name,
                size_mm=size,
                protocol="NB-IoT" if mtype in [MeterType.RESIDENTIAL, MeterType.COMMERCIAL] else "GSM",
                tariff_category="domestic" if mtype == MeterType.RESIDENTIAL else "commercial" if mtype == MeterType.COMMERCIAL else "industrial"
            )
            
            self.meters[meter_id] = meter
            
            # Create profile
            self.profiles[meter_id] = self.analytics.create_consumption_profile(meter, [])
    
    def record_reading(self, meter_id: str, reading_data: Dict) -> MeterReading:
        """
        Record a new meter reading.
        
        Args:
            meter_id: Meter ID
            reading_data: Reading data dictionary
        
        Returns:
            Created MeterReading object
        """
        if meter_id not in self.meters:
            raise ValueError(f"Unknown meter: {meter_id}")
        
        meter = self.meters[meter_id]
        
        # Get previous reading for consumption calculation
        previous_readings = self.readings[meter_id]
        if previous_readings:
            last_reading = previous_readings[-1]
            consumption = reading_data.get("cumulative_volume", 0) - last_reading.cumulative_volume
        else:
            consumption = 0
        
        reading = MeterReading(
            reading_id=f"RDG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{meter_id}",
            meter_id=meter_id,
            timestamp=reading_data.get("timestamp", datetime.now()),
            cumulative_volume=reading_data.get("cumulative_volume", meter.current_reading),
            flow_rate=reading_data.get("flow_rate", 0),
            signal_quality=reading_data.get("signal_quality", 80),
            battery_level=reading_data.get("battery_level", meter.battery_level),
            reverse_flow=reading_data.get("reverse_flow", False),
            tamper_detected=reading_data.get("tamper_detected", False),
            leak_flag=reading_data.get("leak_flag", False),
            consumption_since_last=max(0, consumption)
        )
        
        # Store reading
        self.readings[meter_id].append(reading)
        
        # Update meter state
        meter.current_reading = reading.cumulative_volume
        meter.last_transmission = reading.timestamp
        meter.battery_level = reading.battery_level
        meter.signal_strength = -100 + reading.signal_quality  # Approximate dBm
        
        # Check for anomalies
        if meter_id in self.profiles:
            anomalies = self.analytics.detect_anomalies(reading, self.profiles[meter_id])
            for anomaly in anomalies:
                self.alerts.append({
                    "alert_id": f"ALT_{uuid.uuid4().hex[:8]}",
                    "meter_id": meter_id,
                    "timestamp": reading.timestamp.isoformat(),
                    **anomaly
                })
        
        return reading
    
    def get_customer_dashboard(self, customer_id: str) -> Dict:
        """
        Get customer dashboard data.
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Dashboard data dictionary
        """
        # Find customer's meter(s)
        customer_meters = [
            m for m in self.meters.values()
            if m.customer_id == customer_id
        ]
        
        if not customer_meters:
            return {"error": "Customer not found"}
        
        meter = customer_meters[0]  # Primary meter
        meter_readings = self.readings.get(meter.meter_id, [])
        
        # Calculate usage stats
        if meter_readings:
            recent_readings = meter_readings[-720:]  # Last 30 days at 1hr intervals
            
            # Daily consumption for last 7 days
            daily_consumption = defaultdict(float)
            for reading in recent_readings:
                date_key = reading.timestamp.date().isoformat()
                daily_consumption[date_key] += reading.consumption_since_last
            
            # Today's consumption
            today = datetime.now().date().isoformat()
            today_consumption = daily_consumption.get(today, 0)
            
            # This month's consumption
            month_start = datetime.now().replace(day=1).date()
            monthly_consumption = sum(
                v for k, v in daily_consumption.items()
                if datetime.fromisoformat(k).date() >= month_start
            )
            
            # Average daily
            avg_daily = np.mean(list(daily_consumption.values())) if daily_consumption else 0
        else:
            today_consumption = 0
            monthly_consumption = 0
            avg_daily = 0
            daily_consumption = {}
        
        # Get profile
        profile = self.profiles.get(meter.meter_id)
        
        # Calculate bill estimate
        tariff_rates = {
            "domestic": 5.50,      # ZMW per m³
            "commercial": 8.00,
            "industrial": 6.50
        }
        rate = tariff_rates.get(meter.tariff_category, 5.50)
        estimated_bill = monthly_consumption * rate
        
        # Check for alerts
        customer_alerts = [
            a for a in self.alerts
            if a["meter_id"] == meter.meter_id
        ][-5:]  # Last 5 alerts
        
        return {
            "customer_id": customer_id,
            "meter_id": meter.meter_id,
            "address": meter.address,
            "meter_status": meter.status.value,
            "current_reading": meter.current_reading,
            "consumption": {
                "today_m3": today_consumption,
                "month_m3": monthly_consumption,
                "avg_daily_m3": avg_daily,
                "daily_history": dict(list(daily_consumption.items())[-7:])
            },
            "billing": {
                "tariff_category": meter.tariff_category,
                "rate_per_m3": rate,
                "estimated_bill_zmw": estimated_bill,
                "account_balance_zmw": meter.account_balance
            },
            "meter_health": {
                "battery_level": meter.battery_level,
                "signal_strength": meter.signal_strength,
                "last_reading": meter.last_transmission.isoformat() if meter.last_transmission else None
            },
            "alerts": customer_alerts,
            "tips": self._get_water_saving_tips(avg_daily, profile)
        }
    
    def _get_water_saving_tips(self, avg_daily: float, profile: Optional[ConsumptionProfile]) -> List[str]:
        """Generate water saving tips based on consumption"""
        tips = []
        
        if avg_daily > 1.0:
            tips.append("Consider installing water-efficient showerheads to reduce consumption")
        if avg_daily > 0.8:
            tips.append("Check for running toilets - they can waste up to 200 liters per day")
        if avg_daily > 0.5:
            tips.append("Collect rainwater for garden irrigation during the rainy season")
        
        if profile and profile.night_flow_threshold < 50:
            tips.append("Your night usage is low - great job! Continue monitoring for leaks")
        
        tips.append("Report any visible leaks to help reduce water losses")
        
        return tips[:3]  # Return top 3 tips
    
    def get_dma_summary(self, dma_id: str) -> Dict:
        """
        Get DMA performance summary.
        
        Args:
            dma_id: DMA ID
        
        Returns:
            DMA summary dictionary
        """
        if dma_id not in self.dmas:
            return {"error": "DMA not found"}
        
        dma_info = self.dmas[dma_id]
        
        # Get meters in this DMA
        dma_meters = [m for m in self.meters.values() if m.dma_id == dma_id]
        
        # Separate by type
        inlet_meters = [m for m in dma_meters if m.meter_type == MeterType.DMA_INLET]
        outlet_meters = [m for m in dma_meters if m.meter_type == MeterType.DMA_OUTLET]
        customer_meters = [m for m in dma_meters if m.meter_type not in [MeterType.DMA_INLET, MeterType.DMA_OUTLET]]
        
        # Get recent readings
        inlet_readings = []
        outlet_readings = []
        customer_readings = []
        
        for meter in inlet_meters:
            inlet_readings.extend(self.readings.get(meter.meter_id, [])[-24:])
        for meter in outlet_meters:
            outlet_readings.extend(self.readings.get(meter.meter_id, [])[-24:])
        for meter in customer_meters:
            customer_readings.extend(self.readings.get(meter.meter_id, [])[-24:])
        
        # Calculate water balance
        balance = self.analytics.calculate_dma_balance(
            dma_id, inlet_readings, outlet_readings, customer_readings
        )
        
        # Count alerts
        dma_meter_ids = [m.meter_id for m in dma_meters]
        recent_alerts = [
            a for a in self.alerts
            if a["meter_id"] in dma_meter_ids
        ]
        
        return {
            "dma_id": dma_id,
            "name": dma_info["name"],
            "zone": dma_info["zone"],
            "statistics": {
                "total_meters": len(dma_meters),
                "inlet_meters": len(inlet_meters),
                "customer_meters": len(customer_meters),
                "registered_customers": dma_info["customers"]
            },
            "water_balance": balance["water_balance"],
            "night_flow_analysis": balance["minimum_night_flow"],
            "performance": balance["performance"],
            "alerts": {
                "total_today": len([a for a in recent_alerts if datetime.fromisoformat(a["timestamp"]).date() == datetime.now().date()]),
                "critical": len([a for a in recent_alerts if a.get("severity") == "critical"]),
                "recent": recent_alerts[-5:]
            },
            "meter_health": {
                "active": len([m for m in dma_meters if m.status == MeterStatus.ACTIVE]),
                "faulty": len([m for m in dma_meters if m.status == MeterStatus.FAULTY]),
                "low_battery": len([m for m in dma_meters if m.battery_level < 20])
            }
        }
    
    def get_system_dashboard(self) -> Dict:
        """Get overall smart meter system dashboard"""
        total_meters = len(self.meters)
        
        by_type = defaultdict(int)
        by_status = defaultdict(int)
        low_battery_count = 0
        
        for meter in self.meters.values():
            by_type[meter.meter_type.value] += 1
            by_status[meter.status.value] += 1
            if meter.battery_level < 20:
                low_battery_count += 1
        
        # Today's alerts
        today = datetime.now().date()
        today_alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a["timestamp"]).date() == today
        ]
        
        # Critical alerts
        critical_alerts = [a for a in today_alerts if a.get("severity") == "critical"]
        
        return {
            "system_overview": {
                "total_meters": total_meters,
                "meters_by_type": dict(by_type),
                "meters_by_status": dict(by_status),
                "total_dmas": len(self.dmas),
                "total_readings_today": sum(
                    len([r for r in readings if r.timestamp.date() == today])
                    for readings in self.readings.values()
                )
            },
            "health": {
                "active_meters": by_status.get("active", 0),
                "faulty_meters": by_status.get("faulty", 0),
                "low_battery_meters": low_battery_count,
                "communication_issues": by_status.get("inactive", 0)
            },
            "alerts": {
                "total_today": len(today_alerts),
                "critical": len(critical_alerts),
                "by_type": dict(defaultdict(int, {a["type"]: 1 for a in today_alerts}))
            },
            "dma_summaries": [
                {
                    "dma_id": dma_id,
                    "name": info["name"],
                    "customers": info["customers"]
                }
                for dma_id, info in self.dmas.items()
            ]
        }


# Global instance
smart_meter_manager = SmartMeterManager()


def get_smart_meter_manager() -> SmartMeterManager:
    """Get the global smart meter manager"""
    return smart_meter_manager


if __name__ == "__main__":
    # Demo
    manager = SmartMeterManager()
    
    print("=" * 60)
    print("AquaWatch Smart Meter Integration (AMI)")
    print("=" * 60)
    
    # System overview
    dashboard = manager.get_system_dashboard()
    print(f"\nSystem Overview:")
    print(f"  Total Meters: {dashboard['system_overview']['total_meters']}")
    print(f"  Total DMAs: {dashboard['system_overview']['total_dmas']}")
    print(f"  Meters by Type: {dashboard['system_overview']['meters_by_type']}")
    
    # Simulate some readings
    print("\nSimulating meter readings...")
    
    for meter_id in list(manager.meters.keys())[:5]:
        meter = manager.meters[meter_id]
        
        # Simulate reading
        reading = manager.record_reading(meter_id, {
            "cumulative_volume": meter.current_reading + np.random.uniform(0.01, 0.5),
            "flow_rate": np.random.uniform(10, 200),
            "signal_quality": np.random.randint(60, 100),
            "battery_level": meter.battery_level - np.random.uniform(0, 0.1)
        })
        
        print(f"  {meter_id}: {reading.flow_rate:.1f} L/hr, Total: {reading.cumulative_volume:.2f} m³")
    
    # DMA Summary
    print(f"\nDMA Summary (DMA_KABULONGA):")
    dma_summary = manager.get_dma_summary("DMA_KABULONGA")
    print(f"  Total Meters: {dma_summary['statistics']['total_meters']}")
    print(f"  Registered Customers: {dma_summary['statistics']['registered_customers']}")
    
    # Customer Dashboard
    print(f"\nCustomer Dashboard:")
    customer_dash = manager.get_customer_dashboard("CUST_MTR_RES_001")
    print(f"  Address: {customer_dash['address']}")
    print(f"  Today's Consumption: {customer_dash['consumption']['today_m3']:.3f} m³")
    print(f"  Estimated Bill: ZMW {customer_dash['billing']['estimated_bill_zmw']:.2f}")
