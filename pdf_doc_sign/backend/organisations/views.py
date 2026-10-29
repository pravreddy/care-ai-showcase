"""
Organisation Views - SignSimple UK
Handles organisation requests, invitations, auto-join, and direct member creation
"""
from datetime import timedelta

from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organisation, OrganisationRequest, OrganisationMembership, OrganisationInvitation
from authentication.models import User, generate_temp_password

import logging

logger = logging.getLogger('organisations')


# ============================================================
# Organisation Request Views (Scenario 3 & 4)
# ============================================================

class OrganisationRequestCreateView(APIView):
    """
    Submit a request to create a new organisation.
    User must be logged in (e.g., via Google OAuth).
    A verification email will be sent to the work email.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        
        # Get request data
        organisation_name = request.data.get('organisation_name', '').strip()
        organisation_domain = request.data.get('organisation_domain', '').strip().lower()
        work_email = request.data.get('work_email', '').strip().lower()
        company_number = request.data.get('company_number', '').strip()
        
        # Validate
        if not organisation_name:
            return Response({'error': 'Organisation name is required'}, status=400)
        if not organisation_domain:
            return Response({'error': 'Organisation domain is required'}, status=400)
        if not work_email:
            return Response({'error': 'Work email is required'}, status=400)
        
        # Check work email format
        if '@' not in work_email:
            return Response({'error': 'Invalid work email format'}, status=400)
        
        # Check if user already has a pending request
        existing = OrganisationRequest.objects.filter(
            requested_by=user,
            status__in=['PENDING_WORK_EMAIL', 'PENDING_APPROVAL']
        ).first()
        if existing:
            return Response({
                'error': 'You already have a pending organisation request.',
                'request_id': str(existing.id),
                'status': existing.status,
            }, status=400)
        
        # Check if organisation domain already exists
        if Organisation.objects.filter(domain=organisation_domain).exists():
            return Response({
                'error': f'An organisation with domain {organisation_domain} already exists. Please contact them to be added as a member.'
            }, status=400)
        
        # Create request
        org_request = OrganisationRequest.objects.create(
            requested_by=user,
            organisation_name=organisation_name,
            organisation_domain=organisation_domain,
            work_email=work_email,
            company_number=company_number,
            status='PENDING_WORK_EMAIL',
        )
        
        # Send verification email to work email
        try:
            org_request.send_work_email_verification()
            logger.info(f'[ORG] Work email verification sent to {work_email} for {organisation_name}')
        except Exception as e:
            logger.error(f'[ORG] Failed to send verification to {work_email}: {e}')
            return Response({
                'error': 'Failed to send verification email. Please try again.',
            }, status=500)
        
        return Response({
            'message': f'Verification email sent to {work_email}. Please check your inbox and click the link to verify.',
            'request_id': str(org_request.id),
            'work_email': work_email,
            'status': 'PENDING_WORK_EMAIL',
        }, status=201)


class OrganisationRequestStatusView(APIView):
    """
    Check status of an organisation request.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, request_id=None):
        user = request.user
        
        if request_id:
            try:
                org_request = OrganisationRequest.objects.get(id=request_id, requested_by=user)
            except OrganisationRequest.DoesNotExist:
                return Response({'error': 'Request not found'}, status=404)
            
            return Response({
                'id': str(org_request.id),
                'organisation_name': org_request.organisation_name,
                'work_email': org_request.work_email,
                'work_email_verified': org_request.work_email_verified,
                'status': org_request.status,
                'status_display': org_request.get_status_display(),
                'created_at': org_request.created_at,
                'rejection_reason': org_request.rejection_reason if org_request.status == 'REJECTED' else None,
            })
        else:
            # List all requests for this user
            requests = OrganisationRequest.objects.filter(requested_by=user)
            return Response([{
                'id': str(r.id),
                'organisation_name': r.organisation_name,
                'status': r.status,
                'status_display': r.get_status_display(),
                'created_at': r.created_at,
            } for r in requests])


