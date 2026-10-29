"""
Care AI Engine - OAuth Routes
Google OAuth 2.0 login/registration endpoints.

Flow:
  1. Frontend links to GET /auth/google → redirects to Google consent screen
  2. Google redirects back to GET /auth/google/callback
  3. Backend validates, creates/finds user, issues JWT tokens
  4. Backend redirects to frontend /oauth/callback?token=...&refresh=...
"""

from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.oauth_service import oauth, OAuthService, OAuthError
from app.services.auth_service import create_access_token, create_refresh_token
from app.services.oauth_user_service import get_or_create_oauth_user

logger = get_logger("api.oauth")

router = APIRouter(prefix="/auth", tags=["OAuth"])

oauth_svc = OAuthService()


# ===========================================================
# Google OAuth
# ===========================================================

@router.get("/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow.
    Redirects the user to Google's consent screen.
    """
    settings = get_settings()

    if not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login is not configured",
        )

    # Create CSRF state token
    state = oauth_svc.create_state_token()

    # Store state in session for validation on callback
    request.session["oauth_state"] = state

    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    Validates the response, creates/finds user, issues JWT tokens,
    and redirects to the frontend with tokens in the URL.
    """
    settings = get_settings()

    if not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login is not configured",
        )

    # Validate state (CSRF protection)
    stored_state = request.session.pop("oauth_state", None)
    received_state = request.query_params.get("state")

    if not stored_state or not received_state:
        logger.warning("[OAUTH] Missing state parameter")
        return _redirect_error("OAuth state missing. Please try again.")

    if not oauth_svc.validate_state_token(stored_state):
        logger.warning("[OAUTH] Invalid/expired state token")
        return _redirect_error("OAuth session expired. Please try again.")

    # Exchange code for tokens and get user info
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"[OAUTH] Google token exchange failed: {e}")
        return _redirect_error("Google authentication failed. Please try again.")

    user_data = token.get("userinfo")
    if not user_data:
        # Fallback: fetch from userinfo endpoint
        try:
            user_data = await oauth.google.userinfo()
        except Exception as e:
            logger.error(f"[OAUTH] Failed to fetch Google user info: {e}")
            return _redirect_error("Could not retrieve your Google profile.")

    # Extract standardised user info
    user_info = oauth_svc.extract_user_info("google", dict(user_data))

    if not user_info.get("email"):
        logger.warning("[OAUTH] Google returned no email")
        return _redirect_error("No email address found in your Google account.")

    if not user_info.get("email_verified", False):
        logger.warning(f"[OAUTH] Unverified Google email: {user_info['email']}")
        return _redirect_error("Your Google email address is not verified.")

    # Create or find user
    try:
        user, is_new = await get_or_create_oauth_user(db, user_info)
    except OAuthError as e:
        logger.error(f"[OAUTH] User creation failed: {e}")
        return _redirect_error(str(e))

    # Issue JWT tokens
    access_token, expires_in = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    action = "registered" if is_new else "logged in"
    logger.info(f"[OAUTH] Google {action}: {user.email}")

    # Redirect to frontend with tokens
    frontend_origin = settings.origins_list[0] if settings.origins_list else ""
    callback_url = f"{frontend_origin}/oauth/callback"

    params = urlencode({
        "token": access_token,
        "refresh": refresh_token,
        "expires_in": str(expires_in),
        "new_user": "1" if is_new else "0",
    })

    return RedirectResponse(url=f"{callback_url}?{params}", status_code=302)


# ===========================================================
# OAuth status (for frontend to know what's available)
# ===========================================================

@router.get("/oauth/providers")
async def get_oauth_providers():
    """Return which OAuth providers are enabled."""
    settings = get_settings()
    return {
        "google": settings.google_oauth_enabled,
        # "microsoft": settings.microsoft_oauth_enabled,
    }


# ===========================================================
# Helpers
# ===========================================================

def _redirect_error(message: str) -> RedirectResponse:
    """Redirect to frontend login page with an error message."""
    settings = get_settings()
    frontend_origin = settings.origins_list[0] if settings.origins_list else ""
    params = urlencode({"error": message})
    return RedirectResponse(url=f"{frontend_origin}/login?{params}", status_code=302)
