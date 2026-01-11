"""
AquaWatch NRW - AI-Powered Non-Revenue Water Detection System
=============================================================

A comprehensive platform for detecting, localizing, and managing
water leaks in distribution networks across Zambia and South Africa.

Key Components:
- Storage: TimescaleDB data models
- Features: Physics-based feature engineering
- AI: Three-layer detection pipeline
- Baseline: Rule-based comparison system
- Dashboard: Three-tier user interface
- Workflow: Alert-to-resolution management
- Security: Authentication and authorization
"""

__version__ = "1.0.0"
__author__ = "AquaWatch Team"

from src.config.settings import get_config, get_utility_config

__all__ = [
    "get_config",
    "get_utility_config",
    "__version__"
]
