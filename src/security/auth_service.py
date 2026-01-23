"""
AquaWatch NRW v3.0 - Multi-Tenant Authentication Service
=========================================================

This module provides the authentication service layer:
1. User authentication (login/logout)
2. Token refresh
3. Password management
4. User registration and management

Works with both PostgreSQL and MongoDB backends.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .multi_tenant_auth import (
    TenantRole,
    Permission,
    MultiTenantTokenManager,
    MultiTenantAuditLogger,
    AuditAction,
    TokenResponse,
    CurrentUser,
    ROLE_PERMISSIONS,
    AuthConfig
)


# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

class PasswordUtils:
    """Password hashing and validation utilities."""
    
    MIN_LENGTH = 8
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        try:
            parts = stored_hash.split('$')
            if len(parts) != 2:
                # Legacy hash without salt
                return hashlib.sha256(password.encode()).hexdigest() == stored_hash
            
            salt, hash_value = parts
            check_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return check_hash == hash_value
        except Exception:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password meets minimum requirements."""
        errors = []
        
        if len(password) < PasswordUtils.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordUtils.MIN_LENGTH} characters")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        return len(errors) == 0, errors


# =============================================================================
# USER DATA CLASS
# =============================================================================

@dataclass
class TenantUser:
    """User within a tenant context."""
    user_id: str
    tenant_id: str
    email: str
    password_hash: str
    role: TenantRole
    name: str = ""
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# AUTHENTICATION SERVICE
# =============================================================================

