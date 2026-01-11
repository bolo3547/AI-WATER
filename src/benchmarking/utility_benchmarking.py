"""
AquaWatch Network Benchmarking System
=====================================
Cross-utility KPI comparison and performance ranking system.
Enables utilities to compare performance against peers and identify improvement areas.

Features:
- IWA standard KPI tracking
- Peer utility comparison
- Performance ranking
- Best practice identification
- Improvement recommendations
- Historical trend analysis
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from collections import defaultdict


class KPICategory(Enum):
    """Categories of performance indicators"""
    WATER_RESOURCES = "water_resources"
    PERSONNEL = "personnel"
    PHYSICAL = "physical"
    OPERATIONAL = "operational"
    QUALITY_OF_SERVICE = "quality_of_service"
    FINANCIAL = "financial"
    NRW = "non_revenue_water"


class PerformanceLevel(Enum):
    """Performance levels for benchmarking"""
    EXCELLENT = "excellent"      # Top 10%
    GOOD = "good"               # 10-25%
    AVERAGE = "average"         # 25-50%
    BELOW_AVERAGE = "below_average"  # 50-75%
    POOR = "poor"               # Bottom 25%


@dataclass
class KPI:
    """Key Performance Indicator definition"""
    kpi_id: str
    name: str
    category: KPICategory
    unit: str
    description: str
    
    # Target values
    target_value: float
    excellent_threshold: float
    good_threshold: float
    poor_threshold: float
    
    # Direction (higher/lower is better)
    lower_is_better: bool = True
    
    # IWA reference
    iwa_code: str = ""


@dataclass
class UtilityProfile:
    """Profile of a water utility for benchmarking"""
    utility_id: str
    name: str
    country: str
    region: str
    
    # Size characteristics
    service_area_km2: float
    population_served: int
    connections: int
    staff_count: int
    
    # Infrastructure
    network_length_km: float
    storage_capacity_m3: float
    treatment_capacity_m3_day: float
    
    # Financial
    annual_revenue: float  # Local currency
    annual_opex: float
    
    # Current KPI values
    kpi_values: Dict[str, float] = field(default_factory=dict)
    kpi_history: Dict[str, List[Dict]] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of benchmarking analysis"""
    utility_id: str
    benchmark_date: datetime
    
    # Overall ranking
    overall_rank: int
    total_utilities: int
    overall_score: float  # 0-100
    
    # Category rankings
    category_ranks: Dict[str, int]
    category_scores: Dict[str, float]
    
    # Individual KPI results
    kpi_results: List[Dict]
    
    # Improvement areas
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class IWAKPILibrary:
    """IWA Standard KPI definitions"""
    
    def __init__(self):
        self.kpis: Dict[str, KPI] = {}
        self._initialize_kpis()
    
    def _initialize_kpis(self):
        """Initialize IWA standard KPIs"""
        kpi_definitions = [
            # Non-Revenue Water KPIs
            {
                "kpi_id": "NRW_001",
                "name": "NRW Percentage",
                "category": KPICategory.NRW,
                "unit": "%",
                "description": "Non-revenue water as percentage of system input volume",
                "target": 20.0,
                "excellent": 15.0,
                "good": 25.0,
                "poor": 40.0,
                "lower_better": True,
                "iwa_code": "Op28"
            },
            {
                "kpi_id": "NRW_002",
                "name": "Infrastructure Leakage Index (ILI)",
                "category": KPICategory.NRW,
                "unit": "ratio",
                "description": "Ratio of current annual real losses to unavoidable annual real losses",
                "target": 2.0,
                "excellent": 1.5,
                "good": 3.0,
                "poor": 8.0,
                "lower_better": True,
                "iwa_code": "Op25"
            },
            {
                "kpi_id": "NRW_003",
                "name": "Real Losses per Connection",
                "category": KPICategory.NRW,
                "unit": "L/conn/day",
                "description": "Real losses volume per service connection per day",
                "target": 100.0,
                "excellent": 50.0,
                "good": 150.0,
                "poor": 300.0,
                "lower_better": True,
                "iwa_code": "Op23"
            },
            {
                "kpi_id": "NRW_004",
                "name": "Apparent Losses Rate",
                "category": KPICategory.NRW,
                "unit": "%",
                "description": "Apparent losses as percentage of system input volume",
                "target": 5.0,
                "excellent": 2.0,
                "good": 8.0,
                "poor": 15.0,
                "lower_better": True,
                "iwa_code": "Op27"
            },
            
            # Operational KPIs
            {
                "kpi_id": "OP_001",
                "name": "Water Supply Continuity",
                "category": KPICategory.OPERATIONAL,
                "unit": "hours/day",
                "description": "Average hours of water supply per day",
                "target": 24.0,
                "excellent": 23.0,
                "good": 20.0,
                "poor": 12.0,
                "lower_better": False,
                "iwa_code": "QS13"
            },
            {
                "kpi_id": "OP_002",
                "name": "Pipe Breaks per 100km",
                "category": KPICategory.OPERATIONAL,
                "unit": "breaks/100km/year",
                "description": "Number of pipe breaks per 100 km of network per year",
                "target": 20.0,
                "excellent": 10.0,
                "good": 30.0,
                "poor": 60.0,
                "lower_better": True,
                "iwa_code": "Op32"
            },
            {
                "kpi_id": "OP_003",
                "name": "Leak Repair Time",
                "category": KPICategory.OPERATIONAL,
                "unit": "hours",
                "description": "Average time to repair reported leaks",
                "target": 24.0,
                "excellent": 8.0,
                "good": 48.0,
                "poor": 168.0,
                "lower_better": True,
                "iwa_code": "QS16"
            },
            {
                "kpi_id": "OP_004",
                "name": "Energy Efficiency",
                "category": KPICategory.OPERATIONAL,
                "unit": "kWh/m³",
                "description": "Energy consumption per cubic meter of water produced",
                "target": 0.5,
                "excellent": 0.3,
                "good": 0.7,
                "poor": 1.2,
                "lower_better": True,
                "iwa_code": "Ph5"
            },
            
            # Quality of Service KPIs
            {
                "kpi_id": "QS_001",
                "name": "Water Quality Compliance",
                "category": KPICategory.QUALITY_OF_SERVICE,
                "unit": "%",
                "description": "Percentage of water quality tests meeting standards",
                "target": 99.0,
                "excellent": 99.5,
                "good": 98.0,
                "poor": 95.0,
                "lower_better": False,
                "iwa_code": "QS1"
            },
            {
                "kpi_id": "QS_002",
                "name": "Customer Complaints",
                "category": KPICategory.QUALITY_OF_SERVICE,
                "unit": "per 1000 conn",
                "description": "Number of customer complaints per 1000 connections per year",
                "target": 10.0,
                "excellent": 5.0,
                "good": 20.0,
                "poor": 50.0,
                "lower_better": True,
                "iwa_code": "QS29"
            },
            {
                "kpi_id": "QS_003",
                "name": "Service Coverage",
                "category": KPICategory.QUALITY_OF_SERVICE,
                "unit": "%",
                "description": "Percentage of population with access to water service",
                "target": 100.0,
                "excellent": 98.0,
                "good": 90.0,
                "poor": 75.0,
                "lower_better": False,
                "iwa_code": "QS7"
            },
            
            # Financial KPIs
            {
                "kpi_id": "FN_001",
                "name": "Revenue Collection Efficiency",
                "category": KPICategory.FINANCIAL,
                "unit": "%",
                "description": "Percentage of billed revenue actually collected",
                "target": 95.0,
                "excellent": 98.0,
                "good": 90.0,
                "poor": 75.0,
                "lower_better": False,
                "iwa_code": "Fi36"
            },
            {
                "kpi_id": "FN_002",
                "name": "Operating Cost Coverage",
                "category": KPICategory.FINANCIAL,
                "unit": "ratio",
                "description": "Operating revenue divided by operating costs",
                "target": 1.2,
                "excellent": 1.5,
                "good": 1.0,
                "poor": 0.7,
                "lower_better": False,
                "iwa_code": "Fi1"
            },
            {
                "kpi_id": "FN_003",
                "name": "Unit Production Cost",
                "category": KPICategory.FINANCIAL,
                "unit": "ZMW/m³",
                "description": "Total production cost per cubic meter",
                "target": 8.0,
                "excellent": 5.0,
                "good": 12.0,
                "poor": 20.0,
                "lower_better": True,
                "iwa_code": "Fi26"
            },
            
            # Personnel KPIs
            {
                "kpi_id": "PE_001",
                "name": "Staff per 1000 Connections",
                "category": KPICategory.PERSONNEL,
                "unit": "staff/1000 conn",
                "description": "Number of staff per 1000 service connections",
                "target": 5.0,
                "excellent": 3.0,
                "good": 7.0,
                "poor": 12.0,
                "lower_better": True,
                "iwa_code": "Pe1"
            }
        ]
        
        for kpi_def in kpi_definitions:
            kpi = KPI(
                kpi_id=kpi_def["kpi_id"],
                name=kpi_def["name"],
                category=kpi_def["category"],
                unit=kpi_def["unit"],
                description=kpi_def["description"],
                target_value=kpi_def["target"],
                excellent_threshold=kpi_def["excellent"],
                good_threshold=kpi_def["good"],
                poor_threshold=kpi_def["poor"],
                lower_is_better=kpi_def["lower_better"],
                iwa_code=kpi_def["iwa_code"]
            )
            self.kpis[kpi.kpi_id] = kpi
    
    def get_kpi(self, kpi_id: str) -> Optional[KPI]:
        """Get KPI by ID"""
        return self.kpis.get(kpi_id)
    
    def get_kpis_by_category(self, category: KPICategory) -> List[KPI]:
        """Get all KPIs in a category"""
        return [kpi for kpi in self.kpis.values() if kpi.category == category]


