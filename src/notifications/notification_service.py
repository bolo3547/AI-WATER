"""
AquaWatch NRW v3.0 - Notification Service
=========================================

Multi-channel notification dispatcher with:
- In-app notifications (stored in database)
- Email provider (stub with logging)
- SMS provider (stub with logging)
- WhatsApp provider (stub with logging)
- Push notification provider (stub)
- Audit logging for all sends

Usage:
    from src.notifications.notification_service import notification_service
    
    # Send a notification
    await notification_service.send(
        tenant_id="lwsc-zambia",
        user_id="user-123",
        title="Leak Detected",
        message="Critical leak detected in DMA-01",
        severity=NotificationSeverity.CRITICAL,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    )
"""

import asyncio
import logging
import uuid
import os
import smtplib
from email.message import EmailMessage
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Optional providers
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except Exception:
    SENDGRID_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False


# =============================================================================
# ENUMS (matching database models)
# =============================================================================

class NotificationChannel(str, Enum):
    """Available notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationSeverity(str, Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NotificationPayload:
    """Notification data for dispatch."""
    tenant_id: str
    user_id: str
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    category: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    rule_id: Optional[str] = None
    
    # Recipient details for external channels
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None


@dataclass
class DeliveryResult:
    """Result of notification delivery attempt."""
    channel: NotificationChannel
    success: bool
    notification_id: Optional[str] = None
    external_id: Optional[str] = None  # ID from external provider
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# PROVIDER INTERFACE
# =============================================================================

class NotificationProvider(ABC):
    """Base class for notification providers."""
    
    channel: NotificationChannel
    
    @abstractmethod
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Send notification via this channel."""
        pass
    
    @abstractmethod
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        """Check delivery status for a sent notification."""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        return True


# =============================================================================
# IN-APP PROVIDER
# =============================================================================