class VerifyWorkEmailView(APIView):
    """
    Verify work email via link clicked from email.
    After verification, auto-approve or send to admin review.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        try:
            org_request = OrganisationRequest.objects.get(work_email_verification_token=token)
        except OrganisationRequest.DoesNotExist:
            return redirect('https://signsimple.co.uk/organisation-request?error=Invalid+verification+link')
        
        # Check if already verified
        if org_request.work_email_verified:
            return redirect('https://signsimple.co.uk/organisation-request?message=Email+already+verified')
        
        # Check if token is expired (7 days)
        if org_request.work_email_verification_sent_at:
            expiry = org_request.work_email_verification_sent_at + timezone.timedelta(days=7)
            if timezone.now() > expiry:
                return redirect('https://signsimple.co.uk/organisation-request?error=Verification+link+expired.+Please+submit+a+new+request.')
        
        # Verify the work email
        org_request.verify_work_email()
        
        logger.info(f'[ORG] Work email verified: {org_request.work_email} for {org_request.organisation_name}')
        
        if org_request.status == 'APPROVED':
            return redirect('https://signsimple.co.uk/dashboard?message=Organisation+approved!+Welcome+to+SignSimple.')
        else:
            return redirect('https://signsimple.co.uk/organisation-request?message=Email+verified!+Your+request+is+pending+admin+approval.')


class ResendWorkEmailVerificationView(APIView):
    """
    Resend work email verification for a pending request.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, request_id):
        user = request.user
        
        try:
            org_request = OrganisationRequest.objects.get(id=request_id, requested_by=user)
        except OrganisationRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=404)
        
        if org_request.status != 'PENDING_WORK_EMAIL':
            return Response({'error': 'This request is no longer pending email verification'}, status=400)
        
        try:
            org_request.send_work_email_verification()
            return Response({'message': f'Verification email resent to {org_request.work_email}'})
        except Exception as e:
            logger.error(f'[ORG] Failed to resend verification: {e}')
            return Response({'error': 'Failed to send email. Please try again.'}, status=500)


