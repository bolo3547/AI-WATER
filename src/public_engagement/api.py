"""
AquaWatch NRW - Public Engagement FastAPI Routes
================================================

REST API endpoints for public engagement module.

Public Endpoints (no auth required):
- POST /public/{tenant_id}/report - Create a new report
- GET /public/{tenant_id}/track/{ticket} - Track a report
- POST /public/{tenant_id}/report/{ticket}/media - Upload media

Admin Endpoints (require auth):
- GET /admin/{tenant_id}/reports - List reports with filters
- PATCH /admin/{tenant_id}/reports/{id}/status - Update status
- POST /admin/{tenant_id}/reports/{id}/assign - Assign to team
- POST /admin/{tenant_id}/reports/{id}/work-order - Create work order
- POST /admin/{tenant_id}/reports/merge - Merge duplicates
- GET /admin/{tenant_id}/analytics - Get analytics metrics

WhatsApp/USSD Endpoints:
- POST /whatsapp/{tenant_id}/webhook - WhatsApp bot webhook
- POST /ussd/{tenant_id}/start - USSD session start
- POST /ussd/{tenant_id}/continue - USSD session continue
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from functools import wraps

from fastapi import FastAPI, APIRouter, HTTPException, Query, Path, Body, UploadFile, File, Request, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator, EmailStr

from .models import ReportCategory, ReportStatus, ReportSource, ReportVerification
from .services import (
    PublicReportService,
    DuplicateDetectionService,
    SpamDetectionService,
    AnalyticsService,
    ReportCreateRequest,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ReportCreateSchema(BaseModel):
    """Schema for creating a new public report."""
    category: str = Field(..., description="Report category: leak, burst, no_water, low_pressure, illegal_connection, overflow, contamination, other")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description of the issue")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    area_text: Optional[str] = Field(None, max_length=500, description="Text description of location (fallback for no GPS)")
    reporter_name: Optional[str] = Field(None, max_length=200, description="Reporter's name (optional)")
    reporter_phone: Optional[str] = Field(None, max_length=50, description="Reporter's phone number (optional)")
    reporter_email: Optional[EmailStr] = Field(None, description="Reporter's email (optional)")
    reporter_consent: bool = Field(False, description="Consent to be contacted")
    
    @validator('category')
    def validate_category(cls, v):
        valid = [c.value for c in ReportCategory]
        if v not in valid:
            raise ValueError(f"Invalid category. Must be one of: {valid}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "category": "leak",
                "description": "Water leaking from pipe near the road",
                "latitude": -15.4167,
                "longitude": 28.2833,
                "area_text": "Great East Road, near Arcades Shopping Mall",
                "reporter_name": "John Mwansa",
                "reporter_phone": "+260971234567",
                "reporter_consent": True
            }
        }


class ReportCreatedResponse(BaseModel):
    """Response after creating a report."""
    success: bool
    ticket: Optional[str] = None
    message: str
    tracking_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticket": "TKT-A3B7C9",
                "message": "Your report has been submitted successfully.",
                "tracking_url": "/track/TKT-A3B7C9"
            }
        }


class TimelineEntry(BaseModel):
    """A single timeline entry."""
    status: str
    message: str
    timestamp: str


class TrackingResponse(BaseModel):
    """Response for tracking a report."""
    ticket: str
    status: str
    status_label: str
    category: str
    area: Optional[str] = None
    timeline: List[TimelineEntry]
    created_at: str
    last_updated: str
    resolved_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticket": "TKT-A3B7C9",
                "status": "technician_assigned",
                "status_label": "Team Assigned",
                "category": "leak",
                "area": "Central Business District",
                "timeline": [
                    {"status": "received", "message": "Your report has been received.", "timestamp": "2026-01-22T08:00:00Z"},
                    {"status": "under_review", "message": "Your report is being reviewed.", "timestamp": "2026-01-22T08:30:00Z"},
                    {"status": "technician_assigned", "message": "A team has been assigned.", "timestamp": "2026-01-22T09:00:00Z"}
                ],
                "created_at": "2026-01-22T08:00:00Z",
                "last_updated": "2026-01-22T09:00:00Z"
            }
        }


class AdminReportSchema(BaseModel):
    """Full report schema for admin view."""
    id: str
    ticket: str
    tenant_id: str
    category: str
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    area_text: Optional[str]
    source: str
    reporter_name: Optional[str]
    reporter_phone: Optional[str]
    reporter_email: Optional[str]
    reporter_consent: bool
    status: str
    verification: str
    trust_score_delta: int
    spam_flag: bool
    quarantine: bool
    master_report_id: Optional[str]
    is_master: bool
    duplicate_count: int
    linked_leak_id: Optional[str]
    linked_work_order_id: Optional[str]
    admin_notes: Optional[str]
    assigned_to_user_id: Optional[str]
    assigned_team: Optional[str]
    assigned_at: Optional[str]
    resolved_at: Optional[str]
    created_at: str
    updated_at: str
    media_count: int = 0


class StatusUpdateSchema(BaseModel):
    """Schema for updating report status."""
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(None, max_length=2000, description="Optional notes")
    
    @validator('status')
    def validate_status(cls, v):
        valid = [s.value for s in ReportStatus]
        if v not in valid:
            raise ValueError(f"Invalid status. Must be one of: {valid}")
        return v


class VerificationUpdateSchema(BaseModel):
    """Schema for updating report verification."""
    verification: str = Field(..., description="Verification status")
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('verification')
    def validate_verification(cls, v):
        valid = [r.value for r in ReportVerification]
        if v not in valid:
            raise ValueError(f"Invalid verification. Must be one of: {valid}")
        return v


class AssignmentSchema(BaseModel):
    """Schema for assigning a report."""
    user_id: str = Field(..., description="User ID to assign to")
    team: Optional[str] = Field(None, max_length=100, description="Team name")


class MergeReportsSchema(BaseModel):
    """Schema for merging duplicate reports."""
    master_report_id: str = Field(..., description="ID of the master report")
    duplicate_report_ids: List[str] = Field(..., description="IDs of reports to merge as duplicates")
    reason: str = Field(default="manual", description="Reason for merging")


class CreateWorkOrderSchema(BaseModel):
    """Schema for creating work order from report."""
    priority: int = Field(3, ge=1, le=5, description="Priority level (1=highest)")
    notes: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field("investigation", description="Task type: investigation, repair, inspection")


class AnalyticsResponse(BaseModel):
    """Analytics metrics response."""
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
    conversion_rate: float


class ReportListResponse(BaseModel):
    """Paginated list of reports."""
    items: List[AdminReportSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# WHATSAPP BOT SCHEMAS
# =============================================================================

class WhatsAppIncomingMessage(BaseModel):
    """Incoming WhatsApp message."""
    from_number: str = Field(..., alias="from")
    message_id: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: str

    class Config:
        populate_by_name = True


class WhatsAppResponse(BaseModel):
    """Response to send back to WhatsApp."""
    to: str
    messages: List[Dict[str, Any]]
    session_data: Optional[Dict[str, Any]] = None


# =============================================================================
# USSD SCHEMAS
# =============================================================================

class USSDStartRequest(BaseModel):
    """USSD session start request."""
    session_id: str
    phone_number: str
    service_code: str


class USSDContinueRequest(BaseModel):
    """USSD session continue request."""
    session_id: str
    phone_number: str
    text: str  # User input


class USSDResponse(BaseModel):
    """USSD response."""
    session_id: str
    response_type: str = "CON"  # CON = continue, END = end session
    message: str


# =============================================================================
# RATE LIMITING
# =============================================================================

from collections import defaultdict
import time

# Simple in-memory rate limiter (use Redis in production)
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)

def check_rate_limit(
    key: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Check if rate limit is exceeded.
    
    Returns True if request is allowed, False if blocked.
    """
    now = time.time()
    window_start = now - window_seconds
    
    # Clean old entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]
    
    # Check limit
    if len(_rate_limit_store[key]) >= max_requests:
        return False
    
    # Record this request
    _rate_limit_store[key].append(now)
    return True


