"""
AquaWatch NRW - Starlink Integration for Remote Areas
=====================================================

"The best internet is the one that works everywhere."

For remote water infrastructure in Zambia/South Africa where:
- No cellular coverage
- No fiber/DSL available
- Solar-powered remote sites

Starlink provides:
- 50-200 Mbps anywhere
- Low latency (~20-40ms)
- Works with solar power
- Weather-resistant terminals
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectivityType(Enum):
    """Connection types for ESP32 devices."""
    WIFI = "wifi"              # Standard WiFi
    CELLULAR_4G = "4g"         # 4G/LTE modem
    CELLULAR_2G = "2g"         # Fallback GPRS
    LORAWAN = "lorawan"        # Long-range low-power
    STARLINK = "starlink"      # Satellite
    MESH = "mesh"              # Device-to-device mesh


@dataclass
class RemoteSiteConfig:
    """Configuration for a remote monitoring site."""
    site_id: str
    name: str
    location: Dict[str, float]  # lat, lng
    
    # Power
    power_source: str = "solar"  # solar, grid, battery, hybrid
    battery_capacity_wh: float = 1000
    solar_panel_watts: float = 100
    
    # Connectivity (in priority order)
    connectivity_options: List[ConnectivityType] = None
    current_connection: ConnectivityType = None
    
    # Starlink specific
    starlink_dish_id: Optional[str] = None
    starlink_service_plan: str = "business"  # residential, business, maritime
    
    # Status
    is_online: bool = False
    last_seen: datetime = None
    uptime_pct: float = 99.0


class StarlinkManager:
    """
    Manage Starlink connectivity for remote sites.
    
    Features:
    - Automatic failover to cellular/LoRa
    - Bandwidth management
    - Weather-based scheduling
    - Power optimization
    """
    
    def __init__(self):
        self.sites: Dict[str, RemoteSiteConfig] = {}
        self.starlink_api_token = None
        
    def add_site(self, config: RemoteSiteConfig):
        """Register a remote site."""
        if config.connectivity_options is None:
            config.connectivity_options = [
                ConnectivityType.STARLINK,
                ConnectivityType.CELLULAR_4G,
                ConnectivityType.LORAWAN
            ]
        self.sites[config.site_id] = config
        logger.info(f"Added remote site: {config.name}")
    
    async def check_connectivity(self, site_id: str) -> Dict:
        """Check and report connectivity status."""
        site = self.sites.get(site_id)
        if not site:
            return {"error": "Site not found"}
        
        status = {
            "site_id": site_id,
            "site_name": site.name,
            "current_connection": site.current_connection.value if site.current_connection else None,
            "is_online": site.is_online,
            "last_seen": site.last_seen.isoformat() if site.last_seen else None,
            "available_options": [c.value for c in site.connectivity_options]
        }
        
        # Check Starlink status (would use Starlink API)
        if ConnectivityType.STARLINK in site.connectivity_options:
            status["starlink"] = await self._check_starlink_status(site)
        
        return status
    
    async def _check_starlink_status(self, site: RemoteSiteConfig) -> Dict:
        """Check Starlink dish status."""
        # In production, would call Starlink API
        return {
            "dish_id": site.starlink_dish_id,
            "status": "online",
            "download_mbps": 150,
            "upload_mbps": 20,
            "latency_ms": 35,
            "obstructions_pct": 2.5,
            "uptime_24h_pct": 99.8
        }
    
    async def failover(self, site_id: str, to_connection: ConnectivityType) -> bool:
        """Failover to backup connectivity."""
        site = self.sites.get(site_id)
        if not site or to_connection not in site.connectivity_options:
            return False
        
        logger.warning(f"Failing over {site.name} from {site.current_connection} to {to_connection}")
        site.current_connection = to_connection
        
        # Notify about failover
        await self._send_failover_alert(site, to_connection)
        
        return True
    
    async def _send_failover_alert(self, site: RemoteSiteConfig, new_connection: ConnectivityType):
        """Send alert about connectivity failover."""
        logger.info(f"📡 ALERT: {site.name} failed over to {new_connection.value}")
    
    def get_bandwidth_allocation(self, site_id: str) -> Dict:
        """
        Calculate optimal bandwidth allocation.
        
        Prioritizes:
        1. Critical alerts (always)
        2. Real-time sensor data (high priority)
        3. Status reports (medium)
        4. Firmware updates (low, scheduled)
        5. Video feeds (lowest, on-demand)
        """
        return {
            "critical_alerts": {"priority": 1, "reserved_kbps": 10, "guaranteed": True},
            "sensor_data": {"priority": 2, "reserved_kbps": 50, "guaranteed": True},
            "status_reports": {"priority": 3, "reserved_kbps": 20, "guaranteed": False},
            "firmware_updates": {"priority": 4, "reserved_kbps": 100, "window": "02:00-04:00"},
            "video_feeds": {"priority": 5, "reserved_kbps": 500, "on_demand": True}
        }
    
    def optimize_for_solar(self, site_id: str) -> Dict:
        """
        Optimize connectivity for solar-powered sites.
        
        - High bandwidth during peak sun
        - Reduce to minimum at night
        - Store-and-forward for non-critical data
        """
        site = self.sites.get(site_id)
        if not site:
            return {}
        
        # Calculate available power
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Daytime
            solar_available = site.solar_panel_watts * 0.7  # 70% efficiency
        else:
            solar_available = 0
        
        battery_available = site.battery_capacity_wh * 0.8  # 80% usable
        
        # Starlink dish uses ~50-75W
        starlink_power = 60  # W average
        
        # Calculate runtime
        if solar_available >= starlink_power:
            mode = "full_power"
            runtime_hours = float('inf')
        else:
            mode = "battery"
            net_drain = starlink_power - solar_available
            runtime_hours = battery_available / net_drain if net_drain > 0 else float('inf')
        
        return {
            "site_id": site_id,
            "mode": mode,
            "solar_generation_w": solar_available,
            "starlink_consumption_w": starlink_power,
            "battery_runtime_hours": round(runtime_hours, 1),
            "recommendation": "full_operation" if runtime_hours > 24 else 
                            "reduced_operation" if runtime_hours > 8 else
                            "critical_only"
        }


# =============================================================================
# LORAWAN FALLBACK FOR ULTRA-REMOTE SITES
# =============================================================================

class LoRaWANNetwork:
    """
    LoRaWAN network for ultra-remote sites.
    
    - Range: 10-15 km in rural areas
    - Power: <50mA during transmission
    - Data: Low bandwidth but reliable
    - Perfect for basic sensor readings
    """
    
    def __init__(self):
        self.gateways: Dict[str, Dict] = {}
        self.devices: Dict[str, Dict] = {}
        
    def add_gateway(self, gateway_id: str, location: Dict, backhaul: ConnectivityType):
        """Add LoRaWAN gateway (connected to Starlink/cellular)."""
        self.gateways[gateway_id] = {
            "id": gateway_id,
            "location": location,
            "backhaul": backhaul,
            "status": "online",
            "devices_connected": 0
        }
        logger.info(f"Added LoRaWAN gateway: {gateway_id}")
    
    def register_device(self, device_id: str, device_eui: str, app_key: str):
        """Register LoRaWAN device (ESP32 + LoRa module)."""
        self.devices[device_id] = {
            "id": device_id,
            "dev_eui": device_eui,
            "status": "registered",
            "last_uplink": None,
            "rssi": None,
            "snr": None
        }
    
    def encode_sensor_payload(self, pressure: float, flow: float, battery: float) -> bytes:
        """
        Encode sensor data for LoRaWAN transmission.
        
        LoRaWAN has limited payload size (max 51-242 bytes depending on SF).
        Use compact binary encoding.
        """
        import struct
        
        # Pack into 8 bytes:
        # - Pressure: 2 bytes (0.01 bar resolution, 0-655.35 bar range)
        # - Flow: 2 bytes (0.01 m³/h resolution)
        # - Battery: 1 byte (0-100%)
        # - Reserved: 3 bytes
        
        p_int = int(pressure * 100)
        f_int = int(flow * 100)
        b_int = int(battery)
        
        return struct.pack('<HHBxxx', p_int, f_int, b_int)
    
    def decode_sensor_payload(self, payload: bytes) -> Dict:
        """Decode LoRaWAN sensor payload."""
        import struct
        
        p_int, f_int, b_int = struct.unpack('<HHBxxx', payload[:8])
        
        return {
            "pressure": p_int / 100.0,
            "flow": f_int / 100.0,
            "battery": b_int
        }


# =============================================================================
# MESH NETWORKING FOR SENSOR CLUSTERS
# =============================================================================

class ESP32MeshNetwork:
    """
    ESP-MESH networking for clustered sensors.
    
    One gateway ESP32 with Starlink/cellular,
    multiple sensor ESP32s in mesh configuration.
    
    Benefits:
    - Only one cellular/Starlink connection needed
    - Sensors can be deep in infrastructure
    - Self-healing network topology
    """
    
    def __init__(self):
        self.root_nodes: Dict[str, Dict] = {}  # Gateways
        self.mesh_nodes: Dict[str, Dict] = {}  # Sensors
        
    def configure_mesh(self, root_id: str, mesh_config: Dict):
        """Configure ESP-MESH network."""
        self.root_nodes[root_id] = {
            "id": root_id,
            "mesh_id": mesh_config.get("mesh_id", "aquawatch_mesh"),
            "channel": mesh_config.get("channel", 1),
            "max_layer": mesh_config.get("max_layer", 6),
            "max_connections": mesh_config.get("max_connections", 10),
            "children": []
        }
        
    def get_mesh_topology(self, root_id: str) -> Dict:
        """Get current mesh network topology."""
        root = self.root_nodes.get(root_id)
        if not root:
            return {}
        
        def build_tree(node_id: str, depth: int = 0) -> Dict:
            node = self.mesh_nodes.get(node_id, {})
            return {
                "id": node_id,
                "layer": depth,
                "rssi": node.get("rssi", -50),
                "children": [
                    build_tree(child_id, depth + 1)
                    for child_id in node.get("children", [])
                ]
            }
        
        return {
            "root": root_id,
            "mesh_id": root["mesh_id"],
            "topology": build_tree(root_id)
        }


# =============================================================================
# HYBRID CONNECTIVITY MANAGER
# =============================================================================

class HybridConnectivityManager:
    """
    Manages all connectivity options with automatic failover.
    
    Priority:
    1. Starlink (best performance)
    2. 4G/LTE (good backup)
    3. 2G/GPRS (emergency)
    4. LoRaWAN (ultra-low-power fallback)
    5. ESP-MESH (peer relay)
    """
    
    def __init__(self):
        self.starlink = StarlinkManager()
        self.lorawan = LoRaWANNetwork()
        self.mesh = ESP32MeshNetwork()
        
        # Connectivity status per site
        self.site_status: Dict[str, Dict] = {}
        
    async def get_best_connection(self, site_id: str) -> ConnectivityType:
        """Determine best available connection for a site."""
        status = self.site_status.get(site_id, {})
        
        # Check each option in priority order
        if status.get("starlink_available"):
            return ConnectivityType.STARLINK
        elif status.get("4g_available"):
            return ConnectivityType.CELLULAR_4G
        elif status.get("lorawan_available"):
            return ConnectivityType.LORAWAN
        elif status.get("mesh_available"):
            return ConnectivityType.MESH
        else:
            return ConnectivityType.CELLULAR_2G  # Last resort
    
    async def send_data(self, site_id: str, data: Dict, priority: str = "normal") -> bool:
        """Send data using best available connection."""
        connection = await self.get_best_connection(site_id)
        
        logger.info(f"Sending data from {site_id} via {connection.value}")
        
        if connection == ConnectivityType.STARLINK:
            return await self._send_via_starlink(site_id, data)
        elif connection == ConnectivityType.LORAWAN:
            return await self._send_via_lorawan(site_id, data, priority)
        else:
            return await self._send_via_cellular(site_id, data)
    
    async def _send_via_starlink(self, site_id: str, data: Dict) -> bool:
        """Send via Starlink - full bandwidth."""
        # Full JSON payload
        return True
    
    async def _send_via_lorawan(self, site_id: str, data: Dict, priority: str) -> bool:
        """Send via LoRaWAN - compact payload."""
        # Encode to minimal bytes
        payload = self.lorawan.encode_sensor_payload(
            data.get("pressure", 0),
            data.get("flow", 0),
            data.get("battery", 100)
        )
        return True
    
    async def _send_via_cellular(self, site_id: str, data: Dict) -> bool:
        """Send via cellular."""
        return True


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

starlink_manager = StarlinkManager()
lorawan_network = LoRaWANNetwork()
mesh_network = ESP32MeshNetwork()
connectivity_manager = HybridConnectivityManager()


# =============================================================================
# EXAMPLE: SETTING UP REMOTE SITE
# =============================================================================

def setup_remote_kafue_site():
    """Example: Set up remote monitoring site in Kafue River area."""
    
    # Site with no cellular, only Starlink
    site = RemoteSiteConfig(
        site_id="KAFUE_INTAKE_001",
        name="Kafue River Intake Station",
        location={"lat": -15.7667, "lng": 28.2000},
        power_source="solar",
        battery_capacity_wh=2000,  # 2kWh battery
        solar_panel_watts=200,      # 200W panel
        connectivity_options=[
            ConnectivityType.STARLINK,
            ConnectivityType.LORAWAN
        ],
        starlink_dish_id="DISH_KAFUE_001",
        starlink_service_plan="business"
    )
    
    starlink_manager.add_site(site)
    
    # Add LoRaWAN gateway at same site (backup)
    lorawan_network.add_gateway(
        gateway_id="GW_KAFUE_001",
        location=site.location,
        backhaul=ConnectivityType.STARLINK
    )
    
    print(f"✅ Remote site configured: {site.name}")
    print(f"   Primary: Starlink")
    print(f"   Backup: LoRaWAN")
    print(f"   Power: {site.solar_panel_watts}W solar + {site.battery_capacity_wh}Wh battery")


if __name__ == "__main__":
    setup_remote_kafue_site()
