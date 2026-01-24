"""
AquaWatch NRW v3.0 - Multi-Tenant Authentication & Authorization
================================================================

This module provides:
1. Tenant-aware JWT tokens with user_id, tenant_id, role
2. RBAC roles: SUPER_ADMIN, TENANT_ADMIN, OPERATOR, ENGINEER, TECHNICIAN, EXECUTIVE, VIEWER
3. TenantGuard - FastAPI dependency for tenant isolation
4. RequireRole - FastAPI dependency for role-based access control
5. Comprehensive audit logging for security events

Security Principles:
- Zero-trust: Every request is authenticated and authorized
- Tenant isolation: Users can only access their tenant's data
- Least privilege: Roles have minimal necessary permissions
- Audit trail: All sensitive actions are logged
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import jwt
from pydantic import BaseModel, Field

# FastAPI imports
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class AuthConfig:
    """Authentication configuration from environment."""
    
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', 'aquawatch-v3-secret-change-in-production')
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    # Default tenant for backward compatibility
    DEFAULT_TENANT_ID: str = 'default-tenant'


# =============================================================================
# RBAC ROLES
# =============================================================================

class TenantRole(str, Enum):
    """
    RBAC roles for multi-tenant system.
    
    Hierarchy (highest to lowest privilege):
    1. SUPER_ADMIN - Platform-wide access, can access all tenants
    2. TENANT_ADMIN - Full access within their tenant
    3. EXECUTIVE - View all data, approve budgets
    4. ENGINEER - Configure systems, deploy models
    5. OPERATOR - Monitor and respond to alerts
    6. TECHNICIAN - Field work, complete work orders
    7. VIEWER - Read-only dashboard access
    """
    SUPER_ADMIN = "super_admin"      # Platform admin - ALL tenants
    TENANT_ADMIN = "tenant_admin"    # Tenant administrator
    EXECUTIVE = "executive"          # C-level, view all, approve
    ENGINEER = "engineer"            # System configuration, AI
    OPERATOR = "operator"            # Control room operations
    TECHNICIAN = "technician"        # Field technician
    VIEWER = "viewer"                # Read-only access


class Permission(str, Enum):
    """Granular permissions for fine-grained access control."""
    
    # Tenant management (SUPER_ADMIN only)
    TENANT_CREATE = "tenant:create"
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    TENANT_SWITCH = "tenant:switch"  # Access other tenants
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"
    
    # Alert management
    ALERT_READ = "alert:read"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_RESOLVE = "alert:resolve"
    ALERT_DISMISS = "alert:dismiss"
    
    # Leak management
    LEAK_READ = "leak:read"
    LEAK_ACKNOWLEDGE = "leak:acknowledge"
    LEAK_RESOLVE = "leak:resolve"
    LEAK_CONFIRM = "leak:confirm"
    
    # Work orders
    WORKORDER_CREATE = "workorder:create"
    WORKORDER_READ = "workorder:read"
    WORKORDER_UPDATE = "workorder:update"
    WORKORDER_ASSIGN = "workorder:assign"
    WORKORDER_COMPLETE = "workorder:complete"
    WORKORDER_DELETE = "workorder:delete"
    
    # Data access
    DATA_READ = "data:read"
    DATA_EXPORT = "data:export"
    DATA_DELETE = "data:delete"
    
    # Configuration
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    SENSOR_MANAGE = "sensor:manage"
    DMA_MANAGE = "dma:manage"
    
    # AI/ML
    MODEL_READ = "model:read"
    MODEL_TRAIN = "model:train"
    MODEL_DEPLOY = "model:deploy"
    
    # Billing
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"
    
    # Audit
    AUDIT_READ = "audit:read"


# Role-to-Permission mapping
ROLE_PERMISSIONS: Dict[TenantRole, Set[Permission]] = {
    TenantRole.SUPER_ADMIN: set(Permission),  # All permissions
    
    TenantRole.TENANT_ADMIN: {
        # User management
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
        Permission.USER_DELETE, Permission.USER_INVITE,
        # Alerts
        Permission.ALERT_READ, Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_RESOLVE,
        Permission.ALERT_DISMISS,
        # Leaks
        Permission.LEAK_READ, Permission.LEAK_ACKNOWLEDGE, Permission.LEAK_RESOLVE,
        Permission.LEAK_CONFIRM,
        # Work orders
        Permission.WORKORDER_CREATE, Permission.WORKORDER_READ, Permission.WORKORDER_UPDATE,
        Permission.WORKORDER_ASSIGN, Permission.WORKORDER_COMPLETE, Permission.WORKORDER_DELETE,
        # Data
        Permission.DATA_READ, Permission.DATA_EXPORT, Permission.DATA_DELETE,
        # Config
        Permission.CONFIG_READ, Permission.CONFIG_UPDATE,
        Permission.SENSOR_MANAGE, Permission.DMA_MANAGE,
        # AI
        Permission.MODEL_READ, Permission.MODEL_TRAIN, Permission.MODEL_DEPLOY,
        # Billing
        Permission.BILLING_READ, Permission.BILLING_MANAGE,
        # Audit
        Permission.AUDIT_READ,
    },
    
    TenantRole.EXECUTIVE: {
        Permission.USER_READ,
        Permission.ALERT_READ,
        Permission.LEAK_READ,
        Permission.WORKORDER_READ,
        Permission.DATA_READ, Permission.DATA_EXPORT,
        Permission.CONFIG_READ,
        Permission.MODEL_READ,
        Permission.BILLING_READ, Permission.BILLING_MANAGE,
        Permission.AUDIT_READ,
    },
    
    TenantRole.ENGINEER: {
        Permission.USER_READ,
        Permission.ALERT_READ, Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_RESOLVE,
        Permission.LEAK_READ, Permission.LEAK_ACKNOWLEDGE, Permission.LEAK_CONFIRM,
        Permission.WORKORDER_CREATE, Permission.WORKORDER_READ, Permission.WORKORDER_UPDATE,
        Permission.DATA_READ, Permission.DATA_EXPORT,
        Permission.CONFIG_READ, Permission.CONFIG_UPDATE,
        Permission.SENSOR_MANAGE, Permission.DMA_MANAGE,
        Permission.MODEL_READ, Permission.MODEL_TRAIN, Permission.MODEL_DEPLOY,
    },
    
    TenantRole.OPERATOR: {
        Permission.ALERT_READ, Permission.ALERT_ACKNOWLEDGE,
        Permission.LEAK_READ, Permission.LEAK_ACKNOWLEDGE,
        Permission.WORKORDER_CREATE, Permission.WORKORDER_READ,
        Permission.WORKORDER_ASSIGN,
        Permission.DATA_READ,
        Permission.CONFIG_READ,
    },
    
    TenantRole.TECHNICIAN: {
        Permission.ALERT_READ,
        Permission.LEAK_READ, Permission.LEAK_CONFIRM,
        Permission.WORKORDER_READ, Permission.WORKORDER_UPDATE,
        Permission.WORKORDER_COMPLETE,
        Permission.DATA_READ,
    },
    
    TenantRole.VIEWER: {
        Permission.ALERT_READ,
        Permission.LEAK_READ,
        Permission.WORKORDER_READ,
        Permission.DATA_READ,
    },
}


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str = Field(..., description="User ID (subject)")
    user_id: str = Field(..., description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    role: TenantRole = Field(..., description="User role")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    email: Optional[str] = Field(None, description="User email")
    name: Optional[str] = Field(None, description="User display name")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field("access", description="Token type: access or refresh")
    jti: Optional[str] = Field(None, description="JWT ID for refresh tokens")


class TokenResponse(BaseModel):
    """Authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict


