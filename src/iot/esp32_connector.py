"""
AquaWatch NRW - ESP32 IoT Connectivity Layer
=============================================

Handles communication between ESP32 edge devices and the cloud platform.

Communication Methods:
1. MQTT (Primary) - Real-time sensor data streaming
2. HTTP REST API (Backup) - For areas with limited MQTT support
3. WebSocket - For dashboard real-time updates

Data Flow:
ESP32 → MQTT Broker → Ingestion Service → TimescaleDB → Dashboard

IWA Water Balance Aligned - All sensor data tagged with:
- DMA ID
- Sensor type (pressure/flow/level)
- Timestamp (NTP synchronized)
- Quality flags
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import struct
import hashlib

# MQTT client (paho-mqtt)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not installed. Run: pip install paho-mqtt")

# FastAPI for REST endpoints
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MQTTConfig:
    """MQTT Broker Configuration."""
    broker_host: str = "localhost"
    broker_port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    ca_cert_path: Optional[str] = None
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None
    keepalive: int = 60
    qos: int = 1  # At least once delivery
    
    # Topic structure
    topic_prefix: str = "aquawatch"
    # Full topics:
    # aquawatch/{utility_id}/{dma_id}/sensors/{sensor_id}/pressure
    # aquawatch/{utility_id}/{dma_id}/sensors/{sensor_id}/flow
    # aquawatch/{utility_id}/{dma_id}/sensors/{sensor_id}/status
    # aquawatch/{utility_id}/{dma_id}/alerts


@dataclass
class ESP32Config:
    """ESP32 Device Configuration."""
    device_id: str
    dma_id: str
    utility_id: str
    sensor_type: str  # "pressure", "flow", "level"
    firmware_version: str = "1.0.0"
    sample_interval_sec: int = 60  # Default 1 minute
    transmit_interval_sec: int = 300  # Default 5 minutes (batch)
    wifi_ssid: str = ""
    wifi_password: str = ""
    mqtt_config: MQTTConfig = field(default_factory=MQTTConfig)


# =============================================================================
# DATA MODELS
# =============================================================================

class SensorType(Enum):
    """Types of sensors supported."""
    PRESSURE = "pressure"
    FLOW = "flow"
    LEVEL = "level"
    QUALITY = "quality"


class DataQuality(Enum):
    """Data quality flags."""
    GOOD = "good"
    SUSPECT = "suspect"  # Out of expected range
    BAD = "bad"          # Sensor fault
    STALE = "stale"      # No recent update


@dataclass
class SensorReading:
    """
    Sensor reading from ESP32 device.
    
    Compact format for efficient transmission over low-bandwidth connections.
    """
    device_id: str
    sensor_type: SensorType
    timestamp: datetime
    value: float
    unit: str
    quality: DataQuality = DataQuality.GOOD
    battery_pct: Optional[float] = None
    signal_strength: Optional[int] = None  # RSSI in dBm
    
    # Metadata
    dma_id: Optional[str] = None
    utility_id: Optional[str] = None
    sequence_num: int = 0
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "device_id": self.device_id,
            "sensor_type": self.sensor_type.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality.value,
            "battery_pct": self.battery_pct,
            "signal_strength": self.signal_strength,
            "dma_id": self.dma_id,
            "utility_id": self.utility_id,
            "seq": self.sequence_num
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SensorReading':
        """Parse from JSON string."""
        data = json.loads(json_str)
        return cls(
            device_id=data["device_id"],
            sensor_type=SensorType(data["sensor_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            value=data["value"],
            unit=data["unit"],
            quality=DataQuality(data.get("quality", "good")),
            battery_pct=data.get("battery_pct"),
            signal_strength=data.get("signal_strength"),
            dma_id=data.get("dma_id"),
            utility_id=data.get("utility_id"),
            sequence_num=data.get("seq", 0)
        )
    
    def to_binary(self) -> bytes:
        """
        Convert to compact binary format for low-bandwidth transmission.
        
        Format (24 bytes):
        - 4 bytes: device_id hash (uint32)
        - 4 bytes: timestamp (uint32, unix epoch)
        - 4 bytes: value (float32)
        - 1 byte: sensor_type (uint8)
        - 1 byte: quality (uint8)
        - 1 byte: battery_pct (uint8, 0-100)
        - 1 byte: signal_strength (int8, dBm + 128)
        - 4 bytes: sequence_num (uint32)
        - 4 bytes: CRC32 checksum
        """
        device_hash = struct.unpack('I', hashlib.md5(self.device_id.encode()).digest()[:4])[0]
        timestamp_unix = int(self.timestamp.timestamp())
        sensor_type_int = list(SensorType).index(self.sensor_type)
        quality_int = list(DataQuality).index(self.quality)
        battery = int(self.battery_pct or 0)
        signal = int((self.signal_strength or -128) + 128)
        
        # Pack data
        data = struct.pack(
            '<IIfBBBBI',
            device_hash,
            timestamp_unix,
            self.value,
            sensor_type_int,
            quality_int,
            battery,
            signal,
            self.sequence_num
        )
        
        # Add CRC32
        import zlib
        crc = zlib.crc32(data) & 0xFFFFFFFF
        return data + struct.pack('<I', crc)


@dataclass
class DeviceStatus:
    """ESP32 device status report."""
    device_id: str
    timestamp: datetime
    firmware_version: str
    uptime_seconds: int
    free_heap_bytes: int
    wifi_rssi: int
    battery_voltage: float
    battery_pct: float
    last_reading_time: Optional[datetime] = None
    readings_sent: int = 0
    errors_count: int = 0
    
    def to_json(self) -> str:
        return json.dumps({
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "firmware": self.firmware_version,
            "uptime_sec": self.uptime_seconds,
            "free_heap": self.free_heap_bytes,
            "wifi_rssi": self.wifi_rssi,
            "battery_v": self.battery_voltage,
            "battery_pct": self.battery_pct,
            "readings_sent": self.readings_sent,
            "errors": self.errors_count
        })


# =============================================================================
# MQTT DATA INGESTION SERVICE
# =============================================================================

class MQTTIngestionService:
    """
    MQTT-based data ingestion from ESP32 devices.
    
    Subscribes to sensor data topics and processes incoming readings.
    """
    
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.readings_buffer: List[SensorReading] = []
        self.buffer_lock = asyncio.Lock() if asyncio else None
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "errors": 0,
            "connected_since": None
        }
        
        # Callbacks for data processing
        self.on_reading_received: Optional[Callable[[SensorReading], None]] = None
        self.on_device_status: Optional[Callable[[DeviceStatus], None]] = None
        self.on_alert: Optional[Callable[[Dict], None]] = None
    
    def connect(self) -> bool:
        """Connect to MQTT broker."""
        if not MQTT_AVAILABLE:
            logger.error("paho-mqtt not installed")
            return False
        
        try:
            self.client = mqtt.Client(
                client_id=f"aquawatch-ingestion-{datetime.now().timestamp():.0f}",
                protocol=mqtt.MQTTv311
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Authentication
            if self.config.username and self.config.password:
                self.client.username_pw_set(self.config.username, self.config.password)
            
            # TLS
            if self.config.use_tls:
                self.client.tls_set(
                    ca_certs=self.config.ca_cert_path,
                    certfile=self.config.client_cert_path,
                    keyfile=self.config.client_key_path
                )
            
            # Connect
            self.client.connect(
                self.config.broker_host,
                self.config.broker_port,
                self.config.keepalive
            )
            
            # Start loop in background
            self.client.loop_start()
            
            logger.info(f"Connecting to MQTT broker at {self.config.broker_host}:{self.config.broker_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self.connected = True
            self.stats["connected_since"] = datetime.now()
            logger.info("Connected to MQTT broker")
            
            # Subscribe to all sensor topics
            topics = [
                (f"{self.config.topic_prefix}/+/+/sensors/+/pressure", self.config.qos),
                (f"{self.config.topic_prefix}/+/+/sensors/+/flow", self.config.qos),
                (f"{self.config.topic_prefix}/+/+/sensors/+/level", self.config.qos),
                (f"{self.config.topic_prefix}/+/+/sensors/+/status", self.config.qos),
                (f"{self.config.topic_prefix}/+/+/alerts", self.config.qos),
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")
        
        # Attempt reconnect
        if rc != 0:
            logger.info("Attempting to reconnect...")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        self.stats["messages_received"] += 1
        
        try:
            # Parse topic to extract metadata
            # Format: aquawatch/{utility_id}/{dma_id}/sensors/{sensor_id}/{type}
            parts = msg.topic.split('/')
            
            if len(parts) >= 6 and parts[3] == "sensors":
                utility_id = parts[1]
                dma_id = parts[2]
                sensor_id = parts[4]
                data_type = parts[5]
                
                if data_type in ["pressure", "flow", "level"]:
                    self._process_sensor_reading(msg.payload, utility_id, dma_id, sensor_id, data_type)
                elif data_type == "status":
                    self._process_device_status(msg.payload, sensor_id)
            
            elif len(parts) >= 4 and parts[3] == "alerts":
                self._process_alert(msg.payload, parts[1], parts[2])
            
            self.stats["messages_processed"] += 1
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error processing message from {msg.topic}: {e}")
    
    def _process_sensor_reading(self, payload: bytes, utility_id: str, dma_id: str, 
                                sensor_id: str, data_type: str):
        """Process sensor reading from ESP32."""
        try:
            # Try JSON first
            data = json.loads(payload.decode('utf-8'))
            
            reading = SensorReading(
                device_id=sensor_id,
                sensor_type=SensorType(data_type),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
                value=float(data["value"]),
                unit=data.get("unit", "bar" if data_type == "pressure" else "m3/h"),
                quality=DataQuality(data.get("quality", "good")),
                battery_pct=data.get("battery_pct"),
                signal_strength=data.get("rssi"),
                dma_id=dma_id,
                utility_id=utility_id,
                sequence_num=data.get("seq", 0)
            )
            
            # Validate reading
            if self._validate_reading(reading):
                if self.on_reading_received:
                    self.on_reading_received(reading)
                
                logger.debug(f"Processed reading: {sensor_id} = {reading.value} {reading.unit}")
            
        except json.JSONDecodeError:
            # Try binary format
            if len(payload) == 24:
                reading = self._parse_binary_reading(payload, sensor_id, dma_id, utility_id)
                if reading and self.on_reading_received:
                    self.on_reading_received(reading)
            else:
                logger.warning(f"Unknown payload format from {sensor_id}")
    
    def _parse_binary_reading(self, payload: bytes, sensor_id: str, 
                              dma_id: str, utility_id: str) -> Optional[SensorReading]:
        """Parse binary format sensor reading."""
        try:
            import zlib
            
            # Verify CRC
            data = payload[:-4]
            crc_received = struct.unpack('<I', payload[-4:])[0]
            crc_calculated = zlib.crc32(data) & 0xFFFFFFFF
            
            if crc_received != crc_calculated:
                logger.warning(f"CRC mismatch for reading from {sensor_id}")
                return None
            
            # Unpack data
            device_hash, timestamp_unix, value, sensor_type_int, quality_int, \
                battery, signal, sequence_num = struct.unpack('<IIfBBBBI', data)
            
            return SensorReading(
                device_id=sensor_id,
                sensor_type=list(SensorType)[sensor_type_int],
                timestamp=datetime.fromtimestamp(timestamp_unix, tz=timezone.utc),
                value=value,
                unit="bar",  # Default, should be determined by sensor_type
                quality=list(DataQuality)[quality_int],
                battery_pct=battery,
                signal_strength=signal - 128,
                dma_id=dma_id,
                utility_id=utility_id,
                sequence_num=sequence_num
            )
            
        except Exception as e:
            logger.error(f"Failed to parse binary reading: {e}")
            return None
    
    def _validate_reading(self, reading: SensorReading) -> bool:
        """Validate sensor reading for plausibility."""
        
        # Pressure validation (typical water network: 0-16 bar)
        if reading.sensor_type == SensorType.PRESSURE:
            if not 0 <= reading.value <= 20:
                reading.quality = DataQuality.SUSPECT
                logger.warning(f"Suspect pressure reading: {reading.value} bar from {reading.device_id}")
        
        # Flow validation
        elif reading.sensor_type == SensorType.FLOW:
            if reading.value < 0:
                reading.quality = DataQuality.BAD
                logger.warning(f"Negative flow reading from {reading.device_id}")
                return False
        
        # Level validation
        elif reading.sensor_type == SensorType.LEVEL:
            if not 0 <= reading.value <= 100:
                reading.quality = DataQuality.SUSPECT
        
        return True
    
    def _process_device_status(self, payload: bytes, device_id: str):
        """Process device status report."""
        try:
            data = json.loads(payload.decode('utf-8'))
            
            status = DeviceStatus(
                device_id=device_id,
                timestamp=datetime.now(timezone.utc),
                firmware_version=data.get("firmware", "unknown"),
                uptime_seconds=data.get("uptime_sec", 0),
                free_heap_bytes=data.get("free_heap", 0),
                wifi_rssi=data.get("wifi_rssi", -100),
                battery_voltage=data.get("battery_v", 0),
                battery_pct=data.get("battery_pct", 0),
                readings_sent=data.get("readings_sent", 0),
                errors_count=data.get("errors", 0)
            )
            
            if self.on_device_status:
                self.on_device_status(status)
                
            logger.info(f"Device status: {device_id} - uptime: {status.uptime_seconds}s, battery: {status.battery_pct}%")
            
        except Exception as e:
            logger.error(f"Failed to process device status: {e}")
    
    def _process_alert(self, payload: bytes, utility_id: str, dma_id: str):
        """Process alert from edge device."""
        try:
            data = json.loads(payload.decode('utf-8'))
            data["utility_id"] = utility_id
            data["dma_id"] = dma_id
            
            if self.on_alert:
                self.on_alert(data)
                
            logger.warning(f"Edge alert received: {data.get('type', 'unknown')} from {dma_id}")
            
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
    
    def publish_command(self, device_id: str, command: Dict) -> bool:
        """
        Send command to ESP32 device.
        
        Commands:
        - {"cmd": "reboot"} - Reboot device
        - {"cmd": "config", "interval": 60} - Update sample interval
        - {"cmd": "calibrate", "offset": 0.1} - Apply calibration offset
        - {"cmd": "ota", "url": "..."} - Trigger OTA update
        """
        if not self.connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        topic = f"{self.config.topic_prefix}/commands/{device_id}"
        payload = json.dumps(command)
        
        result = self.client.publish(topic, payload, qos=self.config.qos)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def get_stats(self) -> Dict:
        """Get ingestion statistics."""
        return {
            **self.stats,
            "connected": self.connected,
            "buffer_size": len(self.readings_buffer)
        }


# =============================================================================
# REST API ENDPOINTS (Backup for ESP32)
# =============================================================================

if FASTAPI_AVAILABLE:
    
    class SensorReadingRequest(BaseModel):
        """REST API request model for sensor reading."""
        device_id: str
        sensor_type: str
        value: float
        unit: str = "bar"
        timestamp: Optional[str] = None
        quality: str = "good"
        battery_pct: Optional[float] = None
        rssi: Optional[int] = None
        dma_id: Optional[str] = None
        utility_id: Optional[str] = None
    
    class DeviceStatusRequest(BaseModel):
        """REST API request model for device status."""
        device_id: str
        firmware: str
        uptime_sec: int
        free_heap: int
        wifi_rssi: int
        battery_v: float
        battery_pct: float
    
    def create_api_app(ingestion_service: MQTTIngestionService) -> FastAPI:
        """Create FastAPI application for REST API fallback."""
        
        app = FastAPI(
            title="AquaWatch NRW - ESP32 Data API",
            description="REST API for ESP32 sensor data ingestion",
            version="1.0.0"
        )
        
        @app.post("/api/v1/readings")
        async def post_reading(reading: SensorReadingRequest, background_tasks: BackgroundTasks):
            """
            Submit sensor reading via REST API.
            
            Use this endpoint when MQTT is unavailable.
            """
            try:
                sensor_reading = SensorReading(
                    device_id=reading.device_id,
                    sensor_type=SensorType(reading.sensor_type),
                    timestamp=datetime.fromisoformat(reading.timestamp) if reading.timestamp 
                              else datetime.now(timezone.utc),
                    value=reading.value,
                    unit=reading.unit,
                    quality=DataQuality(reading.quality),
                    battery_pct=reading.battery_pct,
                    signal_strength=reading.rssi,
                    dma_id=reading.dma_id,
                    utility_id=reading.utility_id
                )
                
                # Process in background
                if ingestion_service.on_reading_received:
                    background_tasks.add_task(ingestion_service.on_reading_received, sensor_reading)
                
                return {"status": "accepted", "device_id": reading.device_id}
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.post("/api/v1/readings/batch")
        async def post_readings_batch(readings: List[SensorReadingRequest], 
                                      background_tasks: BackgroundTasks):
            """
            Submit batch of sensor readings.
            
            Efficient for ESP32 devices that buffer readings.
            """
            processed = 0
            for reading in readings:
                try:
                    sensor_reading = SensorReading(
                        device_id=reading.device_id,
                        sensor_type=SensorType(reading.sensor_type),
                        timestamp=datetime.fromisoformat(reading.timestamp) if reading.timestamp 
                                  else datetime.now(timezone.utc),
                        value=reading.value,
                        unit=reading.unit,
                        quality=DataQuality(reading.quality),
                        battery_pct=reading.battery_pct,
                        signal_strength=reading.rssi,
                        dma_id=reading.dma_id,
                        utility_id=reading.utility_id
                    )
                    
                    if ingestion_service.on_reading_received:
                        background_tasks.add_task(ingestion_service.on_reading_received, sensor_reading)
                    
                    processed += 1
                except Exception:
                    continue
            
            return {"status": "accepted", "processed": processed, "total": len(readings)}
        
        @app.post("/api/v1/status")
        async def post_device_status(status: DeviceStatusRequest):
            """Submit device status report."""
            try:
                device_status = DeviceStatus(
                    device_id=status.device_id,
                    timestamp=datetime.now(timezone.utc),
                    firmware_version=status.firmware,
                    uptime_seconds=status.uptime_sec,
                    free_heap_bytes=status.free_heap,
                    wifi_rssi=status.wifi_rssi,
                    battery_voltage=status.battery_v,
                    battery_pct=status.battery_pct
                )
                
                if ingestion_service.on_device_status:
                    ingestion_service.on_device_status(device_status)
                
                return {"status": "accepted", "device_id": status.device_id}
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/api/v1/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "mqtt_connected": ingestion_service.connected,
                "stats": ingestion_service.get_stats()
            }
        
        return app


# =============================================================================
# MAIN INGESTION SERVICE
# =============================================================================

class ESP32DataIngestionService:
    """
    Main service for ingesting data from ESP32 devices.
    
    Manages both MQTT and REST API connections.
    """
    
    def __init__(self, mqtt_config: MQTTConfig, enable_rest_api: bool = True):
        self.mqtt_service = MQTTIngestionService(mqtt_config)
        self.enable_rest_api = enable_rest_api
        self.api_app = None
        
        # Data handlers
        self.reading_handlers: List[Callable[[SensorReading], None]] = []
        self.status_handlers: List[Callable[[DeviceStatus], None]] = []
        
        # Set up MQTT callbacks
        self.mqtt_service.on_reading_received = self._handle_reading
        self.mqtt_service.on_device_status = self._handle_status
    
    def add_reading_handler(self, handler: Callable[[SensorReading], None]):
        """Add handler for incoming sensor readings."""
        self.reading_handlers.append(handler)
    
    def add_status_handler(self, handler: Callable[[DeviceStatus], None]):
        """Add handler for device status updates."""
        self.status_handlers.append(handler)
    
    def _handle_reading(self, reading: SensorReading):
        """Process incoming reading through all handlers."""
        for handler in self.reading_handlers:
            try:
                handler(reading)
            except Exception as e:
                logger.error(f"Reading handler error: {e}")
    
    def _handle_status(self, status: DeviceStatus):
        """Process device status through all handlers."""
        for handler in self.status_handlers:
            try:
                handler(status)
            except Exception as e:
                logger.error(f"Status handler error: {e}")
    
    def start(self):
        """Start the ingestion service."""
        # Connect MQTT
        self.mqtt_service.connect()
        
        # Create REST API if enabled
        if self.enable_rest_api and FASTAPI_AVAILABLE:
            self.api_app = create_api_app(self.mqtt_service)
            logger.info("REST API created (use uvicorn to serve)")
    
    def stop(self):
        """Stop the ingestion service."""
        self.mqtt_service.disconnect()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_reading_handler(reading: SensorReading):
    """Example handler that prints readings."""
    print(f"📊 [{reading.timestamp}] {reading.device_id}: {reading.value} {reading.unit} ({reading.quality.value})")


def example_status_handler(status: DeviceStatus):
    """Example handler for device status."""
    print(f"📱 Device {status.device_id}: Battery {status.battery_pct}%, RSSI {status.wifi_rssi}dBm")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create configuration
    config = MQTTConfig(
        broker_host="localhost",  # Use your MQTT broker
        broker_port=1883,
        topic_prefix="aquawatch"
    )
    
    # Create ingestion service
    service = ESP32DataIngestionService(config)
    
    # Add handlers
    service.add_reading_handler(example_reading_handler)
    service.add_status_handler(example_status_handler)
    
    # Start service
    print("Starting ESP32 Data Ingestion Service...")
    print("Listening for MQTT messages on aquawatch/+/+/sensors/#")
    print("REST API available at /api/v1/readings")
    
    service.start()
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping service...")
        service.stop()
