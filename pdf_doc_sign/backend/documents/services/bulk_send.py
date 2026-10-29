"""
BulkSendService — Send the same document to multiple recipients,
each getting their own independent copy to sign.
"""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger('documents.bulk_send')


class BulkSendService:

    @staticmethod
    def bulk_send(source_document, recipients, sender, ip_address=None):
        """
        Create independent document copies for each recipient and send signing emails.

        Args:
            source_document: The original Document to copy from
            recipients: list of dicts [{name, email}, ...]
            sender: User who is sending
            ip_address: sender's IP

        Returns:
            dict with created_documents, emails_sent, emails_failed, results
        """
        from documents.models import Document, DocumentSigner, SignatureField, DocumentAuditLog
        from documents.emails.signing import send_signing_email

        # Read source PDF once
        try:
            with open(source_document.file.path, 'rb') as f:
                pdf_bytes = f.read()
        except FileNotFoundError:
            raise ValueError('Source document PDF not found.')

        # Get source fields config
        source_fields = list(SignatureField.objects.filter(
            document=source_document,
        ).values(
            'field_type', 'signer_index', 'page',
            'x_percent', 'y_percent', 'width_percent', 'height_percent',
            'label', 'required',
        ))

        results = []

        for recipient in recipients:
            name = recipient.get('name', '').strip()
            email = recipient.get('email', '').strip()

            if not email:
                results.append({'email': email, 'sent': False, 'error': 'Missing email'})
                continue

            try:
                # 1. Create document copy
                doc = Document.objects.create(
                    user=sender,
                    title=f'{source_document.title} — {name or email}',
                    description=f'Bulk sent to {name} ({email})',
                    file_size=len(pdf_bytes),
                    file_type=source_document.file_type,
                    page_count=source_document.page_count,
                    status='PENDING',
                )
                doc.file.save(f'{doc.id}.pdf', ContentFile(pdf_bytes), save=True)

                # 2. Copy signature fields (reset signer_index to 1 for single signer)
                for fc in source_fields:
                    SignatureField.objects.create(
                        document=doc,
                        field_type=fc['field_type'],
                        signer_index=1,
                        page=fc['page'],
                        x_percent=fc['x_percent'],
                        y_percent=fc['y_percent'],
                        width_percent=fc['width_percent'],
                        height_percent=fc['height_percent'],
                        label=fc['label'],
                        required=fc['required'],
                    )

                # 3. Create signer
                ds = DocumentSigner.objects.create(
                    document=doc,
                    signer_name=name or email.split('@')[0],
                    signer_email=email,
                    signing_order=1,
                    access_token=secrets.token_urlsafe(48),
                    access_expires_at=timezone.now() + timedelta(days=settings.DOCUMENT_EXPIRY_DAYS),
                )

                # 4. Send email
                email_sent = send_signing_email(ds, doc, sender)

                # 5. Audit log
                DocumentAuditLog.objects.create(
                    document=doc, user=sender, action='SENT',
                    description=f'Bulk sent to {name} ({email})',
                    ip_address=ip_address,
                )

                # 6. Increment usage
                sender.increment_document_usage()

                results.append({
                    'email': email,
                    'name': name,
                    'document_id': str(doc.id),
                    'sent': email_sent,
                })

            except Exception as e:
                logger.error(f'[BULK SEND] Failed for {email}: {e}')
                results.append({'email': email, 'sent': False, 'error': str(e)})

        sent_count = sum(1 for r in results if r.get('sent'))
        failed_count = sum(1 for r in results if not r.get('sent'))

        # Log on the source document
        DocumentAuditLog.objects.create(
            document=source_document, user=sender, action='SENT',
            description=f'Bulk sent to {len(recipients)} recipient(s) ({sent_count} sent, {failed_count} failed)',
            ip_address=ip_address,
        )

        return {
            'total': len(recipients),
            'emails_sent': sent_count,
            'emails_failed': failed_count,
            'results': results,
        }
