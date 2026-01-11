"""
AquaWatch NRW Cloud Module

Remote access, authentication, and notification services.
"""

from .config import CloudConfig, CloudProvider, get_config
from .auth import (
    AuthService,
    User,
    UserRole,
    Permission,
    APIKey,
    auth_service
)
from .notifications import (
    NotificationService,
    NotificationChannel,
    AlertSeverity,
    NotificationPreference,
    notification_service
)

__all__ = [
    # Configuration
    'CloudConfig',
    'CloudProvider',
    'get_config',
    
    # Authentication
    'AuthService',
    'User',
    'UserRole',
    'Permission',
    'APIKey',
    'auth_service',
    
    # Notifications
    'NotificationService',
    'NotificationChannel',
    'AlertSeverity',
    'NotificationPreference',
    'notification_service'
]
