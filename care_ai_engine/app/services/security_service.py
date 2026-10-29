"""
Care AI Engine - Security Service
FastAPI equivalent of django-axes + password validators + JWT blacklist.

All state stored in Redis — no additional database tables needed.

Features:
  1. Password strength validation (complexity rules)
  2. Login rate limiting by IP (brute force protection)
  3. Account lockout by email (failed attempt tracking)
  4. JWT token blacklist (real logout)
  5. Security event logging (audit trail)

Redis key patterns:
  security:login_attempts:{ip}     → count (TTL: 15 min)
  security:lockout:{email}         → count (TTL: 1 hour)
  security:blacklist:{jti}         → "1" (TTL: token's remaining lifetime)
"""

import hashlib
import re
import time
from datetime import datetime, timezone
from typing import Optional

from app.services.cache_service import get_redis
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("security")


# ===========================================================
# Configuration
# ===========================================================

# Rate limiting
MAX_LOGIN_ATTEMPTS_PER_IP = 10       # per window
LOGIN_RATE_WINDOW_SECONDS = 900      # 15 minutes

# Account lockout
MAX_FAILED_LOGINS_PER_ACCOUNT = 5    # before lockout
LOCKOUT_DURATION_SECONDS = 3600      # 1 hour

# Password rules
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128

# Common passwords (top 100 — catches the most frequent ones)
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "password12",
    "batman", "welcome", "charlie", "donald", "admin", "login", "hello",
    "princess", "1234", "12345", "123456789", "1234567890", "password1234",
    "qwerty123", "111111", "000000", "access", "flower", "hottie", "loveme",
    "zaq1zaq1", "starwars", "whatever", "trustme", "cheese", "pepper",
    "computer", "internet", "samsung", "google", "facebook", "liverpool",
    "arsenal", "chelsea", "manchester", "careai", "carer", "nursing",
}


# ===========================================================
# 1. Password Strength Validation
# ===========================================================

