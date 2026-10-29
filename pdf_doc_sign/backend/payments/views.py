"""
Payment API Views - DocSign UK
Handles checkout, webhooks, and payment status for all providers.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User
from subscriptions.models import Subscription, Payment, ExtraDocsPurchase
from .serializers import CheckoutSerializer
from .services.base import CheckoutRequest, PaymentType, PaymentMethod
from .services.factory import (
    get_payment_provider, get_available_providers,
    get_open_banking_provider, get_card_provider,
)

logger = logging.getLogger('payments')


class AvailableProvidersView(APIView):
    """GET /api/payments/providers/ — which payment methods are available."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response(get_available_providers())


class PlansView(APIView):
    """GET /api/payments/plans/ — list all subscription plans with pricing."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        plans = settings.SUBSCRIPTION_PLANS
        extra = {
            'price_gbp': float(settings.EXTRA_DOCS_PRICE_GBP),
            'bundle_size': settings.EXTRA_DOCS_BUNDLE_SIZE,
            'description': f'£{settings.EXTRA_DOCS_PRICE_GBP} per extra {settings.EXTRA_DOCS_BUNDLE_SIZE} documents',
        }
        return Response({
            'plans': {k: {**v, 'price_gbp': float(v['price_gbp'])} for k, v in plans.items()},
            'extra_docs': extra,
            'currency': 'GBP',
        })


class CheckoutView(APIView):
    """
    POST /api/payments/checkout/
    Create a checkout session with the chosen provider.

    Body:
      plan: STARTER | PROFESSIONAL | EXTRA_DOCS
      payment_method: open_banking | card
      quantity: 1 (for EXTRA_DOCS bundles)
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        plan = data['plan']
        method = data['payment_method']
        quantity = data.get('quantity', 1)

        # Calculate amount
        if plan == 'EXTRA_DOCS':
            amount_pence = int(settings.EXTRA_DOCS_PRICE_GBP * 100) * quantity
            description = f'{quantity * settings.EXTRA_DOCS_BUNDLE_SIZE} extra documents'
            payment_type = PaymentType.ONE_TIME
        else:
            plan_info = settings.SUBSCRIPTION_PLANS.get(plan)
            if not plan_info:
                return Response({'error': f'Unknown plan: {plan}'}, status=400)
            if plan_info['price_gbp'] == 0:
                return Response({'error': 'Free plan does not require payment'}, status=400)
            amount_pence = int(plan_info['price_gbp'] * 100)
            description = f"{plan_info['name']} Plan - {plan_info['documents_per_month']} docs/month"
            payment_type = PaymentType.SUBSCRIPTION

        # Get the provider
        try:
            provider = get_payment_provider(method)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        if not provider.is_configured():
            return Response(
                {'error': f'{method} payments are not available. Try another method.'},
                status=400,
            )

        # Build callback URLs
        base_url = request.build_absolute_uri('/')[:-1]
        frontend_url = settings.OAUTH_FRONTEND_CALLBACK_URL.replace('/oauth/callback', '')

        checkout_req = CheckoutRequest(
            user_id=str(user.id),
            user_email=user.email,
            amount_pence=amount_pence,
            currency='GBP',
            description=description,
            plan=plan,
            payment_type=payment_type,
            success_url=f'{frontend_url}/payment/success',
            cancel_url=f'{frontend_url}/payment/cancel',
            metadata={
                'user_id': str(user.id),
                'plan': plan,
                'quantity': str(quantity),
            },
        )

        try:
            checkout_resp = provider.create_checkout(checkout_req)
        except Exception as e:
            logger.error(f'[PAYMENTS] Checkout failed: {e}')
            return Response({'error': 'Payment initiation failed. Please try again.'}, status=500)

        # Record pending payment
        Payment.objects.create(
            user=user,
            amount=amount_pence / 100,
            currency='GBP',
            status='PENDING',
            payment_method='BANK_TRANSFER' if method == 'open_banking' else 'CARD',
            payment_provider=provider.provider_name,
            provider_payment_id=checkout_resp.payment_id,
            description=description,
        )

        return Response({
            'checkout_url': checkout_resp.checkout_url,
            'payment_id': checkout_resp.payment_id,
            'provider': checkout_resp.provider,
            'payment_method': checkout_resp.payment_method.value,
        })


