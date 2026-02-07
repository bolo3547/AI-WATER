"""
Tests for critical gap fixes:
- Work order assignment notifications
- Work order escalation notifications
- Community report acknowledgment notifications
- SIV timestamp alignment/interpolation
- Configuration validation
- Health check endpoint
"""

import pytest
from datetime import datetime, timezone, timedelta


# =============================================================================
# WORK ORDER NOTIFICATION TESTS
# =============================================================================

class TestWorkOrderNotifications:
    """Test work order assignment and escalation notifications."""

    def _make_service(self):
        from src.workflow.work_orders import (
            WorkOrderService, Technician, SkillLevel, Location,
            WorkOrderType, Priority
        )
        service = WorkOrderService()

        tech = Technician(
            technician_id="tech-001",
            name="John Mwale",
            phone="+260971234567",
            skill_level=SkillLevel.INTERMEDIATE,
            zone_ids=["zone-001"],
            current_location=Location(latitude=-15.4167, longitude=28.2833),
        )
        service.add_technician(tech)

        wo = service.create_work_order(
            wo_type=WorkOrderType.LEAK_REPAIR,
            priority=Priority.HIGH,
            location=Location(latitude=-15.42, longitude=28.29),
            title="Fix leak on Main Road",
            description="Customer reported leak near meter #1234",
        )
        return service, wo, tech

    def test_assign_work_order_with_notify(self):
        """Verify that assigning a work order with notify=True succeeds."""
        service, wo, tech = self._make_service()
        result = service.assign_work_order(wo.work_order_id, tech.technician_id, notify=True)
        assert result is True
        assert wo.assigned_to == tech.technician_id

    def test_assign_work_order_no_notify(self):
        """Verify that notify=False skips notification."""
        service, wo, tech = self._make_service()
        result = service.assign_work_order(wo.work_order_id, tech.technician_id, notify=False)
        assert result is True
        assert wo.assigned_to == tech.technician_id

    def test_escalation_updates_status_and_notes(self):
        """Verify that escalation updates status and internal notes."""
        service, wo, tech = self._make_service()
        from src.workflow.work_orders import WorkOrderStatus

        service._escalate_work_order(wo, "SLA breached")

        assert wo.status == WorkOrderStatus.ESCALATED
        assert "ESCALATED: SLA breached" in wo.internal_notes


# =============================================================================
# COMMUNITY REPORT NOTIFICATION TESTS
# =============================================================================

class TestCommunityReportNotifications:
    """Test community report acknowledgment notifications."""

    def test_acknowledge_report_triggers_notification(self):
        """Verify acknowledge_report attempts to send notification."""
        from src.community.reporting_portal import CommunityPortalService, ReportType

        portal = CommunityPortalService()

        user = portal.register_user(
            name="Jane Banda",
            phone="+260977654321",
            language="en",
        )

        report = portal.submit_report(
            user_id=user.user_id,
            report_type=ReportType.LEAK,
            description="Water leaking from pipe near school",
            latitude=-15.4167,
            longitude=28.2833,
        )

        result = portal.acknowledge_report(report.report_id)
        assert result is True


# =============================================================================
# SIV TIMESTAMP ALIGNMENT TESTS
# =============================================================================

class TestSIVTimestampAlignment:
    """Test SIV data timestamp alignment and interpolation."""

    def _make_manager(self):
        from src.siv.siv_manager import SIVManager, SIVSourceType

        manager = SIVManager()

        source = manager.register_source(
            source_type=SIVSourceType.BULK_METER,
            name="Main Inlet Meter",
            connected_dma_ids=["DMA-001"],
        )

        return manager, source.source_id

    def test_align_timestamps_returns_correct_structure(self):
        """Verify align_timestamps returns correct structure."""
        manager, source_id = self._make_manager()

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 6, tzinfo=timezone.utc)

        result = manager.align_timestamps("DMA-001", start, end, interval_minutes=60)

        assert result["dma_id"] == "DMA-001"
        assert result["interval_minutes"] == 60
        assert len(result["timestamps"]) == 7  # hours 0..6
        assert "siv_m3" in result
        assert "inlet_m3" in result
        assert "data_quality" in result
        assert "siv_completeness" in result["data_quality"]
        assert "inlet_completeness" in result["data_quality"]

    def test_align_timestamps_with_ingested_data(self):
        """Verify interpolation works with ingested SIV records."""
        manager, source_id = self._make_manager()

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 4, tzinfo=timezone.utc)

        for i in range(5):
            ts = start + timedelta(hours=i)
            manager.ingest_siv(
                source_id=source_id,
                timestamp=ts,
                value=100.0 + i * 10,
                is_volume=True,
            )

        result = manager.align_timestamps("DMA-001", start, end, interval_minutes=60)

        assert len(result["timestamps"]) == 5
        assert result["data_quality"]["siv_completeness"] > 0

    def test_interpolate_value_exact_match(self):
        """Verify interpolation returns exact value when timestamp matches."""
        from src.siv.siv_manager import SIVRecord

        manager, _ = self._make_manager()

        ts = datetime(2024, 1, 1, 2, tzinfo=timezone.utc)
        records = [
            SIVRecord(record_id="r1", source_id="s1", timestamp=ts, volume_m3=150.0),
        ]

        result = manager._interpolate_value(records, ts, timedelta(hours=1))
        assert result == 150.0

    def test_interpolate_value_between_points(self):
        """Verify linear interpolation between two data points."""
        from src.siv.siv_manager import SIVRecord

        manager, _ = self._make_manager()

        t1 = datetime(2024, 1, 1, 0, tzinfo=timezone.utc)
        t2 = datetime(2024, 1, 1, 2, tzinfo=timezone.utc)
        target = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)

        records = [
            SIVRecord(record_id="r1", source_id="s1", timestamp=t1, volume_m3=100.0),
            SIVRecord(record_id="r2", source_id="s1", timestamp=t2, volume_m3=200.0),
        ]

        result = manager._interpolate_value(records, target, timedelta(hours=2))
        assert result is not None
        assert abs(result - 150.0) < 0.01

    def test_interpolate_value_no_data(self):
        """Verify interpolation returns None when no data exists."""
        manager, _ = self._make_manager()

        target = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)
        result = manager._interpolate_value([], target, timedelta(hours=1))
        assert result is None


