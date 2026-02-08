"""
AquaWatch NRW - Community Reporting Portal
==========================================

Citizen engagement platform for leak reporting and utility feedback.

Features:
- Geo-tagged photo leak reports
- Report tracking with status updates
- Gamification and rewards
- Public utility scoreboard
- Water conservation tips
- Multi-language support (English, Nyanja, Bemba)

Designed for Zambia/South Africa communities.
"""

import os
import logging
import uuid
import hashlib
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ReportType(Enum):
    LEAK = "leak"
    BURST = "burst"
    LOW_PRESSURE = "low_pressure"
    NO_WATER = "no_water"
    DIRTY_WATER = "dirty_water"
    METER_ISSUE = "meter_issue"
    ILLEGAL_CONNECTION = "illegal_connection"
    VANDALISM = "vandalism"
    SUGGESTION = "suggestion"
    COMPLIMENT = "compliment"


class ReportStatus(Enum):
    SUBMITTED = "submitted"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"
    INVALID = "invalid"


class RewardType(Enum):
    POINTS = "points"
    BADGE = "badge"
    DISCOUNT = "discount"


@dataclass
class CommunityUser:
    """Community member/citizen."""
    user_id: str
    phone: str
    name: str = ""
    email: str = ""
    language: str = "en"  # en, ny, bem
    
    # Location
    area: str = ""
    zone_id: str = ""
    account_number: str = ""  # Utility account if customer
    
    # Gamification
    points: int = 0
    reports_submitted: int = 0
    reports_verified: int = 0
    badges: List[str] = field(default_factory=list)
    level: int = 1
    
    # Status
    verified: bool = False
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def level_title(self) -> str:
        titles = {
            1: "Water Watcher",
            2: "Leak Spotter",
            3: "Community Guardian",
            4: "Water Champion",
            5: "Conservation Hero"
        }
        return titles.get(self.level, "Water Watcher")


@dataclass
class Photo:
    """Photo evidence from community report."""
    photo_id: str
    url: str
    thumbnail_url: str = ""
    caption: str = ""
    
    # Metadata
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    taken_at: Optional[datetime] = None
    file_size_kb: int = 0


@dataclass
class CommunityReport:
    """Leak or issue report from community."""
    report_id: str
    user_id: str
    report_type: ReportType
    status: ReportStatus
    
    # Location
    latitude: float
    longitude: float
    address: str = ""
    landmark: str = ""
    zone_id: str = ""
    
    # Details
    description: str = ""
    urgency: str = "normal"  # low, normal, high, emergency
    photos: List[Photo] = field(default_factory=list)
    
    # Internal
    work_order_id: Optional[str] = None
    assigned_to: Optional[str] = None
    verified: bool = False
    verification_notes: str = ""
    
    # Timestamps
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Feedback
    resolution_notes: str = ""
    user_rating: Optional[int] = None  # 1-5
    user_feedback: str = ""
    
    # Tracking
    tracking_code: str = ""
    
    # Rewards
    points_awarded: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "tracking_code": self.tracking_code,
            "tracking_url": f"{TRACKING_URL_PATH}/{self.tracking_code}" if self.tracking_code else None,
            "type": self.report_type.value,
            "status": self.status.value,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "address": self.address,
                "landmark": self.landmark
            },
            "description": self.description,
            "urgency": self.urgency,
            "photos": [{"url": p.url, "caption": p.caption} for p in self.photos],
            "submitted_at": self.submitted_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "verified": self.verified
        }


@dataclass
class Badge:
    """Achievement badge."""
    badge_id: str
    name: str
    description: str
    icon: str
    points_value: int = 0
    criteria: str = ""


@dataclass
class Reward:
    """Reward for user."""
    reward_id: str
    user_id: str
    reward_type: RewardType
    value: Any  # points amount, badge_id, discount code
    reason: str = ""
    awarded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    claimed: bool = False


# =============================================================================
# GAMIFICATION SYSTEM
# =============================================================================

