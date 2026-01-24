"""
AquaWatch NRW - Public Engagement Models
========================================

Database models for public reporting system.
All tables include tenant_id for multi-tenant isolation.

Tables:
- public_reports: Main reports from public
- public_report_media: Photos/videos attached to reports
- public_report_links: Duplicate report links
- public_engagement_audit_logs: Audit trail for all actions
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid
import secrets
import string

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Text, Enum as SQLEnum, Numeric, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import base from main models
try:
    from src.storage.models import Base
except ImportError:
    Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================

class ReportCategory(str, Enum):
    """Types of reports the public can submit."""
    LEAK = "leak"
    BURST = "burst"
    NO_WATER = "no_water"
    LOW_PRESSURE = "low_pressure"
    ILLEGAL_CONNECTION = "illegal_connection"
    OVERFLOW = "overflow"
    CONTAMINATION = "contamination"
    OTHER = "other"


class ReportStatus(str, Enum):
    """Public-safe status values for reports."""
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    TECHNICIAN_ASSIGNED = "technician_assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReportSource(str, Enum):
    """Channel through which report was submitted."""
    WEB = "web"
    WHATSAPP = "whatsapp"
    USSD = "ussd"
    MOBILE_APP = "mobile_app"
    CALL_CENTER = "call_center"


class ReportVerification(str, Enum):
    """Admin verification status of a report."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DUPLICATE = "duplicate"
    FALSE_REPORT = "false_report"
    NEEDS_REVIEW = "needs_review"
    SPAM = "spam"


