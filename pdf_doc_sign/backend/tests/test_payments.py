"""
Payment Tests - DocSign UK
Unit tests for payment providers + integration tests for API endpoints.
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient

from authentication.models import User
from subscriptions.models import Payment, Subscription, ExtraDocsPurchase
from payments.services.base import (
    CheckoutRequest, CheckoutResponse, PaymentType, PaymentMethod, PaymentStatus,
)
from payments.services.factory import get_available_providers, get_payment_provider
from payments.services.truelayer import TrueLayerProvider
from payments.services.stripe_service import StripeProvider


# ============================================================
# Unit Tests: Payment Provider Base
# ============================================================

class TestCheckoutRequest(TestCase):
    """Test the standardised checkout request model."""

    def test_one_time_request(self):
        req = CheckoutRequest(
            user_id='test-uuid', user_email='test@example.com',
            amount_pence=250, description='Starter Plan',
        )
        self.assertEqual(req.amount_pence, 250)
        self.assertEqual(req.currency, 'GBP')
        self.assertEqual(req.payment_type, PaymentType.ONE_TIME)

    def test_subscription_request(self):
        req = CheckoutRequest(
            user_id='test-uuid', user_email='test@example.com',
            amount_pence=1000, plan='PROFESSIONAL',
            payment_type=PaymentType.SUBSCRIPTION,
        )
        self.assertEqual(req.payment_type, PaymentType.SUBSCRIPTION)
        self.assertEqual(req.plan, 'PROFESSIONAL')


# ============================================================
# Unit Tests: TrueLayer Provider
# ============================================================

class TestTrueLayerProvider(TestCase):
    """Test TrueLayer provider without making real API calls."""

    def test_provider_name(self):
        provider = TrueLayerProvider()
        self.assertEqual(provider.provider_name, 'truelayer')
        self.assertEqual(provider.payment_method, PaymentMethod.OPEN_BANKING)

    @override_settings(TRUELAYER_CLIENT_ID='', TRUELAYER_CLIENT_SECRET='')
    def test_not_configured(self):
        provider = TrueLayerProvider()
        self.assertFalse(provider.is_configured())

    @override_settings(TRUELAYER_CLIENT_ID='test-id', TRUELAYER_CLIENT_SECRET='test-secret')
    def test_configured(self):
        provider = TrueLayerProvider()
        self.assertTrue(provider.is_configured())

    @override_settings(
        TRUELAYER_CLIENT_ID='test-id',
        TRUELAYER_CLIENT_SECRET='test-secret',
        TRUELAYER_SANDBOX=True,
        TRUELAYER_MERCHANT_ACCOUNT_ID='merchant-123',
    )
    @patch('payments.services.truelayer.requests.post')
    def test_create_checkout(self, mock_post):
        """Test checkout creation with mocked TrueLayer API."""
        # Mock auth token response
        mock_auth = MagicMock()
        mock_auth.json.return_value = {'access_token': 'test-token'}
        mock_auth.raise_for_status.return_value = None

        # Mock payment creation response
        mock_payment = MagicMock()
        mock_payment.status_code = 201
        mock_payment.json.return_value = {
            'id': 'payment-123',
            'resource_token': 'rt-456',
            'status': 'authorization_required',
        }

        mock_post.side_effect = [mock_auth, mock_payment]

        provider = TrueLayerProvider()
        req = CheckoutRequest(
            user_id='user-1', user_email='test@test.com',
            amount_pence=250, description='Starter Plan',
            success_url='http://localhost:3001/payment/success',
        )

        result = provider.create_checkout(req)

        self.assertEqual(result.provider, 'truelayer')
        self.assertEqual(result.payment_id, 'payment-123')
        self.assertIn('payment-123', result.checkout_url)
        self.assertEqual(result.payment_method, PaymentMethod.OPEN_BANKING)

    @override_settings(
        TRUELAYER_CLIENT_ID='test-id',
        TRUELAYER_CLIENT_SECRET='test-secret',
        TRUELAYER_SANDBOX=True,
    )
    @patch('payments.services.truelayer.requests.post')
    @patch('payments.services.truelayer.requests.get')
    def test_get_payment_status(self, mock_get, mock_post):
        """Test payment status check."""
        mock_auth = MagicMock()
        mock_auth.json.return_value = {'access_token': 'test-token'}
        mock_auth.raise_for_status.return_value = None
        mock_post.return_value = mock_auth

        mock_status = MagicMock()
        mock_status.json.return_value = {
            'status': 'executed',
            'amount_in_minor': 250,
            'currency': 'GBP',
        }
        mock_status.raise_for_status.return_value = None
        mock_get.return_value = mock_status

        provider = TrueLayerProvider()
        status = provider.get_payment_status('payment-123')

        self.assertEqual(status.status, 'succeeded')
        self.assertEqual(status.amount_pence, 250)


# ============================================================
# Unit Tests: Stripe Provider
# ============================================================

class TestStripeProvider(TestCase):
    """Test Stripe provider without making real API calls."""

    def test_provider_name(self):
        provider = StripeProvider()
        self.assertEqual(provider.provider_name, 'stripe')
        self.assertEqual(provider.payment_method, PaymentMethod.CARD)

    @override_settings(STRIPE_SECRET_KEY='', STRIPE_PUBLISHABLE_KEY='')
    def test_not_configured(self):
        provider = StripeProvider()
        self.assertFalse(provider.is_configured())

    @override_settings(STRIPE_SECRET_KEY='sk_test_xxx', STRIPE_PUBLISHABLE_KEY='pk_test_xxx')
    def test_configured(self):
        provider = StripeProvider()
        self.assertTrue(provider.is_configured())

    @override_settings(
        STRIPE_SECRET_KEY='sk_test_xxx',
        STRIPE_PUBLISHABLE_KEY='pk_test_xxx',
    )
    @patch('payments.services.stripe_service.stripe.checkout.Session.create')
    def test_create_one_time_checkout(self, mock_create):
        """Test Stripe one-time payment checkout."""
        mock_create.return_value = MagicMock(
            id='cs_test_123',
            url='https://checkout.stripe.com/cs_test_123',
            status='open',
        )

        provider = StripeProvider()
        req = CheckoutRequest(
            user_id='user-1', user_email='test@test.com',
            amount_pence=100, description='Extra Documents',
            success_url='http://localhost:3001/payment/success',
            cancel_url='http://localhost:3001/payment/cancel',
        )

        result = provider.create_checkout(req)

        self.assertEqual(result.provider, 'stripe')
        self.assertEqual(result.payment_id, 'cs_test_123')
        self.assertEqual(result.payment_method, PaymentMethod.CARD)
        mock_create.assert_called_once()


# ============================================================
# Unit Tests: Provider Factory
# ============================================================

class TestProviderFactory(TestCase):
    """Test provider factory and availability detection."""

    def test_get_available_providers(self):
        providers = get_available_providers()
        self.assertIn('open_banking', providers)
        self.assertIn('card', providers)
        self.assertEqual(providers['open_banking']['provider'], 'truelayer')
        self.assertEqual(providers['card']['provider'], 'stripe')

    def test_get_provider_by_method(self):
        ob = get_payment_provider('open_banking')
        self.assertEqual(ob.provider_name, 'truelayer')

        card = get_payment_provider('card')
        self.assertEqual(card.provider_name, 'stripe')

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            get_payment_provider('bitcoin')


# ============================================================
# Integration Tests: API Endpoints
# ============================================================

class PaymentAPITestBase(APITestCase):
    """Base class with test user setup."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@avyangah.co.uk',
            password='TestPass123!',
            full_name='Test User',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


