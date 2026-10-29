"""
Care AI Engine - Auth API Routes (Hardened + 2FA)

Security features:
  1. Password strength validation on registration
  2. IP-based rate limiting (10 attempts / 15 min)
  3. Account lockout (5 failures → 1 hour)
  4. JWT blacklisting (real logout)
  5. TOTP 2FA (Google Authenticator / Microsoft Authenticator)
  6. Recovery codes (10 one-time codes for lost phones)
  7. Multi-stage login (password → MFA token → TOTP code → JWT)

Login flow:
  Without 2FA:  POST /login → { access_token, refresh_token }
  With 2FA:     POST /login → { requires_2fa: true, mfa_token }
                POST /login/verify-2fa → { access_token, refresh_token }
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    RegisterRequest, LoginRequest, LoginResponse, TokenResponse,
    RefreshRequest, UserResponse, MFAVerifyRequest,
    Setup2FAResponse, Confirm2FARequest, Confirm2FAResponse,
)
from app.services.auth_service import (
    register_user, authenticate_user, create_access_token,
    create_refresh_token, decode_token, get_user_by_id, AuthError,
)
from app.services.security_service import (
    check_ip_rate_limit, record_login_attempt,
    check_account_lockout, record_failed_login, clear_failed_logins,
    blacklist_token, is_token_blacklisted, get_security_stats,
    SecurityError,
)
from app.services.totp_service import (
    generate_totp_secret, get_provisioning_uri, generate_qr_code_base64,
    verify_totp_code, generate_recovery_codes, verify_recovery_code,
    create_mfa_token, validate_mfa_token, get_2fa_status,
)
from app.middleware.auth import get_current_user
from app.models.database import User
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For from Nginx."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ===========================================================
# Registration
# ===========================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user. Includes 3-month free trial.
    Password: min 12 chars, uppercase + lowercase + digit + special char.
    """
    ip = _get_client_ip(request)

    try:
        await check_ip_rate_limit(ip)
        await record_login_attempt(ip)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    try:
        user = await register_user(
            db=db, email=req.email, password=req.password,
            full_name=req.full_name, organisation=req.organisation, role=req.role,
        )

        access_token, expires_in = create_access_token(str(user.id), user.email)
        refresh_token = create_refresh_token(str(user.id))

        logger.info(f"[AUTH] New registration: {req.email} from {ip}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ===========================================================
# Login (Multi-Stage with 2FA)
# ===========================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stage 1: Verify email + password.
    
    If 2FA is NOT enabled → returns access_token + refresh_token directly.
    If 2FA IS enabled → returns { requires_2fa: true, mfa_token: "..." }.
    The mfa_token is valid for 5 minutes and must be sent to /login/verify-2fa.
    """
    ip = _get_client_ip(request)

    # Security checks
    try:
        await check_ip_rate_limit(ip)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    try:
        await check_account_lockout(req.email)
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))

    await record_login_attempt(ip)

    # Authenticate password
    try:
        user = await authenticate_user(db, req.email, req.password)
    except AuthError:
        await record_failed_login(req.email, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    await clear_failed_logins(req.email)

    # Check if 2FA is enabled
    if user.totp_enabled and user.totp_verified:
        # Issue temporary MFA token — user must complete Stage 2
        mfa_token = await create_mfa_token(str(user.id))

        logger.info(f"[AUTH] Login Stage 1 passed (2FA required): {req.email} from {ip}")

        return LoginResponse(
            requires_2fa=True,
            mfa_token=mfa_token,
        )

    # No 2FA — issue tokens directly
    access_token, expires_in = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    logger.info(f"[AUTH] Login success (no 2FA): {req.email} from {ip}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/login/verify-2fa", response_model=TokenResponse)
async def verify_2fa_login(
    req: MFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stage 2: Verify TOTP code (or recovery code) after password check.
    
    Requires the mfa_token from Stage 1 + the 6-digit code from the 
    authenticator app (or an 8-char recovery code with is_recovery_code=true).
    """
    ip = _get_client_ip(request)

    # Validate MFA token (single-use, 5-min TTL)
    user_id = await validate_mfa_token(req.mfa_token)
    if not user_id:
        logger.warning(f"[SECURITY] Invalid/expired MFA token from {ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA session expired. Please log in again.",
        )

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Verify the code
    if req.is_recovery_code:
        # Recovery code path
        if not user.recovery_codes_hash:
            raise HTTPException(status_code=400, detail="No recovery codes configured")

        is_valid, code_index = verify_recovery_code(req.code, user.recovery_codes_hash)
        if not is_valid:
            logger.warning(f"[SECURITY] Invalid recovery code for {user.email} from {ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid recovery code",
            )

        # Remove the used recovery code (one-time use)
        codes = list(user.recovery_codes_hash)
        codes.pop(code_index)
        user.recovery_codes_hash = codes

        remaining = len(codes)
        logger.info(f"[2FA] Recovery code used: {user.email} ({remaining} remaining)")

        if remaining <= 2:
            logger.warning(f"[2FA] Low recovery codes: {user.email} has only {remaining} left")

    else:
        # TOTP code path
        if not verify_totp_code(user.totp_secret, req.code):
            logger.warning(f"[SECURITY] Invalid TOTP code for {user.email} from {ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Check your authenticator app.",
            )

    # Success — issue real tokens
    access_token, expires_in = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    user.last_login = datetime.now(timezone.utc)

    logger.info(f"[AUTH] Login complete (2FA verified): {user.email} from {ip}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


# ===========================================================
# Logout (JWT Blacklist)
# ===========================================================

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Real logout — blacklists the access token in Redis.
    Token is immediately invalid for all subsequent requests.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        settings = get_settings()
        await blacklist_token(
            access_token,
            settings.jwt_access_token_expire_minutes * 60,
        )

    logger.info(f"[AUTH] Logout: {current_user.email}")
    return {"message": "Successfully logged out", "tokens_revoked": True}


# ===========================================================
# Refresh Token (with rotation)
# ===========================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token. Old refresh token is blacklisted (rotation).
    """
    ip = _get_client_ip(request)

    if await is_token_blacklisted(req.refresh_token):
        logger.warning(f"[SECURITY] Blacklisted refresh token used from {ip}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user = await get_user_by_id(db, payload["sub"])
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")

        access_token, expires_in = create_access_token(str(user.id), user.email)
        new_refresh = create_refresh_token(str(user.id))

        # Blacklist old refresh token (rotation)
        settings = get_settings()
        await blacklist_token(req.refresh_token, settings.jwt_refresh_token_expire_days * 86400)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=expires_in,
        )
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ===========================================================
# 2FA Setup & Management
# ===========================================================

@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start 2FA setup. Returns a QR code and secret for the authenticator app.
    
    The user must scan the QR code and then call /2fa/confirm with a valid
    code to complete the setup. Until confirmed, 2FA is NOT active.
    """
    if current_user.totp_enabled and current_user.totp_verified:
        raise HTTPException(
            status_code=400,
            detail="2FA is already enabled. Disable it first to reconfigure.",
        )

    # Generate new secret
    secret = generate_totp_secret()
    uri = get_provisioning_uri(current_user.email, secret)
    qr_code = generate_qr_code_base64(uri)

    # Store secret but DON'T enable yet (needs confirmation)
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    current_user.totp_verified = False

    logger.info(f"[2FA] Setup initiated: {current_user.email}")

    return Setup2FAResponse(
        secret=secret,
        qr_code=qr_code,
        provisioning_uri=uri,
    )


@router.post("/2fa/confirm", response_model=Confirm2FAResponse)
async def confirm_2fa(
    req: Confirm2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete 2FA setup by verifying a code from the authenticator app.
    
    This proves the user successfully scanned the QR code and their
    app is generating correct codes. Returns one-time recovery codes
    that the user MUST save.
    """
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Start 2FA setup first (POST /2fa/setup)")

    if current_user.totp_enabled and current_user.totp_verified:
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    # Verify the code
    if not verify_totp_code(current_user.totp_secret, req.code):
        raise HTTPException(
            status_code=400,
            detail="Invalid code. Make sure you scanned the QR code and the code hasn't expired.",
        )

    # Generate recovery codes
    plain_codes, hashed_codes = generate_recovery_codes()

    # Enable 2FA
    current_user.totp_enabled = True
    current_user.totp_verified = True
    current_user.recovery_codes_hash = hashed_codes

    logger.info(f"[2FA] Enabled successfully: {current_user.email}")

    return Confirm2FAResponse(
        enabled=True,
        recovery_codes=plain_codes,  # Show ONCE — user saves them
    )


@router.post("/2fa/disable")
async def disable_2fa(
    password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable 2FA. Requires password confirmation for security.
    """
    from app.services.auth_service import verify_password

    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    current_user.totp_enabled = False
    current_user.totp_verified = False
    current_user.totp_secret = None
    current_user.recovery_codes_hash = None

    logger.info(f"[2FA] Disabled: {current_user.email}")

    return {"message": "2FA has been disabled", "enabled": False}


@router.get("/2fa/status")
async def get_2fa_status_endpoint(
    current_user: User = Depends(get_current_user),
):
    """Check current 2FA status and remaining recovery codes."""
    return get_2fa_status(current_user)


@router.post("/2fa/regenerate-recovery")
async def regenerate_recovery_codes(
    password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate new recovery codes. Invalidates all previous codes.
    Requires password confirmation.
    """
    from app.services.auth_service import verify_password

    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    plain_codes, hashed_codes = generate_recovery_codes()
    current_user.recovery_codes_hash = hashed_codes

    logger.info(f"[2FA] Recovery codes regenerated: {current_user.email}")

    return {
        "recovery_codes": plain_codes,  # Show ONCE
        "count": len(plain_codes),
    }


# ===========================================================
# User Profile & Security Stats
# ===========================================================

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile (includes 2FA status)."""
    return current_user


@router.get("/security/stats")
async def security_stats(current_user: User = Depends(get_current_user)):
    """View current security metrics."""
    stats = await get_security_stats()
    stats["user_2fa"] = get_2fa_status(current_user)
    return stats