class MediaType(str, Enum):
    """Types of media attachments."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_ticket_id(prefix: str = "TKT") -> str:
    """
    Generate a short, unique ticket ID.
    Format: TKT-XXXXXX (e.g., TKT-A3B7C9)
    """
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(6))
    return f"{prefix}-{random_part}"


# =============================================================================
# PUBLIC REPORTS TABLE
# =============================================================================

class PublicReport(Base):
    """
    Public reports from community members.
    
    This table stores all reports submitted through various channels:
    - Web form
    - WhatsApp bot
    - USSD menu
    
    Security:
    - All records include tenant_id for multi-tenant isolation
    - Reporter contact info is hidden from public-facing APIs
    - Public can only see ticket ID, status, and safe timeline updates
    """
    __tablename__ = "public_reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy (REQUIRED for all records)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Unique ticket ID for public tracking (e.g., TKT-A3B7C9)
    ticket = Column(String(20), unique=True, nullable=False, default=generate_ticket_id)
    
    # Report classification
    category = Column(SQLEnum(ReportCategory), nullable=False)
    description = Column(Text)
    
    # Location (GPS or text-based)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    area_text = Column(String(500), nullable=True)  # Text fallback for no GPS
    
    # DMA association (set by admin during triage)
    dma_id = Column(UUID(as_uuid=True), ForeignKey("dmas.id"), nullable=True)
    
    # Source channel
    source = Column(SQLEnum(ReportSource), nullable=False, default=ReportSource.WEB)
    
    # Reporter contact (PRIVATE - never exposed to public)
    reporter_name = Column(String(200), nullable=True)
    reporter_phone = Column(String(50), nullable=True)
    reporter_email = Column(String(200), nullable=True)
    reporter_consent = Column(Boolean, default=False)  # Consent to be contacted
    
    # WhatsApp/USSD specific
    whatsapp_phone_hash = Column(String(64), nullable=True)  # Hashed phone for dedup
    session_id = Column(String(100), nullable=True)  # Bot session tracking
    
    # Status workflow
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.RECEIVED, nullable=False)
    verification = Column(SQLEnum(ReportVerification), default=ReportVerification.PENDING)
    
    # Trust and spam detection
    trust_score_delta = Column(Integer, default=0)  # Adjustment to AI confidence
    spam_flag = Column(Boolean, default=False)
    spam_reason = Column(String(200), nullable=True)
    quarantine = Column(Boolean, default=False)  # Flagged for manual review
    
    # Duplicate detection
    master_report_id = Column(UUID(as_uuid=True), ForeignKey("public_reports.id"), nullable=True)
    is_master = Column(Boolean, default=True)  # True if this is the master report
    duplicate_count = Column(Integer, default=0)  # Number of duplicates linked
    
    # Linking to AI/System entities
    linked_leak_id = Column(UUID(as_uuid=True), ForeignKey("leak_events.id"), nullable=True)
    linked_alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=True)
    linked_work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=True)
    
    # Admin notes (PRIVATE)
    admin_notes = Column(Text, nullable=True)
    
    # Assignment (PRIVATE - technician info never exposed to public)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_team = Column(String(100), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Rate limiting metadata
    reporter_ip = Column(String(50), nullable=True)
    device_fingerprint = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    media = relationship("PublicReportMedia", back_populates="report", cascade="all, delete-orphan")
    duplicates = relationship("PublicReportLink", foreign_keys="PublicReportLink.master_report_id", back_populates="master_report")
    
    __table_args__ = (
        # Tenant isolation index
        Index("ix_public_reports_tenant_id", "tenant_id"),
        # Ticket lookup
        Index("ix_public_reports_ticket", "ticket"),
        # Status filtering
        Index("ix_public_reports_status", "status"),
        # Category filtering
        Index("ix_public_reports_category", "category"),
        # Geographic queries
        Index("ix_public_reports_location", "latitude", "longitude"),
        # Time-based queries
        Index("ix_public_reports_created", "created_at"),
        # Spam filter
        Index("ix_public_reports_spam", "spam_flag", "quarantine"),
        # Duplicate lookup
        Index("ix_public_reports_master", "master_report_id"),
        # DMA filtering
        Index("ix_public_reports_dma", "dma_id"),
    )
    
    def __repr__(self):
        return f"<PublicReport {self.ticket}: {self.category.value} ({self.status.value})>"
    
    def to_public_dict(self) -> dict:
        """
        Return public-safe representation.
        NEVER includes reporter contact info, technician names, or internal notes.
        """
        return {
            "ticket": self.ticket,
            "status": self.status.value,
            "category": self.category.value,
            "area": self.area_text,  # Generic area, not exact coordinates
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
    
    def to_admin_dict(self) -> dict:
        """
        Return full representation for admin users.
        Includes all details for triage and management.
        """
        return {
            "id": str(self.id),
            "ticket": self.ticket,
            "tenant_id": self.tenant_id,
            "category": self.category.value,
            "description": self.description,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "area_text": self.area_text,
            "source": self.source.value,
            "reporter_name": self.reporter_name,
            "reporter_phone": self.reporter_phone,
            "reporter_email": self.reporter_email,
            "reporter_consent": self.reporter_consent,
            "status": self.status.value,
            "verification": self.verification.value,
            "trust_score_delta": self.trust_score_delta,
            "spam_flag": self.spam_flag,
            "spam_reason": self.spam_reason,
            "quarantine": self.quarantine,
            "master_report_id": str(self.master_report_id) if self.master_report_id else None,
            "is_master": self.is_master,
            "duplicate_count": self.duplicate_count,
            "linked_leak_id": str(self.linked_leak_id) if self.linked_leak_id else None,
            "linked_alert_id": str(self.linked_alert_id) if self.linked_alert_id else None,
            "linked_work_order_id": str(self.linked_work_order_id) if self.linked_work_order_id else None,
            "admin_notes": self.admin_notes,
            "assigned_to_user_id": str(self.assigned_to_user_id) if self.assigned_to_user_id else None,
            "assigned_team": self.assigned_team,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "media_count": len(self.media) if self.media else 0,
        }


# =============================================================================
# MEDIA ATTACHMENTS TABLE
# =============================================================================

class PublicReportMedia(Base):
    """
    Media attachments (photos, videos) for public reports.
    
    Storage:
    - Local disk: /uploads/{tenant_id}/{report_id}/{filename}
    - S3: s3://{bucket}/{tenant_id}/{report_id}/{filename}
    """
    __tablename__ = "public_report_media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Parent report
    report_id = Column(UUID(as_uuid=True), ForeignKey("public_reports.id", ondelete="CASCADE"), nullable=False)
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    media_type = Column(SQLEnum(MediaType), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Storage path
    storage_path = Column(String(500), nullable=False)  # Local path or S3 key
    url = Column(String(500), nullable=True)  # Public URL if applicable
    
    # Metadata
    width = Column(Integer, nullable=True)  # For images
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # For video/audio
    
    # GPS from EXIF (if available)
    exif_latitude = Column(Numeric(10, 7), nullable=True)
    exif_longitude = Column(Numeric(10, 7), nullable=True)
    exif_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    report = relationship("PublicReport", back_populates="media")
    
    __table_args__ = (
        Index("ix_public_report_media_tenant", "tenant_id"),
        Index("ix_public_report_media_report", "report_id"),
    )
    
    def __repr__(self):
        return f"<PublicReportMedia {self.filename} ({self.media_type.value})>"


# =============================================================================
# DUPLICATE REPORT LINKS TABLE
# =============================================================================

class PublicReportLink(Base):
    """
    Links between master reports and their duplicates.
    
    When multiple reports are detected as duplicates:
    1. The first report becomes the master
    2. Subsequent reports are linked via this table
    3. Admin can merge/unmerge as needed
    """
    __tablename__ = "public_report_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Master report (the primary report)
    master_report_id = Column(UUID(as_uuid=True), ForeignKey("public_reports.id", ondelete="CASCADE"), nullable=False)
    
    # Duplicate report (linked to master)
    duplicate_report_id = Column(UUID(as_uuid=True), ForeignKey("public_reports.id", ondelete="CASCADE"), nullable=False)
    
    # Why they were linked
    reason = Column(String(200), nullable=True)  # "proximity_time", "same_location", "manual"
    
    # Linking metadata
    distance_meters = Column(Numeric(10, 2), nullable=True)
    time_diff_minutes = Column(Integer, nullable=True)
    similarity_score = Column(Numeric(5, 4), nullable=True)  # 0-1 score
    
    # Auto vs manual
    auto_detected = Column(Boolean, default=True)
    linked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    master_report = relationship("PublicReport", foreign_keys=[master_report_id], back_populates="duplicates")
    
    __table_args__ = (
        Index("ix_public_report_links_tenant", "tenant_id"),
        Index("ix_public_report_links_master", "master_report_id"),
        Index("ix_public_report_links_duplicate", "duplicate_report_id"),
        UniqueConstraint("master_report_id", "duplicate_report_id", name="uq_report_link"),
    )
    
    def __repr__(self):
        return f"<PublicReportLink {self.duplicate_report_id} -> {self.master_report_id}>"


# =============================================================================
# AUDIT LOG TABLE (Public Engagement Specific)
# =============================================================================

class PublicEngagementAuditLog(Base):
    """
    Audit trail for all public engagement actions.
    
    Records:
    - Report creation
    - Status updates
    - Assignment changes
    - Duplicate merging
    - Spam marking
    - Work order creation
    
    Note: actor_user_id is NULL for public/system actions.
    """
    __tablename__ = "public_engagement_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Who performed the action (NULL for public/system)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_type = Column(String(50), default="system")  # "user", "system", "public", "whatsapp", "ussd"
    
    # What was done
    action = Column(String(100), nullable=False)  # "create_report", "update_status", "assign", etc.
    
    # Target entity
    entity_type = Column(String(50), nullable=False)  # "public_report", "work_order", "leak"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Additional context
    meta_json = Column(JSONB, nullable=True)  # Flexible metadata
    
    # Change tracking
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    
    # Request context (for security tracking)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("ix_pe_audit_tenant", "tenant_id"),
        Index("ix_pe_audit_entity", "entity_type", "entity_id"),
        Index("ix_pe_audit_action", "action"),
        Index("ix_pe_audit_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<PublicEngagementAuditLog {self.action} on {self.entity_type}:{self.entity_id}>"


# =============================================================================
# TIMELINE UPDATE TABLE (for public status updates)
# =============================================================================

class PublicReportTimeline(Base):
    """
    Public-safe timeline updates for reports.
    
    These are the updates shown to the public when they track their ticket.
    Contains only safe, generic messages - no internal details.
    """
    __tablename__ = "public_report_timeline"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Parent report
    report_id = Column(UUID(as_uuid=True), ForeignKey("public_reports.id", ondelete="CASCADE"), nullable=False)
    
    # Status at this point
    status = Column(SQLEnum(ReportStatus), nullable=False)
    
    # Public-safe message
    message = Column(String(500), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("ix_pe_timeline_tenant", "tenant_id"),
        Index("ix_pe_timeline_report", "report_id"),
        Index("ix_pe_timeline_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<PublicReportTimeline {self.report_id}: {self.status.value}>"
    
    def to_public_dict(self) -> dict:
        """Safe representation for public viewing."""
        return {
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
