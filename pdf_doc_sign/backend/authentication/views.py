"""
Auth Views - SignSimple UK
Email/password + OAuth (Google, GitHub, Microsoft, LinkedIn, Facebook)
With account activation and email verification
"""
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, ChangePasswordSerializer,
)

import logging
import requests as http_requests

logger = logging.getLogger('authentication')


# ============================================================
# Forgot Password
# ============================================================

class ForgotPasswordView(APIView):
    """Request a password reset link. Works for email/password users."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required'}, status=400)

        # Always return success to prevent email enumeration
        success_msg = 'If an account with that email exists, a password reset link has been sent.'

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': success_msg})

        # Don't send reset for OAuth-only users
        if user.is_oauth_user and not user.has_usable_password():
            return Response({
                'message': success_msg,
                'hint': f'This account uses {user.auth_provider} sign-in. Try signing in with {user.auth_provider} instead.',
            })

        # Generate token and send email
        try:
            user.send_password_setup_email()
            logger.info(f'[AUTH] Password reset requested for {email}')
        except Exception as e:
            logger.error(f'[AUTH] Failed to send password reset email to {email}: {e}')

        return Response({'message': success_msg})

OAUTH_PROVIDERS = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
        'scope': 'openid email profile',
        'client_id_env': 'GOOGLE_CLIENT_ID',
        'client_secret_env': 'GOOGLE_CLIENT_SECRET',
    },
    'github': {
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'emails_url': 'https://api.github.com/user/emails',
        'scope': 'user:email',
        'client_id_env': 'GITHUB_CLIENT_ID',
        'client_secret_env': 'GITHUB_CLIENT_SECRET',
    },
    'microsoft': {
        'authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
        'scope': 'openid email profile',
        'client_id_env': 'MICROSOFT_CLIENT_ID',
        'client_secret_env': 'MICROSOFT_CLIENT_SECRET',
    },
    'linkedin': {
        'authorize_url': 'https://www.linkedin.com/oauth/v2/authorization',
        'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
        'userinfo_url': 'https://api.linkedin.com/v2/userinfo',
        'scope': 'openid profile email',
        'client_id_env': 'LINKEDIN_CLIENT_ID',
        'client_secret_env': 'LINKEDIN_CLIENT_SECRET',
    },
    'facebook': {
        'authorize_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'userinfo_url': 'https://graph.facebook.com/me?fields=id,name,email,picture',
        'scope': 'email public_profile',
        'client_id_env': 'FACEBOOK_CLIENT_ID',
        'client_secret_env': 'FACEBOOK_CLIENT_SECRET',
    },
}


def _get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


def _get_oauth_credentials(provider):
    import os
    config = OAUTH_PROVIDERS.get(provider)
    if not config:
        return None, None
    client_id = os.environ.get(config['client_id_env'], '')
    client_secret = os.environ.get(config['client_secret_env'], '')
    return client_id, client_secret


def _redirect_error(message):
    frontend_url = settings.OAUTH_FRONTEND_CALLBACK_URL.replace('/oauth/callback', '/login')
    return redirect(f"{frontend_url}?{urlencode({'error': message})}")


def _redirect_success(user, is_new=False):
    tokens = _get_tokens_for_user(user)
    params = urlencode({
        'token': tokens['access'],
        'refresh': tokens['refresh'],
        'new_user': '1' if is_new else '0',
    })
    return redirect(f"{settings.OAUTH_FRONTEND_CALLBACK_URL}?{params}")


def _send_welcome_email(user, auth_method='email'):
    """Send welcome email to newly registered users."""
    try:
        name = user.full_name.split()[0] if user.full_name else user.email.split('@')[0]
        
        subject = 'Welcome to SignSimple! 🎉'
        
        message = f"""Hi {name},

Welcome to SignSimple! Your account has been created successfully.

You can now sign PDF documents legally and securely.

Your free plan includes 10 documents per month.

Get started: https://signsimple.co.uk/dashboard

