"""
AquaWatch NRW v3.0 - Notification API Routes
============================================

FastAPI routes for notification management:
- GET /tenants/{tenant_id}/notifications - List notifications
- GET /tenants/{tenant_id}/notifications/unread-count - Get unread count
- PATCH /tenants/{tenant_id}/notifications/{id}/read - Mark as read
- POST /tenants/{tenant_id}/notifications/mark-all-read - Mark all as read
- GET /tenants/{tenant_id}/notification-rules - List notification rules
- POST /tenants/{tenant_id}/notification-rules - Create rule
- GET /tenants/{tenant_id}/escalations - Get escalation status
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..security.multi_tenant_auth import (
    TenantGuard,
    RequireRole,
    TenantRole,
    CurrentUser,
)
from .notification_service import (
    notification_service,
    NotificationSeverity,
    NotificationChannel,
)
from .escalation_engine import escalation_engine

logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class NotificationResponse(BaseModel):
    """Notification data for API response."""
    id: str
    title: str
    message: str
    severity: str
    category: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    read: bool
    read_at: Optional[str] = None
    created_at: str
    metadata: Dict = {}


class NotificationListResponse(BaseModel):
    """Response for notification list."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Response for unread count."""
    unread_count: int
    tenant_id: str
    user_id: str


class MarkReadResponse(BaseModel):
    """Response for mark read operations."""
    success: bool
    notification_id: Optional[str] = None
    count: Optional[int] = None


class NotificationRuleCreate(BaseModel):
    """Request to create a notification rule."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: str = Field(...)
    severity: str = Field(...)
    target_roles: List[str] = Field(default=["operator"])
    channels: Dict = Field(
        default={"in_app": {"enabled": True}}
    )
    escalation: List[Dict] = Field(
        default=[]
    )
    conditions: Dict = Field(default={})
    cooldown_minutes: int = Field(default=15, ge=0)
    is_active: bool = True
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Critical Leak Alert",
                    "event_type": "leak.detected",
                    "severity": "critical",
                    "target_roles": ["operator", "engineer"],
                    "channels": {"in_app": {"enabled": True}, "email": {"enabled": True}},
                    "escalation": [{"delay_minutes": 5, "roles": ["engineer"], "channels": ["sms"]}]
                }
            ]
        }
    }


class NotificationRuleResponse(BaseModel):
    """Response for notification rule."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    event_type: str
    severity: str
    target_roles: List[str]
    channels: Dict
    escalation: List[Dict]
    conditions: Dict
    cooldown_minutes: int
    is_active: bool
    created_at: str
    updated_at: str


class EscalationTrackerResponse(BaseModel):
    """Response for escalation tracker."""
    id: str
    tenant_id: str
    alert_id: str
    severity: str
    current_level: int
    max_level: int
    is_resolved: bool
    created_at: str
    last_escalated_at: Optional[str] = None
    next_escalation_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_type: Optional[str] = None
    notifications_sent: List[str]


class EscalationStatsResponse(BaseModel):
    """Response for escalation statistics."""
    total_trackers: int
    active_trackers: int
    resolved_trackers: int
    by_severity: Dict[str, int]
    by_level: Dict[int, int]
    is_running: bool


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    user_id: str
    title: str
    message: str
    severity: str = "info"
    channels: List[str] = ["in_app"]
    category: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    metadata: Dict = {}
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user-123",
                    "title": "New Alert",
                    "message": "A new leak has been detected",
                    "severity": "warning",
                    "channels": ["in_app", "email"]
                }
            ]
        }
    }


class SendNotificationResponse(BaseModel):
    """Response for send notification."""
    success: bool
    channels_sent: List[str]
    channels_failed: List[str]
    errors: List[str]


# =============================================================================
# API ROUTER
# =============================================================================

notification_router = APIRouter(
    prefix="/tenants/{tenant_id}/notifications",
    tags=["Notifications"]
)

rules_router = APIRouter(
    prefix="/tenants/{tenant_id}/notification-rules",
    tags=["Notification Rules"]
)

escalation_router = APIRouter(
    prefix="/tenants/{tenant_id}/escalations",
    tags=["Escalations"]
)


