"""
AquaWatch NRW v3.0 - Escalation Engine
======================================

Background job for automatic alert escalation based on rules:

1. CRITICAL leak not acknowledged within 5 minutes -> Notify ENGINEER
2. Unresolved alert within 2 hours -> Notify EXECUTIVE

Runs as a background asyncio task that periodically checks:
- Unacknowledged critical alerts
- Stale escalation trackers

Usage:
    from src.notifications.escalation_engine import escalation_engine
    
    # Start the engine
    await escalation_engine.start()
    
    # Stop the engine
    await escalation_engine.stop()
    
    # Process a new alert (creates escalation tracker)
    await escalation_engine.track_alert(
        tenant_id="lwsc-zambia",
        alert_id="alert-123",
        severity="critical"
    )
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .notification_service import (
    notification_service,
    NotificationSeverity,
    NotificationChannel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EscalationLevel:
    """Configuration for an escalation level."""
    level: int
    delay_minutes: int
    target_roles: List[str]
    channels: List[NotificationChannel]
    message_template: str


# Default escalation rules
DEFAULT_ESCALATION_RULES = {
    "critical": [
        EscalationLevel(
            level=1,
            delay_minutes=5,
            target_roles=["engineer"],
            channels=[NotificationChannel.IN_APP, NotificationChannel.SMS],
            message_template="ESCALATION: Critical alert {alert_id} not acknowledged after 5 minutes."
        ),
        EscalationLevel(
            level=2,
            delay_minutes=120,  # 2 hours
            target_roles=["executive"],
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            message_template="URGENT ESCALATION: Critical alert {alert_id} unresolved for 2 hours. Executive attention required."
        ),
    ],
    "warning": [
        EscalationLevel(
            level=1,
            delay_minutes=30,
            target_roles=["engineer"],
            channels=[NotificationChannel.IN_APP],
            message_template="Alert {alert_id} requires attention - not acknowledged after 30 minutes."
        ),
        EscalationLevel(
            level=2,
            delay_minutes=240,  # 4 hours
            target_roles=["executive"],
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            message_template="Alert {alert_id} unresolved for 4 hours. Review required."
        ),
    ],
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EscalationTracker:
    """
    Tracks escalation state for an alert.
    """
    id: str
    tenant_id: str
    alert_id: str
    severity: str
    
    # State
    current_level: int = 0
    max_level: int = 2
    is_resolved: bool = False
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_escalated_at: Optional[datetime] = None
    next_escalation_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None  # acknowledged, resolved, timeout
    
    # History
    notifications_sent: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "alert_id": self.alert_id,
            "severity": self.severity,
            "current_level": self.current_level,
            "max_level": self.max_level,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat(),
            "last_escalated_at": self.last_escalated_at.isoformat() if self.last_escalated_at else None,
            "next_escalation_at": self.next_escalation_at.isoformat() if self.next_escalation_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_type": self.resolution_type,
            "notifications_sent": self.notifications_sent,
        }


# =============================================================================
# ESCALATION ENGINE
# =============================================================================

class EscalationEngine:
    """
    Background engine for automatic alert escalation.
    
    Features:
    - Periodic check for escalation triggers
    - Configurable escalation rules per severity
    - Multi-channel notifications at each level
    - Audit logging
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 30,
        escalation_rules: Optional[Dict[str, List[EscalationLevel]]] = None,
    ):
        self.check_interval = check_interval_seconds
        self.escalation_rules = escalation_rules or DEFAULT_ESCALATION_RULES
        
        # In-memory trackers (would use database in production)
        self._trackers: Dict[str, EscalationTracker] = {}
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        # Mock user database for role lookups
        self._mock_users: Dict[str, List[Dict]] = {}
    
    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    
    async def start(self):
        """Start the escalation engine background task."""
        if self._running:
            logger.warning("Escalation engine already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Escalation engine started (check interval: {self.check_interval}s)")
    
    async def stop(self):
        """Stop the escalation engine."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Escalation engine stopped")
    
    async def _run_loop(self):
        """Main escalation check loop."""
        while self._running:
            try:
                await self._check_escalations()
            except Exception as e:
                logger.error(f"Error in escalation check: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    # -------------------------------------------------------------------------
    # Alert Tracking
    # -------------------------------------------------------------------------
    
    async def track_alert(
        self,
        tenant_id: str,
        alert_id: str,
        severity: str,
        title: Optional[str] = None,
        dma_id: Optional[str] = None,
    ) -> EscalationTracker:
        """
        Start tracking an alert for escalation.
        
        Args:
            tenant_id: Tenant identifier
            alert_id: Alert ID to track
            severity: Alert severity (critical, warning, etc.)
            title: Alert title for notifications
            dma_id: DMA ID for context
        
        Returns:
            EscalationTracker instance
        """
        # Check if already tracking
        tracker_key = f"{tenant_id}:{alert_id}"
        if tracker_key in self._trackers:
            logger.debug(f"Already tracking alert {alert_id}")
            return self._trackers[tracker_key]
        
        # Get escalation rules for this severity
        rules = self.escalation_rules.get(severity.lower(), [])
        
        # Calculate first escalation time
        first_escalation = None
        if rules:
            first_escalation = datetime.utcnow() + timedelta(minutes=rules[0].delay_minutes)
        
        # Create tracker
        tracker = EscalationTracker(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            alert_id=alert_id,
            severity=severity.lower(),
            max_level=len(rules),
            next_escalation_at=first_escalation,
        )
        
        self._trackers[tracker_key] = tracker
        
        logger.info(
            f"Started tracking alert {alert_id} for escalation: "
            f"severity={severity}, first_escalation={first_escalation}"
        )
        
        return tracker
    
    async def resolve_alert(
        self,
        tenant_id: str,
        alert_id: str,
        resolution_type: str = "resolved",
    ) -> bool:
        """
        Mark an alert as resolved, stopping escalation.
        
        Args:
            tenant_id: Tenant identifier
            alert_id: Alert ID
            resolution_type: How it was resolved (acknowledged, resolved, etc.)
        
        Returns:
            True if tracker was found and updated
        """
        tracker_key = f"{tenant_id}:{alert_id}"
        tracker = self._trackers.get(tracker_key)
        
        if not tracker:
            return False
        
        tracker.is_resolved = True
        tracker.resolved_at = datetime.utcnow()
        tracker.resolution_type = resolution_type
        tracker.next_escalation_at = None
        
        logger.info(f"Alert {alert_id} resolved: {resolution_type}")
        
        return True
    
    async def acknowledge_alert(
        self,
        tenant_id: str,
        alert_id: str,
    ) -> bool:
        """
        Acknowledge an alert (stops first-level escalation but continues tracking).
        
        Args:
            tenant_id: Tenant identifier
            alert_id: Alert ID
        
        Returns:
            True if tracker was found and updated
        """
        tracker_key = f"{tenant_id}:{alert_id}"
        tracker = self._trackers.get(tracker_key)
        
        if not tracker:
            return False
        
        # If at level 0, this acknowledgment stops the first escalation
        # but we continue tracking for resolution escalation
        if tracker.current_level == 0:
            rules = self.escalation_rules.get(tracker.severity, [])
            if len(rules) > 1:
                # Skip to resolution escalation (level 2)
                tracker.current_level = 1
                next_rule = rules[1]
                tracker.next_escalation_at = datetime.utcnow() + timedelta(minutes=next_rule.delay_minutes)
                logger.info(
                    f"Alert {alert_id} acknowledged, next escalation at {tracker.next_escalation_at}"
                )
            else:
                # No further escalation levels
                tracker.is_resolved = True
                tracker.resolved_at = datetime.utcnow()
                tracker.resolution_type = "acknowledged"
                tracker.next_escalation_at = None
        
        return True
    
    # -------------------------------------------------------------------------
    # Escalation Processing
    # -------------------------------------------------------------------------
    
    async def _check_escalations(self):
        """Check all trackers for escalation triggers."""
        now = datetime.utcnow()
        
        for tracker_key, tracker in list(self._trackers.items()):
            if tracker.is_resolved:
                continue
            
            if tracker.next_escalation_at and now >= tracker.next_escalation_at:
                await self._escalate(tracker)
    
    async def _escalate(self, tracker: EscalationTracker):
        """Process escalation for a tracker."""
        rules = self.escalation_rules.get(tracker.severity, [])
        
        if tracker.current_level >= len(rules):
            # Max escalation reached
            tracker.is_resolved = True
            tracker.resolved_at = datetime.utcnow()
            tracker.resolution_type = "max_escalation_reached"
            logger.warning(f"Alert {tracker.alert_id} reached max escalation level")
            return
        
        rule = rules[tracker.current_level]
        
        # Send escalation notifications
        await self._send_escalation_notifications(tracker, rule)
        
        # Update tracker
        tracker.current_level += 1
        tracker.last_escalated_at = datetime.utcnow()
        
        # Set next escalation time
        if tracker.current_level < len(rules):
            next_rule = rules[tracker.current_level]
            tracker.next_escalation_at = datetime.utcnow() + timedelta(minutes=next_rule.delay_minutes)
        else:
            tracker.next_escalation_at = None
        
        logger.info(
            f"Escalated alert {tracker.alert_id} to level {tracker.current_level}: "
            f"roles={rule.target_roles}, channels={[c.value for c in rule.channels]}"
        )
    
    async def _send_escalation_notifications(
        self,
        tracker: EscalationTracker,
        rule: EscalationLevel,
    ):
        """Send notifications for an escalation level."""
        # Get users with target roles
        users = await self._get_users_by_roles(tracker.tenant_id, rule.target_roles)
        
        if not users:
            logger.warning(
                f"No users found with roles {rule.target_roles} in tenant {tracker.tenant_id}"
            )
            return
        
        # Format message
        message = rule.message_template.format(
            alert_id=tracker.alert_id,
            tenant_id=tracker.tenant_id,
        )
        
        # Determine severity for notification
        notification_severity = NotificationSeverity.CRITICAL if tracker.severity == "critical" else NotificationSeverity.WARNING
        
        # Send to each user
        for user in users:
            results = await notification_service.send(
                tenant_id=tracker.tenant_id,
                user_id=user["id"],
                title=f"⚠️ Alert Escalation (Level {rule.level})",
                message=message,
                severity=notification_severity,
                channels=rule.channels,
                category="escalation",
                source_type="alert",
                source_id=tracker.alert_id,
                action_url=f"/alerts/{tracker.alert_id}",
                recipient_email=user.get("email"),
                recipient_phone=user.get("phone"),
                recipient_name=user.get("name"),
            )
            
            # Track sent notifications
            for result in results:
                if result.notification_id:
                    tracker.notifications_sent.append(result.notification_id)
    
    async def _get_users_by_roles(
        self,
        tenant_id: str,
        roles: List[str],
    ) -> List[Dict]:
        """
        Get users with specified roles in a tenant.
        
        In production, this would query the database.
        For now, returns mock users.
        """
        # Mock implementation - returns test users
        mock_users = {
            "engineer": [
                {
                    "id": "engineer-001",
                    "name": "John Engineer",
                    "email": "engineer@lwsc.co.zm",
                    "phone": "+260971234567",
                    "role": "engineer",
                }
            ],
            "executive": [
                {
                    "id": "exec-001",
                    "name": "Sarah Executive",
                    "email": "executive@lwsc.co.zm",
                    "phone": "+260972345678",
                    "role": "executive",
                }
            ],
            "operator": [
                {
                    "id": "operator-001",
                    "name": "Mike Operator",
                    "email": "operator@lwsc.co.zm",
                    "phone": "+260973456789",
                    "role": "operator",
                }
            ],
        }
        
        users = []
        for role in roles:
            users.extend(mock_users.get(role, []))
        
        return users
    
    # -------------------------------------------------------------------------
    # Status & Metrics
    # -------------------------------------------------------------------------
    
    def get_tracker(self, tenant_id: str, alert_id: str) -> Optional[EscalationTracker]:
        """Get escalation tracker for an alert."""
        tracker_key = f"{tenant_id}:{alert_id}"
        return self._trackers.get(tracker_key)
    
    def get_active_trackers(self, tenant_id: Optional[str] = None) -> List[EscalationTracker]:
        """Get all active (unresolved) trackers."""
        trackers = [t for t in self._trackers.values() if not t.is_resolved]
        
        if tenant_id:
            trackers = [t for t in trackers if t.tenant_id == tenant_id]
        
        return trackers
    
    def get_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get escalation engine statistics."""
        trackers = list(self._trackers.values())
        
        if tenant_id:
            trackers = [t for t in trackers if t.tenant_id == tenant_id]
        
        active = [t for t in trackers if not t.is_resolved]
        resolved = [t for t in trackers if t.is_resolved]
        
        # Count by severity
        by_severity = {}
        for t in active:
            by_severity[t.severity] = by_severity.get(t.severity, 0) + 1
        
        # Count by escalation level
        by_level = {}
        for t in active:
            by_level[t.current_level] = by_level.get(t.current_level, 0) + 1
        
        return {
            "total_trackers": len(trackers),
            "active_trackers": len(active),
            "resolved_trackers": len(resolved),
            "by_severity": by_severity,
            "by_level": by_level,
            "check_interval_seconds": self.check_interval,
            "is_running": self._running,
        }
    
    def clear_resolved(self, older_than_hours: int = 24) -> int:
        """Clear resolved trackers older than specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        to_remove = [
            key for key, tracker in self._trackers.items()
            if tracker.is_resolved and tracker.resolved_at and tracker.resolved_at < cutoff
        ]
        
        for key in to_remove:
            del self._trackers[key]
        
        return len(to_remove)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

escalation_engine = EscalationEngine()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def start_escalation_tracking(
    tenant_id: str,
    alert_id: str,
    severity: str,
    **kwargs
) -> EscalationTracker:
    """Start tracking an alert for escalation."""
    return await escalation_engine.track_alert(
        tenant_id=tenant_id,
        alert_id=alert_id,
        severity=severity,
        **kwargs
    )


async def stop_escalation_tracking(
    tenant_id: str,
    alert_id: str,
    resolution_type: str = "resolved",
) -> bool:
    """Stop tracking an alert (mark as resolved)."""
    return await escalation_engine.resolve_alert(
        tenant_id=tenant_id,
        alert_id=alert_id,
        resolution_type=resolution_type,
    )


async def acknowledge_alert_escalation(
    tenant_id: str,
    alert_id: str,
) -> bool:
    """Acknowledge an alert (affects escalation timing)."""
    return await escalation_engine.acknowledge_alert(
        tenant_id=tenant_id,
        alert_id=alert_id,
    )
