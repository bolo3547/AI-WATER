"""
AquaWatch NRW - NRW Module
==========================

Non-Revenue Water calculation following IWA Water Balance framework.

NRW = System Input Volume - Billed Authorized - Unbilled Authorized
NRW = Real Losses + Apparent Losses

This module focuses on REAL LOSSES (physical leakage).
"""

from .nrw_calculator import (
    NRWCalculator,
    NRWResult,
    DMANRWSummary,
    calculate_simple_nrw,
    get_nrw_rating,
)

__all__ = [
    'NRWCalculator',
    'NRWResult',
    'DMANRWSummary',
    'calculate_simple_nrw',
    'get_nrw_rating',
]
