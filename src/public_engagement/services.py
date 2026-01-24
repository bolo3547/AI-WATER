"""
AquaWatch NRW - Public Engagement Services
==========================================

Business logic services for public engagement module.

Services:
- PublicReportService: Create, track, and manage reports
- DuplicateDetectionService: Auto-detect and merge duplicate reports
- SpamDetectionService: Rate limiting and spam prevention
- AnalyticsService: KPI calculations and reporting
"""

import hashlib
import logging
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ReportCreateRequest:
    """Request to create a new public report."""
    tenant_id: str
    category: str  # Maps to ReportCategory enum
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_text: Optional[str] = None
    source: str = "web"  # web, whatsapp, ussd
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_consent: bool = False
    reporter_ip: Optional[str] = None
    device_fingerprint: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ReportResponse:
    """Response after creating a report."""
    success: bool
    ticket: Optional[str] = None
    message: str = ""
    tracking_url: Optional[str] = None
    spam_blocked: bool = False


@dataclass
class TrackingResponse:
    """Response for tracking a ticket."""
    ticket: str
    status: str
    status_label: str
    category: str
    area: Optional[str]
    timeline: List[Dict[str, Any]]
    created_at: str
    last_updated: str
    resolved_at: Optional[str] = None


@dataclass
class DuplicateMatch:
    """A potential duplicate report match."""
    report_id: str
    ticket: str
    distance_meters: float
    time_diff_minutes: int
    similarity_score: float
    reason: str


@dataclass
class SpamCheckResult:
    """Result of spam detection check."""
    is_spam: bool
    should_quarantine: bool
    reasons: List[str]
    rate_limit_exceeded: bool = False
    trust_adjustment: int = 0


@dataclass
class AnalyticsMetrics:
    """Analytics metrics for a tenant."""
    total_reports: int
    reports_this_month: int
    reports_by_category: Dict[str, int]
    reports_by_status: Dict[str, int]
    confirmed_count: int
    false_count: int
    confirmed_vs_false_ratio: float
    avg_response_time_hours: Optional[float]
    avg_resolution_time_hours: Optional[float]
    hotspot_areas: List[Dict[str, Any]]
    conversion_rate: float  # reports -> work orders -> resolved


# =============================================================================
# PUBLIC REPORT SERVICE
# =============================================================================