class MyOrganisationsView(APIView):
    """
    List organisations the current user belongs to.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        memberships = OrganisationMembership.objects.filter(user=user, is_active=True).select_related('organisation', 'branch')
        
        return Response([{
            'organisation_id': str(m.organisation.id),
            'organisation_name': m.organisation.name,
            'organisation_slug': m.organisation.slug,
            'branch_id': str(m.branch.id) if m.branch else None,
            'branch_name': m.branch.name if m.branch else None,
            'role': m.role,
            'role_display': m.get_role_display(),
            'can_manage': m.can_manage,
            'can_admin': m.can_admin,
            'joined_at': m.joined_at,
        } for m in memberships])


# ============================================================
# Invitation Views (Scenario 5: Direct Invitation)
# ============================================================

class InviteMemberView(APIView):
    """
    Invite a new member to an organisation.
    Only Owners, Admins, and Managers can invite.
    Creates a "ghost user" if the email doesn't have an account.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, org_id):
        user = request.user
        
        # Check if user has permission to invite
        try:
            membership = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this organisation'}, status=403)
        
        if not membership.can_manage:
            return Response({'error': 'You do not have permission to invite members'}, status=403)
        
        # Get invitation data
        email = request.data.get('email', '').strip().lower()
        role = request.data.get('role', 'MEMBER')
        branch_id = request.data.get('branch_id')
        
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        if '@' not in email:
            return Response({'error': 'Invalid email format'}, status=400)
        
        # Validate role (can't invite someone with higher role than yourself)
        role_hierarchy = {'OWNER': 5, 'ADMIN': 4, 'MANAGER': 3, 'MEMBER': 2, 'VIEWER': 1}
        if role_hierarchy.get(role, 0) > role_hierarchy.get(membership.role, 0):
            return Response({'error': f'You cannot invite someone as {role}'}, status=403)
        
        org = membership.organisation
        
        # Check if already a member
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            existing_membership = OrganisationMembership.objects.filter(
                user=existing_user, organisation=org
            ).first()
            if existing_membership:
                return Response({
                    'error': f'{email} is already a member of this organisation',
                    'existing_role': existing_membership.role,
                }, status=400)
        
        # Check for pending invitation
        pending_invite = OrganisationInvitation.objects.filter(
            email=email, organisation=org, status='PENDING'
        ).first()
        if pending_invite and not pending_invite.is_expired:
            return Response({
                'error': f'A pending invitation already exists for {email}',
                'invitation_id': str(pending_invite.id),
            }, status=400)
        
        # Get branch if specified
        branch = None
        if branch_id:
            try:
                from .models import Branch
                branch = Branch.objects.get(id=branch_id, organisation=org)
            except Branch.DoesNotExist:
                return Response({'error': 'Branch not found'}, status=404)
        
        # Create invitation
        invitation = OrganisationInvitation.objects.create(
            organisation=org,
            branch=branch,
            email=email,
            role=role,
            invited_by=user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        
        # Send invitation email
        try:
            invitation.send_invitation_email()
            logger.info(f'[ORG] Invitation sent to {email} for {org.name} by {user.email}')
        except Exception as e:
            logger.error(f'[ORG] Failed to send invitation to {email}: {e}')
            invitation.delete()
            return Response({'error': 'Failed to send invitation email'}, status=500)
        
        return Response({
            'message': f'Invitation sent to {email}',
            'invitation_id': str(invitation.id),
            'expires_at': invitation.expires_at,
        }, status=201)


class CreateMemberDirectlyView(APIView):
    """
    Create a new member account directly with a temporary password OR send password setup email.
    
    Option A: Set temporary password (admin gives it to user)
    Option B: Send password setup email (user sets own password)
    
    Only Owners and Admins can use this.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, org_id):
        user = request.user
        
        # Check if user has permission (must be admin/owner)
        try:
            membership = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this organisation'}, status=403)
        
        if not membership.can_admin:
            return Response({'error': 'Only Owners and Admins can create members directly'}, status=403)
        
        org = membership.organisation
        
        # Get member data
        email = request.data.get('email', '').strip().lower()
        full_name = request.data.get('full_name', '').strip()
        role = request.data.get('role', 'MEMBER')
        branch_id = request.data.get('branch_id')
        
        # Method: 'temp_password' or 'send_email'
        method = request.data.get('method', 'send_email')
        custom_password = request.data.get('password', '').strip()
        
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        if '@' not in email:
            return Response({'error': 'Invalid email format'}, status=400)
        
        # Validate role
        role_hierarchy = {'OWNER': 5, 'ADMIN': 4, 'MANAGER': 3, 'MEMBER': 2, 'VIEWER': 1}
        if role_hierarchy.get(role, 0) > role_hierarchy.get(membership.role, 0):
            return Response({'error': f'You cannot create someone as {role}'}, status=403)
        
        # Check if user already exists
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            # Check if already a member
            existing_membership = OrganisationMembership.objects.filter(
                user=existing_user, organisation=org
            ).first()
            if existing_membership:
                return Response({
                    'error': f'{email} is already a member of this organisation',
                    'existing_role': existing_membership.role,
                }, status=400)
            
            # Add existing user to org
            branch = None
            if branch_id:
                try:
                    from .models import Branch
                    branch = Branch.objects.get(id=branch_id, organisation=org)
                except Branch.DoesNotExist:
                    return Response({'error': 'Branch not found'}, status=404)
            
            new_membership = OrganisationMembership.objects.create(
                user=existing_user,
                organisation=org,
                branch=branch,
                role=role,
            )
            
            logger.info(f'[ORG] Existing user {email} added to {org.name} by {user.email}')
            
            return Response({
                'message': f'{email} has been added to {org.name}',
                'user_id': str(existing_user.id),
                'email': existing_user.email,
                'full_name': existing_user.full_name,
                'role': role,
                'is_new_user': False,
            })
        
        # Get branch if specified
        branch = None
        if branch_id:
            try:
                from .models import Branch
                branch = Branch.objects.get(id=branch_id, organisation=org)
            except Branch.DoesNotExist:
                return Response({'error': 'Branch not found'}, status=404)
        
        # Create new user
        if method == 'temp_password':
            # Option A: Create with temporary password
            temp_password = custom_password if custom_password else generate_temp_password()
            
            new_user = User.objects.create_user(
                email=email,
                password=temp_password,
                full_name=full_name,
                is_active=True,
                email_verified=True,  # Admin-created, so consider verified
                must_change_password=True,  # Force change on first login
            )
            
            # Add to organisation
            new_membership = OrganisationMembership.objects.create(
                user=new_user,
                organisation=org,
                branch=branch,
                role=role,
            )
            
            logger.info(f'[ORG] New user {email} created with temp password for {org.name} by {user.email}')
            
            return Response({
                'message': f'Account created for {email}',
                'user_id': str(new_user.id),
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': role,
                'is_new_user': True,
                'temporary_password': temp_password,
                'must_change_password': True,
                'note': 'Share this password with the user. They will be required to change it on first login.',
            }, status=201)
        
        else:
            # Option B: Create user and send password setup email
            new_user = User.objects.create_user(
                email=email,
                password=None,  # No password yet
                full_name=full_name,
                is_active=True,
                email_verified=True,  # Admin-created, so consider verified
            )
            
            # Add to organisation
            new_membership = OrganisationMembership.objects.create(
                user=new_user,
                organisation=org,
                branch=branch,
                role=role,
            )
            
            # Generate password reset token and try to send email
            token = new_user.generate_password_reset_token()
            email_sent = False
            password_setup_url = f"https://signsimple.co.uk/set-password/{token}/"
            
            try:
                new_user.send_password_setup_email()
                email_sent = True
                logger.info(f'[ORG] New user {email} created with setup email for {org.name} by {user.email}')
            except Exception as e:
                logger.error(f'[ORG] Failed to send setup email to {email}: {e}')
            
            response_data = {
                'message': f'Account created for {email}',
                'user_id': str(new_user.id),
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': role,
                'is_new_user': True,
                'email_sent': email_sent,
                'password_setup_url': password_setup_url,
            }
            
            if not email_sent:
                response_data['note'] = 'Email could not be sent. Share this password setup link with the user manually:'
            else:
                response_data['note'] = 'Password setup email sent. User can also use this link if email not received:'
            
            return Response(response_data, status=201)


class AcceptInvitationView(APIView):
    """
    Accept an organisation invitation.
    If user is logged in, add them directly.
    If not logged in, redirect to register/login with the invitation token.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        """View invitation details (for frontend to show)"""
        try:
            invitation = OrganisationInvitation.objects.select_related('organisation', 'branch').get(token=token)
        except OrganisationInvitation.DoesNotExist:
            return Response({'error': 'Invalid invitation link'}, status=404)
        
        if invitation.status != 'PENDING':
            return Response({
                'error': 'This invitation has already been used or revoked',
                'status': invitation.status,
            }, status=400)
        
        if invitation.is_expired:
            return Response({
                'error': 'This invitation has expired',
                'expired_at': invitation.expires_at,
            }, status=400)
        
        return Response({
            'invitation_id': str(invitation.id),
            'organisation_name': invitation.organisation.name,
            'organisation_logo': invitation.organisation.logo_display_url,
            'branch_name': invitation.branch.name if invitation.branch else None,
            'role': invitation.role,
            'role_display': invitation.get_role_display(),
            'email': invitation.email,
            'invited_by': invitation.invited_by.full_name or invitation.invited_by.email if invitation.invited_by else None,
            'expires_at': invitation.expires_at,
        })

    def post(self, request, token):
        """Accept the invitation"""
        try:
            invitation = OrganisationInvitation.objects.select_related('organisation').get(token=token)
        except OrganisationInvitation.DoesNotExist:
            return Response({'error': 'Invalid invitation link'}, status=404)
        
        if not invitation.is_valid:
            if invitation.is_expired:
                return Response({'error': 'This invitation has expired'}, status=400)
            return Response({'error': 'This invitation is no longer valid'}, status=400)
        
        # User must be authenticated to accept
        if not request.user.is_authenticated:
            return Response({
                'error': 'You must be logged in to accept this invitation',
                'redirect_url': f'/login?invitation={token}',
            }, status=401)
        
        user = request.user
        
        # Check email matches (optional - depends on security requirements)
        # For now, we allow any logged-in user to accept if they clicked the link
        # (the email is just informational)
        
        # Accept the invitation
        try:
            membership = invitation.accept(user)
            logger.info(f'[ORG] Invitation accepted: {user.email} joined {invitation.organisation.name}')
            
            return Response({
                'message': f'Welcome to {invitation.organisation.name}!',
                'organisation_id': str(invitation.organisation.id),
                'organisation_name': invitation.organisation.name,
                'role': membership.role,
            })
        except Exception as e:
            logger.error(f'[ORG] Failed to accept invitation: {e}')
            return Response({'error': 'Failed to accept invitation'}, status=500)


class RevokeInvitationView(APIView):
    """
    Revoke a pending invitation.
    Only the person who sent it or an admin can revoke.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, invitation_id):
        user = request.user
        
        try:
            invitation = OrganisationInvitation.objects.select_related('organisation').get(id=invitation_id)
        except OrganisationInvitation.DoesNotExist:
            return Response({'error': 'Invitation not found'}, status=404)
        
        # Check permission (invited_by or admin of org)
        is_sender = invitation.invited_by == user
        is_admin = OrganisationMembership.objects.filter(
            user=user, organisation=invitation.organisation, role__in=['OWNER', 'ADMIN'], is_active=True
        ).exists()
        
        if not (is_sender or is_admin):
            return Response({'error': 'You do not have permission to revoke this invitation'}, status=403)
        
        if invitation.status != 'PENDING':
            return Response({'error': 'This invitation cannot be revoked'}, status=400)
        
        invitation.status = 'REVOKED'
        invitation.save(update_fields=['status'])
        
        return Response({'message': 'Invitation revoked'})


class OrganisationInvitationsView(APIView):
    """
    List pending invitations for an organisation.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, org_id):
        user = request.user
        
        # Check if user has permission
        try:
            membership = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this organisation'}, status=403)
        
        if not membership.can_manage:
            return Response({'error': 'You do not have permission to view invitations'}, status=403)
        
        invitations = OrganisationInvitation.objects.filter(
            organisation_id=org_id
        ).order_by('-created_at')
        
        return Response([{
            'id': str(inv.id),
            'email': inv.email,
            'role': inv.role,
            'role_display': inv.get_role_display(),
            'status': inv.status,
            'invited_by': inv.invited_by.email if inv.invited_by else None,
            'created_at': inv.created_at,
            'expires_at': inv.expires_at,
            'is_expired': inv.is_expired,
        } for inv in invitations])


