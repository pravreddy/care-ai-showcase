"""
AI Detector — End-to-end integration tests.

Scope: HTTP request → Django view → Celery task (eager mode) → DB state.
All LLM API calls are mocked. Nothing hits the network.

What's covered:
- /api/ai-detector/scan-text/          (text submission)
- /api/ai-detector/scans/<id>/         (poll / reprocess / delete)
- /api/ai-detector/scans/<id>/deep/    (deep scan trigger)
- /api/ai-detector/history/            (list)
- /api/ai-detector/providers/          (provider discovery)
- /api/ai-detector/usage/              (quota)

Auth, quota enforcement, scan-ownership, and org isolation are all exercised.
"""
import json
from unittest.mock import patch, MagicMock

import pytest
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient

from authentication.models import User
from organisations.models import Organisation, OrganisationMembership
from ai_detector.models import AIDetectionScan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canned_llm_success(provider='groq'):
    """Canned successful detection result as returned by detect_ai_content()."""
    return {
        'ai_probability': 0.45,
        'human_probability': 0.55,
        'mixed_probability': 0.0,
        'verdict': 'POSSIBLY_AI',
        'explanation': 'Balanced mixed-signal result for testing.',
        'sentences': [
            {'text': 'First sentence.', 'label': 'Mixed', 'ai_probability': 0.5},
            {'text': 'Second sentence.', 'label': 'AI', 'ai_probability': 0.7},
        ],
        'provider': provider,
        'chunks_analysed': 1,
        'chunks_total': 1,
        'chunks_failed': 0,
        'ai_sentence_count': 1,
        'total_sentence_count': 2,
        'raw': {'test': 'raw'},
        'error': None,
    }


def _canned_llm_failure():
    return {
        'ai_probability': None,
        'human_probability': None,
        'verdict': 'ERROR',
        'explanation': None,
        'sentences': [],
        'provider': 'groq',
        'raw': [],
        'error': 'All providers down',
    }


# Run Celery tasks synchronously in tests so we can assert on DB state
# immediately after the view returns. This matches how the real task runs
# end-to-end but without a broker.
CELERY_EAGER_SETTINGS = dict(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)


# ---------------------------------------------------------------------------
# Base with authenticated user
# ---------------------------------------------------------------------------

class AIDetectorAPITestBase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='scanner@test.com', password='TestPass123!',
            full_name='Scanner User',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _post_text(self, text='A long sample paragraph. ' * 10):
        return self.client.post('/api/ai-detector/scan-text/',
                                 {'text': text}, format='json')