# Badge definitions
BADGES = {
    "first_report": Badge(
        badge_id="first_report",
        name="First Report",
        description="Submitted your first leak report",
        icon="🏅",
        points_value=50,
        criteria="Submit 1 report"
    ),
    "verified_reporter": Badge(
        badge_id="verified_reporter",
        name="Verified Reporter",
        description="3 of your reports have been verified",
        icon="✅",
        points_value=100,
        criteria="3 verified reports"
    ),
    "eagle_eye": Badge(
        badge_id="eagle_eye",
        name="Eagle Eye",
        description="Reported 10 leaks",
        icon="🦅",
        points_value=200,
        criteria="10 reports"
    ),
    "water_saver": Badge(
        badge_id="water_saver",
        name="Water Saver",
        description="Your reports helped save 10,000L of water",
        icon="💧",
        points_value=500,
        criteria="10,000L saved"
    ),
    "community_champion": Badge(
        badge_id="community_champion",
        name="Community Champion",
        description="Top reporter in your zone for the month",
        icon="🏆",
        points_value=300,
        criteria="Monthly top reporter"
    ),
    "quick_responder": Badge(
        badge_id="quick_responder",
        name="Quick Responder",
        description="Reported an emergency within 5 minutes of seeing it",
        icon="⚡",
        points_value=150,
        criteria="Emergency report within 5 min"
    )
}

# Points system
POINTS_CONFIG = {
    "report_submitted": 10,
    "report_verified": 25,
    "report_resolved": 15,
    "photo_attached": 5,
    "detailed_description": 5,
    "emergency_report": 20,
    "burst_report": 30,
    "feedback_provided": 5,
    "referral": 50
}

# Level thresholds
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 300,
    4: 700,
    5: 1500
}

# Tracking URL base path
TRACKING_URL_PATH = "/track"


# =============================================================================
# MULTILINGUAL MESSAGES
# =============================================================================

MESSAGES = {
    "report_received": {
        "en": "Thank you! Your report #{report_id} has been received. Track it at: {tracking_url}",
        "ny": "Zikomo! Lipoti lanu #{report_id} lalandilidwa. Liyang'aneni pa: {tracking_url}",
        "bem": "Natotela! Amalyashi yenu #{report_id} yasangwa. Moneni pa: {tracking_url}"
    },
    "report_verified": {
        "en": "Your leak report #{report_id} has been verified. Thank you for helping save water!",
        "ny": "Lipoti lanu la madzi otayika #{report_id} latsimikizidwa. Zikomo potithandiza kusunga madzi!",
        "bem": "Ifilyashi fya menshi fyasungwa #{report_id} fyafikilishiwa. Natotela pa kutwafikilisha!"
    },
    "report_resolved": {
        "en": "Good news! The issue you reported #{report_id} has been resolved. You earned {points} points!",
        "ny": "Nkhani zabwino! Vuto mwalonjeza #{report_id} lakonzedwa. Mwapeza {points} ma points!",
        "bem": "Amashiwi ayasuma! Ubupusana bwamwalyashi #{report_id} bwakonkanyiwa. Mwasanga {points} points!"
    },
    "badge_earned": {
        "en": "🎉 Congratulations! You earned the '{badge_name}' badge!",
        "ny": "🎉 Msandizeni! Mwapeza njira '{badge_name}'!",
        "bem": "🎉 Bakondele! Mwasanga '{badge_name}'!"
    },
    "level_up": {
        "en": "🎊 Level up! You are now a {level_title}!",
        "ny": "🎊 Mwakwera! Tsopano ndinu {level_title}!",
        "bem": "🎊 Mwakwela! Nomba muli {level_title}!"
    }
}


def get_message(key: str, language: str, **kwargs) -> str:
    """Get localized message."""
    messages = MESSAGES.get(key, {})
    template = messages.get(language, messages.get("en", ""))
    return template.format(**kwargs)


# =============================================================================
# COMMUNITY PORTAL SERVICE
# =============================================================================

