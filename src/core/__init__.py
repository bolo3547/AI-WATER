"""
AQUAWATCH NRW - CORE MODULE
===========================

Central orchestration layer for the AquaWatch NRW Detection System.

This module provides:
- Feature Store: Single source of truth for all processed features
- Event Bus: Event-driven architecture for loose coupling
- System Orchestrator: Continuous AI execution loop
- Health Monitor: System health checks and fail-safes
- System Runner: Main entry point that wires everything together

Usage:
    from src.core import (
        # Feature Store
        get_feature_store,
        FeatureStore,
        FeatureVector,
        
        # Event Bus
        get_event_bus,
        EventType,
        EventPriority,
        publish,
        subscribe,
        
        # Orchestrator
        get_orchestrator,
        SystemOrchestrator,
        PipelineStage,
        
        # Health Monitor
        get_health_monitor,
        HealthStatus,
        get_system_status,
        get_dashboard_health,
        
        # System Runner
        get_system_runner,
        SystemRunner
    )
    
    # Start the system
    runner = get_system_runner()
    runner.run_forever()

Author: AquaWatch AI Team
Version: 1.0.0
"""

# Feature Store
from src.core.feature_store import (
    FeatureStore,
    FeatureVector,
    FeatureRecord,
    FeatureStoreConfig,
    get_feature_store
)

# Event Bus
from src.core.event_bus import (
    EventBus,
    Event,
    EventType,
    EventPriority,
    EventSubscription,
    get_event_bus,
    publish,
    subscribe,
    start_event_bus,
    stop_event_bus,
    emit_sensor_data_received,
    emit_anomaly_detected,
    emit_alert_created,
    emit_leak_confirmed,
    emit_drift_detected
)

# System Orchestrator
from src.core.orchestrator import (
    SystemOrchestrator,
    PipelineStage,
    StageResult,
    CycleResult,
    OrchestratorConfig,
    get_orchestrator
)

# Health Monitor
from src.core.health_monitor import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    ComponentType,
    ComponentHealth,
    SensorHealth,
    SystemHealthReport,
    get_health_monitor,
    get_system_status,
    get_dashboard_health,
    update_sensor_health,
    start_health_monitor,
    stop_health_monitor
)

# System Runner
from src.core.system_runner import (
    SystemRunner,
    get_system_runner
)


# Expose version
__version__ = "1.0.0"

# All exports
__all__ = [
    # Feature Store
    'FeatureStore',
    'FeatureVector',
    'FeatureRecord',
    'FeatureStoreConfig',
    'get_feature_store',
    
    # Event Bus
    'EventBus',
    'Event',
    'EventType',
    'EventPriority',
    'EventSubscription',
    'get_event_bus',
    'publish',
    'subscribe',
    'start_event_bus',
    'stop_event_bus',
    'emit_sensor_data_received',
    'emit_anomaly_detected',
    'emit_alert_created',
    'emit_leak_confirmed',
    'emit_drift_detected',
    
    # Orchestrator
    'SystemOrchestrator',
    'PipelineStage',
    'StageResult',
    'CycleResult',
    'OrchestratorConfig',
    'get_orchestrator',
    
    # Health Monitor
    'HealthMonitor',
    'HealthStatus',
    'HealthCheck',
    'ComponentType',
    'ComponentHealth',
    'SensorHealth',
    'SystemHealthReport',
    'get_health_monitor',
    'get_system_status',
    'get_dashboard_health',
    'update_sensor_health',
    'start_health_monitor',
    'stop_health_monitor',
    
    # System Runner
    'SystemRunner',
    'get_system_runner'
]