class PasswordValidationError(Exception):
    """Raised when password doesn't meet security requirements."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_password_strength(password: str, email: str = "", full_name: str = "") -> None:
    """
    Validate password meets security requirements.
    
    Rules:
      - Minimum 12 characters
      - Maximum 128 characters  
      - At least 1 uppercase letter
      - At least 1 lowercase letter
      - At least 1 digit
      - At least 1 special character
      - Not a common password
      - Not similar to email or name
    
    Raises PasswordValidationError with list of all failures.
    """
    errors = []

    # Length checks
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters (got {len(password)})")
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be at most {MAX_PASSWORD_LENGTH} characters")

    # Complexity checks
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        errors.append("Password must contain at least one special character (!@#$%^&*...)")

    # Common password check
    if password.lower() in COMMON_PASSWORDS:
        errors.append("This password is too common — please choose something unique")

    # Similarity to personal info
    password_lower = password.lower()
    if email:
        email_local = email.split("@")[0].lower()
        if len(email_local) >= 4 and email_local in password_lower:
            errors.append("Password must not contain your email address")
    if full_name:
        for name_part in full_name.lower().split():
            if len(name_part) >= 3 and name_part in password_lower:
                errors.append("Password must not contain your name")
                break

    # Repeated characters
    if re.search(r"(.)\1{3,}", password):
        errors.append("Password must not contain 4+ repeated characters (e.g. 'aaaa')")

    if errors:
        raise PasswordValidationError(errors)


# ===========================================================
# 2. Login Rate Limiting (by IP address)
# ===========================================================

async def check_ip_rate_limit(ip_address: str) -> None:
    """
    Check if an IP has exceeded the login attempt limit.
    
    Raises SecurityError if rate limited.
    Uses a sliding window counter in Redis.
    """
    redis = await get_redis()
    key = f"security:login_attempts:{ip_address}"

    try:
        attempts = await redis.get(key)
        current = int(attempts) if attempts else 0

        if current >= MAX_LOGIN_ATTEMPTS_PER_IP:
            ttl = await redis.ttl(key)
            logger.warning(
                f"[SECURITY] IP rate limited: {ip_address} ({current} attempts)",
                extra={"ip": ip_address, "attempts": current},
            )
            raise SecurityError(
                f"Too many login attempts. Please try again in {max(ttl // 60, 1)} minutes."
            )
    except SecurityError:
        raise
    except Exception as e:
        # Redis down — fail open (don't block legitimate users)
        logger.error(f"Rate limit check failed: {e}")


async def record_login_attempt(ip_address: str) -> None:
    """Record a login attempt from an IP (whether success or failure)."""
    redis = await get_redis()
    key = f"security:login_attempts:{ip_address}"

    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_RATE_WINDOW_SECONDS)
        await pipe.execute()
    except Exception as e:
        logger.error(f"Failed to record login attempt: {e}")


# ===========================================================
# 3. Account Lockout (by email)
# ===========================================================

async def check_account_lockout(email: str) -> None:
    """
    Check if an account is locked due to failed login attempts.
    
    Raises SecurityError if the account is locked.
    """
    redis = await get_redis()
    key = f"security:lockout:{email.lower()}"

    try:
        attempts = await redis.get(key)
        current = int(attempts) if attempts else 0

        if current >= MAX_FAILED_LOGINS_PER_ACCOUNT:
            ttl = await redis.ttl(key)
            minutes_remaining = max(ttl // 60, 1)
            logger.warning(
                f"[SECURITY] Account locked: {email} ({current} failed attempts)",
                extra={"email": email, "attempts": current},
            )
            raise SecurityError(
                f"Account temporarily locked due to too many failed attempts. "
                f"Try again in {minutes_remaining} minutes."
            )
    except SecurityError:
        raise
    except Exception as e:
        logger.error(f"Lockout check failed: {e}")


async def record_failed_login(email: str, ip_address: str) -> None:
    """Record a failed login attempt against an account."""
    redis = await get_redis()
    key = f"security:lockout:{email.lower()}"

    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOCKOUT_DURATION_SECONDS)
        await pipe.execute()

        # Get current count for logging
        count = await redis.get(key)
        remaining = MAX_FAILED_LOGINS_PER_ACCOUNT - int(count or 0)

        logger.warning(
            f"[SECURITY] Failed login: {email} from {ip_address} "
            f"({remaining} attempts remaining before lockout)",
            extra={"email": email, "ip": ip_address, "remaining": remaining},
        )
    except Exception as e:
        logger.error(f"Failed to record failed login: {e}")


async def clear_failed_logins(email: str) -> None:
    """Clear failed login counter on successful authentication."""
    redis = await get_redis()
    key = f"security:lockout:{email.lower()}"

    try:
        await redis.delete(key)
    except Exception as e:
        logger.error(f"Failed to clear lockout: {e}")


# ===========================================================
# 4. JWT Token Blacklist (Real Logout)
# ===========================================================

def _token_fingerprint(token: str) -> str:
    """Create a short hash of a token for the blacklist key."""
    return hashlib.sha256(token.encode()).hexdigest()[:32]


async def blacklist_token(token: str, expires_in_seconds: int) -> None:
    """
    Add a JWT token to the blacklist.
    
    The blacklist entry auto-expires when the token would have expired anyway,
    so Redis doesn't accumulate dead entries.
    """
    redis = await get_redis()
    key = f"security:blacklist:{_token_fingerprint(token)}"

    try:
        await redis.setex(key, expires_in_seconds, "1")
        logger.info("[SECURITY] Token blacklisted")
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token has been revoked."""
    redis = await get_redis()
    key = f"security:blacklist:{_token_fingerprint(token)}"

    try:
        result = await redis.get(key)
        return result is not None
    except Exception:
        # Redis down — fail open (token still valid)
        return False


# ===========================================================
# 5. Security Stats (for admin dashboard)
# ===========================================================

async def get_security_stats() -> dict:
    """Get current security metrics."""
    redis = await get_redis()

    try:
        # Count active lockouts
        lockout_keys = []
        async for key in redis.scan_iter("security:lockout:*"):
            lockout_keys.append(key)

        # Count active rate limits
        rate_keys = []
        async for key in redis.scan_iter("security:login_attempts:*"):
            rate_keys.append(key)

        # Count blacklisted tokens
        blacklist_keys = []
        async for key in redis.scan_iter("security:blacklist:*"):
            blacklist_keys.append(key)

        return {
            "active_account_lockouts": len(lockout_keys),
            "active_ip_rate_limits": len(rate_keys),
            "blacklisted_tokens": len(blacklist_keys),
            "config": {
                "max_login_attempts_per_ip": MAX_LOGIN_ATTEMPTS_PER_IP,
                "rate_limit_window_minutes": LOGIN_RATE_WINDOW_SECONDS // 60,
                "max_failed_logins_per_account": MAX_FAILED_LOGINS_PER_ACCOUNT,
                "lockout_duration_minutes": LOCKOUT_DURATION_SECONDS // 60,
                "min_password_length": MIN_PASSWORD_LENGTH,
            },
        }
    except Exception as e:
        return {"error": str(e)}


class SecurityError(Exception):
    """Raised on security violations (rate limit, lockout, etc.)."""
    pass
