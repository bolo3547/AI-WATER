"""
ESP32 IoT Connectivity Layer

Handles communication between ESP32 edge devices and the AquaWatch cloud platform.
"""

from .esp32_connector import (
    MQTTConfig,
    ESP32Config,
    SensorType,
    DataQuality,
    SensorReading,
    DeviceStatus,
    MQTTIngestionService,
    ESP32DataIngestionService
)

from .database_handler import (
    DatabaseConfig,
    TimescaleDBHandler,
    ESP32DatabaseIntegration
)

__all__ = [
    # Configuration
    'MQTTConfig',
    'ESP32Config',
    'DatabaseConfig',
    
    # Data Models
    'SensorType',
    'DataQuality', 
    'SensorReading',
    'DeviceStatus',
    
    # Services
    'MQTTIngestionService',
    'ESP32DataIngestionService',
    'TimescaleDBHandler',
    'ESP32DatabaseIntegration'
]
