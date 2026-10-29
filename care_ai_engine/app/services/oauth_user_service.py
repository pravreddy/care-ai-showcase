"""
Care AI Engine - OAuth User Service
Handles creating and linking OAuth users to the database.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.database import User, Subscription, SubscriptionTier, SubscriptionStatus
from app.services.oauth_service import OAuthError

logger = get_logger("oauth_user")


async def get_or_create_oauth_user(
    db: AsyncSession,
    user_info: Dict[str, str],
) -> Tuple[User, bool]:
    """
    Find an existing user or create a new one from OAuth data.

    Logic:
      1. Check if a user with this provider + provider_user_id exists → log them in
      2. Check if a user with this email exists (registered via email/password) → link the OAuth account
      3. Otherwise → create a brand new user

    Returns: (user, is_new_user)
    """
    provider = user_info["provider"]
    provider_user_id = user_info["provider_user_id"]
    email = user_info["email"].lower()
    full_name = user_info.get("full_name", "")
    picture_url = user_info.get("picture_url", "")

    # --- Case 1: Existing OAuth user (same provider + ID) ---
    result = await db.execute(
        select(User).where(
            User.auth_provider == provider,
            User.provider_user_id == provider_user_id,
        )
    )
    existing_oauth = result.scalar_one_or_none()

    if existing_oauth:
        # Update profile picture if changed
        if picture_url and existing_oauth.picture_url != picture_url:
            existing_oauth.picture_url = picture_url
        if not existing_oauth.is_active:
            raise OAuthError("Your account has been deactivated. Please contact support.")
        logger.info(f"[OAUTH] Existing OAuth user login: {email}")
        return existing_oauth, False

    # --- Case 2: Email already registered (link OAuth to existing account) ---
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_email = result.scalar_one_or_none()

    if existing_email:
        if not existing_email.is_active:
            raise OAuthError("Your account has been deactivated. Please contact support.")

        # Link OAuth provider to existing account
        existing_email.auth_provider = provider
        existing_email.provider_user_id = provider_user_id
        existing_email.is_verified = True  # OAuth email is verified by Google

        if picture_url and not existing_email.picture_url:
            existing_email.picture_url = picture_url

        logger.info(f"[OAUTH] Linked {provider} to existing account: {email}")
        return existing_email, False

    # --- Case 3: Brand new user ---
    settings = get_settings()
    is_admin = email in settings.admin_email_list

    user = User(
        email=email,
        hashed_password=None,  # No password for OAuth users
        full_name=full_name or email.split("@")[0],
        auth_provider=provider,
        provider_user_id=provider_user_id,
        picture_url=picture_url,
        is_active=True,
        is_verified=True,  # OAuth emails are pre-verified
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()

    # Create free trial subscription (3 months, same as email registration)
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.TRIALING,
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.add(subscription)

    logger.info(f"[OAUTH] New {provider} user registered: {email}{' (admin)' if is_admin else ''}")
    return user, True
