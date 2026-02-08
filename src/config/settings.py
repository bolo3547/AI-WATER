"""
AquaWatch NRW - Configuration Management
=========================================

Centralized configuration for all system components.
Supports:
- Environment-based configuration
- Secure credential management
- Feature flags
- Per-utility customization
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# ENVIRONMENT
# =============================================================================

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "aquawatch"
    username: str = "aquawatch"
    password: str = ""  # Should be set via environment variable
    pool_size: int = 10
    max_overflow: int = 20
    
    # TimescaleDB specific
    chunk_time_interval: str = "1 day"
    retention_days: int = 365
    compression_after_days: int = 7
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class RedisConfig:
    """Redis cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    ssl: bool = False
    
    # Cache TTLs
    sensor_reading_ttl: int = 300  # 5 minutes
    feature_cache_ttl: int = 60   # 1 minute
    model_prediction_ttl: int = 30


@dataclass
class MessagingConfig:
    """Message queue configuration."""
    # MQTT
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_ssl: bool = False
    
    # Kafka
    kafka_bootstrap_servers: List[str] = field(default_factory=lambda: ["localhost:9092"])
    kafka_consumer_group: str = "aquawatch-processors"
    
    # Topics
    topic_sensor_readings: str = "sensors/readings"
    topic_anomalies: str = "ai/anomalies"
    topic_alerts: str = "operations/alerts"


@dataclass
class AIConfig:
    """AI/ML configuration."""
    # Model paths
    model_directory: str = "/opt/aquawatch/models"
    
    # Anomaly detection
    anomaly_contamination: float = 0.05
    anomaly_window_size: int = 96  # 24 hours at 15-min intervals
    
    # Probability estimation
    probability_threshold: float = 0.5
    high_probability_threshold: float = 0.75
    
    # Localization
    localization_prior_weight: float = 0.3
    
    # Feature engineering
    feature_window_hours: int = 24
    baseline_window_days: int = 30
    
    # Training
    retrain_interval_hours: int = 168  # Weekly
    min_samples_for_training: int = 1000
    validation_split: float = 0.2


@dataclass
class AlertConfig:
    """Alert and notification configuration."""
    # Thresholds
    min_pressure_bar: float = 2.0
    max_pressure_bar: float = 8.0
    pressure_drop_threshold: float = 0.3
    
    # Escalation
    critical_response_minutes: int = 30
    high_response_minutes: int = 120
    
    # Notifications
    enable_sms: bool = True
    enable_email: bool = True
    enable_push: bool = True
    
    # SMS provider
    sms_provider: str = "twilio"  # or "africas_talking"
    sms_sender_id: str = "AquaWatch"
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "alerts@aquawatch.africa"


@dataclass
class SecurityConfig:
    """Security configuration."""
    # JWT
    jwt_secret: str = ""  # MUST be set in environment
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Password policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_special: bool = True
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Session
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 3
    
    # Encryption
    encryption_key: str = ""  # For data at rest
    
    # CORS
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:8050"])


@dataclass
class FieldConfig:
    """Field device configuration."""
    # Sensors
    sensor_reading_interval_seconds: int = 900  # 15 minutes
    sensor_battery_threshold_percent: int = 20
    
    # Edge devices
    edge_buffer_hours: int = 72
    edge_sync_interval_minutes: int = 5
    
    # Connectivity
    lora_frequency_mhz: float = 868.0  # Africa region
    cellular_apn: str = ""
    
    # Solar power
    solar_panel_watts: int = 20
    battery_capacity_wh: int = 100


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8050
    debug: bool = False
    
    # Refresh rates
    live_data_refresh_seconds: int = 30
    alert_refresh_seconds: int = 10
    
    # Map
    map_center_lat: float = -15.0  # Zambia center
    map_center_lon: float = 28.0
    map_default_zoom: int = 6


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File logging
    log_directory: str = "/var/log/aquawatch"
    max_file_size_mb: int = 100
    backup_count: int = 10
    
    # Component-specific levels
    component_levels: Dict[str, str] = field(default_factory=lambda: {
        "sqlalchemy": "WARNING",
        "urllib3": "WARNING",
        "werkzeug": "WARNING"
    })


# =============================================================================
# MAIN CONFIGURATION
# =============================================================================

