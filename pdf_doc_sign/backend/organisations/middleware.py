"""
TenantMiddleware — Auto-inject organisation context on every request.

Safety net: once this is in place, no view can accidentally leak data
across orgs even if a developer forgets to filter by organisation.

How it works:
  1. After AuthenticationMiddleware, resolves the user's active org
  2. Sets request.org (Organisation instance or None)
  3. Sets request.org_membership (OrganisationMembership instance or None)

Org selection priority:
  1. X-Organisation-ID header (for multi-org users switching orgs)
  2. ?org= query parameter (convenience for frontend)
  3. Auto-select if user has exactly one active membership
  4. None if unauthenticated or no membership

Skipped endpoints (no org context needed):
  - Public signing: /api/sign/
  - Public delivery confirmation: /api/confirm-delivery/
  - Auth endpoints: /api/auth/
  - Admin: /admin/
  - Public invitations: /api/invitations/
  - Coupon validation: /api/coupons/validate/
  - Plans listing: /api/subscriptions/plans/
  - Chatbot: /api/chatbot/ (future)
  - Health checks, static, media
"""
import logging

from django.utils.deprecation import MiddlewareMixin

from .models import Organisation, OrganisationMembership

logger = logging.getLogger('organisations')

# URL prefixes that don't require org context
EXEMPT_PREFIXES = (
    '/admin/',
    '/api/auth/',
    '/api/sign/',
    '/api/confirm-delivery/',
    '/api/invitations/',
    '/api/organisations/check-auto-join/',
    '/api/organisations/verify-work-email/',
    '/api/coupons/validate/',       # public: check coupon at signup
    '/api/subscriptions/plans/',    # public: show pricing
    '/api/chatbot/',                # public: chatbot for visitors (future)
    '/api/free-sign/',              # public: free tool
    '/accounts/',                   # allauth
    '/static/',
    '/media/',
)

# Endpoints where org context is useful but not required
# (e.g. listing "my organisations" doesn't need an org pre-selected)
OPTIONAL_ORG_PREFIXES = (
    '/api/organisations/my/',
    '/api/organisations/request',
    '/api/payments/',
    '/api/subscriptions/my/',       # user's own subscription
    '/api/coupons/redeem/',         # user redeems their coupon
)


class TenantMiddleware(MiddlewareMixin):
    """
    Injects request.org and request.org_membership for authenticated users.

    Usage in views:
        org = request.org              # Organisation instance or None
        membership = request.org_membership  # OrganisationMembership or None

        if not org:
            return Response({'error': 'No organisation selected'}, status=400)

        # Safe query — guaranteed to be scoped to the user's org
        clients = Client.objects.filter(organisation=org)
    """

    def process_request(self, request):
        # Always set defaults so views never get AttributeError
        request.org = None
        request.org_membership = None

        path = request.path

        # Skip exempt endpoints entirely
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return None

        # Skip if user is not authenticated
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        # Skip optional-org endpoints (they work with or without org)
        if any(path.startswith(prefix) for prefix in OPTIONAL_ORG_PREFIXES):
            # Still try to resolve org for convenience, but don't fail
            self._try_resolve_org(request, user, required=False)
            return None

        # For all other endpoints, resolve org
        self._try_resolve_org(request, user, required=False)
        return None

    def _try_resolve_org(self, request, user, required=False):
        """
        Attempt to resolve the active organisation for this request.

        Priority:
          1. X-Organisation-ID header
          2. ?org= query parameter
          3. Auto-select if single membership
        """
        memberships = OrganisationMembership.objects.filter(
            user=user,
            is_active=True,
            organisation__status__in=['ACTIVE', 'TRIAL'],
        ).select_related('organisation')

        if not memberships.exists():
            return

        # Priority 1: Explicit header
        org_id = request.META.get('HTTP_X_ORGANISATION_ID')

        # Priority 2: Query parameter
        if not org_id:
            org_id = request.GET.get('org')

        if org_id:
            # Validate that user is actually a member of this org
            membership = memberships.filter(organisation_id=org_id).first()
            if membership:
                request.org = membership.organisation
                request.org_membership = membership
                return
            else:
                # User specified an org they don't belong to — ignore silently
                # (don't leak which org IDs exist)
                logger.warning(
                    f'[TENANT] User {user.email} requested org {org_id} '
                    f'but has no active membership'
                )

        # Priority 3: Auto-select if single org
        if memberships.count() == 1:
            membership = memberships.first()
            request.org = membership.organisation
            request.org_membership = membership
            return

        # Multiple orgs, none specified — leave as None
        # Views that need org context should check and prompt user to select
