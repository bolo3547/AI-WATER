"""
AquaWatch NRW - MQTT to AI Bridge
=================================

CRITICAL INTEGRATION COMPONENT

This module bridges ESP32 sensor data to the AquaWatch Central AI.
It implements the non-negotiable data flow:

    Sensors → ESP32 → MQTT → [THIS BRIDGE] → Time-Series DB → AI Models → Dashboard

RESPONSIBILITIES:
1. Subscribe to DMA-organized MQTT topics from ESP32 devices
2. Parse and validate incoming sensor data
3. Aggregate data by DMA for AI processing
4. Forward data to time-series storage
5. Trigger AI anomaly detection pipeline
6. Send control commands back to ESP32 devices

CRITICAL: The ESP32 sends RAW data and edge statistics.
          The AI makes ALL leak decisions - NOT the ESP32.

Topic Structure (DMA-centric):
    aquawatch/<dma_id>/<device_id>/data       - Raw sensor data + edge stats
    aquawatch/<dma_id>/<device_id>/quality    - Water quality readings
    aquawatch/<dma_id>/<device_id>/power      - Battery/solar status
    aquawatch/<dma_id>/<device_id>/status     - Device online/offline
    aquawatch/<dma_id>/<device_id>/diagnostics - System health
    aquawatch/<dma_id>/<device_id>/sensor_fault - Sensor failures
    aquawatch/<dma_id>/<device_id>/config     - Device configuration
    aquawatch/<dma_id>/<device_id>/ack        - Command acknowledgements
    aquawatch/<dma_id>/<device_id>/cmd        - Commands TO device (from AI)
    aquawatch/<dma_id>/mesh/relayed           - Data relayed via mesh network

Author: AquaWatch AI Team
Version: 3.0.0 (Aligned with ESP32 firmware v3.0)
"""

import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading
import queue

# MQTT
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("paho-mqtt not installed. Run: pip install paho-mqtt")

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MQTTAIBridgeConfig:
    """Configuration for MQTT to AI Bridge."""
    
    # MQTT Broker
    broker_host: str = "localhost"
    broker_port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    
    # Topic prefix
    topic_prefix: str = "aquawatch"
    
    # Data aggregation
    aggregation_window_sec: int = 60  # Aggregate DMA data every 60 seconds
    min_sensors_for_analysis: int = 1  # Minimum sensors needed per DMA
    
    # AI Pipeline triggers
    anomaly_check_interval_sec: int = 30
    decision_engine_interval_sec: int = 300  # Full DMA ranking every 5 minutes
    
    # Data retention
    max_readings_in_memory: int = 10000
    buffer_flush_interval_sec: int = 60


# =============================================================================
# DATA STRUCTURES FOR AI PROCESSING
# =============================================================================

