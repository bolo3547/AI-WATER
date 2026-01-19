"""
AquaWatch NRW - System Input Volume (SIV) Module
================================================

CRITICAL FOUNDATION - NRW does not exist without SIV.

This module provides:
1. SIV data models (treatment plants, reservoirs, bulk meters)
2. DMA inlet flow tracking
3. REST API and CSV batch ingestion
4. Timestamp alignment and unit validation
"""

from .siv_manager import (
    SIVManager,
    SIVRecord,
    DMAInletFlow,
    SIVSource,
    SIVSourceType,
    BillingRecord,
)

__all__ = [
    'SIVManager',
    'SIVRecord',
    'DMAInletFlow',
    'SIVSource',
    'SIVSourceType',
    'BillingRecord',
]