@dataclass
class SystemConfig:
    """Main system configuration."""
    environment: Environment = Environment.DEVELOPMENT
    version: str = "1.0.0"
    
    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    messaging: MessagingConfig = field(default_factory=MessagingConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    field_ops: FieldConfig = field(default_factory=FieldConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "ai_detection_enabled": True,
        "baseline_fallback_enabled": True,
        "auto_work_order_creation": True,
        "sms_notifications_enabled": True,
        "edge_processing_enabled": False,
        "realtime_dashboard_enabled": True
    })


# =============================================================================
# UTILITY-SPECIFIC CONFIGURATION
# =============================================================================

@dataclass
class UtilityConfig:
    """Configuration overrides for specific utility."""
    utility_id: str
    utility_name: str
    country: str
    
    # Pressure thresholds (may vary by network)
    min_pressure_bar: float = 2.0
    max_pressure_bar: float = 8.0
    target_nrw_percent: float = 25.0
    
    # Cost parameters
    water_cost_per_m3: float = 2.50
    currency_code: str = "ZMW"
    
    # Working hours
    work_start_hour: int = 7
    work_end_hour: int = 17
    
    # Contact information
    operations_phone: str = ""
    operations_email: str = ""


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

class ConfigLoader:
    """Load and manage configuration."""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.environ.get(
            "AQUAWATCH_CONFIG_DIR",
            "/etc/aquawatch"
        )
        self._config: Optional[SystemConfig] = None
        self._utility_configs: Dict[str, UtilityConfig] = {}
    
    def load(self, environment: str = None) -> SystemConfig:
        """Load system configuration."""
        
        # Determine environment
        env_str = environment or os.environ.get("AQUAWATCH_ENV", "development")
        env = Environment(env_str)
        
        # Start with defaults
        config = SystemConfig(environment=env)
        
        # Load from file if exists
        config_file = Path(self.config_dir) / f"config.{env_str}.json"
        if config_file.exists():
            with open(config_file) as f:
                file_config = json.load(f)
            config = self._merge_config(config, file_config)
        
        # Override from environment variables
        config = self._apply_env_overrides(config)
        
        self._config = config
        return config
    
    def _merge_config(self, config: SystemConfig, overrides: Dict) -> SystemConfig:
        """Merge configuration overrides."""
        
        if "database" in overrides:
            for key, value in overrides["database"].items():
                setattr(config.database, key, value)
        
        if "redis" in overrides:
            for key, value in overrides["redis"].items():
                setattr(config.redis, key, value)
        
        if "ai" in overrides:
            for key, value in overrides["ai"].items():
                setattr(config.ai, key, value)
        
        if "security" in overrides:
            for key, value in overrides["security"].items():
                setattr(config.security, key, value)
        
        if "features" in overrides:
            config.features.update(overrides["features"])
        
        return config
    
    def _apply_env_overrides(self, config: SystemConfig) -> SystemConfig:
        """Apply environment variable overrides."""
        
        # Database
        if os.environ.get("DB_HOST"):
            config.database.host = os.environ["DB_HOST"]
        if os.environ.get("DB_PASSWORD"):
            config.database.password = os.environ["DB_PASSWORD"]
        
        # Security
        if os.environ.get("JWT_SECRET"):
            config.security.jwt_secret = os.environ["JWT_SECRET"]
        if os.environ.get("ENCRYPTION_KEY"):
            config.security.encryption_key = os.environ["ENCRYPTION_KEY"]
        
        # Messaging
        if os.environ.get("MQTT_BROKER"):
            config.messaging.mqtt_broker = os.environ["MQTT_BROKER"]
        if os.environ.get("KAFKA_BOOTSTRAP"):
            config.messaging.kafka_bootstrap_servers = os.environ["KAFKA_BOOTSTRAP"].split(",")
        
        return config
    
    def load_utility_config(self, utility_id: str) -> UtilityConfig:
        """Load utility-specific configuration."""
        
        if utility_id in self._utility_configs:
            return self._utility_configs[utility_id]
        
        # Try to load from file
        utility_file = Path(self.config_dir) / "utilities" / f"{utility_id}.json"
        
        if utility_file.exists():
            with open(utility_file) as f:
                data = json.load(f)
            config = UtilityConfig(**data)
        else:
            # Return defaults
            config = UtilityConfig(
                utility_id=utility_id,
                utility_name="Unknown Utility",
                country="ZM"
            )
        
        self._utility_configs[utility_id] = config
        return config
    
    @property
    def config(self) -> SystemConfig:
        """Get loaded configuration."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled."""
        return self.config.features.get(feature_name, False)
    
    def get_for_environment(self) -> Dict[str, Any]:
        """Get configuration suitable for environment dump (no secrets)."""
        
        config = self.config
        
        return {
            "environment": config.environment.value,
            "version": config.version,
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "database": config.database.database
            },
            "ai": {
                "anomaly_contamination": config.ai.anomaly_contamination,
                "probability_threshold": config.ai.probability_threshold
            },
            "features": config.features
        }


