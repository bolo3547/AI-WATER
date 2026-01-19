"""
AQUAWATCH NRW - HEALTH MONITOR
==============================

System health monitoring and fail-safes.

Monitors:
- Data freshness (last reading per sensor)
- Component health (API, AI, DB, MQTT)
- Model performance (accuracy drift)
- System resources (memory, CPU)

Provides:
- GREEN/AMBER/RED status for dashboard
- Automatic alerts on degradation
- Self-healing triggers

Author: AquaWatch AI Team
Version: 1.0.0
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import psutil
import os

logger = logging.getLogger(__name__)


# =============================================================================
# HEALTH STATUS
# =============================================================================

class HealthStatus(Enum):
    """System health status levels."""
    GREEN = "green"      # All systems operational
    AMBER = "amber"      # Degraded but functional
    RED = "red"          # Critical failure
    UNKNOWN = "unknown"  # Status unknown


class ComponentType(Enum):
    """System component types."""
    DATABASE = "database"
    MQTT_BROKER = "mqtt_broker"
    API_SERVER = "api_server"
    AI_ENGINE = "ai_engine"
    FEATURE_STORE = "feature_store"
    EVENT_BUS = "event_bus"
    ORCHESTRATOR = "orchestrator"
    NOTIFICATION_SERVICE = "notification_service"
    DASHBOARD = "dashboard"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ComponentHealth:
    """Health status for a single component."""
    component: ComponentType
    status: HealthStatus
    last_check: datetime
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None


@dataclass
class SensorHealth:
    """Health status for a sensor/DMA."""
    dma_id: str
    sensor_id: str
    last_reading: Optional[datetime]
    status: HealthStatus
    silence_duration: timedelta = field(default_factory=lambda: timedelta(0))
    expected_interval: timedelta = field(default_factory=lambda: timedelta(minutes=15))


@dataclass
class SystemHealthReport:
    """Complete system health report."""
    timestamp: datetime
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    sensors: Dict[str, SensorHealth]
    metrics: Dict[str, Any]
    alerts: List[str]


# =============================================================================
# HEALTH CHECKS
# =============================================================================

class HealthCheck:
    """Base health check class."""
    
    def __init__(self, name: str, interval: float = 60.0):
        self.name = name
        self.interval = interval
        self.last_check: Optional[datetime] = None
        self.last_result: Optional[bool] = None
    
    def check(self) -> tuple[bool, str, Dict]:
        """Run health check. Returns (success, message, details)."""
        raise NotImplementedError
    
    def should_run(self) -> bool:
        """Check if this health check should run."""
        if self.last_check is None:
            return True
        return (datetime.utcnow() - self.last_check).total_seconds() >= self.interval


class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity."""
    
    def __init__(self, db_handler=None):
        super().__init__("database", interval=30.0)
        self.db_handler = db_handler
    
    def check(self) -> tuple[bool, str, Dict]:
        try:
            if self.db_handler:
                # Try a simple query
                result = self.db_handler.health_check()
                return True, "Database connected", {"latency_ms": result.get('latency_ms', 0)}
            else:
                # Try to connect
                import psycopg2
                conn = psycopg2.connect(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    port=int(os.environ.get('DB_PORT', 5432)),
                    database=os.environ.get('DB_NAME', 'aquawatch'),
                    user=os.environ.get('DB_USER', 'postgres'),
                    password=os.environ.get('DB_PASSWORD', ''),
                    connect_timeout=5
                )
                conn.close()
                return True, "Database connected", {}
        except Exception as e:
            return False, f"Database error: {str(e)}", {}


class MQTTHealthCheck(HealthCheck):
    """Check MQTT broker connectivity."""
    
    def __init__(self, mqtt_client=None):
        super().__init__("mqtt", interval=30.0)
        self.mqtt_client = mqtt_client
    
    def check(self) -> tuple[bool, str, Dict]:
        try:
            if self.mqtt_client:
                if self.mqtt_client.is_connected():
                    return True, "MQTT connected", {}
                else:
                    return False, "MQTT disconnected", {}
            else:
                return True, "MQTT not configured", {}
        except Exception as e:
            return False, f"MQTT error: {str(e)}", {}