class CurrentUser(BaseModel):
    """Current authenticated user context."""
    user_id: str
    tenant_id: str
    role: TenantRole
    permissions: Set[str]
    email: Optional[str] = None
    name: Optional[str] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission.value in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p.value in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(p.value in self.permissions for p in permissions)
    
    def is_super_admin(self) -> bool:
        """Check if user is platform super admin."""
        return self.role == TenantRole.SUPER_ADMIN
    
    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if user can access specified tenant."""
        if self.is_super_admin():
            return True
        return self.tenant_id == tenant_id


# =============================================================================
# JWT TOKEN MANAGER
# =============================================================================

class MultiTenantTokenManager:
    """JWT token management with multi-tenant support."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None,
        refresh_token_expire_days: Optional[int] = None
    ):
        self.secret_key = secret_key or AuthConfig.JWT_SECRET_KEY
        self.algorithm = algorithm or AuthConfig.JWT_ALGORITHM
        self.access_token_expire_minutes = access_token_expire_minutes or AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = refresh_token_expire_days or AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: TenantRole,
        email: Optional[str] = None,
        name: Optional[str] = None,
        extra_claims: Optional[Dict] = None
    ) -> str:
        """
        Create JWT access token with tenant context.
        
        Args:
            user_id: Unique user identifier
            tenant_id: Tenant the user belongs to
            role: User's role within the tenant
            email: Optional user email
            name: Optional display name
            extra_claims: Additional claims to include
        
        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)
        
        # Get permissions for role
        permissions = ROLE_PERMISSIONS.get(role, set())
        
        payload = {
            "sub": user_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role.value,
            "permissions": [p.value for p in permissions],
            "email": email,
            "name": name,
            "exp": expires,
            "iat": now,
            "type": "access"
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str, tenant_id: str) -> str:
        """Create JWT refresh token."""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "exp": expires,
            "iat": now,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Convert role string to enum
            payload['role'] = TenantRole(payload['role'])
            payload['exp'] = datetime.fromtimestamp(payload['exp'])
            payload['iat'] = datetime.fromtimestamp(payload['iat'])
            
            return TokenPayload(**payload)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict]:
        """Decode token without verification (for debugging only)."""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None


# Global token manager instance
token_manager = MultiTenantTokenManager()


# =============================================================================
# FASTAPI SECURITY SCHEME
# =============================================================================

security = HTTPBearer(auto_error=False)


async def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: str = Header(None, alias="Authorization")
) -> Optional[str]:
    """Extract JWT token from Authorization header."""
    
    if credentials:
        return credentials.credentials
    
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    
    return None


# =============================================================================
# TENANT GUARD DEPENDENCY
# =============================================================================

class TenantGuard:
    """
    FastAPI dependency for enforcing tenant isolation.
    
    Usage:
        @app.get("/tenants/{tenant_id}/dmas")
        async def get_dmas(
            tenant_id: str,
            user: CurrentUser = Depends(TenantGuard())
        ):
            # user.tenant_id is guaranteed to match tenant_id
            # or user is SUPER_ADMIN
            pass
    """
    
    def __init__(self, allow_super_admin: bool = True):
        """
        Initialize TenantGuard.
        
        Args:
            allow_super_admin: If True, SUPER_ADMIN can access any tenant
        """
        self.allow_super_admin = allow_super_admin
    
    async def __call__(
        self,
        request: Request,
        token: str = Depends(get_token_from_header)
    ) -> CurrentUser:
        """Validate tenant access."""
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check token type
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Create current user
        user = CurrentUser(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            role=payload.role,
            permissions=set(payload.permissions),
            email=payload.email,
            name=payload.name
        )
        
        # Extract tenant_id from path if present
        path_tenant_id = request.path_params.get("tenant_id")
        
        if path_tenant_id:
            # Enforce tenant isolation
            if user.is_super_admin() and self.allow_super_admin:
                # SUPER_ADMIN can access any tenant
                pass
            elif user.tenant_id != path_tenant_id:
                logger.warning(
                    f"Tenant access denied: user {user.user_id} "
                    f"(tenant={user.tenant_id}) tried to access tenant={path_tenant_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Cannot access other tenant's resources"
                )
        
        # Store user in request state for later use
        request.state.current_user = user
        
        return user


# Simple dependency for basic auth (no tenant path validation)
async def get_current_user(
    token: str = Depends(get_token_from_header)
) -> CurrentUser:
    """
    Get current authenticated user without tenant path validation.
    
    Use this for endpoints that don't have tenant_id in the path.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = token_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    return CurrentUser(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        role=payload.role,
        permissions=set(payload.permissions),
        email=payload.email,
        name=payload.name
    )