class BenchmarkingEngine:
    """Engine for utility benchmarking"""
    
    def __init__(self):
        self.kpi_library = IWAKPILibrary()
        self.utilities: Dict[str, UtilityProfile] = {}
        
        # Regional benchmarks (Southern Africa)
        self.regional_benchmarks = self._initialize_regional_benchmarks()
        
        # Initialize demo utilities
        self._initialize_demo_utilities()
    
    def _initialize_regional_benchmarks(self) -> Dict:
        """Initialize regional benchmark data"""
        return {
            "southern_africa": {
                "NRW_001": {"median": 35.0, "best_quartile": 25.0, "worst_quartile": 50.0},
                "NRW_002": {"median": 5.0, "best_quartile": 3.0, "worst_quartile": 10.0},
                "NRW_003": {"median": 200.0, "best_quartile": 100.0, "worst_quartile": 400.0},
                "OP_001": {"median": 18.0, "best_quartile": 22.0, "worst_quartile": 12.0},
                "OP_002": {"median": 40.0, "best_quartile": 20.0, "worst_quartile": 80.0},
                "QS_001": {"median": 96.0, "best_quartile": 99.0, "worst_quartile": 90.0},
                "FN_001": {"median": 85.0, "best_quartile": 95.0, "worst_quartile": 70.0},
                "PE_001": {"median": 8.0, "best_quartile": 5.0, "worst_quartile": 15.0}
            },
            "global": {
                "NRW_001": {"median": 25.0, "best_quartile": 15.0, "worst_quartile": 40.0},
                "NRW_002": {"median": 3.0, "best_quartile": 1.5, "worst_quartile": 6.0},
                "OP_001": {"median": 22.0, "best_quartile": 24.0, "worst_quartile": 16.0}
            }
        }
    
    def _initialize_demo_utilities(self):
        """Initialize demo utilities for comparison"""
        utilities_data = [
            # Zambian utilities
            {
                "utility_id": "LWSC",
                "name": "Lusaka Water and Sewerage Company",
                "country": "Zambia",
                "region": "Lusaka",
                "area": 360,
                "population": 2500000,
                "connections": 180000,
                "staff": 1200,
                "network_km": 2800,
                "storage_m3": 150000,
                "treatment_m3": 380000,
                "revenue": 850000000,
                "opex": 720000000,
                "kpis": {
                    "NRW_001": 42.0,
                    "NRW_002": 6.5,
                    "NRW_003": 180.0,
                    "NRW_004": 8.0,
                    "OP_001": 16.0,
                    "OP_002": 45.0,
                    "OP_003": 36.0,
                    "OP_004": 0.65,
                    "QS_001": 95.5,
                    "QS_002": 25.0,
                    "QS_003": 78.0,
                    "FN_001": 82.0,
                    "FN_002": 1.18,
                    "FN_003": 9.50,
                    "PE_001": 6.7
                }
            },
            {
                "utility_id": "NWSC",
                "name": "Nkana Water and Sewerage Company",
                "country": "Zambia",
                "region": "Copperbelt",
                "area": 180,
                "population": 800000,
                "connections": 65000,
                "staff": 450,
                "network_km": 950,
                "storage_m3": 45000,
                "treatment_m3": 120000,
                "revenue": 280000000,
                "opex": 250000000,
                "kpis": {
                    "NRW_001": 48.0,
                    "NRW_002": 8.0,
                    "NRW_003": 220.0,
                    "OP_001": 14.0,
                    "OP_002": 55.0,
                    "QS_001": 94.0,
                    "FN_001": 78.0,
                    "PE_001": 6.9
                }
            },
            # South African utilities
            {
                "utility_id": "JOBURG",
                "name": "Johannesburg Water",
                "country": "South Africa",
                "region": "Gauteng",
                "area": 1645,
                "population": 5600000,
                "connections": 480000,
                "staff": 2800,
                "network_km": 12500,
                "storage_m3": 850000,
                "treatment_m3": 1800000,
                "revenue": 12000000000,  # ZAR
                "opex": 9500000000,
                "kpis": {
                    "NRW_001": 35.0,
                    "NRW_002": 4.5,
                    "NRW_003": 150.0,
                    "OP_001": 20.0,
                    "OP_002": 30.0,
                    "QS_001": 98.0,
                    "FN_001": 88.0,
                    "PE_001": 5.8
                }
            },
            {
                "utility_id": "CAPE",
                "name": "City of Cape Town Water",
                "country": "South Africa",
                "region": "Western Cape",
                "area": 2445,
                "population": 4200000,
                "connections": 420000,
                "staff": 2200,
                "network_km": 11000,
                "storage_m3": 950000,
                "treatment_m3": 1200000,
                "revenue": 9500000000,
                "opex": 7200000000,
                "kpis": {
                    "NRW_001": 22.0,
                    "NRW_002": 2.5,
                    "NRW_003": 85.0,
                    "OP_001": 23.0,
                    "OP_002": 18.0,
                    "QS_001": 99.5,
                    "FN_001": 95.0,
                    "PE_001": 5.2
                }
            },
            # Best practice utility
            {
                "utility_id": "SINGAPORE",
                "name": "PUB Singapore",
                "country": "Singapore",
                "region": "Singapore",
                "area": 728,
                "population": 5800000,
                "connections": 1600000,
                "staff": 3200,
                "network_km": 5500,
                "storage_m3": 1200000,
                "treatment_m3": 2000000,
                "revenue": 1800000000,  # SGD
                "opex": 1200000000,
                "kpis": {
                    "NRW_001": 5.0,
                    "NRW_002": 1.2,
                    "NRW_003": 25.0,
                    "OP_001": 24.0,
                    "OP_002": 8.0,
                    "QS_001": 99.9,
                    "FN_001": 99.0,
                    "PE_001": 2.0
                }
            }
        ]
        
        for udata in utilities_data:
            profile = UtilityProfile(
                utility_id=udata["utility_id"],
                name=udata["name"],
                country=udata["country"],
                region=udata["region"],
                service_area_km2=udata["area"],
                population_served=udata["population"],
                connections=udata["connections"],
                staff_count=udata["staff"],
                network_length_km=udata["network_km"],
                storage_capacity_m3=udata["storage_m3"],
                treatment_capacity_m3_day=udata["treatment_m3"],
                annual_revenue=udata["revenue"],
                annual_opex=udata["opex"],
                kpi_values=udata.get("kpis", {})
            )
            self.utilities[profile.utility_id] = profile
    
    def evaluate_kpi_performance(
        self,
        kpi_id: str,
        value: float
    ) -> Tuple[PerformanceLevel, float]:
        """
        Evaluate KPI value against thresholds.
        
        Returns:
            Tuple of (performance level, score 0-100)
        """
        kpi = self.kpi_library.get_kpi(kpi_id)
        if not kpi:
            return PerformanceLevel.AVERAGE, 50.0
        
        # Calculate score based on position between thresholds
        if kpi.lower_is_better:
            if value <= kpi.excellent_threshold:
                level = PerformanceLevel.EXCELLENT
                score = 100 - (value / kpi.excellent_threshold * 10)
            elif value <= kpi.good_threshold:
                level = PerformanceLevel.GOOD
                ratio = (value - kpi.excellent_threshold) / (kpi.good_threshold - kpi.excellent_threshold)
                score = 90 - ratio * 15
            elif value <= kpi.target_value:
                level = PerformanceLevel.AVERAGE
                ratio = (value - kpi.good_threshold) / (kpi.target_value - kpi.good_threshold)
                score = 75 - ratio * 25
            elif value <= kpi.poor_threshold:
                level = PerformanceLevel.BELOW_AVERAGE
                ratio = (value - kpi.target_value) / (kpi.poor_threshold - kpi.target_value)
                score = 50 - ratio * 25
            else:
                level = PerformanceLevel.POOR
                score = max(0, 25 - (value - kpi.poor_threshold) / kpi.poor_threshold * 25)
        else:
            # Higher is better
            if value >= kpi.excellent_threshold:
                level = PerformanceLevel.EXCELLENT
                score = min(100, 90 + (value - kpi.excellent_threshold) / kpi.excellent_threshold * 10)
            elif value >= kpi.good_threshold:
                level = PerformanceLevel.GOOD
                ratio = (kpi.excellent_threshold - value) / (kpi.excellent_threshold - kpi.good_threshold)
                score = 90 - ratio * 15
            elif value >= kpi.target_value:
                level = PerformanceLevel.AVERAGE
                ratio = (kpi.good_threshold - value) / (kpi.good_threshold - kpi.target_value)
                score = 75 - ratio * 25
            elif value >= kpi.poor_threshold:
                level = PerformanceLevel.BELOW_AVERAGE
                ratio = (kpi.target_value - value) / (kpi.target_value - kpi.poor_threshold)
                score = 50 - ratio * 25
            else:
                level = PerformanceLevel.POOR
                score = max(0, 25 * value / kpi.poor_threshold)
        
        return level, max(0, min(100, score))
    
    def benchmark_utility(self, utility_id: str) -> BenchmarkResult:
        """
        Benchmark a utility against peers.
        
        Args:
            utility_id: Utility ID
        
        Returns:
            BenchmarkResult with rankings and recommendations
        """
        if utility_id not in self.utilities:
            raise ValueError(f"Utility {utility_id} not found")
        
        utility = self.utilities[utility_id]
        
        # Calculate KPI results
        kpi_results = []
        category_scores = defaultdict(list)
        
        for kpi_id, value in utility.kpi_values.items():
            kpi = self.kpi_library.get_kpi(kpi_id)
            if not kpi:
                continue
            
            level, score = self.evaluate_kpi_performance(kpi_id, value)
            
            # Get peer comparison
            peer_values = [
                u.kpi_values.get(kpi_id)
                for u in self.utilities.values()
                if u.utility_id != utility_id and kpi_id in u.kpi_values
            ]
            peer_values = [v for v in peer_values if v is not None]
            
            if peer_values:
                if kpi.lower_is_better:
                    rank = sum(1 for v in peer_values if v < value) + 1
                else:
                    rank = sum(1 for v in peer_values if v > value) + 1
                peer_median = np.median(peer_values)
                peer_best = min(peer_values) if kpi.lower_is_better else max(peer_values)
            else:
                rank = 1
                peer_median = value
                peer_best = value
            
            kpi_results.append({
                "kpi_id": kpi_id,
                "kpi_name": kpi.name,
                "category": kpi.category.value,
                "value": value,
                "unit": kpi.unit,
                "target": kpi.target_value,
                "performance_level": level.value,
                "score": score,
                "rank": rank,
                "total_peers": len(peer_values) + 1,
                "peer_median": peer_median,
                "peer_best": peer_best,
                "gap_to_target": value - kpi.target_value if kpi.lower_is_better else kpi.target_value - value,
                "gap_to_best": value - peer_best if kpi.lower_is_better else peer_best - value
            })
            
            category_scores[kpi.category.value].append(score)
        
        # Calculate category averages
        category_avg = {
            cat: np.mean(scores) if scores else 50.0
            for cat, scores in category_scores.items()
        }
        
        # Calculate overall score
        overall_score = np.mean(list(category_avg.values())) if category_avg else 50.0
        
        # Calculate overall rank
        all_scores = []
        for u in self.utilities.values():
            u_scores = []
            for kpi_id, value in u.kpi_values.items():
                _, score = self.evaluate_kpi_performance(kpi_id, value)
                u_scores.append(score)
            if u_scores:
                all_scores.append((u.utility_id, np.mean(u_scores)))
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
        overall_rank = next(
            (i + 1 for i, (uid, _) in enumerate(all_scores) if uid == utility_id),
            len(all_scores)
        )
        
        # Identify strengths and weaknesses
        sorted_kpis = sorted(kpi_results, key=lambda x: x["score"], reverse=True)
        strengths = [
            f"{k['kpi_name']}: {k['performance_level']} ({k['value']:.1f} {k['unit']})"
            for k in sorted_kpis[:3]
            if k["score"] >= 70
        ]
        weaknesses = [
            f"{k['kpi_name']}: {k['performance_level']} ({k['value']:.1f} {k['unit']})"
            for k in sorted_kpis[-3:]
            if k["score"] < 50
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(kpi_results, utility)
        
        # Category ranks
        category_ranks = {}
        for category in KPICategory:
            cat_scores = []
            for u in self.utilities.values():
                u_cat_scores = []
                for kpi_id, value in u.kpi_values.items():
                    kpi = self.kpi_library.get_kpi(kpi_id)
                    if kpi and kpi.category == category:
                        _, score = self.evaluate_kpi_performance(kpi_id, value)
                        u_cat_scores.append(score)
                if u_cat_scores:
                    cat_scores.append((u.utility_id, np.mean(u_cat_scores)))
            
            cat_scores.sort(key=lambda x: x[1], reverse=True)
            category_ranks[category.value] = next(
                (i + 1 for i, (uid, _) in enumerate(cat_scores) if uid == utility_id),
                len(cat_scores)
            )
        
        return BenchmarkResult(
            utility_id=utility_id,
            benchmark_date=datetime.now(),
            overall_rank=overall_rank,
            total_utilities=len(self.utilities),
            overall_score=overall_score,
            category_ranks=category_ranks,
            category_scores=category_avg,
            kpi_results=kpi_results,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        kpi_results: List[Dict],
        utility: UtilityProfile
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Sort by score (lowest first - these need improvement)
        poor_kpis = [k for k in kpi_results if k["score"] < 50]
        
        for kpi in poor_kpis[:5]:  # Top 5 priorities
            kpi_id = kpi["kpi_id"]
            gap = kpi["gap_to_target"]
            
            if kpi_id == "NRW_001":
                recommendations.append(
                    f"Reduce NRW from {kpi['value']:.0f}% to {kpi['target']:.0f}% "
                    f"through active leak detection and pressure management"
                )
            elif kpi_id == "NRW_002":
                recommendations.append(
                    f"Improve ILI from {kpi['value']:.1f} to {kpi['target']:.1f} "
                    f"by investing in infrastructure renewal"
                )
            elif kpi_id == "OP_001":
                recommendations.append(
                    f"Increase supply continuity from {kpi['value']:.0f} to {kpi['target']:.0f} hours/day "
                    f"through network optimization and storage expansion"
                )
            elif kpi_id == "OP_002":
                recommendations.append(
                    f"Reduce pipe breaks from {kpi['value']:.0f} to {kpi['target']:.0f} per 100km "
                    f"through predictive maintenance and pipe replacement"
                )
            elif kpi_id == "FN_001":
                recommendations.append(
                    f"Improve revenue collection from {kpi['value']:.0f}% to {kpi['target']:.0f}% "
                    f"through smart metering and customer engagement"
                )
            else:
                recommendations.append(
                    f"Improve {kpi['kpi_name']} from {kpi['value']:.1f} to {kpi['target']:.1f}"
                )
        
        return recommendations
    
    def compare_utilities(
        self,
        utility_ids: List[str],
        kpi_ids: List[str] = None
    ) -> Dict:
        """
        Compare multiple utilities on selected KPIs.
        
        Args:
            utility_ids: List of utility IDs to compare
            kpi_ids: List of KPI IDs (None = all)
        
        Returns:
            Comparison matrix
        """
        if not kpi_ids:
            kpi_ids = list(self.kpi_library.kpis.keys())
        
        comparison = {
            "kpis": [],
            "utilities": [],
            "data": {}
        }
        
        for uid in utility_ids:
            if uid in self.utilities:
                u = self.utilities[uid]
                comparison["utilities"].append({
                    "id": uid,
                    "name": u.name,
                    "country": u.country
                })
        
        for kpi_id in kpi_ids:
            kpi = self.kpi_library.get_kpi(kpi_id)
            if not kpi:
                continue
            
            comparison["kpis"].append({
                "id": kpi_id,
                "name": kpi.name,
                "unit": kpi.unit,
                "target": kpi.target_value,
                "lower_is_better": kpi.lower_is_better
            })
            
            comparison["data"][kpi_id] = {}
            
            for uid in utility_ids:
                if uid in self.utilities:
                    value = self.utilities[uid].kpi_values.get(kpi_id)
                    if value is not None:
                        level, score = self.evaluate_kpi_performance(kpi_id, value)
                        comparison["data"][kpi_id][uid] = {
                            "value": value,
                            "score": score,
                            "level": level.value
                        }
        
        return comparison
    
    def get_regional_benchmark(self, utility_id: str) -> Dict:
        """Get regional benchmark comparison"""
        if utility_id not in self.utilities:
            return {"error": "Utility not found"}
        
        utility = self.utilities[utility_id]
        region = "southern_africa"  # Default for Zambia/SA
        
        benchmarks = self.regional_benchmarks.get(region, {})
        
        results = []
        for kpi_id, value in utility.kpi_values.items():
            if kpi_id in benchmarks:
                bench = benchmarks[kpi_id]
                kpi = self.kpi_library.get_kpi(kpi_id)
                
                if kpi:
                    # Determine quartile position
                    if kpi.lower_is_better:
                        if value <= bench["best_quartile"]:
                            quartile = "top_25"
                        elif value <= bench["median"]:
                            quartile = "upper_50"
                        elif value <= bench["worst_quartile"]:
                            quartile = "lower_50"
                        else:
                            quartile = "bottom_25"
                    else:
                        if value >= bench["best_quartile"]:
                            quartile = "top_25"
                        elif value >= bench["median"]:
                            quartile = "upper_50"
                        elif value >= bench["worst_quartile"]:
                            quartile = "lower_50"
                        else:
                            quartile = "bottom_25"
                    
                    results.append({
                        "kpi_id": kpi_id,
                        "kpi_name": kpi.name,
                        "value": value,
                        "regional_median": bench["median"],
                        "regional_best": bench["best_quartile"],
                        "regional_worst": bench["worst_quartile"],
                        "quartile_position": quartile
                    })
        
        return {
            "utility_id": utility_id,
            "utility_name": utility.name,
            "region": region,
            "results": results
        }
    
    def get_benchmark_dashboard(self, utility_id: str) -> Dict:
        """Get comprehensive benchmark dashboard"""
        result = self.benchmark_utility(utility_id)
        regional = self.get_regional_benchmark(utility_id)
        
        utility = self.utilities[utility_id]
        
        return {
            "utility": {
                "id": utility.utility_id,
                "name": utility.name,
                "country": utility.country,
                "region": utility.region,
                "connections": utility.connections,
                "network_km": utility.network_length_km
            },
            "overall_performance": {
                "score": result.overall_score,
                "rank": result.overall_rank,
                "total_utilities": result.total_utilities,
                "percentile": (result.total_utilities - result.overall_rank + 1) / result.total_utilities * 100
            },
            "category_performance": result.category_scores,
            "category_ranks": result.category_ranks,
            "kpi_details": result.kpi_results,
            "regional_comparison": regional.get("results", []),
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": result.recommendations,
            "peer_comparison": {
                "better_than": result.total_utilities - result.overall_rank,
                "peers_in_region": len([
                    u for u in self.utilities.values()
                    if u.country == utility.country
                ])
            }
        }


# Global instance
benchmarking_engine = BenchmarkingEngine()


def get_benchmarking_engine() -> BenchmarkingEngine:
    """Get global benchmarking engine"""
    return benchmarking_engine


if __name__ == "__main__":
    # Demo
    engine = BenchmarkingEngine()
    
    print("=" * 60)
    print("AquaWatch Network Benchmarking")
    print("=" * 60)
    
    # Benchmark LWSC
    print("\nBenchmarking: Lusaka Water and Sewerage Company")
    result = engine.benchmark_utility("LWSC")
    
    print(f"\nOverall Performance:")
    print(f"  Score: {result.overall_score:.1f}/100")
    print(f"  Rank: {result.overall_rank} of {result.total_utilities}")
    
    print(f"\nCategory Scores:")
    for cat, score in result.category_scores.items():
        print(f"  {cat}: {score:.1f}")
    
    print(f"\nStrengths:")
    for s in result.strengths:
        print(f"  ✓ {s}")
    
    print(f"\nWeaknesses:")
    for w in result.weaknesses:
        print(f"  ✗ {w}")
    
    print(f"\nRecommendations:")
    for r in result.recommendations[:3]:
        print(f"  → {r}")
    
    # Compare utilities
    print(f"\n{'='*60}")
    print("Utility Comparison")
    comparison = engine.compare_utilities(
        ["LWSC", "CAPE", "SINGAPORE"],
        ["NRW_001", "NRW_002", "OP_001"]
    )
    
    print(f"\nNRW Percentage Comparison:")
    for uid in ["LWSC", "CAPE", "SINGAPORE"]:
        data = comparison["data"]["NRW_001"].get(uid, {})
        print(f"  {uid}: {data.get('value', 'N/A')}% ({data.get('level', 'N/A')})")