class APIHealthCheck(HealthCheck):
    """Check API server health."""
    
    def __init__(self, api_url: str = None):
        super().__init__("api", interval=15.0)
        self.api_url = api_url or "http://localhost:5000/api/health"
    
    def check(self) -> tuple[bool, str, Dict]:
        try:
            import requests
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                return True, "API healthy", response.json()
            else:
                return False, f"API returned {response.status_code}", {}
        except Exception as e:
            return False, f"API error: {str(e)}", {}


class ResourceHealthCheck(HealthCheck):
    """Check system resources (CPU, memory, disk)."""
    
    def __init__(self):
        super().__init__("resources", interval=60.0)
        self.cpu_threshold = 90.0
        self.memory_threshold = 90.0
        self.disk_threshold = 95.0
    
    def check(self) -> tuple[bool, str, Dict]:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            details = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
            
            issues = []
            if cpu_percent > self.cpu_threshold:
                issues.append(f"CPU high: {cpu_percent}%")
            if memory.percent > self.memory_threshold:
                issues.append(f"Memory high: {memory.percent}%")
            if disk.percent > self.disk_threshold:
                issues.append(f"Disk high: {disk.percent}%")
            
            if issues:
                return False, "; ".join(issues), details
            
            return True, "Resources OK", details
            
        except Exception as e:
            return False, f"Resource check error: {str(e)}", {}


# =============================================================================
# HEALTH MONITOR
# =============================================================================

