"""
Care AI Engine - API Schemas
Pydantic models for request validation and response serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=12,
        max_length=72,
        description="Minimum 12 chars, must include uppercase, lowercase, digit, and special character",
    )
    full_name: str = Field(..., min_length=2, max_length=255)
    organisation: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login can return tokens directly OR require 2FA."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    requires_2fa: bool = False
    mfa_token: Optional[str] = None  # Temporary token for 2FA stage


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MFAVerifyRequest(BaseModel):
    """Stage 2 of login: verify TOTP code or recovery code."""
    mfa_token: str
    code: str = Field(..., min_length=6, max_length=12)
    is_recovery_code: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User ---

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    organisation: Optional[str]
    role: Optional[str]
    is_active: bool
    is_verified: bool
    totp_enabled: bool = False
    auth_provider: Optional[str] = None       # 'google', 'microsoft', or None
    picture_url: Optional[str] = None         # Profile picture from OAuth
    created_at: datetime
    subscription_tier: Optional[str] = None

    model_config = {"from_attributes": True}


class Setup2FAResponse(BaseModel):
    """Response when user initiates 2FA setup."""
    secret: str           # Show for manual entry
    qr_code: str          # Base64 PNG or otpauth:// URI
    provisioning_uri: str  # The otpauth:// URI


class Confirm2FARequest(BaseModel):
    """User enters code from authenticator to complete setup."""
    code: str = Field(..., min_length=6, max_length=6)


class Confirm2FAResponse(BaseModel):
    """Response after successful 2FA setup confirmation."""
    enabled: bool = True
    recovery_codes: list[str]  # Show ONCE — user must save them


# --- Medical Agent ---

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    include_sources: bool = True
    max_results: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    confidence: Optional[str] = None  # "high", "medium", "low"
    model_used: str
    processing_time_ms: float
    disclaimer: str = (
        "This information is based on NHS and UK medical sources. "
        "Always consult a qualified healthcare professional for medical advice."
    )


# --- Voice Notes ---

class VoiceNoteResponse(BaseModel):
    id: UUID
    filename: str
    transcript: Optional[str]
    ai_summary: Optional[str]
    duration_seconds: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: float
    processing_time_ms: float


# --- Usage & Subscription ---

class UsageResponse(BaseModel):
    date: str
    ai_queries: int
    voice_notes_count: int
    storage_used_mb: float
    limits: dict


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    trial_ends_at: Optional[datetime]
    current_period_end: Optional[datetime]


# --- Knowledge Base ---

class KnowledgeStatsResponse(BaseModel):
    total_documents: int
    sources: dict[str, int]
    last_updated: Optional[datetime]


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]
    uptime_seconds: float


# --- Coupons ---

class CreateCouponRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Z0-9_-]+$",
                      description="Coupon code (uppercase, no spaces). e.g. CAREFREE2026")
    description: Optional[str] = None
    tier_granted: str = Field(default="pro", description="Tier: free, pro, agency, enterprise")
    duration_days: Optional[int] = Field(default=None, ge=1,
                                         description="Days of access. null = forever")
    max_uses: Optional[int] = Field(default=None, ge=1,
                                    description="Max redemptions. null = unlimited")
    expires_at: Optional[datetime] = Field(default=None,
                                           description="When the coupon code itself expires")


class CouponResponse(BaseModel):
    id: UUID
    code: str
    description: Optional[str]
    tier_granted: str
    duration_days: Optional[int]
    max_uses: Optional[int]
    current_uses: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class RedeemCouponRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)


class RedeemCouponResponse(BaseModel):
    message: str
    tier_granted: str
    valid_until: Optional[datetime] = None  # null = forever
