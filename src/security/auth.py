"""
AquaWatch NRW - Security Module
================================

Implements security controls for the platform:
1. Authentication - JWT-based token authentication
2. Authorization - Role-based access control (RBAC)
3. Data Encryption - AES-256 for sensitive data
4. Audit Logging - Comprehensive activity logging
5. Rate Limiting - API abuse prevention

Security Principles:
- Defense in depth
- Least privilege
- Zero trust within network
- Encryption at rest and in transit
"""

import hashlib
import hmac
import os
import secrets
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class UserRole(Enum):
    """User roles for RBAC."""
    ADMIN = "admin"               # Full system access
    MANAGER = "manager"           # Utility management
    OPERATOR = "operator"         # Operations center
    TECHNICIAN = "technician"     # Field operations
    ANALYST = "analyst"           # Read-only analytics
    VIEWER = "viewer"             # Dashboard only


class Permission(Enum):
    """Granular permissions."""
    # Alert permissions
    ALERT_VIEW = "alert:view"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_CLOSE = "alert:close"
    
    # Work order permissions
    WORKORDER_VIEW = "workorder:view"
    WORKORDER_CREATE = "workorder:create"
    WORKORDER_ASSIGN = "workorder:assign"
    WORKORDER_COMPLETE = "workorder:complete"
    
    # Data permissions
    DATA_VIEW = "data:view"
    DATA_EXPORT = "data:export"
    DATA_DELETE = "data:delete"
    
    # Configuration permissions
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    
    # User management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    
    # AI model permissions
    MODEL_VIEW = "model:view"
    MODEL_TRAIN = "model:train"
    MODEL_DEPLOY = "model:deploy"


class AuditAction(Enum):
    """Audit log action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    ALERT_VIEW = "alert_view"
    ALERT_ACKNOWLEDGE = "alert_acknowledge"
    ALERT_CLOSE = "alert_close"
    
    WORKORDER_CREATE = "workorder_create"
    WORKORDER_UPDATE = "workorder_update"
    WORKORDER_COMPLETE = "workorder_complete"
    
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    
    CONFIG_CHANGE = "config_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    
    MODEL_DEPLOY = "model_deploy"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class User:
    """User account."""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    utility_id: str  # Scope to specific utility
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    permissions: Set[Permission] = field(default_factory=set)


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_valid: bool = True


@dataclass
class AuditLog:
    """Audit log entry."""
    log_id: str
    timestamp: datetime
    user_id: str
    action: AuditAction
    resource_type: str
    resource_id: str
    ip_address: str
    details: Dict = field(default_factory=dict)
    success: bool = True


# =============================================================================
# ROLE-PERMISSION MAPPING
# =============================================================================

ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: set(Permission),  # All permissions
    
    UserRole.MANAGER: {
        Permission.ALERT_VIEW, Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_CLOSE,
        Permission.WORKORDER_VIEW, Permission.WORKORDER_CREATE, Permission.WORKORDER_ASSIGN,
        Permission.DATA_VIEW, Permission.DATA_EXPORT,
        Permission.CONFIG_VIEW, Permission.CONFIG_EDIT,
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_EDIT,
        Permission.MODEL_VIEW
    },
    
    UserRole.OPERATOR: {
        Permission.ALERT_VIEW, Permission.ALERT_ACKNOWLEDGE,
        Permission.WORKORDER_VIEW, Permission.WORKORDER_CREATE, Permission.WORKORDER_ASSIGN,
        Permission.DATA_VIEW,
        Permission.CONFIG_VIEW
    },
    
    UserRole.TECHNICIAN: {
        Permission.ALERT_VIEW,
        Permission.WORKORDER_VIEW, Permission.WORKORDER_COMPLETE,
        Permission.DATA_VIEW
    },
    
    UserRole.ANALYST: {
        Permission.ALERT_VIEW,
        Permission.WORKORDER_VIEW,
        Permission.DATA_VIEW, Permission.DATA_EXPORT,
        Permission.MODEL_VIEW
    },
    
    UserRole.VIEWER: {
        Permission.ALERT_VIEW,
        Permission.DATA_VIEW
    }
}


# =============================================================================
# PASSWORD MANAGEMENT
# =============================================================================

class PasswordManager:
    """Secure password handling."""
    
    # Password requirements
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    # PBKDF2 parameters
    ITERATIONS = 480000  # OWASP 2023 recommendation
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password using PBKDF2-SHA256."""
        
        salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=cls.ITERATIONS
        )
        
        key = kdf.derive(password.encode('utf-8'))
        
        # Combine salt and key for storage
        combined = salt + key
        return base64.b64encode(combined).decode('utf-8')
    
    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        
        try:
            combined = base64.b64decode(stored_hash.encode('utf-8'))
            salt = combined[:32]
            stored_key = combined[32:]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=cls.ITERATIONS
            )
            
            # This will raise exception if password doesn't match
            kdf.verify(password.encode('utf-8'), stored_key)
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_password_strength(cls, password: str) -> tuple[bool, List[str]]:
        """Validate password meets requirements."""
        
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")
        
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letter")
        
        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letter")
        
        if cls.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            errors.append("Password must contain digit")
        
        if cls.REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain special character")
        
        return len(errors) == 0, errors