# Optional auth - returns None if no token
async def get_current_user_optional(
    token: str = Depends(get_token_from_header)
) -> Optional[CurrentUser]:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None
    
    payload = token_manager.verify_token(token)
    if not payload or payload.type != "access":
        return None
    
    return CurrentUser(
        user_id=payload.user_id,
        tenant_id=payload.tenant_id,
        role=payload.role,
        permissions=set(payload.permissions),
        email=payload.email,
        name=payload.name
    )


# =============================================================================
# REQUIRE ROLE DEPENDENCY
# =============================================================================

class RequireRole:
    """
    FastAPI dependency for role-based access control.
    
    Usage:
        @app.post("/tenants/{tenant_id}/work-orders")
        async def create_work_order(
            tenant_id: str,
            user: CurrentUser = Depends(RequireRole([TenantRole.OPERATOR, TenantRole.ENGINEER]))
        ):
            pass
    """
    
    def __init__(
        self,
        allowed_roles: List[TenantRole],
        allow_higher: bool = True
    ):
        """
        Initialize RequireRole.
        
        Args:
            allowed_roles: List of roles that can access this endpoint
            allow_higher: If True, higher privilege roles are also allowed
        """
        self.allowed_roles = set(allowed_roles)
        self.allow_higher = allow_higher
        
        # Role hierarchy (higher index = higher privilege)
        self.role_hierarchy = [
            TenantRole.VIEWER,
            TenantRole.TECHNICIAN,
            TenantRole.OPERATOR,
            TenantRole.ENGINEER,
            TenantRole.EXECUTIVE,
            TenantRole.TENANT_ADMIN,
            TenantRole.SUPER_ADMIN,
        ]
    
    def _get_role_level(self, role: TenantRole) -> int:
        """Get numeric level for role in hierarchy."""
        try:
            return self.role_hierarchy.index(role)
        except ValueError:
            return -1
    
    async def __call__(
        self,
        request: Request,
        token: str = Depends(get_token_from_header)
    ) -> CurrentUser:
        """Validate role-based access."""
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        payload = token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user = CurrentUser(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            role=payload.role,
            permissions=set(payload.permissions),
            email=payload.email,
            name=payload.name
        )
        
        # Check tenant isolation first
        path_tenant_id = request.path_params.get("tenant_id")
        if path_tenant_id and not user.can_access_tenant(path_tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other tenant's resources"
            )
        
        # Check role
        if user.role in self.allowed_roles:
            request.state.current_user = user
            return user
        
        # Check if higher role is allowed
        if self.allow_higher:
            user_level = self._get_role_level(user.role)
            min_required_level = min(
                self._get_role_level(r) for r in self.allowed_roles
            )
            
            if user_level >= min_required_level:
                request.state.current_user = user
                return user
        
        logger.warning(
            f"Role access denied: user {user.user_id} with role {user.role.value} "
            f"tried to access endpoint requiring {[r.value for r in self.allowed_roles]}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires role {[r.value for r in self.allowed_roles]}"
        )


