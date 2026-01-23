"""
AquaWatch NRW v3.0 - Multi-Tenant API Routes
=============================================

FastAPI routes demonstrating multi-tenant authentication and authorization.

Example endpoints:
- POST /auth/login - Authenticate user
- POST /auth/refresh - Refresh access token
- GET /tenants/{tenant_id}/dmas - List DMAs (tenant-isolated)
- POST /tenants/{tenant_id}/work-orders - Create work order (OPERATOR+)
- POST /tenants/{tenant_id}/leaks/{leak_id}/acknowledge - Acknowledge leak
- POST /tenants/{tenant_id}/leaks/{leak_id}/resolve - Resolve leak

All tenant-scoped endpoints enforce:
1. Valid JWT token
2. Token tenant_id matches path tenant_id (or SUPER_ADMIN)
3. User has required role/permission
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .multi_tenant_auth import (
    TenantRole,
    Permission,
    CurrentUser,
    TenantGuard,
    RequireRole,
    RequirePermission,
    get_current_user,
    audit_logger,
    AuditAction,
    AuthConfig
)
from .auth_service import auth_service


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class LoginRequest(BaseModel):
    """Login request body."""
    email: str = Field(..., example="operator@lwsc.co.zm")
    password: str = Field(..., example="operator123")
    tenant_id: Optional[str] = Field(None, example="default-tenant")


class LoginResponse(BaseModel):
    """Login response."""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[Dict] = None
    error: Optional[str] = None


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response."""
    success: bool
    access_token: Optional[str] = None
    error: Optional[str] = None


class WorkOrderCreate(BaseModel):
    """Work order creation request."""
    title: str
    description: str
    priority: int = Field(3, ge=1, le=5)
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    location: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    """Work order update request."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    findings: Optional[str] = None


class LeakAcknowledgeRequest(BaseModel):
    """Leak acknowledgment request."""
    notes: Optional[str] = None


class LeakResolveRequest(BaseModel):
    """Leak resolution request."""
    resolution_type: str = Field(..., example="repaired")
    notes: Optional[str] = None
    repair_cost: Optional[float] = None
    water_saved_m3: Optional[float] = None


# =============================================================================
# API ROUTERS
# =============================================================================

# Auth router (no tenant context required)
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Tenant-scoped router (requires tenant context)
tenant_router = APIRouter(prefix="/tenants/{tenant_id}", tags=["Tenant Resources"])


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@auth_router.post("/login", response_model=LoginResponse)
async def login(request: Request, body: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    
    Returns access_token and refresh_token on success.
    """
    success, token_response, error = auth_service.authenticate(
        email=body.email,
        password=body.password,
        tenant_id=body.tenant_id,
        request=request
    )
    
    if not success:
        return LoginResponse(success=False, error=error)
    
    return LoginResponse(
        success=True,
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
        user=token_response.user
    )


@auth_router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: Request, body: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    success, new_token, error = auth_service.refresh_access_token(
        refresh_token=body.refresh_token,
        request=request
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return RefreshResponse(success=True, access_token=new_token)


@auth_router.get("/me")
async def get_current_user_info(user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "permissions": list(user.permissions),
        "email": user.email,
        "name": user.name,
        "is_super_admin": user.is_super_admin()
    }


@auth_router.post("/logout")
async def logout(request: Request, user: CurrentUser = Depends(get_current_user)):
    """
    Logout user (invalidate tokens on client side).
    
    Note: For stateless JWT, actual invalidation requires token blacklist.
    """
    audit_logger.log(
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        action=AuditAction.LOGOUT,
        resource_type="auth",
        resource_id=user.email,
        request=request,
        user_email=user.email
    )
    
    return {"success": True, "message": "Logged out successfully"}


# =============================================================================
# DMA ENDPOINTS (Tenant-Scoped)
# =============================================================================

@tenant_router.get("/dmas")
async def list_dmas(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard())
):
    """
    List all DMAs for the tenant.
    
    Requires: Any authenticated user in the tenant
    """
    # In real implementation, query database filtered by tenant_id
    return {
        "tenant_id": tenant_id,
        "user_id": user.user_id,
        "user_role": user.role.value,
        "dmas": [
            {"id": "dma-001", "name": "Kabulonga North", "tenant_id": tenant_id},
            {"id": "dma-002", "name": "Woodlands Central", "tenant_id": tenant_id},
            {"id": "dma-003", "name": "Roma Industrial", "tenant_id": tenant_id},
        ]
    }


@tenant_router.post("/dmas")
async def create_dma(
    tenant_id: str,
    user: CurrentUser = Depends(RequireRole([TenantRole.ENGINEER, TenantRole.TENANT_ADMIN]))
):
    """
    Create new DMA.
    
    Requires: ENGINEER or TENANT_ADMIN role
    """
    return {
        "success": True,
        "message": f"DMA created by {user.role.value}",
        "tenant_id": tenant_id
    }