class InAppProvider(NotificationProvider):
    """
    In-app notification provider.
    
    Stores notifications in the database for display in the UI.
    """
    
    channel = NotificationChannel.IN_APP
    
    def __init__(self):
        # In-memory store for demo (would use database in production)
        self._notifications: Dict[str, List[Dict]] = {}
    
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Store notification in database."""
        try:
            notification_id = str(uuid.uuid4())
            
            notification = {
                "id": notification_id,
                "tenant_id": payload.tenant_id,
                "user_id": payload.user_id,
                "title": payload.title,
                "message": payload.message,
                "severity": payload.severity.value,
                "category": payload.category,
                "source_type": payload.source_type,
                "source_id": payload.source_id,
                "action_url": payload.action_url,
                "metadata": payload.metadata,
                "channel": self.channel.value,
                "status": NotificationStatus.DELIVERED.value,
                "read": False,
                "created_at": datetime.utcnow().isoformat(),
                "rule_id": payload.rule_id,
            }
            
            # Store in memory (would be database in production)
            key = f"{payload.tenant_id}:{payload.user_id}"
            if key not in self._notifications:
                self._notifications[key] = []
            self._notifications[key].insert(0, notification)
            
            # Keep only last 100 notifications per user
            self._notifications[key] = self._notifications[key][:100]
            
            logger.info(
                f"[IN_APP] Notification stored: user={payload.user_id}, "
                f"title='{payload.title[:50]}...', severity={payload.severity.value}"
            )
            
            return DeliveryResult(
                channel=self.channel,
                success=True,
                notification_id=notification_id,
            )
            
        except Exception as e:
            logger.error(f"[IN_APP] Failed to store notification: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error=str(e),
            )
    
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        """In-app notifications are always delivered immediately."""
        return NotificationStatus.DELIVERED
    
    def get_notifications(
        self, 
        tenant_id: str, 
        user_id: str, 
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """Get notifications for a user."""
        key = f"{tenant_id}:{user_id}"
        notifications = self._notifications.get(key, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]
        
        return notifications[:limit]
    
    def get_unread_count(self, tenant_id: str, user_id: str) -> int:
        """Get unread notification count for a user."""
        key = f"{tenant_id}:{user_id}"
        notifications = self._notifications.get(key, [])
        return sum(1 for n in notifications if not n.get("read"))
    
    def mark_read(self, tenant_id: str, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        key = f"{tenant_id}:{user_id}"
        notifications = self._notifications.get(key, [])
        
        for n in notifications:
            if n["id"] == notification_id:
                n["read"] = True
                n["read_at"] = datetime.utcnow().isoformat()
                return True
        return False
    
    def mark_all_read(self, tenant_id: str, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        key = f"{tenant_id}:{user_id}"
        notifications = self._notifications.get(key, [])
        
        count = 0
        now = datetime.utcnow().isoformat()
        for n in notifications:
            if not n.get("read"):
                n["read"] = True
                n["read_at"] = now
                count += 1
        return count


# =============================================================================
# EMAIL PROVIDER
# =============================================================================

class EmailProvider(NotificationProvider):
    """
    Email notification provider.
    """
    
    channel = NotificationChannel.EMAIL
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "noreply@aquawatch.io",
        from_name: str = "AquaWatch NRW",
        sendgrid_api_key: Optional[str] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM", from_email)
        self.from_name = from_name
        self.sendgrid_api_key = sendgrid_api_key or os.getenv("SENDGRID_API_KEY")
        
        # Track sent emails for status checks
        self._sent_emails: Dict[str, Dict] = {}
    
    @property
    def is_available(self) -> bool:
        """Check if SendGrid or SMTP is configured."""
        return bool(self.sendgrid_api_key) or bool(self.smtp_host)
    
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Send email notification."""
        external_id = str(uuid.uuid4())
        
        if not payload.recipient_email:
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error="No recipient email provided",
            )
        try:
            if self.sendgrid_api_key and SENDGRID_AVAILABLE:
                message = Mail(
                    from_email=(self.from_email, self.from_name),
                    to_emails=payload.recipient_email,
                    subject=payload.title,
                    html_content=payload.message
                )
                client = SendGridAPIClient(self.sendgrid_api_key)
                response = client.send(message)

                success = 200 <= response.status_code < 300
                status = NotificationStatus.SENT.value if success else NotificationStatus.FAILED.value
                self._sent_emails[external_id] = {
                    "to": payload.recipient_email,
                    "subject": payload.title,
                    "status": status,
                    "sent_at": datetime.utcnow().isoformat(),
                }

                return DeliveryResult(
                    channel=self.channel,
                    success=success,
                    external_id=external_id,
                    error=None if success else f"SendGrid error: {response.status_code}"
                )

            if self.smtp_host:
                msg = EmailMessage()
                msg["Subject"] = payload.title
                msg["From"] = f"{self.from_name} <{self.from_email}>"
                msg["To"] = payload.recipient_email
                msg.set_content(payload.message)

                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                    server.ehlo()
                    if self.smtp_port in (587, 25):
                        server.starttls()
                        server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                self._sent_emails[external_id] = {
                    "to": payload.recipient_email,
                    "subject": payload.title,
                    "status": NotificationStatus.SENT.value,
                    "sent_at": datetime.utcnow().isoformat(),
                }

                return DeliveryResult(
                    channel=self.channel,
                    success=True,
                    external_id=external_id,
                )

            logger.info(
                f"[EMAIL] No provider configured, logging only: to={payload.recipient_email}, subject={payload.title}"
            )
            self._sent_emails[external_id] = {
                "to": payload.recipient_email,
                "subject": payload.title,
                "status": NotificationStatus.PENDING.value,
                "sent_at": datetime.utcnow().isoformat(),
            }
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error="Email provider not configured"
            )
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error=str(e)
            )
    
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        """Check email delivery status."""
        email = self._sent_emails.get(external_id)
        if email:
            return NotificationStatus(email["status"])
        return None


# =============================================================================
# SMS PROVIDER
# =============================================================================

