"""AquaWatch Notifications Package.

This package provides a comprehensive notification system including:
- Multi-channel notification dispatch (in-app, email, SMS, WhatsApp, push, webhook)
- Escalation engine for automatic alert escalation
- API endpoints for notification management
"""

# Legacy alerting module (for backward compatibility)
from .alerting import (
    NotificationService as LegacyNotificationService,
    NotificationChannel as LegacyNotificationChannel,
    NotificationPriority,
    NotificationRecipient,
    LeakAlert,
    EscalationManager as LegacyEscalationManager,
    MessageTemplates,
    SMSProvider as LegacySMSProvider,
    EmailProvider as LegacyEmailProvider,
    PushProvider as LegacyPushProvider,
    WebhookProvider
)

# New notification system (v3.0)
from .notification_service import (
    NotificationService,
    NotificationPayload,
    DeliveryResult,
    NotificationProvider,
    InAppProvider,
    EmailProvider,
    SMSProvider,
    WhatsAppProvider,
    PushProvider,
    get_notification_service
)

from .escalation_engine import (
    EscalationEngine,
    EscalationLevel,
    DEFAULT_ESCALATION_RULES,
    get_escalation_engine
)

from .notification_api import (
    notification_router,
    rules_router,
    escalation_router
)

__all__ = [
    # Legacy (backward compatibility)
    'LegacyNotificationService',
    'LegacyNotificationChannel',
    'NotificationPriority',
    'NotificationRecipient',
    'LeakAlert',
    'LegacyEscalationManager',
    'MessageTemplates',
    'LegacySMSProvider',
    'LegacyEmailProvider',
    'LegacyPushProvider',
    'WebhookProvider',
    
    # New notification system
    'NotificationService',
    'NotificationPayload',
    'DeliveryResult',
    'NotificationProvider',
    'InAppProvider',
    'EmailProvider',
    'SMSProvider',
    'WhatsAppProvider',
    'PushProvider',
    'get_notification_service',
    
    # Escalation engine
    'EscalationEngine',
    'EscalationLevel',
    'DEFAULT_ESCALATION_RULES',
    'get_escalation_engine',
    
    # API routers
    'notification_router',
    'rules_router',
    'escalation_router',
]
