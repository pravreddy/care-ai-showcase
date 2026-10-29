"""
Care AI Engine - Partner API Key Service
Manages API keys for partners who integrate Care AI into their apps.

Partners get:
  - An API key (for authenticating requests)
  - Rate limits based on their plan
  - Usage tracking and billing

This is separate from JWT auth (which is for direct users).
API keys are for machine-to-machine integration.
"""

import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger("api_keys")

# Prefix makes keys identifiable: "cai_live_abc123..." or "cai_test_abc123..."
KEY_PREFIX_LIVE = "cai_live_"
KEY_PREFIX_TEST = "cai_test_"


def generate_api_key(test_mode: bool = False) -> tuple[str, str]:
    """
    Generate an API key and its hash.
    
    Returns:
        (plain_key, key_hash) — store the hash, show the plain key ONCE.
    """
    prefix = KEY_PREFIX_TEST if test_mode else KEY_PREFIX_LIVE
    random_part = secrets.token_urlsafe(32)
    plain_key = f"{prefix}{random_part}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, key_hash


def hash_api_key(plain_key: str) -> str:
    """Hash an API key for lookup."""
    return hashlib.sha256(plain_key.encode()).hexdigest()


def is_valid_key_format(key: str) -> bool:
    """Check if a string looks like a Care AI API key."""
    return key.startswith(KEY_PREFIX_LIVE) or key.startswith(KEY_PREFIX_TEST)


def is_test_key(key: str) -> bool:
    """Check if an API key is a test key."""
    return key.startswith(KEY_PREFIX_TEST)


# Rate limits per partner tier (requests per minute)
PARTNER_RATE_LIMITS = {
    "starter": 30,       # £80/month — small care agency
    "professional": 100,  # £200/month — medium agency
    "enterprise": 500,    # Custom — large provider
}

# Monthly request quotas
PARTNER_QUOTAS = {
    "starter": 10_000,
    "professional": 50_000,
    "enterprise": 500_000,
}
