"""
AquaWatch NRW - Complete System Runner
======================================

Runs the full system with ESP32 integration:
1. MQTT Ingestion Service (receives ESP32 data)
2. Database Storage (TimescaleDB)
3. Dashboard (Monday.com style UI)

Usage:
    python run_system.py

Requirements:
    pip install paho-mqtt psycopg2-binary dash dash-bootstrap-components plotly uvicorn fastapi
"""

import sys
import threading
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("AquaWatch")


def start_mqtt_ingestion():
    """Start MQTT ingestion service."""
    from src.iot.esp32_connector import ESP32DataIngestionService, MQTTConfig
    
    config = MQTTConfig(
        broker_host="localhost",  # Change to your MQTT broker
        broker_port=1883,
        topic_prefix="aquawatch"
    )
    
    service = ESP32DataIngestionService(config, enable_rest_api=True)
    
    # Add simple logging handler
    def log_reading(reading):
        logger.info(f"📊 {reading.device_id}: {reading.value} {reading.unit}")
    
    service.add_reading_handler(log_reading)
    service.start()
    
    logger.info("MQTT Ingestion Service started on localhost:1883")
    return service


def start_dashboard():
    """Start dashboard in a separate thread."""
    try:
        from src.dashboard.monday_style_app import create_monday_dashboard
        
        app = create_monday_dashboard()
        
        # Run in thread
        def run_dash():
            app.run_server(
                debug=False,
                host="0.0.0.0",
                port=8050,
                use_reloader=False
            )
        
        thread = threading.Thread(target=run_dash, daemon=True)
        thread.start()
        
        logger.info("Dashboard started at http://localhost:8050")
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
    ╠══════════════════════════════════════════════════════════════════════╣
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
    print_banner()
    
    logger.info("Starting AquaWatch NRW Detection System...")
    
    # Start services
    services = []
    
    # 1. MQTT Ingestion
    try:
        mqtt_service = start_mqtt_ingestion()
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
    logger.info(f"Started {len(services)} services")
    for name, svc in services:
        status = "✅ Running" if svc else "❌ Failed"
        logger.info(f"  {name}: {status}")
    
    # Keep running
    print("\nPress Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")


if __name__ == "__main__":
    main()
