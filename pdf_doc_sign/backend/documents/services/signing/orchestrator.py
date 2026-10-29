"""
SigningOrchestrator — High-level workflow for processing a signature submission.
Delegates field filling, audit logging, notifications, and status management.
"""
import logging
from django.utils import timezone

from .field_processor import FieldProcessor
from .notifications import SigningNotificationService

logger = logging.getLogger('documents.signing.orchestrator')


class SigningOrchestrator:

    @staticmethod
    def process_signature(signer, signature_image, filled_values=None):
        """
        Orchestrate the full signing workflow for a single signer.

        Steps:
          1. Update signer record (status, image, timestamp)
          2. Fill assigned fields via FieldProcessor
          3. Write audit log entry
          4. Send per-signer notification
          5. Check if all signers done → mark document complete + notify all

        Args:
            filled_values: optional dict of { field_id_str: value_str } for
                TEXT fields (and optional overrides for auto-filled
                NAME/DATE fields). Keys must be SignatureField UUIDs for
                fields assigned to this signer — unknown ids are ignored.

        Returns: dict with all_signed flag
        """
        from documents.models import DocumentAuditLog

        # 1. Update signer status
        signer.signature_image = signature_image
        signer.status = 'SIGNED'
        signer.signed_at = timezone.now()
        signer.save()

        # 2. Fill fields
        FieldProcessor.fill_signer_fields(signer, signature_image, filled_values=filled_values)

        # 3. Audit log
        DocumentAuditLog.objects.create(
            document=signer.document,
            action='SIGNED',
            description=f'Signed by {signer.signer_name} ({signer.signer_email})',
            ip_address=signer.ip_address,
        )

        # 4. Notify sender
        SigningNotificationService.on_signer_completed(signer)

        # 5. Check completion
        document = signer.document
        all_signed = not document.signers.filter(status='PENDING').exists()
        if all_signed:
            document.mark_as_signed()
            # Pre-generate the signed PDF + audit certificate so the
            # completion email can attach them. If either fails, the
            # notification still goes out — it'll just fall back to
            # download links (see SigningNotificationService).
            SigningOrchestrator._generate_completion_artifacts(document)
            SigningNotificationService.on_document_completed(document)
        elif getattr(document, 'sequential_signing', False):
            # Sequential mode: now that this signer is done, email the next
            # pending signer their link (the lowest remaining signing_order).
            SigningOrchestrator._release_next_signer(document)

        return {'all_signed': all_signed}

    @staticmethod
    def _release_next_signer(document):
        """
        In sequential signing, email the next pending signer (the lowest
        signing_order still PENDING) their signing link. No-op if there is
        no further pending signer. Email failures are logged but never
        break the signing flow.
        """
        from documents.emails.signing import send_signing_email

        next_signer = (
            document.signers
            .filter(status='PENDING')
            .order_by('signing_order')
            .first()
        )
        if not next_signer:
            return
        try:
            send_signing_email(next_signer, document, document.user)
            logger.info(
                f'[SEQUENTIAL] Released signer #{next_signer.signing_order} '
                f'({next_signer.signer_email}) for doc {document.id}'
            )
        except Exception as e:
            logger.error(
                f'[SEQUENTIAL] Failed to email next signer for doc {document.id}: {e}'
            )

    @staticmethod
    def _generate_completion_artifacts(document):
        """
        Generate both the signed PDF and the audit certificate so they're
        ready for email attachment. Failures are logged but not raised —
        the notification service degrades gracefully to download links.
        """
        from documents.services import generate_signed_pdf, generate_audit_certificate
        try:
            generate_signed_pdf(document)
        except Exception as e:
            logger.error(f'[COMPLETE] signed_pdf generation failed for doc {document.id}: {e}')
        try:
            generate_audit_certificate(document)
        except Exception as e:
            logger.error(f'[COMPLETE] audit_certificate generation failed for doc {document.id}: {e}')
