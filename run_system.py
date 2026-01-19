"""
AquaWatch NRW - Complete System Runner
======================================

Runs the full system with CONTINUOUS AI ORCHESTRATION:
1. Core Orchestration Layer (Feature Store, Event Bus, Health Monitor)
2. MQTT Ingestion Service (receives ESP32 data)
3. AI Pipeline (anomaly detection, NRW calculation, decisions)
4. Database Storage (TimescaleDB)
5. Dashboard (Monday.com style UI)

Usage:
    python run_system.py [--mode full|simple|demo]

Requirements:
    pip install paho-mqtt psycopg2-binary dash dash-bootstrap-components plotly uvicorn fastapi

Author: AquaWatch AI Team
Version: 2.0.0 - Now with Continuous AI Orchestration
"""

import sys
import threading
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("AquaWatch")

# Core orchestration imports
try:
    from src.core import (
        get_system_runner,
        get_feature_store,
        get_event_bus,
        get_health_monitor,
        get_orchestrator,
        EventType,
        HealthStatus
    )
    CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core orchestration not available: {e}")
    CORE_AVAILABLE = False


def start_mqtt_ingestion(event_bus=None, feature_store=None, health_monitor=None):
    """Start MQTT ingestion service with event bus integration."""
    from src.iot.esp32_connector import ESP32DataIngestionService, MQTTConfig
    
    config = MQTTConfig(
        broker_host="localhost",  # Change to your MQTT broker
        broker_port=1883,
        topic_prefix="aquawatch"
    )
    
    service = ESP32DataIngestionService(config, enable_rest_api=True)
    
    # Integrate with core orchestration if available
    def handle_reading(reading):
        logger.info(f"📊 {reading.device_id}: {reading.value} {reading.unit}")
        
        # Emit event to event bus
        if event_bus:
            event_bus.publish(
                EventType.SENSOR_DATA_RECEIVED,
                "mqtt_ingestion",
                {
                    'dma_id': reading.dma_id or 'default',
                    'sensor_id': reading.device_id,
                    'readings': {
                        reading.sensor_type: reading.value
                    }
                }
            )
        
        # Direct ingest to feature store
        if feature_store:
            feature_store.ingest_reading(
                dma_id=reading.dma_id or 'default',
                sensor_id=reading.device_id,
                readings={reading.sensor_type: reading.value}
            )
        
        # Update health monitor
        if health_monitor:
            health_monitor.update_sensor_reading(
                reading.dma_id or 'default',
                reading.device_id
            )
    
    service.add_reading_handler(handle_reading)
    service.start()
    
    logger.info("MQTT Ingestion Service started on localhost:1883")
    return service


def start_dashboard():
    """Start premium dashboard in a separate thread."""
    try:
        from src.dashboard.aquawatch_premium import app
        # Run in thread
        def run_dash():
            app.run(
                debug=False,
                host="0.0.0.0",
                port=8050
            )
        thread = threading.Thread(target=run_dash, daemon=True)
        thread.start()
        logger.info("Premium Dashboard started at http://localhost:8050")
        return thread
    except ImportError as e:
        logger.warning(f"Dashboard not available: {e}")
        return None


def start_rest_api():
    """Start REST API for ESP32 fallback."""
    try:
        import uvicorn
        from src.iot.esp32_connector import ESP32DataIngestionService, MQTTConfig, create_api_app
        
        config = MQTTConfig(broker_host="localhost")
        service = ESP32DataIngestionService(config, enable_rest_api=True)
        
        if service.api_app:
            def run_api():
                uvicorn.run(service.api_app, host="0.0.0.0", port=8000, log_level="info")
            
            thread = threading.Thread(target=run_api, daemon=True)
            thread.start()
            
            logger.info("REST API started at http://localhost:8000")
            return thread
    except ImportError as e:
        logger.warning(f"REST API not available: {e}")
    return None