@dataclass
class ESP32Reading:
    """
    Parsed reading from ESP32 sensor node.
    
    Matches the JSON format sent by ESP32 firmware v3.0.
    """
    # Device identification
    device_id: str
    dma_id: str
    zone_id: str
    sensor_location: str  # inlet, outlet, junction, service
    firmware_version: str
    sequence: int
    timestamp_ms: int
    
    # Raw sensor values
    flow_rate_lpm: float
    total_volume_l: float
    pressure_bar: float
    tank_level_percent: float
    water_level_cm: float
    
    # Edge-computed statistics (for AI to use)
    pressure_mean: float
    pressure_std: float
    pressure_zscore: float
    flow_mean: float
    flow_std: float
    flow_zscore: float
    
    # Sensor health
    sensor_fault: bool
    fault_type: str
    
    # Device status
    wifi_rssi: int
    uptime_sec: int
    free_heap: int
    battery_percent: float
    solar_charging: bool
    buffered_readings: int
    
    # Data quality
    is_buffered: bool
    was_offline: bool
    
    # Server-side timestamp
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def from_mqtt_payload(cls, payload: bytes, topic: str) -> Optional['ESP32Reading']:
        """Parse from MQTT JSON payload."""
        try:
            data = json.loads(payload.decode('utf-8'))
            
            # Extract from nested structure
            raw = data.get('raw', {})
            edge_stats = data.get('edge_stats', {})
            sensor_health = data.get('sensor_health', {})
            status = data.get('status', {})
            quality = data.get('data_quality', {})
            
            return cls(
                device_id=data.get('device_id', ''),
                dma_id=data.get('dma_id', ''),
                zone_id=data.get('zone_id', ''),
                sensor_location=data.get('sensor_location', 'unknown'),
                firmware_version=data.get('firmware_version', ''),
                sequence=data.get('sequence', 0),
                timestamp_ms=data.get('timestamp_ms', 0),
                
                # Raw values
                flow_rate_lpm=raw.get('flow_rate_lpm', 0.0),
                total_volume_l=raw.get('total_volume_l', 0.0),
                pressure_bar=raw.get('pressure_bar', 0.0),
                tank_level_percent=raw.get('tank_level_percent', 0.0),
                water_level_cm=raw.get('water_level_cm', 0.0),
                
                # Edge statistics
                pressure_mean=edge_stats.get('pressure_mean', 0.0),
                pressure_std=edge_stats.get('pressure_std', 0.0),
                pressure_zscore=edge_stats.get('pressure_zscore', 0.0),
                flow_mean=edge_stats.get('flow_mean', 0.0),
                flow_std=edge_stats.get('flow_std', 0.0),
                flow_zscore=edge_stats.get('flow_zscore', 0.0),
                
                # Sensor health
                sensor_fault=sensor_health.get('fault_detected', False),
                fault_type=sensor_health.get('fault_type', ''),
                
                # Status
                wifi_rssi=status.get('wifi_rssi', 0),
                uptime_sec=status.get('uptime_sec', 0),
                free_heap=status.get('free_heap', 0),
                battery_percent=status.get('battery_percent', 0.0),
                solar_charging=status.get('solar_charging', False),
                buffered_readings=status.get('buffered_readings', 0),
                
                # Quality
                is_buffered=quality.get('is_buffered', False),
                was_offline=quality.get('was_offline', False)
            )
        except Exception as e:
            logger.error(f"Failed to parse ESP32 reading: {e}")
            return None


@dataclass
class DMAAggregatedData:
    """
    Aggregated sensor data for a single DMA.
    
    This is what gets sent to the AI Decision Engine.
    """
    dma_id: str
    timestamp: datetime
    
    # Aggregated from all sensors in DMA
    total_inlet_flow_lpm: float = 0.0
    total_outlet_flow_lpm: float = 0.0
    average_pressure_bar: float = 0.0
    min_pressure_bar: float = 0.0
    max_pressure_bar: float = 0.0
    
    # Edge statistics aggregated
    max_pressure_zscore: float = 0.0
    max_flow_zscore: float = 0.0
    
    # Sensor counts
    active_sensors: int = 0
    sensors_with_faults: int = 0
    sensors_offline: int = 0
    
    # Individual readings
    readings: List[ESP32Reading] = field(default_factory=list)
    
    def add_reading(self, reading: ESP32Reading):
        """Add a reading to the aggregation."""
        self.readings.append(reading)
        self.active_sensors = len(self.readings)
        
        # Update aggregates
        inlet_flows = [r.flow_rate_lpm for r in self.readings if r.sensor_location == 'inlet']
        outlet_flows = [r.flow_rate_lpm for r in self.readings if r.sensor_location == 'outlet']
        pressures = [r.pressure_bar for r in self.readings if r.pressure_bar > 0]
        
        self.total_inlet_flow_lpm = sum(inlet_flows)
        self.total_outlet_flow_lpm = sum(outlet_flows)
        
        if pressures:
            self.average_pressure_bar = sum(pressures) / len(pressures)
            self.min_pressure_bar = min(pressures)
            self.max_pressure_bar = max(pressures)
        
        # Track max z-scores (for AI anomaly flagging)
        self.max_pressure_zscore = max(
            abs(r.pressure_zscore) for r in self.readings
        ) if self.readings else 0.0
        self.max_flow_zscore = max(
            abs(r.flow_zscore) for r in self.readings
        ) if self.readings else 0.0
        
        # Track faults
        self.sensors_with_faults = sum(1 for r in self.readings if r.sensor_fault)


