"""
Subscription & Coupon Serializers
"""
from rest_framework import serializers
from .models import Subscription, Coupon, CouponRedemption, Payment


class SubscriptionSerializer(serializers.ModelSerializer):
    days_remaining = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'start_date', 'end_date',
            'amount', 'currency', 'auto_renew', 'days_remaining',
            'is_active', 'created_at',
        ]


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'plan_granted', 'duration_days', 'price_gbp',
            'documents_included', 'ai_scans_included',
            'lead_first_name', 'lead_last_name', 'lead_email', 'lead_company',
            'source', 'description', 'max_uses', 'current_uses', 'status',
            'is_valid', 'days_until_expiry', 'expires_at',
            'email_sent', 'created_at',
        ]
        read_only_fields = ['id', 'code', 'current_uses', 'status', 'created_at']


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class CouponRedeemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class CouponRedemptionSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model = CouponRedemption
        fields = [
            'id', 'coupon_code', 'plan_granted',
            'valid_from', 'valid_until', 'amount_paid', 'redeemed_at',
        ]


class CouponGenerateSerializer(serializers.Serializer):
    """For admin/chatbot to generate a new coupon."""
    first_name = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)
    email = serializers.EmailField(required=False, default='')
    company = serializers.CharField(max_length=255, required=False, default='', allow_blank=True)
    plan = serializers.ChoiceField(choices=['STARTER', 'PROFESSIONAL'], default='STARTER')
    duration_days = serializers.IntegerField(default=180, min_value=30, max_value=365)
    price_gbp = serializers.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    documents_included = serializers.IntegerField(required=False, default=None, min_value=1, max_value=10000, allow_null=True)
    ai_scans_included = serializers.IntegerField(required=False, default=None, min_value=0, max_value=10000, allow_null=True)
    source = serializers.ChoiceField(
        choices=['CHATBOT', 'ADMIN', 'SALES', 'REFERRAL'], default='ADMIN'
    )


class SuperuserGrantSerializer(serializers.Serializer):
    """
    Superuser-only: grant free docs + AI scans to any user.
    Creates a coupon tied to that user's email and auto-redeems it.

    Usage:
      POST /api/coupons/grant-free/
      {
        "email": "sarah@sparkclean.co.uk",
        "documents": 100,
        "ai_scans": 100,
        "duration_days": 90,
        "description": "Free trial for demo"
      }
    """
    email = serializers.EmailField(help_text='User email to grant free access to')
    documents = serializers.IntegerField(
        default=100, min_value=1, max_value=10000,
        help_text='Number of free documents to grant'
    )
    ai_scans = serializers.IntegerField(
        default=100, min_value=0, max_value=10000,
        help_text='Number of free AI scans to grant'
    )
    duration_days = serializers.IntegerField(
        default=90, min_value=1, max_value=365,
        help_text='How long the free access lasts (days)'
    )
    plan = serializers.ChoiceField(
        choices=['STARTER', 'PROFESSIONAL'], default='STARTER',
        help_text='Which plan to grant'
    )
    description = serializers.CharField(
        max_length=500, required=False, default='', allow_blank=True,
        help_text='Internal note (e.g. "Demo for NHS trust")'
    )