def print_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║     █████╗  ██████╗ ██╗   ██╗ █████╗ ██╗    ██╗ █████╗ ████████╗    ║
    ║    ██╔══██╗██╔═══██╗██║   ██║██╔══██╗██║    ██║██╔══██╗╚══██╔══╝    ║
    ║    ███████║██║   ██║██║   ██║███████║██║ █╗ ██║███████║   ██║       ║
    ║    ██╔══██║██║▄▄ ██║██║   ██║██╔══██║██║███╗██║██╔══██║   ██║       ║
    ║    ██║  ██║╚██████╔╝╚██████╔╝██║  ██║╚███╔███╔╝██║  ██║   ██║       ║
    ║    ╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝       ║
    ║                                                                      ║
    ║              NRW Detection System - Africa Edition                   ║
    ║                    IWA Water Balance Aligned                         ║
    ║                                                                      ║
    ║          ⚡ NOW WITH CONTINUOUS AI ORCHESTRATION ⚡                   ║
    ║                                                                      ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  Core Orchestration:                                                 ║
    ║    🧠 Feature Store:    Single source of truth for all features      ║
    ║    📡 Event Bus:        Event-driven component communication         ║
    ║    🔄 Orchestrator:     Continuous 11-stage AI pipeline              ║
    ║    🏥 Health Monitor:   GREEN/AMBER/RED system health                ║
    ║                                                                      ║
    ║  Services:                                                           ║
    ║    📊 Dashboard:    http://localhost:8050                            ║
    ║    🔌 REST API:     http://localhost:8000                            ║
    ║    📡 MQTT Broker:  localhost:1883                                   ║
    ║                                                                      ║
    ║  ESP32 Topics:                                                       ║
    ║    aquawatch/{utility}/{dma}/sensors/{device}/pressure               ║
    ║    aquawatch/{utility}/{dma}/sensors/{device}/flow                   ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='AquaWatch NRW Detection System')
    parser.add_argument('--mode', choices=['full', 'simple', 'demo'], default='full',
                        help='Startup mode: full (with AI orchestration), simple (legacy), demo (simulation)')
    args = parser.parse_args()
    
    print_banner()
    
    logger.info("Starting AquaWatch NRW Detection System...")
    logger.info(f"Mode: {args.mode.upper()}")
    
    # Start services
    services = []
    
    # Core orchestration components (for full mode)
    event_bus = None
    feature_store = None
    health_monitor = None
    orchestrator = None
    system_runner = None
    
    if args.mode == 'full' and CORE_AVAILABLE:
        logger.info("\n" + "=" * 60)
        logger.info("INITIALIZING CORE ORCHESTRATION LAYER")
        logger.info("=" * 60)
        
        try:
            # Get core components
            event_bus = get_event_bus()
            feature_store = get_feature_store()
            health_monitor = get_health_monitor()
            orchestrator = get_orchestrator()
            
            # Start event bus
            event_bus.start()
            logger.info("  ✓ Event Bus started")
            services.append(("Event Bus", event_bus))
            
            # Start health monitor
            health_monitor.start()
            logger.info("  ✓ Health Monitor started")
            services.append(("Health Monitor", health_monitor))
            
            # Inject minimal components to orchestrator
            orchestrator.inject_components(
                feature_store=feature_store,
                event_bus=event_bus
            )
            
            # Start orchestrator
            orchestrator.start()
            logger.info("  ✓ System Orchestrator started (continuous AI loop)")
            services.append(("Orchestrator", orchestrator))
            
            logger.info("=" * 60)
            logger.info("CORE ORCHESTRATION LAYER READY")
            logger.info("=" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"Failed to start core orchestration: {e}")
            logger.warning("Falling back to simple mode")
            args.mode = 'simple'
    
    # 1. MQTT Ingestion
    try:
        mqtt_service = start_mqtt_ingestion(event_bus, feature_store, health_monitor)
        services.append(("MQTT Ingestion", mqtt_service))
    except Exception as e:
        logger.error(f"Failed to start MQTT service: {e}")
    
    # 2. Dashboard
    try:
        dash_thread = start_dashboard()
        if dash_thread:
            services.append(("Dashboard", dash_thread))
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
    
    # 3. REST API
    try:
        api_thread = start_rest_api()
        if api_thread:
            services.append(("REST API", api_thread))
    except Exception as e:
        logger.error(f"Failed to start REST API: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    logger.info(f"Started {len(services)} services")
    for name, svc in services:
        status = "✅ Running" if svc else "❌ Failed"
        logger.info(f"  {name}: {status}")
    
    # Show health status if available
    if health_monitor and args.mode == 'full':
        status = health_monitor.get_dashboard_status()
        print(f"\n🏥 System Health: {status['status'].upper()} - {status['message']}")
    
    print("=" * 60)
    
    # Keep running
    print("\nPress Ctrl+C to stop...")
    try:
        while True:
            time.sleep(5)
            
            # Periodic status report in full mode
            if args.mode == 'full' and health_monitor and orchestrator:
                orch_status = orchestrator.get_status()
                health_status = health_monitor.get_dashboard_status()
                
                # Only log if something interesting
                if orch_status.get('total_cycles', 0) > 0 and orch_status['total_cycles'] % 10 == 0:
                    logger.info(
                        f"📈 Orchestrator: {orch_status['total_cycles']} cycles | "
                        f"Health: {health_status['status']}"
                    )
                    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        
        # Graceful shutdown of core components
        if args.mode == 'full' and CORE_AVAILABLE:
            if orchestrator:
                orchestrator.stop()
            if health_monitor:
                health_monitor.stop()
            if event_bus:
                event_bus.stop()
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
