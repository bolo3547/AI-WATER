"""
AquaWatch NRW - Authentication & Authorization
==============================================

Secure remote access with:
- JWT token authentication
- Role-based access control (RBAC)
- API key management for ESP32 devices
- Session management
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
import json

# JWT library
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: PyJWT not installed. Run: pip install PyJWT")

# Password hashing
PASSLIB_AVAILABLE = False
BCRYPT_AVAILABLE = False

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    pass

if not BCRYPT_AVAILABLE:
    try:
        from passlib.context import CryptContext
        # Use sha256_crypt as fallback (no bcrypt dependency issues)
        pwd_context = CryptContext(
            schemes=["sha256_crypt"],
            deprecated="auto"
        )
        PASSLIB_AVAILABLE = True
    except ImportError:
        print("Warning: passlib not installed. Run: pip install passlib")


# =============================================================================
# CONFIGURATION
# =============================================================================

# Secret key for JWT - MUST be set in production
SECRET_KEY = os.getenv("AQUAWATCH_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


# =============================================================================
# ROLE-BASED ACCESS CONTROL
# =============================================================================

class UserRole(Enum):
    """User roles with hierarchical permissions."""
    SUPER_ADMIN = "super_admin"      # Full system access
    UTILITY_ADMIN = "utility_admin"  # Manage single utility
    OPERATOR = "operator"            # View & acknowledge alerts
    TECHNICIAN = "technician"        # Field work orders
    VIEWER = "viewer"                # Read-only dashboard
    API_DEVICE = "api_device"        # ESP32 devices


class Permission(Enum):
    """Granular permissions."""
    # Dashboard
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_ALL_DMAS = "view_all_dmas"
    
    # Alerts
    VIEW_ALERTS = "view_alerts"
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
    CREATE_ALERTS = "create_alerts"
    
    # Work Orders
    VIEW_WORK_ORDERS = "view_work_orders"
    CREATE_WORK_ORDERS = "create_work_orders"
    ASSIGN_WORK_ORDERS = "assign_work_orders"
    COMPLETE_WORK_ORDERS = "complete_work_orders"
    
    # Configuration
    MANAGE_DEVICES = "manage_devices"
    MANAGE_DMAS = "manage_dmas"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    
    # Data
    EXPORT_DATA = "export_data"
    DELETE_DATA = "delete_data"
    
    # API
    API_READ = "api_read"
    API_WRITE = "api_write"


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.SUPER_ADMIN: list(Permission),  # All permissions
    
    UserRole.UTILITY_ADMIN: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ALL_DMAS,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
        Permission.VIEW_WORK_ORDERS,
        Permission.CREATE_WORK_ORDERS,
        Permission.ASSIGN_WORK_ORDERS,
        Permission.MANAGE_DEVICES,
        Permission.MANAGE_DMAS,
        Permission.MANAGE_USERS,
        Permission.EXPORT_DATA,
        Permission.API_READ,
    ],
    
    UserRole.OPERATOR: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
        Permission.VIEW_WORK_ORDERS,
        Permission.CREATE_WORK_ORDERS,
        Permission.API_READ,
    ],
    
    UserRole.TECHNICIAN: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ALERTS,
        Permission.VIEW_WORK_ORDERS,
        Permission.COMPLETE_WORK_ORDERS,
    ],
    
    UserRole.VIEWER: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ALERTS,
    ],
    
    UserRole.API_DEVICE: [
        Permission.API_READ,
        Permission.API_WRITE,
        Permission.CREATE_ALERTS,
    ],
}


# =============================================================================
# USER MODEL
# =============================================================================

@dataclass
class User:
    """User account."""
    id: str
    email: str
    password_hash: str
    role: UserRole
    utility_id: Optional[str] = None  # Which utility they belong to
    dma_ids: List[str] = field(default_factory=list)  # Specific DMAs (empty = all)
    
    # Profile
    full_name: str = ""
    phone: str = ""
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    
    # 2FA
    totp_secret: Optional[str] = None
    two_factor_enabled: bool = False
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def can_access_dma(self, dma_id: str) -> bool:
        """Check if user can access specific DMA."""
        if self.role == UserRole.SUPER_ADMIN:
            return True
        if not self.dma_ids:  # Empty = all DMAs in their utility
            return True
        return dma_id in self.dma_ids


@dataclass
class APIKey:
    """API key for ESP32 devices."""
    key_id: str
    key_hash: str  # Hashed API key
    device_id: str
    utility_id: str
    dma_id: str
    
    # Permissions
    permissions: List[Permission] = field(default_factory=lambda: [
        Permission.API_READ, Permission.API_WRITE
    ])
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    
    # Rate limiting
    rate_limit_per_minute: int = 60


# =============================================================================
# AUTHENTICATION SERVICE
# =============================================================================

class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}  # In production, use database
        self.api_keys: Dict[str, APIKey] = {}
        self.refresh_tokens: Dict[str, str] = {}  # token -> user_id
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if none exists."""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@aquawatch.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "change_me_immediately")
        
        if not any(u.email == admin_email for u in self.users.values()):
            admin = User(
                id="admin_001",
                email=admin_email,
                password_hash=self.hash_password(admin_password),
                role=UserRole.SUPER_ADMIN,
                full_name="System Administrator",
                is_verified=True
            )
            self.users[admin.id] = admin
    
    # -------------------------------------------------------------------------
    # Password Management
    # -------------------------------------------------------------------------
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        if BCRYPT_AVAILABLE:
            # Truncate to 72 bytes and encode for bcrypt
            truncated = password[:72].encode('utf-8')
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(truncated, salt).decode('utf-8')
        elif PASSLIB_AVAILABLE:
            return pwd_context.hash(password)
        # Fallback (NOT secure for production)
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        if BCRYPT_AVAILABLE:
            truncated = plain_password[:72].encode('utf-8')
            return bcrypt.checkpw(truncated, hashed_password.encode('utf-8'))
        elif PASSLIB_AVAILABLE:
            return pwd_context.verify(plain_password, hashed_password)
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    # -------------------------------------------------------------------------
    # User Management
    # -------------------------------------------------------------------------
    
    def create_user(self, email: str, password: str, role: UserRole, 
                    utility_id: str = None, **kwargs) -> User:
        """Create new user account."""
        user_id = f"user_{secrets.token_hex(8)}"
        
        user = User(
            id=user_id,
            email=email.lower(),
            password_hash=self.hash_password(password),
            role=role,
            utility_id=utility_id,
            **kwargs
        )
        
        self.users[user_id] = user
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        email = email.lower()
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        return self.users.get(user_id)
    
    # -------------------------------------------------------------------------
    # Token Management
    # -------------------------------------------------------------------------
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT not installed")
        
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "utility_id": user.utility_id,
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(user.role, [])],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, user: User) -> str:
        """Create refresh token for getting new access tokens."""
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT not installed")
        
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user.id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_hex(16)  # Unique token ID
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        self.refresh_tokens[payload["jti"]] = user.id
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token."""
        if not JWT_AVAILABLE:
            return None
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Get new access token using refresh token."""
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return None
        
        jti = payload.get("jti")
        if jti not in self.refresh_tokens:
            return None
        
        user = self.get_user_by_id(payload["sub"])
        if not user or not user.is_active:
            return None
        
        return self.create_access_token(user)
    
    def revoke_refresh_token(self, refresh_token: str):
        """Revoke refresh token (logout)."""
        payload = self.verify_token(refresh_token)
        if payload and "jti" in payload:
            self.refresh_tokens.pop(payload["jti"], None)
    
    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user and return tokens.
        
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "bearer",
                "user": { ... }
            }
        """
        user = self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        return {
            "access_token": self.create_access_token(user),
            "refresh_token": self.create_refresh_token(user),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name,
                "utility_id": user.utility_id
            }
        }
    
    # -------------------------------------------------------------------------
    # API Key Management (for ESP32 devices)
    # -------------------------------------------------------------------------
    
    def create_api_key(self, device_id: str, utility_id: str, dma_id: str) -> tuple:
        """
        Create API key for ESP32 device.
        
        Returns:
            (api_key_id, api_key_secret)  # Secret shown only once!
        """
        key_id = f"ak_{secrets.token_hex(8)}"
        key_secret = secrets.token_hex(32)
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            device_id=device_id,
            utility_id=utility_id,
            dma_id=dma_id
        )
        
        self.api_keys[key_id] = api_key
        
        # Return full key: key_id.key_secret
        return key_id, f"{key_id}.{key_secret}"
    
    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key and return associated data."""
        try:
            key_id, key_secret = api_key.split(".")
        except ValueError:
            return None
        
        stored_key = self.api_keys.get(key_id)
        if not stored_key:
            return None
        
        # Verify secret
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
        if key_hash != stored_key.key_hash:
            return None
        
        if not stored_key.is_active:
            return None
        
        # Update last used
        stored_key.last_used = datetime.now(timezone.utc)
        
        return stored_key


# =============================================================================
# GLOBAL AUTH SERVICE INSTANCE
# =============================================================================

auth_service = AuthService()


# =============================================================================
# FASTAPI INTEGRATION
# =============================================================================

try:
    from fastapi import Depends, HTTPException, status, Header
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    security = HTTPBearer()
    
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """FastAPI dependency to get current authenticated user."""
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = auth_service.get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def require_permission(permission: Permission):
        """FastAPI dependency to require specific permission."""
        async def permission_checker(user: User = Depends(get_current_user)):
            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            return user
        return permission_checker
    
    async def verify_api_key_header(
        x_api_key: str = Header(None, alias="X-API-Key")
    ) -> APIKey:
        """FastAPI dependency to verify API key from header."""
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return api_key

except ImportError:
    # FastAPI not installed - provide stub functions
    def get_current_user():
        """Stub: FastAPI not installed."""
        raise NotImplementedError("FastAPI required for authentication")
    
    def require_permission(permission):
        """Stub: FastAPI not installed."""
        def stub_checker():
            raise NotImplementedError("FastAPI required for permission checking")
        return stub_checker
    
    def verify_api_key_header():
        """Stub: FastAPI not installed."""
        raise NotImplementedError("FastAPI required for API key verification")
