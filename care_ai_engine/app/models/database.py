"""
Care AI Engine - Database Models
SQLAlchemy async models for users, subscriptions, usage tracking, and coupons.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum, Index, BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# --- Enums ---

class SubscriptionTier(str, PyEnum):
    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, PyEnum):
    ACTIVE = "active"
    TRIALING = "trialing"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"


# --- Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=False)
    organisation = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)

    # --- OAuth ---
    auth_provider = Column(String(50), nullable=True)       # 'google', 'microsoft', or None (email)
    provider_user_id = Column(String(255), nullable=True)    # Provider's unique user ID
    picture_url = Column(String(1000), nullable=True)        # Profile picture from OAuth

    # --- 2FA (TOTP) ---
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    totp_verified = Column(Boolean, default=False)
    recovery_codes_hash = Column(JSON, nullable=True)

    # --- Coupon ---
    coupon_code = Column(String(50), nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_records = relationship("UsageRecord", back_populates="user")
    voice_notes = relationship("VoiceNote", back_populates="user")
    partner_accounts = relationship("PartnerAccount", back_populates="user")
    coupon_redemptions = relationship("CouponRedemption", back_populates="user")

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_provider_lookup", "auth_provider", "provider_user_id", unique=True),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIALING)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscription")


class UsageRecord(Base):
    """Daily usage tracking per user for rate limiting and billing."""
    __tablename__ = "usage_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    ai_queries = Column(Integer, default=0)
    voice_notes_count = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0.0)
    processing_seconds = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)

    user = relationship("User", back_populates="usage_records")

    __table_args__ = (
        Index("ix_usage_user_date", "user_id", "date", unique=True),
    )


class VoiceNote(Base):
    """Voice, video, and text note records with AI-generated clinical notes."""
    __tablename__ = "voice_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    input_type = Column(String(20), default="audio")
    duration_seconds = Column(Float, nullable=True)
    transcript = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    clinical_note_data = Column(JSON, nullable=True)
    client_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="voice_notes")

    __table_args__ = (
        Index("ix_voice_notes_user_created", "user_id", "created_at"),
    )


class PartnerAccount(Base):
    """Partner companies that integrate Care AI via API."""
    __tablename__ = "partner_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_name = Column(String(255), nullable=False)
    tier = Column(String(50), default="starter")
    is_active = Column(Boolean, default=True)
    monthly_quota = Column(Integer, default=10000)
    requests_this_month = Column(Integer, default=0)
    quota_reset_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="partner_accounts")
    api_keys = relationship("APIKey", back_populates="partner")


class APIKey(Base):
    """API keys for partner integrations."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partner_accounts.id"), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_test = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    total_requests = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    partner = relationship("PartnerAccount", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_partner_created", "partner_id", "created_at"),
    )


# --- Coupon System ---

class Coupon(Base):
    """
    Promotional coupon codes for free or discounted access.

    Usage:
      - Admin creates coupon with a code (e.g. "CAREFREE2026")
      - Give code to care agencies / demo users
      - They enter code at registration or in settings
      - Gets them free PRO access for the specified duration (or forever)
    """
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)

    # What the coupon grants
    tier_granted = Column(
        Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.PRO
    )
    duration_days = Column(Integer, nullable=True)  # null = forever

    # Limits
    max_uses = Column(Integer, nullable=True)  # null = unlimited
    current_uses = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Coupon code expiry

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    redemptions = relationship("CouponRedemption", back_populates="coupon")


class CouponRedemption(Base):
    """Tracks which users have redeemed which coupons."""
    __tablename__ = "coupon_redemptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    redeemed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    granted_tier = Column(String(50), nullable=False)
    granted_until = Column(DateTime(timezone=True), nullable=True)  # null = forever

    coupon = relationship("Coupon", back_populates="redemptions")
    user = relationship("User", back_populates="coupon_redemptions")

    __table_args__ = (
        Index("ix_redemption_user_coupon", "user_id", "coupon_id", unique=True),
    )


class MedicalKnowledgeLog(Base):
    """Track what medical data has been ingested and when."""
    __tablename__ = "medical_knowledge_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    item_name = Column(String(500), nullable=False)
    item_url = Column(String(1000), nullable=True)
    content_hash = Column(String(64), nullable=False)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)
    character_count = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_knowledge_source_name", "source", "item_name", unique=True),
    )
