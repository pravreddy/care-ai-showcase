"""
Care AI Engine - Authentication Service
JWT-based auth with bcrypt password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.database import User, Subscription, SubscriptionTier, SubscriptionStatus

from app.services.security_service import validate_password_strength, PasswordValidationError

logger = get_logger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Explicitly truncate to 72 bytes to stay within Bcrypt limits
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    # Truncate during verification so long passwords still match
    return pwd_context.verify(plain[:72], hashed)


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Create a JWT access token. Returns (token, expires_in_seconds)."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")


async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: str,
        organisation: Optional[str] = None,
        role: Optional[str] = None,
) -> User:
    """Register a new user with a free trial subscription."""
    # Validate password strength FIRST
    try:
        validate_password_strength(password, email=email, full_name=full_name)
    except PasswordValidationError as e:
        raise AuthError(f"Password too weak: {'; '.join(e.errors)}")

    # Check if email exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        if existing.auth_provider and not existing.hashed_password:
            # User registered via OAuth — tell them to use that instead
            raise AuthError(
                f"This email is registered via {existing.auth_provider.title()}. "
                f"Please sign in with {existing.auth_provider.title()} instead."
            )
        raise AuthError("Email already registered")

    # Create user
    settings = get_settings()
    is_admin = email.lower() in settings.admin_email_list

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        organisation=organisation,
        role=role,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()

    # Create free trial subscription (3 months)
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.TRIALING,
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.add(subscription)

    logger.info(f"New user registered: {email}{' (admin)' if is_admin else ''}")
    return user


async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
) -> User:
    """Authenticate user with email and password."""
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthError("Invalid email or password")

    # Check if this is an OAuth-only user (no password set)
    if user.auth_provider and not user.hashed_password:
        raise AuthError(
            f"This account uses {user.auth_provider.title()} login. "
            f"Please sign in with {user.auth_provider.title()} instead."
        )

    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password")

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    logger.info(f"User authenticated: {email}")
    return user


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


class AuthError(Exception):
    """Authentication/authorization error."""
    pass
