"""
AQUAWATCH NRW - SYSTEM ORCHESTRATOR
===================================

CONTINUOUS AI EXECUTION LOOP

This is the heart of the system - runs continuously to:
1. Pull latest data
2. Validate and clean
3. Update feature store
4. Run anomaly detection
5. Update leak probability
6. Run NRW calculator
7. Execute Decision Engine
8. Generate alerts / work orders
9. Update dashboard caches

The orchestrator is:
- Fault-tolerant (retries on failure)
- Logs every stage
- Never silently stops
- Configurable intervals

Author: AquaWatch AI Team
Version: 1.0.0
"""

import asyncio
import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class PipelineStage(Enum):
    """Stages of the AI pipeline."""
    DATA_INGESTION = "data_ingestion"
    DATA_VALIDATION = "data_validation"
    FEATURE_UPDATE = "feature_update"
    ANOMALY_DETECTION = "anomaly_detection"
    LEAK_PROBABILITY = "leak_probability"
    NRW_CALCULATION = "nrw_calculation"
    DECISION_ENGINE = "decision_engine"
    ALERT_GENERATION = "alert_generation"
    WORK_ORDER_CREATION = "work_order_creation"
    NOTIFICATION = "notification"
    DASHBOARD_UPDATE = "dashboard_update"
    LEARNING_UPDATE = "learning_update"


