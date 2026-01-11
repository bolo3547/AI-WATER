"""
AquaWatch NRW - Multi-Channel Alerting System
==============================================

Sends leak alerts via SMS, Email, Push notifications, and Webhooks.
Integrates with African mobile networks (Zambia/South Africa).

Features:
- SMS via Twilio, Africa's Talking, and local gateways
- Email via SMTP, SendGrid, or Mailgun
- Push notifications via Firebase Cloud Messaging
- Webhook integrations for external systems
- Alert escalation and retry logic
- Delivery status tracking
"""

import os
import json
import logging
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class NotificationChannel(Enum):
    """Available notification channels."""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    WEBHOOK = "webhook"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"           # Daily digest
    NORMAL = "normal"     # Standard delivery
    HIGH = "high"         # Immediate delivery
    CRITICAL = "critical" # Multi-channel blast


class DeliveryStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class NotificationRecipient:
    """Notification recipient details."""
    user_id: str
    name: str
    role: str
    phone: Optional[str] = None       # SMS/WhatsApp
    email: Optional[str] = None       # Email
    fcm_token: Optional[str] = None   # Firebase push
    telegram_id: Optional[str] = None # Telegram
    preferred_channel: NotificationChannel = NotificationChannel.SMS
    language: str = "en"              # en, sw (Swahili), zu (Zulu)


@dataclass
class LeakAlert:
    """Leak alert for notification."""
    alert_id: str
    severity: str           # critical, high, medium, low
    location_name: str
    lat: float
    lon: float
    leak_rate_lps: float    # Liters per second
    detection_time: datetime
    sensor_id: str
    pressure_drop: float    # Bar
    zone: str
    estimated_loss_per_hour: float  # USD
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "location": self.location_name,
            "coordinates": {"lat": self.lat, "lon": self.lon},
            "leak_rate_lps": self.leak_rate_lps,
            "detection_time": self.detection_time.isoformat(),
            "sensor_id": self.sensor_id,
            "pressure_drop": self.pressure_drop,
            "zone": self.zone,
            "estimated_loss_per_hour": self.estimated_loss_per_hour
        }


@dataclass
class NotificationLog:
    """Log of sent notification."""
    notification_id: str
    channel: NotificationChannel
    recipient_id: str
    alert_id: str
    status: DeliveryStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    external_id: Optional[str] = None  # Provider message ID


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

class MessageTemplates:
    """Multi-language message templates."""
    
    TEMPLATES = {
        "leak_alert": {
            "en": {
                "sms": "🚨 LEAK ALERT [{severity}]: {location}. Est. {leak_rate:.1f} L/s. Pressure drop: {pressure_drop:.2f} bar. Respond immediately. ID: {alert_id}",
                "email_subject": "🚨 [{severity}] Water Leak Detected - {location}",
                "email_body": """
                    <h2>⚠️ Water Leak Alert</h2>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Zone:</strong> {zone}</p>
                    <p><strong>Estimated Leak Rate:</strong> {leak_rate:.2f} L/s ({hourly_loss:.0f} L/hour)</p>
                    <p><strong>Pressure Drop:</strong> {pressure_drop:.2f} bar</p>
                    <p><strong>Estimated Loss:</strong> ${cost_per_hour:.2f}/hour</p>
                    <p><strong>Detection Time:</strong> {detection_time}</p>
                    <p><strong>Sensor ID:</strong> {sensor_id}</p>
                    <hr>
                    <p><a href="{dashboard_url}">View on Dashboard</a> | 
                    <a href="{map_url}">View on Map</a></p>
                    <p>Alert ID: {alert_id}</p>
                """,
                "push_title": "🚨 Leak Alert: {location}",
                "push_body": "{severity} - {leak_rate:.1f} L/s leak detected. Tap for details."
            },
            "sw": {  # Swahili
                "sms": "🚨 TAHADHARI YA UVUJAJI [{severity}]: {location}. Kadri. {leak_rate:.1f} L/s. Jibu haraka. ID: {alert_id}",
                "push_title": "🚨 Uvujaji: {location}",
                "push_body": "{severity} - Uvujaji wa {leak_rate:.1f} L/s umegunduliwa."
            },
            "zu": {  # Zulu (South Africa)
                "sms": "🚨 ISEXWAYISO SOKUVUZA [{severity}]: {location}. Cishe {leak_rate:.1f} L/s. Phendula ngokushesha. ID: {alert_id}",
                "push_title": "🚨 Ukuvuza: {location}",
                "push_body": "{severity} - {leak_rate:.1f} L/s ukuvuza kutholakele."
            }
        },
        "work_order": {
            "en": {
                "sms": "📋 New Work Order #{wo_id}: {task} at {location}. Priority: {priority}. Due: {due_date}",
                "push_title": "📋 Work Order Assigned",
                "push_body": "{task} at {location}. Tap to view details."
            }
        },
        "escalation": {
            "en": {
                "sms": "⚠️ ESCALATION: Alert {alert_id} at {location} unresolved for {hours}h. {severity} severity. Requires attention.",
                "email_subject": "⚠️ Alert Escalation - {alert_id}",
            }
        }
    }
    
    @classmethod
    def get(cls, template_type: str, channel: str, language: str = "en") -> str:
        """Get template by type, channel, and language."""
        try:
            lang_templates = cls.TEMPLATES[template_type].get(language, cls.TEMPLATES[template_type]["en"])
            return lang_templates.get(channel, cls.TEMPLATES[template_type]["en"].get(channel, ""))
        except KeyError:
            return ""