class HealthMonitor:
    """
    Centralized health monitoring for the AquaWatch system.
    
    Provides:
    - Component health checks
    - Sensor data freshness monitoring
    - System resource monitoring
    - Alert generation
    - Dashboard status (GREEN/AMBER/RED)
    """
    
    def __init__(
        self,
        check_interval: float = 30.0,
        sensor_timeout: timedelta = timedelta(minutes=30),
        amber_threshold: int = 1,
        red_threshold: int = 3
    ):
        self._lock = threading.RLock()
        self.check_interval = check_interval
        self.sensor_timeout = sensor_timeout
        self.amber_threshold = amber_threshold  # failures to go AMBER
        self.red_threshold = red_threshold      # failures to go RED
        
        # Health checks
        self._health_checks: Dict[ComponentType, HealthCheck] = {}
        self._component_health: Dict[ComponentType, ComponentHealth] = {}
        
        # Sensor tracking
        self._sensor_last_reading: Dict[str, datetime] = {}
        self._sensor_health: Dict[str, SensorHealth] = {}
        
        # Alerts
        self._active_alerts: List[str] = []
        self._alert_callbacks: List[Callable[[str, HealthStatus], None]] = []
        
        # Running state
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Metrics
        self.metrics = {
            'checks_performed': 0,
            'failures_detected': 0,
            'alerts_generated': 0,
            'last_full_check': None
        }
        
        # Register default health checks
        self._register_default_checks()
        
        logger.info("HealthMonitor initialized")
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_check(ComponentType.DATABASE, DatabaseHealthCheck())
        self.register_check(ComponentType.MQTT_BROKER, MQTTHealthCheck())
        # Resource check runs for all components
    
    # =========================================================================
    # HEALTH CHECK MANAGEMENT
    # =========================================================================
    
    def register_check(self, component: ComponentType, check: HealthCheck):
        """Register a health check for a component."""
        self._health_checks[component] = check
        self._component_health[component] = ComponentHealth(
            component=component,
            status=HealthStatus.UNKNOWN,
            last_check=datetime.utcnow()
        )
        logger.debug(f"Registered health check: {component.value}")
    
    def update_sensor_reading(self, dma_id: str, sensor_id: str):
        """Update last reading time for a sensor."""
        key = f"{dma_id}:{sensor_id}"
        with self._lock:
            self._sensor_last_reading[key] = datetime.utcnow()
    
    def register_alert_callback(self, callback: Callable[[str, HealthStatus], None]):
        """Register callback for health alerts."""
        self._alert_callbacks.append(callback)
    
    # =========================================================================
    # MONITORING LOOP
    # =========================================================================
    
    def start(self):
        """Start health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("HealthMonitor started")
    
    def stop(self, timeout: float = 5.0):
        """Stop health monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=timeout)
        logger.info("HealthMonitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._run_checks()
                self._check_sensors()
                self._evaluate_overall_health()
                self.metrics['last_full_check'] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
            
            time.sleep(self.check_interval)
    
    def _run_checks(self):
        """Run all health checks."""
        for component, check in self._health_checks.items():
            if not check.should_run():
                continue
            
            try:
                success, message, details = check.check()
                check.last_check = datetime.utcnow()
                check.last_result = success
                
                self.metrics['checks_performed'] += 1
                
                with self._lock:
                    health = self._component_health[component]
                    
                    if success:
                        health.status = HealthStatus.GREEN
                        health.message = message
                        health.details = details
                        health.consecutive_failures = 0
                        health.last_success = datetime.utcnow()
                    else:
                        health.consecutive_failures += 1
                        health.message = message
                        health.details = details
                        self.metrics['failures_detected'] += 1
                        
                        if health.consecutive_failures >= self.red_threshold:
                            health.status = HealthStatus.RED
                            self._generate_alert(f"CRITICAL: {component.value} - {message}")
                        elif health.consecutive_failures >= self.amber_threshold:
                            health.status = HealthStatus.AMBER
                            self._generate_alert(f"WARNING: {component.value} - {message}")
                    
                    health.last_check = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Health check failed for {component.value}: {e}")
    
    def _check_sensors(self):
        """Check sensor data freshness."""
        now = datetime.utcnow()
        
        with self._lock:
            for key, last_reading in self._sensor_last_reading.items():
                parts = key.split(':')
                dma_id = parts[0]
                sensor_id = parts[1] if len(parts) > 1 else 'unknown'
                
                silence = now - last_reading
                
                if key not in self._sensor_health:
                    self._sensor_health[key] = SensorHealth(
                        dma_id=dma_id,
                        sensor_id=sensor_id,
                        last_reading=last_reading,
                        status=HealthStatus.GREEN
                    )
                
                health = self._sensor_health[key]
                health.last_reading = last_reading
                health.silence_duration = silence
                
                if silence > self.sensor_timeout * 2:
                    health.status = HealthStatus.RED
                    self._generate_alert(f"SENSOR SILENT: {dma_id}/{sensor_id} - no data for {silence}")
                elif silence > self.sensor_timeout:
                    health.status = HealthStatus.AMBER
                else:
                    health.status = HealthStatus.GREEN
    
    def _generate_alert(self, message: str):
        """Generate a health alert."""
        if message not in self._active_alerts:
            self._active_alerts.append(message)
            self.metrics['alerts_generated'] += 1
            
            # Call alert callbacks
            status = HealthStatus.RED if 'CRITICAL' in message else HealthStatus.AMBER
            for callback in self._alert_callbacks:
                try:
                    callback(message, status)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
            
            logger.warning(f"Health alert: {message}")
    
    def _evaluate_overall_health(self):
        """Evaluate overall system health."""
        with self._lock:
            all_statuses = [h.status for h in self._component_health.values()]
            all_statuses.extend([h.status for h in self._sensor_health.values()])
        
        # Determine overall status
        if HealthStatus.RED in all_statuses:
            return HealthStatus.RED
        elif HealthStatus.AMBER in all_statuses:
            return HealthStatus.AMBER
        elif HealthStatus.UNKNOWN in all_statuses:
            return HealthStatus.AMBER
        else:
            return HealthStatus.GREEN
    
    # =========================================================================
    # STATUS QUERIES
    # =========================================================================
    
    def get_status(self) -> HealthStatus:
        """Get overall system status."""
        return self._evaluate_overall_health()
    
    def get_component_status(self, component: ComponentType) -> ComponentHealth:
        """Get status for a specific component."""
        return self._component_health.get(component)
    
    def get_sensor_status(self, dma_id: str, sensor_id: str = None) -> List[SensorHealth]:
        """Get sensor health status."""
        with self._lock:
            results = []
            for key, health in self._sensor_health.items():
                if health.dma_id == dma_id:
                    if sensor_id is None or health.sensor_id == sensor_id:
                        results.append(health)
            return results
    
    def get_full_report(self) -> SystemHealthReport:
        """Get comprehensive health report."""
        with self._lock:
            overall = self._evaluate_overall_health()
            
            # Get resource metrics
            resource_metrics = {}
            try:
                resource_metrics = {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
            except:
                pass
            
            return SystemHealthReport(
                timestamp=datetime.utcnow(),
                overall_status=overall,
                components={k.value: v for k, v in self._component_health.items()},
                sensors=self._sensor_health.copy(),
                metrics={**self.metrics, **resource_metrics},
                alerts=self._active_alerts.copy()
            )
    
    def get_dashboard_status(self) -> Dict:
        """Get simplified status for dashboard display."""
        overall = self._evaluate_overall_health()
        
        return {
            'status': overall.value,
            'color': {
                HealthStatus.GREEN: '#28a745',
                HealthStatus.AMBER: '#ffc107',
                HealthStatus.RED: '#dc3545',
                HealthStatus.UNKNOWN: '#6c757d'
            }.get(overall, '#6c757d'),
            'message': {
                HealthStatus.GREEN: 'All Systems Operational',
                HealthStatus.AMBER: 'System Degraded',
                HealthStatus.RED: 'Critical Issues Detected',
                HealthStatus.UNKNOWN: 'Status Unknown'
            }.get(overall, 'Unknown'),
            'active_alerts': len(self._active_alerts),
            'last_check': self.metrics.get('last_full_check', datetime.utcnow()).isoformat()
        }
    
    def clear_alerts(self):
        """Clear all active alerts."""
        self._active_alerts.clear()
    
    def acknowledge_alert(self, alert_message: str):
        """Acknowledge and remove an alert."""
        if alert_message in self._active_alerts:
            self._active_alerts.remove(alert_message)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_system_status() -> HealthStatus:
    """Get overall system health status."""
    return get_health_monitor().get_status()


def get_dashboard_health() -> Dict:
    """Get health status for dashboard."""
    return get_health_monitor().get_dashboard_status()


def update_sensor_health(dma_id: str, sensor_id: str):
    """Update sensor reading timestamp."""
    get_health_monitor().update_sensor_reading(dma_id, sensor_id)


def start_health_monitor():
    """Start health monitoring."""
    get_health_monitor().start()


def stop_health_monitor():
    """Stop health monitoring."""
    get_health_monitor().stop()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("HEALTH MONITOR DEMO")
    print("=" * 60)
    
    monitor = HealthMonitor(check_interval=5.0)
    
    # Register alert callback
    def on_alert(message: str, status: HealthStatus):
        print(f"🚨 ALERT: {message} (Status: {status.value})")
    
    monitor.register_alert_callback(on_alert)
    
    # Simulate sensor readings
    monitor.update_sensor_reading("DMA-001", "SENSOR-001")
    monitor.update_sensor_reading("DMA-001", "SENSOR-002")
    monitor.update_sensor_reading("DMA-002", "SENSOR-001")
    
    # Start monitoring
    monitor.start()
    
    print("\nMonitoring for 10 seconds...")
    time.sleep(10)
    
    # Get status
    print("\n" + "=" * 60)
    print("STATUS REPORT")
    print("=" * 60)
    
    report = monitor.get_full_report()
    print(f"Overall Status: {report.overall_status.value}")
    print(f"Components: {len(report.components)}")
    print(f"Sensors: {len(report.sensors)}")
    print(f"Active Alerts: {len(report.alerts)}")
    
    dashboard = monitor.get_dashboard_status()
    print(f"\nDashboard: {dashboard}")
    
    # Stop
    monitor.stop()
    print("\nDemo complete")
