"""
AquaWatch NRW - Quick Start Launcher
=====================================

Launches all system components for development/testing.
Run this to start the complete system.

Usage:
    python start.py          # Start all services
    python start.py --api    # API only
    python start.py --dash   # Dashboard only

Services:
    - Sensor API:       http://localhost:5000
    - Main Dashboard:   http://localhost:8050
    - Admin Dashboard:  http://localhost:8060
    - Mobile App:       http://localhost:8070
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import threading
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Service configurations
SERVICES = {
    "api": {
        "name": "Sensor API",
        "module": "src.api.integrated_api",
        "port": 5000,
        "url": "http://127.0.0.1:5000"
    },
    "dashboard": {
        "name": "Main Dashboard",
        "module": "src.dashboard.app",
        "port": 8050,
        "url": "http://127.0.0.1:8050"
    },
    "admin": {
        "name": "Admin Dashboard",
        "module": "src.dashboard.admin_dashboard",
        "port": 8060,
        "url": "http://127.0.0.1:8060"
    },
    "mobile": {
        "name": "Mobile App",
        "module": "src.mobile.field_app",
        "port": 8070,
        "url": "http://127.0.0.1:8070"
    }
}

# Track running processes
processes = []


def print_banner():
    """Print startup banner."""
    print("\n" + "=" * 60)
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   🌊 AquaWatch NRW Detection System                   ║
    ║   AI-Powered Non-Revenue Water Management             ║
    ║   For Zambia & South Africa                           ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    print("=" * 60 + "\n")


def check_port_available(port):
    """Check if a port is available."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def start_service(name, module, port):
    """Start a service as a subprocess."""
    if not check_port_available(port):
        print(f"   ⚠️  Port {port} already in use, skipping {name}")
        return None
    
    cmd = [sys.executable, "-m", module]
    
    # Create startup script content
    script = f'''
import sys
sys.path.insert(0, r"{ROOT}")
try:
    from {module} import app
    if hasattr(app, "run_server"):
        app.run_server(debug=False, host="0.0.0.0", port={port})
    elif hasattr(app, "run"):
        app.run(debug=False, host="0.0.0.0", port={port})
except Exception as e:
    print(f"Error starting {name}: {{e}}")
'''
    
    # Run as python script
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(ROOT)
    )
    
    processes.append(process)
    return process


def start_service_inline(service_key):
    """Start a service in a thread."""
    config = SERVICES[service_key]
    
    if not check_port_available(config["port"]):
        print(f"   ⚠️  Port {config['port']} already in use")
        print(f"   🌐 {config['name']} may already be running at {config['url']}")
        return None
    
    def run_service():
        try:
            if service_key == "api":
                # Use integrated API with all modules connected
                from src.api.integrated_api import app
                app.run(debug=False, host="0.0.0.0", port=config["port"], threaded=True)
            elif service_key == "dashboard":
                from src.dashboard.app import app
                app.run_server(debug=False, host="0.0.0.0", port=config["port"])
            elif service_key == "admin":
                from src.dashboard.admin_dashboard import app
                app.run_server(debug=False, host="0.0.0.0", port=config["port"])
            elif service_key == "mobile":
                from src.mobile.field_app import mobile_app as app
                app.run_server(debug=False, host="0.0.0.0", port=config["port"])
        except Exception as e:
            print(f"   ❌ Error starting {config['name']}: {e}")
    
    thread = threading.Thread(target=run_service, daemon=True)
    thread.start()
    return thread


def wait_for_service(url, timeout=10):
    """Wait for a service to become available."""
    import urllib.request
    import urllib.error
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False


def signal_handler(sig, frame):
    """Handle shutdown signal."""
    print("\n\n🛑 Shutting down services...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    print("   Goodbye! 👋\n")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="AquaWatch NRW System Launcher")
    parser.add_argument("--api", action="store_true", help="Start API only")
    parser.add_argument("--dash", action="store_true", help="Start dashboard only")
    parser.add_argument("--admin", action="store_true", help="Start admin dashboard only")
    parser.add_argument("--mobile", action="store_true", help="Start mobile app only")
    args = parser.parse_args()
    
    print_banner()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Determine what to start
    if args.api:
        services_to_start = ["api"]
    elif args.dash:
        services_to_start = ["dashboard"]
    elif args.admin:
        services_to_start = ["admin"]
    elif args.mobile:
        services_to_start = ["mobile"]
    else:
        services_to_start = ["api", "dashboard", "admin"]
    
    print("🚀 Starting services...\n")
    
    started = []
    for service_key in services_to_start:
        config = SERVICES[service_key]
        print(f"   Starting {config['name']}...", end=" ", flush=True)
        
        thread = start_service_inline(service_key)
        if thread:
            time.sleep(2)  # Give service time to start
            if wait_for_service(config["url"], timeout=5):
                print(f"✅ {config['url']}")
                started.append(config)
            else:
                print(f"⏳ Starting (check {config['url']})")
                started.append(config)
        else:
            print("⚠️  Skipped")
    
    if started:
        print("\n" + "=" * 60)
        print("\n✅ System Ready!\n")
        print("📊 Available Services:")
        for config in started:
            print(f"   • {config['name']}: {config['url']}")
        
        print("\n📝 Useful Commands:")
        print("   • Ctrl+C to stop all services")
        print("   • Open dashboard in browser to view data")
        print("   • Send sensor data via API POST /api/readings")
        
        print("\n" + "=" * 60)
        print("\n⏳ Services running. Press Ctrl+C to stop.\n")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
    else:
        print("\n❌ No services started successfully.")
        print("   Check that dependencies are installed and ports are available.")


if __name__ == "__main__":
    main()