def rate_limit_dependency(request: Request, tenant_id: str):
    """FastAPI dependency for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"{tenant_id}:{client_ip}"
    
    if not check_rate_limit(key, max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


# =============================================================================
# API ROUTER
# =============================================================================

def create_public_engagement_api() -> APIRouter:
    """Create and configure the public engagement API router."""
    
    router = APIRouter(tags=["Public Engagement"])
    
    # Initialize services
    report_service = PublicReportService()
    duplicate_service = DuplicateDetectionService()
    spam_service = SpamDetectionService()
    analytics_service = AnalyticsService()
    
    # =========================================================================
    # PUBLIC ENDPOINTS
    # =========================================================================
    
    @router.post(
        "/public/{tenant_id}/report",
        response_model=ReportCreatedResponse,
        summary="Submit a public report",
        description="Submit a new report about water issues. No authentication required.",
    )
    async def create_report(
        tenant_id: str = Path(..., description="Tenant identifier"),
        body: ReportCreateSchema = Body(...),
        request: Request = None,
    ):
        """
        Create a new public report.
        
        This endpoint is public and does not require authentication.
        Rate limiting is applied to prevent abuse.
        """
        # Rate limiting
        client_ip = request.client.host if request and request.client else None
        if client_ip:
            key = f"report:{tenant_id}:{client_ip}"
            if not check_rate_limit(key, max_requests=5, window_seconds=3600):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="You have submitted too many reports. Please try again later."
                )
        
        # Create request object
        report_request = ReportCreateRequest(
            tenant_id=tenant_id,
            category=body.category,
            description=body.description,
            latitude=body.latitude,
            longitude=body.longitude,
            area_text=body.area_text,
            source="web",
            reporter_name=body.reporter_name,
            reporter_phone=body.reporter_phone,
            reporter_email=body.reporter_email,
            reporter_consent=body.reporter_consent,
            reporter_ip=client_ip,
        )
        
        # Create report
        result = report_service.create_report(report_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return ReportCreatedResponse(
            success=True,
            ticket=result.ticket,
            message=result.message,
            tracking_url=f"/track/{result.ticket}",
        )
    
    @router.get(
        "/public/{tenant_id}/track/{ticket}",
        response_model=TrackingResponse,
        summary="Track a report",
        description="Get the current status and timeline of a submitted report.",
    )
    async def track_report(
        tenant_id: str = Path(..., description="Tenant identifier"),
        ticket: str = Path(..., description="Ticket ID (e.g., TKT-A3B7C9)"),
    ):
        """
        Track a report by ticket ID.
        
        Returns public-safe information only (no technician names or internal notes).
        """
        result = report_service.get_tracking_info(tenant_id, ticket)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ticket {ticket} not found"
            )
        
        return TrackingResponse(
            ticket=result.ticket,
            status=result.status,
            status_label=result.status_label,
            category=result.category,
            area=result.area,
            timeline=[TimelineEntry(**t) for t in result.timeline],
            created_at=result.created_at,
            last_updated=result.last_updated,
            resolved_at=result.resolved_at,
        )
    
    @router.post(
        "/public/{tenant_id}/report/{ticket}/media",
        summary="Upload media to a report",
        description="Upload a photo or video attachment to an existing report.",
    )
    async def upload_media(
        tenant_id: str = Path(..., description="Tenant identifier"),
        ticket: str = Path(..., description="Ticket ID"),
        file: UploadFile = File(..., description="Photo or video file"),
        request: Request = None,
    ):
        """
        Upload media attachment to a report.
        
        Supported formats: JPEG, PNG, MP4, MOV
        Maximum file size: 10MB
        """
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "video/mp4", "video/quicktime"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {allowed_types}"
            )
        
        # Check file size (10MB limit)
        MAX_SIZE = 10 * 1024 * 1024
        contents = await file.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10MB."
            )
        
        # Generate storage path
        file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
        storage_filename = f"{uuid.uuid4().hex}.{file_ext}"
        storage_path = f"uploads/{tenant_id}/{ticket}/{storage_filename}"
        
        # Would save file to disk/S3 in real implementation
        logger.info(f"Media uploaded: {storage_path} ({len(contents)} bytes)")
        
        return {
            "success": True,
            "filename": storage_filename,
            "size_bytes": len(contents),
            "content_type": file.content_type,
        }
    
    # =========================================================================
    # ADMIN ENDPOINTS
    # =========================================================================
    
    @router.get(
        "/admin/{tenant_id}/reports",
        response_model=ReportListResponse,
        summary="List reports (admin)",
        description="Get paginated list of reports with filters.",
    )
    async def list_reports(
        tenant_id: str = Path(..., description="Tenant identifier"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        status: Optional[str] = Query(None, description="Filter by status"),
        category: Optional[str] = Query(None, description="Filter by category"),
        verification: Optional[str] = Query(None, description="Filter by verification"),
        spam_flag: Optional[bool] = Query(None, description="Filter spam flagged"),
        quarantine: Optional[bool] = Query(None, description="Filter quarantined"),
        dma_id: Optional[str] = Query(None, description="Filter by DMA"),
        source: Optional[str] = Query(None, description="Filter by source"),
        start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
        end_date: Optional[str] = Query(None, description="End date (ISO format)"),
        search: Optional[str] = Query(None, description="Search in description, area"),
    ):
        """
        List all reports with filtering and pagination.
        
        Requires admin authentication (enforced by middleware).
        """
        # Would query database with filters
        # For now, return mock data
        
        mock_report = AdminReportSchema(
            id="123e4567-e89b-12d3-a456-426614174000",
            ticket="TKT-A3B7C9",
            tenant_id=tenant_id,
            category="leak",
            description="Water leaking from pipe",
            latitude=-15.4167,
            longitude=28.2833,
            area_text="Central Business District",
            source="web",
            reporter_name="John Mwansa",
            reporter_phone="+260971234567",
            reporter_email=None,
            reporter_consent=True,
            status="under_review",
            verification="pending",
            trust_score_delta=0,
            spam_flag=False,
            quarantine=False,
            master_report_id=None,
            is_master=True,
            duplicate_count=2,
            linked_leak_id=None,
            linked_work_order_id=None,
            admin_notes=None,
            assigned_to_user_id=None,
            assigned_team=None,
            assigned_at=None,
            resolved_at=None,
            created_at="2026-01-22T08:00:00Z",
            updated_at="2026-01-22T09:00:00Z",
            media_count=2,
        )
        
        return ReportListResponse(
            items=[mock_report],
            total=1,
            page=page,
            page_size=page_size,
            total_pages=1,
        )
    
    @router.get(
        "/admin/{tenant_id}/reports/{report_id}",
        response_model=AdminReportSchema,
        summary="Get report details (admin)",
    )
    async def get_report(
        tenant_id: str = Path(...),
        report_id: str = Path(..., description="Report UUID"),
    ):
        """Get full report details for admin."""
        # Would fetch from database
        raise HTTPException(status_code=404, detail="Report not found")
    
    @router.patch(
        "/admin/{tenant_id}/reports/{report_id}/status",
        summary="Update report status",
    )
    async def update_status(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        body: StatusUpdateSchema = Body(...),
    ):
        """Update the status of a report."""
        success = report_service.update_status(
            tenant_id=tenant_id,
            report_id=report_id,
            new_status=body.status,
            notes=body.notes,
        )
        
        return {"success": success, "status": body.status}
    
    @router.patch(
        "/admin/{tenant_id}/reports/{report_id}/verification",
        summary="Update report verification",
    )
    async def update_verification(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        body: VerificationUpdateSchema = Body(...),
    ):
        """Update the verification status of a report."""
        return {"success": True, "verification": body.verification}
    
    @router.post(
        "/admin/{tenant_id}/reports/{report_id}/assign",
        summary="Assign report to team",
    )
    async def assign_report(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        body: AssignmentSchema = Body(...),
    ):
        """Assign a report to a user/team."""
        success = report_service.assign_report(
            tenant_id=tenant_id,
            report_id=report_id,
            user_id=body.user_id,
            team=body.team,
        )
        
        return {"success": success}
    
    @router.post(
        "/admin/{tenant_id}/reports/{report_id}/work-order",
        summary="Create work order from report",
    )
    async def create_work_order(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        body: CreateWorkOrderSchema = Body(...),
    ):
        """Create a work order from a public report."""
        work_order_id = report_service.create_work_order_from_report(
            tenant_id=tenant_id,
            report_id=report_id,
            actor_user_id="admin",  # Would come from auth
            priority=body.priority,
            notes=body.notes,
        )
        
        return {"success": True, "work_order_id": work_order_id}
    
    @router.post(
        "/admin/{tenant_id}/reports/{report_id}/link-leak",
        summary="Link report to AI leak",
    )
    async def link_to_leak(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        leak_id: str = Body(..., embed=True),
        boost_confidence: bool = Body(True, embed=True),
    ):
        """Link a public report to an AI-detected leak."""
        success = report_service.link_to_ai_leak(
            tenant_id=tenant_id,
            report_id=report_id,
            leak_id=leak_id,
            boost_confidence=boost_confidence,
        )
        
        return {"success": success}
    
    @router.post(
        "/admin/{tenant_id}/reports/merge",
        summary="Merge duplicate reports",
    )
    async def merge_reports(
        tenant_id: str = Path(...),
        body: MergeReportsSchema = Body(...),
    ):
        """Merge duplicate reports under a master."""
        success = duplicate_service.merge_reports(
            tenant_id=tenant_id,
            master_report_id=body.master_report_id,
            duplicate_report_ids=body.duplicate_report_ids,
            actor_user_id="admin",  # Would come from auth
            reason=body.reason,
        )
        
        return {"success": success}
    
    @router.post(
        "/admin/{tenant_id}/reports/{report_id}/unmerge",
        summary="Unmerge a report from its master",
    )
    async def unmerge_report(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
    ):
        """Remove a report from its master (unmerge)."""
        success = duplicate_service.unmerge_report(
            tenant_id=tenant_id,
            duplicate_report_id=report_id,
            actor_user_id="admin",
        )
        
        return {"success": success}
    
    @router.post(
        "/admin/{tenant_id}/reports/{report_id}/spam",
        summary="Mark report as spam",
    )
    async def mark_spam(
        tenant_id: str = Path(...),
        report_id: str = Path(...),
        is_spam: bool = Body(True, embed=True),
        reason: Optional[str] = Body(None, embed=True),
    ):
        """Mark or unmark a report as spam."""
        return {"success": True, "spam_flag": is_spam}
    
    # =========================================================================
    # ANALYTICS ENDPOINTS
    # =========================================================================
    
    @router.get(
        "/admin/{tenant_id}/analytics",
        response_model=AnalyticsResponse,
        summary="Get analytics metrics",
    )
    async def get_analytics(
        tenant_id: str = Path(...),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
    ):
        """Get analytics metrics for the tenant."""
        metrics = analytics_service.get_metrics(tenant_id)
        
        return AnalyticsResponse(
            total_reports=metrics.total_reports,
            reports_this_month=metrics.reports_this_month,
            reports_by_category=metrics.reports_by_category,
            reports_by_status=metrics.reports_by_status,
            confirmed_count=metrics.confirmed_count,
            false_count=metrics.false_count,
            confirmed_vs_false_ratio=metrics.confirmed_vs_false_ratio,
            avg_response_time_hours=metrics.avg_response_time_hours,
            avg_resolution_time_hours=metrics.avg_resolution_time_hours,
            hotspot_areas=metrics.hotspot_areas,
            conversion_rate=metrics.conversion_rate,
        )
    
    @router.get(
        "/admin/{tenant_id}/analytics/trend",
        summary="Get monthly trend data",
    )
    async def get_trend(
        tenant_id: str = Path(...),
        months: int = Query(12, ge=1, le=24),
    ):
        """Get monthly report trend data."""
        trend = analytics_service.get_monthly_trend(tenant_id, months)
        return {"trend": trend}
    
    @router.get(
        "/admin/{tenant_id}/analytics/export",
        summary="Export reports to CSV",
    )
    async def export_csv(
        tenant_id: str = Path(...),
        start_date: str = Query(..., description="Start date (ISO format)"),
        end_date: str = Query(..., description="End date (ISO format)"),
        include_contact: bool = Query(False, description="Include reporter contact info"),
    ):
        """Export reports to CSV format."""
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        csv_content = analytics_service.export_csv(
            tenant_id=tenant_id,
            start_date=start,
            end_date=end,
            include_contact_info=include_contact,
        )
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reports_{tenant_id}_{start_date}_{end_date}.csv"}
        )
    
    # =========================================================================
    # WHATSAPP BOT ENDPOINTS
    # =========================================================================
    
    # In-memory session store (use Redis in production)
    whatsapp_sessions: Dict[str, Dict[str, Any]] = {}
    
    @router.post(
        "/whatsapp/{tenant_id}/webhook",
        summary="WhatsApp bot webhook",
        description="Webhook endpoint for WhatsApp bot integration.",
    )
    async def whatsapp_webhook(
        tenant_id: str = Path(...),
        body: WhatsAppIncomingMessage = Body(...),
    ):
        """
        Handle incoming WhatsApp messages.
        
        Workflow:
        1. User sends "LEAK" or similar keyword
        2. Bot asks for report category
        3. Bot requests location
        4. Bot requests photo (optional)
        5. Bot asks for description
        6. Bot confirms and returns ticket ID + tracking link
        """
        phone = body.from_number
        session_key = f"{tenant_id}:{phone}"
        
        # Get or create session
        session = whatsapp_sessions.get(session_key, {"step": 0, "data": {}})
        
        # Process based on current step
        response_messages = []
        
        if session["step"] == 0:
            # Initial greeting / category selection
            text = (body.text or "").lower().strip()
            
            if any(kw in text for kw in ["leak", "burst", "water", "hi", "hello", "help"]):
                session["step"] = 1
                response_messages.append({
                    "type": "text",
                    "text": "Welcome to AquaWatch! 💧\n\nWhat would you like to report?\n\n1. Leak/Burst 💧\n2. No Water 🚫\n3. Low Pressure 📉\n4. Illegal Connection ⚠️\n5. Overflow/Flooding 🌊\n6. Other\n\nReply with a number (1-6):"
                })
            else:
                response_messages.append({
                    "type": "text",
                    "text": "Hello! Send 'LEAK' to report a water issue or 'STATUS' followed by your ticket number to check status."
                })
        
        elif session["step"] == 1:
            # Category selection
            text = (body.text or "").strip()
            category_map = {
                "1": "leak", "2": "no_water", "3": "low_pressure",
                "4": "illegal_connection", "5": "overflow", "6": "other"
            }
            
            if text in category_map:
                session["data"]["category"] = category_map[text]
                session["step"] = 2
                response_messages.append({
                    "type": "text",
                    "text": "📍 Please share your location.\n\nTap the attachment (+) icon and select 'Location' to send your current location.\n\nOr type your area/address:"
                })
            else:
                response_messages.append({
                    "type": "text",
                    "text": "Please reply with a number from 1 to 6."
                })
        
        elif session["step"] == 2:
            # Location
            if body.latitude and body.longitude:
                session["data"]["latitude"] = body.latitude
                session["data"]["longitude"] = body.longitude
                session["step"] = 3
            elif body.text:
                session["data"]["area_text"] = body.text
                session["step"] = 3
            
            if session["step"] == 3:
                response_messages.append({
                    "type": "text",
                    "text": "📷 Would you like to send a photo? (optional)\n\nSend a photo or type 'skip' to continue."
                })
            else:
                response_messages.append({
                    "type": "text",
                    "text": "Please share your location or type your area/address."
                })
        
        elif session["step"] == 3:
            # Photo (optional)
            text = (body.text or "").lower().strip()
            
            if body.media_url:
                session["data"]["media_url"] = body.media_url
            
            if body.media_url or text == "skip":
                session["step"] = 4
                response_messages.append({
                    "type": "text",
                    "text": "📝 Please describe the issue briefly (e.g., 'Water gushing from road'):"
                })
            else:
                response_messages.append({
                    "type": "text",
                    "text": "Send a photo or type 'skip' to continue."
                })
        
        elif session["step"] == 4:
            # Description
            if body.text and len(body.text) >= 5:
                session["data"]["description"] = body.text
                session["step"] = 5
                
                # Create the report
                report_request = ReportCreateRequest(
                    tenant_id=tenant_id,
                    category=session["data"]["category"],
                    description=session["data"].get("description"),
                    latitude=session["data"].get("latitude"),
                    longitude=session["data"].get("longitude"),
                    area_text=session["data"].get("area_text"),
                    source="whatsapp",
                    reporter_phone=phone,
                    session_id=session_key,
                )
                
                result = report_service.create_report(report_request, check_spam=True)
                
                if result.success:
                    response_messages.append({
                        "type": "text",
                        "text": f"✅ Report submitted successfully!\n\n🎫 Ticket: {result.ticket}\n\n🔗 Track status: https://aquawatch.zm{result.tracking_url}\n\nThank you for helping improve water services! 💧"
                    })
                else:
                    response_messages.append({
                        "type": "text",
                        "text": f"❌ Unable to submit report: {result.message}\n\nPlease try again later."
                    })
                
                # Reset session
                session = {"step": 0, "data": {}}
            else:
                response_messages.append({
                    "type": "text",
                    "text": "Please provide a brief description (at least 5 characters)."
                })
        
        # Save session
        whatsapp_sessions[session_key] = session
        
        return WhatsAppResponse(
            to=phone,
            messages=response_messages,
            session_data=session,
        )
    
    # =========================================================================
    # USSD ENDPOINTS
    # =========================================================================
    
    # In-memory USSD session store
    ussd_sessions: Dict[str, Dict[str, Any]] = {}
    
    # Area options for USSD (no GPS fallback)
    USSD_AREAS = [
        ("1", "Central Business District"),
        ("2", "Kabulonga"),
        ("3", "Chilenje"),
        ("4", "Matero"),
        ("5", "Garden Compound"),
        ("6", "Kamwala"),
        ("7", "Kalingalinga"),
        ("8", "Other"),
    ]
    
    @router.post(
        "/ussd/{tenant_id}/start",
        response_model=USSDResponse,
        summary="Start USSD session",
    )
    async def ussd_start(
        tenant_id: str = Path(...),
        body: USSDStartRequest = Body(...),
    ):
        """
        Start a new USSD session.
        
        Returns the main menu.
        """
        session_key = body.session_id
        
        # Initialize session
        ussd_sessions[session_key] = {
            "step": 0,
            "phone": body.phone_number,
            "tenant_id": tenant_id,
            "data": {},
        }
        
        menu = (
            "Welcome to AquaWatch\n"
            "Report Water Issues\n\n"
            "1. Report Leak\n"
            "2. No Water\n"
            "3. Low Pressure\n"
            "4. Check Status"
        )
        
        return USSDResponse(
            session_id=session_key,
            response_type="CON",
            message=menu,
        )
    
    @router.post(
        "/ussd/{tenant_id}/continue",
        response_model=USSDResponse,
        summary="Continue USSD session",
    )
    async def ussd_continue(
        tenant_id: str = Path(...),
        body: USSDContinueRequest = Body(...),
    ):
        """
        Continue an existing USSD session.
        
        Process user input and return next screen.
        """
        session_key = body.session_id
        user_input = body.text.strip()
        
        # Get session
        session = ussd_sessions.get(session_key)
        if not session:
            return USSDResponse(
                session_id=session_key,
                response_type="END",
                message="Session expired. Please dial again.",
            )
        
        step = session["step"]
        
        # Parse full input history for multi-step flows
        inputs = user_input.split("*")
        current_input = inputs[-1] if inputs else ""
        
        # Step 0: Main menu selection
        if step == 0:
            category_map = {"1": "leak", "2": "no_water", "3": "low_pressure"}
            
            if current_input == "4":
                # Check status flow
                session["step"] = 10
                ussd_sessions[session_key] = session
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Enter your ticket number\n(e.g., TKT-ABC123):",
                )
            elif current_input in category_map:
                session["data"]["category"] = category_map[current_input]
                session["step"] = 1
                
                # Show area selection
                area_menu = "Select your area:\n" + "\n".join(
                    f"{num}. {name}" for num, name in USSD_AREAS
                )
                
                ussd_sessions[session_key] = session
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message=area_menu,
                )
            else:
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Invalid option.\n1. Report Leak\n2. No Water\n3. Low Pressure\n4. Check Status",
                )
        
        # Step 1: Area selection
        elif step == 1:
            area_dict = dict(USSD_AREAS)
            if current_input in area_dict:
                session["data"]["area_text"] = area_dict[current_input]
                session["step"] = 2
                ussd_sessions[session_key] = session
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Briefly describe the issue\n(max 100 chars):",
                )
            else:
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Invalid area. Enter 1-8.",
                )
        
        # Step 2: Description
        elif step == 2:
            if len(current_input) >= 3:
                session["data"]["description"] = current_input[:100]
                
                # Create report
                report_request = ReportCreateRequest(
                    tenant_id=tenant_id,
                    category=session["data"]["category"],
                    description=session["data"]["description"],
                    area_text=session["data"]["area_text"],
                    source="ussd",
                    reporter_phone=session["phone"],
                    session_id=session_key,
                )
                
                result = report_service.create_report(report_request, check_spam=False)
                
                if result.success:
                    message = f"Report submitted!\nTicket: {result.ticket}\nTrack at aquawatch.zm{result.tracking_url}"
                else:
                    message = f"Error: {result.message}"
                
                # End session
                del ussd_sessions[session_key]
                return USSDResponse(
                    session_id=session_key,
                    response_type="END",
                    message=message,
                )
            else:
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Description too short. Try again:",
                )
        
        # Step 10: Check status - enter ticket
        elif step == 10:
            ticket = current_input.upper()
            if ticket.startswith("TKT-"):
                tracking = report_service.get_tracking_info(tenant_id, ticket)
                if tracking:
                    message = f"Ticket: {ticket}\nStatus: {tracking.status_label}\nCategory: {tracking.category}"
                else:
                    message = f"Ticket {ticket} not found."
                
                del ussd_sessions[session_key]
                return USSDResponse(
                    session_id=session_key,
                    response_type="END",
                    message=message,
                )
            else:
                return USSDResponse(
                    session_id=session_key,
                    response_type="CON",
                    message="Invalid format.\nEnter ticket (TKT-XXXXXX):",
                )
        
        # Default: end session
        if session_key in ussd_sessions:
            del ussd_sessions[session_key]
        return USSDResponse(
            session_id=session_key,
            response_type="END",
            message="Session ended. Dial again to restart.",
        )
    
    return router


# =============================================================================
# STANDALONE APP FOR TESTING
# =============================================================================

def create_standalone_app() -> FastAPI:
    """Create a standalone FastAPI app for testing."""
    
    app = FastAPI(
        title="AquaWatch Public Engagement API",
        description="Public reporting system for water issues",
        version="1.0.0",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include router
    router = create_public_engagement_api()
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "public-engagement"}
    
    return app


# For running standalone
if __name__ == "__main__":
    import uvicorn
    app = create_standalone_app()
    uvicorn.run(app, host="0.0.0.0", port=8080)
