"""
AquaWatch NRW - Remote Notification Service
==========================================

Multi-channel notifications for remote monitoring:
- SMS (Twilio) - Works in low-connectivity areas
- WhatsApp (Twilio) - Popular in Africa
- Email (SendGrid/AWS SES)
- Push Notifications (Firebase)
- Telegram Bot
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    TELEGRAM = "telegram"


class AlertSeverity(Enum):
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action within hours
    MEDIUM = "medium"      # Action within days
    LOW = "low"            # Informational


@dataclass
class NotificationPreference:
    """User notification preferences."""
    user_id: str
    channels: List[NotificationChannel]
    
    # Channel-specific settings
    phone_number: Optional[str] = None      # E.164 format: +260971234567
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    push_token: Optional[str] = None
    
    # Alert thresholds
    min_severity: AlertSeverity = AlertSeverity.HIGH
    quiet_hours_start: Optional[int] = None  # 22 = 10 PM
    quiet_hours_end: Optional[int] = None    # 6 = 6 AM
    
    # DMA filtering
    dma_ids: List[str] = None  # None = all DMAs


@dataclass 
class Notification:
    """Notification to send."""
    id: str
    recipient_id: str
    channel: NotificationChannel
    severity: AlertSeverity
    
    title: str
    message: str
    
    # Metadata
    alert_id: Optional[str] = None
    dma_id: Optional[str] = None
    device_id: Optional[str] = None
    
    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Action buttons (for rich notifications)
    actions: List[Dict] = None


# =============================================================================
# SMS NOTIFICATIONS (TWILIO)
# =============================================================================

class SMSNotificationService:
    """
    SMS notifications via Twilio.
    
    Reliable for Zambia/South Africa where mobile coverage is better than internet.
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS service initialized")
            except ImportError:
                logger.warning("twilio not installed. Run: pip install twilio")
    
    def send(self, to_number: str, message: str) -> bool:
        """
        Send SMS message.
        
        Args:
            to_number: Phone in E.164 format (+260971234567)
            message: SMS text (max 160 chars for single SMS)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            result = self.client.messages.create(
                body=message[:1600],  # Twilio limit
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent to {to_number}: {result.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False
    
    def send_alert(self, to_number: str, alert_type: str, 
                   dma_name: str, value: float, severity: str) -> bool:
        """Send formatted alert SMS."""
        
        # Severity emoji
        emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "ℹ️"}
        
        message = (
            f"{emoji.get(severity, '📊')} AQUAWATCH ALERT\n"
            f"Type: {alert_type}\n"
            f"DMA: {dma_name}\n"
            f"Value: {value:.2f}\n"
            f"Severity: {severity.upper()}\n"
            f"Time: {datetime.now().strftime('%H:%M')}\n"
            f"Reply STOP to unsubscribe"
        )
        
        return self.send(to_number, message)


# =============================================================================
# WHATSAPP NOTIFICATIONS (TWILIO)
# =============================================================================

class WhatsAppNotificationService:
    """
    WhatsApp notifications via Twilio.
    
    Very popular in Southern Africa for business communications.
    Supports rich messages with buttons.
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio WhatsApp service initialized")
            except ImportError:
                pass
    
    def send(self, to_number: str, message: str) -> bool:
        """
        Send WhatsApp message.
        
        Args:
            to_number: WhatsApp number in E.164 format
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            # Prepend 'whatsapp:' if not already
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"WhatsApp sent to {to_number}: {result.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_number}: {e}")
            return False
    
    def send_alert(self, to_number: str, alert_type: str,
                   dma_name: str, value: float, severity: str,
                   dashboard_url: str = None) -> bool:
        """Send formatted alert with dashboard link."""
        
        emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "ℹ️"}
        
        message = (
            f"{emoji.get(severity, '📊')} *AQUAWATCH ALERT*\n\n"
            f"*Type:* {alert_type}\n"
            f"*DMA:* {dma_name}\n"
            f"*Value:* {value:.2f}\n"
            f"*Severity:* {severity.upper()}\n"
            f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if dashboard_url:
            message += f"\n🔗 View Dashboard: {dashboard_url}"
        
        return self.send(to_number, message)


# =============================================================================
# EMAIL NOTIFICATIONS
# =============================================================================

class EmailNotificationService:
    """Email notifications via SendGrid or SMTP."""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "alerts@aquawatch.com")
        self.sg_client = None
        
        if self.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sg_client = SendGridAPIClient(self.sendgrid_api_key)
                logger.info("SendGrid email service initialized")
            except ImportError:
                logger.warning("sendgrid not installed. Run: pip install sendgrid")
    
    def send(self, to_email: str, subject: str, html_content: str, 
             text_content: str = None) -> bool:
        """Send email."""
        
        if self.sg_client:
            return self._send_sendgrid(to_email, subject, html_content, text_content)
        else:
            return self._send_smtp(to_email, subject, html_content, text_content)
    
    def _send_sendgrid(self, to_email: str, subject: str, 
                       html_content: str, text_content: str) -> bool:
        """Send via SendGrid API."""
        try:
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            response = self.sg_client.send(message)
            logger.info(f"Email sent to {to_email}: {response.status_code}")
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_smtp(self, to_email: str, subject: str,
                   html_content: str, text_content: str) -> bool:
        """Fallback SMTP sending."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_pass:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False
    
    def send_alert(self, to_email: str, alert_type: str,
                   dma_name: str, value: float, severity: str,
                   dashboard_url: str = None) -> bool:
        """Send formatted alert email."""
        
        subject = f"[{severity.upper()}] AquaWatch Alert: {alert_type} in {dma_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .critical {{ background: #ffe6e6; border-left: 4px solid #e2445c; }}
                .high {{ background: #fff3e6; border-left: 4px solid #fdab3d; }}
                .medium {{ background: #e6f3ff; border-left: 4px solid #579bfc; }}
                .low {{ background: #e6ffe6; border-left: 4px solid #00c875; }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #0073ea;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>🚰 AquaWatch NRW Alert</h2>
            
            <div class="alert-box {severity}">
                <h3>{alert_type}</h3>
                <p><strong>Location:</strong> {dma_name}</p>
                <p><strong>Value:</strong> {value:.2f}</p>
                <p><strong>Severity:</strong> {severity.upper()}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            {"<a href='" + dashboard_url + "' class='btn'>View Dashboard</a>" if dashboard_url else ""}
            
            <hr style="margin-top: 40px;">
            <p style="color: #666; font-size: 12px;">
                You received this alert because you're subscribed to AquaWatch notifications.
                <br>
                To update your preferences, visit the dashboard settings.
            </p>
        </body>
        </html>
        """
        
        text_content = f"""
        AQUAWATCH NRW ALERT
        
        Type: {alert_type}
        Location: {dma_name}
        Value: {value:.2f}
        Severity: {severity.upper()}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        {"Dashboard: " + dashboard_url if dashboard_url else ""}
        """
        
        return self.send(to_email, subject, html_content, text_content)


# =============================================================================
# TELEGRAM BOT
# =============================================================================

class TelegramNotificationService:
    """
    Telegram bot notifications.
    
    Good alternative for areas where WhatsApp is throttled.
    Supports rich formatting and inline buttons.
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
    
    def send(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Send Telegram message."""
        if not self.api_url:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            import requests
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode
                }
            )
            
            if response.ok:
                logger.info(f"Telegram message sent to {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_alert(self, chat_id: str, alert_type: str,
                   dma_name: str, value: float, severity: str,
                   dashboard_url: str = None) -> bool:
        """Send formatted alert."""
        
        emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "ℹ️"}
        
        message = (
            f"{emoji.get(severity, '📊')} <b>AQUAWATCH ALERT</b>\n\n"
            f"<b>Type:</b> {alert_type}\n"
            f"<b>DMA:</b> {dma_name}\n"
            f"<b>Value:</b> {value:.2f}\n"
            f"<b>Severity:</b> {severity.upper()}\n"
            f"<b>Time:</b> {datetime.now().strftime('%H:%M')}\n"
        )
        
        if dashboard_url:
            message += f"\n<a href='{dashboard_url}'>📱 Open Dashboard</a>"
        
        return self.send(chat_id, message, "HTML")


# =============================================================================
# UNIFIED NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """
    Unified notification service that routes alerts to appropriate channels.
    """
    
    def __init__(self):
        self.sms = SMSNotificationService()
        self.whatsapp = WhatsAppNotificationService()
        self.email = EmailNotificationService()
        self.telegram = TelegramNotificationService()
        
        # User preferences storage (use database in production)
        self.preferences: Dict[str, NotificationPreference] = {}
    
    def set_user_preference(self, pref: NotificationPreference):
        """Store user notification preference."""
        self.preferences[pref.user_id] = pref
    
    def get_user_preference(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user notification preference."""
        return self.preferences.get(user_id)
    
    def send_alert(self, user_id: str, alert_type: str, dma_id: str,
                   dma_name: str, value: float, severity: AlertSeverity,
                   dashboard_url: str = None) -> Dict[str, bool]:
        """
        Send alert to user via their preferred channels.
        
        Returns:
            Dict of channel -> success status
        """
        pref = self.get_user_preference(user_id)
        
        if not pref:
            logger.warning(f"No notification preference for user {user_id}")
            return {}
        
        # Check severity threshold
        severity_order = [AlertSeverity.LOW, AlertSeverity.MEDIUM, 
                         AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        if severity_order.index(severity) < severity_order.index(pref.min_severity):
            logger.debug(f"Alert below threshold for user {user_id}")
            return {}
        
        # Check DMA filter
        if pref.dma_ids and dma_id not in pref.dma_ids:
            logger.debug(f"DMA {dma_id} not in user {user_id} filter")
            return {}
        
        # Check quiet hours
        current_hour = datetime.now().hour
        if pref.quiet_hours_start and pref.quiet_hours_end:
            if pref.quiet_hours_start <= current_hour or current_hour < pref.quiet_hours_end:
                # In quiet hours - only send critical
                if severity != AlertSeverity.CRITICAL:
                    logger.debug(f"In quiet hours for user {user_id}")
                    return {}
        
        results = {}
        
        for channel in pref.channels:
            try:
                if channel == NotificationChannel.SMS and pref.phone_number:
                    results["sms"] = self.sms.send_alert(
                        pref.phone_number, alert_type, dma_name, 
                        value, severity.value
                    )
                
                elif channel == NotificationChannel.WHATSAPP and pref.whatsapp_number:
                    results["whatsapp"] = self.whatsapp.send_alert(
                        pref.whatsapp_number, alert_type, dma_name,
                        value, severity.value, dashboard_url
                    )
                
                elif channel == NotificationChannel.EMAIL and pref.email:
                    results["email"] = self.email.send_alert(
                        pref.email, alert_type, dma_name,
                        value, severity.value, dashboard_url
                    )
                
                elif channel == NotificationChannel.TELEGRAM and pref.telegram_chat_id:
                    results["telegram"] = self.telegram.send_alert(
                        pref.telegram_chat_id, alert_type, dma_name,
                        value, severity.value, dashboard_url
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
                results[channel.value] = False
        
        return results
    
    def broadcast_alert(self, alert_type: str, dma_id: str, dma_name: str,
                        value: float, severity: AlertSeverity,
                        dashboard_url: str = None) -> Dict[str, Dict[str, bool]]:
        """
        Broadcast alert to all subscribed users.
        
        Returns:
            Dict of user_id -> channel results
        """
        results = {}
        
        for user_id in self.preferences:
            user_results = self.send_alert(
                user_id, alert_type, dma_id, dma_name,
                value, severity, dashboard_url
            )
            if user_results:
                results[user_id] = user_results
        
        logger.info(f"Broadcast alert to {len(results)} users")
        return results


# =============================================================================
# GLOBAL NOTIFICATION SERVICE
# =============================================================================

notification_service = NotificationService()