# =============================================================================
# WORK ORDER ENDPOINTS (Tenant-Scoped)
# =============================================================================

@tenant_router.get("/work-orders")
async def list_work_orders(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard())
):
    """
    List work orders for the tenant.
    
    Requires: Any authenticated user
    """
    return {
        "tenant_id": tenant_id,
        "work_orders": [
            {"id": "wo-001", "title": "Inspect pressure drop", "status": "open"},
            {"id": "wo-002", "title": "Repair leak at Junction 5", "status": "in_progress"},
        ]
    }


@tenant_router.post("/work-orders")
async def create_work_order(
    request: Request,
    tenant_id: str,
    body: WorkOrderCreate,
    user: CurrentUser = Depends(RequirePermission(Permission.WORKORDER_CREATE))
):
    """
    Create new work order.
    
    Requires: WORKORDER_CREATE permission (OPERATOR, ENGINEER, TENANT_ADMIN)
    """
    work_order_id = f"wo-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Audit log
    audit_logger.log_workorder_create(
        tenant_id=tenant_id,
        user_id=user.user_id,
        workorder_id=work_order_id,
        request=request,
        user_email=user.email,
        details={
            "title": body.title,
            "priority": body.priority,
            "assigned_to": body.assigned_to
        }
    )
    
    return {
        "success": True,
        "work_order_id": work_order_id,
        "created_by": user.user_id,
        "tenant_id": tenant_id
    }


@tenant_router.put("/work-orders/{work_order_id}")
async def update_work_order(
    request: Request,
    tenant_id: str,
    work_order_id: str,
    body: WorkOrderUpdate,
    user: CurrentUser = Depends(RequirePermission(Permission.WORKORDER_UPDATE))
):
    """
    Update work order.
    
    Requires: WORKORDER_UPDATE permission
    """
    # Audit log
    audit_logger.log_workorder_update(
        tenant_id=tenant_id,
        user_id=user.user_id,
        workorder_id=work_order_id,
        request=request,
        user_email=user.email,
        changes=body.dict(exclude_none=True)
    )
    
    return {
        "success": True,
        "work_order_id": work_order_id,
        "updated_by": user.user_id
    }


@tenant_router.post("/work-orders/{work_order_id}/complete")
async def complete_work_order(
    request: Request,
    tenant_id: str,
    work_order_id: str,
    user: CurrentUser = Depends(RequirePermission(Permission.WORKORDER_COMPLETE))
):
    """
    Mark work order as complete.
    
    Requires: WORKORDER_COMPLETE permission (TECHNICIAN+)
    """
    audit_logger.log(
        tenant_id=tenant_id,
        user_id=user.user_id,
        action=AuditAction.WORKORDER_COMPLETE,
        resource_type="workorder",
        resource_id=work_order_id,
        request=request,
        user_email=user.email
    )
    
    return {
        "success": True,
        "work_order_id": work_order_id,
        "status": "completed",
        "completed_by": user.user_id
    }


# =============================================================================
# LEAK MANAGEMENT ENDPOINTS (Tenant-Scoped)
# =============================================================================

@tenant_router.get("/leaks")
async def list_leaks(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard())
):
    """
    List detected leaks for the tenant.
    
    Requires: Any authenticated user
    """
    return {
        "tenant_id": tenant_id,
        "leaks": [
            {
                "id": "leak-001",
                "status": "detected",
                "probability": 0.87,
                "dma": "Kabulonga North",
                "detected_at": "2026-01-22T10:30:00Z"
            },
            {
                "id": "leak-002",
                "status": "acknowledged",
                "probability": 0.92,
                "dma": "Woodlands Central",
                "detected_at": "2026-01-22T08:15:00Z"
            },
        ]
    }


@tenant_router.post("/leaks/{leak_id}/acknowledge")
async def acknowledge_leak(
    request: Request,
    tenant_id: str,
    leak_id: str,
    body: LeakAcknowledgeRequest,
    user: CurrentUser = Depends(RequirePermission(Permission.LEAK_ACKNOWLEDGE))
):
    """
    Acknowledge a detected leak.
    
    Requires: LEAK_ACKNOWLEDGE permission (OPERATOR, ENGINEER, TENANT_ADMIN)
    """
    # Audit log
    audit_logger.log_leak_acknowledge(
        tenant_id=tenant_id,
        user_id=user.user_id,
        leak_id=leak_id,
        request=request,
        user_email=user.email,
        details={"notes": body.notes}
    )
    
    return {
        "success": True,
        "leak_id": leak_id,
        "status": "acknowledged",
        "acknowledged_by": user.user_id,
        "acknowledged_at": datetime.utcnow().isoformat()
    }


