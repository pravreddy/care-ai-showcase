"""
Invitation Token Views - Magic Link System
Secure user invitation without default passwords
"""
from django.utils import timezone
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .invitation_models import InvitationToken
from .models import User, UserProfile
from .serializers import UserSerializer

import logging

logger = logging.getLogger('authentication')


class CreateInvitationView(APIView):
    """
    Admin creates an invitation token for a new user.
    Returns the magic link that can be copied or emailed.
    
    POST /api/auth/invite/create/
    Body:
    {
        "email": "newuser@example.com",
        "full_name": "John Doe",  // optional
        "send_email": true,        // optional, default false
        "organisation_id": "uuid"  // optional
    }
    
    Response:
    {
        "invitation_id": "uuid",
        "email": "newuser@example.com",
        "magic_link": "https://signsimple.co.uk/set-password/abc123...",
        "expires_at": "2026-04-03T10:30:00Z",
        "email_sent": true
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        # Only admins can create invitations
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can create invitations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        email = request.data.get('email', '').lower().strip()
        full_name = request.data.get('full_name', '').strip()
        send_email = request.data.get('send_email', False)
        organisation_id = request.data.get('organisation_id', None)
        
        # Validate email
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': f'User with email {email} already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's an active invitation for this email
        active_invitation = InvitationToken.objects.filter(
            email=email,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if active_invitation:
            # Resend the existing invitation
            magic_link = active_invitation.get_magic_link(request)
            
            email_sent = False
            if send_email:
                email_sent = active_invitation.send_invitation_email()
            
            return Response({
                'invitation_id': str(active_invitation.id),
                'email': active_invitation.email,
                'full_name': active_invitation.full_name,
                'magic_link': magic_link,
                'expires_at': active_invitation.expires_at.isoformat(),
                'email_sent': email_sent,
                'message': 'Active invitation already exists. Link regenerated.',
            })
        
        # Create new invitation
        try:
            invitation = InvitationToken.objects.create(
                email=email,
                full_name=full_name,
                created_by=request.user,
                organisation_id=organisation_id if organisation_id else None,
            )
            
            magic_link = invitation.get_magic_link(request)
            
            # Optionally send email
            email_sent = False
            if send_email:
                email_sent = invitation.send_invitation_email()
            
            logger.info(f'[INVITATION] Created by {request.user.email} for {email}')
            
            return Response({
                'invitation_id': str(invitation.id),
                'email': invitation.email,
                'full_name': invitation.full_name,
                'magic_link': magic_link,
                'expires_at': invitation.expires_at.isoformat(),
                'email_sent': email_sent,
                'message': 'Invitation created successfully',
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f'[INVITATION] Failed to create invitation for {email}: {e}')
            return Response(
                {'error': 'Failed to create invitation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyInvitationTokenView(APIView):
    """
    Verify that an invitation token is valid.
    Used by frontend to check token before showing password setup form.
    
    GET /api/auth/invite/verify/{token}/
    
    Response:
    {
        "valid": true,
        "email": "newuser@example.com",
        "full_name": "John Doe"
    }
    """
    permission_classes = (permissions.AllowAny,)
    
    def get(self, request, token):
        try:
            invitation = InvitationToken.objects.get(token=token)
        except InvitationToken.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation link'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if token is valid
        if invitation.is_used:
            return Response(
                {'error': 'This invitation has already been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            return Response(
                {'error': 'This invitation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Token is valid
        return Response({
            'valid': True,
            'email': invitation.email,
            'full_name': invitation.full_name,
        })


class SetupPasswordView(APIView):
    """
    User sets their password using the magic link token.
    Creates a new user account and marks the invitation as used.
    
    POST /api/auth/invite/setup-password/
    Body:
    {
        "token": "abc123...",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }
    
    Response:
    {
        "user": { ... },
        "tokens": {
            "access": "...",
            "refresh": "..."
        },
        "message": "Account created successfully"
    }
    """
    permission_classes = (permissions.AllowAny,)
    
    @transaction.atomic
    def post(self, request):
        token = request.data.get('token', '').strip()
        password = request.data.get('password', '')
        confirm_password = request.data.get('confirm_password', '')
        
        # Validate inputs
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not password or len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find invitation
        try:
            invitation = InvitationToken.objects.select_for_update().get(token=token)
        except InvitationToken.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation link'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify invitation is valid
        if invitation.is_used:
            return Response(
                {'error': 'This invitation has already been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            return Response(
                {'error': 'This invitation has expired. Please contact your administrator.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        # This happens when portal users are auto-created by _auto_link_portal_user
        # before send_password_setup_email() is called. In that case we just
        # set their password instead of creating a new account.
        existing_user = User.objects.filter(email=invitation.email).first()
        
        if existing_user:
            # Pre-created user (e.g. auto-created client portal user)
            # Just set their password and activate them
            try:
                existing_user.set_password(password)
                existing_user.is_active = True
                existing_user.email_verified = True
                existing_user.email_verified_at = timezone.now()
                existing_user.must_change_password = False
                existing_user.save(update_fields=[
                    'password', 'is_active', 'email_verified',
                    'email_verified_at', 'must_change_password'
                ])

                invitation.mark_as_used(user=existing_user)

                refresh = RefreshToken.for_user(existing_user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }

                logger.info(f'[INVITATION] Password set for pre-created user: {existing_user.email}')

                return Response({
                    'user': UserSerializer(existing_user).data,
                    'tokens': tokens,
                    'message': 'Password set successfully! Welcome to SignSimple.',
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f'[INVITATION] Failed to set password for {existing_user.email}: {e}')
                return Response(
                    {'error': 'Failed to set password. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Create user account (new user, normal invitation flow)
        try:
            user = User.objects.create_user(
                email=invitation.email,
                password=password,
                full_name=invitation.full_name or '',
                is_active=True,
                email_verified=True,
                email_verified_at=timezone.now(),
                must_change_password=False,
            )
            
            # Create user profile
            UserProfile.objects.get_or_create(user=user)
            
            # Mark invitation as used
            invitation.mark_as_used(user=user)
            
            # If invitation is org-specific, add user to organisation
            if invitation.organisation:
                from organisations.models import OrganisationMembership
                OrganisationMembership.objects.create(
                    organisation=invitation.organisation,
                    user=user,
                    is_active=True,
                )
                logger.info(f'[INVITATION] User {user.email} added to org {invitation.organisation.name}')
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            logger.info(f'[INVITATION] Account created via magic link: {user.email}')
            
            # Send welcome email
            try:
                from .views import _send_welcome_email
                _send_welcome_email(user, auth_method='invitation')
            except Exception as e:
                logger.error(f'[INVITATION] Failed to send welcome email to {user.email}: {e}')
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'message': 'Account created successfully! Welcome to SignSimple.',
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f'[INVITATION] Failed to create account for {invitation.email}: {e}')
            return Response(
                {'error': 'Failed to create account. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendInvitationView(APIView):
    """
    Resend invitation email for an existing invitation.
    
    POST /api/auth/invite/resend/
    Body:
    {
        "invitation_id": "uuid"
    }
    
    Response:
    {
        "message": "Invitation email sent",
        "email_sent": true
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can resend invitations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invitation_id = request.data.get('invitation_id')
        
        if not invitation_id:
            return Response(
                {'error': 'invitation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invitation = InvitationToken.objects.get(id=invitation_id)
        except InvitationToken.DoesNotExist:
            return Response(
                {'error': 'Invitation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if invitation.is_used:
            return Response(
                {'error': 'This invitation has already been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            return Response(
                {'error': 'This invitation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resend email
        email_sent = invitation.send_invitation_email()
        
        if email_sent:
            logger.info(f'[INVITATION] Resent invitation to {invitation.email} by {request.user.email}')
            return Response({
                'message': 'Invitation email sent',
                'email_sent': True,
            })
        else:
            return Response(
                {'error': 'Failed to send invitation email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListInvitationsView(APIView):
    """
    List all invitations created by the current user or organisation.
    
    GET /api/auth/invite/list/
    
    Optional query params:
    - status: 'active', 'used', 'expired', 'all' (default: 'all')
    
    Response:
    {
        "invitations": [
            {
                "id": "uuid",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_used": false,
                "is_expired": false,
                "created_at": "2026-03-27T10:00:00Z",
                "expires_at": "2026-04-03T10:00:00Z",
                "used_at": null
            },
            ...
        ]
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can view invitations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status', 'all')
        
        # Base queryset - invitations created by this user or their org
        invitations = InvitationToken.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        # Apply status filter
        if status_filter == 'active':
            invitations = invitations.filter(is_used=False, expires_at__gt=timezone.now())
        elif status_filter == 'used':
            invitations = invitations.filter(is_used=True)
        elif status_filter == 'expired':
            invitations = invitations.filter(is_used=False, expires_at__lte=timezone.now())
        
        # Serialize
        data = []
        for inv in invitations:
            data.append({
                'id': str(inv.id),
                'email': inv.email,
                'full_name': inv.full_name,
                'is_used': inv.is_used,
                'is_expired': inv.is_expired,
                'is_valid': inv.is_valid,
                'created_at': inv.created_at.isoformat(),
                'expires_at': inv.expires_at.isoformat(),
                'used_at': inv.used_at.isoformat() if inv.used_at else None,
                'organisation': inv.organisation.name if inv.organisation else None,
            })
        
        return Response({'invitations': data})
