"""
AquaWatch NRW - Public Engagement Module
=========================================

This module enables the public to help water utilities reduce NRW by reporting:
- Leaks / Bursts
- Low pressure / No water  
- Illegal connections
- Tank overflows / Flooding
- Contamination risk events

Supports multiple channels:
- WhatsApp (primary for Zambia)
- Web form
- USSD (for feature phones)

Author: AquaWatch AI Team
Version: 1.0.0
"""

from .models import (
    ReportCategory,
    ReportStatus,
    ReportSource,
    PublicReport,
    PublicReportMedia,
    PublicReportLink,
    PublicEngagementAuditLog,
)
from .services import (
    PublicReportService,
    DuplicateDetectionService,
    SpamDetectionService,
    AnalyticsService,
)
from .api import create_public_engagement_api

__all__ = [
    # Models
    "ReportCategory",
    "ReportStatus", 
    "ReportSource",
    "PublicReport",
    "PublicReportMedia",
    "PublicReportLink",
    "PublicEngagementAuditLog",
    # Services
    "PublicReportService",
    "DuplicateDetectionService",
    "SpamDetectionService",
    "AnalyticsService",
    # API
    "create_public_engagement_api",
]