class OrganisationMembersView(APIView):
    """
    List members of an organisation.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, org_id):
        user = request.user
        
        # Check if user is a member
        try:
            membership = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this organisation'}, status=403)
        
        members = OrganisationMembership.objects.filter(
            organisation_id=org_id, is_active=True
        ).select_related('user', 'branch').order_by('role', 'user__full_name')
        
        return Response([{
            'id': str(m.id),
            'user_id': str(m.user.id),
            'email': m.user.email,
            'full_name': m.user.full_name,
            'role': m.role,
            'role_display': m.get_role_display(),
            'branch_id': str(m.branch.id) if m.branch else None,
            'branch_name': m.branch.name if m.branch else None,
            'joined_at': m.joined_at,
            'can_manage': m.can_manage,
        } for m in members])


# ============================================================
# Organisation Detail & Update (for org admins)
# ============================================================

class OrganisationDetailView(APIView):
    """
    GET  /api/organisations/{org_id}/  — get org details + stats
    PATCH /api/organisations/{org_id}/ — update name, address, email, etc.
    Only OWNER/ADMIN can update.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def _get_membership(self, user, org_id):
        try:
            return OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return None

    def get(self, request, org_id):
        m = self._get_membership(request.user, org_id)
        if not m:
            return Response({'error': 'Not a member'}, status=403)
        org = m.organisation
        from organisations.models import Branch
        branches = Branch.objects.filter(organisation=org, is_active=True)
        return Response({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'domain': org.domain,
            'email': org.email,
            'phone': org.phone,
            'website': org.website,
            'address': org.address,
            'city': org.city,
            'postcode': org.postcode,
            'country': org.country,
            'company_number': org.company_number,
            'vat_number': org.vat_number,
            'plan': org.plan,
            'status': org.status,
            'sales_access_enabled': org.sales_access_enabled,
            'industry': org.industry,
            'industry_display': org.get_industry_display() if org.industry else '',
            'sales_access_notes': org.sales_access_notes,
            'logo_url': org.logo_display_url,
            'primary_colour': org.primary_colour,
            'secondary_colour': org.secondary_colour,
            # Use requesting user's document usage (org-level counter
            # is not reliably updated — user-level is the source of truth)
            'documents_used': request.user.documents_used_this_month,
            'documents_limit': request.user.documents_limit,
            'can_admin': m.can_admin,
            'can_manage': m.can_manage,
            'my_role': m.role,
            'branches': [{'id': str(b.id), 'name': b.name, 'city': b.city} for b in branches],
        })

    def patch(self, request, org_id):
        m = self._get_membership(request.user, org_id)
        if not m:
            return Response({'error': 'Not a member'}, status=403)
        if not m.can_admin:
            return Response({'error': 'Only Owner/Admin can update organisation details'}, status=403)
        org = m.organisation
        allowed = ['name', 'email', 'phone', 'website', 'address', 'city',
                   'postcode', 'country', 'company_number', 'vat_number',
                   'primary_colour', 'secondary_colour']
        for field in allowed:
            if field in request.data:
                setattr(org, field, request.data[field])
        org.save()
        logger.info(f'[ORG] {request.user.email} updated org details for {org.name}')
        return Response({'message': 'Organisation updated successfully.'})


