"""
Tests for production readiness fixes:
- Hardcoded credentials removed
- Error handling middleware added
- Lifecycle events configured
- Demo data generation works
- Config validation at startup
"""

import json
import os
import pytest
from datetime import datetime, timezone


# =============================================================================
# HARDCODED CREDENTIALS TESTS
# =============================================================================

class TestNoHardcodedSecrets:
    """Verify no hardcoded passwords remain in production code."""

    def test_database_handler_uses_env_vars(self):
        """DatabaseConfig should read from environment, not hardcode passwords."""
        from src.iot.database_handler import DatabaseConfig

        config = DatabaseConfig()
        # Password should come from env var, default to empty string (not a hardcoded password)
        assert config.password != "aquawatch_secure_password"
        assert config.password != "password"

    def test_auth_demo_uses_env_var(self):
        """Auth demo code should use os.getenv, not hardcoded secret."""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "security", "auth.py"
        )
        with open(source_path) as f:
            content = f.read()
        # Should import os and use os.getenv for JWT secret
        assert "import os" in content
        assert 'os.getenv("JWT_SECRET"' in content

    def test_cloud_auth_admin_uses_env_var(self):
        """Cloud auth should read admin password from env."""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "cloud", "auth.py"
        )
        with open(source_path) as f:
            content = f.read()
        # Should use os.getenv, not a raw hardcoded value
        assert 'os.getenv("ADMIN_PASSWORD"' in content


# =============================================================================
# ERROR HANDLING MIDDLEWARE TESTS
# =============================================================================

class TestErrorHandling:
    """Verify error handling middleware is configured."""

    def test_cloud_api_has_exception_handlers(self):
        """Cloud API should have exception handlers."""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "cloud", "api.py"
        )
        with open(source_path) as f:
            content = f.read()
        assert "exception_handler" in content
        assert "http_exception_handler" in content
        assert "general_exception_handler" in content

    def test_cloud_api_has_lifecycle_events(self):
        """Cloud API should have lifespan lifecycle management."""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "cloud", "api.py"
        )
        with open(source_path) as f:
            content = f.read()
        assert "lifespan" in content
        assert "asynccontextmanager" in content


# =============================================================================
# DEMO DATA SEEDING TESTS
# =============================================================================

class TestDemoDataSeeding:
    """Verify demo data generation works correctly."""

    def test_generate_demo_data_structure(self):
        """Generated demo data should have correct structure."""
        from scripts.seed_demo_data import generate_demo_data

        data = generate_demo_data()

        assert "dmas" in data
        assert "sensors" in data
        assert "alerts" in data
        assert "work_orders" in data
        assert "community_reports" in data
        assert "nrw_summary" in data

    def test_demo_data_has_correct_counts(self):
        """Demo data should have expected number of entities."""
        from scripts.seed_demo_data import generate_demo_data

        data = generate_demo_data()

        assert len(data["dmas"]) == 2
        assert len(data["sensors"]) == 12  # 6 per DMA
        assert len(data["alerts"]) == 3
        assert len(data["work_orders"]) == 2
        assert len(data["community_reports"]) == 1

    def test_demo_data_zambian_locations(self):
        """Demo data DMAs should have valid Zambian coordinates."""
        from scripts.seed_demo_data import generate_demo_data

        data = generate_demo_data()

        for dma in data["dmas"]:
            # Lusaka, Zambia coordinates
            assert -16 < dma["latitude"] < -15
            assert 28 < dma["longitude"] < 29

    def test_nrw_summary_values(self):
        """NRW summary should have realistic values."""
        from scripts.seed_demo_data import generate_demo_data

        data = generate_demo_data()
        nrw = data["nrw_summary"]

        assert 0 < nrw["nrw_percent"] <= 100
        assert nrw["system_input_volume_m3"] > 0
        assert nrw["real_losses_m3"] > 0
        assert nrw["infrastructure_leakage_index"] > 0

    def test_sensor_readings_generation(self):
        """Sensor readings should be generated correctly."""
        from scripts.seed_demo_data import generate_sensor_readings

        now = datetime.now(timezone.utc)
        readings = generate_sensor_readings("TEST-001", "pressure", now, hours=1)

        # 1 hour at 15-min intervals = 4 readings
        assert len(readings) == 4
        for r in readings:
            assert r["sensor_id"] == "TEST-001"
            assert r["value"] > 0
            assert r["unit"] == "bar"
            assert 0 <= r["quality_score"] <= 100

    def test_demo_data_serializable(self):
        """Demo data should be JSON serializable."""
        from scripts.seed_demo_data import generate_demo_data

        data = generate_demo_data()
        # Should not raise
        json_str = json.dumps(data, default=str)
        assert len(json_str) > 0
