"""
Care AI Engine - Coupon API Routes

Admin endpoints (requires is_admin=True):
  POST   /api/v1/coupons              Create a coupon
  GET    /api/v1/coupons              List all coupons
  DELETE /api/v1/coupons/{code}       Deactivate a coupon

User endpoints (any authenticated user):
  GET    /api/v1/coupons/check/{code}  Check if a coupon is valid
  POST   /api/v1/coupons/redeem        Apply a coupon to your account
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.database import User
from app.models.schemas import (
    CreateCouponRequest, CouponResponse,
    RedeemCouponRequest, RedeemCouponResponse,
)
from app.services.coupon_service import (
    create_coupon, validate_coupon, redeem_coupon,
    list_coupons, deactivate_coupon, CouponError,
)
from app.core.logging import get_logger

logger = get_logger("api.coupons")

router = APIRouter(prefix="/coupons", tags=["Coupons"])


def _require_admin(user: User):
    """Raise 403 if user is not admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


# ===========================================================
# Admin Endpoints
# ===========================================================

@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon_endpoint(
        req: CreateCouponRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    Create a new coupon code. Admin only.

    Example:
      code: "CAREFREE2026"
      tier_granted: "pro"
      duration_days: null (forever)
      max_uses: 50
    """
    _require_admin(current_user)

    try:
        coupon = await create_coupon(
            db=db,
            code=req.code,
            tier_granted=req.tier_granted,
            duration_days=req.duration_days,
            max_uses=req.max_uses,
            description=req.description,
            expires_at=req.expires_at,
            created_by=str(current_user.id),
        )
        return coupon
    except CouponError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[CouponResponse])
async def list_coupons_endpoint(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """List all coupons with usage stats. Admin only."""
    _require_admin(current_user)
    return await list_coupons(db)


@router.delete("/{code}")
async def deactivate_coupon_endpoint(
        code: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Deactivate a coupon so it can no longer be redeemed. Admin only."""
    _require_admin(current_user)

    try:
        coupon = await deactivate_coupon(db, code)
        return {"message": f"Coupon {coupon.code} deactivated", "is_active": False}
    except CouponError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===========================================================
# User Endpoints
# ===========================================================

@router.get("/check/{code}")
async def check_coupon_endpoint(
        code: str,
        db: AsyncSession = Depends(get_db),
):
    """
    Check if a coupon code is valid (no auth required).
    Returns coupon details if valid, 400 if not.
    """
    try:
        coupon = await validate_coupon(db, code)
        return {
            "valid": True,
            "tier_granted": coupon.tier_granted.value,
            "duration_days": coupon.duration_days,
            "description": coupon.description,
        }
    except CouponError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/redeem", response_model=RedeemCouponResponse)
async def redeem_coupon_endpoint(
        req: RedeemCouponRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    Redeem a coupon code. Upgrades your subscription to the coupon's tier.

    Example:
      { "code": "CAREFREE2026" }
    """
    try:
        result = await redeem_coupon(db, current_user, req.code)
        return RedeemCouponResponse(**result)
    except CouponError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
