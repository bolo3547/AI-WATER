"""
AquaWatch NRW - Regulatory Compliance Module
=============================================

Compliance management for water utilities in Zambia and Southern Africa.

Regulatory Bodies:
- NWASCO (National Water Supply and Sanitation Council) - Zambia
- DWS (Department of Water and Sanitation) - South Africa
- WARMA (Water Resources Management Authority) - Zambia

Features:
- Automated compliance reporting
- Audit trail management
- KPI tracking and benchmarking
- License/permit management
- Incident reporting
- Regulatory deadline tracking
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# NWASCO KPIs (Zambia)
NWASCO_KPIS = {
    "nrw_percent": {
        "name": "Non-Revenue Water",
        "unit": "%",
        "target": 25,
        "warning": 35,
        "critical": 45,
        "weight": 15
    },
    "water_quality_compliance": {
        "name": "Water Quality Compliance",
        "unit": "%",
        "target": 95,
        "warning": 85,
        "critical": 70,
        "weight": 20
    },
    "hours_of_supply": {
        "name": "Hours of Supply",
        "unit": "hours/day",
        "target": 20,
        "warning": 16,
        "critical": 12,
        "weight": 15
    },
    "metering_ratio": {
        "name": "Metering Ratio",
        "unit": "%",
        "target": 90,
        "warning": 70,
        "critical": 50,
        "weight": 10
    },
    "collection_efficiency": {
        "name": "Collection Efficiency",
        "unit": "%",
        "target": 85,
        "warning": 70,
        "critical": 55,
        "weight": 15
    },
    "staff_per_1000_connections": {
        "name": "Staff per 1000 Connections",
        "unit": "ratio",
        "target": 5,
        "warning": 8,
        "critical": 12,
        "weight": 5
    },
    "coverage_rate": {
        "name": "Coverage Rate",
        "unit": "%",
        "target": 85,
        "warning": 70,
        "critical": 50,
        "weight": 10
    },
    "service_connection_rate": {
        "name": "Service Connection Rate",
        "unit": "%",
        "target": 80,
        "warning": 60,
        "critical": 40,
        "weight": 10
    }
}

# DWS Requirements (South Africa)
DWS_REQUIREMENTS = {
    "blue_drop": {
        "name": "Blue Drop Certification",
        "description": "Drinking water quality management",
        "minimum_score": 95,
        "categories": [
            "Water Safety Planning",
            "Process Control",
            "Water Quality Monitoring",
            "Management Commitment",
            "Asset Management"
        ]
    },
    "green_drop": {
        "name": "Green Drop Certification",
        "description": "Wastewater quality management",
        "minimum_score": 90,
        "categories": [
            "Effluent Quality",
            "Process Control",
            "Skills Management",
            "Capacity Management",
            "Compliance Monitoring"
        ]
    },
    "no_drop": {
        "name": "No Drop Certification",
        "description": "Water use efficiency",
        "minimum_score": 90,
        "categories": [
            "Water Losses",
            "Water Use Efficiency",
            "Water Demand Management",
            "Resource Protection"
        ]
    }
}

# Water Quality Standards (SANS 241:2015 / Zambian Standards)
WATER_QUALITY_STANDARDS = {
    "ph": {"min": 5.0, "max": 9.7, "unit": "", "test_frequency": "daily"},
    "turbidity": {"min": 0, "max": 1, "unit": "NTU", "test_frequency": "daily"},
    "chlorine_residual": {"min": 0.2, "max": 5, "unit": "mg/L", "test_frequency": "daily"},
    "e_coli": {"min": 0, "max": 0, "unit": "CFU/100mL", "test_frequency": "weekly"},
    "total_coliform": {"min": 0, "max": 10, "unit": "CFU/100mL", "test_frequency": "weekly"},
    "conductivity": {"min": 0, "max": 1700, "unit": "µS/cm", "test_frequency": "weekly"},
    "nitrate": {"min": 0, "max": 11, "unit": "mg/L as N", "test_frequency": "monthly"},
    "fluoride": {"min": 0, "max": 1.5, "unit": "mg/L", "test_frequency": "monthly"},
    "iron": {"min": 0, "max": 0.3, "unit": "mg/L", "test_frequency": "monthly"},
    "manganese": {"min": 0, "max": 0.1, "unit": "mg/L", "test_frequency": "monthly"}
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"
    PENDING = "pending"


class ReportType(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    INCIDENT = "incident"
    AUDIT = "audit"


class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class KPIRecord:
    """KPI measurement record."""
    kpi_id: str
    kpi_name: str
    value: float
    unit: str
    target: float
    status: ComplianceStatus
    period: str
    zone_id: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""


@dataclass
class ComplianceReport:
    """Regulatory compliance report."""
    report_id: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    regulatory_body: str  # NWASCO, DWS, etc.
    
    # Content
    kpis: List[KPIRecord] = field(default_factory=list)
    overall_score: float = 0.0
    overall_status: ComplianceStatus = ComplianceStatus.PENDING
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None
    submitted_by: str = ""
    
    # Audit
    document_hash: str = ""
    version: int = 1


@dataclass
class Incident:
    """Regulatory incident record."""
    incident_id: str
    incident_type: str  # leak, contamination, service_interruption, etc.
    severity: IncidentSeverity
    zone_id: str
    
    # Details
    description: str
    location: Optional[Dict] = None  # lat, lng
    affected_customers: int = 0
    volume_lost_m3: float = 0.0
    
    # Timeline
    reported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Response
    response_time_minutes: int = 0
    resolution_time_hours: float = 0.0
    root_cause: str = ""
    corrective_actions: List[str] = field(default_factory=list)
    
    # Regulatory
    reported_to_regulator: bool = False
    regulator_reference: str = ""


@dataclass
class AuditEntry:
    """Audit trail entry."""
    audit_id: str
    timestamp: datetime
    action: str
    entity_type: str
    entity_id: str
    user_id: str
    user_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: str = ""
    details: str = ""


@dataclass
class License:
    """Permit/license record."""
    license_id: str
    license_type: str  # water_abstraction, effluent_discharge, etc.
    license_number: str
    issued_by: str
    
    # Validity
    issue_date: datetime
    expiry_date: datetime
    renewal_required: bool = True
    
    # Conditions
    conditions: List[str] = field(default_factory=list)
    abstraction_limit_m3_day: float = 0.0
    
    # Status
    active: bool = True


# =============================================================================
# COMPLIANCE SERVICE
# =============================================================================

class ComplianceService:
    """
    Regulatory compliance management for water utilities.
    
    Supports:
    - NWASCO (Zambia)
    - DWS (South Africa)
    - WARMA (Zambia)
    """
    
    def __init__(self, country: str = "zambia", utility_name: str = ""):
        self.country = country.lower()
        self.utility_name = utility_name
        
        # Get country-specific standards
        if self.country == "zambia":
            self.kpi_standards = NWASCO_KPIS
            self.regulatory_body = "NWASCO"
        else:  # South Africa
            self.kpi_standards = self._convert_dws_to_kpis()
            self.regulatory_body = "DWS"
        
        # Data stores
        self.kpi_records: Dict[str, List[KPIRecord]] = {}
        self.reports: Dict[str, ComplianceReport] = {}
        self.incidents: Dict[str, Incident] = {}
        self.audit_trail: List[AuditEntry] = []
        self.licenses: Dict[str, License] = {}
        
        # Water quality tests
        self.water_quality_tests: List[Dict] = []
        
        logger.info(f"ComplianceService initialized for {country} - {self.regulatory_body}")
    
    def _convert_dws_to_kpis(self) -> Dict:
        """Convert DWS requirements to KPI format."""
        return {
            "blue_drop_score": {
                "name": "Blue Drop Score",
                "unit": "%",
                "target": 95,
                "warning": 80,
                "critical": 60,
                "weight": 35
            },
            "green_drop_score": {
                "name": "Green Drop Score",
                "unit": "%",
                "target": 90,
                "warning": 70,
                "critical": 50,
                "weight": 25
            },
            "no_drop_score": {
                "name": "No Drop Score",
                "unit": "%",
                "target": 90,
                "warning": 75,
                "critical": 60,
                "weight": 25
            },
            "nrw_percent": {
                "name": "Non-Revenue Water",
                "unit": "%",
                "target": 20,
                "warning": 30,
                "critical": 40,
                "weight": 15
            }
        }
    
    def _add_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str = "system",
        user_name: str = "System",
        old_value: str = None,
        new_value: str = None,
        details: str = ""
    ):
        """Add audit trail entry."""
        entry = AuditEntry(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_name=user_name,
            old_value=old_value,
            new_value=new_value,
            details=details
        )
        self.audit_trail.append(entry)
    
    # =========================================================================
    # KPI MANAGEMENT
    # =========================================================================
    
    def record_kpi(
        self,
        kpi_id: str,
        value: float,
        zone_id: str,
        period: str,
        notes: str = "",
        user_id: str = "system"
    ) -> KPIRecord:
        """Record a KPI measurement."""
        if kpi_id not in self.kpi_standards:
            raise ValueError(f"Unknown KPI: {kpi_id}")
        
        standard = self.kpi_standards[kpi_id]
        
        # Determine status
        if kpi_id == "staff_per_1000_connections":
            # Lower is better
            if value <= standard["target"]:
                status = ComplianceStatus.COMPLIANT
            elif value <= standard["warning"]:
                status = ComplianceStatus.WARNING
            elif value <= standard["critical"]:
                status = ComplianceStatus.NON_COMPLIANT
            else:
                status = ComplianceStatus.CRITICAL
        elif kpi_id == "nrw_percent":
            # Lower is better
            if value <= standard["target"]:
                status = ComplianceStatus.COMPLIANT
            elif value <= standard["warning"]:
                status = ComplianceStatus.WARNING
            elif value <= standard["critical"]:
                status = ComplianceStatus.NON_COMPLIANT
            else:
                status = ComplianceStatus.CRITICAL
        else:
            # Higher is better
            if value >= standard["target"]:
                status = ComplianceStatus.COMPLIANT
            elif value >= standard["warning"]:
                status = ComplianceStatus.WARNING
            elif value >= standard["critical"]:
                status = ComplianceStatus.NON_COMPLIANT
            else:
                status = ComplianceStatus.CRITICAL
        
        record = KPIRecord(
            kpi_id=kpi_id,
            kpi_name=standard["name"],
            value=value,
            unit=standard["unit"],
            target=standard["target"],
            status=status,
            period=period,
            zone_id=zone_id,
            notes=notes
        )
        
        # Store
        key = f"{kpi_id}_{zone_id}"
        if key not in self.kpi_records:
            self.kpi_records[key] = []
        self.kpi_records[key].append(record)
        
        # Audit
        self._add_audit(
            action="KPI_RECORDED",
            entity_type="kpi",
            entity_id=kpi_id,
            user_id=user_id,
            new_value=str(value),
            details=f"Zone: {zone_id}, Period: {period}, Status: {status.value}"
        )
        
        return record
    
    def get_kpi_trend(self, kpi_id: str, zone_id: str, periods: int = 12) -> List[Dict]:
        """Get KPI trend over time."""
        key = f"{kpi_id}_{zone_id}"
        records = self.kpi_records.get(key, [])
        
        # Sort by period and get recent
        records.sort(key=lambda x: x.period, reverse=True)
        records = records[:periods]
        records.reverse()
        
        return [
            {
                "period": r.period,
                "value": r.value,
                "target": r.target,
                "status": r.status.value,
                "variance": round(r.value - r.target, 2)
            }
            for r in records
        ]
    
    def get_zone_dashboard(self, zone_id: str) -> Dict:
        """Get compliance dashboard for a zone."""
        kpis = {}
        total_score = 0
        total_weight = 0
        
        for kpi_id, standard in self.kpi_standards.items():
            key = f"{kpi_id}_{zone_id}"
            records = self.kpi_records.get(key, [])
            
            if records:
                latest = max(records, key=lambda x: x.recorded_at)
                kpis[kpi_id] = {
                    "name": standard["name"],
                    "value": latest.value,
                    "unit": standard["unit"],
                    "target": standard["target"],
                    "status": latest.status.value,
                    "period": latest.period
                }
                
                # Calculate weighted score (0-100)
                if kpi_id in ["nrw_percent", "staff_per_1000_connections"]:
                    # Lower is better
                    score = max(0, 100 - (latest.value / standard["target"] - 1) * 50)
                else:
                    # Higher is better
                    score = min(100, (latest.value / standard["target"]) * 100)
                
                total_score += score * standard["weight"]
                total_weight += standard["weight"]
            else:
                kpis[kpi_id] = {
                    "name": standard["name"],
                    "value": None,
                    "status": "no_data"
                }
        
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine overall status
        if overall_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            overall_status = ComplianceStatus.WARNING
        elif overall_score >= 50:
            overall_status = ComplianceStatus.NON_COMPLIANT
        else:
            overall_status = ComplianceStatus.CRITICAL
        
        return {
            "zone_id": zone_id,
            "regulatory_body": self.regulatory_body,
            "overall_score": round(overall_score, 1),
            "overall_status": overall_status.value,
            "kpis": kpis,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    # =========================================================================
    # WATER QUALITY COMPLIANCE
    # =========================================================================
    
    def record_water_quality_test(
        self,
        zone_id: str,
        sample_point: str,
        results: Dict[str, float],
        sampled_at: datetime = None,
        lab_id: str = "",
        user_id: str = "system"
    ) -> Dict:
        """Record water quality test results."""
        if sampled_at is None:
            sampled_at = datetime.now(timezone.utc)
        
        test_record = {
            "test_id": str(uuid.uuid4()),
            "zone_id": zone_id,
            "sample_point": sample_point,
            "sampled_at": sampled_at.isoformat(),
            "lab_id": lab_id,
            "parameters": {},
            "compliant": True,
            "failures": []
        }
        
        for param, value in results.items():
            if param in WATER_QUALITY_STANDARDS:
                std = WATER_QUALITY_STANDARDS[param]
                compliant = std["min"] <= value <= std["max"]
                
                test_record["parameters"][param] = {
                    "value": value,
                    "unit": std["unit"],
                    "min": std["min"],
                    "max": std["max"],
                    "compliant": compliant
                }
                
                if not compliant:
                    test_record["compliant"] = False
                    test_record["failures"].append({
                        "parameter": param,
                        "value": value,
                        "limit": f"{std['min']} - {std['max']} {std['unit']}"
                    })
        
        self.water_quality_tests.append(test_record)
        
        # Audit
        self._add_audit(
            action="WATER_QUALITY_TEST",
            entity_type="water_quality",
            entity_id=test_record["test_id"],
            user_id=user_id,
            details=f"Zone: {zone_id}, Compliant: {test_record['compliant']}"
        )
        
        return test_record
    
    def get_water_quality_compliance(self, zone_id: str, days: int = 30) -> Dict:
        """Get water quality compliance summary."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        zone_tests = [
            t for t in self.water_quality_tests
            if t["zone_id"] == zone_id and 
            datetime.fromisoformat(t["sampled_at"]) > cutoff
        ]
        
        if not zone_tests:
            return {"error": "No tests found", "zone_id": zone_id}
        
        total_tests = len(zone_tests)
        compliant_tests = len([t for t in zone_tests if t["compliant"]])
        
        # Parameter-level compliance
        param_stats = {}
        for param in WATER_QUALITY_STANDARDS:
            values = [
                t["parameters"].get(param, {}).get("value")
                for t in zone_tests
                if param in t["parameters"]
            ]
            if values:
                valid_values = [v for v in values if v is not None]
                param_stats[param] = {
                    "tests": len(valid_values),
                    "min": min(valid_values),
                    "max": max(valid_values),
                    "avg": round(sum(valid_values) / len(valid_values), 3),
                    "compliant": len([
                        v for v in valid_values
                        if WATER_QUALITY_STANDARDS[param]["min"] <= v <= WATER_QUALITY_STANDARDS[param]["max"]
                    ])
                }
        
        return {
            "zone_id": zone_id,
            "period_days": days,
            "total_tests": total_tests,
            "compliant_tests": compliant_tests,
            "compliance_rate": round(compliant_tests / total_tests * 100, 1),
            "parameter_stats": param_stats
        }
    
    # =========================================================================
    # INCIDENT MANAGEMENT
    # =========================================================================
    
    def report_incident(
        self,
        incident_type: str,
        severity: str,
        zone_id: str,
        description: str,
        location: Dict = None,
        affected_customers: int = 0,
        volume_lost_m3: float = 0.0,
        detected_at: datetime = None,
        user_id: str = "system"
    ) -> Incident:
        """Report a regulatory incident."""
        incident = Incident(
            incident_id=f"INC_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            incident_type=incident_type,
            severity=IncidentSeverity[severity.upper()],
            zone_id=zone_id,
            description=description,
            location=location,
            affected_customers=affected_customers,
            volume_lost_m3=volume_lost_m3,
            detected_at=detected_at
        )
        
        self.incidents[incident.incident_id] = incident
        
        # Audit
        self._add_audit(
            action="INCIDENT_REPORTED",
            entity_type="incident",
            entity_id=incident.incident_id,
            user_id=user_id,
            details=f"Type: {incident_type}, Severity: {severity}"
        )
        
        return incident
    
    def resolve_incident(
        self,
        incident_id: str,
        root_cause: str,
        corrective_actions: List[str],
        user_id: str = "system"
    ):
        """Resolve an incident."""
        if incident_id not in self.incidents:
            return None
        
        incident = self.incidents[incident_id]
        incident.resolved_at = datetime.now(timezone.utc)
        incident.root_cause = root_cause
        incident.corrective_actions = corrective_actions
        
        # Calculate resolution time
        if incident.detected_at:
            delta = incident.resolved_at - incident.detected_at
            incident.resolution_time_hours = delta.total_seconds() / 3600
        
        # Audit
        self._add_audit(
            action="INCIDENT_RESOLVED",
            entity_type="incident",
            entity_id=incident_id,
            user_id=user_id,
            details=f"Resolution time: {incident.resolution_time_hours:.1f} hours"
        )
        
        return incident
    
    def get_incident_summary(self, days: int = 30) -> Dict:
        """Get incident summary."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        recent = [
            i for i in self.incidents.values()
            if i.reported_at > cutoff
        ]
        
        by_severity = {}
        for severity in IncidentSeverity:
            by_severity[severity.value] = len([
                i for i in recent if i.severity == severity
            ])
        
        by_type = {}
        for i in recent:
            by_type[i.incident_type] = by_type.get(i.incident_type, 0) + 1
        
        resolved = [i for i in recent if i.resolved_at]
        avg_resolution = 0
        if resolved:
            avg_resolution = sum(i.resolution_time_hours for i in resolved) / len(resolved)
        
        return {
            "period_days": days,
            "total_incidents": len(recent),
            "open_incidents": len([i for i in recent if not i.resolved_at]),
            "resolved_incidents": len(resolved),
            "by_severity": by_severity,
            "by_type": by_type,
            "avg_resolution_hours": round(avg_resolution, 1),
            "total_volume_lost_m3": sum(i.volume_lost_m3 for i in recent),
            "total_affected_customers": sum(i.affected_customers for i in recent)
        }
    
    # =========================================================================
    # COMPLIANCE REPORTING
    # =========================================================================
    
    def generate_monthly_report(
        self,
        year: int,
        month: int,
        zones: List[str],
        user_id: str = "system"
    ) -> ComplianceReport:
        """Generate monthly compliance report."""
        period_start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            period_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        report = ComplianceReport(
            report_id=f"RPT_{year}{month:02d}_{uuid.uuid4().hex[:8]}",
            report_type=ReportType.MONTHLY,
            period_start=period_start,
            period_end=period_end,
            regulatory_body=self.regulatory_body
        )
        
        period = f"{year}-{month:02d}"
        total_score = 0
        total_weight = 0
        
        # Collect KPIs for all zones
        for zone_id in zones:
            for kpi_id, standard in self.kpi_standards.items():
                key = f"{kpi_id}_{zone_id}"
                records = [
                    r for r in self.kpi_records.get(key, [])
                    if r.period == period
                ]
                
                if records:
                    report.kpis.append(records[-1])
                    
                    # Calculate score
                    latest = records[-1]
                    if kpi_id in ["nrw_percent", "staff_per_1000_connections"]:
                        score = max(0, 100 - (latest.value / standard["target"] - 1) * 50)
                    else:
                        score = min(100, (latest.value / standard["target"]) * 100)
                    
                    total_score += score * standard["weight"]
                    total_weight += standard["weight"]
        
        # Calculate overall
        if total_weight > 0:
            report.overall_score = total_score / total_weight
            
            if report.overall_score >= 90:
                report.overall_status = ComplianceStatus.COMPLIANT
            elif report.overall_score >= 70:
                report.overall_status = ComplianceStatus.WARNING
            elif report.overall_score >= 50:
                report.overall_status = ComplianceStatus.NON_COMPLIANT
            else:
                report.overall_status = ComplianceStatus.CRITICAL
        
        # Generate document hash for integrity
        content = json.dumps({
            "report_id": report.report_id,
            "period": period,
            "score": report.overall_score,
            "status": report.overall_status.value
        }, sort_keys=True)
        report.document_hash = hashlib.sha256(content.encode()).hexdigest()
        
        self.reports[report.report_id] = report
        
        # Audit
        self._add_audit(
            action="REPORT_GENERATED",
            entity_type="report",
            entity_id=report.report_id,
            user_id=user_id,
            details=f"Period: {period}, Score: {report.overall_score:.1f}"
        )
        
        return report
    
    def submit_report(self, report_id: str, user_id: str, user_name: str):
        """Mark report as submitted to regulator."""
        if report_id not in self.reports:
            return None
        
        report = self.reports[report_id]
        report.submitted_at = datetime.now(timezone.utc)
        report.submitted_by = user_name
        
        self._add_audit(
            action="REPORT_SUBMITTED",
            entity_type="report",
            entity_id=report_id,
            user_id=user_id,
            user_name=user_name,
            details=f"Submitted to {report.regulatory_body}"
        )
        
        return report
    
    def export_nwasco_format(self, report_id: str) -> Dict:
        """Export report in NWASCO format."""
        if report_id not in self.reports:
            return {"error": "Report not found"}
        
        report = self.reports[report_id]
        
        # NWASCO template format
        return {
            "utility_name": self.utility_name,
            "reporting_period": f"{report.period_start.strftime('%B %Y')}",
            "submission_date": datetime.now().strftime("%Y-%m-%d"),
            
            "performance_indicators": {
                kpi.kpi_id: {
                    "indicator": kpi.kpi_name,
                    "value": kpi.value,
                    "unit": kpi.unit,
                    "target": kpi.target,
                    "status": kpi.status.value
                }
                for kpi in report.kpis
            },
            
            "overall_performance": {
                "score": round(report.overall_score, 1),
                "status": report.overall_status.value,
                "document_hash": report.document_hash
            },
            
            "certification": {
                "prepared_by": "",
                "reviewed_by": "",
                "approved_by": "",
                "date": ""
            }
        }
    
    # =========================================================================
    # LICENSE MANAGEMENT
    # =========================================================================
    
    def add_license(self, license: License):
        """Add a permit/license."""
        self.licenses[license.license_id] = license
        
        self._add_audit(
            action="LICENSE_ADDED",
            entity_type="license",
            entity_id=license.license_id,
            details=f"Type: {license.license_type}, Expires: {license.expiry_date.strftime('%Y-%m-%d')}"
        )
    
    def get_expiring_licenses(self, days: int = 90) -> List[License]:
        """Get licenses expiring within specified days."""
        cutoff = datetime.now(timezone.utc) + timedelta(days=days)
        
        return [
            lic for lic in self.licenses.values()
            if lic.active and lic.expiry_date <= cutoff
        ]
    
    def get_license_summary(self) -> Dict:
        """Get license summary."""
        active = [l for l in self.licenses.values() if l.active]
        
        return {
            "total_licenses": len(self.licenses),
            "active_licenses": len(active),
            "expiring_30_days": len(self.get_expiring_licenses(30)),
            "expiring_90_days": len(self.get_expiring_licenses(90)),
            "by_type": {
                l.license_type: len([x for x in active if x.license_type == l.license_type])
                for l in active
            }
        }
    
    # =========================================================================
    # AUDIT TRAIL
    # =========================================================================
    
    def get_audit_trail(
        self,
        entity_type: str = None,
        entity_id: str = None,
        user_id: str = None,
        days: int = 30
    ) -> List[Dict]:
        """Get audit trail entries."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        entries = self.audit_trail
        
        if entity_type:
            entries = [e for e in entries if e.entity_type == entity_type]
        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        
        entries = [e for e in entries if e.timestamp > cutoff]
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "audit_id": e.audit_id,
                "timestamp": e.timestamp.isoformat(),
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "user": e.user_name,
                "details": e.details
            }
            for e in entries[:100]  # Limit to 100
        ]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize for Zambia (NWASCO)
    service = ComplianceService(
        country="zambia",
        utility_name="Lusaka Water Supply and Sanitation Company"
    )
    
    # Record KPIs for December 2024
    period = "2024-12"
    zone = "ZONE_KAB"
    
    service.record_kpi("nrw_percent", 38.5, zone, period)
    service.record_kpi("water_quality_compliance", 92.0, zone, period)
    service.record_kpi("hours_of_supply", 18, zone, period)
    service.record_kpi("metering_ratio", 75.0, zone, period)
    service.record_kpi("collection_efficiency", 72.0, zone, period)
    service.record_kpi("staff_per_1000_connections", 7, zone, period)
    service.record_kpi("coverage_rate", 78.0, zone, period)
    service.record_kpi("service_connection_rate", 65.0, zone, period)
    
    print("Zone Dashboard:")
    dashboard = service.get_zone_dashboard(zone)
    print(json.dumps(dashboard, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Record water quality test
    test = service.record_water_quality_test(
        zone_id=zone,
        sample_point="Treatment Plant Outlet",
        results={
            "ph": 7.2,
            "turbidity": 0.5,
            "chlorine_residual": 0.8,
            "e_coli": 0,
            "conductivity": 450
        }
    )
    print("Water Quality Test:")
    print(json.dumps(test, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Report incident
    incident = service.report_incident(
        incident_type="pipe_burst",
        severity="high",
        zone_id=zone,
        description="Major pipe burst on Cairo Road affecting 500 households",
        location={"lat": -15.4167, "lng": 28.2833},
        affected_customers=500,
        volume_lost_m3=250.0,
        detected_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    print("Incident Reported:")
    print(f"  ID: {incident.incident_id}")
    print(f"  Type: {incident.incident_type}")
    print(f"  Severity: {incident.severity.value}")
    
    # Resolve incident
    service.resolve_incident(
        incident.incident_id,
        root_cause="Aging infrastructure - 50 year old asbestos cement pipe",
        corrective_actions=[
            "Replaced 50m section with HDPE",
            "Scheduled inspection of adjacent sections",
            "Added zone to priority replacement program"
        ]
    )
    print("  Status: Resolved")
    
    print("\n" + "="*50 + "\n")
    
    # Generate monthly report
    report = service.generate_monthly_report(
        year=2024,
        month=12,
        zones=[zone]
    )
    print("Monthly Report Generated:")
    print(f"  Report ID: {report.report_id}")
    print(f"  Overall Score: {report.overall_score:.1f}")
    print(f"  Status: {report.overall_status.value}")
    print(f"  Document Hash: {report.document_hash[:16]}...")
    
    print("\n" + "="*50 + "\n")
    
    # Export NWASCO format
    nwasco = service.export_nwasco_format(report.report_id)
    print("NWASCO Export:")
    print(json.dumps(nwasco, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Audit trail
    print("Recent Audit Trail:")
    audit = service.get_audit_trail(days=7)
    for entry in audit[:5]:
        print(f"  {entry['timestamp'][:19]} | {entry['action']} | {entry['entity_type']} | {entry['details']}")
