"""
Signing Service Package — Manages the document signing workflow.

Public API (unchanged from the monolithic signing.py):
    from documents.services.signing import SigningService

    SigningService.send_for_signing(document, signers_data, sender, ip_address)
    SigningService.process_signature(signer, signature_image)

Internal structure:
    signing/
        __init__.py         ← This file (SigningService entry point)
        orchestrator.py     ← SigningOrchestrator (workflow for process_signature)
        field_processor.py  ← FieldProcessor (filling signature/name/date fields)
        notifications.py    ← SigningNotificationService (email triggers)
"""
import secrets
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .orchestrator import SigningOrchestrator

logger = logging.getLogger('documents.signing')


class SigningService:
    """
    Top-level service consumed by views.py.
    send_for_signing lives here (it's already lean).
    process_signature delegates to SigningOrchestrator.
    """

    @staticmethod
    def send_for_signing(document, signers_data, sender, ip_address=None, sequential=False):
        """
        Create signers, send emails, update document status.

        When sequential=True only the first signer (signing_order 1) is
        emailed now; the rest are created but held, and each is released as
        the previous signer completes (see SigningOrchestrator). When False
        (default) every signer is emailed immediately — the original
        parallel behaviour.

        Returns: dict with created_signers, emails_sent, emails_failed,
        email_results, sequential
        """
        from documents.models import DocumentSigner, DocumentAuditLog
        from documents.emails.signing import send_signing_email

        created_signers = []
        email_results = []

        for i, signer_data in enumerate(signers_data):
            ds = DocumentSigner.objects.create(
                document=document,
                signer_name=signer_data.get('name', ''),
                signer_email=signer_data.get('email', ''),
                signing_order=i + 1,
                access_token=secrets.token_urlsafe(48),
                access_expires_at=timezone.now() + timedelta(days=settings.DOCUMENT_EXPIRY_DAYS),
            )
            created_signers.append(ds)

            # Sequential: hold everyone after the first until it's their turn.
            if sequential and ds.signing_order != 1:
                email_results.append({'email': ds.signer_email, 'sent': False, 'queued': True})
                continue

            email_sent = send_signing_email(ds, document, sender)
            email_results.append({'email': ds.signer_email, 'sent': email_sent})

        document.sequential_signing = sequential
        document.status = 'PENDING'
        document.save(update_fields=['status', 'sequential_signing'])

        emails_sent = sum(1 for r in email_results if r.get('sent'))
        emails_failed = sum(1 for r in email_results if not r.get('sent') and not r.get('queued'))
        queued = sum(1 for r in email_results if r.get('queued'))

        if sequential:
            desc = (
                f'Sent sequentially to {len(created_signers)} signer(s) — first signer '
                f'emailed ({emails_failed} failed), {queued} queued for their turn'
            )
        else:
            desc = (
                f'Sent to {len(created_signers)} signer(s) '
                f'({emails_sent} emails sent, {emails_failed} failed)'
            )

        DocumentAuditLog.objects.create(
            document=document, user=sender, action='SENT',
            description=desc,
            ip_address=ip_address,
        )

        return {
            'created_signers': created_signers,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'email_results': email_results,
            'sequential': sequential,
        }

    @staticmethod
    def process_signature(signer, signature_image, filled_values=None):
        """Delegate to SigningOrchestrator."""
        return SigningOrchestrator.process_signature(signer, signature_image, filled_values=filled_values)