Best regards,
The SignSimple Team
Avyangah Technologies Limited
"""
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #1976d2; color: #fff; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; color: #fff;">Welcome to SignSimple! 🎉</h1>
        </div>
        <div style="background: #fff; padding: 30px; border-radius: 0 0 8px 8px;">
            <p>Hi {name},</p>
            <p>Your account has been created. You're all set to start signing documents!</p>
            <div style="background: #f9f9f9; padding: 20px; border-radius: 6px; margin: 20px 0;">
                <h3 style="margin-top: 0;">What you can do:</h3>
                <p>✅ Sign PDF documents legally and securely</p>
            </div>
            <p><strong>Your free plan includes 10 documents per month.</strong></p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://signsimple.co.uk/dashboard" style="display: inline-block; background-color: #1976d2; color: #ffffff !important; padding: 14px 40px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
            </div>
            <p>Best regards,<br><strong>The SignSimple Team</strong></p>
        </div>
    </div>
</body>
</html>
"""
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)
        logger.info(f'[EMAIL] Welcome email sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'[EMAIL] Failed to send welcome email to {user.email}: {e}')
        return False


class RegisterView(generics.CreateAPIView):
    """Register a new user with email/password."""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        user.is_active = False
        user.email_verified = False
        user.save(update_fields=['is_active', 'email_verified'])
        
        UserProfile.objects.get_or_create(user=user)
        
        try:
            user.send_activation_email()
            logger.info(f'[AUTH] Activation email sent to {user.email}')
        except Exception as e:
            logger.error(f'[AUTH] Failed to send activation email to {user.email}: {e}')
        
        return Response({
            'message': 'Registration successful! Please check your email to activate your account.',
            'email': user.email,
            'requires_activation': True,
        }, status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    """Activate user account via email link."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        try:
            user = User.objects.get(activation_token=token)
        except User.DoesNotExist:
            return redirect('https://signsimple.co.uk/login?error=Invalid+activation+link')
        
        if user.activation_token_created_at:
            expiry = user.activation_token_created_at + timezone.timedelta(days=7)
            if timezone.now() > expiry:
                return redirect('https://signsimple.co.uk/login?error=Activation+link+expired.+Please+register+again.')
        
        user.activate_account()
        _send_welcome_email(user, auth_method='email')
        logger.info(f'[AUTH] Account activated: {user.email}')
        return redirect('https://signsimple.co.uk/login?message=Account+activated!+Please+login.')


class ResendActivationView(APIView):
    """Resend activation email."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').lower()
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If that email exists, we sent a new activation link.'})
        
        if user.email_verified:
            return Response({'message': 'Account is already activated. Please login.'})
        
        try:
            user.send_activation_email()
            return Response({'message': 'Activation email sent. Please check your inbox.'})
        except Exception as e:
            logger.error(f'[AUTH] Failed to resend activation to {email}: {e}')
            return Response({'error': 'Failed to send email. Please try again.'}, status=500)


class LoginView(APIView):
    """
    Login with email/password.
    Account must be activated first.
    Returns must_change_password flag if user needs to change temp password.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Check if account is activated
        if not user.is_active:
            return Response({
                'error': 'Please activate your account first. Check your email for the activation link.',
                'requires_activation': True,
                'email': user.email,
            }, status=status.HTTP_403_FORBIDDEN)
        
        tokens = _get_tokens_for_user(user)
        
        response_data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Login successful',
        }
        
        # Check if user must change their password (temp password)
        if user.must_change_password:
            response_data['must_change_password'] = True
            response_data['message'] = 'Login successful. Please change your password.'
        
        return Response(response_data)


class ForceChangePasswordView(APIView):
    """
    Change password for users who logged in with a temporary password.
    Used when must_change_password is True.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')
        
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=400)
        
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=400)
        
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        
        logger.info(f'[AUTH] Password changed (forced) for {user.email}')
        
        return Response({
            'message': 'Password changed successfully',
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.must_change_password = False  # Clear the flag if set
        request.user.save()
        return Response({'message': 'Password changed'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserDashboardView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        from documents.models import Document
        total_docs = Document.objects.filter(user=user).count()
        pending = Document.objects.filter(user=user, status='PENDING').count()
        signed = Document.objects.filter(user=user, status='SIGNED').count()

        return Response({
            'user': UserSerializer(user).data,
            'statistics': {
                'total_documents': total_docs,
                'pending_documents': pending,
                'signed_documents': signed,
                'documents_remaining': user.documents_remaining,
            },
            'subscription': {
                'plan': user.subscription_plan,
                'documents_used': user.documents_used_this_month,
                'documents_limit': user.documents_limit,
                'plan_details': settings.SUBSCRIPTION_PLANS[user.subscription_plan],
            },
        })


class OAuthProvidersView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        import os
        providers = {}
        for name, config in OAUTH_PROVIDERS.items():
            client_id = os.environ.get(config['client_id_env'], '')
            providers[name] = bool(client_id)
        return Response(providers)


class OAuthRedirectView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, provider):
        if provider not in OAUTH_PROVIDERS:
            return Response({'error': f'Unknown provider: {provider}'}, status=400)

        client_id, _ = _get_oauth_credentials(provider)
        if not client_id:
            return Response({'error': f'{provider.title()} login is not configured'}, status=400)

        config = OAUTH_PROVIDERS[provider]
        callback_url = request.build_absolute_uri(f'/api/auth/oauth/{provider}/callback/')

        params = {
            'client_id': client_id,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'scope': config['scope'],
        }

        if provider == 'google':
            params['prompt'] = 'select_account'
        if provider in ('google', 'microsoft', 'linkedin'):
            params['access_type'] = 'online'

        authorize_url = f"{config['authorize_url']}?{urlencode(params)}"
        return redirect(authorize_url)


class OAuthCallbackView(APIView):
    """OAuth callback - creates user and auto-activates them."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, provider):
        code = request.query_params.get('code')
        error = request.query_params.get('error')

        if error:
            logger.warning(f'[OAUTH] {provider} returned error: {error}')
            return _redirect_error(f'{provider.title()} login was cancelled.')

        if not code:
            return _redirect_error('No authorisation code received.')

        if provider not in OAUTH_PROVIDERS:
            return _redirect_error(f'Unknown provider: {provider}')

        client_id, client_secret = _get_oauth_credentials(provider)
        if not client_id:
            return _redirect_error(f'{provider.title()} login is not configured.')

        config = OAUTH_PROVIDERS[provider]
        callback_url = request.build_absolute_uri(f'/api/auth/oauth/{provider}/callback/')

        try:
            token_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': callback_url,
                'grant_type': 'authorization_code',
            }
            headers = {'Accept': 'application/json'}
            token_resp = http_requests.post(config['token_url'], data=token_data, headers=headers, timeout=10)

            if token_resp.status_code != 200:
                logger.error(f'[OAUTH] {provider} token exchange failed: {token_resp.text}')
                return _redirect_error(f'{provider.title()} authentication failed.')

            token_json = token_resp.json()
            access_token = token_json.get('access_token')

            if not access_token:
                logger.error(f'[OAUTH] {provider} no access_token in response')
                return _redirect_error(f'{provider.title()} authentication failed.')

        except Exception as e:
            logger.error(f'[OAUTH] {provider} token exchange error: {e}')
            return _redirect_error(f'{provider.title()} authentication failed.')

        try:
            user_info = self._fetch_user_info(provider, access_token, config)
        except Exception as e:
            logger.error(f'[OAUTH] {provider} userinfo error: {e}')
            return _redirect_error(f'Could not retrieve your {provider.title()} profile.')

        if not user_info.get('email'):
            return _redirect_error(f'No email address found in your {provider.title()} account.')

        email = user_info['email'].lower()
        full_name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        provider_uid = str(user_info.get('id', ''))

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'auth_provider': provider,
                'provider_user_id': provider_uid,
                'profile_picture': picture,
                'is_active': True,
                'email_verified': True,
                'email_verified_at': timezone.now(),
            }
        )

        if not created:
            if not user.auth_provider:
                user.auth_provider = provider
                user.provider_user_id = provider_uid
            if picture:
                user.profile_picture = picture
            if not user.is_active:
                user.is_active = True
                user.email_verified = True
                user.email_verified_at = timezone.now()
            user.save()
        else:
            UserProfile.objects.create(user=user)
            _send_welcome_email(user, auth_method=provider)

        logger.info(f'[OAUTH] {provider} {"registered" if created else "login"}: {email}')
        return _redirect_success(user, is_new=created)

    def _fetch_user_info(self, provider, access_token, config):
        headers = {'Authorization': f'Bearer {access_token}'}

        if provider == 'github':
            resp = http_requests.get(config['userinfo_url'], headers=headers, timeout=10)
            data = resp.json()
            email_resp = http_requests.get(config['emails_url'], headers=headers, timeout=10)
            emails = email_resp.json()
            primary_email = next((e['email'] for e in emails if e.get('primary')), None)
            return {
                'id': data.get('id'),
                'email': primary_email or data.get('email', ''),
                'name': data.get('name', data.get('login', '')),
                'picture': data.get('avatar_url', ''),
            }
        elif provider == 'facebook':
            resp = http_requests.get(config['userinfo_url'], params={'access_token': access_token}, timeout=10)
            data = resp.json()
            picture_url = data.get('picture', {}).get('data', {}).get('url', '') if isinstance(data.get('picture'), dict) else ''
            return {
                'id': data.get('id'),
                'email': data.get('email', ''),
                'name': data.get('name', ''),
                'picture': picture_url,
            }
        else:
            resp = http_requests.get(config['userinfo_url'], headers=headers, timeout=10)
            data = resp.json()
            return {
                'id': data.get('sub', data.get('id', '')),
                'email': data.get('email', data.get('mail', data.get('userPrincipalName', ''))),
                'name': data.get('name', data.get('displayName', '')),
                'picture': data.get('picture', ''),
            }