class RequirePermission:
    """
    FastAPI dependency for permission-based access control.
    
    Usage:
        @app.post("/tenants/{tenant_id}/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(
            user: CurrentUser = Depends(RequirePermission(Permission.ALERT_ACKNOWLEDGE))
        ):
            pass
    """
    
    def __init__(
        self,
        required_permissions: Union[Permission, List[Permission]],
        require_all: bool = False
    ):
        """
        Initialize RequirePermission.
        
        Args:
            required_permissions: Permission(s) required
            require_all: If True, user must have ALL permissions; otherwise ANY
        """
        if isinstance(required_permissions, Permission):
            self.required_permissions = [required_permissions]
        else:
            self.required_permissions = required_permissions
        self.require_all = require_all
    
    async def __call__(
        self,
        request: Request,
        token: str = Depends(get_token_from_header)
    ) -> CurrentUser:
        """Validate permission-based access."""
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        payload = token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = CurrentUser(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            role=payload.role,
            permissions=set(payload.permissions),
            email=payload.email,
            name=payload.name
        )
        
        # Check tenant isolation
        path_tenant_id = request.path_params.get("tenant_id")
        if path_tenant_id and not user.can_access_tenant(path_tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other tenant's resources"
            )
        
        # Check permissions
        if self.require_all:
            has_permission = user.has_all_permissions(self.required_permissions)
        else:
            has_permission = user.has_any_permission(self.required_permissions)
        
        if not has_permission:
            logger.warning(
                f"Permission denied: user {user.user_id} lacks "
                f"{[p.value for p in self.required_permissions]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires permission {[p.value for p in self.required_permissions]}"
            )
        
        request.state.current_user = user
        return user