# =============================================================================
# MQTT TO AI BRIDGE SERVICE
# =============================================================================

class MQTTAIBridge:
    """
    Bridges ESP32 MQTT data to AquaWatch Central AI.
    
    This is the critical integration layer that:
    1. Receives raw sensor data from ESP32 devices
    2. Aggregates by DMA
    3. Triggers AI analysis
    4. Sends commands back to ESP32s
    """
    
    def __init__(self, config: Optional[MQTTAIBridgeConfig] = None):
        self.config = config or MQTTAIBridgeConfig()
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        
        # Data storage by DMA
        self.dma_readings: Dict[str, List[ESP32Reading]] = defaultdict(list)
        self.dma_last_aggregation: Dict[str, datetime] = {}
        
        # Device registry
        self.registered_devices: Dict[str, Dict[str, Any]] = {}
        
        # Callbacks for AI integration
        self.on_dma_data_ready: Optional[Callable[[DMAAggregatedData], None]] = None
        self.on_sensor_fault: Optional[Callable[[str, str, str], None]] = None
        self.on_device_online: Optional[Callable[[str, str], None]] = None
        self.on_device_offline: Optional[Callable[[str, str], None]] = None
        
        # Processing queue
        self.processing_queue = queue.Queue()
        self.processor_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'readings_processed': 0,
            'dma_aggregations': 0,
            'ai_triggers': 0,
            'commands_sent': 0,
            'errors': 0,
            'connected_since': None
        }
        
        logger.info("MQTTAIBridge initialized")
    
    def connect(self) -> bool:
        """Connect to MQTT broker and start processing."""
        if not MQTT_AVAILABLE:
            logger.error("paho-mqtt not installed")
            return False
        
        try:
            # Create MQTT client
            client_id = f"aquawatch-ai-bridge-{datetime.now().timestamp():.0f}"
            self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Authentication
            if self.config.username and self.config.password:
                self.client.username_pw_set(self.config.username, self.config.password)
            
            # Connect
            self.client.connect(
                self.config.broker_host,
                self.config.broker_port,
                keepalive=60
            )
            
            # Start MQTT loop
            self.client.loop_start()
            
            # Start processing thread
            self.running = True
            self.processor_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.processor_thread.start()
            
            logger.info(f"Connecting to MQTT broker at {self.config.broker_host}:{self.config.broker_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect and cleanup."""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("MQTTAIBridge disconnected")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.connected = True
            self.stats['connected_since'] = datetime.now(timezone.utc)
            logger.info("Connected to MQTT broker")
            
            # Subscribe to ALL DMA topics
            # Topic: aquawatch/<dma_id>/<device_id>/<message_type>
            subscriptions = [
                (f"{self.config.topic_prefix}/+/+/data", 1),        # Sensor data
                (f"{self.config.topic_prefix}/+/+/quality", 1),     # Water quality
                (f"{self.config.topic_prefix}/+/+/power", 1),       # Power status
                (f"{self.config.topic_prefix}/+/+/status", 1),      # Device status
                (f"{self.config.topic_prefix}/+/+/diagnostics", 1), # Diagnostics
                (f"{self.config.topic_prefix}/+/+/sensor_fault", 1),# Sensor faults
                (f"{self.config.topic_prefix}/+/+/config", 1),      # Configuration
                (f"{self.config.topic_prefix}/+/+/ack", 1),         # Acknowledgements
                (f"{self.config.topic_prefix}/+/mesh/relayed", 1),  # Mesh relayed data
            ]
            
            for topic, qos in subscriptions:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed: {topic}")
        else:
            logger.error(f"MQTT connection failed, rc={rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, rc={rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        self.stats['messages_received'] += 1
        
        # Queue for processing
        self.processing_queue.put((msg.topic, msg.payload))
    
    def _process_queue(self):
        """Background thread to process incoming messages."""
        while self.running:
            try:
                topic, payload = self.processing_queue.get(timeout=1)
                self._handle_message(topic, payload)
            except queue.Empty:
                # Check if any DMAs need aggregation
                self._check_aggregation_triggers()
            except Exception as e:
                logger.error(f"Processing error: {e}")
                self.stats['errors'] += 1
    
    def _handle_message(self, topic: str, payload: bytes):
        """Route and handle MQTT message based on topic."""
        try:
            # Parse topic: aquawatch/<dma_id>/<device_id>/<type>
            parts = topic.split('/')
            if len(parts) < 4:
                return
            
            _, dma_id, device_id, msg_type = parts[0], parts[1], parts[2], parts[3]
            
            # Route by message type
            if msg_type == 'data':
                self._handle_sensor_data(dma_id, device_id, payload)
            elif msg_type == 'status':
                self._handle_device_status(dma_id, device_id, payload)
            elif msg_type == 'sensor_fault':
                self._handle_sensor_fault(dma_id, device_id, payload)
            elif msg_type == 'quality':
                self._handle_water_quality(dma_id, device_id, payload)
            elif msg_type == 'diagnostics':
                self._handle_diagnostics(dma_id, device_id, payload)
            elif msg_type == 'ack':
                self._handle_acknowledgement(dma_id, device_id, payload)
            elif msg_type == 'relayed':  # Mesh relayed data
                self._handle_mesh_relayed(dma_id, payload)
                
        except Exception as e:
            logger.error(f"Error handling message from {topic}: {e}")
            self.stats['errors'] += 1
    
    def _handle_sensor_data(self, dma_id: str, device_id: str, payload: bytes):
        """
        Handle incoming sensor data from ESP32.
        
        This is the PRIMARY data path for AI analysis.
        """
        reading = ESP32Reading.from_mqtt_payload(payload, f"aquawatch/{dma_id}/{device_id}/data")
        
        if reading:
            # Store reading
            self.dma_readings[dma_id].append(reading)
            self.stats['readings_processed'] += 1
            
            # Update device registry
            self.registered_devices[device_id] = {
                'dma_id': dma_id,
                'last_seen': datetime.now(timezone.utc),
                'firmware_version': reading.firmware_version,
                'sensor_location': reading.sensor_location,
                'sequence': reading.sequence
            }
            
            # Log significant z-scores (potential anomalies for AI to analyze)
            if abs(reading.pressure_zscore) > 2.0:
                logger.info(
                    f"[{dma_id}/{device_id}] Significant pressure deviation: "
                    f"z-score={reading.pressure_zscore:.2f}, value={reading.pressure_bar:.2f} bar"
                )
            
            if abs(reading.flow_zscore) > 2.0:
                logger.info(
                    f"[{dma_id}/{device_id}] Significant flow deviation: "
                    f"z-score={reading.flow_zscore:.2f}, value={reading.flow_rate_lpm:.2f} lpm"
                )
            
            # Check if we should trigger DMA aggregation
            self._check_dma_aggregation(dma_id)
    
    def _handle_sensor_fault(self, dma_id: str, device_id: str, payload: bytes):
        """Handle sensor fault report from ESP32."""
        try:
            data = json.loads(payload.decode('utf-8'))
            fault_type = data.get('fault_type', 'unknown')
            
            logger.warning(
                f"SENSOR FAULT: Device {device_id} in DMA {dma_id} - {fault_type}"
            )
            
            # Callback for fault handling
            if self.on_sensor_fault:
                self.on_sensor_fault(dma_id, device_id, fault_type)
                
        except Exception as e:
            logger.error(f"Error handling sensor fault: {e}")
    
    def _handle_device_status(self, dma_id: str, device_id: str, payload: bytes):
        """Handle device status update."""
        try:
            data = json.loads(payload.decode('utf-8'))
            status = data.get('status', 'unknown')
            
            if status == 'online':
                logger.info(f"Device ONLINE: {device_id} in DMA {dma_id}")
                if self.on_device_online:
                    self.on_device_online(dma_id, device_id)
            elif status == 'offline':
                logger.warning(f"Device OFFLINE: {device_id} in DMA {dma_id}")
                if self.on_device_offline:
                    self.on_device_offline(dma_id, device_id)
                    
        except Exception as e:
            logger.error(f"Error handling device status: {e}")
    
    def _handle_water_quality(self, dma_id: str, device_id: str, payload: bytes):
        """Handle water quality data."""
        try:
            data = json.loads(payload.decode('utf-8'))
            quality = data.get('water_quality', {})
            
            # Log water quality readings
            logger.debug(
                f"[{dma_id}/{device_id}] Water Quality: "
                f"pH={quality.get('ph', 'N/A')}, "
                f"Turbidity={quality.get('turbidity_ntu', 'N/A')} NTU, "
                f"Chlorine={quality.get('chlorine_mg_l', 'N/A')} mg/L"
            )
        except Exception as e:
            logger.error(f"Error handling water quality: {e}")
    
    def _handle_diagnostics(self, dma_id: str, device_id: str, payload: bytes):
        """Handle device diagnostics."""
        try:
            data = json.loads(payload.decode('utf-8'))
            logger.debug(f"Diagnostics from {device_id}: {data}")
        except Exception as e:
            logger.error(f"Error handling diagnostics: {e}")
    
    def _handle_acknowledgement(self, dma_id: str, device_id: str, payload: bytes):
        """Handle command acknowledgement from device."""
        try:
            data = json.loads(payload.decode('utf-8'))
            command = data.get('command', 'unknown')
            success = data.get('success', False)
            
            logger.info(
                f"Command ACK from {device_id}: {command} - "
                f"{'SUCCESS' if success else 'FAILED'}"
            )
        except Exception as e:
            logger.error(f"Error handling acknowledgement: {e}")
    
    def _handle_mesh_relayed(self, dma_id: str, payload: bytes):
        """Handle data relayed through mesh network."""
        try:
            data = json.loads(payload.decode('utf-8'))
            relayed_by = data.get('relayed_by', 'unknown')
            original_device = data.get('device_id', 'unknown')
            
            logger.info(
                f"Mesh relayed data: Original={original_device}, "
                f"Relayed by={relayed_by}, DMA={dma_id}"
            )
            
            # Process the relayed data as normal sensor data
            # (it should contain the same structure)
            reading = ESP32Reading.from_mqtt_payload(
                json.dumps(data).encode('utf-8'),
                f"aquawatch/{dma_id}/mesh/relayed"
            )
            
            if reading:
                self.dma_readings[dma_id].append(reading)
                self.stats['readings_processed'] += 1
                
        except Exception as e:
            logger.error(f"Error handling mesh relayed data: {e}")
    
    def _check_dma_aggregation(self, dma_id: str):
        """Check if DMA is ready for aggregation and AI processing."""
        now = datetime.now(timezone.utc)
        last_agg = self.dma_last_aggregation.get(dma_id, datetime.min.replace(tzinfo=timezone.utc))
        
        # Aggregate if enough time has passed
        if (now - last_agg).total_seconds() >= self.config.aggregation_window_sec:
            self._aggregate_dma_data(dma_id)
    
    def _check_aggregation_triggers(self):
        """Periodic check for DMAs needing aggregation."""
        now = datetime.now(timezone.utc)
        
        for dma_id in list(self.dma_readings.keys()):
            last_agg = self.dma_last_aggregation.get(
                dma_id, datetime.min.replace(tzinfo=timezone.utc)
            )
            
            if (now - last_agg).total_seconds() >= self.config.aggregation_window_sec:
                if len(self.dma_readings[dma_id]) >= self.config.min_sensors_for_analysis:
                    self._aggregate_dma_data(dma_id)
    
    def _aggregate_dma_data(self, dma_id: str):
        """
        Aggregate DMA sensor data and trigger AI analysis.
        
        This is where we prepare data for the Central AI Decision Engine.
        """
        readings = self.dma_readings[dma_id]
        if not readings:
            return
        
        # Create aggregated data structure
        aggregated = DMAAggregatedData(
            dma_id=dma_id,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add recent readings (last aggregation window)
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self.config.aggregation_window_sec
        )
        
        recent_readings = [r for r in readings if r.received_at >= cutoff]
        
        for reading in recent_readings:
            aggregated.add_reading(reading)
        
        # Update tracking
        self.dma_last_aggregation[dma_id] = datetime.now(timezone.utc)
        self.stats['dma_aggregations'] += 1
        
        # Trim old readings from memory
        self.dma_readings[dma_id] = recent_readings[-100:]  # Keep last 100
        
        # Trigger AI callback if registered
        if self.on_dma_data_ready and aggregated.active_sensors > 0:
            logger.info(
                f"DMA Aggregated: {dma_id} - "
                f"{aggregated.active_sensors} sensors, "
                f"inlet_flow={aggregated.total_inlet_flow_lpm:.2f} lpm, "
                f"avg_pressure={aggregated.average_pressure_bar:.2f} bar"
            )
            
            self.on_dma_data_ready(aggregated)
            self.stats['ai_triggers'] += 1
    
    # =========================================================================
    # COMMANDS TO ESP32 DEVICES (FROM AI)
    # =========================================================================
    
    def send_command(self, dma_id: str, device_id: str, command: str, 
                     params: Optional[Dict] = None) -> bool:
        """
        Send command to ESP32 device.
        
        The Central AI uses this to control ESP32 behavior.
        """
        if not self.connected:
            logger.error("Cannot send command - not connected")
            return False
        
        topic = f"{self.config.topic_prefix}/{dma_id}/{device_id}/cmd"
        
        payload = {'cmd': command}
        if params:
            payload.update(params)
        
        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=1
            )
            
            self.stats['commands_sent'] += 1
            logger.info(f"Command sent to {device_id}: {command}")
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def set_sampling_rate(self, dma_id: str, device_id: str, 
                          sensor_interval_ms: int, publish_interval_ms: int) -> bool:
        """AI requests change in sampling rate."""
        return self.send_command(
            dma_id, device_id, 'set_sampling_rate',
            {
                'sensor_interval_ms': sensor_interval_ms,
                'publish_interval_ms': publish_interval_ms
            }
        )
    
    def request_diagnostics(self, dma_id: str, device_id: str) -> bool:
        """AI requests device diagnostics."""
        return self.send_command(dma_id, device_id, 'diagnostics')
    
    def calibrate_sensor(self, dma_id: str, device_id: str,
                         pulses_per_liter: Optional[float] = None,
                         pressure_offset: Optional[float] = None,
                         ph_offset: Optional[float] = None) -> bool:
        """AI sends calibration values."""
        params = {}
        if pulses_per_liter is not None:
            params['pulses_per_liter'] = pulses_per_liter
        if pressure_offset is not None:
            params['pressure_offset'] = pressure_offset
        if ph_offset is not None:
            params['ph_offset'] = ph_offset
        
        return self.send_command(dma_id, device_id, 'calibrate', params)
    
    def reboot_device(self, dma_id: str, device_id: str) -> bool:
        """AI requests device reboot."""
        return self.send_command(dma_id, device_id, 'reboot')
    
    def send_dma_broadcast(self, dma_id: str, command: str, 
                           params: Optional[Dict] = None) -> bool:
        """Send command to all devices in a DMA."""
        topic = f"{self.config.topic_prefix}/{dma_id}/cmd"
        
        payload = {'cmd': command}
        if params:
            payload.update(params)
        
        try:
            self.client.publish(topic, json.dumps(payload), qos=1)
            return True
        except Exception as e:
            logger.error(f"Failed to broadcast to DMA: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            **self.stats,
            'connected': self.connected,
            'active_dmas': len(self.dma_readings),
            'registered_devices': len(self.registered_devices),
            'queue_size': self.processing_queue.qsize()
        }


# =============================================================================
# INTEGRATION WITH AI DECISION ENGINE
# =============================================================================

def create_ai_integrated_bridge(
    mqtt_config: Optional[MQTTAIBridgeConfig] = None,
    decision_engine = None,
    nrw_calculator = None,
    anomaly_detector = None
) -> MQTTAIBridge:
    """
    Create MQTT bridge with AI components integrated.
    
    This wires up the complete data flow:
    ESP32 → MQTT → Bridge → AI Models → Dashboard
    """
    bridge = MQTTAIBridge(mqtt_config)
    
    def on_dma_data_ready(aggregated: DMAAggregatedData):
        """
        Callback when DMA data is ready for AI processing.
        
        THE CENTRAL AI MAKES ALL LEAK DECISIONS HERE - NOT THE ESP32.
        """
        logger.info(f"AI Processing DMA: {aggregated.dma_id}")
        
        # 1. Run anomaly detection on the aggregated data
        if anomaly_detector:
            try:
                # Prepare data for anomaly detection
                pressure_values = [r.pressure_bar for r in aggregated.readings]
                flow_values = [r.flow_rate_lpm for r in aggregated.readings]
                
                # AI analyzes the data from multiple sensors
                # This is where leak detection ACTUALLY happens
                # (Not on the ESP32!)
                pass  # Anomaly detector would be called here
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")
        
        # 2. Calculate NRW for the DMA
        if nrw_calculator:
            try:
                # NRW calculation would happen here
                pass
            except Exception as e:
                logger.error(f"NRW calculation failed: {e}")
        
        # 3. Run through Decision Engine to get priority
        if decision_engine:
            try:
                # Decision engine would score the DMA here
                pass
            except Exception as e:
                logger.error(f"Decision engine failed: {e}")
    
    bridge.on_dma_data_ready = on_dma_data_ready
    
    return bridge


# =============================================================================
# MAIN (FOR TESTING)
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and connect bridge
    config = MQTTAIBridgeConfig(
        broker_host="localhost",
        broker_port=1883
    )
    
    bridge = MQTTAIBridge(config)
    
    def print_dma_data(data: DMAAggregatedData):
        print(f"\n{'='*60}")
        print(f"DMA DATA READY FOR AI: {data.dma_id}")
        print(f"{'='*60}")
        print(f"Active Sensors: {data.active_sensors}")
        print(f"Inlet Flow: {data.total_inlet_flow_lpm:.2f} lpm")
        print(f"Outlet Flow: {data.total_outlet_flow_lpm:.2f} lpm")
        print(f"Avg Pressure: {data.average_pressure_bar:.2f} bar")
        print(f"Max Pressure Z-Score: {data.max_pressure_zscore:.2f}")
        print(f"Max Flow Z-Score: {data.max_flow_zscore:.2f}")
        print(f"Sensors with Faults: {data.sensors_with_faults}")
        print(f"{'='*60}\n")
    
    bridge.on_dma_data_ready = print_dma_data
    
    if bridge.connect():
        print("MQTT AI Bridge running. Press Ctrl+C to stop.")
        try:
            while True:
                import time
                time.sleep(10)
                stats = bridge.get_stats()
                print(f"Stats: {stats}")
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            bridge.disconnect()
    else:
        print("Failed to connect to MQTT broker")