class MultiTenantAuthService:
    """
    Authentication service with multi-tenant support.
    
    Handles:
    - User authentication
    - Token creation and refresh
    - Password management
    - Account lockout
    """
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 30
    
    def __init__(
        self,
        token_manager: MultiTenantTokenManager = None,
        audit_logger: MultiTenantAuditLogger = None,
        db_session = None
    ):
        """
        Initialize authentication service.
        
        Args:
            token_manager: JWT token manager
            audit_logger: Audit logging service
            db_session: Database session (SQLAlchemy or MongoDB)
        """
        self.token_manager = token_manager or MultiTenantTokenManager()
        self.audit_logger = audit_logger or MultiTenantAuditLogger()
        self.db_session = db_session
        
        # In-memory user store (fallback when no DB)
        self._users: Dict[str, TenantUser] = {}
        self._refresh_tokens: Dict[str, Dict] = {}  # jti -> user mapping
        
        # Seed default users
        self._seed_default_users()
    
    def _seed_default_users(self):
        """Seed default users for development/testing."""
        default_tenant = AuthConfig.DEFAULT_TENANT_ID
        
        # Super admin (platform-wide)
        self._create_user_internal(
            user_id="super-admin-001",
            tenant_id=default_tenant,
            email="superadmin@aquawatch.io",
            password="SuperAdmin123!",
            role=TenantRole.SUPER_ADMIN,
            name="Platform Super Admin"
        )
        
        # Default tenant users
        default_users = [
            ("admin-001", "admin@lwsc.co.zm", "admin123", TenantRole.TENANT_ADMIN, "System Administrator"),
            ("operator-001", "operator@lwsc.co.zm", "operator123", TenantRole.OPERATOR, "Control Room Operator"),
            ("technician-001", "technician@lwsc.co.zm", "technician123", TenantRole.TECHNICIAN, "Field Technician"),
            ("engineer-001", "engineer@lwsc.co.zm", "engineer123", TenantRole.ENGINEER, "System Engineer"),
            ("executive-001", "executive@lwsc.co.zm", "executive123", TenantRole.EXECUTIVE, "Chief Operations Officer"),
            ("viewer-001", "viewer@lwsc.co.zm", "viewer123", TenantRole.VIEWER, "Dashboard Viewer"),
        ]
        
        for user_id, email, password, role, name in default_users:
            self._create_user_internal(
                user_id=user_id,
                tenant_id=default_tenant,
                email=email,
                password=password,
                role=role,
                name=name
            )
    
    def _create_user_internal(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        password: str,
        role: TenantRole,
        name: str = ""
    ) -> TenantUser:
        """Create user in internal store."""
        user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            password_hash=PasswordUtils.hash_password(password),
            role=role,
            name=name,
            created_at=datetime.utcnow()
        )
        self._users[f"{tenant_id}:{email}"] = user
        return user
    
    def _get_user_by_email(self, tenant_id: str, email: str) -> Optional[TenantUser]:
        """Get user by email within tenant."""
        # Try tenant-specific first
        key = f"{tenant_id}:{email}"
        if key in self._users:
            return self._users[key]
        
        # For super admin, check all tenants
        for user_key, user in self._users.items():
            if user.email == email and user.role == TenantRole.SUPER_ADMIN:
                return user
        
        return None
    
    def authenticate(
        self,
        email: str,
        password: str,
        tenant_id: str = None,
        request = None
    ) -> Tuple[bool, Optional[TokenResponse], Optional[str]]:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User email
            password: User password
            tenant_id: Tenant context (optional for super admin)
            request: FastAPI request for audit logging
        
        Returns:
            Tuple of (success, token_response, error_message)
        """
        # Use default tenant if not specified
        tenant_id = tenant_id or AuthConfig.DEFAULT_TENANT_ID
        
        # Find user
        user = self._get_user_by_email(tenant_id, email)
        
        if not user:
            # Log failed attempt
            self.audit_logger.log_login(
                tenant_id=tenant_id,
                user_id="unknown",
                user_email=email,
                request=request,
                success=False,
                error_message="User not found"
            )
            return False, None, "Invalid email or password"
        
        # Check if account is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return False, None, f"Account locked. Try again in {remaining} minutes"
        
        # Verify password
        if not PasswordUtils.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_MINUTES)
            
            self.audit_logger.log_login(
                tenant_id=tenant_id,
                user_id=user.user_id,
                user_email=email,
                request=request,
                success=False,
                error_message=f"Invalid password (attempt {user.failed_login_attempts})"
            )
            
            return False, None, "Invalid email or password"
        
        # Check if user is active
        if not user.is_active:
            return False, None, "Account is disabled"
        
        # Success - reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
            email=user.email,
            name=user.name
        )
        
        refresh_token = self.token_manager.create_refresh_token(
            user_id=user.user_id,
            tenant_id=user.tenant_id
        )
        
        # Log success
        self.audit_logger.log_login(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            user_email=user.email,
            request=request,
            success=True
        )
        
        return True, TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.token_manager.access_token_expire_minutes * 60,
            user=user.to_dict()
        ), None
    
    def refresh_access_token(
        self,
        refresh_token: str,
        request = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            request: FastAPI request for audit
        
        Returns:
            Tuple of (success, new_access_token, error_message)
        """
        payload = self.token_manager.verify_token(refresh_token)
        
        if not payload:
            return False, None, "Invalid or expired refresh token"
        
        if payload.type != "refresh":
            return False, None, "Invalid token type"
        
        # Get user
        user_key = f"{payload.tenant_id}:{payload.user_id}"
        user = None
        for key, u in self._users.items():
            if u.user_id == payload.user_id:
                user = u
                break
        
        if not user or not user.is_active:
            return False, None, "User not found or inactive"
        
        # Create new access token
        new_access_token = self.token_manager.create_access_token(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
            email=user.email,
            name=user.name
        )
        
        # Log refresh
        self.audit_logger.log(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            action=AuditAction.TOKEN_REFRESH,
            resource_type="auth",
            resource_id=user.email,
            request=request,
            user_email=user.email
        )
        
        return True, new_access_token, None
    
    def change_password(
        self,
        user_id: str,
        tenant_id: str,
        current_password: str,
        new_password: str,
        request = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            current_password: Current password
            new_password: New password
            request: FastAPI request for audit
        
        Returns:
            Tuple of (success, error_message)
        """
        # Find user
        user = None
        for u in self._users.values():
            if u.user_id == user_id and u.tenant_id == tenant_id:
                user = u
                break
        
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not PasswordUtils.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password
        valid, errors = PasswordUtils.validate_password_strength(new_password)
        if not valid:
            return False, "; ".join(errors)
        
        # Update password
        user.password_hash = PasswordUtils.hash_password(new_password)
        
        # Log change
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.PASSWORD_CHANGE,
            resource_type="user",
            resource_id=user_id,
            request=request,
            user_email=user.email
        )
        
        return True, None
    
    def create_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        role: TenantRole,
        name: str = "",
        created_by: CurrentUser = None,
        request = None
    ) -> Tuple[bool, Optional[TenantUser], Optional[str]]:
        """
        Create new user in tenant.
        
        Args:
            tenant_id: Tenant ID
            email: User email
            password: Initial password
            role: User role
            name: Display name
            created_by: User creating this account
            request: FastAPI request for audit
        
        Returns:
            Tuple of (success, user, error_message)
        """
        # Check if email already exists in tenant
        if self._get_user_by_email(tenant_id, email):
            return False, None, "Email already registered"
        
        # Validate password
        valid, errors = PasswordUtils.validate_password_strength(password)
        if not valid:
            return False, None, "; ".join(errors)
        
        # Cannot create SUPER_ADMIN unless you are SUPER_ADMIN
        if role == TenantRole.SUPER_ADMIN:
            if not created_by or created_by.role != TenantRole.SUPER_ADMIN:
                return False, None, "Only super admins can create super admin accounts"
        
        # Create user
        user_id = secrets.token_urlsafe(16)
        user = self._create_user_internal(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            password=password,
            role=role,
            name=name
        )
        
        # Log creation
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id=created_by.user_id if created_by else "system",
            action=AuditAction.USER_CREATE,
            resource_type="user",
            resource_id=user_id,
            request=request,
            details={"email": email, "role": role.value}
        )
        
        return True, user, None
    
    def get_user_by_id(self, user_id: str) -> Optional[TenantUser]:
        """Get user by ID."""
        for user in self._users.values():
            if user.user_id == user_id:
                return user
        return None
    
    def list_users_for_tenant(self, tenant_id: str) -> List[TenantUser]:
        """List all users in a tenant."""
        return [u for u in self._users.values() if u.tenant_id == tenant_id]
    
    def deactivate_user(
        self,
        user_id: str,
        tenant_id: str,
        deactivated_by: CurrentUser,
        request = None
    ) -> Tuple[bool, Optional[str]]:
        """Deactivate user account."""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        if user.tenant_id != tenant_id and deactivated_by.role != TenantRole.SUPER_ADMIN:
            return False, "Cannot deactivate user from different tenant"
        
        user.is_active = False
        
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id=deactivated_by.user_id,
            action=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=user_id,
            request=request,
            details={"action": "deactivate"}
        )
        
        return True, None


# Global auth service instance
auth_service = MultiTenantAuthService()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PasswordUtils",
    "TenantUser",
    "MultiTenantAuthService",
    "auth_service",
]