# =============================================================================
# AUDIT LOGGING
# =============================================================================

class AuditAction(str, Enum):
    """Audit log action types."""
    # Authentication
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # Leak management
    LEAK_ACKNOWLEDGE = "leak_acknowledge"
    LEAK_RESOLVE = "leak_resolve"
    LEAK_DISMISS = "leak_dismiss"
    LEAK_CONFIRM = "leak_confirm"
    
    # Work orders
    WORKORDER_CREATE = "workorder_create"
    WORKORDER_UPDATE = "workorder_update"
    WORKORDER_ASSIGN = "workorder_assign"
    WORKORDER_COMPLETE = "workorder_complete"
    WORKORDER_DELETE = "workorder_delete"
    
    # Alerts
    ALERT_ACKNOWLEDGE = "alert_acknowledge"
    ALERT_RESOLVE = "alert_resolve"
    ALERT_DISMISS = "alert_dismiss"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_INVITE = "user_invite"
    
    # Configuration
    CONFIG_UPDATE = "config_update"
    SENSOR_CREATE = "sensor_create"
    SENSOR_UPDATE = "sensor_update"
    DMA_CREATE = "dma_create"
    DMA_UPDATE = "dma_update"
    
    # Data
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    
    # Model
    MODEL_DEPLOY = "model_deploy"
    MODEL_TRAIN = "model_train"