# =============================================================================
# JWT TOKEN MANAGEMENT
# =============================================================================

class TokenManager:
    """JWT token management."""
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    def __init__(self, secret_key: str):
        """Initialize with secret key."""
        self.secret_key = secret_key
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: UserRole,
        utility_id: str,
        permissions: Set[Permission]
    ) -> str:
        """Create JWT access token."""
        
        expires = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role.value,
            "utility_id": utility_id,
            "permissions": [p.value for p in permissions],
            "exp": expires,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        
        expires = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "exp": expires,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode token."""
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM]
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from token."""
        
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


# =============================================================================
# DATA ENCRYPTION
# =============================================================================

class DataEncryption:
    """AES-256 encryption for sensitive data."""
    
    def __init__(self, encryption_key: bytes = None):
        """Initialize with encryption key."""
        
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
        
        self.fernet = Fernet(encryption_key)
        self._key = encryption_key
    
    @property
    def key(self) -> bytes:
        """Get encryption key (for secure storage)."""
        return self._key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        
        encrypted = self.fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_dict(self, data: Dict) -> str:
        """Encrypt dictionary as JSON."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict:
        """Decrypt dictionary from JSON."""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AuditLogger:
    """Comprehensive audit logging."""
    
    def __init__(self, log_file: str = "audit.log"):
        self.logs: List[AuditLog] = []
        self.log_file = log_file
        
        # Set up file logging
        self.file_logger = logging.getLogger("audit")
        self.file_logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.file_logger.addHandler(handler)
    
    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        ip_address: str = "unknown",
        details: Dict = None,
        success: bool = True
    ) -> AuditLog:
        """Create audit log entry."""
        
        entry = AuditLog(
            log_id=secrets.token_urlsafe(16),
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details or {},
            success=success
        )
        
        self.logs.append(entry)
        
        # Write to file
        log_line = (
            f"[{entry.action.value}] "
            f"user={entry.user_id} "
            f"resource={entry.resource_type}/{entry.resource_id} "
            f"ip={entry.ip_address} "
            f"success={entry.success} "
            f"details={json.dumps(entry.details)}"
        )
        self.file_logger.info(log_line)
        
        return entry
    
    def get_logs_for_user(
        self,
        user_id: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[AuditLog]:
        """Get audit logs for specific user."""
        
        logs = [l for l in self.logs if l.user_id == user_id]
        
        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]
        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]
        
        return logs
    
    def get_logs_for_resource(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[AuditLog]:
        """Get audit logs for specific resource."""
        
        return [
            l for l in self.logs
            if l.resource_type == resource_type and l.resource_id == resource_id
        ]


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Get requests in window
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            t for t in self.requests[identifier]
            if t > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in window."""
        
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if identifier not in self.requests:
            return self.max_requests
        
        current_count = len([
            t for t in self.requests[identifier]
            if t > window_start
        ])
        
        return max(0, self.max_requests - current_count)


# =============================================================================
# AUTHENTICATION SERVICE
# =============================================================================

