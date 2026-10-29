"""
Organisation Tests - DocSign UK White-Label
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient

from authentication.models import User
from organisations.models import Organisation, Branch, OrganisationMembership


class TestOrganisationModel(TestCase):
    """Unit tests for Organisation model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@acme.co.uk', password='TestPass123!',
            full_name='Org Owner',
        )

    def test_create_organisation(self):
        org = Organisation.objects.create(
            name='Acme Ltd', slug='acme', owner=self.owner,
        )
        self.assertEqual(str(org), 'Acme Ltd')
        self.assertEqual(org.plan, 'FREE')
        self.assertEqual(org.documents_limit, 10)

    def test_custom_doc_limit_override(self):
        org = Organisation.objects.create(
            name='Enterprise Corp', slug='enterprise', owner=self.owner,
            documents_per_month_override=5000,
        )
        self.assertEqual(org.documents_limit, 5000)

    def test_increment_usage(self):
        org = Organisation.objects.create(
            name='Test Org', slug='test-org', owner=self.owner,
        )
        org.increment_document_usage()
        org.refresh_from_db()
        self.assertEqual(org.documents_used_this_month, 1)

    def test_remaining_docs(self):
        org = Organisation.objects.create(
            name='Test Org', slug='test-remaining', owner=self.owner,
            plan='STARTER',
        )
        # STARTER = 100 docs
        self.assertEqual(org.documents_remaining, 100)
        org.documents_used_this_month = 50
        org.save()
        self.assertEqual(org.documents_remaining, 50)


class TestBranchModel(TestCase):
    """Unit tests for Branch model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@branch.co.uk', password='TestPass123!',
        )
        self.org = Organisation.objects.create(
            name='Multi Branch Ltd', slug='multi-branch', owner=self.owner,
            primary_colour='#ff0000',
        )

    def test_create_branch(self):
        branch = Branch.objects.create(
            organisation=self.org, name='London Office', city='London',
        )
        self.assertEqual(str(branch), 'Multi Branch Ltd — London Office')

    def test_branch_inherits_org_colour(self):
        branch = Branch.objects.create(
            organisation=self.org, name='Default Branch',
        )
        self.assertEqual(branch.display_colour, '#ff0000')

    def test_branch_overrides_colour(self):
        branch = Branch.objects.create(
            organisation=self.org, name='Custom Branch',
            primary_colour='#00ff00',
        )
        self.assertEqual(branch.display_colour, '#00ff00')


class TestMembershipModel(TestCase):
    """Unit tests for OrganisationMembership."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@member.co.uk', password='TestPass123!',
        )
        self.member = User.objects.create_user(
            email='member@member.co.uk', password='TestPass123!',
        )
        self.org = Organisation.objects.create(
            name='Membership Test', slug='membership-test', owner=self.owner,
        )

    def test_owner_can_admin(self):
        m, _ = OrganisationMembership.objects.get_or_create(
            user=self.owner, organisation=self.org,
            defaults={'role': 'OWNER'},
        )
        self.assertTrue(m.can_admin)
        self.assertTrue(m.can_manage)

    def test_member_cannot_admin(self):
        m = OrganisationMembership.objects.create(
            user=self.member, organisation=self.org, role='MEMBER',
        )
        self.assertFalse(m.can_admin)
        self.assertFalse(m.can_manage)

    def test_manager_can_manage(self):
        m = OrganisationMembership.objects.create(
            user=self.member, organisation=self.org, role='MANAGER',
        )
        self.assertFalse(m.can_admin)
        self.assertTrue(m.can_manage)


class TestOrganisationAPI(APITestCase):
    """Integration tests for Organisation API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='api@org.co.uk', password='TestPass123!',
            full_name='API User',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_organisation_via_request(self):
        """Submit an organisation creation request."""
        response = self.client.post('/api/organisations/request/', {
            'organisation_name': 'New Org Ltd',
            'organisation_domain': 'neworg.co.uk',
            'work_email': 'api@neworg.co.uk',
            'company_number': '12345678',
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('request_id', data)
        self.assertEqual(data['status'], 'PENDING_WORK_EMAIL')

    def test_list_my_organisations(self):
        """List orgs the user belongs to via /api/organisations/my/."""
        org = Organisation.objects.create(
            name='My Org', slug='my-org', owner=self.user,
        )
        # Organisation.save() auto-creates OWNER membership

        response = self.client.get('/api/organisations/my/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['organisation_name'], 'My Org')

    def test_cannot_see_others_orgs(self):
        """User should not see orgs they are not a member of."""
        other_user = User.objects.create_user(
            email='other@org.co.uk', password='TestPass123!',
        )
        Organisation.objects.create(
            name='Other Org', slug='other-org', owner=other_user,
        )
        # Organisation.save() auto-creates OWNER membership for other_user

        response = self.client.get('/api/organisations/my/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_org_members_list(self):
        """Owner can list org members."""
        org = Organisation.objects.create(
            name='Members Org', slug='members-org', owner=self.user,
            status='ACTIVE',
        )

        response = self.client.get(f'/api/organisations/{org.id}/members/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['email'], 'api@org.co.uk')
        self.assertEqual(data[0]['role'], 'OWNER')
