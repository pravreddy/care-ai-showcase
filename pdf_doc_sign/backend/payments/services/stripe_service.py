"""
Stripe Payment Provider.
Handles credit/debit card payments and subscriptions.

Docs: https://stripe.com/docs/api
"""
import json
import logging
from typing import Optional

import stripe
from django.conf import settings

from .base import (
    PaymentProviderBase, PaymentMethod, PaymentType,
    CheckoutRequest, CheckoutResponse, PaymentStatus, WebhookEvent,
)

logger = logging.getLogger('payments.stripe')


class StripeProvider(PaymentProviderBase):
    """Stripe payment provider for card payments and subscriptions."""

    def __init__(self):
        self.secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.publishable_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        # Price IDs from Stripe Dashboard
        self.price_ids = {
            'STARTER': getattr(settings, 'STRIPE_PRICE_STARTER', ''),
            'PROFESSIONAL': getattr(settings, 'STRIPE_PRICE_PROFESSIONAL', ''),
            'EXTRA_DOCS': getattr(settings, 'STRIPE_PRICE_EXTRA_DOCS', ''),
        }

        if self.secret_key:
            stripe.api_key = self.secret_key

    @property
    def provider_name(self) -> str:
        return 'stripe'

    @property
    def payment_method(self) -> PaymentMethod:
        return PaymentMethod.CARD

    def is_configured(self) -> bool:
        return bool(self.secret_key and self.publishable_key)

    def create_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """
        Create a Stripe Checkout Session.
        For subscriptions: uses Stripe Price IDs.
        For one-off: creates a payment intent.
        """
        if not self.is_configured():
            raise PaymentError('Stripe is not configured')

        try:
            if request.payment_type == PaymentType.SUBSCRIPTION:
                return self._create_subscription_checkout(request)
            else:
                return self._create_one_time_checkout(request)
        except stripe.error.StripeError as e:
            logger.error(f'[STRIPE] Checkout error: {e}')
            raise PaymentError(f'Stripe error: {str(e)}')

    def _create_one_time_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Create a one-time payment checkout (e.g. extra docs)."""
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer_email=request.user_email,
            line_items=[{
                'price_data': {
                    'currency': request.currency.lower(),
                    'unit_amount': request.amount_pence,
                    'product_data': {
                        'name': request.description or 'Extra Documents',
                    },
                },
                'quantity': 1,
            }],
            metadata={
                'user_id': request.user_id,
                'plan': request.plan,
                'payment_type': 'one_time',
                **(request.metadata or {}),
            },
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
        )

        logger.info(f'[STRIPE] One-time checkout created: {session.id}')

        return CheckoutResponse(
            provider='stripe',
            payment_method=PaymentMethod.CARD,
            checkout_url=session.url,
            payment_id=session.id,
            status='pending',
            raw_response={'session_id': session.id},
        )

    def _create_subscription_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Create a subscription checkout using Stripe Price IDs."""
        price_id = self.price_ids.get(request.plan)
        if not price_id:
            raise PaymentError(f'No Stripe Price ID configured for plan: {request.plan}')

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            customer_email=request.user_email,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            metadata={
                'user_id': request.user_id,
                'plan': request.plan,
                'payment_type': 'subscription',
                **(request.metadata or {}),
            },
            subscription_data={
                'metadata': {
                    'user_id': request.user_id,
                    'plan': request.plan,
                },
            },
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
        )

        logger.info(f'[STRIPE] Subscription checkout created: {session.id} for plan {request.plan}')

        return CheckoutResponse(
            provider='stripe',
            payment_method=PaymentMethod.CARD,
            checkout_url=session.url,
            payment_id=session.id,
            status='pending',
            raw_response={'session_id': session.id},
        )

    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Check Stripe payment/session status."""
        if not self.is_configured():
            raise PaymentError('Stripe is not configured')

        try:
            session = stripe.checkout.Session.retrieve(payment_id)

            status_map = {
                'complete': 'succeeded',
                'expired': 'failed',
                'open': 'pending',
            }

            return PaymentStatus(
                provider='stripe',
                payment_id=payment_id,
                status=status_map.get(session.status, 'unknown'),
                amount_pence=session.amount_total or 0,
                currency=session.currency or 'gbp',
                raw_response=dict(session),
            )
        except stripe.error.StripeError as e:
            raise PaymentError(f'Stripe error: {str(e)}')

    def verify_webhook(self, headers: dict, body: bytes) -> WebhookEvent:
        """Verify Stripe webhook signature and parse event."""
        sig_header = headers.get('Stripe-Signature', '')

        if not self.webhook_secret:
            logger.warning('[STRIPE] Webhook received but no webhook secret configured')
            event = json.loads(body)
        else:
            try:
                event = stripe.Webhook.construct_event(body, sig_header, self.webhook_secret)
            except (ValueError, stripe.error.SignatureVerificationError) as e:
                logger.error(f'[STRIPE] Webhook verification failed: {e}')
                raise PaymentError(f'Webhook verification failed: {str(e)}')

        event_type = event.get('type', '')
        data_obj = event.get('data', {}).get('object', {})
        metadata = data_obj.get('metadata', {})

        # Map Stripe event types to our standard
        type_map = {
            'checkout.session.completed': 'payment.succeeded',
            'invoice.paid': 'payment.succeeded',
            'invoice.payment_failed': 'payment.failed',
            'customer.subscription.updated': 'subscription.updated',
            'customer.subscription.deleted': 'subscription.cancelled',
        }

        return WebhookEvent(
            provider='stripe',
            event_type=type_map.get(event_type, event_type),
            payment_id=data_obj.get('id', ''),
            user_email=data_obj.get('customer_email') or data_obj.get('customer_details', {}).get('email'),
            amount_pence=data_obj.get('amount_total') or data_obj.get('amount_paid'),
            metadata=metadata,
            raw_event=dict(event) if isinstance(event, dict) else event,
        )

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a Stripe subscription."""
        try:
            stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            logger.info(f'[STRIPE] Subscription cancelled: {subscription_id}')
            return True
        except stripe.error.StripeError as e:
            logger.error(f'[STRIPE] Cancel failed: {e}')
            return False

    def refund_payment(self, payment_id: str, amount_pence: Optional[int] = None) -> bool:
        """Refund a Stripe payment."""
        try:
            params = {'payment_intent': payment_id}
            if amount_pence:
                params['amount'] = amount_pence
            stripe.Refund.create(**params)
            logger.info(f'[STRIPE] Refund initiated for {payment_id}')
            return True
        except stripe.error.StripeError as e:
            logger.error(f'[STRIPE] Refund failed: {e}')
            return False


class PaymentError(Exception):
    pass