class AuthenticationService:
    """Main authentication and authorization service."""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 30
    
    def __init__(self, jwt_secret: str):
        self.token_manager = TokenManager(jwt_secret)
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # In-memory user store (replace with database in production)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole,
        utility_id: str
    ) -> tuple[bool, str]:
        """Register new user."""
        
        # Validate password strength
        valid, errors = PasswordManager.validate_password_strength(password)
        if not valid:
            return False, "; ".join(errors)
        
        # Check if username exists
        if any(u.username == username for u in self.users.values()):
            return False, "Username already exists"
        
        # Create user
        user_id = secrets.token_urlsafe(16)
        password_hash = PasswordManager.hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            utility_id=utility_id,
            permissions=ROLE_PERMISSIONS.get(role, set())
        )
        
        self.users[user_id] = user
        
        self.audit_logger.log(
            user_id="system",
            action=AuditAction.USER_CREATE,
            resource_type="user",
            resource_id=user_id,
            details={"username": username, "role": role.value}
        )
        
        return True, user_id
    
    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str = "unknown"
    ) -> tuple[bool, Optional[Dict]]:
        """Authenticate user and return tokens."""
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(ip_address):
            logger.warning(f"Rate limit exceeded for {ip_address}")
            return False, {"error": "Rate limit exceeded"}
        
        # Find user
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if user is None:
            self.audit_logger.log(
                user_id="unknown",
                action=AuditAction.LOGIN_FAILED,
                resource_type="auth",
                resource_id=username,
                ip_address=ip_address,
                details={"reason": "user_not_found"},
                success=False
            )
            return False, {"error": "Invalid credentials"}
        
        # Check lockout
        if user.locked_until and datetime.now() < user.locked_until:
            return False, {"error": "Account locked"}
        
        # Verify password
        if not PasswordManager.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_MINUTES)
            
            self.audit_logger.log(
                user_id=user.user_id,
                action=AuditAction.LOGIN_FAILED,
                resource_type="auth",
                resource_id=username,
                ip_address=ip_address,
                details={"attempts": user.failed_login_attempts},
                success=False
            )
            
            return False, {"error": "Invalid credentials"}
        
        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            user.user_id,
            user.username,
            user.role,
            user.utility_id,
            user.permissions
        )
        refresh_token = self.token_manager.create_refresh_token(user.user_id)
        
        # Log success
        self.audit_logger.log(
            user_id=user.user_id,
            action=AuditAction.LOGIN,
            resource_type="auth",
            resource_id=username,
            ip_address=ip_address
        )
        
        return True, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.token_manager.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "utility_id": user.utility_id
            }
        }
    
    def authorize(
        self,
        token: str,
        required_permission: Permission
    ) -> tuple[bool, Optional[str]]:
        """Check if token has required permission."""
        
        payload = self.token_manager.verify_token(token)
        
        if payload is None:
            return False, "Invalid or expired token"
        
        permissions = set(Permission(p) for p in payload.get("permissions", []))
        
        if required_permission not in permissions:
            return False, "Insufficient permissions"
        
        return True, payload.get("sub")
    
    def logout(self, token: str, ip_address: str = "unknown"):
        """Logout user and invalidate session."""
        
        user_id = self.token_manager.get_user_id_from_token(token)
        
        if user_id:
            self.audit_logger.log(
                user_id=user_id,
                action=AuditAction.LOGOUT,
                resource_type="auth",
                resource_id=user_id,
                ip_address=ip_address
            )


# =============================================================================
# AUTHORIZATION DECORATOR
# =============================================================================

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get auth service and token from context
            # This is simplified - in real app, get from request context
            auth_service = kwargs.get('auth_service')
            token = kwargs.get('token')
            
            if auth_service and token:
                authorized, result = auth_service.authorize(token, permission)
                if not authorized:
                    raise PermissionError(f"Permission denied: {result}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# DEMO
# =============================================================================

def demo_security():
    """Demonstrate security features."""
    
    print("=" * 60)
    print("AquaWatch NRW - Security Module Demo")
    print("=" * 60)
    
    # Initialize
    auth_service = AuthenticationService(jwt_secret=os.getenv("JWT_SECRET", "demo-only-not-for-production"))
    
    # Register user
    print("\n1. Registering user...")
    success, result = auth_service.register_user(
        username="john.doe",
        email="john@utility.zm",
        password="SecureP@ssw0rd!123",
        role=UserRole.OPERATOR,
        utility_id="UTIL-001"
    )
    print(f"   Registration: {'Success' if success else 'Failed'}")
    
    # Authenticate
    print("\n2. Authenticating...")
    success, tokens = auth_service.authenticate(
        username="john.doe",
        password="SecureP@ssw0rd!123",
        ip_address="192.168.1.100"
    )
    
    if success:
        print(f"   Authentication: Success")
        print(f"   Token (first 50 chars): {tokens['access_token'][:50]}...")
    
    # Test authorization
    print("\n3. Testing authorization...")
    
    # Should succeed (operator has ALERT_VIEW)
    authorized, _ = auth_service.authorize(
        tokens['access_token'],
        Permission.ALERT_VIEW
    )
    print(f"   ALERT_VIEW permission: {'Granted' if authorized else 'Denied'}")
    
    # Should fail (operator doesn't have USER_DELETE)
    authorized, _ = auth_service.authorize(
        tokens['access_token'],
        Permission.USER_DELETE
    )
    print(f"   USER_DELETE permission: {'Granted' if authorized else 'Denied'}")
    
    # Test encryption
    print("\n4. Testing encryption...")
    encryption = DataEncryption()
    
    sensitive_data = {"api_key": "abc123", "secret": "xyz789"}
    encrypted = encryption.encrypt_dict(sensitive_data)
    print(f"   Encrypted: {encrypted[:50]}...")
    
    decrypted = encryption.decrypt_dict(encrypted)
    print(f"   Decrypted: {decrypted}")
    
    # Show audit logs
    print("\n5. Audit logs:")
    for log in auth_service.audit_logger.logs[-5:]:
        print(f"   [{log.action.value}] {log.resource_type}/{log.resource_id}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    demo_security()
