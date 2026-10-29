"""
Multi-Tenant Organisation & Branch Models - SignSimple UK White-Label
Allows different companies to use SignSimple with their own branding.

Architecture:
  Organisation (Acme Ltd)
  ├── Branch: London HQ     → custom logo, colours
  ├── Branch: Manchester     → different logo override
  └── Users[]               → staff linked to org + optional branch

White-label features per org:
  - Custom logo + brand colours on signing pages
  - Custom subdomain (acme.signsimple.co.uk) or custom domain
  - Own document templates with their branding
  - Custom pricing negotiated per client
  - Separate billing and usage tracking
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator


class Organisation(models.Model):
    """
    A company/business that uses SignSimple.
    Each org gets white-label branding and separate billing.
    """
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),  # Custom pricing
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('TRIAL', 'Trial'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, help_text='Used in subdomain: {slug}.signsimple.co.uk')

    # Organisation domain (for email verification)
    domain = models.CharField(
        max_length=255, blank=True,
        help_text='Primary email domain (e.g., acerhealthcare.co.uk)'
    )
    
    # Auto-join setting (Scenario 6: Viral Growth)
    auto_join_enabled = models.BooleanField(
        default=False,
        help_text='Allow users with matching domain to join automatically on registration'
    )
    auto_join_default_role = models.CharField(
        max_length=20, default='MEMBER',
        choices=(
            ('MEMBER', 'Member'),
            ('VIEWER', 'Viewer'),
        ),
        help_text='Default role for auto-joined members'
    )

    # Per-org feature flags (configurable per organisation)
    feature_flags = models.JSONField(
        default=dict, blank=True,
        help_text='Per-org feature toggles, e.g. {"show_courier": true, "enable_disputes": false}',
    )

    # Industry vertical (set when requesting sales access)
    INDUSTRY_CHOICES = (
        ('CATERING', 'Catering & Food Delivery'),
        ('HEALTHCARE', 'Home Healthcare & Nursing'),
        ('WASTE', 'Waste Management & Skip Hire'),
        ('PLANT_HIRE', 'Equipment & Plant Hire'),
        ('LOGISTICS', 'Logistics & Courier'),
        ('CLEANING', 'Cleaning Services'),
        ('CONSTRUCTION', 'Construction & Trades'),
        ('RETAIL', 'Retail & Wholesale'),
        ('OTHER', 'Other'),
    )
    industry = models.CharField(
        max_length=20, choices=INDUSTRY_CHOICES, blank=True, default='',
        help_text='Industry vertical — determines column labels and terminology in Sales module',
    )
    sales_access_notes = models.TextField(
        blank=True,
        help_text='Notes from org admin when requesting sales access (use case description)',
    )

    # Sales & Invoicing access for the entire organisation
    sales_access_enabled = models.BooleanField(
        default=False,
        help_text='Enable Sales & Invoicing features for all members of this organisation'
    )
    sales_access_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='org_sales_approvals',
        help_text='Superuser who approved sales access for this organisation'
    )
    sales_access_approved_at = models.DateTimeField(null=True, blank=True)

    # Company details
    company_number = models.CharField(max_length=20, blank=True, help_text='Companies House number')
    vat_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='United Kingdom')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, help_text='Billing/contact email')
    website = models.URLField(blank=True)

    # White-label branding
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True, help_text='External logo URL (if not uploaded)')
    primary_colour = models.CharField(
        max_length=7, default='#1565c0',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Must be a hex colour like #1565c0')],
        help_text='Brand primary colour (hex)',
    )
    secondary_colour = models.CharField(max_length=7, default='#f57c00')
    custom_domain = models.CharField(
        max_length=255, blank=True, unique=True, null=True,
        help_text='Custom domain (e.g. sign.acme.co.uk) — requires DNS setup',
    )

    # Subscription & billing
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    custom_price_gbp = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Custom monthly price (overrides plan price for enterprise clients)',
    )
    documents_per_month_override = models.IntegerField(
        null=True, blank=True,
        help_text='Custom doc limit (overrides plan default)',
    )
    documents_used_this_month = models.IntegerField(default=0)
    extra_docs_purchased = models.IntegerField(default=0)
    usage_reset_date = models.DateField(null=True, blank=True)

    # Owner (the person who created the org)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='owned_organisations',
    )

    # Payment provider link
    payment_provider = models.CharField(max_length=50, blank=True)
    payment_provider_customer_id = models.CharField(max_length=255, blank=True)

    # Timestamps
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['domain']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-create OrganisationMembership for owner when org is created or owner changes.
        This ensures the owner always has OWNER role membership.
        """
        is_new = self._state.adding
        old_owner_id = None
        
        if not is_new:
            # Check if owner is changing
            try:
                old_instance = Organisation.objects.get(pk=self.pk)
                old_owner_id = old_instance.owner_id
            except Organisation.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # After save, ensure owner has OWNER membership
        if is_new or (old_owner_id and old_owner_id != self.owner_id):
            self._ensure_owner_membership()
    
    def _ensure_owner_membership(self):
        """Create or update membership for owner with OWNER role."""
        # Check if membership already exists
        existing = OrganisationMembership.objects.filter(
            user=self.owner,
            organisation=self
        ).first()
        
        if existing:
            # Update role to OWNER if not already
            if existing.role != 'OWNER':
                existing.role = 'OWNER'
                existing.is_active = True
                existing.save(update_fields=['role', 'is_active'])
        else:
            # Create new membership
            OrganisationMembership.objects.create(
                user=self.owner,
                organisation=self,
                role='OWNER',
                is_active=True
            )

    def get_feature(self, key, default=True):
        """Get a feature flag value with a default. All features default to True (enabled)."""
        if not self.feature_flags:
            return default
        return self.feature_flags.get(key, default)

    @property
    def logo_display_url(self):
        """Return logo URL — uploaded file takes priority over external URL."""
        if self.logo:
            return self.logo.url
        return self.logo_url or ''

    @property
    def documents_limit(self):
        """Total docs allowed this month for the whole org."""
        if self.documents_per_month_override:
            return self.documents_per_month_override + self.extra_docs_purchased
        base = settings.SUBSCRIPTION_PLANS.get(self.plan, {}).get('documents_per_month', 10)
        return base + self.extra_docs_purchased

    @property
    def documents_remaining(self):
        self._check_monthly_reset()
        return max(0, self.documents_limit - self.documents_used_this_month)

    def increment_document_usage(self):
        self._check_monthly_reset()
        self.documents_used_this_month += 1
        self.save(update_fields=['documents_used_this_month'])

    def _check_monthly_reset(self):
        today = timezone.now().date()
        if not self.usage_reset_date or today.month != self.usage_reset_date.month or today.year != self.usage_reset_date.year:
            self.documents_used_this_month = 0
            self.extra_docs_purchased = 0
            self.usage_reset_date = today
            self.save(update_fields=['documents_used_this_month', 'extra_docs_purchased', 'usage_reset_date'])

    @property
    def is_trial(self):
        if self.status != 'TRIAL':
            return False
        if self.trial_ends_at and timezone.now() > self.trial_ends_at:
            return False
        return True

    def grant_sales_access(self, approved_by):
        """Grant sales access to this organisation (called by superuser)."""
        self.sales_access_enabled = True
        self.sales_access_approved_by = approved_by
        self.sales_access_approved_at = timezone.now()
        self.save(update_fields=['sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'])

    def revoke_sales_access(self):
        """Revoke sales access from this organisation."""
        self.sales_access_enabled = False
        self.sales_access_approved_by = None
        self.sales_access_approved_at = None
        self.save(update_fields=['sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'])

    @classmethod
    def find_auto_join_org(cls, email):
        """
        Find an organisation that allows auto-join for the given email domain.
        Used during registration to prompt users to join their team.
        """
        if '@' not in email:
            return None
        domain = email.split('@')[1].lower()
        return cls.objects.filter(
            domain=domain,
            auto_join_enabled=True,
            status='ACTIVE'
        ).first()


