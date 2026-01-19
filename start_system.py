#!/usr/bin/env python3
"""
AquaWatch NRW - System Launcher
===============================

Starts all components needed for the system:
1. Python API (port 8000)
2. Next.js Dashboard (port 3001)

Run: python start_system.py
"""

import os
import sys
import subprocess
import time
import threading
import socket
import webbrowser

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print startup banner."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║   {Colors.BOLD}🌊 AQUAWATCH NRW DETECTION SYSTEM{Colors.CYAN}                          ║
║                                                                ║
║   National Water Control Room Interface                        ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")

def get_local_ip():
    """Get the local IP address for ESP32 configuration."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_api():
    """Start the Python API server."""
    print(f"{Colors.YELLOW}Starting Python API server on port 8000...{Colors.ENDC}")
    
    api_path = os.path.join(os.path.dirname(__file__), 'src', 'api', 'integrated_api.py')
    
    # Use the current Python interpreter
    process = subprocess.Popen(
        [sys.executable, api_path],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Stream output
    def stream_output():
        for line in process.stdout:
            print(f"  {Colors.BLUE}[API]{Colors.ENDC} {line.rstrip()}")
    
    thread = threading.Thread(target=stream_output, daemon=True)
    thread.start()
    
    return process

def start_dashboard():
    """Start the Next.js dashboard."""
    print(f"{Colors.YELLOW}Starting Next.js dashboard on port 3001...{Colors.ENDC}")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard')
    
    if os.name == 'nt':  # Windows
        process = subprocess.Popen(
            'npm run dev',
            cwd=dashboard_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    else:  # Linux/Mac
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=dashboard_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    
    # Stream output
    def stream_output():
        for line in process.stdout:
            print(f"  {Colors.GREEN}[DASHBOARD]{Colors.ENDC} {line.rstrip()}")
    
    thread = threading.Thread(target=stream_output, daemon=True)
    thread.start()
    
    return process

def print_esp32_config():
    """Print ESP32 configuration instructions."""
    local_ip = get_local_ip()
    
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║  ESP32 SENSOR CONFIGURATION                                    ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}Update these values in your ESP32 firmware:{Colors.ENDC}
{Colors.YELLOW}(firmware/aquawatch_sensor/aquawatch_sensor.ino){Colors.ENDC}

  const char* WIFI_SSID = "{Colors.GREEN}YOUR_WIFI_SSID{Colors.ENDC}";
  const char* WIFI_PASSWORD = "{Colors.GREEN}YOUR_WIFI_PASSWORD{Colors.ENDC}";
  const char* MQTT_BROKER = "{Colors.GREEN}{local_ip}{Colors.ENDC}";
  const char* API_HOST = "{Colors.GREEN}{local_ip}{Colors.ENDC}";
  const int API_PORT = {Colors.GREEN}8000{Colors.ENDC};

{Colors.BOLD}Sensor Data Flow:{Colors.ENDC}
  ESP32 → HTTP POST to http://{local_ip}:8000/api/sensor
  ESP32 → MQTT to {local_ip}:1883 (if MQTT broker running)

{Colors.BOLD}Test ESP32 Connection:{Colors.ENDC}
  curl -X POST http://{local_ip}:8000/api/sensor \\
    -H "Content-Type: application/json" \\
    -d '{{"pipe_id":"Pipe_TEST","pressure":42.5,"flow":15.3}}'
""")

def main():
    """Main entry point."""
    print_banner()
    
    # Check ports
    if is_port_in_use(8000):
        print(f"{Colors.YELLOW}⚠️  Port 8000 already in use (API may already be running){Colors.ENDC}")
    
    if is_port_in_use(3001):
        print(f"{Colors.YELLOW}⚠️  Port 3001 already in use (Dashboard may already be running){Colors.ENDC}")
    
    processes = []
    
    try:
        # Start API
        if not is_port_in_use(8000):
            api_process = start_api()
            processes.append(api_process)
            time.sleep(2)  # Give API time to start
        
        # Start Dashboard
        if not is_port_in_use(3001):
            dashboard_process = start_dashboard()
            processes.append(dashboard_process)
            time.sleep(3)  # Give dashboard time to compile
        
        # Print ESP32 configuration
        print_esp32_config()
        
        # Print access URLs
        local_ip = get_local_ip()
        print(f"""
{Colors.GREEN}╔══════════════════════════════════════════════════════════════╗
║  ✅ SYSTEM READY                                               ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}Access Points:{Colors.ENDC}
  📊 Dashboard:  http://localhost:3001
  📡 API:        http://localhost:8000
  
{Colors.BOLD}For ESP32/Network Access:{Colors.ENDC}
  📊 Dashboard:  http://{local_ip}:3001
  📡 API:        http://{local_ip}:8000

{Colors.BOLD}Generate Test Data:{Colors.ENDC}
  curl -X POST http://localhost:8000/api/test-data

{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.ENDC}
""")
        
        # Open browser
        try:
            time.sleep(2)
            webbrowser.open('http://localhost:3001')
        except:
            pass
        
        # Keep running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            for p in processes:
                if p.poll() is not None:
                    print(f"{Colors.RED}A process exited unexpectedly{Colors.ENDC}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.ENDC}")
        
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except:
                p.kill()
        
        print(f"{Colors.GREEN}All services stopped.{Colors.ENDC}")

if __name__ == "__main__":
    main()
