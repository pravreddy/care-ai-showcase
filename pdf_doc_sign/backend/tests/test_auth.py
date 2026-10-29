"""
Authentication Tests - DocSign UK
Test
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from authentication.models import User, UserProfile


class TestUserModel(TestCase):
    """Unit tests for User model."""

    def test_create_user(self):
        user = User.objects.create_user(
            email='test@avyangah.co.uk', password='TestPass123!',
            full_name='Test User',
        )
        self.assertEqual(str(user), 'test@avyangah.co.uk')
        self.assertEqual(user.subscription_plan, 'FREE')
        self.assertEqual(user.documents_remaining, 10)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email='admin@avyangah.co.uk', password='AdminPass123!',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_oauth_user_no_password(self):
        user = User.objects.create_user(
            email='google@test.com', auth_provider='google',
            provider_user_id='goog-123',
        )
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_oauth_user)

    def test_email_user_not_oauth(self):
        user = User.objects.create_user(
            email='normal@test.com', password='TestPass123!',
        )
        self.assertTrue(user.has_usable_password())
        self.assertFalse(user.is_oauth_user)

    def test_document_limit_free(self):
        user = User.objects.create_user(email='free@test.com', password='Test123!')
        self.assertEqual(user.documents_limit, 10)

    def test_document_increment(self):
        user = User.objects.create_user(email='inc@test.com', password='Test123!')
        user.increment_document_usage()
        user.refresh_from_db()
        self.assertEqual(user.documents_used_this_month, 1)
        self.assertEqual(user.documents_remaining, 9)

    def test_can_upload_when_limit_reached(self):
        user = User.objects.create_user(email='limit@test.com', password='Test123!')
        user.documents_used_this_month = 10
        user.usage_reset_date = timezone.now().date()  # Prevent monthly reset clearing the count
        user.save(update_fields=['documents_used_this_month', 'usage_reset_date'])
        self.assertFalse(user.can_upload_document)


class TestRegistrationAPI(APITestCase):
    """Integration tests for user registration."""

    def test_register_success(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'new@avyangah.co.uk',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'full_name': 'New User',
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        # Registration now requires email activation — no tokens returned
        self.assertIn('requires_activation', data)
        self.assertTrue(data['requires_activation'])
        self.assertEqual(data['email'], 'new@avyangah.co.uk')

    def test_register_password_mismatch(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'mismatch@test.com',
            'password': 'SecurePass123!',
            'password2': 'DifferentPass!',
            'full_name': 'Test',
        })
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_email(self):
        User.objects.create_user(email='dup@test.com', password='Test123!')
        response = self.client.post('/api/auth/register/', {
            'email': 'dup@test.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'full_name': 'Dup User',
        })
        self.assertEqual(response.status_code, 400)


class TestLoginAPI(APITestCase):
    """Integration tests for login."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='login@avyangah.co.uk', password='TestPass123!',
            full_name='Login Test',
        )

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'login@avyangah.co.uk',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertEqual(data['message'], 'Login successful')

    def test_login_wrong_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'login@avyangah.co.uk',
            'password': 'WrongPass!',
        })
        self.assertEqual(response.status_code, 400)

    def test_oauth_user_password_login_rejected(self):
        """OAuth users trying password login should get helpful message."""
        User.objects.create_user(
            email='google@test.com', auth_provider='google',
            provider_user_id='goog-123',
        )
        response = self.client.post('/api/auth/login/', {
            'email': 'google@test.com',
            'password': 'anypass',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Google', str(response.json()))


class TestProfileAPI(APITestCase):
    """Integration tests for profile endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@test.com', password='Test123!',
            full_name='Profile User',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'profile@test.com')

    def test_profile_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 401)


class TestOAuthProvidersAPI(APITestCase):
    """Test OAuth providers endpoint."""

    def test_providers_list(self):
        response = self.client.get('/api/auth/oauth/providers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('google', data)
        self.assertIn('github', data)
        self.assertIn('microsoft', data)
