"""
Care AI Engine - Partner API Routes
Manage partner accounts and API keys for third-party integrations.

Endpoints:
  POST /partner/register     → Register as a partner
  POST /partner/keys         → Create a new API key
  GET  /partner/keys         → List your API keys
  DELETE /partner/keys/{id}  → Revoke an API key
  GET  /partner/usage        → View usage statistics
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.database import User, PartnerAccount, APIKey
from app.services.api_key_service import (
    generate_api_key, PARTNER_RATE_LIMITS, PARTNER_QUOTAS,
)
from app.core.logging import get_logger

logger = get_logger("api.partner")

router = APIRouter(prefix="/partner", tags=["Partner API"])


# --- Request/Response models ---

class PartnerRegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    tier: str = Field(default="starter", pattern="^(starter|professional|enterprise)$")


class PartnerResponse(BaseModel):
    id: UUID
    company_name: str
    tier: str
    is_active: bool
    monthly_quota: int
    requests_this_month: int
    rate_limit_per_minute: int
    created_at: datetime


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Label for this key, e.g. 'Production'")
    test_mode: bool = False


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str  # Show first few chars only
    is_active: bool
    is_test: bool
    total_requests: int
    last_used_at: Optional[datetime] = None
    created_at: datetime


class APIKeyCreatedResponse(BaseModel):
    """Only returned once — when the key is first created."""
    id: UUID
    name: str
    api_key: str  # ← Full key, shown ONCE. User must save it.
    is_test: bool
    warning: str = "Save this key now. You won't be able to see it again."


class UsageResponse(BaseModel):
    company_name: str
    tier: str
    monthly_quota: int
    requests_this_month: int
    requests_remaining: int
    rate_limit_per_minute: int
    keys_active: int
    keys_total: int


# --- Endpoints ---

@router.post("/register", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def register_partner(
    req: PartnerRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register as a partner to get API access.
    One partner account per user. Choose your tier for rate limits and quotas.
    """
    # Check if user already has a partner account
    existing = await db.execute(
        select(PartnerAccount).where(PartnerAccount.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a partner account.",
        )

    partner = PartnerAccount(
        user_id=current_user.id,
        company_name=req.company_name,
        tier=req.tier,
        monthly_quota=PARTNER_QUOTAS.get(req.tier, 10000),
        quota_reset_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(partner)
    await db.flush()

    logger.info(f"Partner registered: {req.company_name} ({req.tier})")

    return PartnerResponse(
        id=partner.id,
        company_name=partner.company_name,
        tier=partner.tier,
        is_active=partner.is_active,
        monthly_quota=partner.monthly_quota,
        requests_this_month=0,
        rate_limit_per_minute=PARTNER_RATE_LIMITS.get(req.tier, 30),
        created_at=partner.created_at,
    )


@router.post("/keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key. The full key is returned ONCE — save it immediately.
    
    Test keys (test_mode=true) don't count against your quota and return mock data.
    """
    partner = await _get_partner_or_404(current_user.id, db)

    # Limit keys per partner
    key_count = await db.execute(
        select(APIKey).where(APIKey.partner_id == partner.id)
    )
    if len(key_count.all()) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 API keys per partner account.",
        )

    # Generate the key
    plain_key, key_hash = generate_api_key(test_mode=req.test_mode)

    api_key = APIKey(
        partner_id=partner.id,
        key_hash=key_hash,
        key_prefix=plain_key[:16] + "...",  # Store prefix for display
        name=req.name,
        is_test=req.test_mode,
    )
    db.add(api_key)
    await db.flush()

    logger.info(f"API key created: {req.name} ({'test' if req.test_mode else 'live'}) for {partner.company_name}")

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=plain_key,  # Full key — shown only once
        is_test=req.test_mode,
    )


@router.get("/keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for your partner account. Key values are masked."""
    partner = await _get_partner_or_404(current_user.id, db)

    result = await db.execute(
        select(APIKey)
        .where(APIKey.partner_id == partner.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            is_test=k.is_test,
            total_requests=k.total_requests,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (deactivate) an API key. It will immediately stop working."""
    partner = await _get_partner_or_404(current_user.id, db)

    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.partner_id == partner.id,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False

    logger.info(f"API key revoked: {key.name} for {partner.company_name}")

    return {"message": f"API key '{key.name}' has been revoked.", "key_id": str(key_id)}


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View your current usage, quota, and rate limits."""
    partner = await _get_partner_or_404(current_user.id, db)

    # Count keys
    result = await db.execute(
        select(APIKey).where(APIKey.partner_id == partner.id)
    )
    all_keys = result.scalars().all()
    active_keys = sum(1 for k in all_keys if k.is_active)

    return UsageResponse(
        company_name=partner.company_name,
        tier=partner.tier,
        monthly_quota=partner.monthly_quota,
        requests_this_month=partner.requests_this_month,
        requests_remaining=max(0, partner.monthly_quota - partner.requests_this_month),
        rate_limit_per_minute=PARTNER_RATE_LIMITS.get(partner.tier, 30),
        keys_active=active_keys,
        keys_total=len(all_keys),
    )


# --- Helpers ---

async def _get_partner_or_404(user_id, db: AsyncSession) -> PartnerAccount:
    """Get the partner account for a user, or raise 404."""
    result = await db.execute(
        select(PartnerAccount).where(PartnerAccount.user_id == user_id)
    )
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(
            status_code=404,
            detail="No partner account found. Register at POST /api/v1/partner/register first.",
        )
    return partner