class TestPlansAPI(PaymentAPITestBase):
    """Test the plans listing endpoint."""

    def test_list_plans(self):
        response = self.client.get('/api/payments/plans/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('plans', data)
        self.assertIn('FREE', data['plans'])
        self.assertIn('STARTER', data['plans'])
        self.assertIn('PROFESSIONAL', data['plans'])
        self.assertEqual(data['plans']['STARTER']['price_gbp'], 2.5)
        self.assertEqual(data['plans']['PROFESSIONAL']['price_gbp'], 10.0)
        self.assertEqual(data['currency'], 'GBP')

    def test_plans_public_access(self):
        """Plans should be accessible without auth."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/payments/plans/')
        self.assertEqual(response.status_code, 200)


class TestProvidersAPI(PaymentAPITestBase):
    """Test the available providers endpoint."""

    def test_list_providers(self):
        response = self.client.get('/api/payments/providers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('open_banking', data)
        self.assertIn('card', data)

    def test_providers_public_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/payments/providers/')
        self.assertEqual(response.status_code, 200)


class TestCheckoutAPI(PaymentAPITestBase):
    """Test the checkout endpoint."""

    def test_checkout_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/payments/checkout/', {
            'plan': 'STARTER', 'payment_method': 'card',
        })
        self.assertEqual(response.status_code, 401)

    def test_checkout_free_plan_rejected(self):
        """Can't checkout for the free plan."""
        response = self.client.post('/api/payments/checkout/', {
            'plan': 'FREE', 'payment_method': 'card',
        })
        self.assertEqual(response.status_code, 400)

    def test_checkout_invalid_plan_rejected(self):
        response = self.client.post('/api/payments/checkout/', {
            'plan': 'INVALID', 'payment_method': 'card',
        })
        self.assertEqual(response.status_code, 400)

    def test_checkout_invalid_method_rejected(self):
        response = self.client.post('/api/payments/checkout/', {
            'plan': 'STARTER', 'payment_method': 'bitcoin',
        })
        self.assertEqual(response.status_code, 400)


class TestPaymentStatusAPI(PaymentAPITestBase):
    """Test the payment status endpoint."""

    def test_status_not_found(self):
        response = self.client.get('/api/payments/status/nonexistent/')
        self.assertEqual(response.status_code, 404)

    def test_status_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/payments/status/test-id/')
        self.assertEqual(response.status_code, 401)


# ============================================================
# Integration Tests: Webhook Processing
# ============================================================

class TestWebhookProcessing(TestCase):
    """Test the webhook event processing logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='webhook@test.com', password='TestPass123!',
            full_name='Webhook Test',
        )

    def test_payment_success_upgrades_plan(self):
        """When a payment succeeds, user plan should be upgraded."""
        from payments.views import _handle_payment_success
        from payments.services.base import WebhookEvent

        # Create pending payment
        payment = Payment.objects.create(
            user=self.user, amount=Decimal('2.50'), currency='GBP',
            status='PENDING', payment_provider='stripe',
            provider_payment_id='cs_test_webhook',
            description='Starter Plan',
        )

        event = WebhookEvent(
            provider='stripe',
            event_type='payment.succeeded',
            payment_id='cs_test_webhook',
            metadata={'user_id': str(self.user.id), 'plan': 'STARTER', 'quantity': '1'},
        )

        _handle_payment_success(event)

        # Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'SUCCESS')
        self.assertIsNotNone(payment.paid_at)

        # Verify user plan upgraded
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_plan, 'STARTER')

        # Verify subscription created
        sub = Subscription.objects.filter(user=self.user, plan='STARTER').first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.status, 'ACTIVE')

    def test_extra_docs_purchase(self):
        """When extra docs payment succeeds, user gets more documents."""
        from payments.views import _handle_payment_success
        from payments.services.base import WebhookEvent

        payment = Payment.objects.create(
            user=self.user, amount=Decimal('1.00'), currency='GBP',
            status='PENDING', payment_provider='truelayer',
            provider_payment_id='tl_test_extra',
        )

        event = WebhookEvent(
            provider='truelayer',
            event_type='payment.succeeded',
            payment_id='tl_test_extra',
            metadata={'user_id': str(self.user.id), 'plan': 'EXTRA_DOCS', 'quantity': '2'},
        )

        _handle_payment_success(event)

        self.user.refresh_from_db()
        self.assertEqual(self.user.extra_docs_purchased, 200)  # 2 bundles × 100

        purchase = ExtraDocsPurchase.objects.filter(user=self.user).first()
        self.assertIsNotNone(purchase)
        self.assertEqual(purchase.documents_added, 200)

    def test_payment_failed_updates_status(self):
        """When a payment fails, record should be marked as failed."""
        from payments.views import _handle_payment_failed
        from payments.services.base import WebhookEvent

        payment = Payment.objects.create(
            user=self.user, amount=Decimal('2.50'), currency='GBP',
            status='PENDING', provider_payment_id='cs_fail_test',
        )

        event = WebhookEvent(
            provider='stripe',
            event_type='payment.failed',
            payment_id='cs_fail_test',
            metadata={'failure_reason': 'Insufficient funds'},
        )

        _handle_payment_failed(event)

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'FAILED')
