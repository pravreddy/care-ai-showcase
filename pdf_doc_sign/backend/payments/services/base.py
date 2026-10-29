"""
Base Payment Provider Interface.
All payment providers must implement this interface.
Swap providers by changing env vars — zero code changes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PaymentMethod(Enum):
    OPEN_BANKING = 'open_banking'
    CARD = 'card'
    DIRECT_DEBIT = 'direct_debit'


class PaymentType(Enum):
    ONE_TIME = 'one_time'
    SUBSCRIPTION = 'subscription'


@dataclass
class CheckoutRequest:
    """Standardised checkout request — same format regardless of provider."""
    user_id: str
    user_email: str
    amount_pence: int          # Always in pence (£2.50 = 250)
    currency: str = 'GBP'
    description: str = ''
    plan: str = ''             # 'STARTER', 'PROFESSIONAL', or '' for one-off
    payment_type: PaymentType = PaymentType.ONE_TIME
    success_url: str = ''
    cancel_url: str = ''
    metadata: Optional[dict] = None


@dataclass
class CheckoutResponse:
    """Standardised checkout response."""
    provider: str              # 'truelayer', 'stripe'
    payment_method: PaymentMethod
    checkout_url: str          # URL to redirect the user to
    payment_id: str            # Provider's payment/session ID
    status: str = 'pending'
    raw_response: Optional[dict] = None


@dataclass
class PaymentStatus:
    """Standardised payment status."""
    provider: str
    payment_id: str
    status: str                # 'pending', 'succeeded', 'failed', 'refunded'
    amount_pence: int
    currency: str
    paid_at: Optional[str] = None
    failure_reason: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class WebhookEvent:
    """Standardised webhook event."""
    provider: str
    event_type: str            # 'payment.succeeded', 'payment.failed', 'subscription.cancelled'
    payment_id: str
    user_email: Optional[str] = None
    amount_pence: Optional[int] = None
    metadata: Optional[dict] = None
    raw_event: Optional[dict] = None


class PaymentProviderBase(ABC):
    """
    Abstract base class for all payment providers.
    Implement this to add a new provider (Stripe, TrueLayer, GoCardless, etc.)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g. 'stripe', 'truelayer')."""
        ...

    @property
    @abstractmethod
    def payment_method(self) -> PaymentMethod:
        """Return the payment method this provider handles."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this provider has valid credentials."""
        ...

    @abstractmethod
    def create_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Create a checkout session and return a URL for the user to pay."""
        ...

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Check the status of a payment."""
        ...

    @abstractmethod
    def verify_webhook(self, headers: dict, body: bytes) -> WebhookEvent:
        """Verify and parse a webhook from this provider."""
        ...

    def create_subscription_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Create a subscription checkout. Override if provider supports it."""
        request.payment_type = PaymentType.SUBSCRIPTION
        return self.create_checkout(request)

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription. Override if provider supports it."""
        raise NotImplementedError(f'{self.provider_name} does not support subscriptions')

    def refund_payment(self, payment_id: str, amount_pence: Optional[int] = None) -> bool:
        """Refund a payment. Override if provider supports it."""
        raise NotImplementedError(f'{self.provider_name} does not support refunds')