@dataclass
class AuditLogEntry:
    """Audit log entry structure."""
    id: str
    timestamp: datetime
    tenant_id: str
    user_id: str
    user_email: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    details: Dict = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class MultiTenantAuditLogger:
    """
    Audit logger with multi-tenant support.
    
    Logs security-sensitive actions for compliance and forensics.
    """
    
    def __init__(self, db_session=None):
        """Initialize with optional database session."""
        self.db_session = db_session
        self._logs: List[AuditLogEntry] = []  # In-memory fallback
        
        # Set up file logging
        self.file_logger = logging.getLogger("audit")
        self.file_logger.setLevel(logging.INFO)
        
        if not self.file_logger.handlers:
            handler = logging.FileHandler("audit.log")
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(message)s')
            )
            self.file_logger.addHandler(handler)
    
    def log(
        self,
        tenant_id: str,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        request: Optional[Request] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Create audit log entry.
        
        Args:
            tenant_id: Tenant context
            user_id: User performing action
            action: Type of action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            request: Optional FastAPI request for IP/UA
            user_email: Optional user email
            details: Additional details
            success: Whether action succeeded
            error_message: Error message if failed
        
        Returns:
            Created audit log entry
        """
        ip_address = "unknown"
        user_agent = "unknown"
        
        if request:
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")[:500]
        
        entry = AuditLogEntry(
            id=secrets.token_urlsafe(16),
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            success=success,
            error_message=error_message
        )
        
        # Store in memory
        self._logs.append(entry)
        
        # Write to file
        log_line = (
            f"[{entry.action.value}] "
            f"tenant={entry.tenant_id} "
            f"user={entry.user_id} "
            f"resource={entry.resource_type}/{entry.resource_id} "
            f"ip={entry.ip_address} "
            f"success={entry.success} "
            f"details={entry.details}"
        )
        self.file_logger.info(log_line)
        
        # TODO: Store in database when session available
        # if self.db_session:
        #     self._persist_to_db(entry)
        
        return entry
    
    def log_login(
        self,
        tenant_id: str,
        user_id: str,
        user_email: str,
        request: Request,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """Log login attempt."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            resource_type="auth",
            resource_id=user_email,
            request=request,
            user_email=user_email,
            details={"method": "password"},
            success=success,
            error_message=error_message
        )
    
    def log_leak_acknowledge(
        self,
        tenant_id: str,
        user_id: str,
        leak_id: str,
        request: Request,
        user_email: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> AuditLogEntry:
        """Log leak acknowledgment."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LEAK_ACKNOWLEDGE,
            resource_type="leak",
            resource_id=leak_id,
            request=request,
            user_email=user_email,
            details=details
        )
    
    def log_leak_resolve(
        self,
        tenant_id: str,
        user_id: str,
        leak_id: str,
        request: Request,
        user_email: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> AuditLogEntry:
        """Log leak resolution."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LEAK_RESOLVE,
            resource_type="leak",
            resource_id=leak_id,
            request=request,
            user_email=user_email,
            details=details
        )
    
    def log_workorder_create(
        self,
        tenant_id: str,
        user_id: str,
        workorder_id: str,
        request: Request,
        user_email: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> AuditLogEntry:
        """Log work order creation."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.WORKORDER_CREATE,
            resource_type="workorder",
            resource_id=workorder_id,
            request=request,
            user_email=user_email,
            details=details
        )
    
    def log_workorder_update(
        self,
        tenant_id: str,
        user_id: str,
        workorder_id: str,
        request: Request,
        user_email: Optional[str] = None,
        changes: Optional[Dict] = None
    ) -> AuditLogEntry:
        """Log work order update."""
        return self.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.WORKORDER_UPDATE,
            resource_type="workorder",
            resource_id=workorder_id,
            request=request,
            user_email=user_email,
            details={"changes": changes or {}}
        )
    
    def get_logs_for_tenant(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit logs for a tenant."""
        logs = [l for l in self._logs if l.tenant_id == tenant_id]
        
        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]
        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]
        if action:
            logs = [l for l in logs if l.action == action]
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]


# Global audit logger instance
audit_logger = MultiTenantAuditLogger()


# =============================================================================
# CONVENIENCE DECORATORS
# =============================================================================

def require_super_admin():
    """Decorator/dependency requiring SUPER_ADMIN role."""
    return RequireRole([TenantRole.SUPER_ADMIN], allow_higher=False)


def require_tenant_admin():
    """Decorator/dependency requiring TENANT_ADMIN or higher."""
    return RequireRole([TenantRole.TENANT_ADMIN])


def require_engineer():
    """Decorator/dependency requiring ENGINEER or higher."""
    return RequireRole([TenantRole.ENGINEER])


def require_operator():
    """Decorator/dependency requiring OPERATOR or higher."""
    return RequireRole([TenantRole.OPERATOR])


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "AuthConfig",
    
    # Enums
    "TenantRole",
    "Permission",
    "AuditAction",
    
    # Models
    "TokenPayload",
    "TokenResponse",
    "CurrentUser",
    "AuditLogEntry",
    
    # Token management
    "MultiTenantTokenManager",
    "token_manager",
    
    # Dependencies
    "TenantGuard",
    "RequireRole",
    "RequirePermission",
    "get_current_user",
    "get_current_user_optional",
    
    # Convenience
    "require_super_admin",
    "require_tenant_admin",
    "require_engineer",
    "require_operator",
    
    # Audit
    "MultiTenantAuditLogger",
    "audit_logger",
    
    # Role permissions
    "ROLE_PERMISSIONS",
]