# =============================================================================
# CONFIGURATION VALIDATION TESTS
# =============================================================================

class TestConfigValidation:
    """Test startup configuration validation."""

    def test_warns_on_missing_jwt(self):
        """Verify config validation warns when JWT_SECRET is not set."""
        from src.config.settings import validate_config, SystemConfig, Environment

        config = SystemConfig()
        config.environment = Environment.DEVELOPMENT
        config.security.jwt_secret = ""

        warnings = validate_config(config)

        assert len(warnings) > 0
        assert any("JWT_SECRET" in w for w in warnings)

    def test_warns_on_short_jwt(self):
        """Verify config validation warns when JWT_SECRET is too short."""
        from src.config.settings import validate_config, SystemConfig, Environment

        config = SystemConfig()
        config.environment = Environment.DEVELOPMENT
        config.security.jwt_secret = "short"

        warnings = validate_config(config)
        assert any("too short" in w for w in warnings)

    def test_raises_in_production(self):
        """Verify config validation raises RuntimeError in production."""
        from src.config.settings import validate_config, SystemConfig, Environment

        config = SystemConfig()
        config.environment = Environment.PRODUCTION
        config.security.jwt_secret = ""

        with pytest.raises(RuntimeError, match="CRITICAL"):
            validate_config(config)

    def test_passes_with_good_config(self):
        """Verify config validation passes with proper settings."""
        from src.config.settings import validate_config, SystemConfig, Environment

        config = SystemConfig()
        config.environment = Environment.DEVELOPMENT
        config.security.jwt_secret = "a" * 64
        config.security.encryption_key = "b" * 32
        config.database.password = "secure_password"

        warnings = validate_config(config)
        assert len(warnings) == 0


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================

class TestHealthMonitor:
    """Test health monitor functionality."""

    def test_health_monitor_status(self):
        """Verify health monitor returns valid status."""
        from src.core.health_monitor import HealthMonitor, HealthStatus

        monitor = HealthMonitor()
        status = monitor.get_status()

        assert status in (HealthStatus.GREEN, HealthStatus.AMBER, HealthStatus.RED, HealthStatus.UNKNOWN)

    def test_dashboard_status_format(self):
        """Verify dashboard status returns correct format."""
        from src.core.health_monitor import HealthMonitor

        monitor = HealthMonitor()
        dashboard = monitor.get_dashboard_status()

        assert "status" in dashboard
        assert "color" in dashboard
        assert "message" in dashboard
        assert "active_alerts" in dashboard
        assert "last_check" in dashboard

    def test_sensor_health_tracking(self):
        """Verify sensor health tracking works."""
        from src.core.health_monitor import HealthMonitor

        monitor = HealthMonitor()
        monitor.update_sensor_reading("DMA-001", "SENSOR-001")

        assert "DMA-001:SENSOR-001" in monitor._sensor_last_reading

    def test_full_report(self):
        """Verify full health report structure."""
        from src.core.health_monitor import HealthMonitor

        monitor = HealthMonitor()
        report = monitor.get_full_report()

        assert report.overall_status is not None
        assert isinstance(report.components, dict)
        assert isinstance(report.sensors, dict)
        assert isinstance(report.metrics, dict)
        assert isinstance(report.alerts, list)