# ---------------------------------------------------------------------------
# /scan-text/
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestScanTextEndpoint(AIDetectorAPITestBase):

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post('/api/ai-detector/scan-text/',
                                 {'text': 'a' * 100}, format='json')
        assert resp.status_code == 401

    def test_rejects_too_short_text(self):
        resp = self.client.post('/api/ai-detector/scan-text/',
                                 {'text': 'short'}, format='json')
        assert resp.status_code == 400
        assert 'too short' in resp.json()['error'].lower()

    def test_truncates_oversized_text(self):
        # Only check that the endpoint accepts oversized input without 4xx.
        # Actual truncation is asserted by the split_into_chunks unit test.
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self.client.post('/api/ai-detector/scan-text/',
                                     {'text': 'x' * 60000}, format='json')
        assert resp.status_code == 202

    def test_successful_scan_creates_scan_and_runs_task(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self._post_text()

        assert resp.status_code == 202
        data = resp.json()
        scan_id = data['id']

        # Eager task has already run — scan should be 'completed'.
        scan = AIDetectionScan.objects.get(id=scan_id)
        assert scan.status == 'completed'
        assert scan.ai_probability == pytest.approx(0.45)
        assert scan.verdict == 'POSSIBLY_AI'
        assert scan.ai_sentence_count == 1
        assert scan.total_sentence_count == 2

    def test_llm_failure_marks_scan_failed(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_failure()):
            resp = self._post_text()

        assert resp.status_code == 202
        scan = AIDetectionScan.objects.get(id=resp.json()['id'])
        assert scan.status == 'failed'
        assert 'All providers down' in scan.error_message

    def test_response_includes_usage_block(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self._post_text()
        assert 'usage' in resp.json()
        assert {'used', 'limit', 'remaining'} <= resp.json()['usage'].keys()

    def test_successful_scan_increments_usage(self):
        before = self.user.ai_scans_used_this_month
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            self._post_text()
        self.user.refresh_from_db()
        assert self.user.ai_scans_used_this_month == before + 1

    def test_failed_scan_does_not_increment_usage(self):
        before = self.user.ai_scans_used_this_month
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_failure()):
            self._post_text()
        self.user.refresh_from_db()
        # On failure, usage must NOT increment — users shouldn't pay for errors.
        assert self.user.ai_scans_used_this_month == before


# ---------------------------------------------------------------------------
# /scans/<id>/ — poll, reprocess, delete
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestScanDetailEndpoint(AIDetectorAPITestBase):

    def _create_completed_scan(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self._post_text()
        return resp.json()['id']

    def test_poll_returns_scan_data(self):
        scan_id = self._create_completed_scan()
        resp = self.client.get(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'completed'
        assert data['ai_probability'] is not None

    def test_poll_unknown_scan_returns_404(self):
        import uuid
        resp = self.client.get(f'/api/ai-detector/scans/{uuid.uuid4()}/')
        assert resp.status_code == 404

    def test_cannot_poll_another_users_scan(self):
        scan_id = self._create_completed_scan()
        other = User.objects.create_user(email='other@test.com', password='x')
        self.client.force_authenticate(user=other)
        resp = self.client.get(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 404  # not 403 — just not visible

    def test_delete_scan(self):
        scan_id = self._create_completed_scan()
        resp = self.client.delete(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 200
        assert not AIDetectionScan.objects.filter(id=scan_id).exists()

    def test_cannot_delete_another_users_scan(self):
        scan_id = self._create_completed_scan()
        other = User.objects.create_user(email='other2@test.com', password='x')
        self.client.force_authenticate(user=other)
        resp = self.client.delete(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 404
        # And the scan must still exist.
        assert AIDetectionScan.objects.filter(id=scan_id).exists()

    def test_reprocess_failed_scan(self):
        # First create a failed scan.
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_failure()):
            scan_id = self._post_text().json()['id']
        scan = AIDetectionScan.objects.get(id=scan_id)
        assert scan.status == 'failed'

        # Now reprocess — this time the LLM succeeds.
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self.client.post(f'/api/ai-detector/scans/{scan_id}/')

        assert resp.status_code == 202
        scan.refresh_from_db()
        assert scan.status == 'completed'

    def test_reprocess_already_processing_rejected(self):
        scan_id = self._create_completed_scan()
        scan = AIDetectionScan.objects.get(id=scan_id)
        scan.status = 'processing'
        scan.save(update_fields=['status'])

        resp = self.client.post(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 400
        assert 'already processing' in resp.json()['error'].lower()

    def test_reprocess_without_text_rejected(self):
        scan_id = self._create_completed_scan()
        scan = AIDetectionScan.objects.get(id=scan_id)
        scan.extracted_text = ''
        scan.status = 'failed'
        scan.save(update_fields=['extracted_text', 'status'])

        resp = self.client.post(f'/api/ai-detector/scans/{scan_id}/')
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /scans/<id>/deep/
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestDeepScanEndpoint(AIDetectorAPITestBase):

    def test_deep_scan_creates_new_scan_record(self):
        # First create a quick scan.
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            original_id = self._post_text().json()['id']

        # Now trigger deep scan.
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self.client.post(f'/api/ai-detector/scans/{original_id}/deep/')

        assert resp.status_code == 202
        deep_id = resp.json()['id']
        assert deep_id != original_id  # new record
        deep_scan = AIDetectionScan.objects.get(id=deep_id)
        assert 'Deep Scan' in deep_scan.original_filename
        assert deep_scan.status == 'completed'  # eager task has run

    def test_deep_scan_of_unknown_scan_returns_404(self):
        import uuid
        resp = self.client.post(f'/api/ai-detector/scans/{uuid.uuid4()}/deep/')
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /history/
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestHistoryEndpoint(AIDetectorAPITestBase):

    def test_returns_only_own_scans(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            self._post_text()
            self._post_text()

        # Another user's scan must not leak into history.
        other = User.objects.create_user(email='other3@test.com', password='x')
        other_scan = AIDetectionScan.objects.create(
            user=other,
            original_filename='other.txt', file_type='txt',
            file_size_bytes=100, text_length=100,
            status='completed', provider='groq',
        )

        resp = self.client.get('/api/ai-detector/history/')
        assert resp.status_code == 200
        results = resp.json()['results']
        assert len(results) == 2
        assert all(r['id'] != str(other_scan.id) for r in results)

    def test_history_ordered_newest_first(self):
        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            self._post_text(text='First scan. ' * 20)
            self._post_text(text='Second scan. ' * 20)

        resp = self.client.get('/api/ai-detector/history/')
        results = resp.json()['results']
        # Newest first — second post should come first.
        assert len(results) == 2
        assert results[0]['created_at'] >= results[1]['created_at']


# ---------------------------------------------------------------------------
# /providers/ & /usage/
# ---------------------------------------------------------------------------

class TestProvidersAndUsageEndpoints(AIDetectorAPITestBase):

    def test_providers_lists_all_known_providers(self):
        resp = self.client.get('/api/ai-detector/providers/')
        assert resp.status_code == 200
        data = resp.json()
        ids = [p['id'] for p in data['providers']]
        for expected in ['auto', 'groq', 'gemini', 'mistral', 'huggingface']:
            assert expected in ids

    def test_providers_reflects_configured_state(self):
        from django.test import override_settings
        with override_settings(GROQ_API_KEY='present'):
            resp = self.client.get('/api/ai-detector/providers/')
        groq_entry = next(p for p in resp.json()['providers'] if p['id'] == 'groq')
        assert groq_entry['configured'] is True

    def test_usage_returns_quota_info(self):
        resp = self.client.get('/api/ai-detector/usage/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'ai_scans' in data
        assert 'documents' in data
        assert 'plan' in data
        assert {'used', 'limit', 'remaining'} <= data['ai_scans'].keys()


# ---------------------------------------------------------------------------
# Quota enforcement
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestQuotaEnforcement(AIDetectorAPITestBase):

    def setUp(self):
        super().setUp()
        # Anchor usage_reset_date to today so _check_monthly_reset()
        # doesn't wipe ai_scans_used_this_month back to 0 on first access.
        # In production, reset_date is always set after the first scan via
        # increment_ai_scan_usage(); tests that pre-seed usage must mimic that.
        from django.utils import timezone
        self.user.usage_reset_date = timezone.now().date()
        self.user.save(update_fields=['usage_reset_date'])

    def test_scan_blocked_when_quota_exhausted(self):
        # Max out the user's quota.
        limit = self.user.ai_scans_limit
        self.user.ai_scans_used_this_month = limit
        self.user.save(update_fields=['ai_scans_used_this_month'])

        resp = self._post_text()
        assert resp.status_code == 429
        data = resp.json()
        assert data['remaining'] == 0
        assert 'upgrade' in data.get('upgrade_hint', '').lower()

    def test_scan_allowed_just_under_quota(self):
        self.user.ai_scans_used_this_month = max(self.user.ai_scans_limit - 1, 0)
        self.user.save(update_fields=['ai_scans_used_this_month'])

        with patch('ai_detector.tasks.detect_ai_content',
                   return_value=_canned_llm_success()):
            resp = self._post_text()
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# Organisation scoping
# ---------------------------------------------------------------------------

@override_settings(**CELERY_EAGER_SETTINGS)
class TestOrganisationScoping(APITestCase):
    """Org members should only see scans from their own org in history.

    NOTE: The AIDetectView / AIDetectTextView currently read
    `getattr(request, 'organisation', None)` but TenantMiddleware sets
    `request.org`. This means scans are created with organisation=None
    even when the user is in an org context. These tests document the
    current behaviour and the history filter (which uses the real
    `request.organisation` attr — also None). When the view is fixed to
    use `request.org`, these tests will catch the change.
    """

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@org.co.uk', password='TestPass123!',
        )
        self.org = Organisation.objects.create(
            name='Test Org', slug='test-org-ai', owner=self.owner,
            status='ACTIVE',
        )
        OrganisationMembership.objects.get_or_create(
            user=self.owner, organisation=self.org,
            defaults={'role': 'OWNER'},
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.owner)

    def test_history_returns_all_own_scans_when_no_org_filter(self):
        """Without org context, user sees all their scans across orgs."""
        AIDetectionScan.objects.create(
            user=self.owner, organisation=self.org,
            original_filename='mine.txt', file_type='txt',
            file_size_bytes=10, text_length=10,
            status='completed', provider='groq',
        )
        AIDetectionScan.objects.create(
            user=self.owner, organisation=None,
            original_filename='personal.txt', file_type='txt',
            file_size_bytes=10, text_length=10,
            status='completed', provider='groq',
        )
        resp = self.api.get('/api/ai-detector/history/')
        assert resp.status_code == 200
        # Both visible when no org filter is active.
        files = [r['original_filename'] for r in resp.json()['results']]
        assert 'mine.txt' in files
        assert 'personal.txt' in files

    def test_other_users_scans_never_visible(self):
        """Core security guarantee: one user never sees another user's scans."""
        other = User.objects.create_user(email='other@org.co.uk', password='x')
        AIDetectionScan.objects.create(
            user=other, organisation=self.org,  # same org, different user
            original_filename='theirs.txt', file_type='txt',
            file_size_bytes=10, text_length=10,
            status='completed', provider='groq',
        )
        resp = self.api.get('/api/ai-detector/history/')
        assert resp.status_code == 200
        files = [r['original_filename'] for r in resp.json()['results']]
        assert 'theirs.txt' not in files
