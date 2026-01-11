# AquaWatch NRW - ESP32 IoT Integration
# =====================================

This module handles connectivity between ESP32 edge devices and the cloud platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIELD (Edge Layer)                                   │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐             │
│  │  ESP32    │   │  ESP32    │   │  ESP32    │   │  ESP32    │             │
│  │ Pressure  │   │  Flow     │   │  Level    │   │ Pressure  │             │
│  │  Sensor   │   │  Meter    │   │  Sensor   │   │  Sensor   │             │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘             │
│        │               │               │               │                    │
│        └───────────────┴───────────────┴───────────────┘                    │
│                                │                                            │
│                          WiFi / LoRa                                        │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                         CLOUD (Server Layer)                                │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         MQTT Broker                                   │   │
│  │                    (Mosquitto / EMQX / HiveMQ)                        │   │
│  └───────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
│  ┌───────────────────────────────▼──────────────────────────────────────┐   │
│  │              ESP32 Data Ingestion Service                             │   │
│  │                  (esp32_connector.py)                                 │   │
│  │                                                                       │   │
│  │  • Subscribes to MQTT topics                                          │   │
│  │  • Validates sensor data                                              │   │
│  │  • Handles binary/JSON formats                                        │   │
│  │  • REST API fallback                                                  │   │
│  └───────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
│  ┌───────────────────────────────▼──────────────────────────────────────┐   │
│  │                        TimescaleDB                                    │   │
│  │                  (database_handler.py)                                │   │
│  │                                                                       │   │
│  │  • Time-series optimized storage                                      │   │
│  │  • Automatic data compression                                         │   │
│  │  • Continuous aggregates                                              │   │
│  └───────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
│  ┌───────────────────────────────▼──────────────────────────────────────┐   │
│  │                      Dashboard / AI Layer                             │   │
│  │                                                                       │   │
│  │  • Real-time monitoring                                               │   │
│  │  • NRW analysis & anomaly detection                                   │   │
│  │  • Work order generation                                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## MQTT Topic Structure

```
aquawatch/
├── {utility_id}/
│   └── {dma_id}/
│       ├── sensors/
│       │   └── {device_id}/
│       │       ├── pressure     # Pressure readings (bar)
│       │       ├── flow         # Flow readings (m³/h)
│       │       ├── level        # Tank level (%)
│       │       └── status       # Device status
│       └── alerts               # Edge-detected alerts
└── commands/
    └── {device_id}              # Commands to device
```

## Message Formats

### Sensor Reading (JSON)
```json
{
  "device_id": "ESP32_001",
  "timestamp": "2026-01-05T14:30:00Z",
  "value": 4.5,
  "unit": "bar",
  "quality": "good",
  "battery_pct": 85,
  "rssi": -65,
  "seq": 12345
}
```

### Device Status
```json
{
  "device_id": "ESP32_001",
  "firmware": "1.0.0",
  "uptime_sec": 86400,
  "free_heap": 120000,
  "wifi_rssi": -65,
  "battery_v": 3.85,
  "battery_pct": 75,
  "readings_sent": 1440,
  "errors": 2
}
```

### Edge Alert
```json
{
  "type": "pressure_drop",
  "device_id": "ESP32_001",
  "timestamp": "2026-01-05T14:30:00Z",
  "value": 1.2,
  "severity": 45.5,
  "dma_id": "DMA_LUSAKA_001"
}
```

## Quick Start

### 1. Install Dependencies

```bash
pip install paho-mqtt psycopg2-binary fastapi uvicorn
```

### 2. Set Up MQTT Broker

**Option A: Mosquitto (Recommended for development)**
```bash
# Docker
docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 eclipse-mosquitto

# Or install locally
# Ubuntu: sudo apt install mosquitto mosquitto-clients
# Windows: Download from https://mosquitto.org/download/
```

**Option B: Cloud MQTT (Production)**
- HiveMQ Cloud: https://www.hivemq.com/cloud/
- EMQX Cloud: https://www.emqx.com/cloud
- AWS IoT Core

