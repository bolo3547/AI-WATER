"""
AQUAWATCH NRW - SYSTEM RUNNER
=============================

Main entry point that wires all components together.

This is the SINGLE script to start the entire system:
- Initializes all components in correct order
- Wires data flow: Sensors → Feature Store → AI → Decisions → Actions
- Starts continuous monitoring
- Handles graceful shutdown

Usage:
    python -m src.core.system_runner
    
Or import and call:
    from src.core.system_runner import SystemRunner
    runner = SystemRunner()
    runner.start()

Author: AquaWatch AI Team
Version: 1.0.0
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

# Core components
from src.core.feature_store import FeatureStore, get_feature_store
from src.core.orchestrator import SystemOrchestrator, get_orchestrator, OrchestratorConfig
from src.core.event_bus import (
    EventBus, get_event_bus, EventType, EventPriority,
    start_event_bus, stop_event_bus
)
from src.core.health_monitor import (
    HealthMonitor, get_health_monitor, HealthStatus,
    start_health_monitor, stop_health_monitor
)

# AI components
try:
    from src.ai.anomaly_detector import AnomalyDetectionEngine as AnomalyDetector
    from src.ai.leak_localizer import LeakLocalizer
    from src.ai.autonomous_system import AutonomousWaterSystem
except ImportError as e:
    logging.warning(f"AI components not available: {e}")
    AnomalyDetector = None
    LeakLocalizer = None
    AutonomousWaterSystem = None

# Enterprise/AI components (actual locations)
try:
    from src.ai.decision_engine import DecisionEngine
except ImportError as e:
    logging.warning(f"Decision Engine not available: {e}")
    DecisionEngine = None

try:
    from src.nrw.nrw_calculator import NRWCalculator
except ImportError as e:
    logging.warning(f"NRW Calculator not available: {e}")
    NRWCalculator = None

try:
    from src.siv.siv_manager import SIVManager as SIVTracker
except ImportError as e:
    logging.warning(f"SIV Tracker not available: {e}")
    SIVTracker = None

try:
    from src.ai.baseline_comparison import BaselineComparisonService as BaselineComparison
except ImportError as e:
    logging.warning(f"Baseline Comparison not available: {e}")
    BaselineComparison = None

try:
    from src.ai.continuous_learning import ContinuousLearningController as ContinuousLearningSystem
except ImportError as e:
    logging.warning(f"Continuous Learning not available: {e}")
    ContinuousLearningSystem = None

# Workflow and notifications
try:
    from src.workflow.engine import WorkflowEngine
    from src.notifications.alerting import NotificationService
except ImportError as e:
    logging.warning(f"Workflow components not available: {e}")
    WorkflowEngine = None
    NotificationService = None

# Storage
try:
    from src.storage.database import DatabaseHandler
except ImportError as e:
    logging.warning(f"Database not available: {e}")
    DatabaseHandler = None

# API
try:
    from src.api.integrated_api import create_app
except ImportError as e:
    logging.warning(f"API not available: {e}")
    create_app = None

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM RUNNER
# =============================================================================

class SystemRunner:
    """
    Main system runner that orchestrates all components.
    
    Initialization Order:
    1. Event Bus (for component communication)
    2. Health Monitor (for system observability)
    3. Feature Store (single source of truth)
    4. Database Handler (persistence)
    5. AI Components (anomaly detection, leak localization)
    6. Enterprise Components (NRW, SIV, decisions)
    7. Workflow Engine (alerts, work orders)
    8. Notification Service
    9. System Orchestrator (continuous loop)
    10. API Server (external interface)
    
    Shutdown Order: Reverse of initialization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._running = False
        self._shutdown_requested = False
        
        # Component references
        self.event_bus: Optional[EventBus] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.feature_store: Optional[FeatureStore] = None
        self.database: Optional[Any] = None
        self.orchestrator: Optional[SystemOrchestrator] = None
        self.api_server: Optional[Any] = None
        
        # AI components
        self.anomaly_detector: Optional[Any] = None
        self.leak_localizer: Optional[Any] = None
        self.autonomous_system: Optional[Any] = None
        
        # Enterprise components
        self.decision_engine: Optional[Any] = None
        self.nrw_calculator: Optional[Any] = None
        self.siv_tracker: Optional[Any] = None
        self.baseline_comparison: Optional[Any] = None
        self.continuous_learning: Optional[Any] = None
        
        # Workflow components
        self.workflow_engine: Optional[Any] = None
        self.notification_service: Optional[Any] = None
        
        # Startup time
        self._startup_time: Optional[datetime] = None
        
        logger.info("SystemRunner initialized")
    
    # =========================================================================
    # LIFECYCLE MANAGEMENT
    # =========================================================================
    
    def start(self):
        """Start the entire system."""
        if self._running:
            logger.warning("System already running")
            return
        
        logger.info("=" * 60)
        logger.info("STARTING AQUAWATCH NRW SYSTEM")
        logger.info("=" * 60)
        
        self._startup_time = datetime.utcnow()
        
        try:
            # 1. Initialize core infrastructure
            self._init_event_bus()
            self._init_health_monitor()
            self._init_feature_store()
            
            # 2. Initialize persistence
            self._init_database()
            
            # 3. Initialize AI components
            self._init_ai_components()
            
            # 4. Initialize enterprise components
            self._init_enterprise_components()
            
            # 5. Initialize workflow
            self._init_workflow_components()
            
            # 6. Initialize orchestrator
            self._init_orchestrator()
            
            # 7. Wire event handlers
            self._wire_event_handlers()
            
            # 8. Start all services
            self._start_services()
            
            self._running = True
            
            # Publish system started event
            self.event_bus.publish(
                EventType.SYSTEM_STARTED,
                "system_runner",
                {"startup_time": self._startup_time.isoformat()}
            )
            
            logger.info("=" * 60)
            logger.info("AQUAWATCH NRW SYSTEM STARTED SUCCESSFULLY")
            logger.info(f"Startup completed in {(datetime.utcnow() - self._startup_time).total_seconds():.2f}s")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"System startup failed: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the entire system gracefully."""
        if self._shutdown_requested:
            return
        
        self._shutdown_requested = True
        logger.info("=" * 60)
        logger.info("STOPPING AQUAWATCH NRW SYSTEM")
        logger.info("=" * 60)
        
        # Publish system stopped event
        if self.event_bus:
            self.event_bus.publish(
                EventType.SYSTEM_STOPPED,
                "system_runner",
                {}
            )
        
        # Stop in reverse order
        self._stop_services()
        
        self._running = False
        logger.info("AQUAWATCH NRW SYSTEM STOPPED")
    
    def run_forever(self):
        """Run the system until interrupted."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.start()
        
        logger.info("System running. Press Ctrl+C to stop.")
        
        try:
            while self._running and not self._shutdown_requested:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_requested = True
    
    # =========================================================================
    # COMPONENT INITIALIZATION
    # =========================================================================
    
    def _init_event_bus(self):
        """Initialize event bus."""
        logger.info("[1/8] Initializing Event Bus...")
        self.event_bus = get_event_bus()
        logger.info("  ✓ Event Bus ready")
    
    def _init_health_monitor(self):
        """Initialize health monitor."""
        logger.info("[2/8] Initializing Health Monitor...")
        self.health_monitor = get_health_monitor()
        
        # Register alert callback to event bus
        def health_alert_callback(message: str, status: HealthStatus):
            self.event_bus.publish(
                EventType.HEALTH_CHECK_FAILED if status == HealthStatus.RED else EventType.COMPONENT_UNHEALTHY,
                "health_monitor",
                {"message": message, "status": status.value},
                priority=EventPriority.HIGH if status == HealthStatus.RED else EventPriority.NORMAL
            )
        
        self.health_monitor.register_alert_callback(health_alert_callback)
        logger.info("  ✓ Health Monitor ready")
    
    def _init_feature_store(self):
        """Initialize feature store."""
        logger.info("[3/8] Initializing Feature Store...")
        self.feature_store = get_feature_store()
        logger.info("  ✓ Feature Store ready")
    
    def _init_database(self):
        """Initialize database handler."""
        logger.info("[4/8] Initializing Database...")
        if DatabaseHandler:
            try:
                self.database = DatabaseHandler()
                logger.info("  ✓ Database Handler ready")
            except Exception as e:
                logger.warning(f"  ⚠ Database initialization failed: {e}")
                logger.warning("  ⚠ Continuing without database persistence")
        else:
            logger.warning("  ⚠ DatabaseHandler not available")
    
    def _init_ai_components(self):
        """Initialize AI components."""
        logger.info("[5/8] Initializing AI Components...")
        
        if AnomalyDetector:
            try:
                self.anomaly_detector = AnomalyDetector()
                logger.info("  ✓ Anomaly Detector ready")
            except Exception as e:
                logger.warning(f"  ⚠ Anomaly Detector failed: {e}")
        
        if LeakLocalizer:
            try:
                self.leak_localizer = LeakLocalizer()
                logger.info("  ✓ Leak Localizer ready")
            except Exception as e:
                logger.warning(f"  ⚠ Leak Localizer failed: {e}")
        
        if AutonomousWaterSystem:
            try:
                self.autonomous_system = AutonomousWaterSystem()
                logger.info("  ✓ Autonomous System ready")
            except Exception as e:
                logger.warning(f"  ⚠ Autonomous System failed: {e}")
    
    def _init_enterprise_components(self):
        """Initialize enterprise components."""
        logger.info("[6/8] Initializing Enterprise Components...")
        
        if DecisionEngine:
            try:
                self.decision_engine = DecisionEngine()
                logger.info("  ✓ Decision Engine ready")
            except Exception as e:
                logger.warning(f"  ⚠ Decision Engine failed: {e}")
        
        if NRWCalculator:
            try:
                self.nrw_calculator = NRWCalculator()
                logger.info("  ✓ NRW Calculator ready")
            except Exception as e:
                logger.warning(f"  ⚠ NRW Calculator failed: {e}")
        
        if SIVTracker:
            try:
                self.siv_tracker = SIVTracker()
                logger.info("  ✓ SIV Tracker ready")
            except Exception as e:
                logger.warning(f"  ⚠ SIV Tracker failed: {e}")
        
        if BaselineComparison:
            try:
                self.baseline_comparison = BaselineComparison()
                logger.info("  ✓ Baseline Comparison ready")
            except Exception as e:
                logger.warning(f"  ⚠ Baseline Comparison failed: {e}")
        
        if ContinuousLearningSystem:
            try:
                self.continuous_learning = ContinuousLearningSystem()
                logger.info("  ✓ Continuous Learning ready")
            except Exception as e:
                logger.warning(f"  ⚠ Continuous Learning failed: {e}")
    
    def _init_workflow_components(self):
        """Initialize workflow components."""
        logger.info("[7/8] Initializing Workflow Components...")
        
        if WorkflowEngine:
            try:
                self.workflow_engine = WorkflowEngine()
                logger.info("  ✓ Workflow Engine ready")
            except Exception as e:
                logger.warning(f"  ⚠ Workflow Engine failed: {e}")
        
        if NotificationService:
            try:
                self.notification_service = NotificationService()
                logger.info("  ✓ Notification Service ready")
            except Exception as e:
                logger.warning(f"  ⚠ Notification Service failed: {e}")
    
    def _init_orchestrator(self):
        """Initialize system orchestrator."""
        logger.info("[8/8] Initializing System Orchestrator...")
        
        self.orchestrator = get_orchestrator()
        
        # Inject all components
        self.orchestrator.inject_components(
            feature_store=self.feature_store,
            anomaly_detector=self.anomaly_detector,
            leak_localizer=self.leak_localizer,
            decision_engine=self.decision_engine,
            nrw_calculator=self.nrw_calculator,
            siv_tracker=self.siv_tracker,
            baseline_comparison=self.baseline_comparison,
            continuous_learning=self.continuous_learning,
            workflow_engine=self.workflow_engine,
            notification_service=self.notification_service,
            database=self.database,
            event_bus=self.event_bus
        )
        
        logger.info("  ✓ System Orchestrator ready")
    
    # =========================================================================
    # EVENT WIRING
    # =========================================================================
    
    def _wire_event_handlers(self):
        """Wire event handlers for component communication."""
        logger.info("Wiring event handlers...")
        
        # Sensor data → Feature Store
        self.event_bus.subscribe(
            [EventType.SENSOR_DATA_RECEIVED],
            self._handle_sensor_data
        )
        
        # Feature update → Health monitor
        self.event_bus.subscribe(
            [EventType.FEATURE_UPDATED],
            self._handle_feature_update
        )
        
        # Anomaly → Decision Engine
        self.event_bus.subscribe(
            [EventType.ANOMALY_DETECTED],
            self._handle_anomaly
        )
        
        # Leak confirmed → Learning trigger
        self.event_bus.subscribe(
            [EventType.LEAK_CONFIRMED],
            self._handle_leak_confirmed
        )
        
        # False positive → Learning trigger
        self.event_bus.subscribe(
            [EventType.FALSE_POSITIVE_REPORTED],
            self._handle_false_positive
        )
        
        logger.info("  ✓ Event handlers wired")
    
    def _handle_sensor_data(self, event):
        """Handle incoming sensor data."""
        try:
            dma_id = event.data.get('dma_id')
            sensor_id = event.data.get('sensor_id')
            readings = event.data.get('readings', {})
            
            # Update health monitor
            self.health_monitor.update_sensor_reading(dma_id, sensor_id)
            
            # Ingest into feature store
            self.feature_store.ingest_reading(
                dma_id=dma_id,
                sensor_id=sensor_id,
                readings=readings,
                timestamp=event.timestamp
            )
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    def _handle_feature_update(self, event):
        """Handle feature update events."""
        try:
            dma_id = event.data.get('dma_id')
            # Update sensor health in monitor
            self.health_monitor.update_sensor_reading(dma_id, 'feature_store')
        except Exception as e:
            logger.error(f"Error handling feature update: {e}")
    
    def _handle_anomaly(self, event):
        """Handle anomaly detection events."""
        try:
            if self.decision_engine:
                # Feed anomaly to decision engine
                self.decision_engine.process_anomaly(event.data)
        except Exception as e:
            logger.error(f"Error handling anomaly: {e}")
    
    def _handle_leak_confirmed(self, event):
        """Handle leak confirmation events."""
        try:
            if self.continuous_learning:
                # Trigger model update
                self.continuous_learning.add_feedback({
                    'type': 'leak_confirmed',
                    'alert_id': event.data.get('alert_id'),
                    'dma_id': event.data.get('dma_id'),
                    'details': event.data.get('details', {})
                })
        except Exception as e:
            logger.error(f"Error handling leak confirmation: {e}")
    
    def _handle_false_positive(self, event):
        """Handle false positive reports."""
        try:
            if self.continuous_learning:
                # Feed back to learning system
                self.continuous_learning.add_feedback({
                    'type': 'false_positive',
                    'alert_id': event.data.get('alert_id'),
                    'dma_id': event.data.get('dma_id'),
                    'details': event.data.get('details', {})
                })
        except Exception as e:
            logger.error(f"Error handling false positive: {e}")
    
    # =========================================================================
    # SERVICE MANAGEMENT
    # =========================================================================
    
    def _start_services(self):
        """Start all services."""
        logger.info("Starting services...")
        
        # Start event bus
        self.event_bus.start()
        logger.info("  ✓ Event Bus started")
        
        # Start health monitor
        self.health_monitor.start()
        logger.info("  ✓ Health Monitor started")
        
        # Start orchestrator
        self.orchestrator.start()
        logger.info("  ✓ System Orchestrator started")
        
        # Start continuous learning if available
        if self.continuous_learning and hasattr(self.continuous_learning, 'start'):
            self.continuous_learning.start()
            logger.info("  ✓ Continuous Learning started")
    
    def _stop_services(self):
        """Stop all services gracefully."""
        logger.info("Stopping services...")
        
        # Stop orchestrator first
        if self.orchestrator:
            self.orchestrator.stop()
            logger.info("  ✓ Orchestrator stopped")
        
        # Stop continuous learning
        if self.continuous_learning and hasattr(self.continuous_learning, 'stop'):
            self.continuous_learning.stop()
            logger.info("  ✓ Continuous Learning stopped")
        
        # Stop health monitor
        if self.health_monitor:
            self.health_monitor.stop()
            logger.info("  ✓ Health Monitor stopped")
        
        # Stop event bus last
        if self.event_bus:
            self.event_bus.stop()
            logger.info("  ✓ Event Bus stopped")
    
    # =========================================================================
    # STATUS AND DIAGNOSTICS
    # =========================================================================
    
    def get_status(self) -> Dict:
        """Get current system status."""
        uptime = None
        if self._startup_time:
            uptime = (datetime.utcnow() - self._startup_time).total_seconds()
        
        return {
            'running': self._running,
            'startup_time': self._startup_time.isoformat() if self._startup_time else None,
            'uptime_seconds': uptime,
            'health': self.health_monitor.get_dashboard_status() if self.health_monitor else None,
            'orchestrator': self.orchestrator.get_status() if self.orchestrator else None,
            'event_bus': self.event_bus.get_stats() if self.event_bus else None,
            'components': {
                'feature_store': self.feature_store is not None,
                'database': self.database is not None,
                'anomaly_detector': self.anomaly_detector is not None,
                'leak_localizer': self.leak_localizer is not None,
                'decision_engine': self.decision_engine is not None,
                'nrw_calculator': self.nrw_calculator is not None,
                'siv_tracker': self.siv_tracker is not None,
                'baseline_comparison': self.baseline_comparison is not None,
                'continuous_learning': self.continuous_learning is not None,
                'workflow_engine': self.workflow_engine is not None,
                'notification_service': self.notification_service is not None
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_system_runner: Optional[SystemRunner] = None


def get_system_runner() -> SystemRunner:
    """Get the global system runner instance."""
    global _system_runner
    if _system_runner is None:
        _system_runner = SystemRunner()
    return _system_runner


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("AQUAWATCH NRW - NON-REVENUE WATER DETECTION SYSTEM")
    print("=" * 70)
    print()
    print("Starting full system...")
    print()
    
    runner = SystemRunner()
    runner.run_forever()


if __name__ == "__main__":
    main()
