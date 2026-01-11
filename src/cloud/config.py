"""
AquaWatch NRW - Cloud Deployment Configuration
==============================================

Deploy to cloud providers for global remote access.
Supports: AWS, Azure, Google Cloud, DigitalOcean, or self-hosted.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    SELF_HOSTED = "self_hosted"


@dataclass
class CloudConfig:
    """Cloud deployment configuration."""
    
    # Provider settings
    provider: CloudProvider = CloudProvider.DIGITALOCEAN
    region: str = "lon1"  # London (closest to Africa)
    
    # Domain settings
    domain: str = "aquawatch.example.com"
    subdomain_api: str = "api"      # api.aquawatch.example.com
    subdomain_mqtt: str = "mqtt"    # mqtt.aquawatch.example.com
    subdomain_dashboard: str = "app"  # app.aquawatch.example.com
    
    # Security
    ssl_enabled: bool = True
    ssl_provider: str = "letsencrypt"
    
    # Database
    db_host: str = "db.aquawatch.example.com"
    db_port: int = 5432
    db_name: str = "aquawatch"
    db_user: str = "aquawatch_app"
    db_password: str = os.getenv("DB_PASSWORD", "change_me_in_production")
    
    # MQTT Broker
    mqtt_host: str = "mqtt.aquawatch.example.com"
    mqtt_port: int = 1883
    mqtt_port_ssl: int = 8883
    mqtt_ws_port: int = 9001  # WebSocket for browser
    mqtt_user: str = "aquawatch"
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "change_me_in_production")
    
    # Redis (for sessions & caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Notifications
    twilio_account_sid: str = os.getenv("TWILIO_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_TOKEN", "")
    twilio_phone: str = os.getenv("TWILIO_PHONE", "")
    
    # Email (SendGrid/AWS SES)
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = "apikey"
    smtp_password: str = os.getenv("SENDGRID_API_KEY", "")
    email_from: str = "alerts@aquawatch.example.com"


# Production configuration
PRODUCTION_CONFIG = CloudConfig(
    provider=CloudProvider.DIGITALOCEAN,
    region="lon1",
    domain="aquawatch.example.com",
    ssl_enabled=True
)

# Development configuration  
DEV_CONFIG = CloudConfig(
    provider=CloudProvider.SELF_HOSTED,
    domain="localhost",
    ssl_enabled=False,
    db_host="localhost",
    mqtt_host="localhost"
)


def get_config() -> CloudConfig:
    """Get configuration based on environment."""
    env = os.getenv("AQUAWATCH_ENV", "development")
    if env == "production":
        return PRODUCTION_CONFIG
    return DEV_CONFIG