class SMSProvider(NotificationProvider):
    """
    SMS notification provider.
    """
    
    channel = NotificationChannel.SMS
    
    def __init__(
        self,
        provider: str = "twilio",  # twilio, africastalking, local
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.provider = provider
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_PHONE_NUMBER")
        
        self._sent_sms: Dict[str, Dict] = {}
    
    @property
    def is_available(self) -> bool:
        """Check if SMS provider is configured."""
        return bool(self.account_sid and self.auth_token and self.from_number)
    
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Send SMS notification."""
        external_id = str(uuid.uuid4())
        
        if not payload.recipient_phone:
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error="No recipient phone number provided",
            )
        
        # Format message for SMS (keep it short)
        sms_message = f"[AquaWatch] {payload.title}: {payload.message}"
        if len(sms_message) > 160:
            sms_message = sms_message[:157] + "..."
        
        try:
            if self.provider == "twilio" and TWILIO_AVAILABLE and self.is_available:
                client = TwilioClient(self.account_sid, self.auth_token)
                message = client.messages.create(
                    body=sms_message,
                    from_=self.from_number,
                    to=payload.recipient_phone
                )
                self._sent_sms[external_id] = {
                    "to": payload.recipient_phone,
                    "message": sms_message,
                    "status": NotificationStatus.SENT.value,
                    "sent_at": datetime.utcnow().isoformat(),
                }
                return DeliveryResult(
                    channel=self.channel,
                    success=True,
                    external_id=message.sid,
                )

            logger.info(
                f"[SMS] No provider configured, logging only: to={payload.recipient_phone}, provider={self.provider}"
            )
            self._sent_sms[external_id] = {
                "to": payload.recipient_phone,
                "message": sms_message,
                "status": NotificationStatus.PENDING.value,
                "sent_at": datetime.utcnow().isoformat(),
            }
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error="SMS provider not configured"
            )
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error=str(e)
            )
    
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        """Check SMS delivery status."""
        sms = self._sent_sms.get(external_id)
        if sms:
            return NotificationStatus(sms["status"])
        return None


# =============================================================================
# WHATSAPP PROVIDER
# =============================================================================

class WhatsAppProvider(NotificationProvider):
    """
    WhatsApp notification provider.
    
    STUB IMPLEMENTATION - logs instead of sending.
    Replace with WhatsApp Business API/Twilio WhatsApp integration.
    """
    
    channel = NotificationChannel.WHATSAPP
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,  # WhatsApp business number
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        self._sent_messages: Dict[str, Dict] = {}
    
    @property
    def is_available(self) -> bool:
        """Check if WhatsApp is configured."""
        return bool(self.account_sid and self.auth_token and self.from_number)
    
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Send WhatsApp notification."""
        external_id = str(uuid.uuid4())
        
        if not payload.recipient_phone:
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error="No recipient phone number provided",
            )
        
        # Format message for WhatsApp (supports longer messages)
        wa_message = f"🚰 *{payload.title}*\n\n{payload.message}"
        if payload.action_url:
            wa_message += f"\n\n📎 View details: {payload.action_url}"
        
        try:
            if TWILIO_AVAILABLE and self.is_available:
                client = TwilioClient(self.account_sid, self.auth_token)
                to_number = payload.recipient_phone
                if not to_number.startswith("whatsapp:"):
                    to_number = f"whatsapp:{to_number}"
                from_number = self.from_number
                if not from_number.startswith("whatsapp:"):
                    from_number = f"whatsapp:{from_number}"

                message = client.messages.create(
                    body=wa_message,
                    from_=from_number,
                    to=to_number
                )

                self._sent_messages[external_id] = {
                    "to": payload.recipient_phone,
                    "message": wa_message,
                    "status": NotificationStatus.SENT.value,
                    "sent_at": datetime.utcnow().isoformat(),
                }

                return DeliveryResult(
                    channel=self.channel,
                    success=True,
                    external_id=message.sid,
                )

            logger.info(
                f"[WHATSAPP] No provider configured, logging only: to={payload.recipient_phone}"
            )
            self._sent_messages[external_id] = {
                "to": payload.recipient_phone,
                "message": wa_message,
                "status": NotificationStatus.PENDING.value,
                "sent_at": datetime.utcnow().isoformat(),
            }
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error="WhatsApp provider not configured"
            )
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                external_id=external_id,
                error=str(e)
            )
    
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        """Check WhatsApp delivery status."""
        msg = self._sent_messages.get(external_id)
        if msg:
            return NotificationStatus(msg["status"])
        return None


# =============================================================================
# PUSH PROVIDER (STUB)
# =============================================================================

