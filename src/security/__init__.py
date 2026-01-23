"""
AquaWatch NRW Security Module
=============================

Multi-tenant authentication and authorization for AquaWatch v3.0.

Exports:
- TenantRole: RBAC role enum
- Permission: Fine-grained permission enum
- CurrentUser: Authenticated user context
- TenantGuard: FastAPI dependency for tenant isolation
- RequireRole: FastAPI dependency for role-based access
- RequirePermission: FastAPI dependency for permission-based access
- token_manager: JWT token creation/validation
- audit_logger: Multi-tenant audit logging
- auth_service: Authentication service
"""

# Multi-tenant auth (v3.0)
from .multi_tenant_auth import (
    # Config
    AuthConfig,
    
    # Enums
    TenantRole,
    Permission,
    AuditAction,
    
    # Models
    TokenPayload,
    TokenResponse,
    CurrentUser,
    AuditLogEntry,
    
    # Token management
    MultiTenantTokenManager,
    token_manager,
    
    # FastAPI dependencies
    TenantGuard,
    RequireRole,
    RequirePermission,
    get_current_user,
    get_current_user_optional,
    
    # Convenience helpers
    require_super_admin,
    require_tenant_admin,
    require_engineer,
    require_operator,
    
    # Audit logging
    MultiTenantAuditLogger,
    audit_logger,
    
    # Role permissions
    ROLE_PERMISSIONS,
)

# Auth service
from .auth_service import (
    PasswordUtils,
    TenantUser,
    MultiTenantAuthService,
    auth_service,
)

# API routes
from .api_routes import (
    auth_router,
    tenant_router,
    super_admin_router,
)

# Legacy auth (for backward compatibility)
from .auth import (
    UserRole,
    Permission as LegacyPermission,
    AuditAction as LegacyAuditAction,
    PasswordManager,
    TokenManager,
    DataEncryption,
    AuditLogger,
    RateLimiter,
    AuthenticationService,
)

__all__ = [
    # v3.0 Multi-tenant auth
    "AuthConfig",
    "TenantRole",
    "Permission",
    "AuditAction",
    "TokenPayload",
    "TokenResponse",
    "CurrentUser",
    "AuditLogEntry",
    "MultiTenantTokenManager",
    "token_manager",
    "TenantGuard",
    "RequireRole",
    "RequirePermission",
    "get_current_user",
    "get_current_user_optional",
    "require_super_admin",
    "require_tenant_admin",
    "require_engineer",
    "require_operator",
    "MultiTenantAuditLogger",
    "audit_logger",
    "ROLE_PERMISSIONS",
    "PasswordUtils",
    "TenantUser",
    "MultiTenantAuthService",
    "auth_service",
    "auth_router",
    "tenant_router",
    "super_admin_router",
    
    # Legacy
    "UserRole",
    "LegacyPermission",
    "LegacyAuditAction",
    "PasswordManager",
    "TokenManager",
    "DataEncryption",
    "AuditLogger",
    "RateLimiter",
    "AuthenticationService",
]
