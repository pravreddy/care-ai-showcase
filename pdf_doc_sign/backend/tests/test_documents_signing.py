"""
Sequential signing tests — SignSimple

Covers the two pieces added for sequential (one-at-a-time) signing:
  1. SigningService.send_for_signing(sequential=True) — only the first
     signer is emailed; the rest are created but held.
  2. SigningOrchestrator._release_next_signer — emails the next pending
     signer (lowest signing_order) once the previous one completes.
  3. The out-of-turn guard in SignDocumentView.post — a forwarded link
     can't be signed before earlier signers have finished (HTTP 403).

All email sending is patched out, so these are pure-logic/DB tests with
no real SMTP, PDF generation, or file access.
"""
import secrets
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from authentication.models import User
from documents.models import Document, DocumentSigner
from documents.services.signing import SigningService
from documents.services.signing.orchestrator import SigningOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email='owner@test.com'):
    return User.objects.create_user(email=email, password='TestPass123!', full_name='Owner')


def make_document(user, sequential=True, status='PENDING'):
    return Document.objects.create(
        user=user,
        title='Office Agreement',
        file_size=1000,
        file_type='pdf',
        status=status,
        sequential_signing=sequential,
    )


def make_signer(document, order, email, status='PENDING'):
    return DocumentSigner.objects.create(
        document=document,
        signer_name=f'Signer {order}',
        signer_email=email,
        signing_order=order,
        status=status,
        access_token=secrets.token_urlsafe(48),
        access_expires_at=timezone.now() + timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# 1. SigningOrchestrator._release_next_signer
# ---------------------------------------------------------------------------

class TestReleaseNextSigner(TestCase):

    def setUp(self):
        self.user = make_user()
        self.doc = make_document(self.user, sequential=True)

    @patch('documents.emails.signing.send_signing_email')
    def test_emails_lowest_order_pending_signer(self, mock_email):
        make_signer(self.doc, 1, 's1@test.com', status='SIGNED')
        s2 = make_signer(self.doc, 2, 's2@test.com', status='PENDING')
        make_signer(self.doc, 3, 's3@test.com', status='PENDING')

        SigningOrchestrator._release_next_signer(self.doc)

        mock_email.assert_called_once()
        emailed_signer = mock_email.call_args.args[0]
        self.assertEqual(emailed_signer.id, s2.id)

    @patch('documents.emails.signing.send_signing_email')
    def test_noop_when_no_pending_signers(self, mock_email):
        make_signer(self.doc, 1, 's1@test.com', status='SIGNED')
        make_signer(self.doc, 2, 's2@test.com', status='SIGNED')

        SigningOrchestrator._release_next_signer(self.doc)

        mock_email.assert_not_called()

    @patch('documents.emails.signing.send_signing_email')
    def test_email_failure_is_swallowed(self, mock_email):
        # A failing email must never break the signing flow.
        mock_email.side_effect = Exception('SMTP down')
        make_signer(self.doc, 1, 's1@test.com', status='SIGNED')
        make_signer(self.doc, 2, 's2@test.com', status='PENDING')

        # Should not raise
        SigningOrchestrator._release_next_signer(self.doc)
        mock_email.assert_called_once()


# ---------------------------------------------------------------------------
# 2. SigningService.send_for_signing (sequential vs parallel)
# ---------------------------------------------------------------------------

class TestSendForSigningSequential(TestCase):

    def setUp(self):
        self.user = make_user()
        self.doc = make_document(self.user, sequential=False, status='DRAFT')

    @patch('documents.emails.signing.send_signing_email')
    def test_sequential_emails_only_first_signer(self, mock_email):
        mock_email.return_value = True
        signers_data = [
            {'name': 'A', 'email': 'a@test.com'},
            {'name': 'B', 'email': 'b@test.com'},
            {'name': 'C', 'email': 'c@test.com'},
        ]

        result = SigningService.send_for_signing(
            self.doc, signers_data, self.user, sequential=True
        )

        # Only the first signer is emailed now; the rest are queued.
        self.assertEqual(mock_email.call_count, 1)
        self.assertTrue(result['sequential'])
        self.assertEqual(self.doc.signers.count(), 3)

        self.doc.refresh_from_db()
        self.assertTrue(self.doc.sequential_signing)
        self.assertEqual(self.doc.status, 'PENDING')

    @patch('documents.emails.signing.send_signing_email')
    def test_parallel_emails_all_signers(self, mock_email):
        mock_email.return_value = True
        signers_data = [
            {'name': 'A', 'email': 'a@test.com'},
            {'name': 'B', 'email': 'b@test.com'},
        ]

        result = SigningService.send_for_signing(
            self.doc, signers_data, self.user, sequential=False
        )

        self.assertEqual(mock_email.call_count, 2)
        self.assertFalse(result['sequential'])
        self.doc.refresh_from_db()
        self.assertFalse(self.doc.sequential_signing)


# ---------------------------------------------------------------------------
# 3. Out-of-turn guard in SignDocumentView.post
# ---------------------------------------------------------------------------

class TestSequentialOutOfTurnGuard(APITestCase):
    """
    The guard runs before the 'signature image required' check, so an
    out-of-turn POST returns 403, while an in-turn POST (with no signature
    attached) falls through to 400. We use that 403-vs-400 distinction to
    assert the guard's behaviour without invoking the full signing pipeline.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def _post(self, token):
        return self.client.post(f'/api/sign/{token}/', {})

    def test_out_of_turn_signer_is_blocked_403(self):
        doc = make_document(self.user, sequential=True)
        make_signer(doc, 1, 's1@test.com', status='PENDING')
        s2 = make_signer(doc, 2, 's2@test.com', status='PENDING')

        resp = self._post(s2.access_token)
        self.assertEqual(resp.status_code, 403)

    def test_in_turn_signer_passes_guard(self):
        # Signer #1's turn → guard passes → 400 (signature required), not 403.
        doc = make_document(self.user, sequential=True)
        s1 = make_signer(doc, 1, 's1@test.com', status='PENDING')
        make_signer(doc, 2, 's2@test.com', status='PENDING')

        resp = self._post(s1.access_token)
        self.assertEqual(resp.status_code, 400)

    def test_next_signer_unblocked_after_previous_signs(self):
        doc = make_document(self.user, sequential=True)
        make_signer(doc, 1, 's1@test.com', status='SIGNED')
        s2 = make_signer(doc, 2, 's2@test.com', status='PENDING')

        resp = self._post(s2.access_token)
        # Earlier signer done → guard passes → 400, not 403.
        self.assertEqual(resp.status_code, 400)

    def test_non_sequential_document_never_blocks(self):
        doc = make_document(self.user, sequential=False)
        make_signer(doc, 1, 's1@test.com', status='PENDING')
        s2 = make_signer(doc, 2, 's2@test.com', status='PENDING')

        resp = self._post(s2.access_token)
        # Parallel mode → no turn-guard → 400, not 403.
        self.assertEqual(resp.status_code, 400)
