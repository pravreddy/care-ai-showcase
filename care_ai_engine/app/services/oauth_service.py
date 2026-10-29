"""
Care AI Engine - OAuth Service
Handles Google and Microsoft OAuth 2.0 authentication.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import secrets

from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("oauth")

# Initialize OAuth client
oauth = OAuth()


def init_oauth():
    """Initialize OAuth providers with credentials from settings."""
    settings = get_settings()
    
    # Google OAuth
    if settings.google_oauth_enabled:
        oauth.register(
            name='google',
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile',
                'prompt': 'select_account',  # Always show account picker
            },
        )
        logger.info("Google OAuth enabled")
    
    # Microsoft OAuth
    # if settings.microsoft_oauth_enabled:
    #     tenant_id = settings.microsoft_tenant_id
    #     oauth.register(
    #         name='microsoft',
    #         client_id=settings.microsoft_client_id,
    #         client_secret=settings.microsoft_client_secret,
    #         server_metadata_url=f'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration',
    #         client_kwargs={
    #             'scope': 'openid email profile',
    #         },
    #     )
    #     logger.info("Microsoft OAuth enabled")
    
    return oauth


class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    def __init__(self):
        self.settings = get_settings()
        self.serializer = URLSafeTimedSerializer(self.settings.secret_key)
    
    def create_state_token(self, redirect_url: Optional[str] = None) -> str:
        """
        Create a secure state token for OAuth flow (CSRF protection).
        Optionally includes redirect URL for post-login redirect.
        """
        data = {
            'nonce': secrets.token_urlsafe(32),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if redirect_url:
            data['redirect_url'] = redirect_url
        
        return self.serializer.dumps(data)
    
    def validate_state_token(self, token: str, max_age: int = 600) -> Optional[Dict[str, Any]]:
        """
        Validate OAuth state token (expires after max_age seconds).
        Returns the decoded data or None if invalid/expired.
        """
        try:
            data = self.serializer.loads(token, max_age=max_age)
            return data
        except (BadSignature, SignatureExpired) as e:
            logger.warning(f"Invalid OAuth state token: {e}")
            return None
    
    def extract_user_info(self, provider: str, user_data: dict) -> Dict[str, str]:
        """
        Extract standardized user info from OAuth provider response.
        Returns: {email, full_name, provider, provider_user_id, picture_url}
        """
        if provider == 'google':
            return {
                'email': user_data.get('email', '').lower(),
                'full_name': user_data.get('name', ''),
                'provider': 'google',
                'provider_user_id': user_data.get('sub', ''),
                'picture_url': user_data.get('picture', ''),
                'email_verified': user_data.get('email_verified', False),
            }
        
        elif provider == 'microsoft':
            return {
                'email': user_data.get('email', '').lower() or user_data.get('preferred_username', '').lower(),
                'full_name': user_data.get('name', ''),
                'provider': 'microsoft',
                'provider_user_id': user_data.get('sub', '') or user_data.get('oid', ''),
                'picture_url': '',  # Microsoft doesn't provide this in standard claims
                'email_verified': True,  # Microsoft accounts are always verified
            }
        
        else:
            raise ValueError(f"Unknown OAuth provider: {provider}")
    
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if an OAuth provider is configured and enabled."""
        if provider == 'google':
            return self.settings.google_oauth_enabled
        elif provider == 'microsoft':
            return self.settings.microsoft_oauth_enabled
        return False


class OAuthError(Exception):
    """OAuth-related errors."""
    pass