class Branch(models.Model):
    """
    A branch/office within an organisation.
    Can override the org logo for local branding.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True, help_text='Internal branch code')

    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Branding override (optional — falls back to org branding)
    logo = models.ImageField(upload_to='branch_logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True)
    primary_colour = models.CharField(max_length=7, blank=True, help_text='Leave blank to use org colour')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['organisation', 'name']
        unique_together = ['organisation', 'name']
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.organisation.name} — {self.name}"

    @property
    def logo_display_url(self):
        """Return branch logo, or fall back to org logo."""
        if self.logo:
            return self.logo.url
        if self.logo_url:
            return self.logo_url
        return self.organisation.logo_display_url

    @property
    def display_colour(self):
        """Return branch colour, or fall back to org colour."""
        return self.primary_colour or self.organisation.primary_colour


class OrganisationMembership(models.Model):
    """
    Links a user to an organisation with a specific role.
    A user can belong to multiple orgs (e.g. a consultant).
    """
    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('MEMBER', 'Member'),
        ('VIEWER', 'Viewer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='members')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'organisation']
        ordering = ['organisation', 'role']

    def __str__(self):
        branch_str = f" ({self.branch.name})" if self.branch else ""
        return f"{self.user.email} → {self.organisation.name}{branch_str} [{self.role}]"

    @property
    def can_manage(self):
        return self.role in ('OWNER', 'ADMIN', 'MANAGER')

    @property
    def can_admin(self):
        return self.role in ('OWNER', 'ADMIN')


class OrganisationInvitation(models.Model):
    """
    Invitation to join an organisation (Scenario 5: Direct Invitation).
    Sent by org admins to invite new staff members by email.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='invitations')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    email = models.EmailField(help_text='Email address of the person being invited')
    role = models.CharField(max_length=20, choices=OrganisationMembership.ROLE_CHOICES, default='MEMBER')
    
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='sent_invitations'
    )
    
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField()
    
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='accepted_invitations'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Invite {self.email} to {self.organisation.name} [{self.status}]"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status == 'PENDING' and not self.is_expired

    def send_invitation_email(self):
        """Send invitation email to the invitee."""
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        accept_url = f"https://signsimple.co.uk/invitation/{self.token}/"
        inviter_name = self.invited_by.full_name or self.invited_by.email if self.invited_by else 'An administrator'
        org = self.organisation
        role = self.get_role_display()
        branch_text = f" ({self.branch.name})" if self.branch else ""
        
        subject = f"You're invited to join {org.name} on SignSimple"
        message = f"""Hi,

{inviter_name} has invited you to join {org.name}{branch_text} as a {role} on SignSimple.

Click the link below to accept: {accept_url}

This invitation will expire in 7 days.

Best regards,
The SignSimple Team
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

    def accept(self, user):
        """Accept the invitation and add user to organisation."""
        existing = OrganisationMembership.objects.filter(
            user=user, organisation=self.organisation
        ).first()
        
        if existing:
            self.status = 'ACCEPTED'
            self.accepted_by = user
            self.accepted_at = timezone.now()
            self.save()
            return existing
        
        membership = OrganisationMembership.objects.create(
            user=user,
            organisation=self.organisation,
            branch=self.branch,
            role=self.role,
        )
        
        self.status = 'ACCEPTED'
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save()
        
        return membership


class OrganisationRequest(models.Model):
    """
    Request to create a new organisation.
    Users submit this form, then verify their work email.
    Auto-approved if domain matches, otherwise requires admin review.
    """
    STATUS_CHOICES = (
        ('PENDING_WORK_EMAIL', 'Pending Work Email Verification'),
        ('PENDING_APPROVAL', 'Pending Admin Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='organisation_requests',
    )
    
    organisation_name = models.CharField(max_length=255)
    organisation_domain = models.CharField(max_length=255)
    company_number = models.CharField(max_length=20, blank=True)
    
    work_email = models.EmailField()
    work_email_verified = models.BooleanField(default=False)
    work_email_verification_token = models.UUIDField(default=uuid.uuid4)
    work_email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    work_email_verified_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_WORK_EMAIL')
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_org_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    organisation = models.OneToOneField(
        Organisation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='source_request'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organisation_name} (by {self.requested_by.email}) - {self.get_status_display()}"

    @property
    def work_email_domain(self):
        if '@' in self.work_email:
            return self.work_email.split('@')[1].lower()
        return ''

    @property
    def domain_matches(self):
        return self.work_email_domain == self.organisation_domain.lower()

    @property
    def can_auto_approve(self):
        return self.work_email_verified and self.domain_matches

    def send_work_email_verification(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        self.work_email_verification_token = uuid.uuid4()
        self.work_email_verification_sent_at = timezone.now()
        self.save(update_fields=['work_email_verification_token', 'work_email_verification_sent_at'])
        
        verification_url = f"https://signsimple.co.uk/api/organisations/verify-work-email/{self.work_email_verification_token}/"
        
        subject = f"Verify your work email for {self.organisation_name}"
        message = f"""Hi,