class PublicReportService:
    """
    Service for creating and managing public reports.
    
    Handles:
    - Report creation via web, WhatsApp, USSD
    - Ticket tracking for public
    - Status management for admin
    """
    
    # Public-safe status labels
    STATUS_LABELS = {
        "received": "Report Received",
        "under_review": "Under Review",
        "technician_assigned": "Team Assigned",
        "in_progress": "Work In Progress",
        "resolved": "Issue Resolved",
        "closed": "Case Closed",
    }
    
    # Status messages for timeline
    STATUS_MESSAGES = {
        "received": "Your report has been received. Thank you for helping improve water services.",
        "under_review": "Your report is being reviewed by our team.",
        "technician_assigned": "A team has been assigned to investigate this issue.",
        "in_progress": "Work is in progress to resolve this issue.",
        "resolved": "The reported issue has been resolved. Thank you for your patience.",
        "closed": "This case has been closed.",
    }
    
    def __init__(
        self,
        spam_service: Optional['SpamDetectionService'] = None,
        duplicate_service: Optional['DuplicateDetectionService'] = None,
    ):
        self.spam_service = spam_service or SpamDetectionService()
        self.duplicate_service = duplicate_service or DuplicateDetectionService()
    
    def create_report(
        self,
        request: ReportCreateRequest,
        check_spam: bool = True,
        check_duplicates: bool = True,
    ) -> ReportResponse:
        """
        Create a new public report.
        
        Args:
            request: Report creation request
            check_spam: Whether to run spam detection
            check_duplicates: Whether to check for duplicates
            
        Returns:
            ReportResponse with ticket ID if successful
        """
        # 1. Spam check
        if check_spam:
            spam_result = self.spam_service.check_report(request)
            if spam_result.is_spam and not spam_result.should_quarantine:
                logger.warning(f"Spam blocked: {spam_result.reasons}")
                return ReportResponse(
                    success=False,
                    message="Unable to process report at this time. Please try again later.",
                    spam_blocked=True,
                )
        
        # 2. Generate ticket ID
        ticket = self._generate_ticket()
        
        # 3. Hash phone for WhatsApp dedup
        phone_hash = None
        if request.reporter_phone:
            phone_hash = self._hash_phone(request.reporter_phone)
        
        # 4. Create report object (would be saved to DB in real implementation)
        report_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": request.tenant_id,
            "ticket": ticket,
            "category": request.category,
            "description": request.description,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "area_text": request.area_text,
            "source": request.source,
            "reporter_name": request.reporter_name,
            "reporter_phone": request.reporter_phone,
            "reporter_email": request.reporter_email,
            "reporter_consent": request.reporter_consent,
            "reporter_ip": request.reporter_ip,
            "device_fingerprint": request.device_fingerprint,
            "whatsapp_phone_hash": phone_hash,
            "session_id": request.session_id,
            "status": "received",
            "verification": "pending",
            "spam_flag": spam_result.should_quarantine if check_spam else False,
            "quarantine": spam_result.should_quarantine if check_spam else False,
            "trust_score_delta": spam_result.trust_adjustment if check_spam else 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # 5. Check for duplicates
        master_report_id = None
        if check_duplicates and (request.latitude and request.longitude):
            duplicates = self.duplicate_service.find_duplicates(
                tenant_id=request.tenant_id,
                latitude=request.latitude,
                longitude=request.longitude,
                category=request.category,
                created_at=datetime.utcnow(),
            )
            if duplicates:
                # Link to the first (best) match
                master_report_id = duplicates[0].report_id
                report_data["master_report_id"] = master_report_id
                report_data["is_master"] = False
        
        # 6. Generate tracking URL
        tracking_url = f"/track/{ticket}"
        
        logger.info(f"Created report: {ticket} (category={request.category}, source={request.source})")
        
        return ReportResponse(
            success=True,
            ticket=ticket,
            message="Your report has been submitted successfully.",
            tracking_url=tracking_url,
        )
    
    def get_tracking_info(
        self,
        tenant_id: str,
        ticket: str,
    ) -> Optional[TrackingResponse]:
        """
        Get public-safe tracking information for a ticket.
        
        Args:
            tenant_id: Tenant identifier
            ticket: Ticket ID
            
        Returns:
            TrackingResponse or None if not found
        """
        # In real implementation, this would query the database
        # For now, return mock data structure
        
        # Mock response
        return TrackingResponse(
            ticket=ticket,
            status="under_review",
            status_label=self.STATUS_LABELS.get("under_review", "Unknown"),
            category="leak",
            area="Central Business District",
            timeline=[
                {
                    "status": "received",
                    "message": self.STATUS_MESSAGES["received"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "status": "under_review",
                    "message": self.STATUS_MESSAGES["under_review"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ],
            created_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
        )
    
    def update_status(
        self,
        tenant_id: str,
        report_id: str,
        new_status: str,
        actor_user_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update report status (admin function).
        
        Args:
            tenant_id: Tenant identifier
            report_id: Report UUID
            new_status: New status value
            actor_user_id: User making the change
            notes: Optional notes
            
        Returns:
            True if successful
        """
        # Validate status transition
        valid_statuses = ["received", "under_review", "technician_assigned", 
                        "in_progress", "resolved", "closed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        # Would update database and create timeline entry
        logger.info(f"Status updated: {report_id} -> {new_status} by {actor_user_id}")
        
        return True
    
    def assign_report(
        self,
        tenant_id: str,
        report_id: str,
        user_id: str,
        team: Optional[str] = None,
        actor_user_id: Optional[str] = None,
    ) -> bool:
        """
        Assign a report to a technician/team.
        
        Args:
            tenant_id: Tenant identifier
            report_id: Report UUID
            user_id: User to assign to
            team: Team name
            actor_user_id: User making the assignment
            
        Returns:
            True if successful
        """
        # Would update database
        logger.info(f"Report {report_id} assigned to {user_id} (team={team})")
        
        # Auto-update status to technician_assigned
        self.update_status(tenant_id, report_id, "technician_assigned", actor_user_id)
        
        return True
    
    def link_to_ai_leak(
        self,
        tenant_id: str,
        report_id: str,
        leak_id: str,
        boost_confidence: bool = True,
    ) -> bool:
        """
        Link a public report to an AI-detected leak.
        
        Args:
            tenant_id: Tenant identifier
            report_id: Report UUID
            leak_id: LeakEvent UUID
            boost_confidence: Whether to boost leak confidence
            
        Returns:
            True if successful
        """
        # Would update report.linked_leak_id
        # Optionally boost leak confidence score
        logger.info(f"Report {report_id} linked to leak {leak_id}")
        
        return True
    
    def create_work_order_from_report(
        self,
        tenant_id: str,
        report_id: str,
        actor_user_id: str,
        priority: int = 3,
        notes: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a work order from a public report.
        
        Args:
            tenant_id: Tenant identifier
            report_id: Report UUID
            actor_user_id: User creating the work order
            priority: Work order priority (1=highest)
            notes: Additional notes
            
        Returns:
            Work order ID if successful
        """
        # Would create WorkOrder and link it
        work_order_id = str(uuid.uuid4())
        work_order_number = f"WO-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"
        
        logger.info(f"Work order {work_order_number} created from report {report_id}")
        
        return work_order_id
    
    def _generate_ticket(self) -> str:
        """Generate a unique ticket ID."""
        import secrets
        import string
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(6))
        return f"TKT-{random_part}"
    
    def _hash_phone(self, phone: str) -> str:
        """Hash phone number for duplicate detection without storing raw number."""
        normalized = re.sub(r'\D', '', phone)
        return hashlib.sha256(normalized.encode()).hexdigest()


# =============================================================================
# DUPLICATE DETECTION SERVICE
# =============================================================================

class DuplicateDetectionService:
    """
    Service for detecting and merging duplicate reports.
    
    Auto-merge rules:
    - Within 100 meters distance
    - Within 30 minutes time window
    - Same or similar category
    """
    
    # Configuration
    MAX_DISTANCE_METERS = 100
    MAX_TIME_WINDOW_MINUTES = 30
    MIN_SIMILARITY_SCORE = 0.6
    
    # Category similarity (some categories are related)
    CATEGORY_SIMILARITY = {
        ("leak", "burst"): 0.8,
        ("no_water", "low_pressure"): 0.6,
        ("overflow", "leak"): 0.5,
    }
    
    def __init__(self, existing_reports: Optional[List[Dict]] = None):
        """
        Initialize with optional list of existing reports for matching.
        
        In real implementation, this would query the database.
        """
        self.existing_reports = existing_reports or []
    
    def find_duplicates(
        self,
        tenant_id: str,
        latitude: float,
        longitude: float,
        category: str,
        created_at: datetime,
        time_window_minutes: int = None,
        distance_meters: int = None,
    ) -> List[DuplicateMatch]:
        """
        Find potential duplicate reports.
        
        Args:
            tenant_id: Tenant identifier
            latitude: Report latitude
            longitude: Report longitude
            category: Report category
            created_at: Report timestamp
            time_window_minutes: Custom time window (default: 30)
            distance_meters: Custom distance threshold (default: 100)
            
        Returns:
            List of potential duplicate matches, sorted by similarity
        """
        time_window = time_window_minutes or self.MAX_TIME_WINDOW_MINUTES
        distance_threshold = distance_meters or self.MAX_DISTANCE_METERS
        
        matches = []
        
        # Would query database for recent reports in area
        # For now, search through existing_reports
        for report in self.existing_reports:
            if report.get("tenant_id") != tenant_id:
                continue
            
            # Check time window
            report_time = datetime.fromisoformat(report.get("created_at", ""))
            time_diff = abs((created_at - report_time).total_seconds() / 60)
            if time_diff > time_window:
                continue
            
            # Check distance
            report_lat = report.get("latitude")
            report_lon = report.get("longitude")
            if report_lat is None or report_lon is None:
                continue
            
            distance = self._haversine_distance(
                latitude, longitude,
                report_lat, report_lon
            )
            if distance > distance_threshold:
                continue
            
            # Calculate similarity
            category_score = self._category_similarity(category, report.get("category", ""))
            distance_score = 1 - (distance / distance_threshold)
            time_score = 1 - (time_diff / time_window)
            
            similarity = (category_score * 0.4 + distance_score * 0.35 + time_score * 0.25)
            
            if similarity >= self.MIN_SIMILARITY_SCORE:
                matches.append(DuplicateMatch(
                    report_id=report.get("id"),
                    ticket=report.get("ticket"),
                    distance_meters=distance,
                    time_diff_minutes=int(time_diff),
                    similarity_score=similarity,
                    reason=self._get_match_reason(distance, time_diff, category, report.get("category")),
                ))
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        
        return matches
    
    def merge_reports(
        self,
        tenant_id: str,
        master_report_id: str,
        duplicate_report_ids: List[str],
        actor_user_id: str,
        reason: str = "manual",
    ) -> bool:
        """
        Merge duplicate reports under a master.
        
        Args:
            tenant_id: Tenant identifier
            master_report_id: The master report
            duplicate_report_ids: Reports to merge as duplicates
            actor_user_id: User performing merge
            reason: Reason for merge
            
        Returns:
            True if successful
        """
        # Would create PublicReportLink entries and update reports
        for dup_id in duplicate_report_ids:
            logger.info(f"Merged report {dup_id} into master {master_report_id}")
        
        return True
    
    def unmerge_report(
        self,
        tenant_id: str,
        duplicate_report_id: str,
        actor_user_id: str,
    ) -> bool:
        """
        Remove a report from its master.
        
        Args:
            tenant_id: Tenant identifier
            duplicate_report_id: Report to unmerge
            actor_user_id: User performing unmerge
            
        Returns:
            True if successful
        """
        # Would delete PublicReportLink and update report
        logger.info(f"Unmerged report {duplicate_report_id}")
        
        return True
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _category_similarity(self, cat1: str, cat2: str) -> float:
        """Calculate similarity between two categories."""
        if cat1 == cat2:
            return 1.0
        
        # Check defined similarities
        pair = tuple(sorted([cat1, cat2]))
        for (c1, c2), score in self.CATEGORY_SIMILARITY.items():
            if (c1, c2) == pair or (c2, c1) == pair:
                return score
        
        return 0.3  # Default low similarity for different categories
    
    def _get_match_reason(
        self,
        distance: float,
        time_diff: float,
        new_cat: str,
        existing_cat: str,
    ) -> str:
        """Generate human-readable match reason."""
        reasons = []
        
        if distance < 50:
            reasons.append("very close location")
        elif distance < 100:
            reasons.append("nearby location")
        
        if time_diff < 10:
            reasons.append("reported at similar time")
        elif time_diff < 30:
            reasons.append("reported within 30 minutes")
        
        if new_cat == existing_cat:
            reasons.append(f"same category ({new_cat})")
        else:
            reasons.append(f"related categories ({new_cat}/{existing_cat})")
        
        return "; ".join(reasons)


# =============================================================================
# SPAM DETECTION SERVICE
# =============================================================================

class SpamDetectionService:
    """
    Service for detecting spam and rate limiting.
    
    Rules:
    - Rate limit by IP/device signature
    - Flag repeated submissions too fast
    - Flag reports with no location and empty description
    - Flag repeated text patterns
    """
    
    # Configuration
    MAX_REPORTS_PER_IP_PER_HOUR = 5
    MAX_REPORTS_PER_DEVICE_PER_HOUR = 5
    MIN_SUBMISSION_INTERVAL_SECONDS = 60
    MIN_DESCRIPTION_LENGTH = 10
    
    def __init__(self):
        # In-memory rate tracking (would use Redis in production)
        self._ip_counts: Dict[str, List[datetime]] = defaultdict(list)
        self._device_counts: Dict[str, List[datetime]] = defaultdict(list)
        self._text_hashes: Dict[str, List[datetime]] = defaultdict(list)
    
    def check_report(self, request: ReportCreateRequest) -> SpamCheckResult:
        """
        Check if a report request should be blocked or quarantined.
        
        Args:
            request: Report creation request
            
        Returns:
            SpamCheckResult with spam determination
        """
        reasons = []
        is_spam = False
        should_quarantine = False
        rate_limit_exceeded = False
        trust_adjustment = 0
        
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # 1. IP rate limiting
        if request.reporter_ip:
            self._ip_counts[request.reporter_ip] = [
                t for t in self._ip_counts[request.reporter_ip]
                if t > hour_ago
            ]
            if len(self._ip_counts[request.reporter_ip]) >= self.MAX_REPORTS_PER_IP_PER_HOUR:
                reasons.append("IP rate limit exceeded")
                rate_limit_exceeded = True
                is_spam = True
        
        # 2. Device fingerprint rate limiting
        if request.device_fingerprint:
            self._device_counts[request.device_fingerprint] = [
                t for t in self._device_counts[request.device_fingerprint]
                if t > hour_ago
            ]
            if len(self._device_counts[request.device_fingerprint]) >= self.MAX_REPORTS_PER_DEVICE_PER_HOUR:
                reasons.append("Device rate limit exceeded")
                rate_limit_exceeded = True
                is_spam = True
        
        # 3. Check for empty/minimal content
        has_location = request.latitude is not None and request.longitude is not None
        has_area = request.area_text and len(request.area_text.strip()) > 5
        has_description = request.description and len(request.description.strip()) >= self.MIN_DESCRIPTION_LENGTH
        
        if not has_location and not has_area and not has_description:
            reasons.append("No location and empty description")
            should_quarantine = True
            trust_adjustment = -10
        
        # 4. Check for repeated text (spam pattern)
        if request.description:
            text_hash = hashlib.md5(request.description.lower().strip().encode()).hexdigest()
            self._text_hashes[text_hash] = [
                t for t in self._text_hashes[text_hash]
                if t > hour_ago
            ]
            if len(self._text_hashes[text_hash]) >= 3:
                reasons.append("Repeated text pattern detected")
                is_spam = True
                trust_adjustment = -20
        
        # 5. Suspicious patterns in description
        if request.description:
            desc_lower = request.description.lower()
            suspicious_patterns = [
                "test", "asdf", "xxx", "123456",
                "http://", "https://", "www.",  # URLs in description
                "call me", "contact me at",  # Spam patterns
            ]
            for pattern in suspicious_patterns:
                if pattern in desc_lower:
                    reasons.append(f"Suspicious pattern: {pattern}")
                    should_quarantine = True
                    break
        
        # Record this request for future rate limiting
        if request.reporter_ip:
            self._ip_counts[request.reporter_ip].append(now)
        if request.device_fingerprint:
            self._device_counts[request.device_fingerprint].append(now)
        if request.description:
            text_hash = hashlib.md5(request.description.lower().strip().encode()).hexdigest()
            self._text_hashes[text_hash].append(now)
        
        return SpamCheckResult(
            is_spam=is_spam,
            should_quarantine=should_quarantine,
            reasons=reasons,
            rate_limit_exceeded=rate_limit_exceeded,
            trust_adjustment=trust_adjustment,
        )
    
    def clear_rate_limits(self, ip: Optional[str] = None, device: Optional[str] = None):
        """Clear rate limits for testing or admin override."""
        if ip and ip in self._ip_counts:
            del self._ip_counts[ip]
        if device and device in self._device_counts:
            del self._device_counts[device]


# =============================================================================
# ANALYTICS SERVICE
# =============================================================================

class AnalyticsService:
    """
    Service for generating analytics and KPIs for public engagement.
    
    Metrics:
    - Total reports by month
    - Confirmed vs false ratio
    - Average response time
    - Average resolution time
    - Hotspot areas
    - Conversion rate (reports -> work orders -> resolved)
    """
    
    def get_metrics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnalyticsMetrics:
        """
        Calculate analytics metrics for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            
        Returns:
            AnalyticsMetrics with calculated values
        """
        # Default date range
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # In real implementation, these would be database queries
        # For now, return mock metrics
        
        return AnalyticsMetrics(
            total_reports=1250,
            reports_this_month=156,
            reports_by_category={
                "leak": 420,
                "burst": 180,
                "no_water": 280,
                "low_pressure": 190,
                "illegal_connection": 85,
                "overflow": 65,
                "contamination": 15,
                "other": 15,
            },
            reports_by_status={
                "received": 45,
                "under_review": 28,
                "technician_assigned": 32,
                "in_progress": 18,
                "resolved": 890,
                "closed": 237,
            },
            confirmed_count=925,
            false_count=150,
            confirmed_vs_false_ratio=6.17,
            avg_response_time_hours=2.4,  # received -> assigned
            avg_resolution_time_hours=18.6,  # received -> resolved
            hotspot_areas=[
                {"area": "Central Business District", "count": 145, "lat": -15.4167, "lon": 28.2833},
                {"area": "Chilenje South", "count": 98, "lat": -15.4521, "lon": 28.2654},
                {"area": "Kabulonga", "count": 87, "lat": -15.3987, "lon": 28.3123},
                {"area": "Matero", "count": 76, "lat": -15.3654, "lon": 28.2456},
                {"area": "Garden Compound", "count": 65, "lat": -15.4234, "lon": 28.2987},
            ],
            conversion_rate=0.74,  # 74% of reports result in resolved work orders
        )
    
    def get_monthly_trend(
        self,
        tenant_id: str,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Get monthly report trends.
        
        Args:
            tenant_id: Tenant identifier
            months: Number of months to include
            
        Returns:
            List of monthly statistics
        """
        # Mock monthly data
        import random
        trend = []
        now = datetime.utcnow()
        
        for i in range(months - 1, -1, -1):
            month_date = now - timedelta(days=i * 30)
            trend.append({
                "month": month_date.strftime("%Y-%m"),
                "month_label": month_date.strftime("%b %Y"),
                "total": random.randint(80, 180),
                "confirmed": random.randint(60, 140),
                "false": random.randint(10, 30),
                "resolved": random.randint(50, 120),
            })
        
        return trend
    
    def export_csv(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        include_contact_info: bool = False,
    ) -> str:
        """
        Export reports to CSV format.
        
        Args:
            tenant_id: Tenant identifier
            start_date: Start date
            end_date: End date
            include_contact_info: Include reporter contact (admin only)
            
        Returns:
            CSV string
        """
        import csv
        import io
        
        output = io.StringIO()
        
        # Define columns (without contact info for public exports)
        columns = [
            "ticket", "category", "status", "verification",
            "area_text", "latitude", "longitude",
            "source", "created_at", "resolved_at",
        ]
        
        if include_contact_info:
            columns.extend(["reporter_name", "reporter_phone", "reporter_email"])
        
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        
        # Would iterate through database results
        # For now, write sample row
        writer.writerow({
            "ticket": "TKT-ABC123",
            "category": "leak",
            "status": "resolved",
            "verification": "confirmed",
            "area_text": "Central Business District",
            "latitude": -15.4167,
            "longitude": 28.2833,
            "source": "web",
            "created_at": "2026-01-15T08:30:00Z",
            "resolved_at": "2026-01-15T14:45:00Z",
        })
        
        return output.getvalue()
