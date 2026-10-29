"""
Organisation Signals - Send email notifications when users are added to organisations
Note: Does NOT send emails for OrganisationRequest - those are handled in the model methods
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail

from .models import Organisation, OrganisationMembership

import logging

logger = logging.getLogger('organisations')


def _send_organisation_invite_email(membership):
    """
    Send email to user when they are added to an organisation BY AN ADMIN.
    (Not for self-service org requests - those have their own email flow)
    """
    try:
        user = membership.user
        org = membership.organisation
        role = membership.get_role_display()
        branch_name = membership.branch.name if membership.branch else None
        
        # Get user's first name or fallback to email
        name = user.full_name.split()[0] if user.full_name else user.email.split('@')[0]
        
        subject = f"You've been added to {org.name} on SignSimple"
        
        branch_text = f" ({branch_name})" if branch_name else ""
        
        # Plain text message
        message = f"""Hi {name},

You've been added to {org.name}{branch_text} as a {role}.

What you can do:
• Sign and manage documents for {org.name}
• Track daily sales and invoices
• Access the team dashboard

Log in to get started:
https://signsimple.co.uk/login

If you don't have an account yet, register using your email: {user.email}

Best regards,
The SignSimple Team
Avyangah Technologies Limited

---
You received this email because an administrator added you to {org.name}.
"""
        
        # HTML message
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {org.primary_colour}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ display: inline-block; background: {org.primary_colour}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .role-badge {{ display: inline-block; background: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 4px; font-weight: 600; }}
        .features {{ background: white; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .feature {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You've been added to {org.name}</h1>
        </div>
        <div class="content">
            <p>Hi {name},</p>
            <p>You've been added to <strong>{org.name}</strong>{branch_text} as a <span class="role-badge">{role}</span>.</p>
            
            <div class="features">
                <h3>What you can do:</h3>
                <div class="feature">📝 Sign and manage documents for {org.name}</div>
                <div class="feature">📊 Track daily sales and invoices</div>
                <div class="feature">👥 Access the team dashboard</div>
            </div>
            
            <center>
                <a href="https://signsimple.co.uk/login" class="button">Log In Now</a>
            </center>
            
            <p>If you don't have an account yet, register using your email: <strong>{user.email}</strong></p>
            
            <p>Best regards,<br>
            <strong>The SignSimple Team</strong><br>
            Avyangah Technologies Limited</p>
        </div>
        <div class="footer">
            <p>You received this email because an administrator added you to {org.name}.</p>
            <p>© 2026 Avyangah Technologies Limited. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        logger.info(f'[EMAIL] Organisation invite sent to {user.email} for {org.name}')
        return True
        
    except Exception as e:
        logger.error(f'[EMAIL] Failed to send organisation invite to {user.email}: {e}')
        return False


@receiver(post_save, sender=OrganisationMembership)
def membership_created_handler(sender, instance, created, **kwargs):
    """
    Send email when a user is added to an organisation.
    Only sends on creation, not on updates.
    Does NOT send to the owner (they created the org).
    """
    if created:
        # Don't send email to the owner (they already know they created it)
        if instance.user != instance.organisation.owner:
            _send_organisation_invite_email(instance)


# Note: Organisation creation email is NOT sent via signal anymore.
# It's handled by OrganisationRequest._send_approval_email() for self-service,
# or can be added manually for admin-created orgs if needed.
