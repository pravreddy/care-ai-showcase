"""
Subscription, Payment & Coupon Models - SignSimple UK (GBP)
Operated by Avyangah Technologies Limited (08235853)
"""
import uuid
import secrets
import string
from django.db import models
from django.conf import settings
from django.utils import timezone


class Subscription(models.Model):
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('PAST_DUE', 'Past Due'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')

    payment_provider = models.CharField(max_length=50, blank=True)
    payment_provider_subscription_id = models.CharField(max_length=255, blank=True)
    payment_provider_customer_id = models.CharField(max_length=255, blank=True)

    # If this subscription was created by a coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"

    @property
    def is_active(self):
        return self.status == 'ACTIVE' and self.start_date <= timezone.now() <= self.end_date

    @property
    def days_remaining(self):
        if self.is_active:
            return (self.end_date - timezone.now()).days
        return 0

    def cancel(self):
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        self.save()


class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )
    METHOD_CHOICES = (
        ('CARD', 'Credit/Debit Card'),
        ('DIRECT_DEBIT', 'Direct Debit'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True)

    payment_provider = models.CharField(max_length=50, blank=True)
    provider_payment_id = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - £{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            now = timezone.now()
            count = Payment.objects.filter(
                created_at__year=now.year, created_at__month=now.month
            ).count() + 1
            self.invoice_number = f"PAY-{now.year}-{now.month:02d}-{count:05d}"
        super().save(*args, **kwargs)


class ExtraDocsPurchase(models.Model):
    """Track pay-as-you-go extra document purchases. £1 per 100 docs."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='extra_purchases')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    documents_added = models.IntegerField(default=100)
    amount_gbp = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} +{self.documents_added} docs (£{self.amount_gbp})"


# =============================================================
# Coupon System
# =============================================================
# Generated by chatbot or admin. Sent to lead via email.
# Redeemed at signup → creates Subscription with the coupon's plan.
#
# Flow:
#   1. Chatbot captures lead (name + email)
#   2. Generates unique coupon: SARAH-PRO6M-X7K2
#   3. Sends email via Postal/Brevo
#   4. Lead signs up at signsimple.co.uk/signup?coupon=SARAH-PRO6M-X7K2
#   5. Coupon validated → Subscription created → plan upgraded
# =============================================================

def _generate_coupon_code():
    """Generate a random 8-char alphanumeric suffix."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


class Coupon(models.Model):
    PLAN_CHOICES = (
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
    )
    SOURCE_CHOICES = (
        ('CHATBOT', 'AI Chatbot'),
        ('ADMIN', 'Platform Admin'),
        ('SALES', 'Sales Team'),
        ('REFERRAL', 'Customer Referral'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('REDEEMED', 'Redeemed'),
        ('EXPIRED', 'Expired'),
        ('DEACTIVATED', 'Deactivated'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The code itself — unique, uppercase, e.g. SARAH-STARTER6M-X7K2AB3D
    code = models.CharField(max_length=50, unique=True, db_index=True)

    # What the coupon grants
    plan_granted = models.CharField(max_length=20, choices=PLAN_CHOICES, default='STARTER')
    duration_days = models.IntegerField(
        default=180,
        help_text='How long the plan lasts (90=3mo, 180=6mo, 365=1yr)'
    )
    price_gbp = models.DecimalField(
        max_digits=10, decimal_places=2, default=1.00,
        help_text='What the user pays to activate (£1 for chatbot offers)'
    )

    # Includes (bundled: docs + AI scans)
    documents_included = models.IntegerField(
        default=100,
        help_text='Number of document signatures included'
    )
    ai_scans_included = models.IntegerField(
        default=100,
        help_text='Number of AI detector scans included'
    )

    # Who this coupon was generated for
    lead_first_name = models.CharField(max_length=100, blank=True)
    lead_last_name = models.CharField(max_length=100, blank=True)
    lead_email = models.EmailField(blank=True, db_index=True)
    lead_company = models.CharField(max_length=255, blank=True)

    # Where it came from
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='CHATBOT')
    description = models.TextField(blank=True)

    # Organisation scope (optional — for org-level coupons)
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='coupons',
    )

    # Usage limits
    max_uses = models.IntegerField(
        default=1,
        help_text='1 for personal coupons, N for org-wide codes'
    )
    current_uses = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Urgency — coupon expires in N days (7 days for chatbot offers)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the coupon code itself expires (not the subscription)'
    )

    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='coupons_created',
    )
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['lead_email']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        name = f"{self.lead_first_name} {self.lead_last_name}".strip() or self.lead_email
        return f"{self.code} → {self.plan_granted} ({name})"

    @property
    def is_valid(self):
        """Check if this coupon can still be redeemed."""
        if self.status != 'ACTIVE':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

    @property
    def days_until_expiry(self):
        if not self.expires_at:
            return None
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    @classmethod
    def generate_code(cls, first_name='', plan='STARTER', duration_days=180):
        """
        Generate a unique, memorable coupon code.
        Format: NAME-PLAN-DURATION-RANDOM
        e.g. SARAH-STARTER6M-X7K2AB3D
        """
        name_part = first_name.upper()[:6] if first_name else 'GUEST'

        if duration_days <= 90:
            dur = '3M'
        elif duration_days <= 180:
            dur = '6M'
        else:
            dur = '12M'

        plan_short = plan[:4].upper()  # STAR or PROF
        suffix = _generate_coupon_code()

        code = f"{name_part}-{plan_short}{dur}-{suffix}"

        # Ensure uniqueness
        while cls.objects.filter(code=code).exists():
            suffix = _generate_coupon_code()
            code = f"{name_part}-{plan_short}{dur}-{suffix}"

        return code


class CouponRedemption(models.Model):
    """Track who redeemed which coupon and when."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_redemptions')
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='The subscription created by this redemption'
    )

    # What was granted
    plan_granted = models.CharField(max_length=20)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)

    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-redeemed_at']
        unique_together = ('coupon', 'user')  # One redemption per user per coupon

    def __str__(self):
        return f"{self.user.email} redeemed {self.coupon.code}"