class StageStatus(Enum):
    """Status of a pipeline stage."""
    NOT_RUN = "not_run"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class OrchestratorState(Enum):
    """State of the orchestrator."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class StageResult:
    """Result of executing a pipeline stage."""
    stage: PipelineStage
    status: StageStatus
    start_time: datetime
    end_time: datetime
    duration_ms: float
    output: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'stage': self.stage.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_ms': self.duration_ms,
            'error': self.error,
            'retry_count': self.retry_count
        }


@dataclass
class CycleResult:
    """Result of a complete pipeline cycle."""
    cycle_id: str
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    stages: List[StageResult]
    dmas_processed: int
    anomalies_detected: int
    alerts_generated: int
    success: bool
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration_ms': self.total_duration_ms,
            'stages': [s.to_dict() for s in self.stages],
            'dmas_processed': self.dmas_processed,
            'anomalies_detected': self.anomalies_detected,
            'alerts_generated': self.alerts_generated,
            'success': self.success
        }


@dataclass
class OrchestratorConfig:
    """Configuration for the system orchestrator."""
    # Timing
    cycle_interval_seconds: int = 300  # 5 minutes
    min_cycle_interval_seconds: int = 60  # Minimum 1 minute
    
    # Retries
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Fault tolerance
    fail_fast: bool = False  # If True, stop on first failure
    continue_on_stage_failure: bool = True
    
    # Concurrency
    max_concurrent_dmas: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "./logs/orchestrator.log"
    
    # Health
    health_check_interval_seconds: int = 60
    stale_data_threshold_minutes: int = 30


# =============================================================================
# PIPELINE STAGE EXECUTOR
# =============================================================================

class StageExecutor:
    """Executes individual pipeline stages with retry logic."""
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
    
    def execute(
        self,
        stage: PipelineStage,
        func: Callable,
        *args,
        **kwargs
    ) -> StageResult:
        """Execute a pipeline stage with retries."""
        start_time = datetime.utcnow()
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                output = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                
                return StageResult(
                    stage=stage,
                    status=StageStatus.SUCCESS,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration,
                    output=output,
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                logger.warning(f"Stage {stage.value} failed (attempt {retry_count}): {e}")
                
                if retry_count <= self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds)
        
        # All retries exhausted
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=stage,
            status=StageStatus.FAILED,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration,
            error=last_error,
            retry_count=retry_count - 1
        )


# =============================================================================
# SYSTEM ORCHESTRATOR
# =============================================================================

class SystemOrchestrator:
    """
    Main system orchestrator - runs the AI pipeline continuously.
    
    This is the CENTRAL COORDINATOR that ensures:
    - Data flows end-to-end
    - AI runs continuously
    - Decisions are made
    - System health is monitored
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.state = OrchestratorState.STOPPED
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Stage executor
        self.executor = StageExecutor(self.config)
        
        # Cycle history
        self.cycle_history: List[CycleResult] = []
        self.max_history = 100
        
        # Current cycle info
        self.current_cycle_id: Optional[str] = None
        self.last_cycle_time: Optional[datetime] = None
        
        # Component references (to be injected)
        self.feature_store = None
        self.anomaly_detector = None
        self.decision_engine = None
        self.nrw_calculator = None
        self.workflow_engine = None
        self.notification_service = None
        self.baseline_service = None
        self.learning_controller = None
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Metrics
        self.metrics = {
            'cycles_completed': 0,
            'cycles_failed': 0,
            'total_anomalies_detected': 0,
            'total_alerts_generated': 0,
            'total_dmas_processed': 0,
            'average_cycle_duration_ms': 0
        }
        
        logger.info("SystemOrchestrator initialized")
    
    # =========================================================================
    # COMPONENT INJECTION
    # =========================================================================
    
    def inject_components(
        self,
        feature_store=None,
        anomaly_detector=None,
        decision_engine=None,
        nrw_calculator=None,
        workflow_engine=None,
        notification_service=None,
        baseline_service=None,
        learning_controller=None,
        # Additional components
        leak_localizer=None,
        siv_tracker=None,
        baseline_comparison=None,
        continuous_learning=None,
        database=None,
        event_bus=None
    ):
        """Inject component dependencies."""
        if feature_store:
            self.feature_store = feature_store
        if anomaly_detector:
            self.anomaly_detector = anomaly_detector
        if decision_engine:
            self.decision_engine = decision_engine
        if nrw_calculator:
            self.nrw_calculator = nrw_calculator
        if workflow_engine:
            self.workflow_engine = workflow_engine
        if notification_service:
            self.notification_service = notification_service
        if baseline_service:
            self.baseline_service = baseline_service
        if learning_controller:
            self.learning_controller = learning_controller
        # Additional components
        if leak_localizer:
            self.leak_localizer = leak_localizer
        if siv_tracker:
            self.siv_tracker = siv_tracker
        if baseline_comparison:
            self.baseline_comparison = baseline_comparison
            self.baseline_service = baseline_comparison  # Alias
        if continuous_learning:
            self.continuous_learning = continuous_learning
            self.learning_controller = continuous_learning  # Alias
        if database:
            self.database = database
        if event_bus:
            self.event_bus = event_bus
        
        logger.info("Components injected into orchestrator")
    
    # =========================================================================
    # LIFECYCLE CONTROL
    # =========================================================================
    
    def start(self):
        """Start the orchestrator."""
        with self._lock:
            if self.state == OrchestratorState.RUNNING:
                logger.warning("Orchestrator already running")
                return
            
            self.state = OrchestratorState.STARTING
            self._stop_event.clear()
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            self.state = OrchestratorState.RUNNING
            logger.info("SystemOrchestrator started")
    
    def stop(self, timeout: float = 30.0):
        """Stop the orchestrator gracefully."""
        with self._lock:
            if self.state == OrchestratorState.STOPPED:
                return
            
            self.state = OrchestratorState.STOPPING
            self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
        
        self.state = OrchestratorState.STOPPED
        logger.info("SystemOrchestrator stopped")
    
    def pause(self):
        """Pause the orchestrator."""
        with self._lock:
            if self.state == OrchestratorState.RUNNING:
                self.state = OrchestratorState.PAUSED
                logger.info("SystemOrchestrator paused")
    
    def resume(self):
        """Resume the orchestrator."""
        with self._lock:
            if self.state == OrchestratorState.PAUSED:
                self.state = OrchestratorState.RUNNING
                logger.info("SystemOrchestrator resumed")
    
    # =========================================================================
    # MAIN EXECUTION LOOP
    # =========================================================================
    
    def _run_loop(self):
        """Main execution loop - runs continuously."""
        logger.info("Orchestrator loop started")
        
        while not self._stop_event.is_set():
            try:
                # Check if paused
                if self.state == OrchestratorState.PAUSED:
                    time.sleep(1)
                    continue
                
                # Execute one cycle
                cycle_start = time.time()
                cycle_result = self._execute_cycle()
                cycle_duration = time.time() - cycle_start
                
                # Update metrics
                self._update_metrics(cycle_result)
                
                # Store result
                self.cycle_history.append(cycle_result)
                if len(self.cycle_history) > self.max_history:
                    self.cycle_history = self.cycle_history[-self.max_history:]
                
                self.last_cycle_time = datetime.utcnow()
                
                # Log result
                if cycle_result.success:
                    logger.info(
                        f"Cycle {cycle_result.cycle_id} completed: "
                        f"{cycle_result.dmas_processed} DMAs, "
                        f"{cycle_result.anomalies_detected} anomalies, "
                        f"{cycle_result.alerts_generated} alerts "
                        f"({cycle_result.total_duration_ms:.0f}ms)"
                    )
                else:
                    logger.error(f"Cycle {cycle_result.cycle_id} failed")
                
                # Emit event
                self._emit_event('cycle_complete', cycle_result)
                
                # Wait for next cycle
                wait_time = max(
                    self.config.cycle_interval_seconds - cycle_duration,
                    self.config.min_cycle_interval_seconds
                )
                self._stop_event.wait(timeout=wait_time)
                
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")
                logger.error(traceback.format_exc())
                self.state = OrchestratorState.ERROR
                self._emit_event('error', {'error': str(e)})
                time.sleep(self.config.retry_delay_seconds)
        
        logger.info("Orchestrator loop stopped")
    
    def _execute_cycle(self) -> CycleResult:
        """Execute one complete pipeline cycle."""
        cycle_id = f"CYC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.current_cycle_id = cycle_id
        start_time = datetime.utcnow()
        
        stages: List[StageResult] = []
        dmas_processed = 0
        anomalies_detected = 0
        alerts_generated = 0
        
        try:
            # STAGE 1: Data Validation
            result = self.executor.execute(
                PipelineStage.DATA_VALIDATION,
                self._stage_validate_data
            )
            stages.append(result)
            
            if result.status == StageStatus.FAILED and self.config.fail_fast:
                raise Exception(f"Stage failed: {result.error}")
            
            # STAGE 2: Feature Update
            result = self.executor.execute(
                PipelineStage.FEATURE_UPDATE,
                self._stage_update_features
            )
            stages.append(result)
            
            if result.output:
                dmas_processed = result.output.get('dmas_updated', 0)
            
            # STAGE 3: Anomaly Detection
            result = self.executor.execute(
                PipelineStage.ANOMALY_DETECTION,
                self._stage_detect_anomalies
            )
            stages.append(result)
            
            if result.output:
                anomalies_detected = result.output.get('anomalies_found', 0)
            
            # STAGE 4: Leak Probability
            result = self.executor.execute(
                PipelineStage.LEAK_PROBABILITY,
                self._stage_calculate_leak_probability
            )
            stages.append(result)
            
            # STAGE 5: NRW Calculation
            result = self.executor.execute(
                PipelineStage.NRW_CALCULATION,
                self._stage_calculate_nrw
            )
            stages.append(result)
            
            # STAGE 6: Decision Engine
            result = self.executor.execute(
                PipelineStage.DECISION_ENGINE,
                self._stage_run_decision_engine
            )
            stages.append(result)
            
            # STAGE 7: Alert Generation
            result = self.executor.execute(
                PipelineStage.ALERT_GENERATION,
                self._stage_generate_alerts
            )
            stages.append(result)
            
            if result.output:
                alerts_generated = result.output.get('alerts_created', 0)
            
            # STAGE 8: Work Order Creation
            result = self.executor.execute(
                PipelineStage.WORK_ORDER_CREATION,
                self._stage_create_work_orders
            )
            stages.append(result)
            
            # STAGE 9: Notifications
            result = self.executor.execute(
                PipelineStage.NOTIFICATION,
                self._stage_send_notifications
            )
            stages.append(result)
            
            # STAGE 10: Dashboard Update
            result = self.executor.execute(
                PipelineStage.DASHBOARD_UPDATE,
                self._stage_update_dashboard
            )
            stages.append(result)
            
            # STAGE 11: Learning Update
            result = self.executor.execute(
                PipelineStage.LEARNING_UPDATE,
                self._stage_update_learning
            )
            stages.append(result)
            
        except Exception as e:
            logger.error(f"Cycle execution error: {e}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        
        # Check if all critical stages succeeded
        critical_stages = [
            PipelineStage.DATA_VALIDATION,
            PipelineStage.FEATURE_UPDATE,
            PipelineStage.ANOMALY_DETECTION
        ]
        success = all(
            s.status == StageStatus.SUCCESS 
            for s in stages 
            if s.stage in critical_stages
        )
        
        return CycleResult(
            cycle_id=cycle_id,
            start_time=start_time,
            end_time=end_time,
            total_duration_ms=duration,
            stages=stages,
            dmas_processed=dmas_processed,
            anomalies_detected=anomalies_detected,
            alerts_generated=alerts_generated,
            success=success
        )
    
    # =========================================================================
    # PIPELINE STAGES
    # =========================================================================
    
    def _stage_validate_data(self) -> Dict:
        """Stage 1: Validate incoming data."""
        if not self.feature_store:
            return {'status': 'skipped', 'reason': 'No feature store'}
        
        freshness = self.feature_store.check_all_freshness()
        stale_dmas = [k for k, v in freshness.items() if v.get('stale')]
        
        return {
            'total_dmas': len(freshness),
            'fresh_dmas': len(freshness) - len(stale_dmas),
            'stale_dmas': stale_dmas
        }
    
    def _stage_update_features(self) -> Dict:
        """Stage 2: Update feature store."""
        if not self.feature_store:
            return {'status': 'skipped', 'reason': 'No feature store'}
        
        # Features are updated on ingestion, but we can force baseline updates
        dmas = list(self.feature_store.get_latest_all().keys())
        
        for dma_id in dmas:
            self.feature_store.update_baseline_from_history(dma_id, days=7)
        
        return {'dmas_updated': len(dmas)}
    
    def _stage_detect_anomalies(self) -> Dict:
        """Stage 3: Run anomaly detection on all DMAs."""
        if not self.feature_store:
            return {'status': 'skipped', 'anomalies_found': 0}
        
        anomalies = []
        latest_features = self.feature_store.get_latest_all()
        
        for dma_id, features in latest_features.items():
            # Check for anomalous conditions
            if features.pressure_deviation < -0.15:  # >15% pressure drop
                anomalies.append({
                    'dma_id': dma_id,
                    'type': 'pressure_drop',
                    'value': features.pressure_deviation
                })
            
            if features.mnf_deviation > 0.2:  # >20% MNF increase
                anomalies.append({
                    'dma_id': dma_id,
                    'type': 'mnf_increase',
                    'value': features.mnf_deviation
                })
            
            if features.night_day_ratio > 0.35:  # Night flow > 35% of day
                anomalies.append({
                    'dma_id': dma_id,
                    'type': 'high_night_flow',
                    'value': features.night_day_ratio
                })
        
        # Store anomalies for downstream processing
        self._current_anomalies = anomalies
        
        return {'anomalies_found': len(anomalies), 'anomalies': anomalies}
    
    def _stage_calculate_leak_probability(self) -> Dict:
        """Stage 4: Calculate leak probabilities."""
        if not hasattr(self, '_current_anomalies'):
            return {'status': 'skipped'}
        
        probabilities = []
        for anomaly in self._current_anomalies:
            # Simple probability calculation (would use ML model in production)
            base_prob = 0.3
            if anomaly['type'] == 'pressure_drop':
                prob = base_prob + abs(anomaly['value']) * 2
            elif anomaly['type'] == 'mnf_increase':
                prob = base_prob + anomaly['value'] * 1.5
            else:
                prob = base_prob + anomaly['value']
            
            probabilities.append({
                'dma_id': anomaly['dma_id'],
                'probability': min(prob, 1.0),
                'source': anomaly['type']
            })
        
        self._current_probabilities = probabilities
        return {'probabilities_calculated': len(probabilities)}
    
    def _stage_calculate_nrw(self) -> Dict:
        """Stage 5: Calculate NRW metrics."""
        if not self.nrw_calculator or not self.feature_store:
            return {'status': 'skipped'}
        
        # Would calculate NRW for each DMA
        return {'nrw_calculations': 0}
    
    def _stage_run_decision_engine(self) -> Dict:
        """Stage 6: Run decision engine."""
        if not self.decision_engine or not hasattr(self, '_current_probabilities'):
            return {'status': 'skipped'}
        
        decisions = []
        for prob in self._current_probabilities:
            if prob['probability'] > 0.5:
                decisions.append({
                    'dma_id': prob['dma_id'],
                    'action': 'investigate',
                    'priority': 'high' if prob['probability'] > 0.8 else 'medium'
                })
        
        self._current_decisions = decisions
        return {'decisions_made': len(decisions)}
    
    def _stage_generate_alerts(self) -> Dict:
        """Stage 7: Generate alerts from decisions."""
        if not hasattr(self, '_current_decisions'):
            return {'status': 'skipped', 'alerts_created': 0}
        
        alerts_created = 0
        for decision in self._current_decisions:
            if decision['action'] == 'investigate':
                # Would create alert via workflow engine
                alerts_created += 1
        
        return {'alerts_created': alerts_created}
    
    def _stage_create_work_orders(self) -> Dict:
        """Stage 8: Create work orders from alerts."""
        if not self.workflow_engine:
            return {'status': 'skipped'}
        
        return {'work_orders_created': 0}
    
    def _stage_send_notifications(self) -> Dict:
        """Stage 9: Send notifications."""
        if not self.notification_service:
            return {'status': 'skipped'}
        
        return {'notifications_sent': 0}
    
    def _stage_update_dashboard(self) -> Dict:
        """Stage 10: Update dashboard caches."""
        # Dashboard reads directly from feature store
        return {'dashboard_updated': True}
    
    def _stage_update_learning(self) -> Dict:
        """Stage 11: Update learning system."""
        if not self.learning_controller or not self.baseline_service:
            return {'status': 'skipped'}
        
        # Check for drift-triggered retraining
        return {'learning_updated': True}
    
    # =========================================================================
    # METRICS & STATUS
    # =========================================================================
    
    def _update_metrics(self, cycle_result: CycleResult):
        """Update orchestrator metrics."""
        if cycle_result.success:
            self.metrics['cycles_completed'] += 1
        else:
            self.metrics['cycles_failed'] += 1
        
        self.metrics['total_anomalies_detected'] += cycle_result.anomalies_detected
        self.metrics['total_alerts_generated'] += cycle_result.alerts_generated
        self.metrics['total_dmas_processed'] += cycle_result.dmas_processed
        
        # Update average duration
        total_cycles = self.metrics['cycles_completed'] + self.metrics['cycles_failed']
        current_avg = self.metrics['average_cycle_duration_ms']
        self.metrics['average_cycle_duration_ms'] = (
            (current_avg * (total_cycles - 1) + cycle_result.total_duration_ms) / total_cycles
        )
    
    def get_status(self) -> Dict:
        """Get orchestrator status."""
        return {
            'state': self.state.value,
            'current_cycle_id': self.current_cycle_id,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'config': {
                'cycle_interval_seconds': self.config.cycle_interval_seconds,
                'max_retries': self.config.max_retries
            },
            'metrics': self.metrics,
            'components': {
                'feature_store': self.feature_store is not None,
                'anomaly_detector': self.anomaly_detector is not None,
                'decision_engine': self.decision_engine is not None,
                'nrw_calculator': self.nrw_calculator is not None,
                'workflow_engine': self.workflow_engine is not None,
                'notification_service': self.notification_service is not None,
                'baseline_service': self.baseline_service is not None,
                'learning_controller': self.learning_controller is not None
            }
        }
    
    def get_recent_cycles(self, limit: int = 10) -> List[Dict]:
        """Get recent cycle results."""
        return [c.to_dict() for c in self.cycle_history[-limit:]]
    
    # =========================================================================
    # EVENT HANDLING
    # =========================================================================
    
    def on(self, event: str, handler: Callable):
        """Register event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def _emit_event(self, event: str, data: Any):
        """Emit event to handlers."""
        for handler in self._event_handlers.get(event, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_orchestrator: Optional[SystemOrchestrator] = None


def get_orchestrator() -> SystemOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SystemOrchestrator()
    return _orchestrator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def start_orchestrator():
    """Start the global orchestrator."""
    get_orchestrator().start()


def stop_orchestrator():
    """Stop the global orchestrator."""
    get_orchestrator().stop()


def get_orchestrator_status() -> Dict:
    """Get orchestrator status."""
    return get_orchestrator().get_status()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("SYSTEM ORCHESTRATOR DEMO")
    print("=" * 60)
    
    # Create orchestrator
    config = OrchestratorConfig(
        cycle_interval_seconds=10,  # Fast for demo
        max_retries=2
    )
    orchestrator = SystemOrchestrator(config)
    
    # Inject mock feature store
    from src.core.feature_store import FeatureStore
    feature_store = FeatureStore()
    
    # Add some test data
    feature_store.set_baseline("DMA001", {'pressure': 3.0, 'flow': 50.0, 'mnf': 10.0})
    feature_store.ingest_reading(
        dma_id="DMA001",
        sensor_id="SENSOR001",
        timestamp=datetime.utcnow(),
        pressure=2.5,  # Low pressure - anomaly
        flow=60.0,
        noise_level=40.0
    )
    
    orchestrator.inject_components(feature_store=feature_store)
    
    # Register event handler
    orchestrator.on('cycle_complete', lambda r: print(f"Cycle complete: {r.cycle_id}"))
    
    # Start
    print("\nStarting orchestrator (press Ctrl+C to stop)...")
    orchestrator.start()
    
    try:
        while True:
            time.sleep(5)
            status = orchestrator.get_status()
            print(f"\nStatus: {status['state']}, Cycles: {status['metrics']['cycles_completed']}")
    except KeyboardInterrupt:
        print("\nStopping...")
        orchestrator.stop()
    
    print("\nFinal metrics:", orchestrator.metrics)
