"""
AquaWatch NRW - REST API for Remote Access
==========================================

Full REST API for mobile apps, remote dashboards, and third-party integrations.

Base URL: https://api.aquawatch.example.com/v1

Authentication:
- Bearer token (JWT) for users
- API Key (X-API-Key header) for devices
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
import logging

try:
    from fastapi import FastAPI, Depends, HTTPException, status, Query, Path, Header
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, EmailStr
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Run: pip install fastapi uvicorn")

from .auth import (
    auth_service, User, UserRole, Permission,
    get_current_user, require_permission, verify_api_key_header
)
from .notifications import notification_service, NotificationPreference, NotificationChannel, AlertSeverity

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS (Request/Response)
# =============================================================================

if FASTAPI_AVAILABLE:
    
    # Auth Models
    class LoginRequest(BaseModel):
        email: EmailStr
        password: str
    
    class LoginResponse(BaseModel):
        access_token: str
        refresh_token: str
        token_type: str = "bearer"
        expires_in: int
        user: dict
    
    class RefreshRequest(BaseModel):
        refresh_token: str
    
    class RegisterRequest(BaseModel):
        email: EmailStr
        password: str = Field(min_length=8)
        full_name: str
        phone: Optional[str] = None
        utility_id: Optional[str] = None
    
    class UserResponse(BaseModel):
        id: str
        email: str
        role: str
        full_name: str
        utility_id: Optional[str]
        is_active: bool
    
    # DMA Models
    class DMAResponse(BaseModel):
        id: str
        name: str
        utility_id: str
        location: dict
        device_count: int
        current_nrw_pct: float
        last_updated: datetime
    
    class DMAListResponse(BaseModel):
        dmas: List[DMAResponse]
        total: int
    
    # Alert Models
    class AlertResponse(BaseModel):
        id: str
        type: str
        severity: str
        dma_id: str
        dma_name: str
        device_id: Optional[str]
        value: float
        timestamp: datetime
        acknowledged: bool
        acknowledged_by: Optional[str]
        notes: Optional[str]
    
    class AlertListResponse(BaseModel):
        alerts: List[AlertResponse]
        total: int
        unacknowledged: int
    
    class AcknowledgeAlertRequest(BaseModel):
        notes: Optional[str] = None
    
    # Reading Models
    class SensorReadingResponse(BaseModel):
        device_id: str
        sensor_type: str
        value: float
        unit: str
        quality: str
        timestamp: datetime
    
    class ReadingsListResponse(BaseModel):
        readings: List[SensorReadingResponse]
        total: int
    
    # Device Models
    class DeviceResponse(BaseModel):
        id: str
        dma_id: str
        sensor_type: str
        status: str
        battery_pct: Optional[float]
        signal_strength: Optional[int]
        last_seen: Optional[datetime]
        firmware_version: Optional[str]
    
    class DeviceListResponse(BaseModel):
        devices: List[DeviceResponse]
        total: int
        online: int
        offline: int
    
    # Notification Models
    class NotificationPreferenceRequest(BaseModel):
        channels: List[str]  # ["sms", "whatsapp", "email"]
        phone_number: Optional[str] = None
        whatsapp_number: Optional[str] = None
        email: Optional[str] = None
        telegram_chat_id: Optional[str] = None
        min_severity: str = "high"
        quiet_hours_start: Optional[int] = None
        quiet_hours_end: Optional[int] = None
        dma_ids: Optional[List[str]] = None
    
    # Stats Models
    class NRWStatsResponse(BaseModel):
        utility_id: str
        period: str
        total_input: float  # m³
        authorized_consumption: float
        nrw_volume: float
        nrw_percentage: float
        real_losses: float
        apparent_losses: float
        cost_of_nrw: float
    
    class DashboardSummaryResponse(BaseModel):
        total_dmas: int
        total_devices: int
        devices_online: int
        active_alerts: int
        critical_alerts: int
        avg_nrw_pct: float
        last_24h_alerts: int


# =============================================================================
# API APPLICATION
# =============================================================================

def create_api() -> 'FastAPI':
    """Create FastAPI application."""
    
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI not installed")
    
    # -------------------------------------------------------------------------
    # LIFECYCLE (modern lifespan pattern)
    # -------------------------------------------------------------------------
    
    @asynccontextmanager
    async def lifespan(app):
        """Manage startup and shutdown lifecycle."""
        # Startup
        logger.info("AquaWatch NRW API starting up...")
        try:
            from src.config.settings import validate_config
            warnings = validate_config()
            for w in warnings:
                logger.warning(w)
        except Exception as e:
            logger.warning(f"Config validation skipped: {e}")
        logger.info("AquaWatch NRW API ready")
        
        yield  # Application runs here
        
        # Shutdown
        logger.info("AquaWatch NRW API shutting down...")
    
    app = FastAPI(
        title="AquaWatch NRW API",
        description="Remote API for Non-Revenue Water Detection System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS for remote access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # -------------------------------------------------------------------------
    # ERROR HANDLING
    # -------------------------------------------------------------------------
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Standardized HTTP error responses."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Catch-all error handler to prevent raw tracebacks in responses."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    # -------------------------------------------------------------------------
    # AUTHENTICATION ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.post("/v1/auth/login", response_model=LoginResponse, tags=["Authentication"])
    async def login(request: LoginRequest):
        """
        Authenticate user and get access tokens.
        
        Use the access_token in the Authorization header:
        `Authorization: Bearer <access_token>`
        """
        result = auth_service.authenticate(request.email, request.password)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return result
    
    @app.post("/v1/auth/refresh", tags=["Authentication"])
    async def refresh_token(request: RefreshRequest):
        """Get new access token using refresh token."""
        new_token = auth_service.refresh_access_token(request.refresh_token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return {"access_token": new_token, "token_type": "bearer"}
    
    @app.post("/v1/auth/logout", tags=["Authentication"])
    async def logout(request: RefreshRequest):
        """Logout and revoke refresh token."""
        auth_service.revoke_refresh_token(request.refresh_token)
        return {"message": "Logged out successfully"}
    
    @app.get("/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
    async def get_current_user_info(user: User = Depends(get_current_user)):
        """Get current authenticated user info."""
        return UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            full_name=user.full_name,
            utility_id=user.utility_id,
            is_active=user.is_active
        )
    
    # -------------------------------------------------------------------------
    # DASHBOARD ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/dashboard/summary", response_model=DashboardSummaryResponse, tags=["Dashboard"])
    async def get_dashboard_summary(user: User = Depends(get_current_user)):
        """
        Get dashboard summary for remote monitoring.
        
        Returns key metrics at a glance.
        """
        # In production, fetch from database
        return DashboardSummaryResponse(
            total_dmas=12,
            total_devices=48,
            devices_online=45,
            active_alerts=7,
            critical_alerts=2,
            avg_nrw_pct=32.5,
            last_24h_alerts=15
        )
    
    @app.get("/v1/dashboard/nrw-stats", response_model=NRWStatsResponse, tags=["Dashboard"])
    async def get_nrw_statistics(
        period: str = Query("month", pattern="^(day|week|month|year)$"),
        utility_id: Optional[str] = None,
        user: User = Depends(get_current_user)
    ):
        """Get NRW statistics for IWA Water Balance reporting."""
        # In production, calculate from database
        return NRWStatsResponse(
            utility_id=utility_id or user.utility_id or "LWSC",
            period=period,
            total_input=1250000.0,  # m³
            authorized_consumption=850000.0,
            nrw_volume=400000.0,
            nrw_percentage=32.0,
            real_losses=280000.0,
            apparent_losses=120000.0,
            cost_of_nrw=450000.0  # ZMW or ZAR
        )
    
    # -------------------------------------------------------------------------
    # DMA ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/dmas", response_model=DMAListResponse, tags=["DMAs"])
    async def list_dmas(
        utility_id: Optional[str] = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user)
    ):
        """List all District Metered Areas accessible to user."""
        # In production, fetch from database with user's access filter
        sample_dmas = [
            DMAResponse(
                id="DMA_LUSAKA_001",
                name="Kabulonga East",
                utility_id="LWSC",
                location={"lat": -15.4167, "lng": 28.2833},
                device_count=8,
                current_nrw_pct=28.5,
                last_updated=datetime.now(timezone.utc)
            ),
            DMAResponse(
                id="DMA_LUSAKA_002",
                name="Chelstone Central",
                utility_id="LWSC",
                location={"lat": -15.3833, "lng": 28.3333},
                device_count=6,
                current_nrw_pct=35.2,
                last_updated=datetime.now(timezone.utc)
            )
        ]
        
        return DMAListResponse(dmas=sample_dmas, total=len(sample_dmas))
    
    @app.get("/v1/dmas/{dma_id}", response_model=DMAResponse, tags=["DMAs"])
    async def get_dma(
        dma_id: str = Path(...),
        user: User = Depends(get_current_user)
    ):
        """Get detailed DMA information."""
        if not user.can_access_dma(dma_id):
            raise HTTPException(status_code=403, detail="Access denied to this DMA")
        
        return DMAResponse(
            id=dma_id,
            name="Kabulonga East",
            utility_id="LWSC",
            location={"lat": -15.4167, "lng": 28.2833},
            device_count=8,
            current_nrw_pct=28.5,
            last_updated=datetime.now(timezone.utc)
        )
    
    # -------------------------------------------------------------------------
    # ALERTS ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/alerts", response_model=AlertListResponse, tags=["Alerts"])
    async def list_alerts(
        dma_id: Optional[str] = None,
        severity: Optional[str] = Query(None, pattern="^(critical|high|medium|low)$"),
        acknowledged: Optional[bool] = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user)
    ):
        """
        List alerts with filtering.
        
        Perfect for mobile app notifications screen.
        """
        # In production, fetch from database
        sample_alerts = [
            AlertResponse(
                id="alert_001",
                type="Pressure Drop",
                severity="critical",
                dma_id="DMA_LUSAKA_001",
                dma_name="Kabulonga East",
                device_id="ESP32_001",
                value=1.2,
                timestamp=datetime.now(timezone.utc),
                acknowledged=False,
                acknowledged_by=None,
                notes=None
            ),
            AlertResponse(
                id="alert_002",
                type="High Night Flow",
                severity="high",
                dma_id="DMA_LUSAKA_002",
                dma_name="Chelstone Central",
                device_id="ESP32_005",
                value=45.5,
                timestamp=datetime.now(timezone.utc),
                acknowledged=True,
                acknowledged_by="operator@lwsc.co.zm",
                notes="Crew dispatched"
            )
        ]
        
        return AlertListResponse(
            alerts=sample_alerts,
            total=len(sample_alerts),
            unacknowledged=1
        )
    
    @app.post("/v1/alerts/{alert_id}/acknowledge", tags=["Alerts"])
    async def acknowledge_alert(
        alert_id: str = Path(...),
        request: AcknowledgeAlertRequest = None,
        user: User = Depends(require_permission(Permission.ACKNOWLEDGE_ALERTS))
    ):
        """
        Acknowledge an alert from anywhere in the world.
        
        Requires ACKNOWLEDGE_ALERTS permission.
        """
        # In production, update database
        return {
            "message": "Alert acknowledged",
            "alert_id": alert_id,
            "acknowledged_by": user.email,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "notes": request.notes if request else None
        }
    
    # -------------------------------------------------------------------------
    # DEVICES ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/devices", response_model=DeviceListResponse, tags=["Devices"])
    async def list_devices(
        dma_id: Optional[str] = None,
        status: Optional[str] = Query(None, pattern="^(online|offline|error)$"),
        user: User = Depends(get_current_user)
    ):
        """List all ESP32 devices."""
        sample_devices = [
            DeviceResponse(
                id="ESP32_001",
                dma_id="DMA_LUSAKA_001",
                sensor_type="pressure",
                status="online",
                battery_pct=85.0,
                signal_strength=-65,
                last_seen=datetime.now(timezone.utc),
                firmware_version="1.0.0"
            ),
            DeviceResponse(
                id="ESP32_002",
                dma_id="DMA_LUSAKA_001",
                sensor_type="flow",
                status="online",
                battery_pct=72.0,
                signal_strength=-72,
                last_seen=datetime.now(timezone.utc),
                firmware_version="1.0.0"
            )
        ]
        
        return DeviceListResponse(
            devices=sample_devices,
            total=len(sample_devices),
            online=2,
            offline=0
        )
    
    @app.post("/v1/devices/{device_id}/command", tags=["Devices"])
    async def send_device_command(
        device_id: str = Path(...),
        command: dict = None,
        user: User = Depends(require_permission(Permission.MANAGE_DEVICES))
    ):
        """
        Send command to ESP32 device remotely.
        
        Commands: reboot, config, calibrate, ota
        """
        # In production, publish to MQTT
        return {
            "message": "Command sent",
            "device_id": device_id,
            "command": command,
            "sent_by": user.email
        }
    
    # -------------------------------------------------------------------------
    # READINGS ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/readings", response_model=ReadingsListResponse, tags=["Readings"])
    async def get_readings(
        dma_id: Optional[str] = None,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = Query(None, pattern="^(pressure|flow|level)$"),
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = Query(100, ge=1, le=1000),
        user: User = Depends(get_current_user)
    ):
        """
        Get sensor readings with filtering.
        
        Use for charts and historical analysis.
        """
        # In production, fetch from TimescaleDB
        sample_readings = [
            SensorReadingResponse(
                device_id="ESP32_001",
                sensor_type="pressure",
                value=4.5,
                unit="bar",
                quality="good",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        return ReadingsListResponse(
            readings=sample_readings,
            total=len(sample_readings)
        )
    
    # -------------------------------------------------------------------------
    # NOTIFICATIONS ENDPOINTS
    # -------------------------------------------------------------------------
    
    @app.get("/v1/notifications/preferences", tags=["Notifications"])
    async def get_notification_preferences(user: User = Depends(get_current_user)):
        """Get user's notification preferences."""
        pref = notification_service.get_user_preference(user.id)
        
        if not pref:
            return {"message": "No preferences set"}
        
        return {
            "channels": [c.value for c in pref.channels],
            "phone_number": pref.phone_number,
            "whatsapp_number": pref.whatsapp_number,
            "email": pref.email,
            "telegram_chat_id": pref.telegram_chat_id,
            "min_severity": pref.min_severity.value,
            "quiet_hours_start": pref.quiet_hours_start,
            "quiet_hours_end": pref.quiet_hours_end,
            "dma_ids": pref.dma_ids
        }
    
    @app.put("/v1/notifications/preferences", tags=["Notifications"])
    async def update_notification_preferences(
        request: NotificationPreferenceRequest,
        user: User = Depends(get_current_user)
    ):
        """
        Update notification preferences.
        
        Configure how you receive alerts when away from Zambia.
        """
        pref = NotificationPreference(
            user_id=user.id,
            channels=[NotificationChannel(c) for c in request.channels],
            phone_number=request.phone_number,
            whatsapp_number=request.whatsapp_number,
            email=request.email,
            telegram_chat_id=request.telegram_chat_id,
            min_severity=AlertSeverity(request.min_severity),
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
            dma_ids=request.dma_ids
        )
        
        notification_service.set_user_preference(pref)
        
        return {"message": "Preferences updated successfully"}
    
    @app.post("/v1/notifications/test", tags=["Notifications"])
    async def test_notification(
        channel: str = Query(..., pattern="^(sms|whatsapp|email|telegram)$"),
        user: User = Depends(get_current_user)
    ):
        """Send test notification to verify setup."""
        pref = notification_service.get_user_preference(user.id)
        
        if not pref:
            raise HTTPException(status_code=400, detail="Set preferences first")
        
        # Send test based on channel
        if channel == "sms" and pref.phone_number:
            success = notification_service.sms.send(
                pref.phone_number, 
                "🧪 AquaWatch Test: Your SMS notifications are working!"
            )
        elif channel == "whatsapp" and pref.whatsapp_number:
            success = notification_service.whatsapp.send(
                pref.whatsapp_number,
                "🧪 *AquaWatch Test*\n\nYour WhatsApp notifications are working!"
            )
        elif channel == "email" and pref.email:
            success = notification_service.email.send(
                pref.email,
                "AquaWatch Test Notification",
                "<h2>🧪 Test Notification</h2><p>Your email notifications are working!</p>",
                "Test Notification: Your email notifications are working!"
            )
        elif channel == "telegram" and pref.telegram_chat_id:
            success = notification_service.telegram.send(
                pref.telegram_chat_id,
                "🧪 <b>AquaWatch Test</b>\n\nYour Telegram notifications are working!"
            )
        else:
            raise HTTPException(status_code=400, detail=f"No {channel} configured")
        
        return {"success": success, "channel": channel}
    
    # -------------------------------------------------------------------------
    # API KEY ENDPOINTS (for ESP32 devices)
    # -------------------------------------------------------------------------
    
    @app.post("/v1/api-keys", tags=["API Keys"])
    async def create_api_key(
        device_id: str,
        dma_id: str,
        user: User = Depends(require_permission(Permission.MANAGE_DEVICES))
    ):
        """
        Create API key for new ESP32 device.
        
        The secret is only shown once - save it securely!
        """
        key_id, full_key = auth_service.create_api_key(
            device_id=device_id,
            utility_id=user.utility_id or "default",
            dma_id=dma_id
        )
        
        return {
            "key_id": key_id,
            "api_key": full_key,  # Only shown once!
            "device_id": device_id,
            "warning": "Save this API key securely - it won't be shown again!"
        }
    
    # -------------------------------------------------------------------------
    # HEALTH CHECK
    # -------------------------------------------------------------------------
    
    @app.get("/v1/health", tags=["System"])
    async def health_check():
        """Basic health check for load balancers and monitoring."""
        try:
            from src.core.health_monitor import get_dashboard_health
            health = get_dashboard_health()
            return {
                "status": health.get("status", "unknown"),
                "message": health.get("message", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
                "active_alerts": health.get("active_alerts", 0),
            }
        except Exception:
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0"
            }
    
    @app.get("/v1/health/components", tags=["System"])
    async def health_components(current_user: dict = Depends(get_current_user)):
        """
        Detailed component health status.
        
        Returns health status for each system component (database, MQTT, AI engine, etc.).
        Requires authentication.
        """
        try:
            from src.core.health_monitor import get_health_monitor
            monitor = get_health_monitor()
            report = monitor.get_full_report()
            
            components = {}
            for name, comp in report.components.items():
                components[name] = {
                    "status": comp.status.value,
                    "message": comp.message,
                    "last_check": comp.last_check.isoformat() if comp.last_check else None,
                    "consecutive_failures": comp.consecutive_failures,
                }
            
            return {
                "overall_status": report.overall_status.value,
                "components": components,
                "metrics": report.metrics,
                "active_alerts": report.alerts,
                "timestamp": report.timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Health components check failed: {e}")
            return {
                "overall_status": "unknown",
                "components": {},
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    return app


# Create app instance
if FASTAPI_AVAILABLE:
    api_app = create_api()
