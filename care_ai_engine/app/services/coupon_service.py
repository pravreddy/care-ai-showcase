"""
Care AI Engine - Coupon Service

Handles coupon creation, validation, and redemption.
Coupons grant free access to specific tiers for a duration (or forever).

Usage flow:
  1. Admin creates coupon: POST /api/v1/coupons
  2. Share code with care agency: "Use code CAREFREE2026 for free PRO access"
  3. User redeems at registration or later: POST /api/v1/coupons/redeem
  4. System upgrades their subscription automatically
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    Coupon, CouponRedemption, Subscription, User,
    SubscriptionTier, SubscriptionStatus,
)
from app.core.logging import get_logger

logger = get_logger("coupon")


class CouponError(Exception):
    pass


async def create_coupon(
        db: AsyncSession,
        code: str,
        tier_granted: str = "pro",
        duration_days: Optional[int] = None,
        max_uses: Optional[int] = None,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
) -> Coupon:
    """Create a new coupon code (admin only)."""

    # Check code doesn't already exist
    existing = await db.execute(
        select(Coupon).where(func.upper(Coupon.code) == code.upper())
    )
    if existing.scalar_one_or_none():
        raise CouponError(f"Coupon code '{code}' already exists")

    # Validate tier
    try:
        tier = SubscriptionTier(tier_granted.lower())
    except ValueError:
        raise CouponError(f"Invalid tier: {tier_granted}. Use: free, pro, agency, enterprise")

    coupon = Coupon(
        code=code.upper(),
        description=description,
        tier_granted=tier,
        duration_days=duration_days,
        max_uses=max_uses,
        expires_at=expires_at,
        created_by=created_by,
    )
    db.add(coupon)
    await db.flush()

    logger.info(
        f"[COUPON] Created: {code} → {tier_granted} tier, "
        f"duration={'forever' if not duration_days else f'{duration_days}d'}, "
        f"max_uses={'unlimited' if not max_uses else max_uses}"
    )

    return coupon


async def validate_coupon(db: AsyncSession, code: str) -> Coupon:
    """Check if a coupon code is valid. Raises CouponError if not."""

    result = await db.execute(
        select(Coupon).where(func.upper(Coupon.code) == code.upper())
    )
    coupon = result.scalar_one_or_none()

    if not coupon:
        raise CouponError("Invalid coupon code")

    if not coupon.is_active:
        raise CouponError("This coupon has been deactivated")

    if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
        raise CouponError("This coupon has expired")

    if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
        raise CouponError("This coupon has reached its maximum number of uses")

    return coupon


async def redeem_coupon(
        db: AsyncSession,
        user: User,
        code: str,
) -> dict:
    """
    Redeem a coupon for a user. Upgrades their subscription.

    Returns dict with tier_granted and valid_until.
    """

    # Validate the coupon
    coupon = await validate_coupon(db, code)

    # Check user hasn't already redeemed this coupon
    existing = await db.execute(
        select(CouponRedemption).where(
            CouponRedemption.user_id == user.id,
            CouponRedemption.coupon_id == coupon.id,
            )
    )
    if existing.scalar_one_or_none():
        raise CouponError("You have already redeemed this coupon")

    # Calculate validity period
    valid_until = None
    if coupon.duration_days:
        valid_until = datetime.now(timezone.utc) + timedelta(days=coupon.duration_days)

    # Create redemption record
    redemption = CouponRedemption(
        coupon_id=coupon.id,
        user_id=user.id,
        granted_tier=coupon.tier_granted.value,
        granted_until=valid_until,
    )
    db.add(redemption)

    # Increment coupon usage
    coupon.current_uses = (coupon.current_uses or 0) + 1

    # Update or create subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.tier = coupon.tier_granted
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = datetime.now(timezone.utc)
        subscription.current_period_end = valid_until
    else:
        subscription = Subscription(
            user_id=user.id,
            tier=coupon.tier_granted,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=valid_until,
        )
        db.add(subscription)

    # Store coupon code on user for reference
    user.coupon_code = coupon.code

    await db.flush()

    tier_name = coupon.tier_granted.value.upper()
    duration = "forever" if not valid_until else f"until {valid_until.strftime('%d %B %Y')}"

    logger.info(f"[COUPON] Redeemed: {user.email} used {coupon.code} → {tier_name} {duration}")

    return {
        "tier_granted": coupon.tier_granted.value,
        "valid_until": valid_until,
        "message": f"Coupon applied! You now have {tier_name} access {duration}.",
    }


async def list_coupons(db: AsyncSession) -> list[Coupon]:
    """List all coupons (admin only)."""
    result = await db.execute(
        select(Coupon).order_by(Coupon.created_at.desc())
    )
    return list(result.scalars().all())


async def deactivate_coupon(db: AsyncSession, code: str) -> Coupon:
    """Deactivate a coupon (admin only)."""
    result = await db.execute(
        select(Coupon).where(func.upper(Coupon.code) == code.upper())
    )
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise CouponError("Coupon not found")

    coupon.is_active = False
    await db.flush()

    logger.info(f"[COUPON] Deactivated: {code}")
    return coupon
