"""
Better Business Builder - Authentication System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
import secrets
import hashlib
from hmac import compare_digest

try:
    from passlib.context import CryptContext  # type: ignore
except ImportError:  # pragma: no cover
    CryptContext = None
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from .database import get_db, User
from .config import settings

# Security configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Password hashing
if CryptContext:  # pragma: no cover - skip when passlib isn't available
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:  # pragma: no cover - exercised when passlib is unavailable
    class _SimpleCryptContext:
        """Secure PBKDF2-HMAC-SHA256 based password hashing fallback."""

        # Parameters for PBKDF2
        ALGO = 'pbkdf2_sha256'
        ITERATIONS = 100000
        SALT_SIZE = 16

        @staticmethod
        def hash(password: str) -> str:
            """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
            salt = secrets.token_hex(_SimpleCryptContext.SALT_SIZE)
            pw_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                _SimpleCryptContext.ITERATIONS
            ).hex()
            return f"{_SimpleCryptContext.ALGO}${_SimpleCryptContext.ITERATIONS}${salt}${pw_hash}"

        @staticmethod
        def verify(plain_password: str, hashed_password: str) -> bool:
            """Verify a password against a hash."""
            try:
                # Parse secure format: algo$iterations$salt$hash
                parts = hashed_password.split('$')
                if len(parts) != 4:
                    return False

                algo, iterations, salt, pw_hash = parts

                if algo != _SimpleCryptContext.ALGO:
                    return False

                iterations = int(iterations)
                new_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    plain_password.encode('utf-8'),
                    salt.encode('utf-8'),
                    iterations
                ).hex()

                return compare_digest(pw_hash, new_hash)
            except (ValueError, TypeError):
                return False

    pwd_context = _SimpleCryptContext()

# HTTP Bearer token scheme
security = HTTPBearer()


class AuthService:
    """Authentication service for user management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except AttributeError:  # pragma: no cover - defensive fallback for unexpected PyJWT APIs
            # Older/newer PyJWT versions expose PyJWTError instead of JWTError
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Get current user ID from JWT token."""
        token = credentials.credentials
        payload = AuthService.decode_token(token)

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id


class Auth0Service:  # pragma: no cover - exercised via integration tests in deployment environments
    """Auth0 integration for enterprise authentication."""

    def __init__(self):
        self.domain = os.getenv("AUTH0_DOMAIN", "")
        self.client_id = os.getenv("AUTH0_CLIENT_ID", "")
        self.client_secret = os.getenv("AUTH0_CLIENT_SECRET", "")
        self.audience = os.getenv("AUTH0_AUDIENCE", "")
        self.enabled = bool(self.domain and self.client_id)

    def verify_auth0_token(self, token: str) -> dict:
        """Verify Auth0 JWT token."""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Auth0 not configured"
            )

        try:
            # In production, use python-jose to verify Auth0 tokens properly
            # This is a simplified version
            import requests
            from jose import jwt as jose_jwt

            # Get Auth0 public keys
            jwks_url = f'https://{self.domain}/.well-known/jwks.json'
            jwks = requests.get(jwks_url).json()

            # Verify token
            unverified_header = jose_jwt.get_unverified_header(token)
            rsa_key = {}

            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }

            if rsa_key:
                payload = jose_jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=self.audience,
                    issuer=f'https://{self.domain}/'
                )
                return payload

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Auth0 verification failed: {str(e)}"
            )


class RoleBasedAccessControl:
    """Role-based access control for subscription tiers."""

    TIER_PERMISSIONS = {
        "free": {
            "businesses": 1,
            "campaigns_per_month": 5,
            "ai_requests_per_month": 100,
            "social_posts_per_month": 20,
            "email_campaigns_per_month": 2
        },
        "starter": {
            "businesses": 3,
            "campaigns_per_month": 30,
            "ai_requests_per_month": 500,
            "social_posts_per_month": 100,
            "email_campaigns_per_month": 10
        },
        "pro": {
            "businesses": 6,
            "campaigns_per_month": 75,
            "ai_requests_per_month": 2500,
            "social_posts_per_month": 400,
            "email_campaigns_per_month": 40
        },
        "enterprise": {
            "businesses": 12,
            "campaigns_per_month": -1,
            "ai_requests_per_month": -1,
            "social_posts_per_month": -1,
            "email_campaigns_per_month": -1
        }
    }

    TIER_FEATURES = {
        "free": set(),
        "starter": {"core"},
        "pro": {"core", "quantum"},
        "enterprise": {"core", "quantum", "enterprise"}
    }

    @staticmethod
    def check_permission(subscription_tier: str, resource: str, current_count: int) -> bool:
        """Check if user has permission to access resource."""
        tier_limits = RoleBasedAccessControl.TIER_PERMISSIONS.get(subscription_tier, {})
        limit = tier_limits.get(resource, 0)

        # -1 means unlimited
        if limit == -1:
            return True

        return current_count < limit

    @staticmethod
    def has_feature(subscription_tier: str, feature: str) -> bool:
        """Check if tier includes requested feature."""
        features = RoleBasedAccessControl.TIER_FEATURES.get(subscription_tier, set())
        return feature in features


# Dependency for getting current user from database
def get_current_user(
    user_id: str = Depends(AuthService.get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user from database."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def require_license_access(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user has accepted 50% revenue share or purchased a license."""
    # Check if user has purchased a full license
    if current_user.license_status == "licensed":
        return current_user

    # Check if user has accepted 50% revenue share agreement
    if current_user.license_status == "revenue_share":
        return current_user

    # Allow trial period (14 days)
    if current_user.license_status == "trial":
        if current_user.trial_expires_at and current_user.trial_expires_at > datetime.utcnow():
            return current_user

    # No valid license or agreement
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="License required. Choose one: (1) Accept 50% revenue share agreement, or (2) Purchase a full license. Contact support for pricing."
    )


def require_quantum_access(current_user: User = Depends(require_license_access)) -> User:
    """Ensure the current user can access quantum capabilities.

    Quantum features require either:
    1. 50% revenue share agreement, OR
    2. Purchased full license
    """
    # License check already done by require_license_access dependency
    # All licensed/revenue_share users get quantum features
    return current_user


# Rate limiting decorator
def rate_limit(max_requests: int, window_seconds: int):
    """Rate limiting decorator for API endpoints."""
    from functools import wraps
    from collections import defaultdict
    from time import time

    request_counts = defaultdict(list)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('current_user').id if kwargs.get('current_user') else 'anonymous'
            now = time()

            # Clean old requests
            request_counts[user_id] = [
                req_time for req_time in request_counts[user_id]
                if now - req_time < window_seconds
            ]

            # Check rate limit
            if len(request_counts[user_id]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                )

            # Add current request
            request_counts[user_id].append(now)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
