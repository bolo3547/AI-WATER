"""
AquaWatch NRW v3.0 - Multi-Tenant Auth Tests
=============================================

Tests for:
1. JWT token creation and validation
2. Tenant isolation (users can't access other tenants)
3. RBAC (role-based access control)
4. Permission-based access control
5. Audit logging

Run with: pytest src/security/test_multi_tenant_auth.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import auth modules
from .multi_tenant_auth import (
    TenantRole,
    Permission,
    CurrentUser,
    MultiTenantTokenManager,
    TenantGuard,
    RequireRole,
    RequirePermission,
    ROLE_PERMISSIONS,
    AuditAction,
    MultiTenantAuditLogger,
    AuthConfig
)
from .auth_service import (
    MultiTenantAuthService,
    PasswordUtils,
    TenantUser
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def token_manager():
    """Create token manager with test secret."""
    return MultiTenantTokenManager(secret_key="test-secret-key-for-testing")


@pytest.fixture
def auth_service():
    """Create auth service for testing."""
    return MultiTenantAuthService()


@pytest.fixture
def audit_logger():
    """Create audit logger for testing."""
    return MultiTenantAuditLogger()


# =============================================================================
# PASSWORD UTILS TESTS
# =============================================================================

class TestPasswordUtils:
    """Tests for password utilities."""
    
    def test_hash_password_creates_unique_hashes(self):
        """Same password should create different hashes (due to salt)."""
        password = "TestPassword123!"
        hash1 = PasswordUtils.hash_password(password)
        hash2 = PasswordUtils.hash_password(password)
        
        # Different hashes due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "TestPassword123!"
        password_hash = PasswordUtils.hash_password(password)
        
        assert PasswordUtils.verify_password(password, password_hash) is True
    
    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "TestPassword123!"
        password_hash = PasswordUtils.hash_password(password)
        
        assert PasswordUtils.verify_password("WrongPassword", password_hash) is False
    
    def test_password_validation_too_short(self):
        """Short password should fail validation."""
        valid, errors = PasswordUtils.validate_password_strength("short")
        
        assert valid is False
        assert any("at least" in e for e in errors)
    
    def test_password_validation_missing_uppercase(self):
        """Password without uppercase should fail."""
        valid, errors = PasswordUtils.validate_password_strength("lowercase123!")
        
        assert valid is False
        assert any("uppercase" in e.lower() for e in errors)
    
    def test_password_validation_strong(self):
        """Strong password should pass validation."""
        valid, errors = PasswordUtils.validate_password_strength("StrongPass123!")
        
        assert valid is True
        assert len(errors) == 0


# =============================================================================
# JWT TOKEN TESTS
# =============================================================================

class TestTokenManager:
    """Tests for JWT token management."""
    
    def test_create_access_token(self, token_manager):
        """Access token should contain correct claims."""
        token = token_manager.create_access_token(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            email="test@example.com",
            name="Test User"
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_verify_access_token(self, token_manager):
        """Valid token should be verified successfully."""
        token = token_manager.create_access_token(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload is not None
        assert payload.user_id == "user-001"
        assert payload.tenant_id == "tenant-001"
        assert payload.role == TenantRole.OPERATOR
        assert payload.type == "access"
    
    def test_token_contains_permissions(self, token_manager):
        """Token should contain role permissions."""
        token = token_manager.create_access_token(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload is not None
        assert len(payload.permissions) > 0
        assert "alert:read" in payload.permissions
        assert "alert:acknowledge" in payload.permissions
    
    def test_expired_token_fails(self, token_manager):
        """Expired token should fail verification."""
        # Create token manager with very short expiry
        short_expiry_manager = MultiTenantTokenManager(
            secret_key="test-secret",
            access_token_expire_minutes=-1  # Already expired
        )
        
        token = short_expiry_manager.create_access_token(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR
        )
        
        payload = short_expiry_manager.verify_token(token)
        
        assert payload is None  # Should fail due to expiration
    
    def test_invalid_token_fails(self, token_manager):
        """Invalid token should fail verification."""
        payload = token_manager.verify_token("invalid-token")
        
        assert payload is None
    
    def test_create_refresh_token(self, token_manager):
        """Refresh token should be created with correct type."""
        token = token_manager.create_refresh_token(
            user_id="user-001",
            tenant_id="tenant-001"
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload is not None
        assert payload.type == "refresh"
        assert payload.jti is not None  # Unique token ID


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================

class TestTenantIsolation:
    """Tests for tenant isolation."""
    
    def test_user_can_access_own_tenant(self):
        """User should be able to access their own tenant."""
        user = CurrentUser(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions=set(p.value for p in ROLE_PERMISSIONS[TenantRole.OPERATOR])
        )
        
        assert user.can_access_tenant("tenant-001") is True
    
    def test_user_cannot_access_other_tenant(self):
        """User should NOT be able to access other tenants."""
        user = CurrentUser(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions=set(p.value for p in ROLE_PERMISSIONS[TenantRole.OPERATOR])
        )
        
        assert user.can_access_tenant("tenant-002") is False
    
    def test_super_admin_can_access_any_tenant(self):
        """SUPER_ADMIN should access any tenant."""
        user = CurrentUser(
            user_id="super-admin",
            tenant_id="platform",
            role=TenantRole.SUPER_ADMIN,
            permissions=set(p.value for p in ROLE_PERMISSIONS[TenantRole.SUPER_ADMIN])
        )
        
        assert user.can_access_tenant("tenant-001") is True
        assert user.can_access_tenant("tenant-002") is True
        assert user.can_access_tenant("any-tenant") is True
    
    def test_is_super_admin(self):
        """is_super_admin should correctly identify role."""
        super_admin = CurrentUser(
            user_id="admin",
            tenant_id="platform",
            role=TenantRole.SUPER_ADMIN,
            permissions=set()
        )
        
        regular_user = CurrentUser(
            user_id="user",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions=set()
        )
        
        assert super_admin.is_super_admin() is True
        assert regular_user.is_super_admin() is False


# =============================================================================
# RBAC TESTS
# =============================================================================

class TestRBAC:
    """Tests for role-based access control."""
    
    def test_role_has_correct_permissions(self):
        """Roles should have expected permissions."""
        # OPERATOR should have alert:read and alert:acknowledge
        operator_perms = ROLE_PERMISSIONS[TenantRole.OPERATOR]
        assert Permission.ALERT_READ in operator_perms
        assert Permission.ALERT_ACKNOWLEDGE in operator_perms
        
        # OPERATOR should NOT have user management
        assert Permission.USER_CREATE not in operator_perms
        assert Permission.USER_DELETE not in operator_perms
    
    def test_technician_permissions(self):
        """TECHNICIAN should have limited permissions."""
        tech_perms = ROLE_PERMISSIONS[TenantRole.TECHNICIAN]
        
        # Can read and complete work orders
        assert Permission.WORKORDER_READ in tech_perms
        assert Permission.WORKORDER_COMPLETE in tech_perms
        
        # Cannot create or assign
        assert Permission.WORKORDER_CREATE not in tech_perms
        assert Permission.WORKORDER_ASSIGN not in tech_perms
    
    def test_tenant_admin_has_all_tenant_permissions(self):
        """TENANT_ADMIN should have all tenant-level permissions."""
        admin_perms = ROLE_PERMISSIONS[TenantRole.TENANT_ADMIN]
        
        # User management
        assert Permission.USER_CREATE in admin_perms
        assert Permission.USER_UPDATE in admin_perms
        assert Permission.USER_DELETE in admin_perms
        
        # But NOT tenant-level management (that's SUPER_ADMIN)
        assert Permission.TENANT_CREATE not in admin_perms
        assert Permission.TENANT_DELETE not in admin_perms
    
    def test_super_admin_has_all_permissions(self):
        """SUPER_ADMIN should have ALL permissions."""
        super_admin_perms = ROLE_PERMISSIONS[TenantRole.SUPER_ADMIN]
        
        # Should have every permission
        for perm in Permission:
            assert perm in super_admin_perms
    
    def test_user_has_permission(self):
        """CurrentUser.has_permission should work correctly."""
        user = CurrentUser(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions={"alert:read", "alert:acknowledge", "workorder:create"}
        )
        
        assert user.has_permission(Permission.ALERT_READ) is True
        assert user.has_permission(Permission.ALERT_ACKNOWLEDGE) is True
        assert user.has_permission(Permission.USER_CREATE) is False
    
    def test_user_has_any_permission(self):
        """has_any_permission should return True if any match."""
        user = CurrentUser(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions={"alert:read"}
        )
        
        assert user.has_any_permission([Permission.ALERT_READ, Permission.USER_CREATE]) is True
        assert user.has_any_permission([Permission.USER_CREATE, Permission.USER_DELETE]) is False
    
    def test_user_has_all_permissions(self):
        """has_all_permissions should require all to match."""
        user = CurrentUser(
            user_id="user-001",
            tenant_id="tenant-001",
            role=TenantRole.OPERATOR,
            permissions={"alert:read", "alert:acknowledge"}
        )
        
        assert user.has_all_permissions([Permission.ALERT_READ, Permission.ALERT_ACKNOWLEDGE]) is True
        assert user.has_all_permissions([Permission.ALERT_READ, Permission.USER_CREATE]) is False


# =============================================================================
# AUTH SERVICE TESTS
# =============================================================================

class TestAuthService:
    """Tests for authentication service."""
    
    def test_authenticate_valid_user(self, auth_service):
        """Valid credentials should authenticate successfully."""
        success, response, error = auth_service.authenticate(
            email="operator@lwsc.co.zm",
            password="operator123",
            tenant_id="default-tenant"
        )
        
        assert success is True
        assert response is not None
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert error is None
    
    def test_authenticate_invalid_password(self, auth_service):
        """Invalid password should fail authentication."""
        success, response, error = auth_service.authenticate(
            email="operator@lwsc.co.zm",
            password="wrong-password",
            tenant_id="default-tenant"
        )
        
        assert success is False
        assert response is None
        assert "Invalid" in error
    
    def test_authenticate_unknown_user(self, auth_service):
        """Unknown user should fail authentication."""
        success, response, error = auth_service.authenticate(
            email="unknown@example.com",
            password="password",
            tenant_id="default-tenant"
        )
        
        assert success is False
        assert response is None
    
    def test_account_lockout(self, auth_service):
        """Account should lock after too many failed attempts."""
        # Make multiple failed attempts
        for _ in range(5):
            auth_service.authenticate(
                email="operator@lwsc.co.zm",
                password="wrong-password",
                tenant_id="default-tenant"
            )
        
        # Next attempt should indicate lockout
        success, response, error = auth_service.authenticate(
            email="operator@lwsc.co.zm",
            password="operator123",  # Even correct password
            tenant_id="default-tenant"
        )
        
        assert success is False
        assert "locked" in error.lower()
    
    def test_create_user(self, auth_service):
        """Should be able to create new users."""
        success, user, error = auth_service.create_user(
            tenant_id="default-tenant",
            email="newuser@lwsc.co.zm",
            password="NewUser123!",
            role=TenantRole.VIEWER,
            name="New User"
        )
        
        assert success is True
        assert user is not None
        assert user.email == "newuser@lwsc.co.zm"
        assert user.role == TenantRole.VIEWER
    
    def test_create_user_weak_password(self, auth_service):
        """Weak password should fail user creation."""
        success, user, error = auth_service.create_user(
            tenant_id="default-tenant",
            email="weakuser@lwsc.co.zm",
            password="weak",  # Too short
            role=TenantRole.VIEWER
        )
        
        assert success is False
        assert user is None
        assert error is not None


# =============================================================================
# AUDIT LOGGING TESTS
# =============================================================================

class TestAuditLogging:
    """Tests for audit logging."""
    
    def test_log_creates_entry(self, audit_logger):
        """Logging should create audit entry."""
        entry = audit_logger.log(
            tenant_id="tenant-001",
            user_id="user-001",
            action=AuditAction.LOGIN,
            resource_type="auth",
            resource_id="user@example.com"
        )
        
        assert entry is not None
        assert entry.tenant_id == "tenant-001"
        assert entry.user_id == "user-001"
        assert entry.action == AuditAction.LOGIN
    
    def test_log_login_success(self, audit_logger):
        """Login logging should work correctly."""
        entry = audit_logger.log_login(
            tenant_id="tenant-001",
            user_id="user-001",
            user_email="user@example.com",
            request=None,
            success=True
        )
        
        assert entry.action == AuditAction.LOGIN
        assert entry.success is True
    
    def test_log_login_failure(self, audit_logger):
        """Failed login logging should record error."""
        entry = audit_logger.log_login(
            tenant_id="tenant-001",
            user_id="unknown",
            user_email="attacker@example.com",
            request=None,
            success=False,
            error_message="Invalid credentials"
        )
        
        assert entry.action == AuditAction.LOGIN_FAILED
        assert entry.success is False
        assert entry.error_message == "Invalid credentials"
    
    def test_log_leak_acknowledge(self, audit_logger):
        """Leak acknowledge logging should work."""
        entry = audit_logger.log_leak_acknowledge(
            tenant_id="tenant-001",
            user_id="operator-001",
            leak_id="leak-001",
            request=None,
            user_email="operator@example.com"
        )
        
        assert entry.action == AuditAction.LEAK_ACKNOWLEDGE
        assert entry.resource_type == "leak"
        assert entry.resource_id == "leak-001"
    
    def test_log_workorder_create(self, audit_logger):
        """Work order creation logging should work."""
        entry = audit_logger.log_workorder_create(
            tenant_id="tenant-001",
            user_id="operator-001",
            workorder_id="wo-001",
            request=None,
            details={"priority": 2}
        )
        
        assert entry.action == AuditAction.WORKORDER_CREATE
        assert entry.resource_type == "workorder"
        assert entry.details["priority"] == 2
    
    def test_get_logs_for_tenant(self, audit_logger):
        """Should retrieve logs for specific tenant."""
        # Create logs for different tenants
        audit_logger.log(
            tenant_id="tenant-001",
            user_id="user-001",
            action=AuditAction.LOGIN,
            resource_type="auth",
            resource_id="user1"
        )
        audit_logger.log(
            tenant_id="tenant-002",
            user_id="user-002",
            action=AuditAction.LOGIN,
            resource_type="auth",
            resource_id="user2"
        )
        audit_logger.log(
            tenant_id="tenant-001",
            user_id="user-001",
            action=AuditAction.WORKORDER_CREATE,
            resource_type="workorder",
            resource_id="wo-001"
        )
        
        # Get logs for tenant-001 only
        logs = audit_logger.get_logs_for_tenant("tenant-001")
        
        assert len(logs) == 2
        assert all(log.tenant_id == "tenant-001" for log in logs)


# =============================================================================
# ROLE HIERARCHY TESTS
# =============================================================================

class TestRoleHierarchy:
    """Tests for role hierarchy (higher roles can do lower role actions)."""
    
    def test_engineer_can_do_operator_tasks(self):
        """ENGINEER should have OPERATOR permissions."""
        engineer_perms = ROLE_PERMISSIONS[TenantRole.ENGINEER]
        operator_perms = ROLE_PERMISSIONS[TenantRole.OPERATOR]
        
        # Engineer should have all operator permissions
        for perm in operator_perms:
            assert perm in engineer_perms, f"ENGINEER missing OPERATOR permission: {perm}"
    
    def test_tenant_admin_can_do_engineer_tasks(self):
        """TENANT_ADMIN should have ENGINEER permissions."""
        admin_perms = ROLE_PERMISSIONS[TenantRole.TENANT_ADMIN]
        engineer_perms = ROLE_PERMISSIONS[TenantRole.ENGINEER]
        
        # Admin should have all engineer permissions
        for perm in engineer_perms:
            assert perm in admin_perms, f"TENANT_ADMIN missing ENGINEER permission: {perm}"
    
    def test_viewer_has_minimal_permissions(self):
        """VIEWER should have minimal read-only permissions."""
        viewer_perms = ROLE_PERMISSIONS[TenantRole.VIEWER]
        
        # Should have read permissions
        assert Permission.ALERT_READ in viewer_perms
        assert Permission.DATA_READ in viewer_perms
        
        # Should NOT have write permissions
        assert Permission.ALERT_ACKNOWLEDGE not in viewer_perms
        assert Permission.WORKORDER_CREATE not in viewer_perms


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