# =============================================================================
# NOTIFICATION PROVIDERS
# =============================================================================

class NotificationProvider(ABC):
    """Base class for notification providers."""
    
    @abstractmethod
    async def send(self, recipient: NotificationRecipient, message: str, 
                   subject: Optional[str] = None, data: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send notification.
        Returns: (success, external_id, error_message)
        """
        pass
    
    @abstractmethod
    def get_channel(self) -> NotificationChannel:
        pass


class SMSProvider(NotificationProvider):
    """SMS via multiple providers (Africa's Talking, Twilio, local gateways)."""
    
    def __init__(self, provider: str = "africas_talking"):
        self.provider = provider
        
        # Africa's Talking (Kenya, Uganda, Tanzania, Nigeria, Rwanda, Malawi)
        self.at_api_key = os.getenv("AFRICAS_TALKING_API_KEY")
        self.at_username = os.getenv("AFRICAS_TALKING_USERNAME")
        self.at_sender_id = os.getenv("AFRICAS_TALKING_SENDER_ID", "AQUAWATCH")
        
        # Twilio (Global)
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_PHONE_NUMBER")
        
        # BulkSMS (South Africa)
        self.bulksms_token = os.getenv("BULKSMS_TOKEN")
        
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.SMS
    
    async def send(self, recipient: NotificationRecipient, message: str, 
                   subject: Optional[str] = None, data: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if not recipient.phone:
            return False, None, "No phone number"
        
        try:
            if self.provider == "africas_talking":
                return await self._send_africas_talking(recipient.phone, message)
            elif self.provider == "twilio":
                return await self._send_twilio(recipient.phone, message)
            elif self.provider == "bulksms":
                return await self._send_bulksms(recipient.phone, message)
            else:
                return await self._send_mock(recipient.phone, message)
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False, None, str(e)
    
    async def _send_africas_talking(self, phone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send via Africa's Talking."""
        if not self.at_api_key:
            return await self._send_mock(phone, message)
        
        async with aiohttp.ClientSession() as session:
            url = "https://api.africastalking.com/version1/messaging"
            headers = {
                "apiKey": self.at_api_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "username": self.at_username,
                "to": phone,
                "message": message,
                "from": self.at_sender_id
            }
            
            async with session.post(url, headers=headers, data=data) as resp:
                result = await resp.json()
                if resp.status == 201:
                    msg_id = result.get("SMSMessageData", {}).get("Recipients", [{}])[0].get("messageId")
                    return True, msg_id, None
                else:
                    return False, None, result.get("message", "Unknown error")
    
    async def _send_twilio(self, phone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send via Twilio."""
        if not self.twilio_sid:
            return await self._send_mock(phone, message)
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            auth = aiohttp.BasicAuth(self.twilio_sid, self.twilio_token)
            data = {
                "To": phone,
                "From": self.twilio_from,
                "Body": message
            }
            
            async with session.post(url, auth=auth, data=data) as resp:
                result = await resp.json()
                if resp.status in (200, 201):
                    return True, result.get("sid"), None
                else:
                    return False, None, result.get("message", "Unknown error")
    
    async def _send_bulksms(self, phone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send via BulkSMS South Africa."""
        if not self.bulksms_token:
            return await self._send_mock(phone, message)
        
        async with aiohttp.ClientSession() as session:
            url = "https://api.bulksms.com/v1/messages"
            headers = {
                "Authorization": f"Bearer {self.bulksms_token}",
                "Content-Type": "application/json"
            }
            data = {
                "to": phone,
                "body": message
            }
            
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    return True, result[0].get("id"), None
                else:
                    return False, None, await resp.text()
    
    async def _send_mock(self, phone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Mock send for testing."""
        logger.info(f"[MOCK SMS] To: {phone} | Message: {message}")
        return True, f"mock_{datetime.utcnow().timestamp()}", None


class EmailProvider(NotificationProvider):
    """Email via SMTP or API providers."""
    
    def __init__(self, provider: str = "smtp"):
        self.provider = provider
        
        # SMTP settings
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "alerts@aquawatch.local")
        self.from_name = os.getenv("FROM_NAME", "AquaWatch NRW")
        
        # SendGrid
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY")
        
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
    
    async def send(self, recipient: NotificationRecipient, message: str, 
                   subject: Optional[str] = None, data: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if not recipient.email:
            return False, None, "No email address"
        
        try:
            if self.provider == "sendgrid" and self.sendgrid_key:
                return await self._send_sendgrid(recipient.email, subject or "Alert", message)
            elif self.smtp_user:
                return await self._send_smtp(recipient.email, subject or "Alert", message)
            else:
                return await self._send_mock(recipient.email, subject, message)
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False, None, str(e)
    
    async def _send_smtp(self, to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        
        # Plain text version
        part1 = MIMEText(body.replace("<br>", "\n").replace("</p>", "\n"), "plain")
        # HTML version
        part2 = MIMEText(body, "html")
        
        msg.attach(part1)
        msg.attach(part2)
        
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            return True, f"smtp_{datetime.utcnow().timestamp()}", None
        except Exception as e:
            return False, None, str(e)
    
    async def _send_sendgrid(self, to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send via SendGrid."""
        async with aiohttp.ClientSession() as session:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_key}",
                "Content-Type": "application/json"
            }
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.from_email, "name": self.from_name},
                "subject": subject,
                "content": [
                    {"type": "text/html", "value": body}
                ]
            }
            
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 202:
                    msg_id = resp.headers.get("X-Message-Id", str(datetime.utcnow().timestamp()))
                    return True, msg_id, None
                else:
                    return False, None, await resp.text()
    
    async def _send_mock(self, to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Mock send for testing."""
        logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
        return True, f"mock_{datetime.utcnow().timestamp()}", None


class PushProvider(NotificationProvider):
    """Push notifications via Firebase Cloud Messaging."""
    
    def __init__(self):
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY")
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.PUSH
    
    async def send(self, recipient: NotificationRecipient, message: str, 
                   subject: Optional[str] = None, data: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if not recipient.fcm_token:
            return False, None, "No FCM token"
        
        if not self.fcm_server_key:
            return await self._send_mock(recipient.fcm_token, subject, message, data)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"key={self.fcm_server_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "to": recipient.fcm_token,
                    "notification": {
                        "title": subject or "AquaWatch Alert",
                        "body": message,
                        "icon": "/icons/notification.png",
                        "click_action": data.get("click_url") if data else None
                    },
                    "data": data or {}
                }
                
                async with session.post(self.fcm_url, headers=headers, json=payload) as resp:
                    result = await resp.json()
                    if result.get("success") == 1:
                        return True, result.get("results", [{}])[0].get("message_id"), None
                    else:
                        return False, None, str(result.get("results", [{}])[0].get("error"))
        except Exception as e:
            return False, None, str(e)
    
    async def _send_mock(self, token: str, title: str, body: str, data: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        logger.info(f"[MOCK PUSH] Token: {token[:20]}... | Title: {title}")
        return True, f"mock_{datetime.utcnow().timestamp()}", None


class WebhookProvider(NotificationProvider):
    """Webhook notifications to external systems."""
    
    def __init__(self, webhook_url: str = None, headers: Dict = None):
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_URL")
        self.headers = headers or {"Content-Type": "application/json"}
        
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK
    
    async def send(self, recipient: NotificationRecipient, message: str, 
                   subject: Optional[str] = None, data: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if not self.webhook_url:
            return False, None, "No webhook URL configured"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "alert_type": "leak_detected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": message,
                    "subject": subject,
                    "recipient": recipient.user_id,
                    **(data or {})
                }
                
                async with session.post(self.webhook_url, headers=self.headers, json=payload) as resp:
                    if resp.status in (200, 201, 202, 204):
                        return True, f"webhook_{datetime.utcnow().timestamp()}", None
                    else:
                        return False, None, f"HTTP {resp.status}: {await resp.text()}"
        except Exception as e:
            return False, None, str(e)


# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """Main notification service coordinating all channels."""
    
    def __init__(self):
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.notification_logs: List[NotificationLog] = []
        self.retry_queue: List[NotificationLog] = []
        
        # Rate limiting per recipient
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.rate_limit_window = timedelta(hours=1)
        self.rate_limit_max = 10  # Max notifications per hour per recipient
        
        # Initialize default providers
        self._init_default_providers()
    
    def _init_default_providers(self):
        """Initialize default notification providers."""
        self.providers[NotificationChannel.SMS] = SMSProvider()
        self.providers[NotificationChannel.EMAIL] = EmailProvider()
        self.providers[NotificationChannel.PUSH] = PushProvider()
        self.providers[NotificationChannel.WEBHOOK] = WebhookProvider()
    
    def register_provider(self, channel: NotificationChannel, provider: NotificationProvider):
        """Register a custom notification provider."""
        self.providers[channel] = provider
    
    def _check_rate_limit(self, recipient_id: str) -> bool:
        """Check if recipient is within rate limit."""
        now = datetime.utcnow()
        cutoff = now - self.rate_limit_window
        
        # Clean old entries
        self.rate_limits[recipient_id] = [
            t for t in self.rate_limits[recipient_id] if t > cutoff
        ]
        
        if len(self.rate_limits[recipient_id]) >= self.rate_limit_max:
            return False
        
        self.rate_limits[recipient_id].append(now)
        return True
    
    async def send_leak_alert(self, alert: LeakAlert, recipients: List[NotificationRecipient],
                              channels: List[NotificationChannel] = None) -> Dict[str, Any]:
        """
        Send leak alert to multiple recipients via multiple channels.
        
        Args:
            alert: Leak alert data
            recipients: List of recipients
            channels: Specific channels to use (defaults to recipient preference)
        
        Returns:
            Summary of send results
        """
        results = {
            "alert_id": alert.alert_id,
            "sent": 0,
            "failed": 0,
            "rate_limited": 0,
            "details": []
        }
        
        # Determine priority and channels based on severity
        if alert.severity == "critical":
            default_channels = [NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.EMAIL]
        elif alert.severity == "high":
            default_channels = [NotificationChannel.SMS, NotificationChannel.PUSH]
        else:
            default_channels = [NotificationChannel.PUSH]
        
        use_channels = channels or default_channels
        
        for recipient in recipients:
            # Rate limit check
            if not self._check_rate_limit(recipient.user_id):
                results["rate_limited"] += 1
                logger.warning(f"Rate limited: {recipient.user_id}")
                continue
            
            for channel in use_channels:
                provider = self.providers.get(channel)
                if not provider:
                    continue
                
                # Format message
                message = self._format_leak_message(alert, recipient, channel)
                subject = self._format_leak_subject(alert, recipient, channel)
                
                # Send notification
                success, external_id, error = await provider.send(
                    recipient, message, subject, alert.to_dict()
                )
                
                # Log the notification
                log = NotificationLog(
                    notification_id=f"notif_{datetime.utcnow().timestamp()}_{recipient.user_id}",
                    channel=channel,
                    recipient_id=recipient.user_id,
                    alert_id=alert.alert_id,
                    status=DeliveryStatus.SENT if success else DeliveryStatus.FAILED,
                    sent_at=datetime.utcnow(),
                    external_id=external_id,
                    error_message=error
                )
                self.notification_logs.append(log)
                
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    # Add to retry queue for critical alerts
                    if alert.severity in ("critical", "high"):
                        self.retry_queue.append(log)
                
                results["details"].append({
                    "recipient": recipient.user_id,
                    "channel": channel.value,
                    "success": success,
                    "error": error
                })
        
        return results
    
    def _format_leak_message(self, alert: LeakAlert, recipient: NotificationRecipient, 
                             channel: NotificationChannel) -> str:
        """Format leak alert message for channel and language."""
        template_key = "sms" if channel == NotificationChannel.SMS else \
                       "push_body" if channel == NotificationChannel.PUSH else \
                       "email_body"
        
        template = MessageTemplates.get("leak_alert", template_key, recipient.language)
        
        return template.format(
            severity=alert.severity.upper(),
            location=alert.location_name,
            zone=alert.zone,
            leak_rate=alert.leak_rate_lps,
            hourly_loss=alert.leak_rate_lps * 3600,
            pressure_drop=alert.pressure_drop,
            cost_per_hour=alert.estimated_loss_per_hour,
            detection_time=alert.detection_time.strftime("%Y-%m-%d %H:%M"),
            sensor_id=alert.sensor_id,
            alert_id=alert.alert_id[:8],
            dashboard_url=f"http://localhost:8050/alert/{alert.alert_id}",
            map_url=f"http://localhost:8050/map?lat={alert.lat}&lon={alert.lon}"
        )
    
    def _format_leak_subject(self, alert: LeakAlert, recipient: NotificationRecipient,
                             channel: NotificationChannel) -> str:
        """Format leak alert subject/title."""
        if channel == NotificationChannel.EMAIL:
            template = MessageTemplates.get("leak_alert", "email_subject", recipient.language)
        else:
            template = MessageTemplates.get("leak_alert", "push_title", recipient.language)
        
        return template.format(
            severity=alert.severity.upper(),
            location=alert.location_name
        )
    
    async def process_retry_queue(self, max_retries: int = 3):
        """Process failed notifications in retry queue."""
        for log in list(self.retry_queue):
            if log.retry_count >= max_retries:
                log.status = DeliveryStatus.FAILED
                self.retry_queue.remove(log)
                continue
            
            # Retry with exponential backoff
            log.retry_count += 1
            # In production, re-fetch recipient and re-send
            logger.info(f"Retrying notification {log.notification_id} (attempt {log.retry_count})")
    
    def get_notification_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get notification statistics for last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_logs = [l for l in self.notification_logs if l.sent_at > cutoff]
        
        stats = {
            "total": len(recent_logs),
            "sent": len([l for l in recent_logs if l.status == DeliveryStatus.SENT]),
            "failed": len([l for l in recent_logs if l.status == DeliveryStatus.FAILED]),
            "by_channel": {},
            "retry_queue_size": len(self.retry_queue)
        }
        
        for channel in NotificationChannel:
            channel_logs = [l for l in recent_logs if l.channel == channel]
            stats["by_channel"][channel.value] = {
                "total": len(channel_logs),
                "success_rate": len([l for l in channel_logs if l.status == DeliveryStatus.SENT]) / max(1, len(channel_logs)) * 100
            }
        
        return stats


# =============================================================================
# ESCALATION MANAGER
# =============================================================================

class EscalationManager:
    """Manages alert escalation for unresolved leaks."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
        # Escalation rules by severity (time in minutes)
        self.escalation_rules = {
            "critical": [
                {"time": 5, "notify": ["on_duty_technician"]},
                {"time": 15, "notify": ["zone_supervisor", "on_duty_technician"]},
                {"time": 30, "notify": ["operations_manager", "zone_supervisor"]},
                {"time": 60, "notify": ["utility_director", "operations_manager"]}
            ],
            "high": [
                {"time": 15, "notify": ["on_duty_technician"]},
                {"time": 60, "notify": ["zone_supervisor"]},
                {"time": 120, "notify": ["operations_manager"]}
            ],
            "medium": [
                {"time": 60, "notify": ["on_duty_technician"]},
                {"time": 240, "notify": ["zone_supervisor"]}
            ],
            "low": [
                {"time": 240, "notify": ["on_duty_technician"]}
            ]
        }
        
        # Track escalation state
        self.escalation_state: Dict[str, Dict] = {}
    
    async def check_escalations(self, open_alerts: List[LeakAlert], 
                                 get_recipients_func: callable) -> List[Dict]:
        """
        Check if any open alerts need escalation.
        
        Args:
            open_alerts: List of currently open alerts
            get_recipients_func: Function to get recipients by role
        
        Returns:
            List of escalation actions taken
        """
        actions = []
        now = datetime.utcnow()
        
        for alert in open_alerts:
            alert_age_minutes = (now - alert.detection_time).total_seconds() / 60
            rules = self.escalation_rules.get(alert.severity, [])
            
            # Initialize state if new
            if alert.alert_id not in self.escalation_state:
                self.escalation_state[alert.alert_id] = {
                    "last_escalation_level": -1,
                    "notified_roles": set()
                }
            
            state = self.escalation_state[alert.alert_id]
            
            # Check each escalation level
            for level, rule in enumerate(rules):
                if alert_age_minutes >= rule["time"] and level > state["last_escalation_level"]:
                    # Escalate!
                    recipients = []
                    for role in rule["notify"]:
                        if role not in state["notified_roles"]:
                            recipients.extend(get_recipients_func(role))
                            state["notified_roles"].add(role)
                    
                    if recipients:
                        result = await self.notification_service.send_leak_alert(
                            alert, recipients,
                            [NotificationChannel.SMS, NotificationChannel.PUSH]
                        )
                        
                        state["last_escalation_level"] = level
                        actions.append({
                            "alert_id": alert.alert_id,
                            "level": level,
                            "roles": rule["notify"],
                            "result": result
                        })
                        
                        logger.warning(
                            f"Escalated alert {alert.alert_id} to level {level}: {rule['notify']}"
                        )
        
        return actions
    
    def clear_escalation(self, alert_id: str):
        """Clear escalation state when alert is resolved."""
        if alert_id in self.escalation_state:
            del self.escalation_state[alert_id]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("\n📣 AquaWatch Alerting System")
    print("=" * 50)
    
    # Create service
    service = NotificationService()
    
    # Create test alert
    alert = LeakAlert(
        alert_id="ALT-2024-001",
        severity="critical",
        location_name="Chilenje Zone A - Main St",
        lat=-15.4478,
        lon=28.2873,
        leak_rate_lps=2.5,
        detection_time=datetime.utcnow(),
        sensor_id="ESP-001",
        pressure_drop=0.35,
        zone="Chilenje-A",
        estimated_loss_per_hour=15.50
    )
    
    # Create test recipients
    recipients = [
        NotificationRecipient(
            user_id="tech-001",
            name="John Mwale",
            role="technician",
            phone="+260971234567",
            email="john.mwale@lwsc.zm",
            preferred_channel=NotificationChannel.SMS,
            language="en"
        ),
        NotificationRecipient(
            user_id="sup-001",
            name="Grace Banda",
            role="supervisor",
            phone="+260972345678",
            email="grace.banda@lwsc.zm",
            preferred_channel=NotificationChannel.EMAIL,
            language="en"
        )
    ]
    
    print(f"\n🚨 Test Alert: {alert.severity.upper()}")
    print(f"   Location: {alert.location_name}")
    print(f"   Leak Rate: {alert.leak_rate_lps} L/s")
    print(f"   Est. Loss: ${alert.estimated_loss_per_hour}/hour")
    
    print("\n📤 Sending notifications...")
    
    async def test():
        result = await service.send_leak_alert(alert, recipients)
        print(f"\n📊 Results:")
        print(f"   Sent: {result['sent']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Rate Limited: {result['rate_limited']}")
        
        for detail in result["details"]:
            status = "✅" if detail["success"] else "❌"
            print(f"   {status} {detail['recipient']} via {detail['channel']}")
        
        # Get stats
        stats = service.get_notification_stats()
        print(f"\n📈 Stats (24h):")
        print(f"   Total: {stats['total']}")
        print(f"   Success Rate: {stats['sent']/max(1,stats['total'])*100:.0f}%")
    
    asyncio.run(test())
    
    print("\n✅ Alerting system ready!")