### 3. Set Up TimescaleDB

```bash
# Docker
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg14

# Create database
psql -h localhost -U postgres -c "CREATE DATABASE aquawatch"
```

### 4. Configure ESP32

Edit `firmware/esp32_sensor_node/esp32_sensor_node.ino`:

```cpp
// Device Identity
#define DEVICE_ID       "ESP32_001"
#define DMA_ID          "DMA_LUSAKA_001"
#define UTILITY_ID      "LWSC"

// WiFi
#define WIFI_SSID       "YourWiFiSSID"
#define WIFI_PASSWORD   "YourWiFiPassword"

// MQTT Broker
#define MQTT_BROKER     "192.168.1.100"
#define MQTT_PORT       1883
```

### 5. Flash ESP32

Using Arduino IDE:
1. Install ESP32 board support
2. Install libraries: PubSubClient, ArduinoJson
3. Open `esp32_sensor_node.ino`
4. Select board: ESP32 Dev Module
5. Upload

### 6. Start Ingestion Service

```python
from src.iot.esp32_connector import ESP32DataIngestionService, MQTTConfig
from src.iot.database_handler import TimescaleDBHandler, DatabaseConfig, ESP32DatabaseIntegration

# MQTT config
mqtt_config = MQTTConfig(
    broker_host="localhost",
    broker_port=1883,
    topic_prefix="aquawatch"
)

# Database config
db_config = DatabaseConfig(
    host="localhost",
    database="aquawatch",
    user="postgres",
    password="password"
)

# Initialize services
ingestion = ESP32DataIngestionService(mqtt_config)
db = TimescaleDBHandler(db_config)

# Connect
db.connect()
db.setup_schema()

# Set up integration
integration = ESP32DatabaseIntegration(ingestion.mqtt_service, db)
integration.setup()

# Start ingestion
ingestion.start()
```

## Hardware Setup

### Pressure Sensor Connection

```
ESP32          4-20mA Sensor
─────          ─────────────
GPIO34 ────────── OUT (via 250Ω resistor for voltage conversion)
GND    ────────── GND
3.3V   ────────── VCC (check sensor voltage!)
```

**250Ω Resistor**: Converts 4-20mA to 1-5V (safe for ESP32 3.3V ADC)

### Flow Sensor Connection

```
ESP32          Flow Sensor
─────          ───────────
GPIO35 ────────── PULSE OUT
GND    ────────── GND
5V     ────────── VCC
```

### Battery Monitoring

```
ESP32          Battery
─────          ───────
GPIO33 ────────── V+ (via voltage divider)
GND    ────────── V-
```

**Voltage Divider**: 100kΩ + 100kΩ for 2:1 ratio (7.4V max → 3.7V)

## Deployment Checklist

- [ ] ESP32 devices registered with unique IDs
- [ ] WiFi credentials configured
- [ ] MQTT broker deployed and secured (TLS recommended)
- [ ] TimescaleDB instance running
- [ ] Ingestion service deployed
- [ ] Dashboard connected to database
- [ ] Alerts configured in workflow engine
- [ ] Field technicians trained on device installation

## Troubleshooting

### ESP32 Not Connecting to WiFi
- Check SSID/password
- Verify WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check signal strength (move closer to router)

### ESP32 Not Publishing to MQTT
- Verify MQTT broker IP/port
- Check firewall rules (port 1883)
- Monitor broker logs: `mosquitto_sub -t '#' -v`

### Missing Data in Database
- Check ingestion service logs
- Verify database connection
- Monitor MQTT traffic: `mosquitto_sub -t 'aquawatch/#' -v`

### High Battery Drain
- Increase `SAMPLE_INTERVAL_MS`
- Enable deep sleep mode
- Check for WiFi reconnection loops

## Security Recommendations

1. **MQTT Authentication**: Always use username/password
2. **TLS Encryption**: Enable MQTT over TLS (port 8883)
3. **Device Certificates**: Use X.509 certificates for device auth
4. **Network Segmentation**: IoT devices on separate VLAN
5. **Firmware Signing**: Sign OTA updates