# =============================================================================
# NOTIFICATION ENDPOINTS
# =============================================================================

@notification_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    tenant_id: str,
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    user: CurrentUser = Depends(TenantGuard()),
):
    """
    List notifications for the current user.
    
    Returns notifications sorted by creation time (newest first).
    """
    notifications = notification_service.get_notifications(
        tenant_id=tenant_id,
        user_id=user.user_id,
        unread_only=unread_only,
        limit=limit,
    )
    
    unread_count = notification_service.get_unread_count(
        tenant_id=tenant_id,
        user_id=user.user_id,
    )
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n["id"],
                title=n["title"],
                message=n["message"],
                severity=n.get("severity", "info"),
                category=n.get("category"),
                source_type=n.get("source_type"),
                source_id=n.get("source_id"),
                action_url=n.get("action_url"),
                read=n.get("read", False),
                read_at=n.get("read_at"),
                created_at=n.get("created_at", ""),
                metadata=n.get("metadata", {}),
            )
            for n in notifications
        ],
        total=len(notifications),
        unread_count=unread_count,
    )


@notification_router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Get the unread notification count for the current user."""
    count = notification_service.get_unread_count(
        tenant_id=tenant_id,
        user_id=user.user_id,
    )
    
    return UnreadCountResponse(
        unread_count=count,
        tenant_id=tenant_id,
        user_id=user.user_id,
    )


@notification_router.patch("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_read(
    tenant_id: str,
    notification_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Mark a specific notification as read."""
    success = notification_service.mark_read(
        tenant_id=tenant_id,
        user_id=user.user_id,
        notification_id=notification_id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return MarkReadResponse(
        success=True,
        notification_id=notification_id,
    )


@notification_router.post("/mark-all-read", response_model=MarkReadResponse)
async def mark_all_notifications_read(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Mark all notifications as read for the current user."""
    count = notification_service.mark_all_read(
        tenant_id=tenant_id,
        user_id=user.user_id,
    )
    
    return MarkReadResponse(
        success=True,
        count=count,
    )


@notification_router.post("/send", response_model=SendNotificationResponse)
async def send_notification(
    tenant_id: str,
    request: SendNotificationRequest,
    user: CurrentUser = Depends(RequireRole([TenantRole.TENANT_ADMIN, TenantRole.OPERATOR])),
):
    """
    Send a notification to a user.
    
    Requires TENANT_ADMIN or OPERATOR role.
    """
    # Convert channel strings to enums
    channels = []
    for ch in request.channels:
        try:
            channels.append(NotificationChannel(ch))
        except ValueError:
            pass
    
    if not channels:
        channels = [NotificationChannel.IN_APP]
    
    # Convert severity
    try:
        severity = NotificationSeverity(request.severity)
    except ValueError:
        severity = NotificationSeverity.INFO
    
    results = await notification_service.send(
        tenant_id=tenant_id,
        user_id=request.user_id,
        title=request.title,
        message=request.message,
        severity=severity,
        channels=channels,
        category=request.category,
        source_type=request.source_type,
        source_id=request.source_id,
        action_url=request.action_url,
        metadata=request.metadata,
    )
    
    channels_sent = [r.channel.value for r in results if r.success]
    channels_failed = [r.channel.value for r in results if not r.success]
    errors = [r.error for r in results if r.error]
    
    return SendNotificationResponse(
        success=len(channels_sent) > 0,
        channels_sent=channels_sent,
        channels_failed=channels_failed,
        errors=errors,
    )


# =============================================================================
# NOTIFICATION RULES ENDPOINTS
# =============================================================================

# In-memory rules storage for demo (would use database in production)
_notification_rules: Dict[str, List[Dict]] = {}


@rules_router.get("", response_model=List[NotificationRuleResponse])
async def list_notification_rules(
    tenant_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user: CurrentUser = Depends(TenantGuard()),
):
    """List notification rules for the tenant."""
    rules = _notification_rules.get(tenant_id, [])
    
    if event_type:
        rules = [r for r in rules if r["event_type"] == event_type]
    
    if is_active is not None:
        rules = [r for r in rules if r["is_active"] == is_active]
    
    return [
        NotificationRuleResponse(**r)
        for r in rules
    ]


@rules_router.post("", response_model=NotificationRuleResponse, status_code=201)
async def create_notification_rule(
    tenant_id: str,
    request: NotificationRuleCreate,
    user: CurrentUser = Depends(RequireRole([TenantRole.TENANT_ADMIN])),
):
    """
    Create a new notification rule.
    
    Requires TENANT_ADMIN role.
    """
    import uuid
    
    now = datetime.utcnow().isoformat()
    
    rule = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": request.name,
        "description": request.description,
        "event_type": request.event_type,
        "severity": request.severity,
        "target_roles": request.target_roles,
        "channels": request.channels,
        "escalation": request.escalation,
        "conditions": request.conditions,
        "cooldown_minutes": request.cooldown_minutes,
        "is_active": request.is_active,
        "created_at": now,
        "updated_at": now,
    }
    
    if tenant_id not in _notification_rules:
        _notification_rules[tenant_id] = []
    
    _notification_rules[tenant_id].append(rule)
    
    return NotificationRuleResponse(**rule)


@rules_router.get("/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    tenant_id: str,
    rule_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Get a specific notification rule."""
    rules = _notification_rules.get(tenant_id, [])
    
    for rule in rules:
        if rule["id"] == rule_id:
            return NotificationRuleResponse(**rule)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification rule not found"
    )


@rules_router.delete("/{rule_id}", status_code=204)
async def delete_notification_rule(
    tenant_id: str,
    rule_id: str,
    user: CurrentUser = Depends(RequireRole([TenantRole.TENANT_ADMIN])),
):
    """
    Delete a notification rule.
    
    Requires TENANT_ADMIN role.
    """
    rules = _notification_rules.get(tenant_id, [])
    
    for i, rule in enumerate(rules):
        if rule["id"] == rule_id:
            del rules[i]
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification rule not found"
    )


