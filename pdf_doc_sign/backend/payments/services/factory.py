"""
Payment Provider Factory.
Returns the correct provider based on configuration.
Add new providers here — no other code changes needed.
"""
import logging
from .base import PaymentProviderBase, PaymentMethod
from .truelayer import TrueLayerProvider
from .stripe_service import StripeProvider

logger = logging.getLogger('payments.factory')

# Registry of all providers
_PROVIDERS = {
    'truelayer': TrueLayerProvider,
    'stripe': StripeProvider,
}

# Cache instances
_instances = {}


def _get_instance(name: str) -> PaymentProviderBase:
    """Get or create a provider instance."""
    if name not in _instances:
        cls = _PROVIDERS.get(name)
        if not cls:
            raise ValueError(f'Unknown payment provider: {name}')
        _instances[name] = cls()
    return _instances[name]


def get_open_banking_provider() -> PaymentProviderBase:
    """Get the Open Banking (Pay by Bank) provider."""
    provider = _get_instance('truelayer')
    if not provider.is_configured():
        logger.warning('TrueLayer is not configured — Open Banking unavailable')
    return provider


def get_card_provider() -> PaymentProviderBase:
    """Get the card payment provider (Stripe)."""
    provider = _get_instance('stripe')
    if not provider.is_configured():
        logger.warning('Stripe is not configured — card payments unavailable')
    return provider


def get_payment_provider(method: str) -> PaymentProviderBase:
    """
    Get a payment provider by method name.
    method: 'open_banking' or 'card'
    """
    if method == 'open_banking':
        return get_open_banking_provider()
    elif method == 'card':
        return get_card_provider()
    else:
        raise ValueError(f'Unknown payment method: {method}')


def get_available_providers() -> dict:
    """Return which providers are configured and available."""
    return {
        'open_banking': {
            'available': _get_instance('truelayer').is_configured(),
            'provider': 'truelayer',
            'label': 'Pay by Bank (instant, free)',
        },
        'card': {
            'available': _get_instance('stripe').is_configured(),
            'provider': 'stripe',
            'label': 'Pay by Card',
        },
    }