class PushProvider(NotificationProvider):
    """
    Push notification provider (Firebase Cloud Messaging).
    
    STUB IMPLEMENTATION - logs instead of sending.
    """
    
    channel = NotificationChannel.PUSH
    
    def __init__(self, firebase_credentials: Optional[Dict] = None):
        self.firebase_credentials = firebase_credentials
        self._sent_pushes: Dict[str, Dict] = {}
    
    @property
    def is_available(self) -> bool:
        return bool(self.firebase_credentials)
    
    async def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Send push notification (STUB)."""
        external_id = str(uuid.uuid4())
        
        # STUB: Log instead of sending
        logger.info(
            f"[PUSH STUB] Would send push notification:\n"
            f"  User: {payload.user_id}\n"
            f"  Title: {payload.title}\n"
            f"  Body: {payload.message[:100]}..."
        )
        
        self._sent_pushes[external_id] = {
            "user_id": payload.user_id,
            "title": payload.title,
            "status": NotificationStatus.SENT.value,
            "sent_at": datetime.utcnow().isoformat(),
        }
        
        return DeliveryResult(
            channel=self.channel,
            success=True,
            external_id=external_id,
        )
    
    async def check_status(self, external_id: str) -> Optional[NotificationStatus]:
        push = self._sent_pushes.get(external_id)
        if push:
            return NotificationStatus(push["status"])
        return None


# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """
    Main notification dispatcher service.
    
    Features:
    - Multi-channel dispatch
    - Provider abstraction
    - Audit logging
    - Retry logic
    - Rate limiting
    """
    
    def __init__(self):
        # Initialize providers
        self.providers: Dict[NotificationChannel, NotificationProvider] = {
            NotificationChannel.IN_APP: InAppProvider(),
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.SMS: SMSProvider(),
            NotificationChannel.WHATSAPP: WhatsAppProvider(),
            NotificationChannel.PUSH: PushProvider(),
        }
        
        # Audit log (in-memory for demo, would use database)
        self._audit_log: List[Dict] = []
        
        # Rate limiting
        self._rate_limits: Dict[str, List[datetime]] = {}
        self._rate_limit_window = 60  # seconds
        self._rate_limit_max = 10  # notifications per window per user
    
    async def send(
        self,
        tenant_id: str,
        user_id: str,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        channels: Optional[List[NotificationChannel]] = None,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_name: Optional[str] = None,
        rule_id: Optional[str] = None,
    ) -> List[DeliveryResult]:
        """
        Send notification via specified channels.
        
        Args:
            tenant_id: Tenant identifier
            user_id: Target user ID
            title: Notification title
            message: Notification body
            severity: Notification severity level
            channels: List of channels to use (default: IN_APP only)
            category: Notification category (leak, sensor, etc.)
            source_type: Source entity type (alert, work_order, etc.)
            source_id: Source entity ID
            action_url: URL for notification action
            metadata: Additional metadata
            recipient_email: Email address for email channel
            recipient_phone: Phone number for SMS/WhatsApp
            recipient_name: Recipient display name
            rule_id: ID of notification rule that triggered this
        
        Returns:
            List of delivery results for each channel
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]
        
        # Check rate limit
        if not self._check_rate_limit(tenant_id, user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return [DeliveryResult(
                channel=ch,
                success=False,
                error="Rate limit exceeded"
            ) for ch in channels]
        
        # Build payload
        payload = NotificationPayload(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            source_type=source_type,
            source_id=source_id,
            action_url=action_url,
            metadata=metadata or {},
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            recipient_name=recipient_name,
            rule_id=rule_id,
        )
        
        # Send via each channel
        results: List[DeliveryResult] = []
        
        for channel in channels:
            provider = self.providers.get(channel)
            
            if not provider:
                results.append(DeliveryResult(
                    channel=channel,
                    success=False,
                    error=f"No provider for channel: {channel.value}"
                ))
                continue
            
            try:
                result = await provider.send(payload)
                results.append(result)
                
                # Log to audit
                self._log_audit(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="notification_sent",
                    channel=channel.value,
                    success=result.success,
                    notification_id=result.notification_id,
                    external_id=result.external_id,
                    error=result.error,
                    metadata={
                        "title": title,
                        "severity": severity.value,
                        "category": category,
                        "source_type": source_type,
                        "source_id": source_id,
                    }
                )
                
            except Exception as e:
                logger.error(f"Error sending notification via {channel.value}: {e}")
                result = DeliveryResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                )
                results.append(result)
                
                self._log_audit(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="notification_failed",
                    channel=channel.value,
                    success=False,
                    error=str(e),
                )
        
        return results
    
    async def send_to_roles(
        self,
        tenant_id: str,
        roles: List[str],
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        channels: Optional[List[NotificationChannel]] = None,
        **kwargs
    ) -> Dict[str, List[DeliveryResult]]:
        """
        Send notification to all users with specified roles.
        
        Args:
            tenant_id: Tenant identifier
            roles: List of roles to notify
            title: Notification title
            message: Notification body
            severity: Severity level
            channels: Channels to use
            **kwargs: Additional arguments for send()
        
        Returns:
            Dict mapping user_id to delivery results
        """
        # In production, would query database for users with these roles
        # For now, return empty (stub implementation)
        logger.info(f"Would notify roles {roles} in tenant {tenant_id}: {title}")
        return {}
    
    def _check_rate_limit(self, tenant_id: str, user_id: str) -> bool:
        """Check if user is within rate limits."""
        key = f"{tenant_id}:{user_id}"
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self._rate_limit_window)
        
        # Clean old entries
        if key in self._rate_limits:
            self._rate_limits[key] = [
                ts for ts in self._rate_limits[key]
                if ts > window_start
            ]
        else:
            self._rate_limits[key] = []
        
        # Check limit
        if len(self._rate_limits[key]) >= self._rate_limit_max:
            return False
        
        # Record this notification
        self._rate_limits[key].append(now)
        return True
    
    def _log_audit(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        channel: str,
        success: bool,
        notification_id: Optional[str] = None,
        external_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log notification action to audit trail."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "resource_type": "notification",
            "channel": channel,
            "success": success,
            "notification_id": notification_id,
            "external_id": external_id,
            "error": error,
            "metadata": metadata or {},
        }
        
        self._audit_log.append(entry)
        
        # Keep only last 10000 entries in memory
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]
        
        # In production, would write to audit_logs table
        logger.debug(f"Audit: {action} channel={channel} success={success}")
    
    def get_audit_log(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit log entries."""
        entries = self._audit_log
        
        if tenant_id:
            entries = [e for e in entries if e.get("tenant_id") == tenant_id]
        
        if user_id:
            entries = [e for e in entries if e.get("user_id") == user_id]
        
        return list(reversed(entries))[:limit]
    
    # Convenience access to in-app provider methods
    def get_notifications(
        self,
        tenant_id: str,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """Get in-app notifications for a user."""
        provider = self.providers.get(NotificationChannel.IN_APP)
        if isinstance(provider, InAppProvider):
            return provider.get_notifications(tenant_id, user_id, unread_only, limit)
        return []
    
    def get_unread_count(self, tenant_id: str, user_id: str) -> int:
        """Get unread notification count."""
        provider = self.providers.get(NotificationChannel.IN_APP)
        if isinstance(provider, InAppProvider):
            return provider.get_unread_count(tenant_id, user_id)
        return 0
    
    def mark_read(self, tenant_id: str, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        provider = self.providers.get(NotificationChannel.IN_APP)
        if isinstance(provider, InAppProvider):
            success = provider.mark_read(tenant_id, user_id, notification_id)
            if success:
                self._log_audit(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="notification_read",
                    channel="in_app",
                    success=True,
                    notification_id=notification_id,
                )
            return success
        return False
    
    def mark_all_read(self, tenant_id: str, user_id: str) -> int:
        """Mark all notifications as read."""
        provider = self.providers.get(NotificationChannel.IN_APP)
        if isinstance(provider, InAppProvider):
            count = provider.mark_all_read(tenant_id, user_id)
            if count > 0:
                self._log_audit(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="notifications_marked_all_read",
                    channel="in_app",
                    success=True,
                    metadata={"count": count},
                )
            return count
        return 0


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

notification_service = NotificationService()
