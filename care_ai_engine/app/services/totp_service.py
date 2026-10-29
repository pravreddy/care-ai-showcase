"""
Care AI Engine - Two-Factor Authentication Service (TOTP)

NHS DSPT 2025/26 mandates MFA for systems with health data.
We use TOTP (Time-based One-Time Password) because:
  - Free (no SMS costs)
  - Works offline (carers in homes with no signal)
  - Compatible with Google Authenticator, Microsoft Authenticator, Authy
  - The code is on the carer's PERSONAL phone, not a shared tablet

Flow:
  1. User enables 2FA → gets QR code + recovery codes
  2. User scans QR in authenticator app
  3. User enters 6-digit code to confirm setup
  4. On future logins: password → MFA token → 6-digit code → real JWT
  5. If phone lost: use a one-time recovery code instead

Security:
  - TOTP secrets stored in database (encrypt at rest with LUKS)
  - Recovery codes are bcrypt-hashed (like passwords)
  - MFA tokens are short-lived (5 min) and single-use via Redis
  - Brute force on TOTP codes limited by existing rate limiter
"""

import secrets
import hashlib
import io
import base64
from typing import Optional

import pyotp
from passlib.context import CryptContext

from app.services.cache_service import get_redis
from app.core.logging import get_logger

logger = get_logger("2fa")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MFA tokens: short-lived tokens issued after password check, before TOTP verification
MFA_TOKEN_TTL_SECONDS = 300  # 5 minutes to enter the code
RECOVERY_CODE_COUNT = 10
ISSUER_NAME = "Care AI"


# ===========================================================
# TOTP Setup
# ===========================================================

def generate_totp_secret() -> str:
    """Generate a new TOTP secret for a user."""
    return pyotp.random_base32()


def get_provisioning_uri(email: str, secret: str) -> str:
    """
    Generate the otpauth:// URI for QR code scanning.
    Works with Google Authenticator, Microsoft Authenticator, Authy, etc.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=ISSUER_NAME)


def generate_qr_code_base64(uri: str) -> str:
    """
    Generate a QR code image as base64-encoded PNG.
    Returns a data URI that can be rendered directly in an <img> tag.
    
    Uses the segno library (lightweight, pure Python).
    Falls back to a URL-based QR if segno is unavailable.
    """
    try:
        import segno
        qr = segno.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=6, border=2)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except ImportError:
        # Fallback: return the URI itself (frontend can use a JS QR library)
        logger.warning("segno not installed — returning raw TOTP URI instead of QR image")
        return uri


# ===========================================================
# TOTP Verification
# ===========================================================

def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify a 6-digit TOTP code.
    
    Allows a ±1 window (30 seconds either side) to account for
    clock drift between the server and the user's phone.
    """
    if not code or not secret:
        return False

    # Clean the code (remove spaces, dashes)
    code = code.strip().replace(" ", "").replace("-", "")

    if len(code) != 6 or not code.isdigit():
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ===========================================================
# Recovery Codes
# ===========================================================

def generate_recovery_codes() -> tuple[list[str], list[str]]:
    """
    Generate one-time recovery codes for 2FA bypass.
    
    Returns:
        (plain_codes, hashed_codes)
        - plain_codes: Show to user ONCE (they save them)
        - hashed_codes: Store in database (bcrypt-hashed)
    
    Format: XXXX-XXXX (8 chars, easy to read and type)
    """
    plain_codes = []
    hashed_codes = []

    for _ in range(RECOVERY_CODE_COUNT):
        # Generate a random 8-character alphanumeric code
        code = secrets.token_hex(4).upper()  # 8 hex chars
        formatted = f"{code[:4]}-{code[4:]}"  # XXXX-XXXX format
        plain_codes.append(formatted)
        hashed_codes.append(pwd_context.hash(formatted))

    return plain_codes, hashed_codes


def verify_recovery_code(code: str, hashed_codes: list[str]) -> tuple[bool, int]:
    """
    Verify a recovery code against the stored hashed codes.
    
    Returns:
        (is_valid, index) — index of the matched code (for removal)
    """
    code = code.strip().upper()

    for i, hashed in enumerate(hashed_codes):
        if pwd_context.verify(code, hashed):
            return True, i

    return False, -1


# ===========================================================
# MFA Tokens (temporary tokens between password and TOTP)
# ===========================================================

async def create_mfa_token(user_id: str) -> str:
    """
    Create a short-lived MFA token after successful password check.
    
    This token proves the user passed Stage 1 (password) and is
    waiting for Stage 2 (TOTP code). It's stored in Redis with
    a 5-minute TTL and can only be used once.
    """
    token = secrets.token_urlsafe(32)
    redis = await get_redis()

    key = f"mfa:pending:{token}"
    await redis.setex(key, MFA_TOKEN_TTL_SECONDS, user_id)

    logger.info(f"[2FA] MFA token created for user {user_id}")
    return token


async def validate_mfa_token(token: str) -> Optional[str]:
    """
    Validate and consume an MFA token. Returns user_id if valid.
    
    The token is deleted after use (single-use).
    Returns None if invalid or expired.
    """
    redis = await get_redis()
    key = f"mfa:pending:{token}"

    user_id = await redis.get(key)
    if user_id:
        # Delete immediately — single use
        await redis.delete(key)
        return user_id.decode() if isinstance(user_id, bytes) else user_id

    return None


# ===========================================================
# 2FA Status Helper
# ===========================================================

def get_2fa_status(user) -> dict:
    """Get 2FA status for a user."""
    has_recovery = bool(user.recovery_codes_hash and len(user.recovery_codes_hash) > 0)

    return {
        "enabled": user.totp_enabled or False,
        "verified": user.totp_verified or False,
        "has_recovery_codes": has_recovery,
        "recovery_codes_remaining": len(user.recovery_codes_hash) if has_recovery else 0,
    }