# =============================================================================
# ESCALATION ENDPOINTS
# =============================================================================

@escalation_router.get("", response_model=List[EscalationTrackerResponse])
async def list_escalations(
    tenant_id: str,
    active_only: bool = Query(True, description="Only return active escalations"),
    user: CurrentUser = Depends(TenantGuard()),
):
    """List escalation trackers for the tenant."""
    if active_only:
        trackers = escalation_engine.get_active_trackers(tenant_id)
    else:
        trackers = [
            t for t in escalation_engine._trackers.values()
            if t.tenant_id == tenant_id
        ]
    
    return [
        EscalationTrackerResponse(**t.to_dict())
        for t in trackers
    ]


@escalation_router.get("/stats", response_model=EscalationStatsResponse)
async def get_escalation_stats(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Get escalation statistics for the tenant."""
    stats = escalation_engine.get_stats(tenant_id)
    return EscalationStatsResponse(**stats)


@escalation_router.get("/{alert_id}", response_model=EscalationTrackerResponse)
async def get_escalation_tracker(
    tenant_id: str,
    alert_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Get escalation tracker for a specific alert."""
    tracker = escalation_engine.get_tracker(tenant_id, alert_id)
    
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation tracker not found"
        )
    
    return EscalationTrackerResponse(**tracker.to_dict())


@escalation_router.post("/{alert_id}/acknowledge")
async def acknowledge_escalation(
    tenant_id: str,
    alert_id: str,
    user: CurrentUser = Depends(TenantGuard()),
):
    """Acknowledge an alert to affect escalation timing."""
    success = await escalation_engine.acknowledge_alert(tenant_id, alert_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation tracker not found"
        )
    
    return {"success": True, "alert_id": alert_id, "action": "acknowledged"}


@escalation_router.post("/{alert_id}/resolve")
async def resolve_escalation(
    tenant_id: str,
    alert_id: str,
    resolution_type: str = Query("resolved", description="Resolution type"),
    user: CurrentUser = Depends(TenantGuard()),
):
    """Resolve an alert to stop escalation."""
    success = await escalation_engine.resolve_alert(
        tenant_id, alert_id, resolution_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation tracker not found"
        )
    
    return {"success": True, "alert_id": alert_id, "action": "resolved"}
