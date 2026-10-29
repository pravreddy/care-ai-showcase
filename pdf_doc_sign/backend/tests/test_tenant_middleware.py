"""
Tests for TenantMiddleware — org context injection.
"""
import uuid
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from organisations.models import Organisation, OrganisationMembership
from organisations.middleware import TenantMiddleware

User = get_user_model()


def dummy_get_response(request):
    """Minimal view for middleware testing."""
    return HttpResponse('OK')


class TenantMiddlewareTest(TestCase):
    """Test that TenantMiddleware correctly resolves org context."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(dummy_get_response)

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123',
            full_name='Test User',
        )

        # Create org
        self.org = Organisation.objects.create(
            name='Test Org', slug='test-org', owner=self.user,
            status='ACTIVE', sales_access_enabled=True,
        )

        # Membership created by Organisation.save() override

    def _make_request(self, path='/api/sales/clients/', org_header=None, org_param=None):
        """Helper to create a request with optional org selection."""
        url = path
        if org_param:
            url += f'?org={org_param}'

        request = self.factory.get(url)
        request.user = self.user

        if org_header:
            request.META['HTTP_X_ORGANISATION_ID'] = str(org_header)

        self.middleware.process_request(request)
        return request

    def test_single_org_auto_selected(self):
        """User with one org gets it auto-selected."""
        request = self._make_request()
        self.assertEqual(request.org, self.org)
        self.assertIsNotNone(request.org_membership)

    def test_explicit_header_selects_org(self):
        """X-Organisation-ID header selects the correct org."""
        request = self._make_request(org_header=self.org.id)
        self.assertEqual(request.org, self.org)

    def test_query_param_selects_org(self):
        """?org= query parameter selects the correct org."""
        request = self._make_request(org_param=self.org.id)
        self.assertEqual(request.org, self.org)

    def test_invalid_org_id_ignored(self):
        """Invalid org ID does not set request.org (single org fallback)."""
        fake_id = uuid.uuid4()
        request = self._make_request(org_header=fake_id)
        # Falls through to single-org auto-select
        self.assertEqual(request.org, self.org)

    def test_unauthenticated_gets_none(self):
        """Unauthenticated user gets None for org."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/api/sales/clients/')
        request.user = AnonymousUser()
        self.middleware.process_request(request)
        self.assertIsNone(request.org)

    def test_exempt_paths_skipped(self):
        """Exempt paths (admin, auth, signing) skip org resolution."""
        for path in ['/admin/', '/api/auth/login/', '/api/sign/abc123/']:
            request = self.factory.get(path)
            request.user = self.user
            self.middleware.process_request(request)
            self.assertIsNone(request.org, f'Expected None for {path}')

    def test_multi_org_no_selection_gets_none(self):
        """Multi-org user without selection gets None."""
        # Create second org
        org2 = Organisation.objects.create(
            name='Second Org', slug='second-org', owner=self.user,
            status='ACTIVE',
        )
        # Membership auto-created by save()

        request = self._make_request()
        self.assertIsNone(request.org)

    def test_multi_org_with_header_selects_correct(self):
        """Multi-org user with header gets the right org."""
        org2 = Organisation.objects.create(
            name='Second Org', slug='second-org', owner=self.user,
            status='ACTIVE',
        )

        request = self._make_request(org_header=org2.id)
        self.assertEqual(request.org, org2)

    def test_inactive_membership_excluded(self):
        """Inactive membership does not count."""
        membership = OrganisationMembership.objects.get(
            user=self.user, organisation=self.org,
        )
        membership.is_active = False
        membership.save()

        request = self._make_request()
        self.assertIsNone(request.org)

    def test_suspended_org_excluded(self):
        """Suspended org is not selectable."""
        self.org.status = 'SUSPENDED'
        self.org.save()

        request = self._make_request()
        self.assertIsNone(request.org)