class OrganisationMemberDetailView(APIView):
    """
    PATCH /api/organisations/{org_id}/members/{membership_id}/ — change role or branch
    DELETE                                                       — deactivate member
    Only OWNER/ADMIN can do this. Cannot remove yourself.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, org_id, membership_id):
        user = request.user
        try:
            actor = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not actor.can_admin:
            return Response({'error': 'Only Owner/Admin can change roles'}, status=403)
        try:
            target = OrganisationMembership.objects.get(
                id=membership_id, organisation_id=org_id
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Member not found'}, status=404)

        # Cannot change owner's role
        if target.role == 'OWNER' and actor.role != 'OWNER':
            return Response({'error': 'Cannot change the Owner role'}, status=403)

        new_role = request.data.get('role')
        if new_role:
            role_hierarchy = {'OWNER': 5, 'ADMIN': 4, 'MANAGER': 3, 'MEMBER': 2, 'VIEWER': 1}
            if role_hierarchy.get(new_role, 0) > role_hierarchy.get(actor.role, 0):
                return Response({'error': f'Cannot assign role higher than your own'}, status=403)
            target.role = new_role

        branch_id = request.data.get('branch_id')
        if branch_id:
            from organisations.models import Branch
            try:
                branch = Branch.objects.get(id=branch_id, organisation_id=org_id)
                target.branch = branch
            except Branch.DoesNotExist:
                return Response({'error': 'Branch not found'}, status=404)
        elif 'branch_id' in request.data and branch_id is None:
            target.branch = None

        target.save()
        logger.info(f'[ORG] {user.email} updated membership {membership_id} in {org_id}')
        return Response({'message': 'Member updated.', 'role': target.role})

    def delete(self, request, org_id, membership_id):
        user = request.user
        try:
            actor = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not actor.can_admin:
            return Response({'error': 'Only Owner/Admin can remove members'}, status=403)
        try:
            target = OrganisationMembership.objects.get(
                id=membership_id, organisation_id=org_id
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Member not found'}, status=404)
        if str(target.user_id) == str(user.id):
            return Response({'error': 'You cannot remove yourself'}, status=400)
        if target.role == 'OWNER':
            return Response({'error': 'Cannot remove the Owner'}, status=403)
        target.is_active = False
        target.save(update_fields=['is_active'])
        logger.info(f'[ORG] {user.email} removed {target.user.email} from {org_id}')
        return Response({'message': 'Member removed.'})


class ResendMemberSetupEmailView(APIView):
    """
    POST /api/organisations/{org_id}/members/{membership_id}/resend-setup/
    Resend password setup email to a member who hasn't logged in yet.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, org_id, membership_id):
        user = request.user
        try:
            actor = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not actor.can_admin:
            return Response({'error': 'Only Owner/Admin can resend setup emails'}, status=403)
        try:
            target = OrganisationMembership.objects.get(
                id=membership_id, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Member not found'}, status=404)
        try:
            target.user.send_password_setup_email()
            return Response({'message': f'Setup email sent to {target.user.email}'})
        except Exception as e:
            logger.error(f'[ORG] Resend setup email failed: {e}')
            return Response({'error': 'Failed to send email.'}, status=500)


class BranchViewSet(APIView):
    """
    GET  /api/organisations/{org_id}/branches/       — list branches
    POST /api/organisations/{org_id}/branches/       — create branch
    PATCH /api/organisations/{org_id}/branches/{id}/ — update branch
    DELETE /api/organisations/{org_id}/branches/{id}/ — deactivate branch
    """
    permission_classes = (permissions.IsAuthenticated,)

    def _check_admin(self, user, org_id):
        try:
            m = OrganisationMembership.objects.get(
                user=user, organisation_id=org_id, is_active=True
            )
            return m if m.can_admin else None
        except OrganisationMembership.DoesNotExist:
            return None

    def get(self, request, org_id):
        try:
            OrganisationMembership.objects.get(
                user=request.user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        from organisations.models import Branch
        branches = Branch.objects.filter(organisation_id=org_id).order_by('name')
        return Response([{
            'id': str(b.id), 'name': b.name, 'code': b.code,
            'address': b.address, 'city': b.city, 'postcode': b.postcode,
            'phone': b.phone, 'is_active': b.is_active,
            'member_count': OrganisationMembership.objects.filter(
                branch=b, is_active=True
            ).count(),
        } for b in branches])

    def post(self, request, org_id):
        if not self._check_admin(request.user, org_id):
            return Response({'error': 'Only Owner/Admin can create branches'}, status=403)
        from organisations.models import Branch
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Branch name is required'}, status=400)
        if Branch.objects.filter(organisation_id=org_id, name=name).exists():
            return Response({'error': 'A branch with this name already exists'}, status=400)
        branch = Branch.objects.create(
            organisation_id=org_id,
            name=name,
            code=request.data.get('code', ''),
            address=request.data.get('address', ''),
            city=request.data.get('city', ''),
            postcode=request.data.get('postcode', ''),
            phone=request.data.get('phone', ''),
        )
        logger.info(f'[ORG] {request.user.email} created branch {name} in org {org_id}')
        return Response({
            'id': str(branch.id), 'name': branch.name, 'message': f'Branch "{name}" created.'
        }, status=201)


class BranchDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def _get(self, org_id, branch_id):
        from organisations.models import Branch
        try:
            return Branch.objects.get(id=branch_id, organisation_id=org_id)
        except Branch.DoesNotExist:
            return None

    def patch(self, request, org_id, branch_id):
        try:
            m = OrganisationMembership.objects.get(
                user=request.user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not m.can_admin:
            return Response({'error': 'Only Owner/Admin can edit branches'}, status=403)
        branch = self._get(org_id, branch_id)
        if not branch:
            return Response({'error': 'Branch not found'}, status=404)
        for field in ['name', 'code', 'address', 'city', 'postcode', 'phone']:
            if field in request.data:
                setattr(branch, field, request.data[field])
        branch.save()
        return Response({'message': 'Branch updated.'})

    def delete(self, request, org_id, branch_id):
        try:
            m = OrganisationMembership.objects.get(
                user=request.user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not m.can_admin:
            return Response({'error': 'Only Owner/Admin can delete branches'}, status=403)
        branch = self._get(org_id, branch_id)
        if not branch:
            return Response({'error': 'Branch not found'}, status=404)
        # Unassign members from this branch before deactivating
        OrganisationMembership.objects.filter(branch=branch).update(branch=None)
        branch.is_active = False
        branch.save(update_fields=['is_active'])
        logger.info(f'[ORG] {request.user.email} deactivated branch {branch.name}')
        return Response({'message': 'Branch removed.'})


class SalesAccessRequestView(APIView):
    """
    POST /api/organisations/{org_id}/request-sales-access/
    Org admin requests sales access — notifies platform superusers.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, org_id):
        try:
            m = OrganisationMembership.objects.get(
                user=request.user, organisation_id=org_id, is_active=True
            )
        except OrganisationMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=403)
        if not m.can_admin:
            return Response({'error': 'Only Owner/Admin can request sales access'}, status=403)
        org = m.organisation
        if org.sales_access_enabled:
            return Response({'message': 'Sales access is already enabled for this organisation.'})

        # Save industry and notes
        industry = request.data.get('industry', '').strip()
        notes = request.data.get('notes', '').strip()
        if industry:
            org.industry = industry
        if notes:
            org.sales_access_notes = notes
        if industry or notes:
            org.save(update_fields=[
                f for f in ['industry', 'sales_access_notes']
                if (f == 'industry' and industry) or (f == 'sales_access_notes' and notes)
            ])

        # Build industry label for email
        industry_label = dict(org.INDUSTRY_CHOICES).get(industry, industry or 'Not specified')

        # Notify platform superusers
        try:
            from django.core.mail import send_mail
            from django.conf import settings as django_settings
            admins = User.objects.filter(is_superuser=True, is_active=True)
            admin_emails = [a.email for a in admins]
            if admin_emails:
                send_mail(
                    subject=f'[Sales Access Request] {org.name} — {industry_label}',
                    message=(
                        f'{request.user.email} has requested Sales & Invoicing access.\n\n'
                        f'Organisation: {org.name}\n'
                        f'Industry: {industry_label}\n'
                        f'Use case: {notes or "Not provided"}\n'
                        f'ID: {org.id}\n\n'
                        f'Enable in Django Admin:\n'
                        f'https://signsimple.co.uk/admin/organisations/organisation/{org.id}/change/'
                    ),
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            logger.error(f'[ORG] Sales access request email failed: {e}')

        logger.info(f'[ORG] Sales access requested for {org.name} ({industry_label}) by {request.user.email}')
        return Response({
            'message': 'Your request has been submitted. Our team will review and enable it within 24 hours.',
            'industry': industry_label,
        })


# ============================================================
# Platform Admin Views (superuser only — replaces Django admin for common tasks)
# ============================================================

class PlatformAdminOrgsView(APIView):
    """
    GET  /api/platform/organisations/
    List all organisations with their sales access status, industry, pending requests.
    Superuser only.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Platform admin access required'}, status=403)

        orgs = Organisation.objects.all().order_by('-created_at')
        data = []
        for org in orgs:
            member_count = OrganisationMembership.objects.filter(
                organisation=org, is_active=True
            ).count()
            data.append({
                'id': str(org.id),
                'name': org.name,
                'domain': org.domain,
                'email': org.email,
                'plan': org.plan,
                'status': org.status,
                'sales_access_enabled': org.sales_access_enabled,
                'industry': org.industry,
                'industry_display': org.get_industry_display() if org.industry else '',
                'sales_access_notes': org.sales_access_notes,
                'member_count': member_count,
                'created_at': org.created_at,
                'owner_email': org.owner.email if org.owner else '',
            })
        return Response(data)


class PlatformAdminOrgActionView(APIView):
    """
    POST /api/platform/organisations/{org_id}/enable-sales/
    POST /api/platform/organisations/{org_id}/disable-sales/
    POST /api/platform/organisations/{org_id}/set-plan/
    Superuser only.
    """
    permission_classes = (permissions.IsAuthenticated,)

    # Actions that platform admins (Avyangah org ADMIN/OWNER) can do
    SAFE_ACTIONS = {'enable-sales', 'disable-sales'}
    # Actions only Django superusers can do (billing-sensitive / irreversible)
    SUPERUSER_ONLY_ACTIONS = {'set-plan', 'set-status'}

    def post(self, request, org_id, action):
        user = request.user

        if action in self.SUPERUSER_ONLY_ACTIONS:
            # Billing / status changes — superuser only, no delegation
            if not user.is_superuser:
                return Response(
                    {'error': 'Only a platform superuser can change plan or status.'},
                    status=403,
                )
        elif action in self.SAFE_ACTIONS:
            # Day-to-day tasks — any Avyangah org admin can do this
            if not user.is_platform_admin:
                return Response(
                    {'error': 'Platform admin access required.'},
                    status=403,
                )
        else:
            return Response({'error': f'Unknown action: {action}'}, status=400)

        try:
            org = Organisation.objects.get(id=org_id)
        except Organisation.DoesNotExist:
            return Response({'error': 'Organisation not found'}, status=404)

        if action == 'enable-sales':
            org.grant_sales_access(approved_by=request.user)
            # Notify the org owner/admin by email
            try:
                from django.core.mail import send_mail
                from django.conf import settings as django_settings
                if org.email or org.owner.email:
                    send_mail(
                        subject=f'Sales & Invoicing is now enabled — {org.name}',
                        message=(
                            f'Hi,\n\n'
                            f'Sales & Invoicing has been enabled for {org.name}.\n\n'
                            f'You can now access Daily Sales, Clients, and Invoicing from your dashboard.\n\n'
                            f'Login at: https://signsimple.co.uk/dashboard\n\n'
                            f'Best regards,\nThe SignSimple Team'
                        ),
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[org.email or org.owner.email],
                        fail_silently=True,
                    )
            except Exception as e:
                logger.error(f'[PLATFORM] Enable sales notify email failed: {e}')
            logger.info(f'[PLATFORM] {request.user.email} enabled sales for {org.name}')
            return Response({'message': f'Sales access enabled for {org.name}. Notification sent.'})

        elif action == 'disable-sales':
            org.revoke_sales_access()
            logger.info(f'[PLATFORM] {request.user.email} disabled sales for {org.name}')
            return Response({'message': f'Sales access disabled for {org.name}.'})

        elif action == 'set-plan':
            new_plan = request.data.get('plan')
            valid_plans = ['FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE']
            if new_plan not in valid_plans:
                return Response({'error': f'Invalid plan. Choose from: {valid_plans}'}, status=400)
            org.plan = new_plan
            org.save(update_fields=['plan'])
            logger.info(f'[PLATFORM] {request.user.email} set plan {new_plan} for {org.name}')
            return Response({'message': f'Plan set to {new_plan} for {org.name}.'})

        elif action == 'set-status':
            new_status = request.data.get('status')
            valid_statuses = ['ACTIVE', 'TRIAL', 'SUSPENDED', 'CANCELLED']
            if new_status not in valid_statuses:
                return Response({'error': f'Invalid status.'}, status=400)
            org.status = new_status
            org.save(update_fields=['status'])
            logger.info(f'[PLATFORM] {request.user.email} set status {new_status} for {org.name}')
            return Response({'message': f'Status set to {new_status} for {org.name}.'})


# ============================================================
# Auto-Join Views (Scenario 6: Viral Growth)
# ============================================================

class CheckAutoJoinView(APIView):
    """
    Check if an email domain matches an organisation with auto-join enabled.
    Called during registration to prompt users to join their team.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return Response({'auto_join_available': False})
        
        org = Organisation.find_auto_join_org(email)
        
        if org:
            return Response({
                'auto_join_available': True,
                'organisation_id': str(org.id),
                'organisation_name': org.name,
                'organisation_logo': org.logo_display_url,
                'default_role': org.auto_join_default_role,
            })
        else:
            return Response({'auto_join_available': False})


class AutoJoinOrganisationView(APIView):
    """
    Join an organisation automatically based on email domain.
    User must be logged in and their email domain must match the org's domain.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, org_id):
        user = request.user
        
        # Get organisation
        try:
            org = Organisation.objects.get(id=org_id, auto_join_enabled=True, status='ACTIVE')
        except Organisation.DoesNotExist:
            return Response({'error': 'Organisation not found or auto-join is disabled'}, status=404)
        
        # Check email domain matches
        if '@' not in user.email:
            return Response({'error': 'Invalid email'}, status=400)
        
        user_domain = user.email.split('@')[1].lower()
        if user_domain != org.domain.lower():
            return Response({
                'error': f'Your email domain ({user_domain}) does not match the organisation domain ({org.domain})'
            }, status=403)
        
        # Check if already a member
        existing = OrganisationMembership.objects.filter(user=user, organisation=org).first()
        if existing:
            return Response({
                'error': 'You are already a member of this organisation',
                'role': existing.role,
            }, status=400)
        
        # Join the organisation
        membership = OrganisationMembership.objects.create(
            user=user,
            organisation=org,
            role=org.auto_join_default_role,
        )
        
        logger.info(f'[ORG] Auto-join: {user.email} joined {org.name}')
        
        return Response({
            'message': f'Welcome to {org.name}!',
            'organisation_id': str(org.id),
            'organisation_name': org.name,
            'role': membership.role,
        })


# ============================================================
# Password Reset Views
# ============================================================

class SetPasswordView(APIView):
    """
    Set password using a password reset token.
    Used when admin creates a user without password and sends setup link.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        """Check if token is valid"""
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Invalid or expired link'}, status=404)
        
        if not user.is_password_reset_token_valid():
            return Response({'error': 'This link has expired'}, status=400)
        
        return Response({
            'email': user.email,
            'full_name': user.full_name,
            'valid': True,
        })

    def post(self, request, token):
        """Set the password"""
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Invalid or expired link'}, status=404)
        
        if not user.is_password_reset_token_valid():
            return Response({'error': 'This link has expired'}, status=400)
        
        new_password = request.data.get('password', '')
        
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=400)
        
        user.set_password(new_password)
        user.clear_password_reset_token()
        user.must_change_password = False
        user.is_active = True
        user.save(update_fields=['password', 'must_change_password', 'is_active'])
        
        logger.info(f'[AUTH] Password set for {user.email} via reset token')
        
        return Response({
            'message': 'Password set successfully. You can now log in.',
            'email': user.email,
        })
