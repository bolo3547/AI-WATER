"""
AquaWatch Real Losses Module
============================

Production-grade leak detection, classification, and management system.
Focused on IWA Real Losses (physical leakage) in the RED ZONE:

- Leakage in Transmission & Distribution (mains leaks / burst pipes)
- Service Connection Leaks (connections/joints/house service pipes)
- Storage Leaks & Tank Overflows (reservoirs & elevated tanks)
"""

from .mnf_analyzer import MNFAnalyzer
from .burst_detector import BurstDetector
from .pressure_analyzer import PressureInstabilityAnalyzer
from .leak_localizer import LeakLocalizer
from .dispatch_engine import AutoDispatchEngine
from .report_generator import NRWReportGenerator

__all__ = [
    'MNFAnalyzer',
    'BurstDetector', 
    'PressureInstabilityAnalyzer',
    'LeakLocalizer',
    'AutoDispatchEngine',
    'NRWReportGenerator'
]
