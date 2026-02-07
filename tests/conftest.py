"""Shared test fixtures for AquaWatch NRW test suite."""

import pytest


@pytest.fixture
def sample_pressure_data():
    """Sample pressure readings for testing."""
    return [
        {"sensor_id": "sensor-001", "pressure": 3.2, "timestamp": "2024-01-01T00:00:00Z"},
        {"sensor_id": "sensor-001", "pressure": 3.1, "timestamp": "2024-01-01T00:05:00Z"},
        {"sensor_id": "sensor-001", "pressure": 3.15, "timestamp": "2024-01-01T00:10:00Z"},
    ]


@pytest.fixture
def sample_anomaly_reading():
    """Sample anomalous pressure reading (sudden drop)."""
    return {
        "sensor_id": "sensor-001",
        "pressure": 1.5,
        "timestamp": "2024-01-01T00:15:00Z",
    }
