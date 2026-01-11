"""
AquaWatch NRW - Work Order Management System
============================================

Complete work order lifecycle management for water utility field operations.

Features:
- Automatic work order generation from alerts
- Assignment to technicians by zone/skill
- Mobile-optimized tracking
- Parts inventory integration
- Photo evidence and sign-off
- SLA tracking and escalation
- Analytics and reporting

Designed for Zambia/South Africa water utilities.
"""

import os
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# WORK ORDER TYPES & STATUSES
# =============================================================================

class WorkOrderType(Enum):
    LEAK_REPAIR = "leak_repair"
    BURST_REPAIR = "burst_repair"
    METER_INSTALLATION = "meter_installation"
    METER_REPAIR = "meter_repair"
    METER_REPLACEMENT = "meter_replacement"
    VALVE_MAINTENANCE = "valve_maintenance"
    PIPE_REPLACEMENT = "pipe_replacement"
    PRESSURE_CHECK = "pressure_check"
    WATER_QUALITY_TEST = "water_quality_test"
    CUSTOMER_COMPLAINT = "customer_complaint"
    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    INSPECTION = "inspection"
    NEW_CONNECTION = "new_connection"
    DISCONNECTION = "disconnection"
    RECONNECTION = "reconnection"


class WorkOrderStatus(Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PARTS_NEEDED = "parts_needed"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class Priority(Enum):
    EMERGENCY = 1      # Respond within 1 hour
    URGENT = 2         # Respond within 4 hours
    HIGH = 3           # Respond within 24 hours
    NORMAL = 4         # Respond within 48 hours
    LOW = 5            # Schedule within 1 week


class SkillLevel(Enum):
    BASIC = "basic"           # Meter reading, inspections
    INTERMEDIATE = "intermediate"  # Minor repairs, installations
    ADVANCED = "advanced"     # Major repairs, complex work
    SPECIALIST = "specialist" # Specialized equipment/conditions


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Location:
    """Geographic location with address."""
    latitude: float
    longitude: float
    address: str = ""
    zone_id: str = ""
    dma_id: str = ""
    landmark: str = ""  # Helpful in areas without formal addresses


@dataclass
class Part:
    """Part/material used in work order."""
    part_id: str
    name: str
    quantity: int
    unit: str = "each"
    unit_cost_usd: float = 0.0
    
    @property
    def total_cost(self) -> float:
        return self.quantity * self.unit_cost_usd


@dataclass
class TimeEntry:
    """Time tracking entry."""
    entry_id: str
    technician_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    activity: str = ""
    travel_km: float = 0.0
    
    @property
    def duration_hours(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return 0.0


@dataclass
class PhotoEvidence:
    """Photo evidence attached to work order."""
    photo_id: str
    url: str
    caption: str = ""
    photo_type: str = "general"  # before, during, after, asset, signature
    taken_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    taken_by: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class Technician:
    """Field technician."""
    technician_id: str
    name: str
    phone: str
    email: str = ""
    skill_level: SkillLevel = SkillLevel.BASIC
    zone_ids: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    # Status
    active: bool = True
    available: bool = True
    current_location: Optional[Location] = None
    current_work_order_id: Optional[str] = None


@dataclass
class SLAConfig:
    """Service Level Agreement configuration."""
    priority: Priority
    response_time_hours: float
    completion_time_hours: float
    escalation_levels: List[str]  # Role hierarchy for escalation


@dataclass
class WorkOrder:
    """Main work order data structure."""
    work_order_id: str
    type: WorkOrderType
    priority: Priority
    status: WorkOrderStatus
    
    # Source
    source_alert_id: Optional[str] = None
    source_type: str = "alert"  # alert, customer, inspection, scheduled
    
    # Location
    location: Optional[Location] = None
    
    # Assignment
    assigned_to: Optional[str] = None  # technician_id
    assigned_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Description
    title: str = ""
    description: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    customer_account: str = ""
    
    # Asset
    asset_id: str = ""
    asset_type: str = ""  # pipe, meter, valve, hydrant
    pipe_material: str = ""
    pipe_diameter_mm: int = 0
    
    # Work details
    parts_used: List[Part] = field(default_factory=list)
    time_entries: List[TimeEntry] = field(default_factory=list)
    photos: List[PhotoEvidence] = field(default_factory=list)
    
    # Findings
    root_cause: str = ""
    work_performed: str = ""
    recommendations: str = ""
    
    # Measurements
    flow_before_lpm: Optional[float] = None
    flow_after_lpm: Optional[float] = None
    pressure_before_bar: Optional[float] = None
    pressure_after_bar: Optional[float] = None
    water_saved_lph: Optional[float] = None  # Liters per hour saved
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: str = ""
    
    # SLA
    sla_response_deadline: Optional[datetime] = None
    sla_completion_deadline: Optional[datetime] = None
    sla_breached: bool = False
    
    # Costs
    labor_cost_usd: float = 0.0
    parts_cost_usd: float = 0.0
    other_cost_usd: float = 0.0
    
    # Notes
    internal_notes: str = ""
    customer_notes: str = ""
    
    @property
    def total_cost(self) -> float:
        return self.labor_cost_usd + self.parts_cost_usd + self.other_cost_usd
    
    @property
    def total_time_hours(self) -> float:
        return sum(t.duration_hours for t in self.time_entries)
    
    @property
    def response_time_hours(self) -> Optional[float]:
        if self.acknowledged_at:
            return (self.acknowledged_at - self.created_at).total_seconds() / 3600
        return None
    
    @property
    def completion_time_hours(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds() / 3600
        return None


# =============================================================================
# SLA CONFIGURATIONS BY PRIORITY
# =============================================================================

DEFAULT_SLA_CONFIG = {
    Priority.EMERGENCY: SLAConfig(
        priority=Priority.EMERGENCY,
        response_time_hours=1,
        completion_time_hours=4,
        escalation_levels=["supervisor", "manager", "director"]
    ),
    Priority.URGENT: SLAConfig(
        priority=Priority.URGENT,
        response_time_hours=4,
        completion_time_hours=12,
        escalation_levels=["supervisor", "manager"]
    ),
    Priority.HIGH: SLAConfig(
        priority=Priority.HIGH,
        response_time_hours=8,
        completion_time_hours=24,
        escalation_levels=["supervisor"]
    ),
    Priority.NORMAL: SLAConfig(
        priority=Priority.NORMAL,
        response_time_hours=24,
        completion_time_hours=48,
        escalation_levels=[]
    ),
    Priority.LOW: SLAConfig(
        priority=Priority.LOW,
        response_time_hours=72,
        completion_time_hours=168,  # 1 week
        escalation_levels=[]
    )
}


# =============================================================================
# WORK ORDER SERVICE
# =============================================================================

class WorkOrderService:
    """
    Main service for work order management.
    
    Features:
    - Create work orders from alerts or manually
    - Assign to technicians based on location/skill
    - Track status through lifecycle
    - SLA monitoring and escalation
    - Cost tracking and reporting
    """
    
    def __init__(self):
        # In-memory stores (replace with database in production)
        self.work_orders: Dict[str, WorkOrder] = {}
        self.technicians: Dict[str, Technician] = {}
        self.parts_inventory: Dict[str, Dict] = {}
        
        # Configuration
        self.sla_config = DEFAULT_SLA_CONFIG
        
        # Statistics
        self.stats = {
            "total_created": 0,
            "total_completed": 0,
            "total_water_saved_liters": 0,
            "total_cost_usd": 0,
            "sla_breaches": 0
        }
        
        logger.info("WorkOrderService initialized")
    
    # =========================================================================
    # TECHNICIAN MANAGEMENT
    # =========================================================================
    
    def add_technician(self, technician: Technician):
        """Add a technician to the system."""
        self.technicians[technician.technician_id] = technician
        logger.info(f"Added technician: {technician.name}")
    
    def get_available_technicians(
        self, 
        zone_id: str = None, 
        skill_level: SkillLevel = None
    ) -> List[Technician]:
        """Get available technicians, optionally filtered."""
        available = []
        for tech in self.technicians.values():
            if not tech.active or not tech.available:
                continue
            if zone_id and zone_id not in tech.zone_ids:
                continue
            if skill_level and tech.skill_level.value < skill_level.value:
                continue
            available.append(tech)
        return available
    
    def get_nearest_technician(
        self, 
        location: Location, 
        skill_level: SkillLevel = SkillLevel.BASIC
    ) -> Optional[Technician]:
        """Find nearest available technician to a location."""
        available = self.get_available_technicians(
            zone_id=location.zone_id, 
            skill_level=skill_level
        )
        
        if not available:
            # Try without zone filter
            available = self.get_available_technicians(skill_level=skill_level)
        
        if not available:
            return None
        
        # Sort by distance (simplified - just return first for now)
        # In production, calculate actual distances using coordinates
        return available[0]
    
    def update_technician_status(
        self, 
        technician_id: str, 
        available: bool = None,
        location: Location = None,
        current_work_order: str = None
    ):
        """Update technician status."""
        if technician_id not in self.technicians:
            return
        
        tech = self.technicians[technician_id]
        if available is not None:
            tech.available = available
        if location:
            tech.current_location = location
        if current_work_order is not None:
            tech.current_work_order_id = current_work_order
    
    # =========================================================================
    # WORK ORDER CREATION
    # =========================================================================
    
    def create_work_order(
        self,
        wo_type: WorkOrderType,
        priority: Priority,
        location: Location,
        title: str,
        description: str = "",
        source_alert_id: str = None,
        asset_id: str = "",
        customer_name: str = "",
        customer_phone: str = ""
    ) -> WorkOrder:
        """Create a new work order."""
        wo_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate SLA deadlines
        sla = self.sla_config.get(priority, DEFAULT_SLA_CONFIG[Priority.NORMAL])
        now = datetime.now(timezone.utc)
        
        work_order = WorkOrder(
            work_order_id=wo_id,
            type=wo_type,
            priority=priority,
            status=WorkOrderStatus.CREATED,
            source_alert_id=source_alert_id,
            location=location,
            title=title,
            description=description,
            asset_id=asset_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            sla_response_deadline=now + timedelta(hours=sla.response_time_hours),
            sla_completion_deadline=now + timedelta(hours=sla.completion_time_hours)
        )
        
        self.work_orders[wo_id] = work_order
        self.stats["total_created"] += 1
        
        logger.info(f"Created work order {wo_id}: {title}")
        
        return work_order
    
    def create_from_alert(
        self,
        alert_id: str,
        alert_type: str,
        zone_id: str,
        location: Location,
        confidence: float,
        sensor_data: Dict
    ) -> WorkOrder:
        """Automatically create work order from an alert."""
        # Determine work order type from alert type
        type_mapping = {
            "pressure_drop": WorkOrderType.LEAK_REPAIR,
            "flow_spike": WorkOrderType.BURST_REPAIR,
            "leak_detected": WorkOrderType.LEAK_REPAIR,
            "water_quality": WorkOrderType.WATER_QUALITY_TEST,
            "meter_anomaly": WorkOrderType.METER_REPAIR
        }
        
        wo_type = type_mapping.get(alert_type, WorkOrderType.INSPECTION)
        
        # Determine priority from confidence
        if confidence > 90 or alert_type == "flow_spike":
            priority = Priority.EMERGENCY
        elif confidence > 75:
            priority = Priority.URGENT
        elif confidence > 50:
            priority = Priority.HIGH
        else:
            priority = Priority.NORMAL
        
        # Generate title and description
        title = f"{alert_type.replace('_', ' ').title()} - {zone_id}"
        description = f"""
Alert ID: {alert_id}
Type: {alert_type}
Confidence: {confidence:.1f}%
Zone: {zone_id}

Sensor Readings:
- Pressure: {sensor_data.get('pressure', 'N/A')} bar
- Flow: {sensor_data.get('flow', 'N/A')} L/min
- pH: {sensor_data.get('ph', 'N/A')}

AI Recommendation: Investigate and repair if leak confirmed.
        """.strip()
        
        work_order = self.create_work_order(
            wo_type=wo_type,
            priority=priority,
            location=location,
            title=title,
            description=description,
            source_alert_id=alert_id
        )
        
        work_order.source_type = "alert"
        
        return work_order
    
    # =========================================================================
    # WORK ORDER ASSIGNMENT
    # =========================================================================
    
    def assign_work_order(
        self, 
        work_order_id: str, 
        technician_id: str,
        notify: bool = True
    ) -> bool:
        """Assign work order to a technician."""
        if work_order_id not in self.work_orders:
            return False
        if technician_id not in self.technicians:
            return False
        
        wo = self.work_orders[work_order_id]
        tech = self.technicians[technician_id]
        
        wo.assigned_to = technician_id
        wo.assigned_at = datetime.now(timezone.utc)
        wo.status = WorkOrderStatus.ASSIGNED
        wo.updated_at = datetime.now(timezone.utc)
        
        # Update technician status
        tech.current_work_order_id = work_order_id
        
        logger.info(f"Assigned {work_order_id} to {tech.name}")
        
        # TODO: Send notification if notify=True
        
        return True
    
    def auto_assign_work_order(self, work_order_id: str) -> Optional[str]:
        """Automatically assign work order to best available technician."""
        if work_order_id not in self.work_orders:
            return None
        
        wo = self.work_orders[work_order_id]
        
        # Determine required skill level
        skill_mapping = {
            WorkOrderType.LEAK_REPAIR: SkillLevel.INTERMEDIATE,
            WorkOrderType.BURST_REPAIR: SkillLevel.ADVANCED,
            WorkOrderType.METER_INSTALLATION: SkillLevel.BASIC,
            WorkOrderType.PIPE_REPLACEMENT: SkillLevel.SPECIALIST,
            WorkOrderType.INSPECTION: SkillLevel.BASIC
        }
        required_skill = skill_mapping.get(wo.type, SkillLevel.BASIC)
        
        # Find best technician
        tech = self.get_nearest_technician(wo.location, required_skill)
        
        if tech:
            self.assign_work_order(work_order_id, tech.technician_id)
            return tech.technician_id
        
        logger.warning(f"No available technician for {work_order_id}")
        return None
    
    # =========================================================================
    # STATUS UPDATES
    # =========================================================================
    
    def update_status(
        self, 
        work_order_id: str, 
        new_status: WorkOrderStatus,
        notes: str = ""
    ) -> bool:
        """Update work order status."""
        if work_order_id not in self.work_orders:
            return False
        
        wo = self.work_orders[work_order_id]
        old_status = wo.status
        wo.status = new_status
        wo.updated_at = datetime.now(timezone.utc)
        
        if notes:
            wo.internal_notes += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
        
        # Handle specific status transitions
        if new_status == WorkOrderStatus.ACKNOWLEDGED:
            wo.acknowledged_at = datetime.now(timezone.utc)
        elif new_status == WorkOrderStatus.IN_PROGRESS:
            wo.started_at = datetime.now(timezone.utc)
        elif new_status == WorkOrderStatus.COMPLETED:
            wo.completed_at = datetime.now(timezone.utc)
            self._on_completion(wo)
        elif new_status == WorkOrderStatus.VERIFIED:
            wo.verified_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated {work_order_id}: {old_status.value} -> {new_status.value}")
        
        return True
    
    def acknowledge_work_order(
        self, 
        work_order_id: str, 
        technician_id: str
    ) -> bool:
        """Technician acknowledges receiving the work order."""
        if work_order_id not in self.work_orders:
            return False
        
        wo = self.work_orders[work_order_id]
        
        if wo.assigned_to != technician_id:
            return False
        
        return self.update_status(
            work_order_id, 
            WorkOrderStatus.ACKNOWLEDGED,
            f"Acknowledged by technician"
        )
    
    def start_work(
        self, 
        work_order_id: str, 
        technician_id: str,
        latitude: float = None,
        longitude: float = None
    ) -> bool:
        """Technician starts work on the job."""
        if work_order_id not in self.work_orders:
            return False
        
        wo = self.work_orders[work_order_id]
        
        # Create time entry
        entry = TimeEntry(
            entry_id=str(uuid.uuid4())[:8],
            technician_id=technician_id,
            start_time=datetime.now(timezone.utc),
            activity="On-site work"
        )
        wo.time_entries.append(entry)
        
        return self.update_status(
            work_order_id, 
            WorkOrderStatus.IN_PROGRESS,
            "Work started on site"
        )
    
    def complete_work_order(
        self,
        work_order_id: str,
        technician_id: str,
        work_performed: str,
        root_cause: str = "",
        parts_used: List[Part] = None,
        photos: List[PhotoEvidence] = None,
        measurements: Dict = None
    ) -> bool:
        """Complete a work order with findings."""
        if work_order_id not in self.work_orders:
            return False
        
        wo = self.work_orders[work_order_id]
        
        wo.work_performed = work_performed
        wo.root_cause = root_cause
        
        if parts_used:
            wo.parts_used.extend(parts_used)
            wo.parts_cost_usd = sum(p.total_cost for p in wo.parts_used)
        
        if photos:
            wo.photos.extend(photos)
        
        if measurements:
            wo.flow_before_lpm = measurements.get("flow_before")
            wo.flow_after_lpm = measurements.get("flow_after")
            wo.pressure_before_bar = measurements.get("pressure_before")
            wo.pressure_after_bar = measurements.get("pressure_after")
            
            # Calculate water saved
            if wo.flow_before_lpm and wo.flow_after_lpm:
                wo.water_saved_lph = (wo.flow_before_lpm - wo.flow_after_lpm) * 60
        
        # End time entry
        for entry in wo.time_entries:
            if entry.technician_id == technician_id and not entry.end_time:
                entry.end_time = datetime.now(timezone.utc)
        
        # Calculate labor cost (simplified: $10/hour)
        wo.labor_cost_usd = wo.total_time_hours * 10
        
        # Release technician
        if technician_id in self.technicians:
            tech = self.technicians[technician_id]
            tech.available = True
            tech.current_work_order_id = None
        
        return self.update_status(
            work_order_id, 
            WorkOrderStatus.COMPLETED,
            f"Completed by {technician_id}"
        )
    
    def _on_completion(self, wo: WorkOrder):
        """Handle work order completion."""
        self.stats["total_completed"] += 1
        self.stats["total_cost_usd"] += wo.total_cost
        
        if wo.water_saved_lph:
            # Estimate annual savings
            annual_saved = wo.water_saved_lph * 24 * 365
            self.stats["total_water_saved_liters"] += annual_saved
    
    # =========================================================================
    # SLA MONITORING
    # =========================================================================
    
    def check_sla_breaches(self) -> List[WorkOrder]:
        """Check for SLA breaches and escalate if needed."""
        now = datetime.now(timezone.utc)
        breached = []
        
        for wo in self.work_orders.values():
            if wo.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.VERIFIED, 
                            WorkOrderStatus.CANCELLED]:
                continue
            
            # Check response SLA
            if wo.sla_response_deadline and not wo.acknowledged_at:
                if now > wo.sla_response_deadline:
                    wo.sla_breached = True
                    breached.append(wo)
                    self._escalate_work_order(wo, "Response SLA breached")
            
            # Check completion SLA
            if wo.sla_completion_deadline and not wo.completed_at:
                if now > wo.sla_completion_deadline:
                    wo.sla_breached = True
                    breached.append(wo)
                    self._escalate_work_order(wo, "Completion SLA breached")
        
        if breached:
            self.stats["sla_breaches"] += len(breached)
        
        return breached
    
    def _escalate_work_order(self, wo: WorkOrder, reason: str):
        """Escalate a work order."""
        wo.status = WorkOrderStatus.ESCALATED
        wo.internal_notes += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] ESCALATED: {reason}"
        
        logger.warning(f"Escalated {wo.work_order_id}: {reason}")
        
        # TODO: Send escalation notifications
    
    # =========================================================================
    # QUERIES & REPORTING
    # =========================================================================
    
    def get_work_order(self, work_order_id: str) -> Optional[WorkOrder]:
        """Get a work order by ID."""
        return self.work_orders.get(work_order_id)
    
    def get_work_orders_by_status(self, status: WorkOrderStatus) -> List[WorkOrder]:
        """Get all work orders with a specific status."""
        return [wo for wo in self.work_orders.values() if wo.status == status]
    
    def get_work_orders_by_technician(self, technician_id: str) -> List[WorkOrder]:
        """Get all work orders assigned to a technician."""
        return [wo for wo in self.work_orders.values() if wo.assigned_to == technician_id]
    
    def get_work_orders_by_zone(self, zone_id: str) -> List[WorkOrder]:
        """Get all work orders in a zone."""
        return [wo for wo in self.work_orders.values() 
                if wo.location and wo.location.zone_id == zone_id]
    
    def get_open_work_orders(self) -> List[WorkOrder]:
        """Get all open (not completed/cancelled) work orders."""
        closed_statuses = [WorkOrderStatus.COMPLETED, WorkOrderStatus.VERIFIED, 
                         WorkOrderStatus.CANCELLED]
        return [wo for wo in self.work_orders.values() if wo.status not in closed_statuses]
    
    def get_daily_summary(self, date: datetime = None) -> Dict:
        """Get daily work order summary."""
        if date is None:
            date = datetime.now(timezone.utc).date()
        
        daily_orders = [wo for wo in self.work_orders.values() 
                       if wo.created_at.date() == date]
        
        completed = [wo for wo in daily_orders if wo.status == WorkOrderStatus.COMPLETED]
        
        return {
            "date": date.isoformat(),
            "total_created": len(daily_orders),
            "total_completed": len(completed),
            "by_type": self._count_by_type(daily_orders),
            "by_priority": self._count_by_priority(daily_orders),
            "avg_completion_time_hours": self._avg_completion_time(completed),
            "total_water_saved_lph": sum(wo.water_saved_lph or 0 for wo in completed),
            "total_cost_usd": sum(wo.total_cost for wo in completed),
            "sla_breaches": len([wo for wo in daily_orders if wo.sla_breached])
        }
    
    def _count_by_type(self, work_orders: List[WorkOrder]) -> Dict:
        counts = {}
        for wo in work_orders:
            counts[wo.type.value] = counts.get(wo.type.value, 0) + 1
        return counts
    
    def _count_by_priority(self, work_orders: List[WorkOrder]) -> Dict:
        counts = {}
        for wo in work_orders:
            counts[wo.priority.name] = counts.get(wo.priority.name, 0) + 1
        return counts
    
    def _avg_completion_time(self, work_orders: List[WorkOrder]) -> float:
        times = [wo.completion_time_hours for wo in work_orders if wo.completion_time_hours]
        return round(sum(times) / len(times), 1) if times else 0
    
    def get_technician_performance(self, technician_id: str, days: int = 30) -> Dict:
        """Get performance metrics for a technician."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        tech_orders = [wo for wo in self.work_orders.values() 
                      if wo.assigned_to == technician_id and wo.created_at > cutoff]
        
        completed = [wo for wo in tech_orders if wo.status == WorkOrderStatus.COMPLETED]
        
        return {
            "technician_id": technician_id,
            "period_days": days,
            "total_assigned": len(tech_orders),
            "total_completed": len(completed),
            "completion_rate": round(len(completed) / len(tech_orders) * 100, 1) if tech_orders else 0,
            "avg_response_time_hours": self._avg_response_time(tech_orders),
            "avg_completion_time_hours": self._avg_completion_time(completed),
            "total_water_saved_lph": sum(wo.water_saved_lph or 0 for wo in completed),
            "sla_breaches": len([wo for wo in tech_orders if wo.sla_breached])
        }
    
    def _avg_response_time(self, work_orders: List[WorkOrder]) -> float:
        times = [wo.response_time_hours for wo in work_orders if wo.response_time_hours]
        return round(sum(times) / len(times), 1) if times else 0
    
    def export_work_order(self, work_order_id: str) -> Dict:
        """Export work order as dictionary for API/reporting."""
        wo = self.work_orders.get(work_order_id)
        if not wo:
            return {}
        
        return {
            "work_order_id": wo.work_order_id,
            "type": wo.type.value,
            "priority": wo.priority.name,
            "status": wo.status.value,
            "title": wo.title,
            "description": wo.description,
            "location": {
                "latitude": wo.location.latitude if wo.location else None,
                "longitude": wo.location.longitude if wo.location else None,
                "address": wo.location.address if wo.location else "",
                "zone_id": wo.location.zone_id if wo.location else ""
            },
            "assigned_to": wo.assigned_to,
            "customer": {
                "name": wo.customer_name,
                "phone": wo.customer_phone,
                "account": wo.customer_account
            },
            "work_performed": wo.work_performed,
            "root_cause": wo.root_cause,
            "measurements": {
                "flow_before_lpm": wo.flow_before_lpm,
                "flow_after_lpm": wo.flow_after_lpm,
                "pressure_before_bar": wo.pressure_before_bar,
                "pressure_after_bar": wo.pressure_after_bar,
                "water_saved_lph": wo.water_saved_lph
            },
            "costs": {
                "labor_usd": wo.labor_cost_usd,
                "parts_usd": wo.parts_cost_usd,
                "total_usd": wo.total_cost
            },
            "parts_used": [{"name": p.name, "quantity": p.quantity, "cost": p.total_cost} 
                         for p in wo.parts_used],
            "photos": [{"url": p.url, "caption": p.caption, "type": p.photo_type} 
                      for p in wo.photos],
            "timestamps": {
                "created": wo.created_at.isoformat(),
                "assigned": wo.assigned_at.isoformat() if wo.assigned_at else None,
                "acknowledged": wo.acknowledged_at.isoformat() if wo.acknowledged_at else None,
                "started": wo.started_at.isoformat() if wo.started_at else None,
                "completed": wo.completed_at.isoformat() if wo.completed_at else None,
                "verified": wo.verified_at.isoformat() if wo.verified_at else None
            },
            "sla": {
                "response_deadline": wo.sla_response_deadline.isoformat() if wo.sla_response_deadline else None,
                "completion_deadline": wo.sla_completion_deadline.isoformat() if wo.sla_completion_deadline else None,
                "breached": wo.sla_breached
            },
            "total_time_hours": wo.total_time_hours
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    service = WorkOrderService()
    
    # Add technicians
    service.add_technician(Technician(
        technician_id="TECH001",
        name="Mwamba Chanda",
        phone="+260971234567",
        skill_level=SkillLevel.ADVANCED,
        zone_ids=["ZONE_A", "ZONE_B"]
    ))
    
    service.add_technician(Technician(
        technician_id="TECH002",
        name="Grace Mulenga",
        phone="+260962345678",
        skill_level=SkillLevel.INTERMEDIATE,
        zone_ids=["ZONE_A", "ZONE_C"]
    ))
    
    # Create work order from alert
    location = Location(
        latitude=-15.4167,
        longitude=28.2833,
        address="Plot 123, Main Road",
        zone_id="ZONE_A",
        landmark="Near Shoprite"
    )
    
    wo = service.create_from_alert(
        alert_id="ALERT_001",
        alert_type="pressure_drop",
        zone_id="ZONE_A",
        location=location,
        confidence=85.5,
        sensor_data={
            "pressure": 2.1,
            "flow": 45.2,
            "ph": 7.1
        }
    )
    
    print(f"Created: {wo.work_order_id}")
    print(f"Type: {wo.type.value}")
    print(f"Priority: {wo.priority.name}")
    print(f"SLA Response: {wo.sla_response_deadline}")
    
    # Auto-assign
    tech_id = service.auto_assign_work_order(wo.work_order_id)
    print(f"Assigned to: {tech_id}")
    
    # Simulate workflow
    service.acknowledge_work_order(wo.work_order_id, tech_id)
    service.start_work(wo.work_order_id, tech_id)
    
    # Complete
    service.complete_work_order(
        wo.work_order_id,
        tech_id,
        work_performed="Repaired 50mm pipe joint leak. Replaced gasket.",
        root_cause="Worn gasket due to age",
        parts_used=[Part("GASKET50", "50mm Gasket", 1, "each", 5.0)],
        measurements={
            "flow_before": 45.2,
            "flow_after": 12.1,
            "pressure_before": 2.1,
            "pressure_after": 3.5
        }
    )
    
    # Export
    print("\nWork Order Export:")
    print(json.dumps(service.export_work_order(wo.work_order_id), indent=2, default=str))
    
    # Daily summary
    print("\nDaily Summary:")
    print(json.dumps(service.get_daily_summary(), indent=2))