# =============================================================================
# ZAMBIA DEFAULTS
# =============================================================================

ZAMBIA_UTILITY_DEFAULTS = {
    "NWSC": UtilityConfig(
        utility_id="NWSC",
        utility_name="Nkana Water and Sewerage Company",
        country="ZM",
        min_pressure_bar=2.0,
        max_pressure_bar=6.0,
        target_nrw_percent=25.0,
        water_cost_per_m3=1.50,
        currency_code="ZMW"
    ),
    "LWSC": UtilityConfig(
        utility_id="LWSC",
        utility_name="Lusaka Water and Sewerage Company",
        country="ZM",
        min_pressure_bar=2.5,
        max_pressure_bar=7.0,
        target_nrw_percent=30.0,
        water_cost_per_m3=2.00,
        currency_code="ZMW"
    )
}


SOUTH_AFRICA_UTILITY_DEFAULTS = {
    "RAND_WATER": UtilityConfig(
        utility_id="RAND_WATER",
        utility_name="Rand Water",
        country="ZA",
        min_pressure_bar=2.5,
        max_pressure_bar=8.0,
        target_nrw_percent=20.0,
        water_cost_per_m3=15.00,  # ZAR
        currency_code="ZAR"
    )
}


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_config_loader: Optional[ConfigLoader] = None


def get_config() -> SystemConfig:
    """Get global configuration instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.config


def get_utility_config(utility_id: str) -> UtilityConfig:
    """Get utility-specific configuration."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.load_utility_config(utility_id)


# =============================================================================
# STARTUP VALIDATION
# =============================================================================

def validate_config(config: Optional[SystemConfig] = None) -> List[str]:
    """
    Validate configuration at startup.
    
    Returns a list of warnings/errors. Critical issues raise RuntimeError.
    """
    if config is None:
        config = get_config()
    
    warnings: List[str] = []
    is_production = config.environment == Environment.PRODUCTION
    
    # JWT Secret validation
    if not config.security.jwt_secret:
        msg = "JWT_SECRET is not set - authentication will not work"
        if is_production:
            raise RuntimeError(f"CRITICAL: {msg}")
        warnings.append(f"WARNING: {msg}")
    elif len(config.security.jwt_secret) < 32:
        msg = "JWT_SECRET is too short (minimum 32 characters recommended)"
        if is_production:
            raise RuntimeError(f"CRITICAL: {msg}")
        warnings.append(f"WARNING: {msg}")
    
    # Encryption key validation
    if not config.security.encryption_key:
        msg = "ENCRYPTION_KEY is not set - data-at-rest encryption disabled"
        if is_production:
            warnings.append(f"CRITICAL: {msg}")
        else:
            warnings.append(f"WARNING: {msg}")
    
    # Database password
    if not config.database.password:
        msg = "Database password is empty"
        if is_production:
            raise RuntimeError(f"CRITICAL: {msg}")
        warnings.append(f"WARNING: {msg}")
    
    # Log all warnings
    for warning in warnings:
        logger.warning(f"[CONFIG] {warning}")
    
    if not warnings:
        logger.info("[CONFIG] Configuration validation passed")
    
    return warnings


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AquaWatch NRW - Configuration Demo")
    print("=" * 60)
    
    loader = ConfigLoader()
    config = loader.load("development")
    
    print(f"\nEnvironment: {config.environment.value}")
    print(f"Version: {config.version}")
    
    print("\nDatabase Configuration:")
    print(f"  Host: {config.database.host}")
    print(f"  Database: {config.database.database}")
    
    print("\nAI Configuration:")
    print(f"  Contamination: {config.ai.anomaly_contamination}")
    print(f"  Probability threshold: {config.ai.probability_threshold}")
    
    print("\nFeature Flags:")
    for feature, enabled in config.features.items():
        status = "✓ Enabled" if enabled else "✗ Disabled"
        print(f"  {feature}: {status}")
    
    print("\nUtility Configuration (LWSC):")
    utility = ZAMBIA_UTILITY_DEFAULTS["LWSC"]
    print(f"  Name: {utility.utility_name}")
    print(f"  Target NRW: {utility.target_nrw_percent}%")
    print(f"  Water cost: {utility.water_cost_per_m3} {utility.currency_code}/m³")