class CommunityPortalService:
    """
    Community engagement portal for water utilities.
    
    Features:
    - Report submission and tracking
    - User management and gamification
    - Public utility scoreboard
    - Analytics and reporting
    """
    
    def __init__(self):
        # In-memory stores
        self.users: Dict[str, CommunityUser] = {}
        self.reports: Dict[str, CommunityReport] = {}
        self.rewards: List[Reward] = []
        
        # Stats
        self.stats = {
            "total_reports": 0,
            "resolved_reports": 0,
            "total_water_saved_liters": 0,
            "total_points_awarded": 0,
            "active_users": 0
        }
        
        logger.info("CommunityPortalService initialized")
    
    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================
    
    def register_user(
        self,
        phone: str,
        name: str = "",
        language: str = "en",
        area: str = "",
        account_number: str = ""
    ) -> CommunityUser:
        """Register a new community user."""
        # Generate user ID from phone hash
        user_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
        
        if user_id in self.users:
            return self.users[user_id]
        
        user = CommunityUser(
            user_id=user_id,
            phone=phone,
            name=name,
            language=language,
            area=area,
            account_number=account_number
        )
        
        self.users[user_id] = user
        self.stats["active_users"] += 1
        
        logger.info(f"Registered user: {user_id}")
        return user
    
    def get_user(self, user_id: str) -> Optional[CommunityUser]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_phone(self, phone: str) -> Optional[CommunityUser]:
        """Get user by phone number."""
        user_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
        return self.users.get(user_id)
    
    def update_user_language(self, user_id: str, language: str):
        """Update user's preferred language."""
        if user_id in self.users:
            self.users[user_id].language = language
    
    # =========================================================================
    # REPORT SUBMISSION
    # =========================================================================
    
    def submit_report(
        self,
        user_id: str,
        report_type: ReportType,
        latitude: float,
        longitude: float,
        description: str = "",
        address: str = "",
        landmark: str = "",
        urgency: str = "normal",
        photos: List[Photo] = None
    ) -> CommunityReport:
        """Submit a new community report."""
        if user_id not in self.users:
            raise ValueError("User not registered")
        
        report_id = f"CR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        tracking_code = self._generate_tracking_code()
        
        report = CommunityReport(
            report_id=report_id,
            user_id=user_id,
            report_type=report_type,
            status=ReportStatus.SUBMITTED,
            latitude=latitude,
            longitude=longitude,
            description=description,
            address=address,
            landmark=landmark,
            urgency=urgency,
            photos=photos or [],
            tracking_code=tracking_code,
        )
        
        self.reports[report_id] = report
        self.stats["total_reports"] += 1
        
        # Update user stats
        user = self.users[user_id]
        user.reports_submitted += 1
        
        # Award points
        points = POINTS_CONFIG["report_submitted"]
        if photos:
            points += POINTS_CONFIG["photo_attached"] * len(photos)
        if len(description) > 50:
            points += POINTS_CONFIG["detailed_description"]
        if urgency == "emergency":
            points += POINTS_CONFIG["emergency_report"]
        if report_type == ReportType.BURST:
            points += POINTS_CONFIG["burst_report"]
        
        self._award_points(user, points, f"Report {report_id} submitted")
        report.points_awarded = points
        
        # Check for badges
        self._check_badges(user)
        
        logger.info(f"Report submitted: {report_id} by {user_id} (tracking: {tracking_code})")
        
        return report
    
    def get_report(self, report_id: str) -> Optional[CommunityReport]:
        """Get report by ID."""
        return self.reports.get(report_id)
    
    def get_reports_by_user(self, user_id: str) -> List[CommunityReport]:
        """Get all reports by a user."""
        return [r for r in self.reports.values() if r.user_id == user_id]
    
    def get_reports_by_status(self, status: ReportStatus) -> List[CommunityReport]:
        """Get reports by status."""
        return [r for r in self.reports.values() if r.status == status]
    
    def get_reports_in_zone(self, zone_id: str) -> List[CommunityReport]:
        """Get reports in a zone."""
        return [r for r in self.reports.values() if r.zone_id == zone_id]
    
    # =========================================================================
    # REPORT UPDATES
    # =========================================================================
    
    def acknowledge_report(self, report_id: str) -> bool:
        """Acknowledge receipt of report."""
        if report_id not in self.reports:
            return False
        
        report = self.reports[report_id]
        report.status = ReportStatus.RECEIVED
        report.acknowledged_at = datetime.now(timezone.utc)
        
        # Notify user
        user = self.users.get(report.user_id)
        if user:
            message = get_message(
                "report_received",
                user.language,
                report_id=report_id,
                tracking_url=f"{TRACKING_URL_PATH}/{report.tracking_code}"
            )
            # TODO: Send SMS/notification
            logger.info(f"Would send to {user.phone}: {message}")
            
            # Send notification via notification service
            try:
                from src.notifications.notification_service import notification_service, NotificationSeverity, NotificationChannel
                import asyncio
                
                channels = [NotificationChannel.IN_APP]
                if user.phone:
                    channels.append(NotificationChannel.SMS)
                
                asyncio.run(notification_service.send(
                    tenant_id="community",
                    user_id=report.user_id,
                    title="Report Received",
                    message=message,
                    severity=NotificationSeverity.INFO,
                    channels=channels,
                    category="report_acknowledgment",
                    source_type="community_report",
                    source_id=report_id,
                    recipient_phone=user.phone,
                    recipient_name=user.name,
                ))
                    
                logger.info(f"Acknowledgment notification sent to {user.name}")
            except Exception as e:
                logger.error(f"Failed to send report acknowledgment notification: {e}")
        
        return True
    
    def verify_report(
        self, 
        report_id: str, 
        verified: bool = True,
        notes: str = ""
    ) -> bool:
        """Verify or reject a report."""
        if report_id not in self.reports:
            return False
        
        report = self.reports[report_id]
        report.verified = verified
        report.verification_notes = notes
        
        if verified:
            report.status = ReportStatus.UNDER_REVIEW
            
            # Award verification bonus
            user = self.users.get(report.user_id)
            if user:
                user.reports_verified += 1
                self._award_points(user, POINTS_CONFIG["report_verified"], f"Report {report_id} verified")
                self._check_badges(user)
                
                message = get_message("report_verified", user.language, report_id=report_id)
                logger.info(f"Would send to {user.phone}: {message}")
        else:
            report.status = ReportStatus.INVALID
        
        return True
    
    def assign_report(self, report_id: str, work_order_id: str):
        """Assign report to a work order."""
        if report_id not in self.reports:
            return False
        
        report = self.reports[report_id]
        report.work_order_id = work_order_id
        report.status = ReportStatus.DISPATCHED
        
        return True
    
    def update_report_status(
        self, 
        report_id: str, 
        status: ReportStatus,
        notes: str = ""
    ):
        """Update report status."""
        if report_id not in self.reports:
            return
        
        report = self.reports[report_id]
        report.status = status
        
        if notes:
            report.resolution_notes = notes
    
    def resolve_report(
        self, 
        report_id: str,
        resolution_notes: str = "",
        water_saved_liters: float = 0
    ) -> bool:
        """Mark report as resolved."""
        if report_id not in self.reports:
            return False
        
        report = self.reports[report_id]
        report.status = ReportStatus.RESOLVED
        report.resolved_at = datetime.now(timezone.utc)
        report.resolution_notes = resolution_notes
        
        self.stats["resolved_reports"] += 1
        self.stats["total_water_saved_liters"] += water_saved_liters
        
        # Award resolution bonus
        user = self.users.get(report.user_id)
        if user:
            self._award_points(user, POINTS_CONFIG["report_resolved"], f"Report {report_id} resolved")
            
            message = get_message(
                "report_resolved",
                user.language,
                report_id=report_id,
                points=POINTS_CONFIG["report_resolved"]
            )
            logger.info(f"Would send to {user.phone}: {message}")
        
        return True
    
    def submit_feedback(
        self, 
        report_id: str, 
        rating: int, 
        feedback: str = ""
    ):
        """Submit user feedback for resolved report."""
        if report_id not in self.reports:
            return
        
        report = self.reports[report_id]
        report.user_rating = rating
        report.user_feedback = feedback
        report.status = ReportStatus.CLOSED
        
        # Award feedback bonus
        user = self.users.get(report.user_id)
        if user:
            self._award_points(user, POINTS_CONFIG["feedback_provided"], "Feedback provided")
    
    # =========================================================================
    # TRACKING CODE GENERATION
    # =========================================================================
    
    def _generate_tracking_code(self) -> str:
        """Generate a unique tracking code for a report. Format: TRK-XXXXXX."""
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(6))
        return f"TRK-{random_part}"
    
    # =========================================================================
    # GAMIFICATION
    # =========================================================================
    
    def _award_points(self, user: CommunityUser, points: int, reason: str):
        """Award points to a user."""
        user.points += points
        self.stats["total_points_awarded"] += points
        
        # Record reward
        self.rewards.append(Reward(
            reward_id=str(uuid.uuid4())[:8],
            user_id=user.user_id,
            reward_type=RewardType.POINTS,
            value=points,
            reason=reason
        ))
        
        # Check for level up
        self._check_level_up(user)
    
    def _check_level_up(self, user: CommunityUser):
        """Check if user has leveled up."""
        for level, threshold in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
            if user.points >= threshold and user.level < level:
                user.level = level
                
                message = get_message(
                    "level_up",
                    user.language,
                    level_title=user.level_title
                )
                logger.info(f"User {user.user_id} leveled up to {level}: {message}")
                break
    
    def _check_badges(self, user: CommunityUser):
        """Check and award badges."""
        # First report badge
        if user.reports_submitted >= 1 and "first_report" not in user.badges:
            self._award_badge(user, "first_report")
        
        # Verified reporter badge
        if user.reports_verified >= 3 and "verified_reporter" not in user.badges:
            self._award_badge(user, "verified_reporter")
        
        # Eagle eye badge
        if user.reports_submitted >= 10 and "eagle_eye" not in user.badges:
            self._award_badge(user, "eagle_eye")
    
    def _award_badge(self, user: CommunityUser, badge_id: str):
        """Award a badge to user."""
        if badge_id not in BADGES:
            return
        
        badge = BADGES[badge_id]
        user.badges.append(badge_id)
        
        # Award badge points
        self._award_points(user, badge.points_value, f"Badge: {badge.name}")
        
        # Record reward
        self.rewards.append(Reward(
            reward_id=str(uuid.uuid4())[:8],
            user_id=user.user_id,
            reward_type=RewardType.BADGE,
            value=badge_id,
            reason=f"Earned badge: {badge.name}"
        ))
        
        message = get_message("badge_earned", user.language, badge_name=badge.name)
        logger.info(f"User {user.user_id} earned badge: {message}")
    
    # =========================================================================
    # LEADERBOARD & ANALYTICS
    # =========================================================================
    
    def get_leaderboard(
        self, 
        zone_id: str = None, 
        limit: int = 10
    ) -> List[Dict]:
        """Get leaderboard of top reporters."""
        users = list(self.users.values())
        
        if zone_id:
            users = [u for u in users if u.zone_id == zone_id]
        
        users.sort(key=lambda u: u.points, reverse=True)
        
        return [
            {
                "rank": i + 1,
                "name": u.name or f"User {u.user_id[:6]}",
                "points": u.points,
                "level": u.level,
                "level_title": u.level_title,
                "reports": u.reports_submitted,
                "verified": u.reports_verified,
                "badges": len(u.badges)
            }
            for i, u in enumerate(users[:limit])
        ]
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile with stats and badges."""
        user = self.users.get(user_id)
        if not user:
            return {}
        
        return {
            "user_id": user.user_id,
            "name": user.name or f"User {user.user_id[:6]}",
            "level": user.level,
            "level_title": user.level_title,
            "points": user.points,
            "next_level_points": LEVEL_THRESHOLDS.get(user.level + 1, user.points),
            "reports_submitted": user.reports_submitted,
            "reports_verified": user.reports_verified,
            "badges": [
                {
                    "id": badge_id,
                    "name": BADGES[badge_id].name,
                    "icon": BADGES[badge_id].icon,
                    "description": BADGES[badge_id].description
                }
                for badge_id in user.badges if badge_id in BADGES
            ],
            "recent_activity": self._get_user_activity(user_id, limit=5),
            "member_since": user.created_at.strftime("%B %Y")
        }
    
    def _get_user_activity(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent user activity."""
        user_reports = sorted(
            [r for r in self.reports.values() if r.user_id == user_id],
            key=lambda r: r.submitted_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "report_id": r.report_id,
                "type": r.report_type.value,
                "status": r.status.value,
                "submitted_at": r.submitted_at.isoformat(),
                "points_earned": r.points_awarded
            }
            for r in user_reports
        ]
    
    def get_public_stats(self, zone_id: str = None) -> Dict:
        """Get public statistics for utility transparency."""
        reports = list(self.reports.values())
        if zone_id:
            reports = [r for r in reports if r.zone_id == zone_id]
        
        resolved = [r for r in reports if r.status == ReportStatus.RESOLVED]
        
        avg_resolution_time = None
        if resolved:
            resolution_times = [
                (r.resolved_at - r.submitted_at).total_seconds() / 3600
                for r in resolved if r.resolved_at
            ]
            if resolution_times:
                avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1)
        
        # Calculate grade
        if len(reports) > 0:
            resolution_rate = len(resolved) / len(reports) * 100
            if resolution_rate >= 90:
                grade = "A"
            elif resolution_rate >= 75:
                grade = "B"
            elif resolution_rate >= 60:
                grade = "C"
            elif resolution_rate >= 40:
                grade = "D"
            else:
                grade = "F"
        else:
            resolution_rate = 0
            grade = "N/A"
        
        return {
            "zone_id": zone_id,
            "total_reports": len(reports),
            "resolved_reports": len(resolved),
            "resolution_rate_percent": round(resolution_rate, 1),
            "avg_resolution_time_hours": avg_resolution_time,
            "total_water_saved_liters": self.stats["total_water_saved_liters"],
            "active_reporters": len([u for u in self.users.values() if u.reports_submitted > 0]),
            "utility_grade": grade,
            "reports_by_type": self._count_by_type(reports),
            "this_month": {
                "reports": len([r for r in reports if r.submitted_at.month == datetime.now().month]),
                "resolved": len([r for r in resolved if r.resolved_at and r.resolved_at.month == datetime.now().month])
            }
        }
    
    def _count_by_type(self, reports: List[CommunityReport]) -> Dict:
        counts = {}
        for r in reports:
            t = r.report_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    # =========================================================================
    # WATER CONSERVATION TIPS
    # =========================================================================
    
    def get_conservation_tips(self, language: str = "en") -> List[Dict]:
        """Get water conservation tips."""
        tips = {
            "en": [
                {"tip": "Fix leaky taps - a dripping tap wastes up to 15 liters per day!", "icon": "🚰"},
                {"tip": "Take shorter showers - 5 minutes is enough!", "icon": "🚿"},
                {"tip": "Turn off the tap while brushing teeth", "icon": "🦷"},
                {"tip": "Use a bucket instead of a hose to wash cars", "icon": "🚗"},
                {"tip": "Water gardens in early morning or evening to reduce evaporation", "icon": "🌱"},
                {"tip": "Report leaks immediately - even small leaks waste thousands of liters", "icon": "💧"},
                {"tip": "Collect rainwater for gardening", "icon": "🌧️"},
                {"tip": "Use water-efficient appliances", "icon": "🔧"}
            ],
            "ny": [
                {"tip": "Konzani tapulo zotayikira - tapulo lotayikira limatayitsa malit. 15 patsiku!", "icon": "🚰"},
                {"tip": "Sambilani mwachangu - mphindi 5 zokwanira!", "icon": "🚿"},
                {"tip": "Tsekani tapulo mukasula mano", "icon": "🦷"},
                {"tip": "Gwiritsani ntchito baketi osati hoze kusamba galimoto", "icon": "🚗"}
            ]
        }
        
        return tips.get(language, tips["en"])


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    service = CommunityPortalService()
    
    # Register user
    user = service.register_user(
        phone="+260971234567",
        name="Mwamba Banda",
        language="en",
        area="Kabulonga",
        account_number="ACC123456"
    )
    print(f"Registered: {user.user_id}, Level: {user.level_title}")
    
    # Submit report
    report = service.submit_report(
        user_id=user.user_id,
        report_type=ReportType.LEAK,
        latitude=-15.4033,
        longitude=28.3228,
        description="Water leaking from underground pipe near the main road junction. Been leaking for 2 days.",
        address="Plot 123, Kabulonga Road",
        landmark="Near Total Filling Station",
        urgency="high",
        photos=[Photo(
            photo_id="P001",
            url="https://storage.aquawatch.zm/photos/leak001.jpg",
            caption="Water pooling on road"
        )]
    )
    print(f"\nReport submitted: {report.report_id}")
    print(f"Points earned: {report.points_awarded}")
    print(f"User total points: {user.points}")
    
    # Acknowledge and verify
    service.acknowledge_report(report.report_id)
    service.verify_report(report.report_id, verified=True, notes="Confirmed via satellite imagery")
    
    print(f"\nAfter verification:")
    print(f"User verified reports: {user.reports_verified}")
    print(f"User badges: {user.badges}")
    
    # Resolve
    service.resolve_report(
        report.report_id,
        resolution_notes="Pipe joint repaired. Estimated 500L/hr water saved.",
        water_saved_liters=500 * 24  # Daily savings
    )
    
    print(f"\nAfter resolution:")
    print(f"User total points: {user.points}")
    print(f"User level: {user.level} ({user.level_title})")
    
    # Get leaderboard
    print("\nLeaderboard:")
    for entry in service.get_leaderboard(limit=5):
        print(f"  {entry['rank']}. {entry['name']} - {entry['points']} pts ({entry['level_title']})")
    
    # Get public stats
    print("\nPublic Statistics:")
    stats = service.get_public_stats()
    print(json.dumps(stats, indent=2))
    
    # Get user profile
    print("\nUser Profile:")
    profile = service.get_user_profile(user.user_id)
    print(json.dumps(profile, indent=2, default=str))
    
    # Get tips
    print("\nWater Conservation Tips:")
    for tip in service.get_conservation_tips("en")[:3]:
        print(f"  {tip['icon']} {tip['tip']}")
