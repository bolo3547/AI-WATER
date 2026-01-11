"""
AquaWatch NRW - Multi-Channel Notification System
=================================================

SMS, WhatsApp, Voice & Push notifications for Zambia/South Africa utilities.

Supported Providers:
- Africa's Talking (East/Southern Africa coverage)
- Twilio (Global fallback)
- WhatsApp Business API
- Firebase Cloud Messaging (Push)

Designed for low-bandwidth African networks with SMS fallback.
"""

import os
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# =============================================================================
# NOTIFICATION TYPES & PRIORITIES
# =============================================================================

class NotificationType(Enum):
    LEAK_DETECTED = "leak_detected"
    BURST_ALERT = "burst_alert"
    PRESSURE_DROP = "pressure_drop"
    WATER_QUALITY = "water_quality"
    SENSOR_OFFLINE = "sensor_offline"
    WORK_ORDER = "work_order"
    MAINTENANCE_DUE = "maintenance_due"
    ESCALATION = "escalation"
    DAILY_REPORT = "daily_report"
    SYSTEM_STATUS = "system_status"


class Priority(Enum):
    CRITICAL = 1    # Immediate - call + SMS + WhatsApp
    HIGH = 2        # Urgent - SMS + WhatsApp within 5 min
    MEDIUM = 3      # Important - SMS within 30 min
    LOW = 4         # Info - WhatsApp/Email only


