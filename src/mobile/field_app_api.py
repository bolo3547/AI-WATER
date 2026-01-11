"""
AquaWatch NRW - Mobile Field App API
====================================

REST API backend for field technician mobile app.

Features:
- Work order management
- GPS tracking
- Photo uploads
- Offline sync
- Real-time updates via WebSockets
- Time tracking
- Material inventory

Designed for use in Zambia/Southern Africa with:
- Low bandwidth optimization
- Offline-first architecture
- Multi-language support
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps

from flask import Flask, request, jsonify, g
import jwt

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    SECRET_KEY = os.environ.get('JWT_SECRET', 'aquawatch-field-app-secret-2024')
    TOKEN_EXPIRY_HOURS = 24 * 7  # 1 week
    MAX_PHOTO_SIZE_MB = 5
    OFFLINE_SYNC_BATCH_SIZE = 50
    GPS_UPDATE_INTERVAL_SECONDS = 60


# =============================================================================
# DATA MODELS
# =============================================================================

class WorkOrderStatus(Enum):
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TechnicianStatus(Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    ON_CALL = "on_call"
    BUSY = "busy"
    ON_BREAK = "on_break"


@dataclass
class GPSLocation:
    latitude: float
    longitude: float
    accuracy_m: float = 0.0
    altitude_m: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        return {
            "lat": self.latitude,
            "lng": self.longitude,
            "accuracy": self.accuracy_m,
            "altitude": self.altitude_m,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Technician:
    technician_id: str
    employee_id: str
    name: str
    phone: str
    email: str = ""
    
    # Status
    status: TechnicianStatus = TechnicianStatus.OFFLINE
    current_location: Optional[GPSLocation] = None
    last_seen: Optional[datetime] = None
    
    # Assignment
    zone_ids: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    current_work_order_id: Optional[str] = None
    
    # Stats
    completed_today: int = 0
    completed_week: int = 0


@dataclass
class MobileWorkOrder:
    """Work order optimized for mobile."""
    work_order_id: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    work_type: str  # leak_repair, meter_installation, inspection, etc.
    
    # Location
    zone_id: str
    location: Optional[Dict] = None  # lat, lng
    address: str = ""
    
    # Assignment
    technician_id: str = ""
    assigned_at: Optional[datetime] = None
    
    # Timeline
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Status
    status: WorkOrderStatus = WorkOrderStatus.ASSIGNED
    
    # Details
    estimated_duration_minutes: int = 60
    actual_duration_minutes: int = 0
    materials_used: List[Dict] = field(default_factory=list)
    photos: List[Dict] = field(default_factory=list)
    notes: str = ""
    customer_signature: str = ""
    
    # Sync
    last_synced: Optional[datetime] = None
    offline_changes: bool = False


@dataclass
class TimeEntry:
    """Time tracking entry."""
    entry_id: str
    technician_id: str
    work_order_id: Optional[str]
    entry_type: str  # travel, work, break
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    location_start: Optional[GPSLocation] = None
    location_end: Optional[GPSLocation] = None
    notes: str = ""


@dataclass
class InventoryItem:
    """Material inventory item."""
    item_id: str
    name: str
    sku: str
    category: str
    quantity: int = 0
    unit: str = "each"
    vehicle_id: str = ""


@dataclass
class SyncPackage:
    """Package for offline sync."""
    package_id: str
    technician_id: str
    device_id: str
    created_at: datetime
    
    # Data
    work_orders: List[Dict] = field(default_factory=list)
    time_entries: List[Dict] = field(default_factory=list)
    photos: List[Dict] = field(default_factory=list)
    gps_history: List[Dict] = field(default_factory=list)
    
    # Sync status
    uploaded: bool = False
    conflicts: List[Dict] = field(default_factory=list)


# =============================================================================
# FIELD APP SERVICE
# =============================================================================

class FieldAppService:
    """Backend service for mobile field app."""
    
    def __init__(self):
        self.technicians: Dict[str, Technician] = {}
        self.work_orders: Dict[str, MobileWorkOrder] = {}
        self.time_entries: Dict[str, TimeEntry] = {}
        self.sync_packages: Dict[str, SyncPackage] = {}
        self.inventory: Dict[str, InventoryItem] = {}
        self.gps_history: Dict[str, List[GPSLocation]] = {}
        
        # Translations
        self.translations = {
            "en": {
                "assigned": "Assigned",
                "en_route": "En Route",
                "on_site": "On Site",
                "in_progress": "In Progress",
                "completed": "Completed",
                "critical": "Critical - Respond Immediately",
                "high": "High Priority",
                "medium": "Medium Priority",
                "low": "Low Priority"
            },
            "ny": {  # Nyanja
                "assigned": "Mwapatsidwa",
                "en_route": "Mukupita",
                "on_site": "Muli Pamalo",
                "in_progress": "Mukugwira Ntchito",
                "completed": "Yathera",
                "critical": "Yofunikira Kwambiri",
                "high": "Yofunikira",
                "medium": "Yapakati",
                "low": "Yosakhalira"
            },
            "bem": {  # Bemba
                "assigned": "Bapeelwe",
                "en_route": "Baleya",
                "on_site": "Bali Pali",
                "in_progress": "Balabomba",
                "completed": "Yapwa",
                "critical": "Iyacindama Sana",
                "high": "Iyacindama",
                "medium": "Napakati",
                "low": "Tayacindama"
            }
        }
        
        logger.info("FieldAppService initialized")
    
    def translate(self, key: str, lang: str = "en") -> str:
        """Get translated text."""
        return self.translations.get(lang, {}).get(key, key)
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    def generate_token(self, technician_id: str, device_id: str) -> str:
        """Generate JWT token for mobile app."""
        payload = {
            "technician_id": technician_id,
            "device_id": device_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=Config.TOKEN_EXPIRY_HOURS),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token."""
        try:
            return jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def authenticate_technician(
        self,
        employee_id: str,
        pin: str,
        device_id: str
    ) -> Optional[Dict]:
        """Authenticate technician by employee ID and PIN."""
        # Find technician
        tech = None
        for t in self.technicians.values():
            if t.employee_id == employee_id:
                tech = t
                break
        
        if not tech:
            return None
        
        # In production, verify PIN against database
        # For demo, accept any 4-digit PIN
        if len(pin) != 4 or not pin.isdigit():
            return None
        
        token = self.generate_token(tech.technician_id, device_id)
        
        return {
            "success": True,
            "token": token,
            "technician": {
                "id": tech.technician_id,
                "name": tech.name,
                "zones": tech.zone_ids,
                "skills": tech.skills
            }
        }
    
    # =========================================================================
    # TECHNICIAN MANAGEMENT
    # =========================================================================
    
    def register_technician(self, tech: Technician):
        """Register a technician."""
        self.technicians[tech.technician_id] = tech
        self.gps_history[tech.technician_id] = []
    
    def update_technician_status(
        self,
        technician_id: str,
        status: str,
        location: Optional[Dict] = None
    ) -> bool:
        """Update technician status."""
        if technician_id not in self.technicians:
            return False
        
        tech = self.technicians[technician_id]
        tech.status = TechnicianStatus[status.upper()]
        tech.last_seen = datetime.now(timezone.utc)
        
        if location:
            gps = GPSLocation(
                latitude=location["lat"],
                longitude=location["lng"],
                accuracy_m=location.get("accuracy", 0)
            )
            tech.current_location = gps
            
            # Store GPS history
            self.gps_history[technician_id].append(gps)
            # Keep last 1000 points
            if len(self.gps_history[technician_id]) > 1000:
                self.gps_history[technician_id] = self.gps_history[technician_id][-1000:]
        
        return True
    
    def get_technician_location(self, technician_id: str) -> Optional[Dict]:
        """Get technician's current location."""
        if technician_id not in self.technicians:
            return None
        
        tech = self.technicians[technician_id]
        if tech.current_location:
            return tech.current_location.to_dict()
        return None
    
    def get_technician_gps_trail(
        self,
        technician_id: str,
        hours: int = 8
    ) -> List[Dict]:
        """Get technician's GPS trail."""
        if technician_id not in self.gps_history:
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            loc.to_dict()
            for loc in self.gps_history[technician_id]
            if loc.timestamp > cutoff
        ]
    
    # =========================================================================
    # WORK ORDER MANAGEMENT
    # =========================================================================
    
    def get_technician_work_orders(
        self,
        technician_id: str,
        status_filter: List[str] = None,
        lang: str = "en"
    ) -> List[Dict]:
        """Get work orders for a technician."""
        orders = [
            wo for wo in self.work_orders.values()
            if wo.technician_id == technician_id
        ]
        
        if status_filter:
            orders = [
                wo for wo in orders
                if wo.status.value in status_filter
            ]
        
        # Sort by priority and due date
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        orders.sort(key=lambda x: (
            priority_order.get(x.priority, 9),
            x.due_date or datetime.max.replace(tzinfo=timezone.utc)
        ))
        
        # Format for mobile with translations
        return [
            {
                "id": wo.work_order_id,
                "title": wo.title,
                "description": wo.description,
                "priority": wo.priority,
                "priority_label": self.translate(wo.priority, lang),
                "status": wo.status.value,
                "status_label": self.translate(wo.status.value, lang),
                "work_type": wo.work_type,
                "zone_id": wo.zone_id,
                "address": wo.address,
                "location": wo.location,
                "due_date": wo.due_date.isoformat() if wo.due_date else None,
                "estimated_minutes": wo.estimated_duration_minutes,
                "created_at": wo.created_at.isoformat()
            }
            for wo in orders
        ]
    
    def get_work_order_details(
        self,
        work_order_id: str,
        lang: str = "en"
    ) -> Optional[Dict]:
        """Get full work order details."""
        if work_order_id not in self.work_orders:
            return None
        
        wo = self.work_orders[work_order_id]
        
        return {
            "id": wo.work_order_id,
            "title": wo.title,
            "description": wo.description,
            "priority": wo.priority,
            "priority_label": self.translate(wo.priority, lang),
            "status": wo.status.value,
            "status_label": self.translate(wo.status.value, lang),
            "work_type": wo.work_type,
            "zone_id": wo.zone_id,
            "address": wo.address,
            "location": wo.location,
            "due_date": wo.due_date.isoformat() if wo.due_date else None,
            "estimated_minutes": wo.estimated_duration_minutes,
            "actual_minutes": wo.actual_duration_minutes,
            "created_at": wo.created_at.isoformat(),
            "started_at": wo.started_at.isoformat() if wo.started_at else None,
            "completed_at": wo.completed_at.isoformat() if wo.completed_at else None,
            "materials": wo.materials_used,
            "photos": wo.photos,
            "notes": wo.notes,
            "last_synced": wo.last_synced.isoformat() if wo.last_synced else None
        }
    
    def update_work_order_status(
        self,
        work_order_id: str,
        new_status: str,
        technician_id: str,
        location: Optional[Dict] = None,
        notes: str = ""
    ) -> Dict:
        """Update work order status from mobile."""
        if work_order_id not in self.work_orders:
            return {"success": False, "error": "Work order not found"}
        
        wo = self.work_orders[work_order_id]
        
        if wo.technician_id != technician_id:
            return {"success": False, "error": "Not assigned to you"}
        
        old_status = wo.status
        wo.status = WorkOrderStatus[new_status.upper()]
        
        # Handle status-specific actions
        if new_status == "en_route":
            # Start travel time tracking
            self._start_time_entry(technician_id, work_order_id, "travel", location)
            
        elif new_status == "on_site":
            # End travel, start work
            self._end_current_time_entry(technician_id)
            
        elif new_status == "in_progress":
            if old_status != WorkOrderStatus.IN_PROGRESS:
                wo.started_at = datetime.now(timezone.utc)
                self._start_time_entry(technician_id, work_order_id, "work", location)
            
        elif new_status == "completed":
            wo.completed_at = datetime.now(timezone.utc)
            if wo.started_at:
                wo.actual_duration_minutes = int(
                    (wo.completed_at - wo.started_at).total_seconds() / 60
                )
            self._end_current_time_entry(technician_id)
            
            # Update technician stats
            tech = self.technicians.get(technician_id)
            if tech:
                tech.completed_today += 1
                tech.completed_week += 1
                tech.current_work_order_id = None
        
        if notes:
            wo.notes = notes
        
        wo.last_synced = datetime.now(timezone.utc)
        
        return {
            "success": True,
            "work_order_id": work_order_id,
            "old_status": old_status.value,
            "new_status": wo.status.value
        }
    
    def add_work_order_photo(
        self,
        work_order_id: str,
        photo_data: Dict  # base64 data, caption, type
    ) -> Dict:
        """Add photo to work order."""
        if work_order_id not in self.work_orders:
            return {"success": False, "error": "Work order not found"}
        
        wo = self.work_orders[work_order_id]
        
        photo_record = {
            "photo_id": str(uuid.uuid4()),
            "type": photo_data.get("type", "general"),  # before, during, after
            "caption": photo_data.get("caption", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": photo_data.get("location"),
            "file_size_kb": len(photo_data.get("data", "")) * 0.75 / 1024,  # Base64 estimate
            "uploaded": False
        }
        
        wo.photos.append(photo_record)
        
        return {"success": True, "photo_id": photo_record["photo_id"]}
    
    def add_materials_used(
        self,
        work_order_id: str,
        technician_id: str,
        materials: List[Dict]
    ) -> Dict:
        """Record materials used on work order."""
        if work_order_id not in self.work_orders:
            return {"success": False, "error": "Work order not found"}
        
        wo = self.work_orders[work_order_id]
        
        for material in materials:
            wo.materials_used.append({
                "item_id": material.get("item_id"),
                "name": material.get("name"),
                "quantity": material.get("quantity", 1),
                "unit": material.get("unit", "each"),
                "added_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Update inventory if tracked
            if material.get("item_id") in self.inventory:
                item = self.inventory[material["item_id"]]
                item.quantity -= material.get("quantity", 1)
        
        return {"success": True, "materials_count": len(wo.materials_used)}
    
    def complete_work_order(
        self,
        work_order_id: str,
        technician_id: str,
        completion_data: Dict
    ) -> Dict:
        """Complete work order with full details."""
        if work_order_id not in self.work_orders:
            return {"success": False, "error": "Work order not found"}
        
        wo = self.work_orders[work_order_id]
        
        # Update status
        self.update_work_order_status(
            work_order_id,
            "completed",
            technician_id,
            completion_data.get("location")
        )
        
        # Add completion details
        wo.notes = completion_data.get("notes", wo.notes)
        wo.customer_signature = completion_data.get("signature", "")
        
        return {
            "success": True,
            "work_order_id": work_order_id,
            "completed_at": wo.completed_at.isoformat(),
            "duration_minutes": wo.actual_duration_minutes
        }
    
    # =========================================================================
    # TIME TRACKING
    # =========================================================================
    
    def _start_time_entry(
        self,
        technician_id: str,
        work_order_id: str,
        entry_type: str,
        location: Optional[Dict] = None
    ):
        """Start a time tracking entry."""
        entry = TimeEntry(
            entry_id=str(uuid.uuid4()),
            technician_id=technician_id,
            work_order_id=work_order_id,
            entry_type=entry_type,
            start_time=datetime.now(timezone.utc)
        )
        
        if location:
            entry.location_start = GPSLocation(
                latitude=location["lat"],
                longitude=location["lng"]
            )
        
        self.time_entries[entry.entry_id] = entry
        return entry
    
    def _end_current_time_entry(self, technician_id: str):
        """End the current time entry for a technician."""
        for entry in self.time_entries.values():
            if entry.technician_id == technician_id and entry.end_time is None:
                entry.end_time = datetime.now(timezone.utc)
                entry.duration_minutes = int(
                    (entry.end_time - entry.start_time).total_seconds() / 60
                )
    
    def get_technician_timesheet(
        self,
        technician_id: str,
        date: datetime = None
    ) -> Dict:
        """Get technician's timesheet for a day."""
        if date is None:
            date = datetime.now(timezone.utc)
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        entries = [
            e for e in self.time_entries.values()
            if e.technician_id == technician_id
            and start_of_day <= e.start_time < end_of_day
        ]
        
        total_travel = sum(
            e.duration_minutes for e in entries if e.entry_type == "travel"
        )
        total_work = sum(
            e.duration_minutes for e in entries if e.entry_type == "work"
        )
        total_break = sum(
            e.duration_minutes for e in entries if e.entry_type == "break"
        )
        
        return {
            "technician_id": technician_id,
            "date": date.strftime("%Y-%m-%d"),
            "entries": [
                {
                    "id": e.entry_id,
                    "type": e.entry_type,
                    "work_order_id": e.work_order_id,
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat() if e.end_time else None,
                    "duration_minutes": e.duration_minutes
                }
                for e in entries
            ],
            "summary": {
                "travel_minutes": total_travel,
                "work_minutes": total_work,
                "break_minutes": total_break,
                "total_minutes": total_travel + total_work + total_break
            }
        }
    
    # =========================================================================
    # OFFLINE SYNC
    # =========================================================================
    
    def create_sync_package_for_download(
        self,
        technician_id: str,
        device_id: str
    ) -> Dict:
        """Create data package for offline use."""
        # Get all assigned work orders
        work_orders = self.get_technician_work_orders(
            technician_id,
            ["assigned", "en_route", "on_site", "in_progress", "pending_parts"]
        )
        
        # Get inventory for technician's vehicle
        tech = self.technicians.get(technician_id)
        inventory = []
        if tech:
            inventory = [
                asdict(item) for item in self.inventory.values()
                # Filter by vehicle if applicable
            ]
        
        package = {
            "package_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "technician_id": technician_id,
            "device_id": device_id,
            "data": {
                "work_orders": work_orders,
                "inventory": inventory[:50],  # Limit for bandwidth
                "translations": self.translations
            },
            "version": 1
        }
        
        return package
    
    def process_sync_upload(
        self,
        technician_id: str,
        sync_data: Dict
    ) -> Dict:
        """Process sync upload from offline device."""
        results = {
            "success": True,
            "processed": {
                "work_orders": 0,
                "time_entries": 0,
                "photos": 0,
                "gps_points": 0
            },
            "conflicts": [],
            "errors": []
        }
        
        # Process work order updates
        for wo_update in sync_data.get("work_orders", []):
            try:
                wo_id = wo_update.get("id")
                if wo_id in self.work_orders:
                    wo = self.work_orders[wo_id]
                    
                    # Check for conflicts
                    client_sync_time = datetime.fromisoformat(
                        wo_update.get("last_synced", "2000-01-01T00:00:00+00:00")
                    )
                    if wo.last_synced and wo.last_synced > client_sync_time:
                        results["conflicts"].append({
                            "type": "work_order",
                            "id": wo_id,
                            "server_time": wo.last_synced.isoformat(),
                            "client_time": client_sync_time.isoformat()
                        })
                        continue
                    
                    # Apply updates
                    if wo_update.get("status"):
                        wo.status = WorkOrderStatus[wo_update["status"].upper()]
                    if wo_update.get("notes"):
                        wo.notes = wo_update["notes"]
                    if wo_update.get("materials"):
                        wo.materials_used.extend(wo_update["materials"])
                    
                    wo.last_synced = datetime.now(timezone.utc)
                    results["processed"]["work_orders"] += 1
                    
            except Exception as e:
                results["errors"].append(f"Work order {wo_id}: {str(e)}")
        
        # Process time entries
        for entry_data in sync_data.get("time_entries", []):
            try:
                entry = TimeEntry(
                    entry_id=entry_data.get("id", str(uuid.uuid4())),
                    technician_id=technician_id,
                    work_order_id=entry_data.get("work_order_id"),
                    entry_type=entry_data.get("type", "work"),
                    start_time=datetime.fromisoformat(entry_data["start"]),
                    end_time=datetime.fromisoformat(entry_data["end"]) if entry_data.get("end") else None,
                    duration_minutes=entry_data.get("duration_minutes", 0)
                )
                self.time_entries[entry.entry_id] = entry
                results["processed"]["time_entries"] += 1
            except Exception as e:
                results["errors"].append(f"Time entry: {str(e)}")
        
        # Process GPS history
        for gps_point in sync_data.get("gps_history", []):
            try:
                loc = GPSLocation(
                    latitude=gps_point["lat"],
                    longitude=gps_point["lng"],
                    accuracy_m=gps_point.get("accuracy", 0),
                    timestamp=datetime.fromisoformat(gps_point["timestamp"])
                )
                if technician_id not in self.gps_history:
                    self.gps_history[technician_id] = []
                self.gps_history[technician_id].append(loc)
                results["processed"]["gps_points"] += 1
            except Exception as e:
                pass  # Skip invalid GPS points silently
        
        # Photo uploads would be handled separately with binary upload
        results["processed"]["photos"] = len(sync_data.get("photos", []))
        
        return results
    
    # =========================================================================
    # INVENTORY
    # =========================================================================
    
    def get_vehicle_inventory(self, vehicle_id: str) -> List[Dict]:
        """Get inventory for a vehicle."""
        items = [
            {
                "id": item.item_id,
                "name": item.name,
                "sku": item.sku,
                "category": item.category,
                "quantity": item.quantity,
                "unit": item.unit
            }
            for item in self.inventory.values()
            if item.vehicle_id == vehicle_id
        ]
        return items
    
    def request_materials(
        self,
        technician_id: str,
        items: List[Dict]
    ) -> Dict:
        """Request materials from warehouse."""
        request_id = f"REQ_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # In production, this would create a warehouse request
        return {
            "request_id": request_id,
            "status": "pending",
            "items": items,
            "estimated_delivery": "Next business day"
        }


# =============================================================================
# FLASK API
# =============================================================================

def create_field_app_api(service: FieldAppService) -> Flask:
    """Create Flask API for mobile field app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Auth decorator
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            payload = service.verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            g.technician_id = payload.get("technician_id")
            g.device_id = payload.get("device_id")
            return f(*args, **kwargs)
        return decorated
    
    # ----- Authentication -----
    
    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        """Authenticate technician."""
        data = request.json
        result = service.authenticate_technician(
            employee_id=data.get("employee_id"),
            pin=data.get("pin"),
            device_id=data.get("device_id", "unknown")
        )
        
        if result:
            return jsonify(result)
        return jsonify({"error": "Invalid credentials"}), 401
    
    @app.route('/api/v1/auth/refresh', methods=['POST'])
    @require_auth
    def refresh_token():
        """Refresh auth token."""
        token = service.generate_token(g.technician_id, g.device_id)
        return jsonify({"token": token})
    
    # ----- Work Orders -----
    
    @app.route('/api/v1/work-orders', methods=['GET'])
    @require_auth
    def get_work_orders():
        """Get technician's work orders."""
        status_filter = request.args.getlist('status')
        lang = request.args.get('lang', 'en')
        
        orders = service.get_technician_work_orders(
            g.technician_id,
            status_filter or None,
            lang
        )
        return jsonify({"work_orders": orders})
    
    @app.route('/api/v1/work-orders/<wo_id>', methods=['GET'])
    @require_auth
    def get_work_order(wo_id):
        """Get work order details."""
        lang = request.args.get('lang', 'en')
        details = service.get_work_order_details(wo_id, lang)
        
        if details:
            return jsonify(details)
        return jsonify({"error": "Not found"}), 404
    
    @app.route('/api/v1/work-orders/<wo_id>/status', methods=['PUT'])
    @require_auth
    def update_status(wo_id):
        """Update work order status."""
        data = request.json
        result = service.update_work_order_status(
            wo_id,
            data.get("status"),
            g.technician_id,
            data.get("location"),
            data.get("notes", "")
        )
        
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
    
    @app.route('/api/v1/work-orders/<wo_id>/photos', methods=['POST'])
    @require_auth
    def add_photo(wo_id):
        """Add photo to work order."""
        data = request.json
        result = service.add_work_order_photo(wo_id, data)
        
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
    
    @app.route('/api/v1/work-orders/<wo_id>/materials', methods=['POST'])
    @require_auth
    def add_materials(wo_id):
        """Add materials to work order."""
        data = request.json
        result = service.add_materials_used(
            wo_id,
            g.technician_id,
            data.get("materials", [])
        )
        
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
    
    @app.route('/api/v1/work-orders/<wo_id>/complete', methods=['POST'])
    @require_auth
    def complete_order(wo_id):
        """Complete work order."""
        data = request.json
        result = service.complete_work_order(
            wo_id,
            g.technician_id,
            data
        )
        
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
    
    # ----- Location & Status -----
    
    @app.route('/api/v1/status', methods=['PUT'])
    @require_auth
    def update_status_location():
        """Update technician status and location."""
        data = request.json
        
        service.update_technician_status(
            g.technician_id,
            data.get("status", "available"),
            data.get("location")
        )
        
        return jsonify({"success": True})
    
    @app.route('/api/v1/location', methods=['POST'])
    @require_auth
    def update_location():
        """Update location only (for background tracking)."""
        data = request.json
        
        service.update_technician_status(
            g.technician_id,
            None,  # Don't change status
            data
        )
        
        return jsonify({"success": True})
    
    # ----- Time Tracking -----
    
    @app.route('/api/v1/timesheet', methods=['GET'])
    @require_auth
    def get_timesheet():
        """Get today's timesheet."""
        date_str = request.args.get('date')
        date = None
        if date_str:
            date = datetime.fromisoformat(date_str)
        
        timesheet = service.get_technician_timesheet(g.technician_id, date)
        return jsonify(timesheet)
    
    # ----- Sync -----
    
    @app.route('/api/v1/sync/download', methods=['GET'])
    @require_auth
    def sync_download():
        """Download data for offline use."""
        package = service.create_sync_package_for_download(
            g.technician_id,
            g.device_id
        )
        return jsonify(package)
    
    @app.route('/api/v1/sync/upload', methods=['POST'])
    @require_auth
    def sync_upload():
        """Upload offline changes."""
        data = request.json
        result = service.process_sync_upload(g.technician_id, data)
        return jsonify(result)
    
    # ----- Inventory -----
    
    @app.route('/api/v1/inventory', methods=['GET'])
    @require_auth
    def get_inventory():
        """Get vehicle inventory."""
        vehicle_id = request.args.get('vehicle_id', '')
        items = service.get_vehicle_inventory(vehicle_id)
        return jsonify({"items": items})
    
    @app.route('/api/v1/inventory/request', methods=['POST'])
    @require_auth
    def request_materials_api():
        """Request materials."""
        data = request.json
        result = service.request_materials(
            g.technician_id,
            data.get("items", [])
        )
        return jsonify(result)
    
    return app


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize service
    service = FieldAppService()
    
    # Register sample technician
    tech = Technician(
        technician_id="TECH001",
        employee_id="EMP12345",
        name="Moses Banda",
        phone="+260977123456",
        zone_ids=["ZONE_KAB", "ZONE_CBD"],
        skills=["leak_repair", "meter_installation", "pipe_replacement"]
    )
    service.register_technician(tech)
    
    # Create sample work order
    wo = MobileWorkOrder(
        work_order_id="WO_20241215_001",
        title="Major Leak Repair - Cairo Road",
        description="Pipe burst reported by community member. Estimated 50 m³/hour loss.",
        priority="critical",
        work_type="leak_repair",
        zone_id="ZONE_KAB",
        location={"lat": -15.4167, "lng": 28.2833},
        address="Plot 123, Cairo Road, Lusaka",
        technician_id="TECH001",
        assigned_at=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(hours=4),
        estimated_duration_minutes=120
    )
    service.work_orders[wo.work_order_id] = wo
    
    print("Field App Service Demo")
    print("=" * 50)
    
    # Authenticate
    auth = service.authenticate_technician("EMP12345", "1234", "device_001")
    print(f"\nAuthentication:")
    print(f"  Token: {auth['token'][:50]}...")
    print(f"  Technician: {auth['technician']['name']}")
    
    # Get work orders
    orders = service.get_technician_work_orders("TECH001", lang="en")
    print(f"\nWork Orders ({len(orders)} assigned):")
    for order in orders:
        print(f"  [{order['priority_label']}] {order['title']}")
        print(f"    Status: {order['status_label']}")
    
    # Update status
    print("\nUpdating status to 'en_route'...")
    result = service.update_work_order_status(
        "WO_20241215_001",
        "en_route",
        "TECH001",
        {"lat": -15.4100, "lng": 28.2800}
    )
    print(f"  Result: {result['new_status']}")
    
    # Get with Nyanja translation
    orders_ny = service.get_technician_work_orders("TECH001", lang="ny")
    print(f"\nIn Nyanja (Chichewa):")
    for order in orders_ny:
        print(f"  [{order['priority_label']}] {order['title']}")
        print(f"    Status: {order['status_label']}")
    
    # Sync package
    package = service.create_sync_package_for_download("TECH001", "device_001")
    print(f"\nSync Package:")
    print(f"  Package ID: {package['package_id']}")
    print(f"  Work Orders: {len(package['data']['work_orders'])}")
    print(f"  Languages: {list(package['data']['translations'].keys())}")
    
    print("\n" + "=" * 50)
    print("Creating Flask API...")
    
    # Create API
    app = create_field_app_api(service)
    
    print("\nAvailable Endpoints:")
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static'):
            print(f"  {rule.methods - {'OPTIONS', 'HEAD'}} {rule.rule}")
    
    # Uncomment to run server
    # app.run(host='0.0.0.0', port=5001, debug=True)
