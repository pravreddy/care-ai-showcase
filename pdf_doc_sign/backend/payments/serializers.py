"""
Payment Serializers - DocSign UK
"""
from rest_framework import serializers


class CheckoutSerializer(serializers.Serializer):
    """Request to create a checkout session."""
    plan = serializers.ChoiceField(
        choices=['STARTER', 'PROFESSIONAL', 'EXTRA_DOCS'],
        help_text='Plan to purchase or EXTRA_DOCS for pay-as-you-go',
    )
    payment_method = serializers.ChoiceField(
        choices=['open_banking', 'card'],
        default='open_banking',
        help_text='Payment method: open_banking (Pay by Bank) or card',
    )
    quantity = serializers.IntegerField(
        default=1, min_value=1, max_value=100,
        help_text='For EXTRA_DOCS: how many bundles of 100 docs (£1 each)',
    )


class CheckoutResponseSerializer(serializers.Serializer):
    """Response with checkout URL."""
    checkout_url = serializers.URLField()
    payment_id = serializers.CharField()
    provider = serializers.CharField()
    payment_method = serializers.CharField()


class PaymentStatusSerializer(serializers.Serializer):
    """Payment status check."""
    payment_id = serializers.CharField()
    provider = serializers.CharField()
    status = serializers.CharField()
    amount_pence = serializers.IntegerField()
    currency = serializers.CharField()


class AvailableProvidersSerializer(serializers.Serializer):
    """Available payment providers."""
    open_banking = serializers.DictField()
    card = serializers.DictField()
