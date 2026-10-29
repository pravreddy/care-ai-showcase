"""
Shared mixins and helpers for document views.
"""
import logging

logger = logging.getLogger('documents')


def get_client_ip(request):
    """Extract the real client IP, even behind a reverse proxy."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