You've requested to create "{self.organisation_name}" on SignSimple.

Click here to verify: {verification_url}

This link expires in 7 days.

Best regards,
The SignSimple Team
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.work_email],
            fail_silently=False,
        )

    def verify_work_email(self):
        self.work_email_verified = True
        self.work_email_verified_at = timezone.now()
        
        if self.can_auto_approve:
            self.status = 'APPROVED'
            self._create_organisation()
        else:
            self.status = 'PENDING_APPROVAL'
            self._notify_admins_for_review()
        
        self.save()

    def approve(self, reviewed_by):
        self.status = 'APPROVED'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self._create_organisation()
        self.save()
        self._send_approval_email()

    def reject(self, reviewed_by, reason=''):
        self.status = 'REJECTED'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        self._send_rejection_email()

    def _create_organisation(self):
        from django.utils.text import slugify
        
        base_slug = slugify(self.organisation_name)
        slug = base_slug
        counter = 1
        while Organisation.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        org = Organisation.objects.create(
            name=self.organisation_name,
            slug=slug,
            domain=self.organisation_domain,
            company_number=self.company_number,
            owner=self.requested_by,
            status='ACTIVE',
        )
        
        # Note: Organisation.save() now auto-creates owner membership
        # but we explicitly create it here anyway for clarity
        OrganisationMembership.objects.get_or_create(
            user=self.requested_by,
            organisation=org,
            defaults={'role': 'OWNER'}
        )
        
        self.organisation = org
        self._send_approval_email()

    def _notify_admins_for_review(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        from authentication.models import User
        
        admins = User.objects.filter(is_superuser=True, is_active=True)
        admin_emails = [a.email for a in admins]
        
        if admin_emails:
            subject = f"[ACTION REQUIRED] Organisation request: {self.organisation_name}"
            message = f"""Review needed for: {self.organisation_name}
Requested by: {self.requested_by.email}
Work email: {self.work_email} (domain mismatch)

Review at: https://signsimple.co.uk/admin/organisations/organisationrequest/{self.id}/change/
"""
            send_mail(subject, message, django_settings.DEFAULT_FROM_EMAIL, admin_emails, fail_silently=True)

    def _send_approval_email(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        name = self.requested_by.full_name.split()[0] if self.requested_by.full_name else 'there'
        subject = f"🎉 {self.organisation_name} is approved!"
        message = f"""Hi {name},

Your organisation "{self.organisation_name}" has been approved!

Get started: https://signsimple.co.uk/dashboard

Best regards,
The SignSimple Team
"""
        send_mail(subject, message, django_settings.DEFAULT_FROM_EMAIL, [self.requested_by.email], fail_silently=True)

    def _send_rejection_email(self):
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        
        subject = f"Organisation request not approved"
        reason = f"\nReason: {self.rejection_reason}" if self.rejection_reason else ""
        message = f"""Hi,

Your request for "{self.organisation_name}" was not approved.{reason}

Contact support@avyangah.co.uk if you have questions.

Best regards,
The SignSimple Team
"""
        send_mail(subject, message, django_settings.DEFAULT_FROM_EMAIL, [self.requested_by.email], fail_silently=True)