@tenant_router.post("/leaks/{leak_id}/resolve")
async def resolve_leak(
    request: Request,
    tenant_id: str,
    leak_id: str,
    body: LeakResolveRequest,
    user: CurrentUser = Depends(RequirePermission(Permission.LEAK_RESOLVE))
):
    """
    Mark a leak as resolved.
    
    Requires: LEAK_RESOLVE permission (ENGINEER, TENANT_ADMIN)
    """
    # Audit log
    audit_logger.log_leak_resolve(
        tenant_id=tenant_id,
        user_id=user.user_id,
        leak_id=leak_id,
        request=request,
        user_email=user.email,
        details={
            "resolution_type": body.resolution_type,
            "notes": body.notes,
            "repair_cost": body.repair_cost,
            "water_saved_m3": body.water_saved_m3
        }
    )
    
    return {
        "success": True,
        "leak_id": leak_id,
        "status": "resolved",
        "resolved_by": user.user_id,
        "resolved_at": datetime.utcnow().isoformat(),
        "resolution_type": body.resolution_type
    }


# =============================================================================
# ALERT ENDPOINTS (Tenant-Scoped)
# =============================================================================

@tenant_router.get("/alerts")
async def list_alerts(
    tenant_id: str,
    user: CurrentUser = Depends(TenantGuard())
):
    """
    List alerts for the tenant.
    """
    return {
        "tenant_id": tenant_id,
        "alerts": [
            {"id": "alert-001", "severity": "high", "type": "pressure_anomaly"},
            {"id": "alert-002", "severity": "medium", "type": "flow_anomaly"},
        ]
    }


@tenant_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    request: Request,
    tenant_id: str,
    alert_id: str,
    user: CurrentUser = Depends(RequirePermission(Permission.ALERT_ACKNOWLEDGE))
):
    """
    Acknowledge an alert.
    
    Requires: ALERT_ACKNOWLEDGE permission
    """
    audit_logger.log(
        tenant_id=tenant_id,
        user_id=user.user_id,
        action=AuditAction.ALERT_ACKNOWLEDGE,
        resource_type="alert",
        resource_id=alert_id,
        request=request,
        user_email=user.email
    )
    
    return {
        "success": True,
        "alert_id": alert_id,
        "status": "acknowledged"
    }


# =============================================================================
# ADMIN ENDPOINTS (TENANT_ADMIN+)
# =============================================================================

@tenant_router.get("/users")
async def list_tenant_users(
    tenant_id: str,
    user: CurrentUser = Depends(RequireRole([TenantRole.TENANT_ADMIN]))
):
    """
    List all users in the tenant.
    
    Requires: TENANT_ADMIN role
    """
    users = auth_service.list_users_for_tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "users": [u.to_dict() for u in users]
    }


@tenant_router.get("/audit-logs")
async def get_audit_logs(
    tenant_id: str,
    limit: int = 100,
    user: CurrentUser = Depends(RequirePermission(Permission.AUDIT_READ))
):
    """
    Get audit logs for the tenant.
    
    Requires: AUDIT_READ permission (TENANT_ADMIN, EXECUTIVE)
    """
    logs = audit_logger.get_logs_for_tenant(tenant_id, limit=limit)
    
    return {
        "tenant_id": tenant_id,
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "action": log.action.value,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "success": log.success
            }
            for log in logs
        ]
    }


# =============================================================================
# SUPER ADMIN ENDPOINTS
# =============================================================================

super_admin_router = APIRouter(prefix="/admin", tags=["Super Admin"])


@super_admin_router.get("/tenants")
async def list_all_tenants(
    user: CurrentUser = Depends(RequireRole([TenantRole.SUPER_ADMIN], allow_higher=False))
):
    """
    List all tenants in the system.
    
    Requires: SUPER_ADMIN role only
    """
    return {
        "tenants": [
            {"id": "default-tenant", "name": "LWSC Zambia", "plan": "professional"},
            {"id": "tenant-002", "name": "JSWC Kenya", "plan": "enterprise"},
        ]
    }


@super_admin_router.get("/tenants/{tenant_id}/users")
async def list_any_tenant_users(
    tenant_id: str,
    user: CurrentUser = Depends(RequireRole([TenantRole.SUPER_ADMIN], allow_higher=False))
):
    """
    List users in any tenant (SUPER_ADMIN cross-tenant access).
    
    Requires: SUPER_ADMIN role only
    """
    users = auth_service.list_users_for_tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "users": [u.to_dict() for u in users],
        "accessed_by": user.email
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "auth_router",
    "tenant_router", 
    "super_admin_router",
]