class PaymentStatusView(APIView):
    """GET /api/payments/status/<payment_id>/ — check payment status."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, payment_id):
        # Find in our DB first
        try:
            payment = Payment.objects.get(
                provider_payment_id=payment_id,
                user=request.user,
            )
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)

        # Check with provider for latest status
        try:
            provider = get_payment_provider(
                'open_banking' if payment.payment_provider == 'truelayer' else 'card'
            )
            ps = provider.get_payment_status(payment_id)

            return Response({
                'payment_id': payment_id,
                'provider': payment.payment_provider,
                'status': ps.status,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'description': payment.description,
                'created_at': payment.created_at,
            })
        except Exception as e:
            logger.error(f'[PAYMENTS] Status check failed: {e}')
            return Response({
                'payment_id': payment_id,
                'status': payment.status.lower(),
                'amount': float(payment.amount),
            })


@method_decorator(csrf_exempt, name='dispatch')
class TrueLayerWebhookView(APIView):
    """POST /api/payments/webhook/truelayer/ — handle TrueLayer webhooks."""
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []

    def post(self, request):
        try:
            provider = get_open_banking_provider()
            event = provider.verify_webhook(
                headers=dict(request.headers),
                body=request.body,
            )
        except Exception as e:
            logger.error(f'[WEBHOOK] TrueLayer verification failed: {e}')
            return Response({'error': 'Invalid webhook'}, status=400)

        logger.info(f'[WEBHOOK] TrueLayer event: {event.event_type} for {event.payment_id}')
        _process_webhook_event(event)
        return Response({'received': True})


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """POST /api/payments/webhook/stripe/ — handle Stripe webhooks."""
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []

    def post(self, request):
        try:
            provider = get_card_provider()
            event = provider.verify_webhook(
                headers=dict(request.headers),
                body=request.body,
            )
        except Exception as e:
            logger.error(f'[WEBHOOK] Stripe verification failed: {e}')
            return Response({'error': 'Invalid webhook'}, status=400)

        logger.info(f'[WEBHOOK] Stripe event: {event.event_type} for {event.payment_id}')
        _process_webhook_event(event)
        return Response({'received': True})


def _process_webhook_event(event):
    """
    Process a standardised webhook event from any provider.
    This is the single place where payments → subscriptions/docs happen.
    """
    if event.event_type == 'payment.succeeded':
        _handle_payment_success(event)
    elif event.event_type == 'payment.failed':
        _handle_payment_failed(event)
    elif event.event_type == 'subscription.cancelled':
        _handle_subscription_cancelled(event)
    else:
        logger.info(f'[WEBHOOK] Unhandled event type: {event.event_type}')


def _handle_payment_success(event):
    """Payment succeeded — activate plan or add extra docs."""
    payment = Payment.objects.filter(
        provider_payment_id=event.payment_id,
    ).first()

    if not payment:
        # Try to find by Stripe session → payment intent
        if event.metadata:
            user_id = event.metadata.get('user_id')
            if user_id:
                payment = Payment.objects.filter(
                    user_id=user_id, status='PENDING',
                ).order_by('-created_at').first()

    if not payment:
        logger.warning(f'[WEBHOOK] No matching payment for {event.payment_id}')
        return

    # Update payment record
    payment.status = 'SUCCESS'
    payment.paid_at = timezone.now()
    payment.save()

    user = payment.user
    plan = event.metadata.get('plan', '') if event.metadata else ''

    if plan == 'EXTRA_DOCS':
        # Add extra documents
        quantity = int(event.metadata.get('quantity', 1))
        docs_to_add = quantity * settings.EXTRA_DOCS_BUNDLE_SIZE
        user.extra_docs_purchased += docs_to_add
        user.save(update_fields=['extra_docs_purchased'])

        ExtraDocsPurchase.objects.create(
            user=user,
            payment=payment,
            documents_added=docs_to_add,
            amount_gbp=payment.amount,
        )
        logger.info(f'[PAYMENT] {user.email} purchased {docs_to_add} extra docs')

    elif plan in ('STARTER', 'PROFESSIONAL'):
        # Upgrade subscription
        user.subscription_plan = plan
        user.save(update_fields=['subscription_plan'])

        Subscription.objects.create(
            user=user,
            plan=plan,
            status='ACTIVE',
            amount=payment.amount,
            currency='GBP',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            payment_provider=event.provider,
            payment_provider_subscription_id=event.payment_id,
        )
        logger.info(f'[PAYMENT] {user.email} upgraded to {plan}')


def _handle_payment_failed(event):
    """Payment failed — mark as failed."""
    Payment.objects.filter(
        provider_payment_id=event.payment_id,
    ).update(
        status='FAILED',
        failure_reason=event.metadata.get('failure_reason', 'Payment failed') if event.metadata else 'Payment failed',
    )
    logger.warning(f'[PAYMENT] Payment failed: {event.payment_id}')


def _handle_subscription_cancelled(event):
    """Subscription cancelled — downgrade to free."""
    if event.metadata and event.metadata.get('user_id'):
        try:
            user = User.objects.get(id=event.metadata['user_id'])
            user.subscription_plan = 'FREE'
            user.save(update_fields=['subscription_plan'])

            Subscription.objects.filter(
                user=user, status='ACTIVE',
            ).update(status='CANCELLED', cancelled_at=timezone.now())

            logger.info(f'[PAYMENT] {user.email} downgraded to FREE')
        except User.DoesNotExist:
            pass
