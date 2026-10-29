"""
Custom User Model - SignSimple UK
With account activation via email and feature access control
"""
import uuid
import secrets
import string
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# The slug of the platform owner organisation (Avyangah Technologies)
PLATFORM_OWNER_ORG_SLUG = 'avyangah'


def generate_temp_password(length=12):
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits
    # Ensure at least one uppercase, one lowercase, one digit
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    password += [secrets.choice(alphabet) for _ in range(length - 3)]
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=255, blank=True)

    # Email verification / Account activation
    email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address'
    )
    activation_token = models.UUIDField(default=uuid.uuid4)
    activation_token_created_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Password reset / Set password
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)
    
    # Force password change (for temp passwords)
    must_change_password = models.BooleanField(
        default=False,
        help_text='User must change password on next login (set when admin creates with temp password)'
    )

    # Individual user-level sales access (rarely used - org-level is preferred)
    sales_access_enabled = models.BooleanField(
        default=False,
        help_text='Individual sales access (usually org-level is used instead)'
    )
    sales_access_approved_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales_access_approvals',
    )
    sales_access_approved_at = models.DateTimeField(null=True, blank=True)

    # Subscription & Usage
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    documents_used_this_month = models.IntegerField(default=0)
    extra_docs_purchased = models.IntegerField(default=0)
    ai_scans_used_this_month = models.IntegerField(default=0)
    extra_ai_scans_purchased = models.IntegerField(default=0)
    usage_reset_date = models.DateField(null=True, blank=True)

    # Coupon tracking
    coupon_code = models.CharField(max_length=50, blank=True, help_text='Coupon code used at signup')

    # OAuth provider info
    auth_provider = models.CharField(max_length=50, blank=True)
    provider_user_id = models.CharField(max_length=255, blank=True)
    profile_picture = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    # ===========================================
    # Document Usage
    # ===========================================

    @property
    def documents_limit(self):
        from django.conf import settings
        base = settings.SUBSCRIPTION_PLANS[self.subscription_plan]['documents_per_month']
        return base + self.extra_docs_purchased

    @property
    def documents_remaining(self):
        self._check_monthly_reset()
        return max(0, self.documents_limit - self.documents_used_this_month)

    @property
    def can_upload_document(self):
        return self.documents_remaining > 0

    def increment_document_usage(self):
        self._check_monthly_reset()
        self.documents_used_this_month += 1
        self.save(update_fields=['documents_used_this_month'])

    # ===========================================
    # AI Scan Usage
    # ===========================================

    @property
    def ai_scans_limit(self):
        from django.conf import settings
        base = settings.SUBSCRIPTION_PLANS[self.subscription_plan]['ai_scans_per_month']
        return base + self.extra_ai_scans_purchased

    @property
    def ai_scans_remaining(self):
        self._check_monthly_reset()
        return max(0, self.ai_scans_limit - self.ai_scans_used_this_month)

    @property
    def can_scan_document(self):
        return self.ai_scans_remaining > 0

    def increment_ai_scan_usage(self):
        self._check_monthly_reset()
        self.ai_scans_used_this_month += 1
        self.save(update_fields=['ai_scans_used_this_month'])

    # ===========================================
    # Monthly Reset (shared for docs + AI scans)
    # ===========================================

    def _check_monthly_reset(self):
        today = timezone.now().date()
        if not self.usage_reset_date or today.month != self.usage_reset_date.month or today.year != self.usage_reset_date.year:
            self.documents_used_this_month = 0
            self.extra_docs_purchased = 0
            self.ai_scans_used_this_month = 0
            self.extra_ai_scans_purchased = 0
            self.usage_reset_date = today
            self.save(update_fields=[
                'documents_used_this_month', 'extra_docs_purchased',
                'ai_scans_used_this_month', 'extra_ai_scans_purchased',
                'usage_reset_date',
            ])

    # ===========================================
    # OAuth & Account Status
    # ===========================================

    @property
    def is_oauth_user(self):
        return bool(self.auth_provider)

    @property
    def is_account_activated(self):
        """Check if account is activated (email verified OR OAuth user)."""
        if self.is_oauth_user:
            return True
        return self.email_verified

    @property
    def is_platform_admin(self):
        """
        Check if user is a platform admin (Avyangah Technologies staff).

        Access requires BOTH:
          1. User is a Django superuser, OR
          2. User is OWNER or ADMIN of the Avyangah org
             AND the Avyangah org is the ONLY org they belong to
        """
        if self.is_superuser:
            return True
        from organisations.models import OrganisationMembership
        is_avyangah_admin = OrganisationMembership.objects.filter(
            user=self,
            is_active=True,
            role__in=['OWNER', 'ADMIN'],
            organisation__slug=PLATFORM_OWNER_ORG_SLUG,
            organisation__status='ACTIVE'
        ).exists()
        if not is_avyangah_admin:
            return False
        other_orgs = OrganisationMembership.objects.filter(
            user=self,
            is_active=True,
        ).exclude(
            organisation__slug=PLATFORM_OWNER_ORG_SLUG
        ).exists()
        return not other_orgs

    @property
    def can_access_sales(self):
        """
        Check if user can access Sales & Invoicing features.
        """
        if self.sales_access_enabled:
            return True
        from organisations.models import OrganisationMembership
        return OrganisationMembership.objects.filter(
            user=self,
            is_active=True,
            organisation__sales_access_enabled=True,
            organisation__status__in=['ACTIVE', 'TRIAL']
        ).exists()

    def get_sales_organisations(self):
        from organisations.models import OrganisationMembership, Organisation
        org_ids = OrganisationMembership.objects.filter(
            user=self,
            is_active=True,
            organisation__sales_access_enabled=True,
            organisation__status__in=['ACTIVE', 'TRIAL']
        ).values_list('organisation_id', flat=True)
        return Organisation.objects.filter(id__in=org_ids)

    def get_client_accounts(self):
        from sales.models import Client
        return Client.objects.filter(user=self, is_active=True)

    @property
    def is_client_user(self):
        return self.get_client_accounts().exists()

    def grant_sales_access(self, approved_by):
        self.sales_access_enabled = True
        self.sales_access_approved_by = approved_by
        self.sales_access_approved_at = timezone.now()
        self.save(update_fields=['sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'])

    def revoke_sales_access(self):
        self.sales_access_enabled = False
        self.sales_access_approved_by = None
        self.sales_access_approved_at = None
        self.save(update_fields=['sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'])

    # ===========================================
    # Password Reset / Setup
    # ===========================================

    def generate_password_reset_token(self):
        self.password_reset_token = uuid.uuid4()
        self.password_reset_token_created_at = timezone.now()
        self.save(update_fields=['password_reset_token', 'password_reset_token_created_at'])
        return self.password_reset_token

    def is_password_reset_token_valid(self):
        if not self.password_reset_token or not self.password_reset_token_created_at:
            return False
        expiry = self.password_reset_token_created_at + timezone.timedelta(hours=24)
        return timezone.now() < expiry

    def clear_password_reset_token(self):
        self.password_reset_token = None
        self.password_reset_token_created_at = None
        self.save(update_fields=['password_reset_token', 'password_reset_token_created_at'])

    def send_password_setup_email(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        from .invitation_models import InvitationToken

        InvitationToken.objects.filter(
            email=self.email, is_used=False
        ).update(is_used=True)

        invitation = InvitationToken.objects.create(
            email=self.email,
            full_name=self.full_name or '',
            created_by=None,
        )

        setup_url = f"https://signsimple.co.uk/set-password/{invitation.token}/"
        name = self.full_name.split()[0] if self.full_name else self.email.split('@')[0]
        
        subject = "Set your SignSimple password"
        message = f"""Hi {name},

An account has been created for you on SignSimple.

Click the link below to set your password and get started:

{setup_url}

This link will expire in 24 hours.

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
            <h1>Welcome to SignSimple!</h1>
        </div>
        <div class="content">
            <p>Hi {name},</p>
            <p>An account has been created for you on SignSimple.</p>
            <p>Click the button below to set your password and get started:</p>
            <center>
                <a href="{setup_url}" class="button" style="color: #ffffff !important;">Set My Password</a>
            </center>
            <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>
            <p>Best regards,<br>
            <strong>The SignSimple Team</strong><br>
            Avyangah Technologies Limited</p>
        </div>
        <div class="footer">
            <p>&copy; 2026 Avyangah Technologies Limited. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        send_mail(
            subject=subject, message=message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message, fail_silently=False,
        )

    def send_activation_email(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        self.activation_token = uuid.uuid4()
        self.activation_token_created_at = timezone.now()
        self.save(update_fields=['activation_token', 'activation_token_created_at'])
        
        activation_url = f"https://signsimple.co.uk/api/auth/activate/{self.activation_token}/"
        name = self.full_name.split()[0] if self.full_name else self.email.split('@')[0]
        
        subject = "Activate your SignSimple account"
        message = f"""Hi {name},

Welcome to SignSimple! Please activate your account by clicking the link below:

{activation_url}

This link will expire in 7 days.

Once activated, you can:
- Sign PDF documents legally and securely
- Scan documents for AI-generated content

Your free plan includes 10 documents and 3 AI scans per month.

If you didn't create this account, you can ignore this email.

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
        .features {{ background: white; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .feature {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to SignSimple!</h1>
        </div>
        <div class="content">
            <p>Hi {name},</p>
            <p>Welcome to SignSimple! Please activate your account:</p>
            <center>
                <a href="{activation_url}" class="button" style="color: #ffffff !important;">Activate My Account</a>
            </center>
            <p style="color: #666; font-size: 14px;">This link will expire in 7 days.</p>
            <div class="features">
                <h3>Once activated, you can:</h3>
                <div class="feature">Sign PDF documents legally and securely</div>
                <div class="feature">Scan documents for AI-generated content</div>
            </div>
            <p><strong>Your free plan includes 10 documents and 3 AI scans per month.</strong></p>
            <p>If you didn't create this account, you can ignore this email.</p>
            <p>Best regards,<br>
            <strong>The SignSimple Team</strong><br>
            Avyangah Technologies Limited</p>
        </div>
        <div class="footer">
            <p>&copy; 2026 Avyangah Technologies Limited. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        send_mail(
            subject=subject, message=message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message, fail_silently=False,
        )

    def activate_account(self):
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.is_active = True
        self.save(update_fields=['email_verified', 'email_verified_at', 'is_active'])


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='United Kingdom')
    postcode = models.CharField(max_length=10, blank=True)
    company_number = models.CharField(max_length=20, blank=True, help_text='Companies House number')
    vat_number = models.CharField(max_length=20, blank=True, help_text='VAT registration number')
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"
