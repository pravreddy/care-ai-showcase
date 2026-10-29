"""
Invitation Token Model for Magic Link System
Secure user invitation without default passwords
"""
import uuid
import secrets
from django.db import models
from django.utils import timezone
from django.conf import settings


def generate_secure_token():
    """Generate a cryptographically secure token (128-bit hex = 32 chars)."""
    return secrets.token_urlsafe(32)


class InvitationToken(models.Model):
    """
    Invitation token for new user registration via Magic Link.
    Used by admins to invite users without setting a default password.
    
    Workflow:
    1. Admin creates invitation with user's email
    2. System generates secure one-time token
    3. Admin sends magic link (via email/WhatsApp/Teams)
    4. User clicks link and sets their own password
    5. Token expires after use or 7 days
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The invitee
    email = models.EmailField(
        help_text='Email address of the person being invited'
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional: Full name of invitee'
    )
    
    # The secure token
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_secure_token,
        help_text='One-time use secure token'
    )
    
    # Expiry and usage tracking
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text='Token expiry date (default: 7 days from creation)'
    )
    
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the token was used (if at all)'
    )
    
    is_used = models.BooleanField(
        default=False,
        help_text='Whether token has been used'
    )
    
    # Who created the invitation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invitations_sent',
        help_text='Admin who created this invitation'
    )
    
    # Optional: Organisation context (if org-based invites)
    organisation = models.ForeignKey(
        'organisations.Organisation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='auth_invitation_tokens',  # Changed to avoid clash with OrganisationInvitation
        help_text='Organisation the user is being invited to (optional)'
    )
    
    # The created user (once they set their password)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_invitation',
        help_text='User created from this invitation'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['is_used', 'expires_at']),
        ]
    
    def __str__(self):
        status = 'Used' if self.is_used else ('Expired' if self.is_expired else 'Active')
        return f"Invitation to {self.email} [{status}]"
    
    def save(self, *args, **kwargs):
        # Set expiry to 7 days from now if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self, user=None):
        """Mark token as used."""
        self.is_used = True
        self.used_at = timezone.now()
        if user:
            self.user = user
        self.save(update_fields=['is_used', 'used_at', 'user'])
    
    def get_magic_link(self, request=None):
        """
        Generate the magic link URL.
        Returns the full URL that should be sent to the invitee.
        """
        if request:
            # Use request to build absolute URL
            from django.urls import reverse
            path = reverse('setup-password', kwargs={'token': self.token})
            return request.build_absolute_uri(path)
        else:
            # Fallback to settings-based URL
            return f"https://signsimple.co.uk/set-password/{self.token}/"
    
    def send_invitation_email(self):
        """
        Send invitation email with magic link.
        Returns True if successful, False otherwise.
        """
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        try:
            magic_link = self.get_magic_link()
            name = self.full_name.split()[0] if self.full_name else self.email.split('@')[0]
            inviter_name = self.created_by.full_name if self.created_by and self.created_by.full_name else "Your administrator"
            
            subject = f"{inviter_name} invited you to SignSimple"
            
            message = f"""Hi {name},

{inviter_name} has invited you to join SignSimple.

Click the link below to create your account and set your password:

{magic_link}

This link will expire in 7 days.

If you didn't expect this invitation, you can safely ignore this email.

Best regards,
The SignSimple Team
Avyangah Technologies Limited
"""
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ display: inline-block; background: #4caf50; color: #ffffff !important; padding: 14px 40px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You're Invited to SignSimple! 🎉</h1>
        </div>
        <div class="content">
            <p>Hi {name},</p>
            <p><strong>{inviter_name}</strong> has invited you to join SignSimple.</p>
            <p>Click the button below to create your account and set your password:</p>
            
            <center>
                <a href="{magic_link}" class="button" style="color: #ffffff !important;">Set Up My Account</a>
            </center>
            
            <p style="color: #666; font-size: 14px;">This link will expire in 7 days.</p>
            <p style="color: #666; font-size: 14px;">If you didn't expect this invitation, you can safely ignore this email.</p>
            
            <p>Best regards,<br>
            <strong>The SignSimple Team</strong><br>
            Avyangah Technologies Limited</p>
        </div>
        <div class="footer">
            <p>© 2026 Avyangah Technologies Limited. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger('authentication')
            logger.error(f'[INVITATION] Failed to send invitation email to {self.email}: {e}')
            return False