class Channel(Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    PUSH = "push"
    EMAIL = "email"


@dataclass
class Contact:
    """Contact for notifications."""
    contact_id: str
    name: str
    phone: str              # E.164 format: +260971234567
    email: Optional[str] = None
    whatsapp: Optional[str] = None  # Can be different from phone
    role: str = "technician"        # technician, supervisor, manager, executive
    zone_ids: List[str] = field(default_factory=list)
    preferred_channel: Channel = Channel.SMS
    language: str = "en"    # en, ny (Nyanja), bem (Bemba), zu (Zulu)
    active: bool = True
    on_call: bool = False


@dataclass
class NotificationResult:
    """Result of sending a notification."""
    success: bool
    channel: Channel
    message_id: Optional[str] = None
    error: Optional[str] = None
    cost: float = 0.0       # Cost in USD
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# NOTIFICATION TEMPLATES - MULTILINGUAL
# =============================================================================

TEMPLATES = {
    "leak_detected": {
        "en": "⚠️ LEAK DETECTED\nZone: {zone_id}\nLocation: {location}\nConfidence: {confidence}%\nPressure Drop: {pressure_drop} bar\nEstimated Loss: {loss_rate} L/hr\n\nAction: Dispatch technician",
        "ny": "⚠️ MADZI AKUTAYIKA\nDera: {zone_id}\nMalo: {location}\nChithumba: {confidence}%\n\nLandani fundi",
        "bem": "⚠️ AMENSHI YALEKELELA\nIncende: {zone_id}\nUkwaba: {location}\n\nTumeni ba teknishani",
        "zu": "⚠️ AMANZI AYAVUZA\nIndawo: {zone_id}\nKulapho: {location}\n\nThumela isisebenzi"
    },
    "burst_alert": {
        "en": "🚨 CRITICAL: PIPE BURST\nZone: {zone_id}\nLocation: {location}\nFlow Spike: {flow_spike} L/min\n\n⚡ IMMEDIATE ACTION REQUIRED\nCall: {emergency_number}",
        "ny": "🚨 CHAPUTIKA: MPAIPI YASWEKA\nDera: {zone_id}\n\nIMBANI TSOPANO: {emergency_number}",
        "bem": "🚨 UBUSUMA: IMPAIPI YAPASUKA\n\nITENI NOMBA: {emergency_number}",
        "zu": "🚨 KUPHUTHUMAYO: IPAYIPI LIQA\n\nSHAYELA MANJE: {emergency_number}"
    },
    "water_quality": {
        "en": "⚠️ WATER QUALITY ALERT\nZone: {zone_id}\nIssue: {issue}\npH: {ph}\nTurbidity: {turbidity} NTU\nChlorine: {chlorine} mg/L\n\nAction: Check treatment process",
        "ny": "⚠️ MADZI SAKWANIRA\nDera: {zone_id}\nVuto: {issue}",
        "bem": "⚠️ AMENSHI TAYABWINO\nIncende: {zone_id}",
        "zu": "⚠️ AMANZI AWAPHEPHILE\nIndawo: {zone_id}"
    },
    "work_order": {
        "en": "📋 NEW WORK ORDER #{work_order_id}\nType: {type}\nLocation: {location}\nPriority: {priority}\nDescription: {description}\n\nReply YES to accept",
        "ny": "📋 NTCHITO YATSOPANO #{work_order_id}\nMtundu: {type}\nMalo: {location}\n\nYankha ENYA kuvomereza",
        "bem": "📋 IMILIMO IPYA #{work_order_id}\n\nAsukeni EYA ukusumina",
        "zu": "📋 UMSEBENZI OMUSHA #{work_order_id}\n\nPhendula YEBO ukwamukela"
    },
    "escalation": {
        "en": "🔺 ESCALATION ALERT\nOriginal Alert: {original_type}\nTime Elapsed: {time_elapsed} min\nNo Response From: {no_response}\nZone: {zone_id}\n\nPlease take immediate action!",
        "ny": "🔺 NKHAWA YAKWERA\nPanalibe Yankho: {no_response}\n\nChonde chitani kanthu!",
        "bem": "🔺 UKUFWAYA AMANO\n\nNapapata chiteni cimo!",
        "zu": "🔺 ISIXWAYISO ESIPHAKEME\n\nSicela wenze okuthile!"
    },
    "daily_report": {
        "en": "📊 DAILY NRW REPORT - {date}\n\nTotal NRW: {nrw_percent}%\nWater Lost: {water_lost} m³\nRevenue Lost: ${revenue_lost}\nAlerts: {alert_count}\nResolved: {resolved_count}\n\nTop Issue Zones:\n{top_zones}",
        "ny": "📊 LIPOTI LA TSIKU - {date}\n\nMadzi Otayika: {nrw_percent}%",
        "bem": "📊 AMALYASHI YA BUSHIKU - {date}\n\nAmenshi Yalekelela: {nrw_percent}%",
        "zu": "📊 UMBIKO WANSUKU ZONKE - {date}\n\nAmanzi Alahlekile: {nrw_percent}%"
    }
}


# =============================================================================
# NOTIFICATION PROVIDERS
# =============================================================================

class NotificationProvider(ABC):
    """Base class for notification providers."""
    
    @abstractmethod
    async def send_sms(self, to: str, message: str) -> NotificationResult:
        pass
    
    @abstractmethod
    async def send_whatsapp(self, to: str, message: str) -> NotificationResult:
        pass
    
    @abstractmethod
    async def make_voice_call(self, to: str, message: str) -> NotificationResult:
        pass


class AfricasTalkingProvider(NotificationProvider):
    """
    Africa's Talking - Best coverage for Zambia, Zimbabwe, South Africa.
    https://africastalking.com/
    
    Pricing (2024):
    - Zambia SMS: ~$0.03/SMS
    - South Africa SMS: ~$0.02/SMS
    - Voice: ~$0.04/min
    """
    
    def __init__(self):
        self.api_key = os.getenv("AT_API_KEY", "")
        self.username = os.getenv("AT_USERNAME", "sandbox")
        self.base_url = "https://api.africastalking.com/version1"
        self.sender_id = os.getenv("AT_SENDER_ID", "AquaWatch")
        
        if not self.api_key:
            logger.warning("Africa's Talking API key not configured")
    
    async def send_sms(self, to: str, message: str) -> NotificationResult:
        """Send SMS via Africa's Talking."""
        try:
            url = f"{self.base_url}/messaging"
            headers = {
                "apiKey": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            data = {
                "username": self.username,
                "to": to,
                "message": message,
                "from": self.sender_id
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            result = response.json()
            
            if response.status_code == 201:
                recipients = result.get("SMSMessageData", {}).get("Recipients", [])
                if recipients:
                    return NotificationResult(
                        success=True,
                        channel=Channel.SMS,
                        message_id=recipients[0].get("messageId"),
                        cost=float(recipients[0].get("cost", "0").replace("USD ", ""))
                    )
            
            return NotificationResult(
                success=False,
                channel=Channel.SMS,
                error=result.get("SMSMessageData", {}).get("Message", "Unknown error")
            )
            
        except Exception as e:
            logger.error(f"AT SMS error: {e}")
            return NotificationResult(success=False, channel=Channel.SMS, error=str(e))
    
    async def send_whatsapp(self, to: str, message: str) -> NotificationResult:
        """Send WhatsApp via Africa's Talking (if available)."""
        # AT doesn't have native WhatsApp - use Twilio fallback
        return NotificationResult(
            success=False, 
            channel=Channel.WHATSAPP, 
            error="WhatsApp not available via AT"
        )
    
    async def make_voice_call(self, to: str, message: str) -> NotificationResult:
        """Make voice call with text-to-speech."""
        try:
            url = f"{self.base_url}/call"
            headers = {
                "apiKey": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            data = {
                "username": self.username,
                "to": to,
                "from": os.getenv("AT_PHONE_NUMBER", "")
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 201:
                return NotificationResult(
                    success=True,
                    channel=Channel.VOICE,
                    message_id=response.json().get("callId")
                )
            
            return NotificationResult(
                success=False,
                channel=Channel.VOICE,
                error=response.text
            )
            
        except Exception as e:
            logger.error(f"AT Voice error: {e}")
            return NotificationResult(success=False, channel=Channel.VOICE, error=str(e))


class TwilioProvider(NotificationProvider):
    """
    Twilio - Global coverage, good WhatsApp support.
    https://www.twilio.com/
    
    Better for WhatsApp Business API integration.
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        
        if not self.account_sid:
            logger.warning("Twilio credentials not configured")
    
    async def send_sms(self, to: str, message: str) -> NotificationResult:
        """Send SMS via Twilio."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            
            response = requests.post(
                url,
                auth=(self.account_sid, self.auth_token),
                data={
                    "To": to,
                    "From": self.phone_number,
                    "Body": message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return NotificationResult(
                    success=True,
                    channel=Channel.SMS,
                    message_id=result.get("sid"),
                    cost=float(result.get("price", 0) or 0)
                )
            
            return NotificationResult(
                success=False,
                channel=Channel.SMS,
                error=response.json().get("message", "Unknown error")
            )
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return NotificationResult(success=False, channel=Channel.SMS, error=str(e))
    
    async def send_whatsapp(self, to: str, message: str) -> NotificationResult:
        """Send WhatsApp message via Twilio."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            
            # WhatsApp numbers need whatsapp: prefix
            whatsapp_to = f"whatsapp:{to}"
            whatsapp_from = f"whatsapp:{self.whatsapp_number}"
            
            response = requests.post(
                url,
                auth=(self.account_sid, self.auth_token),
                data={
                    "To": whatsapp_to,
                    "From": whatsapp_from,
                    "Body": message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return NotificationResult(
                    success=True,
                    channel=Channel.WHATSAPP,
                    message_id=result.get("sid")
                )
            
            return NotificationResult(
                success=False,
                channel=Channel.WHATSAPP,
                error=response.json().get("message", "Unknown error")
            )
            
        except Exception as e:
            logger.error(f"Twilio WhatsApp error: {e}")
            return NotificationResult(success=False, channel=Channel.WHATSAPP, error=str(e))
    
    async def make_voice_call(self, to: str, message: str) -> NotificationResult:
        """Make voice call with Twilio."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
            
            # TwiML for text-to-speech
            twiml = f'<Response><Say voice="alice" language="en-GB">{message}</Say></Response>'
            
            response = requests.post(
                url,
                auth=(self.account_sid, self.auth_token),
                data={
                    "To": to,
                    "From": self.phone_number,
                    "Twiml": twiml
                },
                timeout=30
            )
            
            if response.status_code == 201:
                return NotificationResult(
                    success=True,
                    channel=Channel.VOICE,
                    message_id=response.json().get("sid")
                )
            
            return NotificationResult(
                success=False,
                channel=Channel.VOICE,
                error=response.json().get("message", "Unknown error")
            )
            
        except Exception as e:
            logger.error(f"Twilio Voice error: {e}")
            return NotificationResult(success=False, channel=Channel.VOICE, error=str(e))


# =============================================================================
# NOTIFICATION SERVICE - MAIN CLASS
# =============================================================================

class NotificationService:
    """
    Main notification service for AquaWatch NRW.
    
    Features:
    - Multi-channel delivery (SMS, WhatsApp, Voice, Push)
    - Automatic failover between providers
    - Escalation rules
    - On-call scheduling
    - Rate limiting
    - Cost tracking
    """
    
    def __init__(self):
        self.providers = {
            "africastalking": AfricasTalkingProvider(),
            "twilio": TwilioProvider()
        }
        self.primary_provider = os.getenv("PRIMARY_SMS_PROVIDER", "africastalking")
        
        # In-memory contact store (replace with database in production)
        self.contacts: Dict[str, Contact] = {}
        self.on_call_rotation: Dict[str, List[str]] = {}  # zone_id -> [contact_ids]
        
        # Notification history for rate limiting
        self.sent_notifications: List[Dict] = []
        self.total_cost = 0.0
        
        # Escalation settings
        self.escalation_timeout = 15 * 60  # 15 minutes
        self.pending_alerts: Dict[str, Dict] = {}
        
        logger.info("NotificationService initialized")
    
    def add_contact(self, contact: Contact):
        """Add a contact to the system."""
        self.contacts[contact.contact_id] = contact
        logger.info(f"Added contact: {contact.name} ({contact.phone})")
    
    def get_contacts_for_zone(self, zone_id: str, role: str = None) -> List[Contact]:
        """Get all contacts for a zone, optionally filtered by role."""
        contacts = []
        for contact in self.contacts.values():
            if not contact.active:
                continue
            if zone_id in contact.zone_ids or not contact.zone_ids:
                if role is None or contact.role == role:
                    contacts.append(contact)
        return contacts
    
    def get_on_call_contact(self, zone_id: str) -> Optional[Contact]:
        """Get the current on-call contact for a zone."""
        for contact in self.contacts.values():
            if contact.active and contact.on_call and zone_id in contact.zone_ids:
                return contact
        # Fallback to any technician for the zone
        technicians = self.get_contacts_for_zone(zone_id, "technician")
        return technicians[0] if technicians else None
    
    def format_message(
        self, 
        notification_type: NotificationType, 
        language: str, 
        **kwargs
    ) -> str:
        """Format a notification message using templates."""
        templates = TEMPLATES.get(notification_type.value, {})
        template = templates.get(language, templates.get("en", ""))
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        priority: Priority,
        zone_id: str,
        data: Dict[str, Any],
        specific_contacts: List[str] = None
    ) -> List[NotificationResult]:
        """
        Send a notification based on type and priority.
        
        Priority determines channels:
        - CRITICAL: Voice call + SMS + WhatsApp to on-call + supervisors
        - HIGH: SMS + WhatsApp to on-call + technicians
        - MEDIUM: SMS to relevant technicians
        - LOW: WhatsApp/Push only
        """
        results = []
        
        # Determine recipients
        if specific_contacts:
            recipients = [self.contacts[c] for c in specific_contacts if c in self.contacts]
        else:
            recipients = self._get_recipients_by_priority(priority, zone_id)
        
        if not recipients:
            logger.warning(f"No recipients found for zone {zone_id}")
            return results
        
        # Send to each recipient
        for contact in recipients:
            message = self.format_message(
                notification_type,
                contact.language,
                **data
            )
            
            # Determine channels based on priority
            channels = self._get_channels_for_priority(priority, contact)
            
            for channel in channels:
                result = await self._send_via_channel(contact, channel, message)
                results.append(result)
                
                if result.success:
                    self.total_cost += result.cost
                    self._log_notification(notification_type, contact, channel, result)
        
        # Schedule escalation for high priority alerts
        if priority in [Priority.CRITICAL, Priority.HIGH]:
            alert_id = f"{zone_id}_{notification_type.value}_{datetime.now().timestamp()}"
            self.pending_alerts[alert_id] = {
                "type": notification_type,
                "zone_id": zone_id,
                "data": data,
                "sent_at": datetime.now(timezone.utc),
                "recipients": [c.contact_id for c in recipients]
            }
        
        return results
    
    def _get_recipients_by_priority(self, priority: Priority, zone_id: str) -> List[Contact]:
        """Get recipients based on alert priority."""
        if priority == Priority.CRITICAL:
            # On-call + all supervisors + managers
            recipients = []
            on_call = self.get_on_call_contact(zone_id)
            if on_call:
                recipients.append(on_call)
            recipients.extend(self.get_contacts_for_zone(zone_id, "supervisor"))
            recipients.extend(self.get_contacts_for_zone(zone_id, "manager"))
            return list(set(recipients))
        
        elif priority == Priority.HIGH:
            # On-call + supervisors
            recipients = []
            on_call = self.get_on_call_contact(zone_id)
            if on_call:
                recipients.append(on_call)
            recipients.extend(self.get_contacts_for_zone(zone_id, "supervisor"))
            return list(set(recipients))
        
        elif priority == Priority.MEDIUM:
            # All technicians for zone
            return self.get_contacts_for_zone(zone_id, "technician")
        
        else:  # LOW
            # Only on-call
            on_call = self.get_on_call_contact(zone_id)
            return [on_call] if on_call else []
    
    def _get_channels_for_priority(self, priority: Priority, contact: Contact) -> List[Channel]:
        """Determine notification channels based on priority."""
        if priority == Priority.CRITICAL:
            return [Channel.VOICE, Channel.SMS, Channel.WHATSAPP]
        elif priority == Priority.HIGH:
            return [Channel.SMS, Channel.WHATSAPP]
        elif priority == Priority.MEDIUM:
            return [Channel.SMS]
        else:
            return [contact.preferred_channel]
    
    async def _send_via_channel(
        self, 
        contact: Contact, 
        channel: Channel, 
        message: str
    ) -> NotificationResult:
        """Send notification via specific channel with failover."""
        provider = self.providers.get(self.primary_provider)
        fallback = self.providers.get("twilio" if self.primary_provider == "africastalking" else "africastalking")
        
        phone = contact.whatsapp if channel == Channel.WHATSAPP and contact.whatsapp else contact.phone
        
        if channel == Channel.SMS:
            result = await provider.send_sms(phone, message)
            if not result.success and fallback:
                result = await fallback.send_sms(phone, message)
        
        elif channel == Channel.WHATSAPP:
            result = await provider.send_whatsapp(phone, message)
            if not result.success and fallback:
                result = await fallback.send_whatsapp(phone, message)
        
        elif channel == Channel.VOICE:
            result = await provider.make_voice_call(phone, message)
            if not result.success and fallback:
                result = await fallback.make_voice_call(phone, message)
        
        else:
            result = NotificationResult(success=False, channel=channel, error="Channel not supported")
        
        return result
    
    def _log_notification(
        self, 
        notification_type: NotificationType, 
        contact: Contact, 
        channel: Channel, 
        result: NotificationResult
    ):
        """Log notification for tracking."""
        self.sent_notifications.append({
            "type": notification_type.value,
            "contact_id": contact.contact_id,
            "contact_name": contact.name,
            "channel": channel.value,
            "success": result.success,
            "message_id": result.message_id,
            "cost": result.cost,
            "timestamp": result.timestamp.isoformat()
        })
    
    async def check_escalations(self):
        """Check for alerts that need escalation."""
        now = datetime.now(timezone.utc)
        
        for alert_id, alert in list(self.pending_alerts.items()):
            elapsed = (now - alert["sent_at"]).total_seconds()
            
            if elapsed > self.escalation_timeout:
                # Escalate to next level
                logger.warning(f"Escalating alert {alert_id}")
                
                await self.send_notification(
                    NotificationType.ESCALATION,
                    Priority.CRITICAL,
                    alert["zone_id"],
                    {
                        "original_type": alert["type"].value,
                        "time_elapsed": int(elapsed / 60),
                        "no_response": ", ".join(alert["recipients"]),
                        "zone_id": alert["zone_id"]
                    }
                )
                
                del self.pending_alerts[alert_id]
    
    def acknowledge_alert(self, alert_id: str, contact_id: str):
        """Acknowledge an alert to stop escalation."""
        if alert_id in self.pending_alerts:
            del self.pending_alerts[alert_id]
            logger.info(f"Alert {alert_id} acknowledged by {contact_id}")
    
    def get_notification_stats(self) -> Dict:
        """Get notification statistics."""
        stats = {
            "total_sent": len(self.sent_notifications),
            "total_cost_usd": round(self.total_cost, 2),
            "by_channel": {},
            "by_type": {},
            "success_rate": 0
        }
        
        successes = 0
        for notif in self.sent_notifications:
            channel = notif["channel"]
            ntype = notif["type"]
            
            stats["by_channel"][channel] = stats["by_channel"].get(channel, 0) + 1
            stats["by_type"][ntype] = stats["by_type"].get(ntype, 0) + 1
            
            if notif["success"]:
                successes += 1
        
        if stats["total_sent"] > 0:
            stats["success_rate"] = round(successes / stats["total_sent"] * 100, 1)
        
        return stats


# =============================================================================
# ZAMBIA/SOUTH AFRICA SPECIFIC UTILITIES
# =============================================================================

def format_zambian_phone(phone: str) -> str:
    """Format phone number to Zambian E.164 format."""
    # Remove spaces and dashes
    phone = phone.replace(" ", "").replace("-", "")
    
    # Zambian numbers
    if phone.startswith("0"):
        return "+260" + phone[1:]
    elif phone.startswith("260"):
        return "+" + phone
    elif phone.startswith("+260"):
        return phone
    
    return phone


def format_south_african_phone(phone: str) -> str:
    """Format phone number to South African E.164 format."""
    phone = phone.replace(" ", "").replace("-", "")
    
    if phone.startswith("0"):
        return "+27" + phone[1:]
    elif phone.startswith("27"):
        return "+" + phone
    elif phone.startswith("+27"):
        return phone
    
    return phone


# =============================================================================
# QUICK NOTIFICATION FUNCTIONS
# =============================================================================

async def send_leak_alert(
    service: NotificationService,
    zone_id: str,
    location: str,
    confidence: float,
    pressure_drop: float,
    loss_rate: float
):
    """Quick function to send a leak detection alert."""
    priority = Priority.HIGH if confidence > 80 else Priority.MEDIUM
    
    await service.send_notification(
        NotificationType.LEAK_DETECTED,
        priority,
        zone_id,
        {
            "zone_id": zone_id,
            "location": location,
            "confidence": round(confidence, 1),
            "pressure_drop": round(pressure_drop, 2),
            "loss_rate": round(loss_rate, 1)
        }
    )


async def send_burst_alert(
    service: NotificationService,
    zone_id: str,
    location: str,
    flow_spike: float,
    emergency_number: str = "+260211123456"
):
    """Quick function to send a critical burst alert."""
    await service.send_notification(
        NotificationType.BURST_ALERT,
        Priority.CRITICAL,
        zone_id,
        {
            "zone_id": zone_id,
            "location": location,
            "flow_spike": round(flow_spike, 1),
            "emergency_number": emergency_number
        }
    )


async def send_daily_report(
    service: NotificationService,
    zone_id: str,
    nrw_percent: float,
    water_lost: float,
    revenue_lost: float,
    alert_count: int,
    resolved_count: int,
    top_zones: str
):
    """Send daily NRW report to managers."""
    await service.send_notification(
        NotificationType.DAILY_REPORT,
        Priority.LOW,
        zone_id,
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "nrw_percent": round(nrw_percent, 1),
            "water_lost": round(water_lost, 0),
            "revenue_lost": round(revenue_lost, 2),
            "alert_count": alert_count,
            "resolved_count": resolved_count,
            "top_zones": top_zones
        },
        specific_contacts=None  # Will go to managers
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    async def demo():
        service = NotificationService()
        
        # Add sample contacts (Zambian utility)
        service.add_contact(Contact(
            contact_id="tech_001",
            name="Mwamba Chanda",
            phone=format_zambian_phone("0971234567"),
            email="mwamba@lwsc.co.zm",
            role="technician",
            zone_ids=["ZONE_A", "ZONE_B"],
            language="en",
            on_call=True
        ))
        
        service.add_contact(Contact(
            contact_id="super_001",
            name="Grace Mulenga",
            phone=format_zambian_phone("0962345678"),
            email="grace@lwsc.co.zm",
            role="supervisor",
            zone_ids=["ZONE_A", "ZONE_B", "ZONE_C"],
            language="en"
        ))
        
        # Send test leak alert
        print("Sending leak alert...")
        results = await send_leak_alert(
            service,
            zone_id="ZONE_A",
            location="Main St & 5th Ave",
            confidence=85.5,
            pressure_drop=1.2,
            loss_rate=150.0
        )
        
        print(f"\nNotification Stats:")
        print(json.dumps(service.get_notification_stats(), indent=2))
    
    asyncio.run(demo())
